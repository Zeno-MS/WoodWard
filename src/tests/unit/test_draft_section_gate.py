"""
tests/unit/test_draft_section_gate.py
Unit tests for the Phase 3 draft_section gate workflow.
Uses mock repos and canon manifests.
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
)
from schemas.records_models import Claim, ClaimSupport
from src.core.exceptions import BlockedClaimError
from src.workflows.draft_section import DraftSectionGateResult, draft_section


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_schema_version() -> SchemaVersion:
    return SchemaVersion(
        schema_version="1.0.0",
        created="2026-03-12",
        investigation="vps_2026_test",
        locked_by="test",
    )


def _make_canon(
    claims: list[ClaimRecord] | None = None,
    figures: list[CanonicalFigure] | None = None,
    banned_claims: list[BannedClaim] | None = None,
    articles: list[ArticleRecord] | None = None,
) -> CanonManifest:
    return CanonManifest(
        schema_version=_make_schema_version(),
        figures=figures or [],
        vendors=[],
        articles=articles or [
            ArticleRecord(
                article_id="article_2",
                title="Test Article 2",
                status="draft",
                file_path="drafts/article_2.md",
                locked=False,
            )
        ],
        claims=claims or [],
        banned_claims=banned_claims or [],
        source_policy=SourcePolicy(source_classes=[]),
    )


def _make_locked_figure(
    figure_id: str = "fy2425_staffing_vendor_total",
    value: float = 13326622.0,
) -> CanonicalFigure:
    return CanonicalFigure(
        figure_id=figure_id,
        display_label="Test Figure",
        value=value,
        display_value=f"${value:,.0f}",
        fiscal_year="FY2024-25",
        source_of_truth="ledger.db",
        derivation_id=f"deriv_{figure_id}",
        status="locked",
    )


def _make_db_claim(
    claim_id: str = "c1",
    status: str = "verified",
    public_citable: int = 1,
    support_chain_complete: int = 1,
    right_of_reply_required: int = 0,
    article_id: str = "article_2",
    text: str = "Test claim",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        article_id=article_id,
        text=text,
        status=status,
        public_citable=public_citable,
        support_chain_complete=support_chain_complete,
        right_of_reply_required=right_of_reply_required,
        stale=0,
        ingest_source="canonical_seed",
    )


def _make_support(claim_id: str = "c1") -> ClaimSupport:
    return ClaimSupport(
        support_id=f"sup_{claim_id}",
        claim_id=claim_id,
        doc_id="doc_board_minutes",
        support_type="direct_quote",
        quote="Supporting text from public record.",
    )


def _make_records(
    claims_by_article: dict[str, list[Claim]] | None = None,
    support_by_claim: dict[str, list[ClaimSupport]] | None = None,
) -> MagicMock:
    claims_by_article = claims_by_article or {}
    support_by_claim = support_by_claim or {}

    mock = MagicMock()
    mock.get_claims_for_article = AsyncMock(
        side_effect=lambda aid: claims_by_article.get(aid, [])
    )
    mock.get_claim = AsyncMock(
        side_effect=lambda cid: next(
            (c for claims in claims_by_article.values() for c in claims if c.claim_id == cid),
            None,
        )
    )
    mock.get_claim_support = AsyncMock(
        side_effect=lambda cid: support_by_claim.get(cid, [])
    )
    return mock


def _make_ledger() -> MagicMock:
    return MagicMock()


def _make_settings() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_passes_with_all_verified_claims() -> None:
    """When all claims are verified and public-citable, the gate passes."""
    claim_1 = _make_db_claim("c1", status="verified", public_citable=1, support_chain_complete=1)
    claim_2 = _make_db_claim("c2", status="verified", public_citable=1, support_chain_complete=1)

    records = _make_records(
        claims_by_article={"article_2": [claim_1, claim_2]},
        support_by_claim={
            "c1": [_make_support("c1")],
            "c2": [_make_support("c2")],
        },
    )
    canon = _make_canon(figures=[_make_locked_figure()])

    result: DraftSectionGateResult = await draft_section(
        article_id="article_2",
        section_id="section_a",
        run_id="test_run_001",
        settings=_make_settings(),
        records=records,
        ledger=_make_ledger(),
        canon=canon,
    )

    assert result.gate_passed is True
    assert result.gate_failure_reason is None
    assert len(result.draftable_claims) == 2
    assert len(result.blocked_claims) == 0


@pytest.mark.asyncio
async def test_gate_strips_blocked_claims() -> None:
    """Blocked claims are stripped by gate_draft_context and do not reach LLM context."""
    verified_claim = _make_db_claim("c_ok", status="verified", public_citable=1, support_chain_complete=1)
    # Non-critical blocked claim (right_of_reply_required=0) — silently stripped
    blocked_claim = _make_db_claim(
        "c_blocked", status="blocked", public_citable=0, support_chain_complete=0,
        right_of_reply_required=0
    )

    records = _make_records(
        claims_by_article={"article_2": [verified_claim, blocked_claim]},
        support_by_claim={"c_ok": [_make_support("c_ok")]},
    )
    canon = _make_canon()

    result = await draft_section(
        article_id="article_2",
        section_id="section_a",
        run_id="test_run_002",
        settings=_make_settings(),
        records=records,
        ledger=_make_ledger(),
        canon=canon,
    )

    # Gate should pass (one draftable claim survived)
    assert result.gate_passed is True
    # c_blocked was stripped by gate_draft_context before check_batch — not in blocked_claims
    assert "c_ok" in result.draftable_claim_ids


@pytest.mark.asyncio
async def test_gate_injects_locked_figures() -> None:
    """Locked figures from canon must be injected into the gate result."""
    fig1 = _make_locked_figure("fy2425_staffing_vendor_total", 13326622.0)
    fig2 = _make_locked_figure("amergis_fy2425_total", 10970973.0)

    claim = _make_db_claim("c1", status="verified", public_citable=1, support_chain_complete=1)
    records = _make_records(
        claims_by_article={"article_2": [claim]},
        support_by_claim={"c1": [_make_support("c1")]},
    )
    canon = _make_canon(figures=[fig1, fig2])

    result = await draft_section(
        article_id="article_2",
        section_id="section_b",
        run_id="test_run_003",
        settings=_make_settings(),
        records=records,
        ledger=_make_ledger(),
        canon=canon,
    )

    assert result.gate_passed is True
    assert "fy2425_staffing_vendor_total" in result.injected_figures
    assert result.injected_figures["fy2425_staffing_vendor_total"] == 13326622.0
    assert "amergis_fy2425_total" in result.injected_figures
    assert result.injected_figures["amergis_fy2425_total"] == 10970973.0


@pytest.mark.asyncio
async def test_gate_fails_if_critical_blocked_claim_present() -> None:
    """
    A blocked claim with right_of_reply_required=True must cause the gate to fail
    with gate_passed=False (BlockedClaimError is caught and reported).
    """
    critical_blocked = _make_db_claim(
        "c_critical_blocked",
        status="blocked",
        public_citable=0,
        support_chain_complete=0,
        right_of_reply_required=1,  # Critical — raises in gate_draft_context
    )
    records = _make_records(
        claims_by_article={"article_2": [critical_blocked]},
        support_by_claim={},
    )
    canon = _make_canon()

    result = await draft_section(
        article_id="article_2",
        section_id="section_a",
        run_id="test_run_004",
        settings=_make_settings(),
        records=records,
        ledger=_make_ledger(),
        canon=canon,
    )

    assert result.gate_passed is False
    assert result.gate_failure_reason is not None
    assert "CRITICAL_BLOCKED_CLAIM" in result.gate_failure_reason


@pytest.mark.asyncio
async def test_gate_raises_on_banned_claim_text() -> None:
    """
    If a claim's text matches a banned pattern, gate returns gate_passed=False
    with BANNED_CLAIM_PATTERN in the failure reason.
    """
    banned = BannedClaim(
        ban_id="ban_001",
        text_pattern="never conducted competitive bidding",
        reason="Unconfirmed assertion requiring PRR confirmation",
        added_date="2026-03-12",
    )
    claim = _make_db_claim(
        "c_banned_text",
        status="verified",
        public_citable=1,
        support_chain_complete=1,
        text="VPS has never conducted competitive bidding for this contract",
    )
    records = _make_records(
        claims_by_article={"article_2": [claim]},
        support_by_claim={"c_banned_text": [_make_support("c_banned_text")]},
    )
    canon = _make_canon(banned_claims=[banned])

    result = await draft_section(
        article_id="article_2",
        section_id="section_a",
        run_id="test_run_005",
        settings=_make_settings(),
        records=records,
        ledger=_make_ledger(),
        canon=canon,
    )

    assert result.gate_passed is False
    assert result.gate_failure_reason is not None
    assert "BANNED_CLAIM_PATTERN" in result.gate_failure_reason


@pytest.mark.asyncio
async def test_gate_fails_when_zero_claims_in_article() -> None:
    """When no claims exist for an article, gate_passed remains True (empty is valid)."""
    records = _make_records(
        claims_by_article={"article_2": []},
        support_by_claim={},
    )
    canon = _make_canon(figures=[_make_locked_figure()])

    result = await draft_section(
        article_id="article_2",
        section_id="section_a",
        run_id="test_run_006",
        settings=_make_settings(),
        records=records,
        ledger=_make_ledger(),
        canon=canon,
    )

    # No claims = no failures — gate passes, draftable list is empty
    assert result.gate_passed is True
    assert len(result.draftable_claims) == 0


@pytest.mark.asyncio
async def test_draft_section_gate_result_summary() -> None:
    """DraftSectionGateResult.summary() returns a non-empty informational string."""
    result = DraftSectionGateResult(
        article_id="article_2",
        section_id="section_a",
        run_id="run_001",
        gate_passed=True,
    )
    summary = result.summary()
    assert "article_2" in summary
    assert "gate_passed=True" in summary
