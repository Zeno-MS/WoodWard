"""
src/tests/unit/test_publication_gate.py
Unit tests for PublicationGate.
Uses mock repos and a minimal CanonManifest.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from schemas.canonical import (
    ArticleRecord,
    BannedClaim,
    CanonicalFigure,
    CanonManifest,
    ClaimRecord,
    SchemaVersion,
    SourcePolicy,
    VendorScope,
)
from schemas.comms_models import ArticleDependency, ResponseWindow
from schemas.records_models import Claim, PublicationBlock
from src.core.exceptions import PublicationBlockedError
from src.services.publication_gate import PublicationGate, PublicationGateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_schema_version() -> SchemaVersion:
    return SchemaVersion(
        schema_version="1.0",
        created="2026-03-12",
        investigation="vps_2026",
        locked_by="architect",
    )


def _make_source_policy() -> SourcePolicy:
    return SourcePolicy(source_classes=[])


def _make_canon(figures: list[CanonicalFigure] | None = None) -> CanonManifest:
    if figures is None:
        figures = []
    return CanonManifest(
        schema_version=_make_schema_version(),
        figures=figures,
        vendors=[],
        articles=[],
        claims=[],
        banned_claims=[],
        source_policy=_make_source_policy(),
    )


def _make_figure(figure_id: str) -> CanonicalFigure:
    return CanonicalFigure(
        figure_id=figure_id,
        display_label=f"Label {figure_id}",
        value=1000000.0,
        display_value="$1,000,000",
        fiscal_year="FY2024-25",
        source_of_truth="ledger.db",
        derivation_id=f"deriv_{figure_id}",
        status="locked",
    )


def _make_blocked_claim(claim_id: str, article_id: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        article_id=article_id,
        text=f"Blocked claim: {claim_id}",
        status="blocked",
        public_citable=0,
        support_chain_complete=0,
        right_of_reply_required=1,
        stale=0,
        ingest_source="canonical_seed",
    )


def _make_pub_block(block_id: str, claim_id: str, article_id: str) -> PublicationBlock:
    return PublicationBlock(
        block_id=block_id,
        claim_id=claim_id,
        article_id=article_id,
        reason="Awaiting PRR response.",
        blocking_since="2026-03-01",
        resolved_at=None,
    )


def _make_response_window(
    window_id: str,
    thread_id: str,
    publication_blocking: int = 1,
    status: str = "open",
) -> ResponseWindow:
    return ResponseWindow(
        window_id=window_id,
        thread_id=thread_id,
        deadline="2026-03-20",
        status=status,
        publication_blocking=publication_blocking,
    )


def _make_dep(dep_id: str, article_id: str, thread_id: str, resolved: int = 0) -> ArticleDependency:
    return ArticleDependency(
        dep_id=dep_id,
        article_id=article_id,
        thread_id=thread_id,
        claim_id="claim_1",
        dependency_type="right_of_reply",
        resolved=resolved,
    )


def _make_records(
    blocked_claims: list[Claim] | None = None,
    active_blocks: list[PublicationBlock] | None = None,
) -> MagicMock:
    records = MagicMock()
    records.get_blocked_claims = AsyncMock(return_value=blocked_claims or [])
    records.get_active_blocks = AsyncMock(return_value=active_blocks or [])
    return records


def _make_comms(
    blocking_windows: list[ResponseWindow] | None = None,
    unresolved_deps: list[ArticleDependency] | None = None,
) -> MagicMock:
    comms = MagicMock()
    comms.get_publication_blocking_windows = AsyncMock(return_value=blocking_windows or [])
    comms.get_unresolved_dependencies = AsyncMock(return_value=unresolved_deps or [])
    return comms


def _make_ledger() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_passes_with_no_blocked_claims():
    """Gate passes when there are no blocked claims, blocks, or RoR windows."""
    records = _make_records()
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result = await gate.check("article_clean", records, comms, ledger, canon)

    assert result.passed is True
    assert result.failure_reasons == []
    assert result.blocked_claim_count == 0
    assert result.unresolved_ror_count == 0
    assert result.article_id == "article_clean"


@pytest.mark.asyncio
async def test_gate_fails_with_blocked_claim():
    """Gate fails when blocked claims exist for the article."""
    blocked = [_make_blocked_claim("claim_amergis_no_spending_cap", "article_1")]
    records = _make_records(blocked_claims=blocked)
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result = await gate.check("article_1", records, comms, ledger, canon)

    assert result.passed is False
    assert result.blocked_claim_count == 1
    assert any("Blocked claims" in r for r in result.failure_reasons)


@pytest.mark.asyncio
async def test_gate_fails_with_active_publication_block():
    """Gate fails when there are unresolved publication_blocks."""
    pub_block = _make_pub_block("block_1", "claim_no_bid", "article_1")
    records = _make_records(active_blocks=[pub_block])
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result = await gate.check("article_1", records, comms, ledger, canon)

    assert result.passed is False
    assert any("publication_blocks" in r for r in result.failure_reasons)


@pytest.mark.asyncio
async def test_gate_fails_with_unresolved_ror():
    """Gate fails when there are unresolved publication-blocking RoR threads."""
    dep = _make_dep("dep_1", "article_1", "thread_sao", resolved=0)
    window = _make_response_window("rw_1", "thread_sao", publication_blocking=1)

    records = _make_records()
    comms = _make_comms(blocking_windows=[window], unresolved_deps=[dep])
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result = await gate.check("article_1", records, comms, ledger, canon)

    assert result.passed is False
    assert result.unresolved_ror_count == 1
    assert any("right-of-reply" in r for r in result.failure_reasons)


@pytest.mark.asyncio
async def test_gate_fails_with_unlocked_figure():
    """Gate fails when draft references a figure not in canon locked_figures."""
    from schemas.llm_contracts import DraftSectionResponse

    draft_resp = DraftSectionResponse(
        section_id="sec_1",
        article_id="article_1",
        content="VPS spent [fig:mystery_figure] on contractors.",
        assertions=[],
        figures_used=["mystery_figure"],
    )

    draft_result = MagicMock()
    draft_result.draft = draft_resp

    records = _make_records()
    comms = _make_comms()
    ledger = _make_ledger()
    # Canon has no locked figures
    canon = _make_canon(figures=[])

    gate = PublicationGate()
    result = await gate.check(
        "article_1", records, comms, ledger, canon, draft_result=draft_result
    )

    assert result.passed is False
    assert result.unlocked_figure_count == 1
    assert any("mystery_figure" in r for r in result.failure_reasons)


@pytest.mark.asyncio
async def test_gate_fails_with_adversarial_blocker():
    """Gate fails when review_result has unresolved blockers."""
    review_result = MagicMock()
    review_result.blocker_ids = ["finding_1", "finding_2"]

    records = _make_records()
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result = await gate.check(
        "article_1", records, comms, ledger, canon, review_result=review_result
    )

    assert result.passed is False
    assert result.review_blocker_count == 2
    assert any("blocker" in r for r in result.failure_reasons)


@pytest.mark.asyncio
async def test_assert_passes_raises_on_failure():
    """assert_passes() raises PublicationBlockedError when gate fails."""
    blocked = [_make_blocked_claim("claim_1", "article_1")]
    records = _make_records(blocked_claims=blocked)
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    with pytest.raises(PublicationBlockedError) as exc_info:
        await gate.assert_passes("article_1", records, comms, ledger, canon)

    assert "article_1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_assert_passes_does_not_raise_when_clean():
    """assert_passes() does not raise when gate passes."""
    records = _make_records()
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    # Should not raise
    await gate.assert_passes("article_clean", records, comms, ledger, canon)


@pytest.mark.asyncio
async def test_gate_result_is_deterministic():
    """Same inputs produce identical gate result (no randomness)."""
    records = _make_records()
    comms = _make_comms()
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result_a = await gate.check("article_1", records, comms, ledger, canon)
    result_b = await gate.check("article_1", records, comms, ledger, canon)

    assert result_a.passed == result_b.passed
    assert result_a.failure_reasons == result_b.failure_reasons
    assert result_a.blocked_claim_count == result_b.blocked_claim_count
    assert result_a.unresolved_ror_count == result_b.unresolved_ror_count


@pytest.mark.asyncio
async def test_gate_multiple_failures_all_surfaced():
    """All failed conditions appear in failure_reasons, not just the first."""
    blocked = [_make_blocked_claim("claim_1", "article_1")]
    pub_block = _make_pub_block("block_1", "claim_2", "article_1")
    dep = _make_dep("dep_1", "article_1", "thread_sao", resolved=0)
    window = _make_response_window("rw_1", "thread_sao")
    review_result = MagicMock()
    review_result.blocker_ids = ["finding_blocker"]

    records = _make_records(blocked_claims=blocked, active_blocks=[pub_block])
    comms = _make_comms(blocking_windows=[window], unresolved_deps=[dep])
    ledger = _make_ledger()
    canon = _make_canon()

    gate = PublicationGate()
    result = await gate.check(
        "article_1", records, comms, ledger, canon, review_result=review_result
    )

    assert result.passed is False
    # All four conditions failed — expect at least 4 reasons
    assert len(result.failure_reasons) >= 4
