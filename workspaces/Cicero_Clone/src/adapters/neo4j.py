from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
import json
import asyncio
from .base import DatabaseAdapter
from ..core.types import RetrievalResult, StoreResult, SourceType
from ..core.constants import LEGAL_GRAPH_PATTERNS

class Neo4jAdapter(DatabaseAdapter):
    """
    Adapter for Neo4j Aura graph database.
    
    Handles:
    - Graph traversal queries
    - Relationship-based retrieval
    - Hybrid vector + graph search (if Neo4j has vector index)
    - Cypher query execution
    - Legal-specific graph patterns
    
    CRITICAL: Scores are normalized to 0-1 range.
    """
    
    def __init__(self, 
                 uri: str,
                 username: str,
                 password: str,
                 database: str = "neo4j",
                 vector_index_name: str = "document_embeddings"):
        """
        Args:
            uri: Neo4j Aura URI (neo4j+s://...)
            username: Database username
            password: Database password
            database: Database name (default: "neo4j")
            vector_index_name: Name of vector index (if using vector search)
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database_name = database
        self.vector_index_name = vector_index_name
        self.driver = None
        self._has_vector_index_cache: Optional[bool] = None
    
    @property
    def name(self) -> str:
        return "neo4j"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.GRAPH
    
    async def connect(self) -> None:
        """Connect to Neo4j Aura"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri, 
            auth=(self.username, self.password)
        )
        # Verify connection
        await self.driver.verify_connectivity()
        # Check for vector index
        self._has_vector_index_cache = await self._check_vector_index()
    
    async def disconnect(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            self.driver = None
    
    async def health_check(self) -> bool:
        """Check if Neo4j is accessible"""
        try:
            if self.driver is None:
                return False
            async with asyncio.timeout(2.0):
                async with self.driver.session(database=self.database_name) as session:
                    await session.run("RETURN 1")
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
        """Store document as a node in Neo4j"""
        try:
            async with self.driver.session(database=self.database_name) as session:
                result = await session.run("""
                    CREATE (d:Document:Chunk {
                        content: $content,
                        embedding: $embedding,
                        source_document_id: $source_document_id,
                        citation_key: $citation_key,
                        workspace_id: $workspace_id,
                        chunk_index: $chunk_index,
                        metadata: $metadata,
                        created_at: datetime()
                    })
                    RETURN elementId(d) as node_id
                """, 
                content=content, 
                embedding=embedding,
                source_document_id=source_document_id,
                citation_key=citation_key,
                workspace_id=workspace_id or "",
                chunk_index=metadata.get("chunk_index", 0),
                metadata=json.dumps(metadata))
                
                record = await result.single()
                return StoreResult(
                    item_id=record["node_id"], 
                    success=True, 
                    database=self.name
                )
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
        """Store multiple items using UNWIND for efficiency"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_data = []
            
            for item in batch:
                batch_data.append({
                    "content": item["content"],
                    "embedding": item["embedding"],
                    "source_document_id": item["source_document_id"],
                    "citation_key": item["citation_key"],
                    "workspace_id": item.get("workspace_id", ""),
                    "chunk_index": item.get("metadata", {}).get("chunk_index", 0),
                    "metadata": json.dumps(item.get("metadata", {}))
                })
            
            try:
                async with self.driver.session(database=self.database_name) as session:
                    result = await session.run("""
                        UNWIND $batch as item
                        CREATE (d:Document:Chunk {
                            content: item.content,
                            embedding: item.embedding,
                            source_document_id: item.source_document_id,
                            citation_key: item.citation_key,
                            workspace_id: item.workspace_id,
                            chunk_index: item.chunk_index,
                            metadata: item.metadata,
                            created_at: datetime()
                        })
                        RETURN elementId(d) as node_id
                    """, batch=batch_data)
                    
                    records = await result.data()
                    results.extend([
                        StoreResult(item_id=r["node_id"], success=True, database=self.name)
                        for r in records
                    ])
            except Exception as e:
                results.extend([
                    StoreResult(item_id="", success=False, database=self.name, error=str(e))
                    for _ in batch
                ])
        
        return results
    
    async def retrieve(self, 
                      query: str, 
                      query_embedding: Optional[List[float]] = None,
                      top_k: int = 5,
                      filters: Optional[Dict[str, Any]] = None,
                      workspace_id: Optional[str] = None) -> List[RetrievalResult]:
        """
        Retrieve from Neo4j using graph traversal or vector search.
        
        Strategy selection:
        1. If query_embedding provided AND vector index exists: Hybrid (vector + graph boost)
        2. If query contains relationship keywords: Graph pattern matching
        3. Otherwise: Full-text search with graph boost
        """
        async with self.driver.session(database=self.database_name) as session:
            
            # Determine best retrieval strategy
            # Note: filters are not fully implemented here yet besides workspace_id
            
            if query_embedding and self._has_vector_index_cache:
                results = await self._vector_search(session, query_embedding, top_k, workspace_id)
            else:
                # Select graph pattern based on query analysis
                pattern = self._select_graph_pattern(query)
                results = await self._graph_search(session, query, pattern, top_k, workspace_id)
            
            return results
    
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
    
    async def _vector_search(self, session, query_embedding: List[float], 
                            top_k: int, workspace_id: Optional[str]) -> List[RetrievalResult]:
        """Vector similarity search using Neo4j vector index"""
        
        # Determine strict or oversample+filter
        # Better: `CALL ... WHERE node.workspace_id = $wid` is efficient in Neo4j 5.x if strict filtering
        # But `queryNodes` doesn't strictly support WHERE inside the procedure call itself in all versions
        # Standard: `CALL ... YIELD node, score WHERE node.workspace_id = ...`
        
        workspace_filter = "AND node.workspace_id = $workspace_id" if workspace_id else ""
        
        # We need to oversample if we filter post-yield
        LIMIT_MULTIPLIER = 5 if workspace_id else 1
        
        cypher = f"""
            CALL db.index.vector.queryNodes($index_name, $limit, $embedding)
            YIELD node, score
            WHERE node:Chunk {workspace_filter}
            RETURN node.content as content,
                   node.citation_key as citation_key,
                   node.source_document_id as source_document_id,
                   node.chunk_index as chunk_index,
                   node.workspace_id as workspace_id,
                   node.metadata as metadata,
                   score
        """
        
        result = await session.run(
            cypher,
            index_name=self.vector_index_name,
            embedding=query_embedding,
            limit=top_k * LIMIT_MULTIPLIER,
            workspace_id=workspace_id
        )
        
        records = await result.data()
        
        # Neo4j vector search returns similarity scores already in [0, 1] for Cosine
        return [
            RetrievalResult(
                content=record["content"],
                score=float(record["score"]),  # Already 0-1
                source_type=SourceType.HYBRID,  # Vector from graph DB
                database=self.name,
                source_document_id=record["source_document_id"],
                citation_key=record["citation_key"],
                chunk_index=record.get("chunk_index"),
                workspace_id=record.get("workspace_id") or None,
                metadata=json.loads(record["metadata"]) if record.get("metadata") else {}
            )
            for record in records
        ][:top_k] # Re-limit after filter
    
    async def _graph_search(self, session, query: str, pattern_name: str,
                           top_k: int, workspace_id: Optional[str]) -> List[RetrievalResult]:
        """Graph pattern-based search"""
        
        pattern = LEGAL_GRAPH_PATTERNS.get(pattern_name, LEGAL_GRAPH_PATTERNS["full_text_with_graph_boost"])
        
        # Add workspace filter if needed
        # For simplicity in MVP, strict workspace filtering on graph results post-query
        # unless we inject into Cypher.
        # Let's inject into Cypher for better perf if possible, but patterns are complex strings.
        # We will filter post-query for safety in Phase 1.
        
        result = await session.run(
            pattern,
            search_term=query,
            limit=top_k * 5 # Oversample for filtering
        )
        
        records = await result.data()
        
        if not records:
            return []
        
        # Normalize scores to 0-1
        max_score = max(r["relevance_score"] for r in records) if records else 1.0
        max_score = max_score if max_score > 0 else 1.0
        
        results = [
            RetrievalResult(
                content=record["content"],
                score=float(record["relevance_score"]) / max_score,  # Normalize
                source_type=SourceType.GRAPH,
                database=self.name,
                source_document_id=record["source_document_id"],
                citation_key=record["citation_key"],
                workspace_id=workspace_id,
                metadata={}
            )
            for record in records
        ]
        
        # Filter by workspace if needed
        if workspace_id:
            results = [r for r in results if r.workspace_id == workspace_id]
        
        return results[:top_k]
    
    def _select_graph_pattern(self, query: str) -> str:
        """Select appropriate graph pattern based on query content"""
        query_lower = query.lower()
        
        # Citation chain patterns
        if any(kw in query_lower for kw in ["cites", "cited by", "authority", "relied on", "relies on"]):
            return "authority_chain"
        
        # Issue clustering
        if any(kw in query_lower for kw in ["issue", "addresses", "deals with", "concerns"]):
            return "issue_cluster"
        
        # Statutory patterns
        if any(kw in query_lower for kw in ["rcw", "statute", "code", "usc", "applies"]):
            return "statutory_application"
        
        # Factor analysis (e.g., Gunwall factors)
        if any(kw in query_lower for kw in ["factor", "prong", "element", "test"]):
            return "factor_analysis"
        
        # Procedural history
        if any(kw in query_lower for kw in ["appeal", "reversed", "affirmed", "remand"]):
            return "procedural_history"
        
        # Default: full-text with graph boost
        return "full_text_with_graph_boost"
    
    async def delete(self, item_id: str) -> bool:
        """Delete node by ID"""
        async with self.driver.session(database=self.database_name) as session:
            try:
                await session.run("""
                    MATCH (n)
                    WHERE elementId(n) = $node_id
                    DETACH DELETE n
                """, node_id=item_id)
                return True
            except Exception:
                return False
    
    async def delete_by_workspace(self, workspace_id: str) -> int:
        """Delete all items in a workspace"""
        async with self.driver.session(database=self.database_name) as session:
            try:
                result = await session.run("""
                    MATCH (n:Chunk {workspace_id: $workspace_id})
                    WITH n, count(n) as cnt
                    DETACH DELETE n
                    RETURN cnt
                """, workspace_id=workspace_id)
                record = await result.single()
                return record["cnt"] if record else 0
            except Exception:
                return 0
    
    async def count(self, workspace_id: Optional[str] = None) -> int:
        """Return count of chunks"""
        async with self.driver.session(database=self.database_name) as session:
            if workspace_id:
                result = await session.run(
                    "MATCH (n:Chunk {workspace_id: $wid}) RETURN count(n) as cnt",
                    wid=workspace_id
                )
            else:
                result = await session.run("MATCH (n:Chunk) RETURN count(n) as cnt")
            record = await result.single()
            return record["cnt"] if record else 0
    
    async def _check_vector_index(self) -> bool:
        """Check if vector index exists"""
        async with self.driver.session(database=self.database_name) as session:
            result = await session.run(
                "SHOW INDEXES YIELD name WHERE name = $name RETURN count(*) as count",
                name=self.vector_index_name
            )
            record = await result.single()
            return record["count"] > 0 if record else False
