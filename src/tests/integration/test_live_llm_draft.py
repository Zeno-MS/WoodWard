"""
Live LLM integration test — requires OPENAI_API_KEY.
Drafts a section for Article 2 (procurement overview) using the full Phase 4 pipeline.

This is the first end-to-end live test of the Woodward Core v2 drafting pipeline.

Article 2 subject: The Amergis contract — how $3M became $10.97M in one fiscal year.

Expected behavior:
- Gate passes (article_2 has verified claims with seeded support rows)
- LLM receives locked figures: amergis_fy2425_total=$10,970,973,
  board_amergis_estimate_july2024=~$3,000,000
- LLM produces DraftSectionResponse with assertions
- All context_ids in assertions must resolve (hard-stop on hallucination)
- Draft content must reference the locked Amergis figure ($10,970,973 or ~$10.97M)

Support row seeding: same pattern as test_live_gate.py — minimal but real
document + chunk rows to satisfy ClaimSupportChecker's "at least one support row"
requirement. This mirrors the production flow once source documents are ingested.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _seed_support_rows(records_db_path: Path) -> dict[str, str]:
    """
    Insert minimal claim_support + document rows for article_2 claims.
    Returns {claim_id: chunk_id} for context_id validation.

    Uses sqlite3 (not aiosqlite) per project rules for seed scripts.
    """
    con = sqlite3.connect(str(records_db_path))
    con.execute("PRAGMA foreign_keys=ON")

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

    chunk_rows = [
        (
            "chunk_board_amergis_estimate_001",
            "doc_board_minutes_july2024",
            "Amergis Healthcare — approximate cost $3,000,000 (consent agenda, no objection recorded)",
            0,
        ),
        (
            "chunk_warrant_amergis_fy2425_001",
            "doc_warrant_register_fy2425",
            "Amergis Healthcare total payments FY2024-25: $10,970,973 across 25,578 deduplicated records",
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


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY — live LLM test",
)
async def test_live_llm_draft_article_2(tmp_path):
    """
    Full Phase 4 pipeline: gate + LLM draft for article_2 procurement_overview.

    Validates:
    1. Gate passes with seeded support rows
    2. LLM produces a valid DraftSectionResponse
    3. All context_ids resolve (HallucinatedContextError would hard-stop)
    4. Draft content references the locked Amergis figure
    5. Artifact is written to runs/{run_id}/draft_procurement_overview.json
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    from src.core.settings import WoodwardSettings
    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.records_repo import RecordsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.providers.openai_client import OpenAIClient
    from src.workflows.draft_section import draft_section

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)

    # Use tmp db copies — never touch real db/
    ledger_path = tmp_path / "ledger.db"
    records_path = tmp_path / "records.db"
    shutil.copy(str(PROJECT_ROOT / "db" / "ledger.db"), ledger_path)
    shutil.copy(str(PROJECT_ROOT / "db" / "records.db"), records_path)

    # Seed claim_support rows so gate and context_assembler have real support docs
    _seed_support_rows(records_path)

    settings = WoodwardSettings(
        WOODWARD_RUNS_PATH=str(runs_dir),
        WOODWARD_DB_PATH=str(tmp_path),
        WOODWARD_CANONICAL_PATH=str(PROJECT_ROOT / "canonical"),
    )

    canon = CanonicalRepo(PROJECT_ROOT / "canonical").load_all()
    ledger = LedgerRepo(ledger_path)
    records = RecordsRepo(records_path)

    api_key = os.environ["OPENAI_API_KEY"]
    client = OpenAIClient(api_key=api_key, model="gpt-4o")

    run_id = "test_live_llm_001"

    result = await draft_section(
        article_id="article_2",
        section_id="procurement_overview",
        run_id=run_id,
        settings=settings,
        records=records,
        ledger=ledger,
        canon=canon,
        provider_client=client,
    )

    print(f"\n=== LIVE DRAFT RESULT ===")
    print(f"Gate passed: {result.gate_passed}")
    print(f"Draftable claims: {result.draftable_claim_count}")
    print(f"Blocked claims: {result.blocked_claim_count}")

    # Gate must pass
    assert result.gate_passed, (
        f"Gate failed: {result.gate_failure_reason}"
    )

    if result.draft:
        print(f"Draft word count: {result.draft.word_count}")
        print(f"Assertions: {len(result.draft.assertions)}")
        print(f"Figures used: {result.draft.figures_used}")
        print(f"Unresolved questions: {len(result.draft.unresolved_questions)}")
        print(f"Right-of-reply flags: {len(result.draft.right_of_reply_flags)}")
        print(f"\n--- DRAFT CONTENT (first 1000 chars) ---")
        print(result.draft.content[:1000])
        if len(result.draft.content) > 1000:
            print("...")

    # Draft must be present
    assert result.draft is not None, "LLM draft should be present"
    assert result.draft.word_count > 0, "Draft must have content"

    # Locked figures must appear in the draft (canonical values, not hallucinated)
    # Accept either full value or abbreviated form
    content = result.draft.content
    amergis_figure_present = (
        "10,970,973" in content
        or "10.97" in content
        or "10.9" in content
    )
    assert amergis_figure_present, (
        f"Locked Amergis figure ($10,970,973) must appear in draft content. "
        f"Content: {content[:500]}"
    )

    # Artifact file must be written
    artifact_file = runs_dir / run_id / "draft_procurement_overview.json"
    assert artifact_file.exists(), (
        f"Artifact file not written at {artifact_file}"
    )

    print(f"\nArtifact written: {artifact_file}")
    print(f"\nPASS: Full Phase 4 pipeline succeeded for article_2/procurement_overview")
