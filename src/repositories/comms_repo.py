"""
src/repositories/comms_repo.py
Repository for comms.db.
Tracks outreach, right-of-reply threads, response windows, and publication dependencies.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiosqlite

from schemas.comms_models import (
    ArticleDependency,
    Organization,
    Recipient,
    ResponseWindow,
    Thread,
    Message,
)


class CommsRepo:
    """Async repository for comms.db."""

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
    # Organization queries
    # ------------------------------------------------------------------

    async def get_organization(self, org_id: str) -> Optional[Organization]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT org_id, name, org_type, notes FROM organizations WHERE org_id = ?",
                (org_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return Organization(**dict(row)) if row else None

    # ------------------------------------------------------------------
    # Recipient queries
    # ------------------------------------------------------------------

    async def get_recipient(self, recipient_id: str) -> Optional[Recipient]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT recipient_id, org_id, name, role, email, notes "
                "FROM recipients WHERE recipient_id = ?",
                (recipient_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return Recipient(**dict(row)) if row else None

    # ------------------------------------------------------------------
    # Thread queries
    # ------------------------------------------------------------------

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT thread_id, recipient_id, subject, status, created_at, updated_at "
                "FROM threads WHERE thread_id = ?",
                (thread_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return Thread(**dict(row)) if row else None

    async def get_threads_for_article(self, article_id: str) -> list[Thread]:
        """Get all threads linked to an article via article_dependencies."""
        async with self.db_connection() as db:
            async with db.execute(
                """
                SELECT DISTINCT t.thread_id, t.recipient_id, t.subject, t.status,
                       t.created_at, t.updated_at
                FROM threads t
                JOIN article_dependencies ad ON ad.thread_id = t.thread_id
                WHERE ad.article_id = ?
                ORDER BY t.created_at
                """,
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [Thread(**dict(r)) for r in rows]

    async def get_open_threads(self) -> list[Thread]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT thread_id, recipient_id, subject, status, created_at, updated_at "
                "FROM threads WHERE status IN ('open', 'awaiting_response') ORDER BY created_at",
            ) as cursor:
                rows = await cursor.fetchall()
                return [Thread(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Message queries
    # ------------------------------------------------------------------

    async def get_messages_for_thread(self, thread_id: str) -> list[Message]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT msg_id, thread_id, direction, content, sent_at, notes "
                "FROM messages WHERE thread_id = ? ORDER BY sent_at",
                (thread_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [Message(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Response window queries
    # ------------------------------------------------------------------

    async def get_open_response_windows(self) -> list[ResponseWindow]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT window_id, thread_id, deadline, status, publication_blocking "
                "FROM response_windows WHERE status = 'open' ORDER BY deadline",
            ) as cursor:
                rows = await cursor.fetchall()
                return [ResponseWindow(**dict(r)) for r in rows]

    async def get_publication_blocking_windows(self) -> list[ResponseWindow]:
        """Return all open response windows that are blocking publication."""
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT window_id, thread_id, deadline, status, publication_blocking "
                "FROM response_windows "
                "WHERE publication_blocking = 1 AND status = 'open' ORDER BY deadline",
            ) as cursor:
                rows = await cursor.fetchall()
                return [ResponseWindow(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Article dependency queries
    # ------------------------------------------------------------------

    async def get_article_dependencies(self, article_id: str) -> list[ArticleDependency]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT dep_id, article_id, thread_id, claim_id, dependency_type, resolved "
                "FROM article_dependencies WHERE article_id = ? ORDER BY dep_id",
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [ArticleDependency(**dict(r)) for r in rows]

    async def get_unresolved_dependencies(self, article_id: str) -> list[ArticleDependency]:
        async with self.db_connection() as db:
            async with db.execute(
                "SELECT dep_id, article_id, thread_id, claim_id, dependency_type, resolved "
                "FROM article_dependencies "
                "WHERE article_id = ? AND resolved = 0 ORDER BY dep_id",
                (article_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [ArticleDependency(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Table count (for status display)
    # ------------------------------------------------------------------

    async def get_table_counts(self) -> dict[str, int]:
        tables = [
            "organizations", "recipients", "question_sets",
            "threads", "messages", "response_windows", "article_dependencies",
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
