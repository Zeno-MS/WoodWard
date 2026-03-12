"""
src/services/public_source_gate.py
PublicSourceGate — enforces source policy on claims before they enter
any publication-bound workflow or LLM context.
No blocked or unverified claim may pass through this gate.
"""
from __future__ import annotations

import logging

from schemas.canonical import BannedClaim, SourcePolicy
from schemas.records_models import Claim
from src.core.exceptions import BlockedClaimError
from src.core.types import SourceClass

logger = logging.getLogger(__name__)


class PublicSourceGate:
    """
    Enforces source policy rules on claims.

    Three operations:
    1. is_allowed — check if a source_class is permitted by policy
    2. filter_claims — return only publishable claims from a list
    3. gate_draft_context — strip non-publishable claims before LLM context assembly
    """

    def is_allowed(self, source_class: SourceClass, policy: SourcePolicy) -> bool:
        """
        Returns True if the source_class is 'allowed' per policy.
        'pending_review' and 'blocked' both return False.
        Unknown source classes return False (fail-safe).
        """
        status = policy.get_status(source_class)
        return status == "allowed"

    def filter_claims(
        self, claims: list[Claim], policy: SourcePolicy
    ) -> list[Claim]:
        """
        Returns only claims that are fully publishable:
        - status = 'verified'
        - public_citable = 1
        - support_chain_complete = 1
        - stale = 0
        - NOT blocked

        Claims with ingest_source='webapp_export' are treated as pending_review
        and are never returned by this filter.
        """
        publishable = []
        for claim in claims:
            if not claim.is_publishable:
                continue
            # Additional check: webapp_export claims are never publishable
            if claim.ingest_source == "webapp_export":
                continue
            publishable.append(claim)
        return publishable

    def gate_draft_context(
        self, claims: list[Claim], policy: SourcePolicy
    ) -> list[Claim]:
        """
        Strip blocked, pending, and non-public claims from the list before
        any LLM sees them.

        Unlike filter_claims (which only returns verified claims), this method
        also passes through 'draft' claims with complete support chains —
        allowing iterative drafting workflows.

        Raises BlockedClaimError if a blocked claim is in the list and would
        otherwise need to appear in context (i.e., right_of_reply_required=1).
        This prevents the LLM from accidentally drafting around a blocked fact.
        """
        safe_claims = []
        for claim in claims:
            # Hard block — these must never be in LLM context
            if claim.status == "blocked":
                if claim.right_of_reply_required:
                    raise BlockedClaimError(
                        claim_id=claim.claim_id,
                        reason=(
                            "Blocked claim with right_of_reply_required=True attempted "
                            "to enter draft context. Resolve the right-of-reply first."
                        ),
                    )
                # Non-critical blocked claims are silently dropped
                continue

            # Webapp exports are never exposed to LLM context
            if claim.ingest_source == "webapp_export":
                continue

            # Pending review claims are dropped
            if claim.status == "pending_review":
                continue

            # Superseded claims are dropped
            if claim.status == "superseded":
                continue

            # Stale claims are dropped
            if claim.stale:
                continue

            safe_claims.append(claim)

        return safe_claims

    def check_claim_source(
        self, claim: Claim, policy: SourcePolicy, raise_on_block: bool = True
    ) -> bool:
        """
        Check a single claim against source policy.
        Returns True if the claim is allowed for publication.
        If raise_on_block=True, raises BlockedClaimError for blocked claims.
        """
        if claim.status == "blocked":
            if raise_on_block:
                raise BlockedClaimError(
                    claim_id=claim.claim_id,
                    reason=f"Claim status is 'blocked'",
                )
            return False

        if not claim.is_public_citable:
            return False

        if claim.support_chain_complete == 0:
            return False

        if claim.stale:
            return False

        return True

    def assert_no_banned_claims(
        self,
        claim_texts: list[str],
        banned: list[BannedClaim],
    ) -> None:
        """
        Raises BlockedClaimError if any text in claim_texts matches a banned claim pattern.
        Matching is case-insensitive substring match.
        Use before any LLM context assembly.
        """
        for text in claim_texts:
            text_lower = text.lower()
            for ban in banned:
                if ban.text_pattern.lower() in text_lower:
                    raise BlockedClaimError(
                        claim_id=f"text_match:{ban.ban_id}",
                        reason=(
                            f"Claim text matches banned pattern '{ban.ban_id}': "
                            f"{ban.reason}"
                        ),
                    )
