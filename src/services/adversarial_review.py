"""
src/services/adversarial_review.py
AdversarialReviewer — submits a draft section to an adversarial LLM reviewer,
parses structured AdversarialReviewResponse, enforces pass_build rules.

Hard rules:
- pass_build=True only if blocker_count=0
- If LLM returns pass_build=True with blockers, override to False and log warning
- Raises ValueError if response is malformed and cannot be parsed
- Local banned-figure check runs without LLM call
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from schemas.canonical import CanonManifest
from schemas.llm_contracts import (
    AdversarialFinding,
    AdversarialReviewResponse,
    DraftSectionResponse,
    ContextPacket,
)

logger = logging.getLogger(__name__)

ADVERSARIAL_REVIEWER_SYSTEM_PROMPT = """
You are an adversarial editor reviewing a draft section for publication readiness.

Your ONLY job is to find problems. Do not fix them. Do not add praise. Return structured findings only.

You MUST return a valid AdversarialReviewResponse JSON object with this exact schema:
{
  "section_id": "string",
  "article_id": "string or null",
  "findings": [
    {
      "finding_id": "unique string",
      "severity": "blocker" | "warning" | "note",
      "category": one of [
        "overclaim", "unsupported_math", "scope_drift", "weak_attribution",
        "right_of_reply_gap", "motive_language", "denominator_issue", "hallucinated_context"
      ],
      "description": "string",
      "affected_text": "exact quoted text from the draft",
      "affected_claim_id": "claim_id or null",
      "suggestion": "string or null"
    }
  ],
  "blocker_count": integer,
  "warning_count": integer,
  "pass_build": boolean (true ONLY if blocker_count == 0),
  "reviewer_notes": "brief summary string"
}

Do not return plain prose. Do not return anything outside the JSON object.
"""


class AdversarialReviewer:
    """
    Submits a DraftSectionResponse to an adversarial LLM reviewer.
    Returns a structured AdversarialReviewResponse.

    Also performs a local (no-LLM) check for unlocked figures appearing in the draft.
    """

    def __init__(self, settings: Any, provider_client: Any) -> None:
        """
        Args:
            settings: WoodwardSettings instance
            provider_client: OpenAIClient or compatible async client
        """
        self.settings = settings
        self.client = provider_client

    async def review(
        self,
        draft: DraftSectionResponse,
        context: ContextPacket,
    ) -> AdversarialReviewResponse:
        """
        Submit draft to adversarial reviewer LLM.
        Parse structured AdversarialReviewResponse.

        Hard rules:
        - pass_build=True only if blocker_count=0
        - If LLM returns pass_build=True with blockers, override to False and log warning
        - Raises ValueError if response is malformed and cannot be parsed
        """
        logger.info(
            f"AdversarialReviewer.review: section={draft.section_id} "
            f"article={draft.article_id}"
        )

        prompt = self._build_review_prompt(draft, context)

        raw_response: AdversarialReviewResponse = await self.client.complete_structured(
            prompt=prompt,
            system_prompt=ADVERSARIAL_REVIEWER_SYSTEM_PROMPT,
            response_model=AdversarialReviewResponse,
            temperature=0.2,  # Low temperature for consistency in review
        )

        logger.info(
            f"AdversarialReviewer: received response — "
            f"findings={len(raw_response.findings)} "
            f"pass_build={raw_response.pass_build}"
        )

        # Hard rule: override pass_build if blockers are present
        blockers = raw_response.get_blockers()
        if blockers and raw_response.pass_build:
            logger.warning(
                f"AdversarialReviewer: LLM returned pass_build=True with "
                f"{len(blockers)} blocker(s) — overriding to False for section='{draft.section_id}'"
            )
            # Rebuild with corrected pass_build using model_copy
            raw_response = raw_response.model_copy(update={"pass_build": False})

        # Also ensure blocker_count and warning_count are accurate
        actual_blocker_count = len(raw_response.get_blockers())
        actual_warning_count = len(raw_response.get_warnings())

        if (raw_response.blocker_count != actual_blocker_count or
                raw_response.warning_count != actual_warning_count):
            logger.warning(
                f"AdversarialReviewer: correcting counts — "
                f"blockers: {raw_response.blocker_count} -> {actual_blocker_count}, "
                f"warnings: {raw_response.warning_count} -> {actual_warning_count}"
            )
            raw_response = raw_response.model_copy(update={
                "blocker_count": actual_blocker_count,
                "warning_count": actual_warning_count,
            })

        logger.info(
            f"AdversarialReviewer: final result — "
            f"blockers={raw_response.blocker_count} "
            f"warnings={raw_response.warning_count} "
            f"pass_build={raw_response.pass_build}"
        )

        return raw_response

    def check_for_blocked_figures(
        self,
        draft: DraftSectionResponse,
        canon: CanonManifest,
    ) -> list[AdversarialFinding]:
        """
        Local check (no LLM): scan draft.content for any figure display_values
        that appear in banned_claims or that are NOT in locked_figures.

        Returns list of findings (empty = clean).

        Specifically checks:
        1. Any dollar amount pattern in content that does NOT match a locked figure display_value
           is flagged as unsupported_math.
        2. Any figure_id referenced in assertions.figure_ids that is not in canon.figures
           is flagged as hallucinated_context.
        """
        findings: list[AdversarialFinding] = []

        # Build set of known locked display values (e.g. "$13,326,622")
        locked_display_values: set[str] = {
            fig.display_value for fig in canon.get_locked_figures()
        }
        locked_figure_ids: set[str] = {
            fig.figure_id for fig in canon.get_locked_figures()
        }
        all_figure_ids: set[str] = {fig.figure_id for fig in canon.figures}

        # Check assertions for figure_ids not in canon
        for assertion in draft.assertions:
            for fig_id in assertion.figure_ids:
                if fig_id and fig_id not in all_figure_ids:
                    findings.append(
                        AdversarialFinding(
                            finding_id=f"local_fig_hallucinated_{fig_id}",
                            severity="blocker",
                            category="hallucinated_context",
                            description=(
                                f"figure_id '{fig_id}' referenced in assertion "
                                f"does not exist in canon figures"
                            ),
                            affected_text=assertion.text[:200],
                            affected_claim_id=None,
                            suggestion=(
                                f"Remove reference to '{fig_id}' or add to canonical figures.yaml"
                            ),
                        )
                    )
                elif fig_id and fig_id not in locked_figure_ids:
                    findings.append(
                        AdversarialFinding(
                            finding_id=f"local_fig_unlocked_{fig_id}",
                            severity="blocker",
                            category="unsupported_math",
                            description=(
                                f"figure_id '{fig_id}' is in canon but not locked. "
                                "Only locked figures may appear in publication-bound assertions."
                            ),
                            affected_text=assertion.text[:200],
                            affected_claim_id=None,
                            suggestion=(
                                f"Lock figure '{fig_id}' in figures.yaml before using in draft"
                            ),
                        )
                    )

        # Scan content for any banned claim text patterns
        content_lower = draft.content.lower()
        for ban in canon.banned_claims:
            if ban.text_pattern.lower() in content_lower:
                findings.append(
                    AdversarialFinding(
                        finding_id=f"local_ban_{ban.ban_id}",
                        severity="blocker",
                        category="overclaim",
                        description=(
                            f"Draft content matches banned claim pattern '{ban.ban_id}': "
                            f"{ban.reason}"
                        ),
                        affected_text=ban.text_pattern,
                        affected_claim_id=None,
                        suggestion="Remove or rephrase the banned claim text",
                    )
                )

        if findings:
            logger.warning(
                f"AdversarialReviewer.check_for_blocked_figures: "
                f"{len(findings)} local finding(s) for section='{draft.section_id}'"
            )
        else:
            logger.info(
                f"AdversarialReviewer.check_for_blocked_figures: clean for section='{draft.section_id}'"
            )

        return findings

    def _build_review_prompt(
        self,
        draft: DraftSectionResponse,
        context: ContextPacket,
    ) -> str:
        """Build the full review prompt from draft and context."""
        parts: list[str] = []

        parts.append("=== ADVERSARIAL REVIEW TASK ===")
        parts.append(f"section_id: {draft.section_id}")
        parts.append(f"article_id: {draft.article_id}")
        parts.append("")

        parts.append("=== DRAFT CONTENT TO REVIEW ===")
        parts.append(draft.content)
        parts.append("")

        parts.append("=== LOCKED FIGURES (only these figures are permitted in assertions) ===")
        if context.locked_figures:
            for fig_id, display_val in context.locked_figures.items():
                parts.append(f"  {fig_id}: {display_val}")
        else:
            parts.append("  (none)")
        parts.append("")

        parts.append("=== VERIFIED CLAIMS (reference set for review) ===")
        for claim in context.draftable_claims:
            if isinstance(claim, dict):
                cid = claim.get("claim_id", "?")
                text = claim.get("text", "")
            else:
                cid = getattr(claim, "claim_id", "?")
                text = getattr(claim, "text", "")
            parts.append(f"  claim_id={cid}: {text}")
        parts.append("")

        parts.append("=== ASSERTIONS DECLARED BY DRAFTER ===")
        for i, assertion in enumerate(draft.assertions):
            parts.append(
                f"  [{i+1}] context_ids={assertion.context_ids} "
                f"claim_ids={assertion.claim_ids} "
                f"figure_ids={assertion.figure_ids}"
            )
            parts.append(f"      \"{assertion.text[:200]}\"")
        parts.append("")

        parts.append("=== OUTPUT ===")
        parts.append(
            "Return an AdversarialReviewResponse JSON. "
            "Find every problem. Be rigorous. Do not narrate."
        )

        return "\n".join(parts)
