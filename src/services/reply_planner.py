"""
src/services/reply_planner.py
Reply planner — identifies what right-of-reply outreach is needed before publication.

For a given article, loads all claims with right_of_reply_required=True,
cross-references comms.db threads, and returns a structured list of
ReplyRequirement objects showing what is resolved, pending, or blocking.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.repositories.comms_repo import CommsRepo
from src.repositories.records_repo import RecordsRepo

logger = logging.getLogger(__name__)


@dataclass
class ReplyRequirement:
    """
    Represents a single right-of-reply requirement for a claim in an article.

    status reflects the current state of the linked thread (if any), or
    'pending' if no thread exists yet.
    publication_blocking is True if the claim is in article_dependencies with resolved=0
    AND has a publication-blocking response window.
    """
    claim_id: str
    claim_text: str
    article_id: str
    thread_id: Optional[str]       # Existing thread if any
    recipient_id: Optional[str]
    recipient_name: Optional[str]
    status: str                    # 'pending'|'sent'|'responded'|'no_response'|'resolved'
    publication_blocking: bool
    deadline: Optional[str]


class ReplyPlanner:
    """
    Loads right-of-reply requirements for an article by cross-referencing
    records.db (claims) and comms.db (threads, dependencies, response windows).
    """

    async def get_requirements(
        self,
        article_id: str,
        records: RecordsRepo,
        comms: CommsRepo,
    ) -> list[ReplyRequirement]:
        """
        For a given article:
        1. Load all claims where right_of_reply_required=True from records.db.
        2. Load article_dependencies from comms.db.
        3. Load response windows to determine publication-blocking status.
        4. Return ReplyRequirement for each claim, with status from linked thread.
        """
        # Step 1: Load all claims for the article
        all_claims = await records.get_claims_for_article(article_id)
        ror_claims = [c for c in all_claims if c.right_of_reply_required == 1]

        if not ror_claims:
            logger.info(
                f"reply_planner: no right-of-reply claims for article '{article_id}'"
            )
            return []

        # Step 2: Load article dependencies for this article
        deps = await comms.get_article_dependencies(article_id)
        # Map claim_id -> ArticleDependency
        dep_by_claim: dict[str, list] = {}
        for dep in deps:
            if dep.claim_id:
                dep_by_claim.setdefault(dep.claim_id, []).append(dep)

        # Step 3: Load threads for this article and their response windows
        threads = await comms.get_threads_for_article(article_id)
        thread_map = {t.thread_id: t for t in threads}

        # Load publication-blocking windows: map thread_id -> ResponseWindow
        blocking_windows = await comms.get_publication_blocking_windows()
        blocking_by_thread: dict[str, list] = {}
        for w in blocking_windows:
            blocking_by_thread.setdefault(w.thread_id, []).append(w)

        # Step 4: Build ReplyRequirement for each RoR claim
        requirements: list[ReplyRequirement] = []
        for claim in ror_claims:
            deps_for_claim = dep_by_claim.get(claim.claim_id, [])

            # Find the primary thread for this claim (first unresolved dep, if any)
            thread_id: Optional[str] = None
            recipient_id: Optional[str] = None
            recipient_name: Optional[str] = None
            publication_blocking = False
            deadline: Optional[str] = None

            if deps_for_claim:
                # Prefer unresolved dependencies
                primary_dep = next(
                    (d for d in deps_for_claim if d.resolved == 0),
                    deps_for_claim[0],
                )
                thread_id = primary_dep.thread_id
                # Check blocking
                if thread_id and thread_id in blocking_by_thread:
                    for w in blocking_by_thread[thread_id]:
                        if w.publication_blocking == 1 and w.status == "open":
                            publication_blocking = True
                            if w.deadline:
                                deadline = w.deadline
                            break

            # Resolve recipient from thread
            if thread_id and thread_id in thread_map:
                t = thread_map[thread_id]
                recipient_id = t.recipient_id
                if recipient_id:
                    recipient = await comms.get_recipient(recipient_id)
                    if recipient:
                        recipient_name = recipient.name

            # Determine status from thread
            status = _derive_status(thread_id, thread_map, deps_for_claim)

            requirements.append(
                ReplyRequirement(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    article_id=article_id,
                    thread_id=thread_id,
                    recipient_id=recipient_id,
                    recipient_name=recipient_name,
                    status=status,
                    publication_blocking=publication_blocking,
                    deadline=deadline,
                )
            )

        logger.info(
            f"reply_planner: article='{article_id}' "
            f"ror_claims={len(ror_claims)} "
            f"blocking={sum(1 for r in requirements if r.publication_blocking)}"
        )
        return requirements

    async def get_blocking_requirements(
        self,
        article_id: str,
        records: RecordsRepo,
        comms: CommsRepo,
    ) -> list[ReplyRequirement]:
        """Returns only publication-blocking requirements."""
        all_reqs = await self.get_requirements(article_id, records, comms)
        return [r for r in all_reqs if r.publication_blocking]

    def format_summary(self, requirements: list[ReplyRequirement]) -> str:
        """Returns a plain-text summary suitable for inclusion in handoff packets."""
        if not requirements:
            return "No right-of-reply requirements found."

        lines = [
            f"Right-of-Reply Requirements ({len(requirements)} total)",
            "=" * 50,
        ]
        blocking = [r for r in requirements if r.publication_blocking]
        non_blocking = [r for r in requirements if not r.publication_blocking]

        if blocking:
            lines.append(f"\nPUBLICATION-BLOCKING ({len(blocking)}):")
            for r in blocking:
                lines.append(f"  [{r.status.upper()}] {r.claim_id}")
                lines.append(f"    Claim: {r.claim_text[:80]}{'...' if len(r.claim_text) > 80 else ''}")
                if r.recipient_name:
                    lines.append(f"    Contact: {r.recipient_name}")
                if r.deadline:
                    lines.append(f"    Deadline: {r.deadline}")
                if r.thread_id:
                    lines.append(f"    Thread: {r.thread_id}")

        if non_blocking:
            lines.append(f"\nNON-BLOCKING ({len(non_blocking)}):")
            for r in non_blocking:
                lines.append(f"  [{r.status.upper()}] {r.claim_id}")
                lines.append(f"    Claim: {r.claim_text[:80]}{'...' if len(r.claim_text) > 80 else ''}")

        return "\n".join(lines)


def _derive_status(
    thread_id: Optional[str],
    thread_map: dict,
    deps: list,
) -> str:
    """
    Derive a canonical status string for a ReplyRequirement.

    Priority:
    - If no thread found: 'pending'
    - If all deps resolved: 'resolved'
    - Map thread status to requirement status
    """
    if not thread_id:
        return "pending"

    # Check if all dependencies are resolved
    if deps and all(d.resolved == 1 for d in deps):
        return "resolved"

    thread = thread_map.get(thread_id)
    if not thread:
        return "pending"

    status_map = {
        "open":                "sent",
        "awaiting_response":   "sent",
        "responded":           "responded",
        "closed":              "no_response",
        "publication_blocked": "no_response",
    }
    return status_map.get(thread.status or "", "pending")
