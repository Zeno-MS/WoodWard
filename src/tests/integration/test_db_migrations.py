"""
tests/integration/test_db_migrations.py
Integration tests for the DB migration runner.
Uses tmp_path — NEVER writes to the real db/ directory.
"""
from __future__ import annotations

from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from src.core.exceptions import MigrationError
from src.services.db_migrator import DbMigrator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def migrations_root() -> Path:
    """Return path to the real migration files in the project."""
    # Find project root by looking for pyproject.toml
    here = Path(__file__).parent
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent / "db" / "migrations"
    # Fallback
    return Path("db") / "migrations"


@pytest_asyncio.fixture
async def migrated_ledger(tmp_path: Path, migrations_root: Path):
    """Create and migrate a temporary ledger.db."""
    db_path = tmp_path / "ledger.db"
    migrator = DbMigrator()
    await migrator.migrate(db_path, migrations_root, "ledger")
    return db_path


@pytest_asyncio.fixture
async def migrated_records(tmp_path: Path, migrations_root: Path):
    """Create and migrate a temporary records.db."""
    db_path = tmp_path / "records.db"
    migrator = DbMigrator()
    await migrator.migrate(db_path, migrations_root, "records")
    return db_path


@pytest_asyncio.fixture
async def migrated_comms(tmp_path: Path, migrations_root: Path):
    """Create and migrate a temporary comms.db."""
    db_path = tmp_path / "comms.db"
    migrator = DbMigrator()
    await migrator.migrate(db_path, migrations_root, "comms")
    return db_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_tables(db_path: Path) -> set[str]:
    """Return set of table names in a SQLite database."""
    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            return {row[0] for row in rows}


async def _get_pragma(db_path: Path, pragma: str) -> str:
    """Get a SQLite pragma value."""
    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(f"PRAGMA {pragma}") as cursor:
            row = await cursor.fetchone()
            return str(row[0]) if row else ""


# ---------------------------------------------------------------------------
# Ledger migration tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ledger_migration_creates_all_tables(
    migrated_ledger: Path,
) -> None:
    """ledger.db migration must create all required tables."""
    tables = await _get_tables(migrated_ledger)
    expected = {
        "vendors",
        "vendor_aliases",
        "source_documents",
        "payments",
        "fiscal_rollups",
        "figure_derivations",
        "figure_locks",
        "dedup_audit",
        "_migrations",
    }
    for table in expected:
        assert table in tables, f"Expected table '{table}' not found in ledger.db"


@pytest.mark.asyncio
async def test_records_migration_creates_all_tables(
    migrated_records: Path,
) -> None:
    """records.db migration must create all required tables."""
    tables = await _get_tables(migrated_records)
    expected = {
        "documents",
        "chunks",
        "claims",
        "claim_support",
        "publication_blocks",
        "_migrations",
    }
    for table in expected:
        assert table in tables, f"Expected table '{table}' not found in records.db"


@pytest.mark.asyncio
async def test_comms_migration_creates_all_tables(
    migrated_comms: Path,
) -> None:
    """comms.db migration must create all required tables."""
    tables = await _get_tables(migrated_comms)
    expected = {
        "organizations",
        "recipients",
        "question_sets",
        "threads",
        "messages",
        "response_windows",
        "article_dependencies",
        "_migrations",
    }
    for table in expected:
        assert table in tables, f"Expected table '{table}' not found in comms.db"


@pytest.mark.asyncio
async def test_wal_pragma_is_set(migrated_ledger: Path) -> None:
    """WAL mode should be enabled when using the repo's db_connection()."""
    from src.repositories.ledger_repo import LedgerRepo
    repo = LedgerRepo(migrated_ledger)
    async with repo.db_connection() as db:
        async with db.execute("PRAGMA journal_mode") as cursor:
            row = await cursor.fetchone()
            assert row[0] == "wal", f"Expected WAL mode, got {row[0]}"


@pytest.mark.asyncio
async def test_foreign_keys_pragma_is_set(migrated_ledger: Path) -> None:
    """Foreign key enforcement should be enabled when using the repo's db_connection()."""
    from src.repositories.ledger_repo import LedgerRepo
    repo = LedgerRepo(migrated_ledger)
    async with repo.db_connection() as db:
        async with db.execute("PRAGMA foreign_keys") as cursor:
            row = await cursor.fetchone()
            assert row[0] == 1, f"Expected foreign_keys=1, got {row[0]}"


@pytest.mark.asyncio
async def test_migration_is_idempotent(tmp_path: Path, migrations_root: Path) -> None:
    """Running migrations twice must not raise and must not duplicate records."""
    db_path = tmp_path / "idempotent_ledger.db"
    migrator = DbMigrator()

    # First run
    applied_1 = await migrator.migrate(db_path, migrations_root, "ledger")
    assert len(applied_1) > 0

    # Second run — must apply nothing new
    applied_2 = await migrator.migrate(db_path, migrations_root, "ledger")
    assert len(applied_2) == 0


@pytest.mark.asyncio
async def test_migration_records_are_tracked(migrated_ledger: Path) -> None:
    """Applied migrations must be recorded in the _migrations table."""
    async with aiosqlite.connect(str(migrated_ledger)) as db:
        async with db.execute("SELECT migration_id FROM _migrations") as cursor:
            rows = await cursor.fetchall()
            migration_ids = [row[0] for row in rows]

    assert "001_init.sql" in migration_ids


@pytest.mark.asyncio
async def test_ledger_payments_constraint_enforces_non_negative(
    migrated_ledger: Path,
) -> None:
    """The payments table must reject negative amounts."""
    async with aiosqlite.connect(str(migrated_ledger)) as db:
        # First insert a vendor to satisfy FK
        await db.execute(
            "INSERT INTO vendors (vendor_id, canonical_name) VALUES ('v1', 'Test Vendor')"
        )
        await db.commit()

        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO payments (payment_id, vendor_id, amount, fiscal_year) "
                "VALUES ('p1', 'v1', -100.0, 'FY2024-25')"
            )
            await db.commit()


@pytest.mark.asyncio
async def test_claims_status_constraint(migrated_records: Path) -> None:
    """The claims table must reject invalid status values."""
    async with aiosqlite.connect(str(migrated_records)) as db:
        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO claims (claim_id, text, status) "
                "VALUES ('c1', 'test', 'invalid_status_value')"
            )
            await db.commit()
