"""
src/repositories/ledger_repo.py
Repository for ledger.db — the sole monetary source of truth.
Uses aiosqlite with WAL mode and foreign key enforcement.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiosqlite

from schemas.ledger_models import (
    FigureDerivation,
    FigureLock,
    FiscalRollup,
    Vendor,
    VendorAlias,
)
from src.core.exceptions import MigrationError


class LedgerRepo:
    """
    Async repository for ledger.db.
    All monetary queries go through this class.
    ledger.db is the sole source of truth for dollar figures.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @asynccontextmanager
    async def db_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """
        Async context manager that opens a connection with WAL mode and FK enforcement.
        Always use this rather than opening aiosqlite directly.
        """
        db = await aiosqlite.connect(str(self._db_path))
        try:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")
            yield db
        finally:
            await db.close()

    # ------------------------------------------------------------------
    # Vendor queries
    # ------------------------------------------------------------------

    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT vendor_id, canonical_name, notes, created_at FROM vendors WHERE vendor_id = ?",
                (vendor_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return Vendor(**dict(row))

    async def list_vendors(self) -> list[Vendor]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT vendor_id, canonical_name, notes, created_at FROM vendors ORDER BY canonical_name"
            ) as cursor:
                rows = await cursor.fetchall()
                return [Vendor(**dict(r)) for r in rows]

    async def get_vendor_aliases(self, vendor_id: str) -> list[VendorAlias]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT alias_id, vendor_id, alias, effective_from, effective_to "
                "FROM vendor_aliases WHERE vendor_id = ? ORDER BY alias",
                (vendor_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [VendorAlias(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Fiscal rollup queries
    # ------------------------------------------------------------------

    async def get_fiscal_rollup(
        self, vendor_id: str, fiscal_year: str
    ) -> Optional[FiscalRollup]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT rollup_id, vendor_id, fiscal_year, total_amount, payment_count, "
                "source_doc_ids, computed_at "
                "FROM fiscal_rollups WHERE vendor_id = ? AND fiscal_year = ?",
                (vendor_id, fiscal_year),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return FiscalRollup(**dict(row))

    async def list_fiscal_rollups(self, vendor_id: str) -> list[FiscalRollup]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT rollup_id, vendor_id, fiscal_year, total_amount, payment_count, "
                "source_doc_ids, computed_at "
                "FROM fiscal_rollups WHERE vendor_id = ? ORDER BY fiscal_year",
                (vendor_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [FiscalRollup(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Figure derivation queries
    # ------------------------------------------------------------------

    async def get_figure_derivation(self, derivation_id: str) -> Optional[FigureDerivation]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT derivation_id, figure_id, sql_query, computed_value, "
                "canonical_value, status, computed_at, notes "
                "FROM figure_derivations WHERE derivation_id = ?",
                (derivation_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return FigureDerivation(**dict(row))

    async def get_derivation_for_figure(self, figure_id: str) -> Optional[FigureDerivation]:
        """Get the most recent derivation for a given figure_id."""
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT derivation_id, figure_id, sql_query, computed_value, "
                "canonical_value, status, computed_at, notes "
                "FROM figure_derivations WHERE figure_id = ? "
                "ORDER BY computed_at DESC LIMIT 1",
                (figure_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return FigureDerivation(**dict(row))

    # ------------------------------------------------------------------
    # Figure lock queries
    # ------------------------------------------------------------------

    async def get_figure_lock(self, figure_id: str) -> Optional[FigureLock]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT lock_id, figure_id, locked_value, locked_at, locked_by, canon_hash "
                "FROM figure_locks WHERE figure_id = ?",
                (figure_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return FigureLock(**dict(row))

    async def upsert_figure_lock(self, lock: FigureLock) -> None:
        """Insert or replace a figure lock. figure_id must be UNIQUE in the table."""
        async with self.db_connection() as db:
            await db.execute(
                """
                INSERT INTO figure_locks (lock_id, figure_id, locked_value, locked_at, locked_by, canon_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(figure_id) DO UPDATE SET
                    lock_id      = excluded.lock_id,
                    locked_value = excluded.locked_value,
                    locked_at    = excluded.locked_at,
                    locked_by    = excluded.locked_by,
                    canon_hash   = excluded.canon_hash
                """,
                (
                    lock.lock_id,
                    lock.figure_id,
                    lock.locked_value,
                    lock.locked_at,
                    lock.locked_by,
                    lock.canon_hash,
                ),
            )
            await db.commit()

    # ------------------------------------------------------------------
    # Computed aggregation queries
    # ------------------------------------------------------------------

    async def compute_vendor_total(self, vendor_id: str, fiscal_year: str) -> float:
        """
        Compute the sum of all payments for a vendor in a fiscal year
        directly from the payments table.
        This is the live recomputation — compare to fiscal_rollups for verification.
        """
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT COALESCE(SUM(amount), 0.0) as total "
                "FROM payments WHERE vendor_id = ? AND fiscal_year = ?",
                (vendor_id, fiscal_year),
            ) as cursor:
                row = await cursor.fetchone()
                return float(row["total"]) if row else 0.0

    async def get_all_vendor_fiscal_totals(self, fiscal_year: str) -> dict[str, float]:
        """Get {vendor_id: total} for all vendors in a given fiscal year."""
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT vendor_id, COALESCE(SUM(amount), 0.0) as total "
                "FROM payments WHERE fiscal_year = ? GROUP BY vendor_id",
                (fiscal_year,),
            ) as cursor:
                rows = await cursor.fetchall()
                return {row["vendor_id"]: float(row["total"]) for row in rows}

    # ------------------------------------------------------------------
    # Table count (for status display)
    # ------------------------------------------------------------------

    async def get_table_counts(self) -> dict[str, int]:
        tables = [
            "vendors", "vendor_aliases", "source_documents",
            "payments", "fiscal_rollups", "figure_derivations",
            "figure_locks", "dedup_audit",
        ]
        counts: dict[str, int] = {}
        async with self.db_connection() as db:
            for table in tables:
                try:
                    async with db.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                        row = await cursor.fetchone()
                        counts[table] = row[0] if row else 0
                except Exception:
                    counts[table] = -1
        return counts
