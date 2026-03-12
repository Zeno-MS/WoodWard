"""
src/workflows/review_draft.py
review_draft workflow — runs adversarial review on a draft section.

Produces a ReviewDraftResult artifact written to runs/{run_id}/.

Steps:
1. Run local banned-figure check (no LLM)
2. Call AdversarialReviewer.review()
3. Combine findings (local + LLM)
4. Set can_advance = (total blockers == 0)
5. Write runs/{run_id}/review_{section_id}.json
6. Return ReviewDraftResult

If can_advance=False, the section cannot proceed to publication_gate.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from schemas.canonical import CanonManifest
from schemas.llm_contracts import (
    AdversarialFinding,
    AdversarialReviewResponse,
    ContextPacket,
    DraftSectionResponse,
)
from src.core.settings import WoodwardSettings
from src.services.adversarial_review import AdversarialReviewer

logger = logging.getLogger(__name__)


@dataclass
class ReviewDraftResult:
    """
    Result of the review_draft workflow for one section.
    can_advance=True only if there are zero blockers across all findings.
    """
    section_id: str
    article_id: str
    run_id: str
    review: AdversarialReviewResponse
    blocker_ids: list[str] = field(default_factory=list)     # finding_ids for blockers
    can_advance: bool = False                                  # True only if no blockers
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    canon_hash: str = ""
    artifact_path: Optional[str] = None

    def summary(self) -> str:
        return (
            f"ReviewDraftResult section={self.section_id} article={self.article_id} "
            f"can_advance={self.can_advance} blockers={len(self.blocker_ids)} "
            f"total_findings={len(self.review.findings)}"
        )


async def review_draft(
    draft: DraftSectionResponse,
    context: ContextPacket,
    run_id: str,
    settings: WoodwardSettings,
    canon: CanonManifest,
    provider_client: Any,
) -> ReviewDraftResult:
    """
    Run adversarial review on a draft section.

    Steps:
    1. Run local banned-figure check (no LLM)
    2. Call AdversarialReviewer.review() via LLM
    3. Combine findings (local + LLM)
    4. Set can_advance = (total blockers == 0)
    5. Write runs/{run_id}/review_{section_id}.json
    6. Return ReviewDraftResult

    Args:
        draft: The DraftSectionResponse to review
        context: The ContextPacket used to create the draft
        run_id: Unique run identifier
        settings: WoodwardSettings
        canon: CanonManifest (for local checks)
        provider_client: LLM client with complete_structured() method
    """
    logger.info(
        f"review_draft: section={draft.section_id} article={draft.article_id} run_id={run_id}"
    )

    reviewer = AdversarialReviewer(settings=settings, provider_client=provider_client)

    # Step 1: Local banned-figure check (no LLM call)
    local_findings: list[AdversarialFinding] = reviewer.check_for_blocked_figures(draft, canon)
    logger.info(
        f"review_draft: local check complete — {len(local_findings)} finding(s)"
    )

    # Step 2: LLM adversarial review
    llm_review: AdversarialReviewResponse = await reviewer.review(draft, context)
    logger.info(
        f"review_draft: LLM review complete — "
        f"{len(llm_review.findings)} finding(s) from LLM"
    )

    # Step 3: Combine findings (local findings prepended — they are definitive)
    all_findings = local_findings + llm_review.findings

    # Step 4: Recompute pass_build and counts from combined findings
    total_blockers = [f for f in all_findings if f.severity == "blocker"]
    total_warnings = [f for f in all_findings if f.severity == "warning"]
    can_advance = len(total_blockers) == 0

    if local_findings and llm_review.pass_build and not can_advance:
        logger.warning(
            f"review_draft: LLM passed but local check found blockers — "
            f"overriding can_advance=False for section='{draft.section_id}'"
        )

    # Build merged review response
    merged_review = AdversarialReviewResponse(
        section_id=draft.section_id,
        article_id=draft.article_id,
        findings=all_findings,
        blocker_count=len(total_blockers),
        warning_count=len(total_warnings),
        pass_build=can_advance,
        reviewer_notes=(
            f"Combined review: {len(local_findings)} local + "
            f"{len(llm_review.findings)} LLM findings. "
            + (llm_review.reviewer_notes or "")
        ).strip(),
        reviewer_model=llm_review.reviewer_model,
    )

    blocker_ids = [f.finding_id for f in total_blockers]

    # Step 5: Write artifact
    artifact_path: Optional[str] = None
    runs_path = settings.runs_path_obj / run_id
    try:
        runs_path.mkdir(parents=True, exist_ok=True)
        artifact_file = runs_path / f"review_{draft.section_id}.json"

        artifact_data = {
            "section_id": draft.section_id,
            "article_id": draft.article_id,
            "run_id": run_id,
            "can_advance": can_advance,
            "blocker_ids": blocker_ids,
            "canon_hash": context.canon_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "review": merged_review.model_dump(),
        }

        artifact_file.write_text(
            json.dumps(artifact_data, indent=2, default=str),
            encoding="utf-8",
        )
        artifact_path = str(artifact_file)
        logger.info(f"review_draft: artifact written to {artifact_path}")

    except Exception as exc:
        logger.error(f"review_draft: failed to write artifact: {exc}")
        # Artifact write failure does not hard-stop — log and continue

    result = ReviewDraftResult(
        section_id=draft.section_id,
        article_id=draft.article_id,
        run_id=run_id,
        review=merged_review,
        blocker_ids=blocker_ids,
        can_advance=can_advance,
        canon_hash=context.canon_hash,
        artifact_path=artifact_path,
    )

    logger.info(result.summary())
    return result
