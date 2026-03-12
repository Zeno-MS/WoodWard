"""
schemas/comms_models.py
Pydantic v2 models matching the comms.db schema.
comms.db tracks outreach, right-of-reply correspondence, and publication dependencies.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


ALLOWED_ORG_TYPES = {"district", "agency", "media", "union", "advocacy", "government", "other"}


class Organization(BaseModel):
    org_id: str
    name: str
    org_type: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("org_type")
    @classmethod
    def validate_org_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_ORG_TYPES:
            raise ValueError(
                f"Invalid org_type '{v}'. Must be one of: {ALLOWED_ORG_TYPES}"
            )
        return v


class Recipient(BaseModel):
    recipient_id: str
    org_id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class QuestionSet(BaseModel):
    qset_id: str
    article_id: Optional[str] = None
    questions: Optional[str] = None  # JSON-encoded list of question strings
    created_at: Optional[str] = None


ALLOWED_THREAD_STATUSES = {
    "open", "awaiting_response", "responded", "closed", "publication_blocked"
}


class Thread(BaseModel):
    thread_id: str
    recipient_id: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_THREAD_STATUSES:
            raise ValueError(
                f"Invalid thread status '{v}'. Must be one of: {ALLOWED_THREAD_STATUSES}"
            )
        return v


ALLOWED_MESSAGE_DIRECTIONS = {"outbound", "inbound", "internal"}


class Message(BaseModel):
    msg_id: str
    thread_id: str
    direction: Optional[str] = None
    content: Optional[str] = None
    sent_at: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_MESSAGE_DIRECTIONS:
            raise ValueError(
                f"Invalid direction '{v}'. Must be one of: {ALLOWED_MESSAGE_DIRECTIONS}"
            )
        return v


ALLOWED_WINDOW_STATUSES = {"open", "expired", "responded", "waived"}


class ResponseWindow(BaseModel):
    window_id: str
    thread_id: str
    deadline: Optional[str] = None
    status: Optional[str] = None
    publication_blocking: int = Field(default=0, description="0=False, 1=True (SQLite bool)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_WINDOW_STATUSES:
            raise ValueError(
                f"Invalid window status '{v}'. Must be one of: {ALLOWED_WINDOW_STATUSES}"
            )
        return v

    @property
    def is_publication_blocking(self) -> bool:
        return self.publication_blocking == 1


ALLOWED_DEPENDENCY_TYPES = {
    "right_of_reply",
    "public_records_response",
    "agency_confirmation",
    "editorial_approval",
}


class ArticleDependency(BaseModel):
    dep_id: str
    article_id: Optional[str] = None
    thread_id: Optional[str] = None
    claim_id: Optional[str] = None
    dependency_type: Optional[str] = None
    resolved: int = Field(default=0, description="0=False, 1=True")

    @field_validator("dependency_type")
    @classmethod
    def validate_dependency_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_DEPENDENCY_TYPES:
            raise ValueError(
                f"Invalid dependency_type '{v}'. Must be one of: {ALLOWED_DEPENDENCY_TYPES}"
            )
        return v

    @property
    def is_resolved(self) -> bool:
        return self.resolved == 1
