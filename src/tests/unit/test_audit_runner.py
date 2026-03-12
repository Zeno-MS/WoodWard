"""
tests/unit/test_audit_runner.py
Unit tests for AuditRunner.
Uses tmp_path fixtures and real SQLite databases to verify audit logic.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
import yaml

from schemas.canonical import (
    BannedClaim,
    CanonicalFigure,
    CanonManifest,
    ClaimRecord,
    SchemaVersion,
    SourcePolicy,
)
from schemas.ledger_models import FigureDerivation
from src.services.audit_runner import AuditCheck, AuditReport, AuditRunner


# ---------------------------------------------------------------------------
# Helpers — minimal canonical fixtures
# ---------------------------------------------------------------------------

def _make_figure(
    figure_id: str = "test_fig",
    value: float = 1000.0,
    status: str = "locked",
) -> CanonicalFigure:
    return CanonicalFigure(
        figure_id=figure_id,
        display_label="Test Figure",
        value=value,
        display_value=f"${value:,.0f}",
        fiscal_year="FY2024-25",
        source_of_truth="ledger.db/fiscal_rollups",
        derivation_id=f"deriv_{figure_id}",
        status=status,
    )


def _make_claim_record(
    claim_id: str = "test_claim",
    article_id: str = "article_1",
    status: str = "verified",
    public_citable: bool = True,
    support_chain_complete: bool = True,
) -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        text=f"Test claim text for {claim_id}",
        article_id=article_id,
        status=status,
        public_citable=public_citable,
        support_chain_complete=support_chain_complete,
        right_of_reply_required=False,
        stale=False,
    )


def _make_banned(ban_id: str = "ban_test") -> BannedClaim:
    return BannedClaim(
        ban_id=ban_id,
        text_pattern="Test banned pattern",
        reason="Test reason",
        added_date="2026-03-12",
    )


def _make_canon(
    figures: list[CanonicalFigure] | None = None,
    claims: list[ClaimRecord] | None = None,
    banned: list[BannedClaim] | None = None,
) -> CanonManifest:
    return CanonManifest(
        schema_version=SchemaVersion(
            schema_version="1.0.0",
            created="2026-03-12",
            investigation="test",
            locked_by="test",
        ),
        figures=figures or [],
        vendors=[],
        articles=[],
        claims=claims or [],
        banned_claims=banned or [],
        source_policy=SourcePolicy(source_classes=[]),
    )


def _write_canonical(tmp_path: Path, canon: CanonManifest) -> Path:
    """Write canonical YAML files to a tmp directory and return the path."""
    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir(exist_ok=True)

    # schema_version.yaml
    (canonical_dir / "schema_version.yaml").write_text(
        yaml.dump({
            "schema_version": canon.schema_version.schema_version,
            "created": canon.schema_version.created,
            "investigation": canon.schema_version.investigation,
            "locked_by": canon.schema_version.locked_by,
        }),
        encoding="utf-8",
    )

    # figures.yaml
    figures_data = []
    for f in canon.figures:
        fig_dict = f.model_dump()
        figures_data.append(fig_dict)
    (canonical_dir / "figures.yaml").write_text(
        yaml.dump({"figures": figures_data}),
        encoding="utf-8",
    )

    # claims_registry.yaml
    claims_data = []
    for c in canon.claims:
        claims_data.append(c.model_dump())
    (canonical_dir / "claims_registry.yaml").write_text(
        yaml.dump({"claims": claims_data}),
        encoding="utf-8",
    )

    # banned_claims.yaml
    banned_data = []
    for b in canon.banned_claims:
        banned_data.append(b.model_dump())
    (canonical_dir / "banned_claims.yaml").write_text(
        yaml.dump({"banned_claims": banned_data}),
        encoding="utf-8",
    )

    # source_policy.yaml
    (canonical_dir / "source_policy.yaml").write_text(
        yaml.dump({"source_classes": []}),
        encoding="utf-8",
    )

    # vendor_scope.yaml
    (canonical_dir / "vendor_scope.yaml").write_text(
        yaml.dump({"vendors": []}),
        encoding="utf-8",
    )

    # articles.yaml
    (canonical_dir / "articles.yaml").write_text(
        yaml.dump({"articles": []}),
        encoding="utf-8",
    )

    return canonical_dir


async def _create_records_db(db_path: Path) -> None:
    """Create a minimal records.db with the required tables."""
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                doc_type TEXT,
                source_class TEXT,
                file_path TEXT,
                date TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT REFERENCES documents(doc_id),
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding_id TEXT,
                created_at TEXT DEFAULT (datetime('now', 'utc'))
            );
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                article_id TEXT,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                public_citable INTEGER DEFAULT 0,
                support_chain_complete INTEGER DEFAULT 0,
                right_of_reply_required INTEGER DEFAULT 0,
                stale INTEGER DEFAULT 0,
                ingest_source TEXT,
                created_at TEXT DEFAULT (datetime('now', 'utc')),
                updated_at TEXT DEFAULT (datetime('now', 'utc'))
            );
            CREATE TABLE IF NOT EXISTS claim_support (
                support_id TEXT PRIMARY KEY,
                claim_id TEXT REFERENCES claims(claim_id),
                doc_id TEXT,
                chunk_id TEXT,
                quote TEXT,
                support_type TEXT,
                created_at TEXT DEFAULT (datetime('now', 'utc'))
            );
            CREATE TABLE IF NOT EXISTS publication_blocks (
                block_id TEXT PRIMARY KEY,
                claim_id TEXT REFERENCES claims(claim_id),
                article_id TEXT,
                reason TEXT NOT NULL,
                blocking_since TEXT,
                resolved_at TEXT
            );
        """)
        await db.commit()


async def _create_ledger_db(db_path: Path) -> None:
    """Create a minimal ledger.db with figure_derivations table."""
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now', 'utc'))
            );
            CREATE TABLE IF NOT EXISTS vendor_aliases (
                alias_id TEXT PRIMARY KEY,
                vendor_id TEXT REFERENCES vendors(vendor_id),
                alias TEXT NOT NULL,
                effective_from TEXT,
                effective_to TEXT
            );
            CREATE TABLE IF NOT EXISTS source_documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                doc_type TEXT,
                fiscal_year TEXT,
                source_class TEXT,
                file_path TEXT,
                url TEXT,
                date_acquired TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                vendor_id TEXT REFERENCES vendors(vendor_id),
                amount REAL NOT NULL,
                fiscal_year TEXT NOT NULL,
                payment_date TEXT,
                warrant_number TEXT,
                doc_id TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS fiscal_rollups (
                rollup_id TEXT PRIMARY KEY,
                vendor_id TEXT REFERENCES vendors(vendor_id),
                fiscal_year TEXT NOT NULL,
                total_amount REAL NOT NULL,
                payment_count INTEGER,
                source_doc_ids TEXT,
                computed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS figure_derivations (
                derivation_id TEXT PRIMARY KEY,
                figure_id TEXT NOT NULL,
                sql_query TEXT NOT NULL,
                computed_value REAL,
                canonical_value REAL,
                status TEXT,
                computed_at TEXT DEFAULT (datetime('now', 'utc')),
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS figure_locks (
                lock_id TEXT PRIMARY KEY,
                figure_id TEXT UNIQUE NOT NULL,
                locked_value REAL NOT NULL,
                locked_at TEXT,
                locked_by TEXT,
                canon_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS dedup_audit (
                audit_id TEXT PRIMARY KEY,
                source TEXT,
                total_records INTEGER,
                dedup_records INTEGER,
                method TEXT,
                run_at TEXT
            );
        """)
        await db.commit()


async def _create_comms_db(db_path: Path) -> None:
    """Create a minimal comms.db."""
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS organizations (
                org_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                org_type TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS recipients (
                recipient_id TEXT PRIMARY KEY,
                org_id TEXT REFERENCES organizations(org_id),
                name TEXT NOT NULL,
                role TEXT,
                email TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS question_sets (
                qs_id TEXT PRIMARY KEY,
                article_id TEXT,
                recipient_id TEXT,
                questions TEXT,
                created_at TEXT DEFAULT (datetime('now', 'utc'))
            );
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                recipient_id TEXT REFERENCES recipients(recipient_id),
                subject TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT (datetime('now', 'utc')),
                updated_at TEXT DEFAULT (datetime('now', 'utc'))
            );
            CREATE TABLE IF NOT EXISTS messages (
                msg_id TEXT PRIMARY KEY,
                thread_id TEXT REFERENCES threads(thread_id),
                direction TEXT NOT NULL,
                content TEXT NOT NULL,
                sent_at TEXT DEFAULT (datetime('now', 'utc')),
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS response_windows (
                window_id TEXT PRIMARY KEY,
                thread_id TEXT REFERENCES threads(thread_id),
                deadline TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                publication_blocking INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS article_dependencies (
                dep_id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL,
                thread_id TEXT,
                claim_id TEXT,
                dependency_type TEXT,
                resolved INTEGER DEFAULT 0
            );
        """)
        await db.commit()


async def _setup_env(tmp_path: Path, canon: CanonManifest) -> tuple:
    """Set up all temp directories and databases. Returns (settings, runner)."""
    canonical_dir = _write_canonical(tmp_path, canon)
    db_dir = tmp_path / "db"
    db_dir.mkdir(exist_ok=True)
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(exist_ok=True)

    await _create_ledger_db(db_dir / "ledger.db")
    await _create_records_db(db_dir / "records.db")
    await _create_comms_db(db_dir / "comms.db")

    from src.core.settings import WoodwardSettings
    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.comms_repo import CommsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.repositories.records_repo import RecordsRepo

    settings = MagicMock(spec=WoodwardSettings)
    settings.db_path_obj = db_dir
    settings.canonical_path_obj = canonical_dir
    settings.runs_path_obj = runs_dir
    settings.ledger_db_path = db_dir / "ledger.db"
    settings.records_db_path = db_dir / "records.db"
    settings.comms_db_path = db_dir / "comms.db"
    settings.backups_path_obj = tmp_path / "backups"

    canonical_repo = CanonicalRepo(canonical_dir)
    ledger_repo = LedgerRepo(db_dir / "ledger.db")
    records_repo = RecordsRepo(db_dir / "records.db")
    comms_repo = CommsRepo(db_dir / "comms.db")

    runner = AuditRunner(
        settings=settings,
        canonical_repo=canonical_repo,
        ledger_repo=ledger_repo,
        records_repo=records_repo,
        comms_repo=comms_repo,
    )

    return settings, runner, records_repo, ledger_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_audit_passes_on_clean_state(tmp_path: Path) -> None:
    """A clean state with matching data should produce an all-pass audit."""
    fig = _make_figure("fig_1", value=1000.0)
    claim = _make_claim_record("claim_1", article_id="article_1")
    canon = _make_canon(figures=[fig], claims=[claim])

    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    # Seed records.db with the claim and support
    async with aiosqlite.connect(str(settings.records_db_path)) as db:
        await db.execute(
            "INSERT INTO documents (doc_id, title) VALUES (?, ?)",
            ("doc_1", "Test Document"),
        )
        await db.execute(
            "INSERT INTO claims (claim_id, article_id, text, status, public_citable, support_chain_complete) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("claim_1", "article_1", "Test claim", "verified", 1, 1),
        )
        await db.execute(
            "INSERT INTO claim_support (support_id, claim_id, doc_id, support_type) "
            "VALUES (?, ?, ?, ?)",
            ("sup_1", "claim_1", "doc_1", "direct_quote"),
        )
        await db.commit()

    # Seed ledger.db with derivation
    async with aiosqlite.connect(str(settings.ledger_db_path)) as db:
        await db.execute(
            "INSERT INTO figure_derivations (derivation_id, figure_id, sql_query, computed_value, status) "
            "VALUES (?, ?, ?, ?, ?)",
            ("deriv_fig_1", "fig_1", "SELECT 1000.0", 1000.0, "computed"),
        )
        await db.commit()

    report = await runner.run_full_audit()

    assert report.overall_status == "pass"
    assert len(report.checks) == 5
    assert all(c.status == "pass" for c in report.checks)


@pytest.mark.asyncio
async def test_audit_detects_stale_banned_reference(tmp_path: Path) -> None:
    """Audit should detect when a banned ID appears as a claim_id in the registry."""
    # Create a banned claim whose ban_id also appears as a claim_id in the registry
    # This isn't the normal use case (ban_ids don't match claim_ids), but let's test
    # that the check scans for ID collisions properly.
    banned = _make_banned("ban_test_ref")
    # Add a claim in figures.yaml with a figure_id matching a ban_id
    fig = _make_figure("ban_test_ref", value=999.0)  # figure_id = ban_id
    canon = _make_canon(figures=[fig], banned=[banned])

    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    result = await runner.detect_stale_banned_references(canon)

    assert result.status == "fail"
    assert result.count >= 1
    assert any("ban_test_ref" in d for d in result.details)


@pytest.mark.asyncio
async def test_audit_detects_broken_support_chain(tmp_path: Path) -> None:
    """Audit should detect claims that are verified+public_citable but have no support rows."""
    claim = _make_claim_record("claim_broken", article_id="article_1")
    canon = _make_canon(claims=[claim])

    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    # Seed claim in DB as verified+public_citable+support_chain_complete
    # but do NOT add any claim_support rows
    async with aiosqlite.connect(str(settings.records_db_path)) as db:
        await db.execute(
            "INSERT INTO claims (claim_id, article_id, text, status, public_citable, support_chain_complete) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("claim_broken", "article_1", "Broken claim", "verified", 1, 1),
        )
        await db.commit()

    result = await runner.verify_support_chains(canon)

    assert result.status == "fail"
    assert result.count >= 1
    assert any("claim_broken" in d and "no ClaimSupport rows" in d for d in result.details)


@pytest.mark.asyncio
async def test_audit_detects_orphaned_claim(tmp_path: Path) -> None:
    """Audit should detect claims in DB that are not in the registry, and vice versa."""
    # Registry has claim_in_registry; DB will have claim_in_db_only
    claim_reg = _make_claim_record("claim_in_registry", article_id="article_1")
    canon = _make_canon(claims=[claim_reg])

    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    # Seed only claim_in_db_only (not claim_in_registry)
    async with aiosqlite.connect(str(settings.records_db_path)) as db:
        await db.execute(
            "INSERT INTO claims (claim_id, article_id, text, status, public_citable, support_chain_complete) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("claim_in_db_only", "article_1", "Orphan claim in DB", "draft", 0, 0),
        )
        await db.commit()

    result = await runner.detect_orphaned_claims(canon)

    assert result.status == "fail"
    assert result.count >= 2  # claim_in_db_only not in registry + claim_in_registry not in DB
    assert any("claim_in_db_only" in d and "records.db but not in claims_registry" in d for d in result.details)
    assert any("claim_in_registry" in d and "claims_registry.yaml but not in records.db" in d for d in result.details)


@pytest.mark.asyncio
async def test_audit_detects_missing_source_document(tmp_path: Path) -> None:
    """Audit should detect claim_support rows referencing non-existent documents."""
    claim = _make_claim_record("claim_missing_doc", article_id="article_1")
    canon = _make_canon(claims=[claim])

    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    # Seed claim and support, but NOT the document
    async with aiosqlite.connect(str(settings.records_db_path)) as db:
        await db.execute(
            "INSERT INTO claims (claim_id, article_id, text, status) VALUES (?, ?, ?, ?)",
            ("claim_missing_doc", "article_1", "Claim text", "verified"),
        )
        await db.execute(
            "INSERT INTO claim_support (support_id, claim_id, doc_id, support_type) "
            "VALUES (?, ?, ?, ?)",
            ("sup_missing", "claim_missing_doc", "doc_does_not_exist", "direct_quote"),
        )
        await db.commit()

    result = await runner.detect_missing_source_documents()

    assert result.status == "fail"
    assert result.count >= 1
    assert any("doc_does_not_exist" in d for d in result.details)


@pytest.mark.asyncio
async def test_audit_report_is_valid_json(tmp_path: Path) -> None:
    """The audit report should serialize to valid JSON."""
    canon = _make_canon()
    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    report = await runner.run_full_audit()
    json_str = report.model_dump_json(indent=2)

    # Parse it back
    parsed = json.loads(json_str)
    assert "audit_timestamp" in parsed
    assert "checks" in parsed
    assert isinstance(parsed["checks"], list)
    assert "overall_status" in parsed


@pytest.mark.asyncio
async def test_audit_report_includes_canon_hash(tmp_path: Path) -> None:
    """The audit report must include a non-empty canon_hash."""
    canon = _make_canon()
    settings, runner, records_repo, ledger_repo = await _setup_env(tmp_path, canon)

    report = await runner.run_full_audit()

    assert report.canon_hash
    assert len(report.canon_hash) == 64  # SHA-256 hex digest
