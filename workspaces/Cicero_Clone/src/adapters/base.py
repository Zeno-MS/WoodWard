from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.types import RetrievalResult, StoreResult, SourceType

class DatabaseAdapter(ABC):
    """
    Abstract base class that ALL database adapters must implement.
    
    This is your contract: any database (vector, graph, SQL, etc.) 
    must provide these methods.
    
    CRITICAL REQUIREMENTS:
    1. All retrieve() scores MUST be normalized to 0-1 (1 = most relevant)
    2. All results MUST include citation_key and source_document_id
    3. Workspace filtering MUST be supported
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this adapter (e.g., 'lancedb', 'neo4j')"""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Type of retrieval source this adapter provides"""
        pass
    
    # === Connection Management ===
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to database"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection gracefully"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if database is reachable and healthy.
        
        MUST:
        - Return within 2 seconds (use timeout)
        - Return False on any exception
        - Not raise exceptions
        """
        pass
    
    # === Single Item Operations ===
    
    @abstractmethod
    async def store(self, 
                   content: str, 
                   embedding: List[float], 
                   metadata: Dict[str, Any],
                   source_document_id: str,
                   citation_key: str,
                   workspace_id: Optional[str] = None) -> StoreResult:
        """
        Store content with embedding and metadata.
        """
        pass
    
    @abstractmethod
    async def retrieve(self, 
                      query: str, 
                      query_embedding: Optional[List[float]] = None,
                      top_k: int = 5,
                      filters: Optional[Dict[str, Any]] = None,
                      workspace_id: Optional[str] = None) -> List[RetrievalResult]:
        """
        Retrieve relevant items based on query.
        
        CRITICAL: Scores MUST be normalized to 0-1 where 1 = most relevant.
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete item by ID"""
        pass
    
    # === Batch Operations (REQUIRED for ingestion) ===
    
    @abstractmethod
    async def store_batch(self,
                         items: List[Dict[str, Any]],
                         batch_size: int = 100) -> List[StoreResult]:
        """
        Store multiple items efficiently.
        """
        pass
    
    @abstractmethod
    async def retrieve_batch(self,
                            queries: List[str],
                            query_embeddings: List[List[float]],
                            top_k: int = 5,
                            workspace_id: Optional[str] = None) -> List[List[RetrievalResult]]:
        """
        Retrieve for multiple queries efficiently.
        """
        pass
    
    # === Optional: Not all databases will implement these ===
    
    async def get_schema(self) -> Dict[str, Any]:
        """Return database schema (for graph DBs)"""
        raise NotImplementedError("This adapter doesn't support schema retrieval")
    
    async def execute_custom_query(self, query: str, params: Dict[str, Any]) -> List[Dict]:
        """Execute database-specific query (Cypher for Neo4j, SQL for Postgres, etc.)"""
        raise NotImplementedError("This adapter doesn't support custom queries")
    
    async def delete_by_workspace(self, workspace_id: str) -> int:
        """Delete all items in a workspace. Returns count of deleted items."""
        raise NotImplementedError("This adapter doesn't support workspace deletion")
    
    async def count(self, workspace_id: Optional[str] = None) -> int:
        """Return count of items, optionally filtered by workspace"""
        raise NotImplementedError("This adapter doesn't support counting")
