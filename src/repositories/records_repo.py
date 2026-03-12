"""
src/repositories/records_repo.py
Repository for records.db.
Manages public documents, text chunks, claims, support chains, and publication blocks.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiosqlite

from schemas.records_models import Claim, ClaimSupport, Document, PublicationBlock


class RecordsRepo:
    """Async repository for records.db."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @asynccontextmanager
    async def db_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = await aiosqlite.connect(str(self._db_path))
        try:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")
            yield db
        finally:
            await db.close()

    # ------------------------------------------------------------------
    # Document queries
    # ------------------------------------------------------------------

    async def get_document(self, doc_id: str) -> Optional[Document]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT doc_id, title, doc_type, source_class, file_path, date, notes "
                "FROM documents WHERE doc_id = ?",
                (doc_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return Document(**dict(row)) if row else None

    # ------------------------------------------------------------------
    # Claim queries
    # ------------------------------------------------------------------

    async def get_claim(self, claim_id: str) -> Optional[Claim]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT claim_id, article_id, text, status, public_citable, "
                "support_chain_complete, right_of_reply_required, stale, "
                "ingest_source, created_at, updated_at "
                "FROM claims WHERE claim_id = ?",
                (claim_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return Claim(**dict(row)) if row else None

    async def get_claims_for_article(self, article_id: str) -> list[Claim]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT claim_id, article_id, text, status, public_citable, "
                "support_chain_complete, right_of_reply_required, stale, "
                "ingest_source, created_at, updated_at "
                "FROM claims WHERE article_id = ? ORDER BY created_at",
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [Claim(**dict(r)) for r in rows]

    async def get_blocked_claims(self, article_id: str) -> list[Claim]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT claim_id, article_id, text, status, public_citable, "
                "support_chain_complete, right_of_reply_required, stale, "
                "ingest_source, created_at, updated_at "
                "FROM claims WHERE article_id = ? AND status = 'blocked' ORDER BY created_at",
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [Claim(**dict(r)) for r in rows]

    async def get_publishable_claims(self, article_id: str) -> list[Claim]:
        """Returns only claims that pass all publication gates."""
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT claim_id, article_id, text, status, public_citable, "
                "support_chain_complete, right_of_reply_required, stale, "
                "ingest_source, created_at, updated_at "
                "FROM claims "
                "WHERE article_id = ? "
                "AND status = 'verified' "
                "AND public_citable = 1 "
                "AND support_chain_complete = 1 "
                "AND stale = 0 "
                "ORDER BY created_at",
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [Claim(**dict(r)) for r in rows]

    async def upsert_claim(self, claim: Claim) -> None:
        async with self.db_connection() as db:
            await db.execute(
                """
                INSERT INTO claims (claim_id, article_id, text, status, public_citable,
                    support_chain_complete, right_of_reply_required, stale, ingest_source,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(claim_id) DO UPDATE SET
                    article_id              = excluded.article_id,
                    text                    = excluded.text,
                    status                  = excluded.status,
                    public_citable          = excluded.public_citable,
                    support_chain_complete  = excluded.support_chain_complete,
                    right_of_reply_required = excluded.right_of_reply_required,
                    stale                   = excluded.stale,
                    ingest_source           = excluded.ingest_source,
                    updated_at              = datetime('now', 'utc')
                """,
                (
                    claim.claim_id,
                    claim.article_id,
                    claim.text,
                    claim.status,
                    claim.public_citable,
                    claim.support_chain_complete,
                    claim.right_of_reply_required,
                    claim.stale,
                    claim.ingest_source,
                    claim.created_at,
                    claim.updated_at,
                ),
            )
            await db.commit()

    # ------------------------------------------------------------------
    # Claim support queries
    # ------------------------------------------------------------------

    async def get_claim_support(self, claim_id: str) -> list[ClaimSupport]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT support_id, claim_id, doc_id, chunk_id, quote, support_type, created_at "
                "FROM claim_support WHERE claim_id = ? ORDER BY created_at",
                (claim_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [ClaimSupport(**dict(r)) for r in rows]

    async def add_claim_support(self, support: ClaimSupport) -> None:
        async with self.db_connection() as db:
            await db.execute(
                "INSERT OR IGNORE INTO claim_support "
                "(support_id, claim_id, doc_id, chunk_id, quote, support_type, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    support.support_id,
                    support.claim_id,
                    support.doc_id,
                    support.chunk_id,
                    support.quote,
                    support.support_type,
                    support.created_at,
                ),
            )
            await db.commit()

    # ------------------------------------------------------------------
    # Publication block queries
    # ------------------------------------------------------------------

    async def add_publication_block(self, block: PublicationBlock) -> None:
        async with self.db_connection() as db:
            await db.execute(
                "INSERT OR IGNORE INTO publication_blocks "
                "(block_id, claim_id, article_id, reason, blocking_since, resolved_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    block.block_id,
                    block.claim_id,
                    block.article_id,
                    block.reason,
                    block.blocking_since,
                    block.resolved_at,
                ),
            )
            await db.commit()

    async def get_active_blocks(self, article_id: str) -> list[PublicationBlock]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT block_id, claim_id, article_id, reason, blocking_since, resolved_at "
                "FROM publication_blocks "
                "WHERE article_id = ? AND resolved_at IS NULL ORDER BY blocking_since",
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [PublicationBlock(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Table count (for status display)
    # ------------------------------------------------------------------

    async def get_table_counts(self) -> dict[str, int]:
        tables = ["documents", "chunks", "claims", "claim_support", "publication_blocks"]
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
