"""
schemas/records_models.py
Pydantic v2 models matching the records.db schema.
records.db stores public documents, chunks, claims, support chains, and publication blocks.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Document(BaseModel):
    doc_id: str
    title: Optional[str] = None
    doc_type: Optional[str] = None
    source_class: Optional[str] = None
    file_path: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = None


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    chunk_index: int
    embedding_id: Optional[str] = None
    created_at: Optional[str] = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Chunk content cannot be empty")
        return v


ALLOWED_CLAIM_STATUSES = {"draft", "verified", "blocked", "superseded", "pending_review"}


class Claim(BaseModel):
    claim_id: str
    article_id: Optional[str] = None
    text: str
    status: str = "draft"
    public_citable: int = Field(default=0, description="0=False, 1=True (SQLite bool)")
    support_chain_complete: int = Field(default=0, description="0=False, 1=True")
    right_of_reply_required: int = Field(default=0, description="0=False, 1=True")
    stale: int = Field(default=0, description="0=False, 1=True")
    ingest_source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_CLAIM_STATUSES:
            raise ValueError(
                f"Invalid claim status '{v}'. Must be one of: {ALLOWED_CLAIM_STATUSES}"
            )
        return v

    @model_validator(mode="after")
    def validate_blocked_not_public(self) -> Claim:
        if self.status == "blocked" and self.public_citable == 1:
            raise ValueError(
                f"Claim '{self.claim_id}' is 'blocked' but public_citable=1. Inconsistent state."
            )
        return self

    @property
    def is_public_citable(self) -> bool:
        return self.public_citable == 1

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"

    @property
    def is_publishable(self) -> bool:
        return (
            self.is_public_citable
            and self.support_chain_complete == 1
            and not self.is_blocked
            and self.stale == 0
        )


ALLOWED_SUPPORT_TYPES = {"direct_quote", "paraphrase", "figure_reference", "context"}


class ClaimSupport(BaseModel):
    support_id: str
    claim_id: str
    doc_id: Optional[str] = None
    chunk_id: Optional[str] = None
    quote: Optional[str] = None
    support_type: Optional[str] = None
    created_at: Optional[str] = None

    @field_validator("support_type")
    @classmethod
    def validate_support_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_SUPPORT_TYPES:
            raise ValueError(
                f"Invalid support_type '{v}'. Must be one of: {ALLOWED_SUPPORT_TYPES}"
            )
        return v


class PublicationBlock(BaseModel):
    block_id: str
    claim_id: str
    article_id: Optional[str] = None
    reason: str
    blocking_since: Optional[str] = None
    resolved_at: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.resolved_at is None
