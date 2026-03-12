"""
src/services/publication_gate.py
Publication gate — final check before article assembly.

All five conditions must pass before assemble_article() is allowed to run.
A single failure sets passed=False. No silent passes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from schemas.canonical import CanonManifest
from src.core.exceptions import PublicationBlockedError
from src.repositories.comms_repo import CommsRepo
from src.repositories.ledger_repo import LedgerRepo
from src.repositories.records_repo import RecordsRepo

logger = logging.getLogger(__name__)


@dataclass
class PublicationGateResult:
    """
    Result of a publication gate check.

    passed=True only when ALL conditions clear.
    Every failure reason is surfaced in failure_reasons.
    """
    article_id: str
    passed: bool
    failure_reasons: list[str] = field(default_factory=list)
    blocked_claim_count: int = 0
    unresolved_ror_count: int = 0          # Right-of-reply still open
    unlocked_figure_count: int = 0         # Figures not in canon
    review_blocker_count: int = 0          # Adversarial review blockers unresolved
    canon_hash: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PublicationGate:
    """
    Enforces publication readiness before article assembly.

    Gate conditions (ALL must pass):
    1. No blocked claims exist for this article.
    2. All publication_blocks for this article are resolved.
    3. No unresolved publication-blocking right-of-reply threads.
    4. All figures in draft (if provided) are in locked_figures.
    5. No adversarial review blockers (if review_result provided).
    """

    async def check(
        self,
        article_id: str,
        records: RecordsRepo,
        comms: CommsRepo,
        ledger: LedgerRepo,
        canon: CanonManifest,
        draft_result=None,      # Optional DraftSectionResult or list thereof
        review_result=None,     # Optional ReviewDraftResult or list thereof
        canon_hash: str = "",
    ) -> PublicationGateResult:
        """
        Run all gate conditions. Returns a PublicationGateResult.
        Never raises — all failures are captured in the result.
        """
        failure_reasons: list[str] = []
        blocked_claim_count = 0
        unresolved_ror_count = 0
        unlocked_figure_count = 0
        review_blocker_count = 0

        # ------------------------------------------------------------------
        # Condition 1: No blocked claims for this article
        # ------------------------------------------------------------------
        try:
            blocked_claims = await records.get_blocked_claims(article_id)
            blocked_claim_count = len(blocked_claims)
            if blocked_claim_count > 0:
                claim_ids = [c.claim_id for c in blocked_claims]
                failure_reasons.append(
                    f"Blocked claims exist for article '{article_id}': {claim_ids}"
                )
                logger.warning(
                    f"publication_gate: article='{article_id}' "
                    f"FAIL condition 1 — {blocked_claim_count} blocked claims: {claim_ids}"
                )
        except Exception as e:
            failure_reasons.append(f"Error checking blocked claims: {e}")
            logger.error(f"publication_gate: condition 1 error: {e}")

        # ------------------------------------------------------------------
        # Condition 2: All publication_blocks for this article are resolved
        # ------------------------------------------------------------------
        try:
            pub_blocks = await records.get_active_blocks(article_id)
            active_blocks = [b for b in pub_blocks if b.is_active]
            if active_blocks:
                block_ids = [b.block_id for b in active_blocks]
                failure_reasons.append(
                    f"Unresolved publication_blocks for article '{article_id}': {block_ids}"
                )
                logger.warning(
                    f"publication_gate: article='{article_id}' "
                    f"FAIL condition 2 — {len(active_blocks)} active publication blocks: {block_ids}"
                )
        except Exception as e:
            failure_reasons.append(f"Error checking publication blocks: {e}")
            logger.error(f"publication_gate: condition 2 error: {e}")

        # ------------------------------------------------------------------
        # Condition 3: No unresolved publication-blocking right-of-reply threads
        # ------------------------------------------------------------------
        try:
            blocking_windows = await comms.get_publication_blocking_windows()
            # Filter to windows tied to this article via article_dependencies
            deps = await comms.get_unresolved_dependencies(article_id)
            dep_thread_ids = {d.thread_id for d in deps if d.thread_id}
            blocking_for_article = [
                w for w in blocking_windows
                if w.thread_id in dep_thread_ids
            ]
            unresolved_ror_count = len(blocking_for_article)
            if unresolved_ror_count > 0:
                thread_ids = [w.thread_id for w in blocking_for_article]
                failure_reasons.append(
                    f"Unresolved publication-blocking right-of-reply threads for "
                    f"article '{article_id}': {thread_ids}"
                )
                logger.warning(
                    f"publication_gate: article='{article_id}' "
                    f"FAIL condition 3 — {unresolved_ror_count} blocking RoR threads: {thread_ids}"
                )
        except Exception as e:
            failure_reasons.append(f"Error checking right-of-reply windows: {e}")
            logger.error(f"publication_gate: condition 3 error: {e}")

        # ------------------------------------------------------------------
        # Condition 4: All figures in draft are in locked_figures (if draft provided)
        # ------------------------------------------------------------------
        if draft_result is not None:
            try:
                locked_figure_ids = {f.figure_id for f in canon.get_locked_figures()}
                figures_used: list[str] = []
                # Handle both DraftSectionResult (single) and list of results
                if hasattr(draft_result, "draft") and draft_result.draft is not None:
                    figures_used = draft_result.draft.figures_used or []
                elif isinstance(draft_result, list):
                    for dr in draft_result:
                        if hasattr(dr, "draft") and dr.draft is not None:
                            figures_used.extend(dr.draft.figures_used or [])

                unlocked = [fid for fid in figures_used if fid not in locked_figure_ids]
                unlocked_figure_count = len(unlocked)
                if unlocked:
                    failure_reasons.append(
                        f"Draft references figures not in canon locked_figures: {unlocked}"
                    )
                    logger.warning(
                        f"publication_gate: article='{article_id}' "
                        f"FAIL condition 4 — unlocked figures: {unlocked}"
                    )
            except Exception as e:
                failure_reasons.append(f"Error checking locked figures: {e}")
                logger.error(f"publication_gate: condition 4 error: {e}")

        # ------------------------------------------------------------------
        # Condition 5: No adversarial review blockers (if review_result provided)
        # ------------------------------------------------------------------
        if review_result is not None:
            try:
                # Handle both single ReviewDraftResult and list
                all_blockers: list = []
                if isinstance(review_result, list):
                    for rr in review_result:
                        if hasattr(rr, "blocker_ids"):
                            all_blockers.extend(rr.blocker_ids)
                elif hasattr(review_result, "blocker_ids"):
                    all_blockers = review_result.blocker_ids

                review_blocker_count = len(all_blockers)
                if review_blocker_count > 0:
                    failure_reasons.append(
                        f"Adversarial review has {review_blocker_count} unresolved "
                        f"blocker(s): {all_blockers}"
                    )
                    logger.warning(
                        f"publication_gate: article='{article_id}' "
                        f"FAIL condition 5 — {review_blocker_count} review blockers: {all_blockers}"
                    )
            except Exception as e:
                failure_reasons.append(f"Error checking adversarial review result: {e}")
                logger.error(f"publication_gate: condition 5 error: {e}")

        # ------------------------------------------------------------------
        # Final decision
        # ------------------------------------------------------------------
        passed = len(failure_reasons) == 0

        result = PublicationGateResult(
            article_id=article_id,
            passed=passed,
            failure_reasons=failure_reasons,
            blocked_claim_count=blocked_claim_count,
            unresolved_ror_count=unresolved_ror_count,
            unlocked_figure_count=unlocked_figure_count,
            review_blocker_count=review_blocker_count,
            canon_hash=canon_hash,
        )

        if passed:
            logger.info(
                f"publication_gate: article='{article_id}' PASS — "
                f"all 5 conditions clear"
            )
        else:
            logger.warning(
                f"publication_gate: article='{article_id}' FAIL — "
                f"{len(failure_reasons)} condition(s) failed"
            )

        return result

    async def assert_passes(
        self,
        article_id: str,
        records: RecordsRepo,
        comms: CommsRepo,
        ledger: LedgerRepo,
        canon: CanonManifest,
        **kwargs,
    ) -> None:
        """
        Raises PublicationBlockedError if the gate fails.
        Pass optional draft_result=, review_result=, canon_hash= via kwargs.
        """
        result = await self.check(
            article_id=article_id,
            records=records,
            comms=comms,
            ledger=ledger,
            canon=canon,
            draft_result=kwargs.get("draft_result"),
            review_result=kwargs.get("review_result"),
            canon_hash=kwargs.get("canon_hash", ""),
        )
        if not result.passed:
            raise PublicationBlockedError(
                article_id=article_id,
                reasons=result.failure_reasons,
            )
