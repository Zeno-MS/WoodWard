"""
schemas/canonical.py
Pydantic v2 models for canonical YAML files.
These models are the authoritative Python representation of canonical/*.yaml.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# SchemaVersion
# ---------------------------------------------------------------------------

class SchemaVersion(BaseModel):
    schema_version: str
    created: str
    investigation: str
    locked_by: str


# ---------------------------------------------------------------------------
# CanonicalFigure
# ---------------------------------------------------------------------------

ALLOWED_FIGURE_STATUSES = {"locked", "provisional", "superseded"}


class CanonicalFigure(BaseModel):
    figure_id: str = Field(..., description="snake_case unique identifier")
    display_label: str
    value: float = Field(..., description="Exact numeric value (no formatting)")
    display_value: str = Field(..., description="Human-readable formatted string, e.g. '$13,326,622'")
    fiscal_year: Optional[str] = None
    date_context: Optional[str] = None
    source_of_truth: str
    derivation_id: str
    status: str
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_FIGURE_STATUSES:
            raise ValueError(
                f"Invalid figure status '{v}'. Must be one of: {ALLOWED_FIGURE_STATUSES}"
            )
        return v

    @field_validator("value")
    @classmethod
    def validate_value_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Figure value must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_fiscal_or_date_context(self) -> CanonicalFigure:
        if not self.fiscal_year and not self.date_context:
            raise ValueError(
                f"Figure '{self.figure_id}' must have either fiscal_year or date_context"
            )
        return self


# ---------------------------------------------------------------------------
# VendorScope
# ---------------------------------------------------------------------------

class RebrandHistory(BaseModel):
    from_name: str = Field(..., alias="from")
    to: str
    effective_date: str

    model_config = {"populate_by_name": True}


class VendorAlias(BaseModel):
    """Simple alias model used in deserialization. YAML stores aliases as plain list[str]."""
    alias: str


class VendorScope(BaseModel):
    vendor_id: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    rebrand_history: list[RebrandHistory] = Field(default_factory=list)
    canonical_total_included: bool
    notes: Optional[str] = None

    @field_validator("vendor_id")
    @classmethod
    def validate_vendor_id_snake_case(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(f"vendor_id must be snake_case, got '{v}'")
        return v


# ---------------------------------------------------------------------------
# ArticleRecord
# ---------------------------------------------------------------------------

ALLOWED_ARTICLE_STATUSES = {"locked_baseline", "draft", "published"}


class ArticleRecord(BaseModel):
    article_id: str
    title: str
    status: str
    file_path: str
    locked: bool
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_ARTICLE_STATUSES:
            raise ValueError(
                f"Invalid article status '{v}'. Must be one of: {ALLOWED_ARTICLE_STATUSES}"
            )
        return v


# ---------------------------------------------------------------------------
# ClaimRecord
# ---------------------------------------------------------------------------

ALLOWED_CLAIM_STATUSES = {"draft", "verified", "blocked", "superseded", "pending_review"}


class ClaimRecord(BaseModel):
    claim_id: str
    text: str
    article_id: str
    status: str
    public_citable: bool
    support_chain_complete: bool
    right_of_reply_required: bool
    stale: bool
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_CLAIM_STATUSES:
            raise ValueError(
                f"Invalid claim status '{v}'. Must be one of: {ALLOWED_CLAIM_STATUSES}"
            )
        return v

    @model_validator(mode="after")
    def validate_publication_consistency(self) -> ClaimRecord:
        """
        A claim that is public_citable=True must not be blocked.
        A claim that is blocked must not be public_citable=True.
        """
        if self.status == "blocked" and self.public_citable:
            raise ValueError(
                f"Claim '{self.claim_id}' is 'blocked' but has public_citable=True. "
                "A blocked claim cannot be marked as public-citable."
            )
        if self.status == "verified" and not self.support_chain_complete:
            raise ValueError(
                f"Claim '{self.claim_id}' is 'verified' but support_chain_complete=False. "
                "A verified claim must have a complete support chain."
            )
        return self


# ---------------------------------------------------------------------------
# BannedClaim
# ---------------------------------------------------------------------------

class BannedClaim(BaseModel):
    ban_id: str
    text_pattern: str
    reason: str
    added_date: str


# ---------------------------------------------------------------------------
# SourcePolicy
# ---------------------------------------------------------------------------

ALLOWED_SOURCE_STATUSES = {"allowed", "blocked", "pending_review"}


class SourcePolicyEntry(BaseModel):
    source_class: str
    status: str
    description: str
    citation_requirement: str
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(
                f"Invalid source policy status '{v}'. Must be one of: {ALLOWED_SOURCE_STATUSES}"
            )
        return v


class SourcePolicy(BaseModel):
    source_classes: list[SourcePolicyEntry]

    def is_allowed(self, source_class: str) -> bool:
        for entry in self.source_classes:
            if entry.source_class == source_class:
                return entry.status == "allowed"
        return False

    def get_status(self, source_class: str) -> Optional[str]:
        for entry in self.source_classes:
            if entry.source_class == source_class:
                return entry.status
        return None


# ---------------------------------------------------------------------------
# CanonManifest
# ---------------------------------------------------------------------------

class CanonManifest(BaseModel):
    """Top-level container holding all loaded canonical state."""
    schema_version: SchemaVersion
    figures: list[CanonicalFigure]
    vendors: list[VendorScope]
    articles: list[ArticleRecord]
    claims: list[ClaimRecord]
    banned_claims: list[BannedClaim]
    source_policy: SourcePolicy

    def get_figure(self, figure_id: str) -> Optional[CanonicalFigure]:
        for f in self.figures:
            if f.figure_id == figure_id:
                return f
        return None

    def get_vendor(self, vendor_id: str) -> Optional[VendorScope]:
        for v in self.vendors:
            if v.vendor_id == vendor_id:
                return v
        return None

    def get_article(self, article_id: str) -> Optional[ArticleRecord]:
        for a in self.articles:
            if a.article_id == article_id:
                return a
        return None

    def get_claim(self, claim_id: str) -> Optional[ClaimRecord]:
        for c in self.claims:
            if c.claim_id == claim_id:
                return c
        return None

    def get_locked_figures(self) -> list[CanonicalFigure]:
        return [f for f in self.figures if f.status == "locked"]

    def get_claims_for_article(self, article_id: str) -> list[ClaimRecord]:
        return [c for c in self.claims if c.article_id == article_id]
