"""
tests/unit/test_public_source_gate.py
Unit tests for PublicSourceGate.
"""
from __future__ import annotations

import pytest

from schemas.canonical import SourcePolicy, SourcePolicyEntry
from schemas.records_models import Claim
from src.core.exceptions import BlockedClaimError
from src.services.public_source_gate import PublicSourceGate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_policy() -> SourcePolicy:
    """Full source policy matching the canonical source_policy.yaml."""
    return SourcePolicy(
        source_classes=[
            SourcePolicyEntry(
                source_class="public_record",
                status="allowed",
                description="Official government documents",
                citation_requirement="Document title and date",
            ),
            SourcePolicyEntry(
                source_class="public_reporting",
                status="allowed",
                description="Published journalism",
                citation_requirement="Publication and date",
            ),
            SourcePolicyEntry(
                source_class="public_records_response",
                status="allowed",
                description="PRR response documents",
                citation_requirement="PRR reference number",
            ),
            SourcePolicyEntry(
                source_class="public_agency_finding",
                status="allowed",
                description="Official agency findings",
                citation_requirement="Agency and document title",
            ),
            SourcePolicyEntry(
                source_class="internal_nonpublic",
                status="blocked",
                description="Internal non-public documents",
                citation_requirement="N/A — BLOCKED",
            ),
            SourcePolicyEntry(
                source_class="memory_only",
                status="blocked",
                description="AI memory only",
                citation_requirement="N/A — BLOCKED",
            ),
            SourcePolicyEntry(
                source_class="insider_awareness",
                status="blocked",
                description="Confidential insider information",
                citation_requirement="N/A — BLOCKED",
            ),
            SourcePolicyEntry(
                source_class="webapp_export",
                status="pending_review",
                description="Webapp export — requires review",
                citation_requirement="N/A until reviewed",
            ),
        ]
    )


@pytest.fixture
def gate() -> PublicSourceGate:
    return PublicSourceGate()


def _make_claim(
    claim_id: str = "c1",
    status: str = "verified",
    public_citable: int = 1,
    support_chain_complete: int = 1,
    right_of_reply_required: int = 0,
    stale: int = 0,
    ingest_source: str = "canonical_seed",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        article_id="article_1",
        text=f"Test claim {claim_id}",
        status=status,
        public_citable=public_citable,
        support_chain_complete=support_chain_complete,
        right_of_reply_required=right_of_reply_required,
        stale=stale,
        ingest_source=ingest_source,
    )


# ---------------------------------------------------------------------------
# Tests: is_allowed
# ---------------------------------------------------------------------------

def test_public_record_is_allowed(gate: PublicSourceGate, full_policy: SourcePolicy) -> None:
    assert gate.is_allowed("public_record", full_policy) is True


def test_public_reporting_is_allowed(gate: PublicSourceGate, full_policy: SourcePolicy) -> None:
    assert gate.is_allowed("public_reporting", full_policy) is True


def test_public_records_response_is_allowed(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    assert gate.is_allowed("public_records_response", full_policy) is True


def test_internal_nonpublic_is_blocked(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    assert gate.is_allowed("internal_nonpublic", full_policy) is False


def test_memory_only_is_blocked(gate: PublicSourceGate, full_policy: SourcePolicy) -> None:
    assert gate.is_allowed("memory_only", full_policy) is False


def test_insider_awareness_is_blocked(gate: PublicSourceGate, full_policy: SourcePolicy) -> None:
    assert gate.is_allowed("insider_awareness", full_policy) is False


def test_pending_review_is_not_canonical(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """webapp_export is pending_review — not allowed for publication."""
    assert gate.is_allowed("webapp_export", full_policy) is False


def test_unknown_source_class_is_not_allowed(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """Unknown source classes must not be allowed (fail-safe)."""
    assert gate.is_allowed("totally_unknown_class", full_policy) is False  # type: ignore


# ---------------------------------------------------------------------------
# Tests: filter_claims
# ---------------------------------------------------------------------------

def test_filter_claims_returns_only_publishable(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """Only fully verified, public-citable, support-complete, non-stale claims pass."""
    publishable = _make_claim("c1", status="verified", public_citable=1, support_chain_complete=1)
    blocked_claim = _make_claim("c2", status="blocked", public_citable=0)
    draft_claim = _make_claim("c3", status="draft", public_citable=0)
    stale_claim = _make_claim("c4", status="verified", public_citable=1, support_chain_complete=1, stale=1)

    result = gate.filter_claims(
        [publishable, blocked_claim, draft_claim, stale_claim], full_policy
    )

    assert len(result) == 1
    assert result[0].claim_id == "c1"


def test_filter_claims_removes_blocked(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """Blocked claims must not appear in filtered output."""
    claims = [
        _make_claim("c1", status="verified", public_citable=1, support_chain_complete=1),
        _make_claim("c2", status="blocked", public_citable=0, support_chain_complete=0),
    ]
    result = gate.filter_claims(claims, full_policy)
    claim_ids = [c.claim_id for c in result]
    assert "c2" not in claim_ids
    assert "c1" in claim_ids


def test_filter_claims_removes_webapp_exports(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """webapp_export claims must never pass the publication filter."""
    webapp_claim = _make_claim(
        "c_webapp",
        status="verified",
        public_citable=1,
        support_chain_complete=1,
        ingest_source="webapp_export",
    )
    result = gate.filter_claims([webapp_claim], full_policy)
    assert len(result) == 0


def test_filter_claims_empty_input(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """Empty input must return empty output."""
    result = gate.filter_claims([], full_policy)
    assert result == []


# ---------------------------------------------------------------------------
# Tests: gate_draft_context
# ---------------------------------------------------------------------------

def test_gate_draft_context_passes_verified_claims(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """Verified claims must pass through gate_draft_context."""
    claim = _make_claim("c1", status="verified", public_citable=1)
    result = gate.gate_draft_context([claim], full_policy)
    assert len(result) == 1


def test_gate_draft_context_raises_on_critical_blocked_claim(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """A blocked claim with right_of_reply_required=1 must raise BlockedClaimError."""
    critical_blocked = _make_claim(
        "c_blocked",
        status="blocked",
        public_citable=0,
        right_of_reply_required=1,
    )

    with pytest.raises(BlockedClaimError) as exc_info:
        gate.gate_draft_context([critical_blocked], full_policy)

    assert "c_blocked" in str(exc_info.value)


def test_gate_draft_context_silently_drops_non_critical_blocked(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """A blocked claim with right_of_reply_required=0 is silently dropped (no exception)."""
    non_critical_blocked = _make_claim(
        "c_blocked_nc",
        status="blocked",
        public_citable=0,
        right_of_reply_required=0,
    )
    result = gate.gate_draft_context([non_critical_blocked], full_policy)
    assert len(result) == 0


def test_gate_draft_context_drops_webapp_exports(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """webapp_export claims must never enter LLM draft context."""
    webapp_claim = _make_claim("c_wa", status="draft", ingest_source="webapp_export")
    result = gate.gate_draft_context([webapp_claim], full_policy)
    assert len(result) == 0


def test_gate_draft_context_drops_pending_review(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """pending_review claims must not enter draft context."""
    pending = _make_claim("c_pr", status="pending_review", public_citable=0)
    result = gate.gate_draft_context([pending], full_policy)
    assert len(result) == 0


def test_gate_draft_context_drops_stale(
    gate: PublicSourceGate, full_policy: SourcePolicy
) -> None:
    """Stale claims must be dropped from draft context."""
    stale = _make_claim("c_stale", status="verified", stale=1)
    result = gate.gate_draft_context([stale], full_policy)
    assert len(result) == 0
