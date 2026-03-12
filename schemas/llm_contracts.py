"""
schemas/llm_contracts.py
Pydantic v2 models for structured LLM input/output contracts.
Every LLM call in Woodward must use one of these models as its output schema.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# FactualAssertion
# ---------------------------------------------------------------------------

class FactualAssertion(BaseModel):
    """A single factual claim made in draft output that must be verifiable."""
    text: str                          # The exact sentence or clause
    context_ids: list[str] = Field(default_factory=list)   # IDs of records/chunks that support this
    claim_ids: list[str] = Field(default_factory=list)     # IDs from claims registry
    figure_ids: list[str] = Field(default_factory=list)    # IDs of any locked figures used
    confidence: Literal["high", "medium", "low"] = "high"

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("FactualAssertion text cannot be empty")
        return v.strip()

    def has_support(self) -> bool:
        """Returns True if the assertion has at least one supporting reference."""
        return bool(self.context_ids or self.claim_ids or self.figure_ids)


# ---------------------------------------------------------------------------
# DraftSectionResponse
# ---------------------------------------------------------------------------

class DraftSectionMetadata(BaseModel):
    model: str = Field(..., description="LLM model identifier used for this draft")
    temperature: Optional[float] = None
    run_id: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    token_count: Optional[int] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DraftSectionResponse(BaseModel):
    """Structured output contract for article_drafter LLM call."""
    section_id: str
    article_id: str
    content: str                       # The draft prose (Markdown)
    assertions: list[FactualAssertion] = Field(default_factory=list)  # Every factual sentence mapped
    unresolved_questions: list[str] = Field(default_factory=list)     # Questions that remain open (not stated as facts)
    right_of_reply_flags: list[str] = Field(default_factory=list)     # Claims needing right-of-reply before publication
    figures_used: list[str] = Field(default_factory=list)             # figure_ids referenced in content
    word_count: int = 0
    metadata: Optional[DraftSectionMetadata] = None

    @field_validator("assertions")
    @classmethod
    def assertions_must_have_support(cls, v: list[FactualAssertion]) -> list[FactualAssertion]:
        for a in v:
            if not a.context_ids and not a.claim_ids and not a.figure_ids:
                raise ValueError(f"Assertion has no support: '{a.text[:60]}'")
        return v

    def get_unsupported_assertions(self) -> list[FactualAssertion]:
        """Returns assertions with no support chain — these fail build."""
        return [a for a in self.assertions if not a.has_support()]

    def passes_support_check(self) -> bool:
        return len(self.get_unsupported_assertions()) == 0


# ---------------------------------------------------------------------------
# AdversarialFinding
# ---------------------------------------------------------------------------

FINDING_SEVERITIES = {"blocker", "warning", "note"}

FINDING_CATEGORIES = {
    "overclaim",           # States as fact something that is uncertain
    "unsupported_math",    # Figure used without declared derivation
    "scope_drift",         # Vendor scope not declared
    "weak_attribution",    # Source not specified
    "right_of_reply_gap",  # Claim needs right-of-reply not yet obtained
    "motive_language",     # Attributes intent or motive without public evidence
    "denominator_issue",   # Mixes budget/actual without disclosure
    "hallucinated_context" # context_id does not resolve to a real record
}


class AdversarialFinding(BaseModel):
    finding_id: str
    severity: Literal["blocker", "warning", "note"]
    category: Literal[
        "overclaim",
        "unsupported_math",
        "scope_drift",
        "weak_attribution",
        "right_of_reply_gap",
        "motive_language",
        "denominator_issue",
        "hallucinated_context"
    ]
    description: str
    affected_text: str             # The specific sentence flagged
    affected_claim_id: Optional[str] = None  # If tied to a specific claim
    suggestion: Optional[str] = None         # How to fix (optional)

    # Legacy aliases retained for backward compatibility
    @property
    def affected_assertion_text(self) -> str:
        return self.affected_text

    @property
    def remediation_suggestion(self) -> Optional[str]:
        return self.suggestion

    @property
    def is_blocker(self) -> bool:
        return self.severity == "blocker"


# ---------------------------------------------------------------------------
# AdversarialReviewResponse
# ---------------------------------------------------------------------------

class AdversarialReviewResponse(BaseModel):
    """Structured output contract for adversarial_review LLM call."""
    section_id: str
    article_id: Optional[str] = None
    findings: list[AdversarialFinding] = Field(default_factory=list)
    blocker_count: int = 0
    warning_count: int = 0
    pass_build: bool = False               # True only if blocker_count == 0
    reviewer_notes: str = ""               # Brief prose summary
    reviewed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reviewer_model: Optional[str] = None

    @field_validator("pass_build")
    @classmethod
    def pass_requires_no_blockers(cls, v: bool, info: Any) -> bool:
        data = info.data if hasattr(info, "data") else {}
        if data.get("blocker_count", 0) > 0 and v:
            raise ValueError("pass_build cannot be True when blocker_count > 0")
        return v

    def get_blockers(self) -> list[AdversarialFinding]:
        return [f for f in self.findings if f.is_blocker]

    def get_warnings(self) -> list[AdversarialFinding]:
        return [f for f in self.findings if f.severity == "warning"]

    # Keep as method for backward compatibility (was a method in prior version)
    def blocker_count_computed(self) -> int:
        return len(self.get_blockers())

    # Legacy accessor
    @property
    def summary(self) -> str:
        return self.reviewer_notes


# ---------------------------------------------------------------------------
# ReplyPacketResponse
# ---------------------------------------------------------------------------

class ReplyPacketResponse(BaseModel):
    """Structured output for right-of-reply packet assembly."""
    thread_id: str
    recipient_name: str
    article_id: str
    questions: list[str] = Field(default_factory=list)           # Specific questions for right of reply
    affected_claims: list[str] = Field(default_factory=list)     # claim_ids that depend on this response
    deadline_recommendation: str = ""   # e.g., "10 business days"
    packet_markdown: str = ""           # The full letter/email text
    publication_blocking: bool = False  # True if publication should wait for response
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Legacy aliases for backward compatibility
    @property
    def recipient(self) -> str:
        return self.recipient_name

    @property
    def outstanding_claims(self) -> list[str]:
        return self.affected_claims

    @property
    def deadline(self) -> str:
        return self.deadline_recommendation


# ---------------------------------------------------------------------------
# ContextPacket
# ---------------------------------------------------------------------------

class ContextPacket(BaseModel):
    """What gets assembled and passed to the LLM drafter."""
    article_id: str
    section_id: str
    run_id: str
    task_profile: Literal["article_draft", "figure_verification", "adversarial_review", "reply_packet"]
    # Injected from canon — LLM sees these as ground truth, cannot change them
    locked_figures: dict[str, str] = Field(default_factory=dict)  # {figure_id: display_value}
    # Filtered claims — only draftable ones (blocked/pending stripped)
    draftable_claims: list[dict] = Field(default_factory=list)    # Serialized Claim objects
    # Support context — chunks/docs supporting the claims
    support_context: list[dict] = Field(default_factory=list)     # {chunk_id, content, doc_title, source_class}
    # System instructions injected by task profile
    task_instructions: str = ""
    canon_hash: str = ""                 # Hash at time of assembly
