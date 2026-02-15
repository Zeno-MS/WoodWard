from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class SourceType(Enum):
    """Type of retrieval source"""
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    SKILL = "skill"

@dataclass
class RetrievalResult:
    """
    Universal result format from any database.
    
    CRITICAL: All scores MUST be normalized to 0-1 where 1 = most relevant.
    Adapters are responsible for this normalization.
    """
    # Core content
    content: str                              # The actual text chunk
    score: float                              # Relevance score (0-1, 1 = best)
    
    # Source tracking
    source_type: SourceType                   # How this was retrieved
    database: str                             # 'lancedb', 'neo4j', etc.
    
    # Citation/Provenance (REQUIRED for legal RAG)
    source_document_id: str                   # Original document this came from
    citation_key: str                         # e.g., "State v. Gunwall, 106 Wn.2d 54, 58"
    chunk_index: Optional[int] = None         # Position in original document
    page_or_paragraph: Optional[str] = None   # For precise citation
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    
    # Workspace/Matter isolation
    workspace_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate score is normalized"""
        if not 0.0 <= self.score <= 1.0:
            # Allow small float error or warn effectively, but for now strict raise
            # to catch adapter bugs early.
            # Using 1.000001 constraint for float precision safety if needed, 
            # but strict 0-1 is better for finding bugs.
            if self.score > 1.0 and self.score < 1.0001:
                self.score = 1.0
            elif self.score < 0.0 and self.score > -0.0001:
                self.score = 0.0
            
            if not 0.0 <= self.score <= 1.0:
                 raise ValueError(f"Score must be 0-1, got {self.score}")

@dataclass
class StoreResult:
    """Result from storing a document"""
    item_id: str
    success: bool
    database: str
    error: Optional[str] = None
