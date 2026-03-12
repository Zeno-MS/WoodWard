"""
src/services/claim_support_checker.py
ClaimSupportChecker — checks whether a claim has sufficient public-citable support
to be allowed into a publication-bound draft context.

Rules per claim:
  - status must be 'verified' (not draft/blocked/pending_review/superseded)
  - public_citable must be True (integer 1 in DB)
  - support_chain_complete must be True (integer 1 in DB)
  - At least one ClaimSupport row must exist linked to the claim
  - right_of_reply_required=True: log a warning but do NOT block drafting
    (right-of-reply is a pre-publication gate, not a pre-draft gate)

All checks are non-raising — results are always returned. The caller decides
whether to hard-stop.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from schemas.canonical import CanonManifest, SourcePolicy
from schemas.records_models import Claim
from src.repositories.records_repo import RecordsRepo

logger = logging.getLogger(__name__)


@dataclass
class ClaimSupportResult:
    """
    Result of checking a single claim for draft eligibility.

    reason values:
      'ok'                      — claim passed all checks, draftable
      'not_verified'            — status is not 'verified'
      'blocked_status'          — status is 'blocked'
      'not_public_citable'      — public_citable is False
      'no_support_chain'        — support_chain_complete is False
      'no_public_support_docs'  — no ClaimSupport rows exist for the claim
    """
    claim_id: str
    draftable: bool
    reason: str
    right_of_reply_warning: bool = False
    notes: str = ""


class ClaimSupportChecker:
    """
    Checks whether a claim has sufficient public-citable support
    to be allowed into a publication-bound draft context.
    """

    async def check(
        self,
        claim_id: str,
        records: RecordsRepo,
        policy: SourcePolicy,
    ) -> ClaimSupportResult:
        """
        Returns a ClaimSupportResult indicating whether the claim can proceed to drafting.

        Fetches the claim from records.db, then applies the publication-readiness rules.
        Returns a result even if the claim does not exist (draftable=False, reason='not_verified').
        """
        claim: Optional[Claim] = await records.get_claim(claim_id)

        if claim is None:
            return ClaimSupportResult(
                claim_id=claim_id,
                draftable=False,
                reason="not_verified",
                notes=f"Claim '{claim_id}' not found in records.db",
            )

        return await self._evaluate(claim, records, policy)

    async def check_batch(
        self,
        claim_ids: list[str],
        records: RecordsRepo,
        policy: SourcePolicy,
    ) -> list[ClaimSupportResult]:
        """
        Check multiple claims. Returns results for all, including failures.
        Order of results matches order of claim_ids.
        """
        results: list[ClaimSupportResult] = []
        for cid in claim_ids:
            result = await self.check(cid, records, policy)
            results.append(result)
        return results

    def filter_to_draftable(
        self,
        results: list[ClaimSupportResult],
    ) -> tuple[list[ClaimSupportResult], list[ClaimSupportResult]]:
        """
        Split results into (draftable, blocked).
        Never raises — always returns both lists.
        Right-of-reply warnings are preserved in the draftable list.
        """
        draftable: list[ClaimSupportResult] = []
        blocked: list[ClaimSupportResult] = []

        for r in results:
            if r.draftable:
                draftable.append(r)
            else:
                blocked.append(r)

        return draftable, blocked

    # ------------------------------------------------------------------
    # Internal evaluation logic
    # ------------------------------------------------------------------

    async def _evaluate(
        self,
        claim: Claim,
        records: RecordsRepo,
        policy: SourcePolicy,
    ) -> ClaimSupportResult:
        """Apply all draftability rules to a loaded Claim object."""

        # Hard block — blocked claims are never draftable
        if claim.status == "blocked":
            return ClaimSupportResult(
                claim_id=claim.claim_id,
                draftable=False,
                reason="blocked_status",
                notes=f"Claim status is 'blocked'",
            )

        # Only 'verified' claims are draftable
        if claim.status != "verified":
            return ClaimSupportResult(
                claim_id=claim.claim_id,
                draftable=False,
                reason="not_verified",
                notes=f"Claim status is '{claim.status}', must be 'verified'",
            )

        # Must be public-citable
        if not claim.is_public_citable:
            return ClaimSupportResult(
                claim_id=claim.claim_id,
                draftable=False,
                reason="not_public_citable",
                notes="Claim public_citable=0 — not eligible for public drafting",
            )

        # Support chain must be declared complete
        if claim.support_chain_complete != 1:
            return ClaimSupportResult(
                claim_id=claim.claim_id,
                draftable=False,
                reason="no_support_chain",
                notes="Claim support_chain_complete=0 — incomplete support chain",
            )

        # At least one support document row must exist
        support_docs = await records.get_claim_support(claim.claim_id)
        if not support_docs:
            return ClaimSupportResult(
                claim_id=claim.claim_id,
                draftable=False,
                reason="no_public_support_docs",
                notes=(
                    f"Claim '{claim.claim_id}' has support_chain_complete=1 "
                    "but no ClaimSupport rows exist in records.db"
                ),
            )

        # right_of_reply_required: warn but do not block drafting
        ror_warning = bool(claim.right_of_reply_required)
        if ror_warning:
            logger.warning(
                f"[ClaimSupportChecker] Claim '{claim.claim_id}' has right_of_reply_required=True. "
                "This claim is draftable but must not be published until right-of-reply is resolved."
            )

        return ClaimSupportResult(
            claim_id=claim.claim_id,
            draftable=True,
            reason="ok",
            right_of_reply_warning=ror_warning,
            notes="All draftability checks passed",
        )
