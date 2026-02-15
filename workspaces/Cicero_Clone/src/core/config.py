from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Literal

class Settings(BaseSettings):
    """
    Application configuration (loaded from environment variables).
    
    Uses pydantic-settings for Pydantic v2 compatibility.
    """
    
    # LanceDB config (Strictly Local)
    LANCEDB_PATH: str = Field(
        default="./data/vectors", 
        description="Path to WoodWard LanceDB data"
    )
    LANCEDB_TABLE: str = Field(default="woodward_contracts", description="LanceDB table name")
    
    # Neo4j config (Strictly Local)
    NEO4J_URI: str = Field(..., description="Neo4j connection URI")
    NEO4J_USERNAME: str = Field(default="neo4j", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(..., description="Neo4j password")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j database name")
    
    # REMOVED: CaseLawDB and BrainBase configurations to ensure strict isolation.
    # This agent (General Counsel) should NOT have access to those knowledge graphs.
    
    # Embedding config
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small", 
        description="Embedding model name"
    )
    EMBEDDING_DIM: int = Field(default=1536, description="Embedding dimension")
    EMBEDDING_PROVIDER: Literal["openai", "google", "local", "isaacus"] = Field(
        default="openai", 
        description="Embedding provider"
    )
    EMBEDDING_CACHE_SIZE: int = Field(
        default=10000, 
        description="Embedding cache size"
    )
    
    # API keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ISAACUS_API_KEY: Optional[str] = Field(default=None, description="Isaacus API key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google API key")
    COURTLISTENER_API_TOKEN: Optional[str] = Field(default=None, description="CourtListener API Token")
    
    # Redis (optional)
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for distributed cache")

    # LLM Provider
    LLM_PROVIDER: Literal["openai", "anthropic", "none"] = Field(
        default="openai",
        description="LLM Provider for query routing"
    )
    
    # Retrieval config
    DEFAULT_TOP_K: int = Field(default=10, description="Default number of results")
    DEFAULT_STRATEGY: Literal["auto", "vector_only", "graph_only", "hybrid"] = Field(
        default="auto", 
        description="Default retrieval strategy"
    )
    HEALTH_CHECK_TIMEOUT: float = Field(
        default=2.0, 
        description="Adapter health check timeout"
    )
    RETRIEVAL_TIMEOUT: float = Field(
        default=10.0, 
        description="Parallel retrieval timeout"
    )
    
    # Context building
    MAX_CONTEXT_TOKENS: int = Field(
        default=12000, 
        description="Maximum context tokens"
    )
    MAX_TOTAL_TOKENS: int = Field(
        default=16000, 
        description="Maximum total prompt tokens"
    )
    
    # Council of Models Config
    MODEL_ORCHESTRATOR: str = Field(default="gemini-3-pro-preview", description="Orchestrator Model")
    MODEL_RESEARCHER: str = Field(default="gemini-3-flash-preview", description="Researcher Model")
    MODEL_LOGICIAN: str = Field(default="o3", description="Logician Model")
    MODEL_HISTORIAN: str = Field(default="gemini-3-pro-preview", description="Historian Model")
    MODEL_ORATOR: str = Field(default="gpt-5.2", description="Orator Model")
    MODEL_FACT_CHECKER: str = Field(default="gpt-4.1-2025-04-14", description="Fact Checker Model")
    MODEL_JUDGE: str = Field(default="gpt-5.2", description="Judge Model")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Ignore extra env vars
    }


# Global settings instance
settings = Settings()
