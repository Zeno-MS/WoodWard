"""
Live integration test: runs draft_section in gate-only mode (no LLM call)
to generate a real run artifact for Phase 5 bridge testing.
Does NOT require API key — gate-only mode.

Seeding note: records.db seeds claim rows from canon but does NOT seed
claim_support rows (those come from ingest of real source documents).
For this integration test we insert minimal claim_support rows into a tmp db
so the ClaimSupportChecker's "at least one support row" requirement is satisfied.
This reflects the correct production flow once source documents are ingested.
"""
from __future__ import annotations

import shutil
import sqlite3
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _seed_support_rows(records_db_path: Path) -> dict[str, str]:
    """
    Insert minimal claim_support + document rows for article_2 claims
    into a records.db copy.

    Returns {claim_id: chunk_id} for assertions in downstream tests.
    """
    con = sqlite3.connect(str(records_db_path))
    con.execute("PRAGMA foreign_keys=ON")

    # Insert supporting documents (public board records)
    doc_rows = [
        (
            "doc_board_minutes_july2024",
            "VPS Board Minutes — July 9, 2024 Consent Agenda",
            "board_minutes",
            "public_record",
            None,
            "2024-07-09",
            "VPS Board approved Amergis contract estimate on consent agenda",
        ),
        (
            "doc_warrant_register_fy2425",
            "VPS Warrant Register FY2024-25 (BoardDocs)",
            "financial_record",
            "public_record",
            None,
            None,
            "25,578 deduplicated payment records sourced from BoardDocs PDFs",
        ),
    ]
    for row in doc_rows:
        con.execute(
            """
            INSERT OR IGNORE INTO documents
            (doc_id, title, doc_type, source_class, file_path, date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    # Insert chunks (schema: chunk_id, doc_id, content, chunk_index, embedding_id, created_at)
    chunk_rows = [
        (
            "chunk_board_amergis_estimate_001",
            "doc_board_minutes_july2024",
            "Amergis Healthcare — approximate cost $3,000,000 (consent agenda, no objection)",
            0,
        ),
        (
            "chunk_warrant_amergis_fy2425_001",
            "doc_warrant_register_fy2425",
            "Amergis Healthcare total payments FY2024-25: $10,970,973 across 25,578 records",
            0,
        ),
    ]
    for chunk_id, doc_id, content, chunk_index in chunk_rows:
        con.execute(
            """
            INSERT OR IGNORE INTO chunks
            (chunk_id, doc_id, content, chunk_index, created_at)
            VALUES (?, ?, ?, ?, datetime('now','utc'))
            """,
            (chunk_id, doc_id, content, chunk_index),
        )

    # Insert claim_support rows linking claims to document chunks
    support_rows = [
        (
            "sup_" + uuid.uuid4().hex[:12],
            "claim_board_3m_estimate",
            "doc_board_minutes_july2024",
            "chunk_board_amergis_estimate_001",
            "approximate cost $3,000,000",
            "direct_quote",
        ),
        (
            "sup_" + uuid.uuid4().hex[:12],
            "claim_amergis_fy2425_payment",
            "doc_warrant_register_fy2425",
            "chunk_warrant_amergis_fy2425_001",
            "$10,970,973",
            "figure_reference",
        ),
    ]

    chunk_map: dict[str, str] = {}
    for sup_id, claim_id, doc_id, chunk_id, quote, support_type in support_rows:
        con.execute(
            """
            INSERT OR IGNORE INTO claim_support
            (support_id, claim_id, doc_id, chunk_id, quote, support_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now','utc'))
            """,
            (sup_id, claim_id, doc_id, chunk_id, quote, support_type),
        )
        chunk_map[claim_id] = chunk_id

    con.commit()
    con.close()
    return chunk_map


async def test_gate_only_draft_produces_artifact(tmp_path):
    """
    Gate-only draft_section creates a result with gate decision populated.

    article_2 has 2 verified, public-citable claims. After seeding support rows,
    both claims should be draftable and the gate should pass.
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    from src.core.settings import WoodwardSettings
    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.records_repo import RecordsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.workflows.draft_section import draft_section

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)

    # Use tmp db copies — never touch real db/
    ledger_path = tmp_path / "ledger.db"
    records_path = tmp_path / "records.db"
    shutil.copy(str(PROJECT_ROOT / "db" / "ledger.db"), ledger_path)
    shutil.copy(str(PROJECT_ROOT / "db" / "records.db"), records_path)

    # Seed claim_support rows so ClaimSupportChecker passes
    chunk_map = _seed_support_rows(records_path)

    settings = WoodwardSettings(
        WOODWARD_RUNS_PATH=str(runs_dir),
        WOODWARD_DB_PATH=str(tmp_path),
        WOODWARD_CANONICAL_PATH=str(PROJECT_ROOT / "canonical"),
    )

    canonical_path = PROJECT_ROOT / "canonical"
    canon = CanonicalRepo(canonical_path).load_all()

    ledger = LedgerRepo(ledger_path)
    records = RecordsRepo(records_path)

    run_id = "test_live_gate_001"

    result = await draft_section(
        article_id="article_2",
        section_id="procurement_overview",
        run_id=run_id,
        settings=settings,
        records=records,
        ledger=ledger,
        canon=canon,
        provider_client=None,  # gate-only, no LLM
    )

    print(
        f"\nGate result: gate_passed={result.gate_passed}, "
        f"draftable={result.draftable_claim_count}, "
        f"blocked={result.blocked_claim_count}"
    )
    print(f"Injected figures: {list(result.injected_figures.keys())}")
    if result.gate_failure_reason:
        print(f"Gate failure reason: {result.gate_failure_reason}")

    assert result.article_id == "article_2"
    assert result.section_id == "procurement_overview"
    assert result.run_id == run_id
    assert result.draft is None  # gate-only mode — no LLM call

    # Gate must pass — article_2 has 2 verified, public-citable claims with support rows
    assert result.gate_passed, (
        f"Gate should pass for article_2. "
        f"Reason: {result.gate_failure_reason}. "
        f"draftable={result.draftable_claim_count}, blocked={result.blocked_claim_count}"
    )
    assert result.draftable_claim_count >= 2, (
        "Expected at least 2 draftable claims for article_2"
    )

    # Figures must be injected from canon
    assert "amergis_fy2425_total" in result.injected_figures, (
        "amergis_fy2425_total must be injected from canon"
    )
    assert "board_amergis_estimate_july2024" in result.injected_figures, (
        "board_amergis_estimate_july2024 must be injected from canon"
    )

    # Figure values must match canon
    assert result.injected_figures["amergis_fy2425_total"] == 10970973
    assert result.injected_figures["board_amergis_estimate_july2024"] == 3000000

    print(f"\nPASS: gate_passed=True, {result.draftable_claim_count} draftable claims, "
          f"{len(result.injected_figures)} figures injected")
