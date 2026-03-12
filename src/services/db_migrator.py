"""
src/services/db_migrator.py
Simple deterministic DB migration runner.
Reads all SQL files in order from db/migrations/{db_name}/*.sql,
executes them, and tracks which have been applied in a _migrations table.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import NamedTuple

import aiosqlite

from src.core.exceptions import MigrationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class MigrationRecord(NamedTuple):
    migration_id: str
    applied_at: str
    checksum: str


class DbMigrator:
    """
    Runs SQL migration files against a SQLite database.

    Migration files are read from migrations_path/{db_name}/*.sql,
    sorted lexicographically (so 001_init.sql runs before 002_add_index.sql).

    Applied migrations are tracked in a _migrations table in each database.
    A migration is never re-applied if its migration_id already exists in _migrations.
    """

    async def migrate(
        self, db_path: Path, migrations_path: Path, db_name: str
    ) -> list[str]:
        """
        Run all pending migrations for a single database.

        Args:
            db_path: Path to the SQLite database file
            migrations_path: Root path of migrations directory
            db_name: Name of the DB (e.g. 'ledger', 'records', 'comms')

        Returns:
            List of migration_ids that were applied in this run.

        Raises:
            MigrationError on any SQL execution failure.
        """
        migration_dir = migrations_path / db_name
        if not migration_dir.exists():
            raise MigrationError(
                db_name=db_name,
                migration_file="<dir>",
                reason=f"Migration directory not found: {migration_dir}",
            )

        # Get sorted list of SQL files
        sql_files = sorted(
            f for f in migration_dir.iterdir()
            if f.suffix == ".sql" and f.is_file()
        )

        if not sql_files:
            logger.info(f"No migration files found for {db_name}")
            return []

        # Ensure DB directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(str(db_path)) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")

            # Ensure _migrations table exists (bootstraps from first migration or here)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS _migrations (
                    migration_id TEXT PRIMARY KEY,
                    applied_at   TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
                    checksum     TEXT
                )
                """
            )
            await db.commit()

            # Get already-applied migrations
            async with db.execute("SELECT migration_id FROM _migrations") as cursor:
                applied = {row[0] for row in await cursor.fetchall()}

            newly_applied: list[str] = []

            for sql_file in sql_files:
                migration_id = sql_file.name  # e.g. "001_init.sql"

                if migration_id in applied:
                    logger.debug(f"[{db_name}] Skipping already-applied: {migration_id}")
                    continue

                sql_content = sql_file.read_text(encoding="utf-8")
                checksum = hashlib.sha256(sql_content.encode()).hexdigest()

                logger.info(f"[{db_name}] Applying migration: {migration_id}")

                try:
                    await db.executescript(sql_content)
                    await db.execute(
                        "INSERT INTO _migrations (migration_id, checksum) VALUES (?, ?)",
                        (migration_id, checksum),
                    )
                    await db.commit()
                    newly_applied.append(migration_id)
                except Exception as e:
                    await db.rollback()
                    raise MigrationError(
                        db_name=db_name,
                        migration_file=migration_id,
                        reason=str(e),
                    ) from e

        return newly_applied

    async def migrate_all(
        self, db_root: Path, migrations_root: Path
    ) -> dict[str, list[str]]:
        """
        Run migrations for all three databases: ledger, records, comms.

        Returns:
            {db_name: [list of newly applied migration_ids]}
        """
        results: dict[str, list[str]] = {}

        for db_name in ["ledger", "records", "comms"]:
            db_path = db_root / f"{db_name}.db"
            applied = await self.migrate(db_path, migrations_root, db_name)
            results[db_name] = applied
            if applied:
                logger.info(f"[{db_name}] Applied {len(applied)} migration(s): {applied}")
            else:
                logger.info(f"[{db_name}] No new migrations")

        return results

    async def get_status(
        self, db_root: Path, migrations_root: Path
    ) -> dict[str, dict]:
        """
        Return migration status for all databases without applying anything.
        """
        status: dict[str, dict] = {}

        for db_name in ["ledger", "records", "comms"]:
            db_path = db_root / f"{db_name}.db"
            migration_dir = migrations_root / db_name

            available_files = []
            if migration_dir.exists():
                available_files = sorted(
                    f.name for f in migration_dir.iterdir()
                    if f.suffix == ".sql" and f.is_file()
                )

            applied: list[str] = []
            if db_path.exists():
                try:
                    async with aiosqlite.connect(str(db_path)) as db:
                        # Check if _migrations table exists
                        async with db.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='_migrations'"
                        ) as cursor:
                            if await cursor.fetchone():
                                async with db.execute(
                                    "SELECT migration_id, applied_at FROM _migrations ORDER BY migration_id"
                                ) as cur2:
                                    applied = [row[0] for row in await cur2.fetchall()]
                except Exception:
                    pass

            pending = [f for f in available_files if f not in applied]
            status[db_name] = {
                "db_path": str(db_path),
                "exists": db_path.exists(),
                "available": available_files,
                "applied": applied,
                "pending": pending,
            }

        return status
