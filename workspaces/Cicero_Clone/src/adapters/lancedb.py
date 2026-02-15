import lancedb
import pyarrow as pa
from typing import List, Dict, Any, Optional
import json
import uuid
import asyncio
from .base import DatabaseAdapter
from ..core.types import RetrievalResult, StoreResult, SourceType

class LanceDBAdapter(DatabaseAdapter):
    """
    Adapter for LanceDB vector database.
    
    Handles:
    - Vector similarity search
    - Local/cloud storage
    - Proper distance-to-similarity conversion
    
    CRITICAL: LanceDB returns DISTANCE (lower = better).
    We convert to SIMILARITY (higher = better, 0-1 range).
    """
    
    def __init__(self, 
                 db_path: str = "./lancedb_data",
                 table_name: str = "documents",
                 embedding_dim: int = 1536,
                 distance_metric: str = "cosine"):
        """
        Args:
            db_path: Local path or cloud URI (s3://..., gs://...)
            table_name: Name of table to use
            embedding_dim: Dimension of embedding vectors
            distance_metric: "cosine", "l2", or "dot"
        """
        self.db_path = db_path
        self.table_name = table_name
        self.embedding_dim = embedding_dim
        self.distance_metric = distance_metric
        self.db = None
        self.table = None
    
    @property
    def name(self) -> str:
        return "lancedb"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.VECTOR
    
    async def connect(self) -> None:
        """Connect to LanceDB (local or cloud)"""
        # LanceDB's connect_async is available in newer versions
        # Ensure lancedb is installed and supports async or wrap sync calls if needed.
        # For now assuming standard async usage pattern from docs for v0.4+
        try:
             self.db = await lancedb.connect_async(self.db_path)
        except AttributeError:
             # Fallback if async not available directly (older lancedb) or wrap sync
             # For MVP assuming modern lancedb
             self.db = await lancedb.connect_async(self.db_path)
        
        # Check if table exists, create if not
        if self.table_name not in await self.db.table_names():
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("embedding", pa.list_(pa.float32(), self.embedding_dim)),
                pa.field("source_document_id", pa.string()),
                pa.field("citation_key", pa.string()),
                pa.field("chunk_index", pa.int32()),
                pa.field("workspace_id", pa.string()),
                pa.field("metadata", pa.string())  # JSON string
            ])
            self.table = await self.db.create_table(
                self.table_name, 
                schema=schema
            )
        else:
            self.table = await self.db.open_table(self.table_name)
    
    async def disconnect(self) -> None:
        """LanceDB doesn't require explicit disconnect"""
        self.db = None
        self.table = None
    
    async def health_check(self) -> bool:
        """Check if LanceDB is accessible"""
        try:
            if self.table is None:
                return False
            # Try a simple operation with timeout
            async with asyncio.timeout(2.0):
                await self.table.count_rows()
            return True
        except Exception:
            return False
    
    async def store(self, 
                   content: str, 
                   embedding: List[float], 
                   metadata: Dict[str, Any],
                   source_document_id: str,
                   citation_key: str,
                   workspace_id: Optional[str] = None) -> StoreResult:
        """Store document in LanceDB"""
        try:
            doc_id = str(uuid.uuid4())
            
            data = [{
                "id": doc_id,
                "content": content,
                "embedding": embedding,
                "source_document_id": source_document_id,
                "citation_key": citation_key,
                "chunk_index": metadata.get("chunk_index", 0),
                "workspace_id": workspace_id or "",
                "metadata": json.dumps(metadata)
            }]
            
            await self.table.add(data)
            return StoreResult(item_id=doc_id, success=True, database=self.name)
            
        except Exception as e:
            return StoreResult(
                item_id="", 
                success=False, 
                database=self.name, 
                error=str(e)
            )
    
    async def store_batch(self,
                         items: List[Dict[str, Any]],
                         batch_size: int = 100) -> List[StoreResult]:
        """Store multiple items efficiently"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_data = []
            batch_ids = []
            
            for item in batch:
                doc_id = str(uuid.uuid4())
                batch_ids.append(doc_id)
                batch_data.append({
                    "id": doc_id,
                    "content": item["content"],
                    "embedding": item["embedding"],
                    "source_document_id": item["source_document_id"],
                    "citation_key": item["citation_key"],
                    "chunk_index": item.get("metadata", {}).get("chunk_index", 0),
                    "workspace_id": item.get("workspace_id", ""),
                    "metadata": json.dumps(item.get("metadata", {}))
                })
            
            try:
                await self.table.add(batch_data)
                results.extend([
                    StoreResult(item_id=doc_id, success=True, database=self.name)
                    for doc_id in batch_ids
                ])
            except Exception as e:
                results.extend([
                    StoreResult(item_id="", success=False, database=self.name, error=str(e))
                    for _ in batch_ids
                ])
        
        return results
    
    async def retrieve(self, 
                      query: str, 
                      query_embedding: Optional[List[float]] = None,
                      top_k: int = 5,
                      filters: Optional[Dict[str, Any]] = None,
                      workspace_id: Optional[str] = None) -> List[RetrievalResult]:
        """
        Vector similarity search in LanceDB.
        
        CRITICAL: Converts LanceDB distance to 0-1 similarity score.
        """
        if query_embedding is None:
            raise ValueError("LanceDB requires query_embedding for retrieval")
        
        # Build search query builder
        search_builder = await self.table.search(query_embedding)
        
        # Apply workspace filter and additional filters
        conditions = []
        if workspace_id:
             conditions.append(f"workspace_id = '{workspace_id}'")
        if filters:
             conditions.append(self._build_filter_expression(filters))
        
        if conditions:
             final_filter = " AND ".join(filter(None, conditions))
             search_builder = search_builder.where(final_filter)
        
        # Apply limit LAST
        search_builder = search_builder.limit(top_k)
        
        results = await search_builder.to_list()
        
        # Convert to universal RetrievalResult format with NORMALIZED SCORES
        return [
            RetrievalResult(
                content=result["content"],
                score=self._distance_to_similarity(result["_distance"]),
                source_type=self.source_type,
                database=self.name,
                source_document_id=result["source_document_id"],
                citation_key=result["citation_key"],
                chunk_index=result.get("chunk_index"),
                workspace_id=result.get("workspace_id") or None,
                metadata=json.loads(result["metadata"]) if result.get("metadata") else {}
            )
            for result in results
        ]
    
    async def retrieve_batch(self,
                            queries: List[str],
                            query_embeddings: List[List[float]],
                            top_k: int = 5,
                            workspace_id: Optional[str] = None) -> List[List[RetrievalResult]]:
        """Retrieve for multiple queries"""
        tasks = [
            self.retrieve(q, emb, top_k, workspace_id=workspace_id)
            for q, emb in zip(queries, query_embeddings)
        ]
        return await asyncio.gather(*tasks)
    
    async def delete(self, item_id: str) -> bool:
        """Delete document by ID"""
        try:
            await self.table.delete(f"id = '{item_id}'")
            return True
        except Exception:
            return False
    
    async def delete_by_workspace(self, workspace_id: str) -> int:
        """Delete all items in a workspace"""
        try:
            count_before = await self.table.count_rows()
            await self.table.delete(f"workspace_id = '{workspace_id}'")
            count_after = await self.table.count_rows()
            return count_before - count_after
        except Exception:
            return 0
    
    async def count(self, workspace_id: Optional[str] = None) -> int:
        """Return count of items"""
        if workspace_id:
            # LanceDB doesn't have direct filtered count, so we query
            # Optimizing: using limit? No, we need count all.
            # LanceDB SQL support might be better if available.
            # Using search with dummy vector might be slow for full scans.
            # Better approach: To list with just 'id' column?
            try:
                # Assuming pandas df approach or pyarrow scanner
                scanner = self.table.to_pandas() # Might be heavy
                # Better: arrow filter
                t = self.table.to_arrow()
                filtered = t.filter(pa.compute.equal(t['workspace_id'], workspace_id))
                return len(filtered)
            except Exception:
                return 0
        return await self.table.count_rows()
    
    def _distance_to_similarity(self, distance: float) -> float:
        """
        Convert distance metric to 0-1 similarity score.
        
        CRITICAL: This is where score normalization happens.
        """
        if self.distance_metric == "cosine":
            # Cosine distance is in [0, 2], similarity in [-1, 1]
            # Normalize to [0, 1]
            return max(0.0, min(1.0, 1.0 - distance))
        
        elif self.distance_metric == "l2":
            # L2 distance is in [0, inf), convert to [0, 1]
            return 1.0 / (1.0 + distance)
        
        elif self.distance_metric == "dot":
            # Dot product can be negative, clamp to [0, 1]
            # Assuming normalized vectors, dot product is in [-1, 1]
            return max(0.0, min(1.0, (distance + 1.0) / 2.0))
        
        else:
            # Default: assume distance, convert
            return 1.0 / (1.0 + distance)
    
    def _build_filter_expression(self, filters: Dict[str, Any]) -> str:
        """Convert filters dict to LanceDB WHERE clause"""
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            elif isinstance(value, bool):
                conditions.append(f"{key} = {str(value).lower()}")
            else:
                conditions.append(f"{key} = {value}")
        return " AND ".join(conditions)
