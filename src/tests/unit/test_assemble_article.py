"""
src/tests/unit/test_assemble_article.py
Unit tests for assemble_article workflow.
Tests scaffolding stripping, figures table, and gate enforcement.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schemas.canonical import (
    CanonicalFigure,
    CanonManifest,
    SchemaVersion,
    SourcePolicy,
)
from src.core.exceptions import PublicationBlockedError
from src.workflows.assemble_article import (
    ArticleAssemblyResult,
    assemble_article,
    build_figures_table,
    strip_scaffolding,
)


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


def _make_figure(figure_id: str, label: str = None) -> CanonicalFigure:
    return CanonicalFigure(
        figure_id=figure_id,
        display_label=label or f"Label {figure_id}",
        value=1000000.0,
        display_value="$1,000,000",
        fiscal_year="FY2024-25",
        source_of_truth="ledger.db",
        derivation_id=f"deriv_{figure_id}",
        status="locked",
    )


def _make_canon(figures: list[CanonicalFigure] | None = None) -> CanonManifest:
    return CanonManifest(
        schema_version=_make_schema_version(),
        figures=figures or [],
        vendors=[],
        articles=[],
        claims=[],
        banned_claims=[],
        source_policy=_make_source_policy(),
    )


def _make_draft_result(
    article_id: str,
    section_id: str,
    content: str,
    figures_used: list[str] | None = None,
    gate_passed: bool = True,
) -> MagicMock:
    from schemas.llm_contracts import DraftSectionResponse

    draft = DraftSectionResponse(
        section_id=section_id,
        article_id=article_id,
        content=content,
        assertions=[],
        figures_used=figures_used or [],
    )
    result = MagicMock()
    result.section_id = section_id
    result.article_id = article_id
    result.gate_passed = gate_passed
    result.draft = draft
    return result


def _make_settings(tmp_path) -> MagicMock:
    settings = MagicMock()
    settings.runs_path_obj = tmp_path
    return settings


# ---------------------------------------------------------------------------
# strip_scaffolding tests
# ---------------------------------------------------------------------------

def test_strip_scaffolding_removes_context_ids():
    """All [ctx:xxx] markers are removed from content."""
    content = "VPS paid [ctx:doc_warrant_123] over $10 million [ctx:chunk_456] to vendors."
    result = strip_scaffolding(content)
    assert "[ctx:" not in result
    assert "VPS paid" in result
    assert "over $10 million" in result
    assert "to vendors." in result


def test_strip_scaffolding_removes_claim_ids():
    """[claim:xxx] markers are stripped."""
    content = "The board approved $3M [claim:claim_board_3m_estimate] on the agenda."
    result = strip_scaffolding(content)
    assert "[claim:" not in result
    assert "The board approved $3M" in result


def test_strip_scaffolding_removes_fig_and_support():
    """[fig:xxx] and [support:xxx] markers are stripped."""
    content = "Spending total: $13.3M [fig:fy2425_total] [support:support_abc]."
    result = strip_scaffolding(content)
    assert "[fig:" not in result
    assert "[support:" not in result
    assert "Spending total:" in result
    assert "$13.3M" in result


def test_strip_scaffolding_preserves_content():
    """Prose content is fully preserved after stripping."""
    clean_text = "Vancouver Public Schools paid approximately $10.97 million to Amergis."
    result = strip_scaffolding(clean_text)
    assert result == clean_text


def test_strip_scaffolding_handles_empty_string():
    """Empty string returns empty string."""
    assert strip_scaffolding("") == ""


def test_strip_scaffolding_case_insensitive():
    """Marker stripping is case-insensitive."""
    content = "Fact [CTX:upper_case] and [Claim:mixed_case] verified."
    result = strip_scaffolding(content)
    assert "[CTX:" not in result.upper()
    assert "[CLAIM:" not in result.upper()
    assert "Fact" in result
    assert "verified." in result


def test_strip_scaffolding_does_not_strip_real_brackets():
    """Real bracketed text (not scaffolding patterns) is preserved."""
    content = "The board [as required by RCW 28A.335.190] approved the contract."
    result = strip_scaffolding(content)
    assert "[as required by RCW 28A.335.190]" in result


# ---------------------------------------------------------------------------
# build_figures_table tests
# ---------------------------------------------------------------------------

def test_figures_table_only_includes_used_figures():
    """Only figures in the figures_used list appear in the table."""
    canon = _make_canon(figures=[
        _make_figure("fig_a", "Amergis Total"),
        _make_figure("fig_b", "Five-Year Total"),
        _make_figure("fig_c", "Object 7 Overage"),
    ])
    table = build_figures_table(["fig_a", "fig_c"], canon)

    assert "Amergis Total" in table
    assert "Object 7 Overage" in table
    assert "Five-Year Total" not in table


def test_figures_table_marks_unlocked_figure():
    """Figures not in canon are noted as 'not in canon'."""
    canon = _make_canon(figures=[])
    table = build_figures_table(["mystery_figure"], canon)

    assert "mystery_figure" in table
    assert "not in canon" in table


def test_figures_table_empty_when_no_figures_used():
    """Empty string returned when no figures are used."""
    canon = _make_canon()
    table = build_figures_table([], canon)
    assert table == ""


def test_figures_table_has_correct_columns():
    """Table has Figure, Value, Source, Status columns."""
    canon = _make_canon(figures=[_make_figure("fig_a", "Amergis Total")])
    table = build_figures_table(["fig_a"], canon)

    assert "Figure" in table
    assert "Value" in table
    assert "Source" in table
    assert "Status" in table


# ---------------------------------------------------------------------------
# assemble_article tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assembly_blocked_if_gate_fails(tmp_path):
    """assemble_article raises PublicationBlockedError if gate fails."""
    from schemas.records_models import Claim

    blocked_claim = Claim(
        claim_id="claim_blocked",
        article_id="article_1",
        text="A blocked claim.",
        status="blocked",
        public_citable=0,
        support_chain_complete=0,
        right_of_reply_required=1,
        stale=0,
        ingest_source="canonical_seed",
    )

    records = MagicMock()
    records.get_blocked_claims = AsyncMock(return_value=[blocked_claim])
    records.get_active_blocks = AsyncMock(return_value=[])

    comms = MagicMock()
    comms.get_publication_blocking_windows = AsyncMock(return_value=[])
    comms.get_unresolved_dependencies = AsyncMock(return_value=[])

    ledger = MagicMock()
    canon = _make_canon()
    settings = _make_settings(tmp_path)

    with pytest.raises(PublicationBlockedError):
        await assemble_article(
            article_id="article_1",
            section_results=[],
            run_id="test_run",
            settings=settings,
            records=records,
            comms=comms,
            ledger=ledger,
            canon=canon,
        )


@pytest.mark.asyncio
async def test_assembly_produces_clean_final_version(tmp_path):
    """Final article strips scaffolding markers from draft content."""
    records = MagicMock()
    records.get_blocked_claims = AsyncMock(return_value=[])
    records.get_active_blocks = AsyncMock(return_value=[])

    comms = MagicMock()
    comms.get_publication_blocking_windows = AsyncMock(return_value=[])
    comms.get_unresolved_dependencies = AsyncMock(return_value=[])

    ledger = MagicMock()
    canon = _make_canon()
    settings = _make_settings(tmp_path)

    section = _make_draft_result(
        article_id="article_3",
        section_id="sec_intro",
        content="VPS paid $13.3M [ctx:chunk_001] [claim:claim_fy2425_total_spending] to vendors.",
        figures_used=[],
    )

    result = await assemble_article(
        article_id="article_3",
        section_results=[section],
        run_id="test_run_clean",
        settings=settings,
        records=records,
        comms=comms,
        ledger=ledger,
        canon=canon,
    )

    assert "[ctx:" not in result.final_markdown
    assert "[claim:" not in result.final_markdown
    assert "VPS paid $13.3M" in result.final_markdown
    # Scaffolded version preserves them
    assert "[ctx:" in result.scaffolded_markdown or "[claim:" in result.scaffolded_markdown


@pytest.mark.asyncio
async def test_assembly_writes_files(tmp_path):
    """Both final and scaffolded files are written to runs/{run_id}/."""
    records = MagicMock()
    records.get_blocked_claims = AsyncMock(return_value=[])
    records.get_active_blocks = AsyncMock(return_value=[])

    comms = MagicMock()
    comms.get_publication_blocking_windows = AsyncMock(return_value=[])
    comms.get_unresolved_dependencies = AsyncMock(return_value=[])

    ledger = MagicMock()
    canon = _make_canon()
    settings = _make_settings(tmp_path)

    result = await assemble_article(
        article_id="article_2",
        section_results=[],
        run_id="test_run_files",
        settings=settings,
        records=records,
        comms=comms,
        ledger=ledger,
        canon=canon,
    )

    assert result.artifact_path_final is not None
    assert result.artifact_path_scaffolded is not None

    from pathlib import Path
    assert Path(result.artifact_path_final).exists()
    assert Path(result.artifact_path_scaffolded).exists()
