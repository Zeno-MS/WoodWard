"""
src/core/settings.py
Application settings for Woodward Core v2.
Uses pydantic-settings for env-var loading from .env.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WoodwardSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WOODWARD_",
        extra="ignore",
    )

    # LLM Provider keys (no prefix — they come from provider env vars)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")

    # Runtime environment
    env: str = Field(default="development", alias="WOODWARD_ENV")
    investigation: str = Field(default="vps_2026", alias="WOODWARD_INVESTIGATION")

    # Path configuration
    db_path: str = Field(default="./db", alias="WOODWARD_DB_PATH")
    canonical_path: str = Field(default="./canonical", alias="WOODWARD_CANONICAL_PATH")
    runs_path: str = Field(default="./runs", alias="WOODWARD_RUNS_PATH")
    lancedb_path: str = Field(default="./lancedb", alias="WOODWARD_LANCEDB_PATH")

    # Log level
    log_level: str = Field(default="INFO", alias="WOODWARD_LOG_LEVEL")

    # Model defaults — these are non-negotiable defaults per isolation rules
    # Default embeddings must be OpenAI text-embedding-3-small (NOT kanon-2)
    default_embedding_model: str = "text-embedding-3-small"
    default_llm_model: str = "gpt-4o"

    @property
    def db_path_obj(self) -> Path:
        return Path(self.db_path)

    @property
    def canonical_path_obj(self) -> Path:
        return Path(self.canonical_path)

    @property
    def runs_path_obj(self) -> Path:
        return Path(self.runs_path)

    @property
    def lancedb_path_obj(self) -> Path:
        return Path(self.lancedb_path)

    @property
    def ledger_db_path(self) -> Path:
        return self.db_path_obj / "ledger.db"

    @property
    def records_db_path(self) -> Path:
        return self.db_path_obj / "records.db"

    @property
    def comms_db_path(self) -> Path:
        return self.db_path_obj / "comms.db"

    @property
    def backups_path_obj(self) -> Path:
        return self.db_path_obj.parent / "backups"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


# Module-level singleton — use get_settings() to allow override in tests
_settings: Optional[WoodwardSettings] = None


def get_settings() -> WoodwardSettings:
    global _settings
    if _settings is None:
        _settings = WoodwardSettings()
    return _settings


def reset_settings() -> None:
    """Reset the singleton — used in tests to reload from a different .env."""
    global _settings
    _settings = None
