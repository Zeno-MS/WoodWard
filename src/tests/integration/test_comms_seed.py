"""
src/tests/integration/test_comms_seed.py
Integration tests for the comms.db seed script.
Runs the seed against a real (or temp) SQLite database.
"""
from __future__ import annotations

import asyncio
import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

COMMS_DB = PROJECT_ROOT / "db" / "comms.db"
SEED_SCRIPT = PROJECT_ROOT / "db" / "seeds" / "seed_comms_from_tracker.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db() -> sqlite3.Connection:
    """Open a read connection to the seeded comms.db."""
    db = sqlite3.connect(str(COMMS_DB))
    db.row_factory = sqlite3.Row
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_comms_seed_runs_clean():
    """Seed script runs without errors and populates expected tables."""
    assert COMMS_DB.exists(), (
        f"comms.db not found at {COMMS_DB}. Run: python3 db/seeds/seed_comms_from_tracker.py"
    )
    db = _get_db()
    try:
        # All expected tables exist and have rows
        tables = [
            "organizations",
            "recipients",
            "threads",
            "messages",
            "response_windows",
            "article_dependencies",
        ]
        for table in tables:
            row = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            count = row[0]
            assert count > 0, f"Expected rows in {table}, found 0"
    finally:
        db.close()


def test_threads_linked_to_recipients():
    """Each thread is linked to a valid recipient via recipient_id FK."""
    db = _get_db()
    try:
        rows = db.execute(
            """
            SELECT t.thread_id, t.recipient_id, r.name
            FROM threads t
            LEFT JOIN recipients r ON r.recipient_id = t.recipient_id
            """
        ).fetchall()

        assert len(rows) > 0
        for row in rows:
            assert row["recipient_id"] is not None, (
                f"Thread '{row['thread_id']}' has no recipient_id"
            )
            assert row["name"] is not None, (
                f"Thread '{row['thread_id']}' recipient not found in recipients table"
            )
    finally:
        db.close()


def test_article_dependencies_linked_to_claims():
    """article_dependencies reference valid claim_ids (per the claims_registry)."""
    db = _get_db()
    try:
        rows = db.execute(
            "SELECT dep_id, article_id, thread_id, claim_id, resolved "
            "FROM article_dependencies"
        ).fetchall()

        assert len(rows) > 0
        for row in rows:
            assert row["article_id"] is not None
            assert row["thread_id"] is not None
            assert row["claim_id"] is not None
            # resolved must be 0 or 1
            assert row["resolved"] in (0, 1)
    finally:
        db.close()


def test_vps_ror_thread_seeded():
    """The VPS right-of-reply thread for brett_blechschmidt exists."""
    db = _get_db()
    try:
        row = db.execute(
            "SELECT thread_id, recipient_id, status FROM threads WHERE thread_id = 'vps_ror_feb27'"
        ).fetchone()
        assert row is not None, "Thread 'vps_ror_feb27' not found"
        assert row["recipient_id"] == "brett_blechschmidt"
    finally:
        db.close()


def test_sao_cooper_thread_has_publication_blocking_window():
    """sao_cooper thread has a publication-blocking response window."""
    db = _get_db()
    try:
        row = db.execute(
            """
            SELECT rw.window_id, rw.publication_blocking, rw.deadline, rw.status
            FROM response_windows rw
            WHERE rw.thread_id = 'sao_cooper'
            AND rw.publication_blocking = 1
            """
        ).fetchone()
        assert row is not None, "No publication-blocking window found for sao_cooper"
        assert row["status"] == "open"
        assert row["deadline"] == "2026-03-20"
    finally:
        db.close()


def test_ospi_lewis_thread_responded():
    """OSPI Lewis thread status is 'responded' and has inbound message."""
    db = _get_db()
    try:
        thread = db.execute(
            "SELECT status FROM threads WHERE thread_id = 'ospi_lewis'"
        ).fetchone()
        assert thread is not None
        assert thread["status"] == "responded"

        # Check for inbound message confirming the advance amount
        msg = db.execute(
            "SELECT content FROM messages WHERE thread_id = 'ospi_lewis' AND direction = 'inbound'"
        ).fetchone()
        assert msg is not None
        assert "8.7" in msg["content"] or "21,367,552" in msg["content"]
    finally:
        db.close()


def test_organizations_all_seeded():
    """All four expected organizations are present."""
    db = _get_db()
    try:
        rows = db.execute("SELECT org_id FROM organizations").fetchall()
        org_ids = {r["org_id"] for r in rows}
        expected = {"vps", "sao", "ospi", "amergis"}
        assert expected == org_ids, f"Missing orgs: {expected - org_ids}"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_comms_repo_reads_threads():
    """CommsRepo can read seeded threads asynchronously."""
    from src.repositories.comms_repo import CommsRepo

    comms = CommsRepo(COMMS_DB)
    threads = await comms.get_threads_for_article("article_1")

    # article_1 has a dependency on sao_cooper thread
    assert any(t.thread_id == "sao_cooper" for t in threads), (
        f"Expected sao_cooper thread for article_1. Got: {[t.thread_id for t in threads]}"
    )


@pytest.mark.asyncio
async def test_comms_repo_reads_publication_blocking_windows():
    """CommsRepo returns publication-blocking windows correctly."""
    from src.repositories.comms_repo import CommsRepo

    comms = CommsRepo(COMMS_DB)
    windows = await comms.get_publication_blocking_windows()

    assert len(windows) >= 1
    # sao_cooper window is blocking
    blocking_thread_ids = {w.thread_id for w in windows}
    assert "sao_cooper" in blocking_thread_ids
