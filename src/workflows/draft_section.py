"""
src/workflows/draft_section.py
draft_section workflow — Phase 4 full implementation.

Gate steps (always run):
  1. Load claims for the article from records.db
  2. Run public_source_gate.gate_draft_context() — strips blocked/pending/stale claims
  3. Run claim_support_checker.check_batch() — validates each claim's support chain
  4. Check for banned claim text patterns via public_source_gate.assert_no_banned_claims()
  5. Inject locked figures from canon (do NOT let LLM invent figures)
  6. Return early with gate_only=True if provider_client is None (Phase 3 mode)

Draft steps (Phase 4, only when provider_client is supplied):
  7. Assemble ContextPacket via ContextAssembler
  8. Call ArticleDrafter.draft_section()
  9. Validate all context_ids (hard-stop on hallucination)
 10. Write runs/{run_id}/draft_{section_id}.json
 11. Return DraftSectionResult
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from schemas.canonical import CanonManifest, SourcePolicy
from schemas.llm_contracts import ContextPacket, DraftSectionResponse
from schemas.records_models import Claim
from src.core.exceptions import BlockedClaimError, HallucinatedContextError
from src.core.settings import WoodwardSettings
from src.repositories.ledger_repo import LedgerRepo
from src.repositories.records_repo import RecordsRepo
from src.services.claim_support_checker import ClaimSupportChecker, ClaimSupportResult
from src.services.context_assembler import ContextAssembler
from src.services.public_source_gate import PublicSourceGate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass — replaces Phase 3 DraftSectionGateResult
# ---------------------------------------------------------------------------

@dataclass
class DraftSectionResult:
    """
    Result from the Phase 4 draft_section workflow.

    gate_passed=True means the draft context is clean.
    If provider_client was None (gate-only mode), draft=None.
    If draft is present, context_ids have been validated.

    draftable_claims and blocked_claims are preserved for backward compatibility
    with Phase 3 tests that accessed the old DraftSectionGateResult fields.
    """
    article_id: str
    section_id: str
    run_id: str
    gate_passed: bool = False
    gate_failure_reason: Optional[str] = None
    draft: Optional[DraftSectionResponse] = None   # None if gate failed or gate_only mode
    context: Optional[ContextPacket] = None         # The assembled ContextPacket (if drafted)
    draftable_claim_count: int = 0
    blocked_claim_count: int = 0
    # Phase 3 compatibility — ClaimSupportResult lists
    draftable_claims: list = field(default_factory=list)   # list[ClaimSupportResult]
    blocked_claims: list = field(default_factory=list)     # list[ClaimSupportResult]
    injected_figures: dict[str, float] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    canon_hash: str = ""
    artifact_path: Optional[str] = None

    @property
    def draftable_claim_ids(self) -> list[str]:
        """Phase 3 compatibility: claim_ids of draftable claims."""
        return [r.claim_id for r in self.draftable_claims]

    @property
    def blocked_claim_ids(self) -> list[str]:
        """Phase 3 compatibility: claim_ids of blocked claims."""
        return [r.claim_id for r in self.blocked_claims]

    def summary(self) -> str:
        return (
            f"DraftSectionResult article={self.article_id} section={self.section_id} "
            f"gate_passed={self.gate_passed} "
            f"draftable={self.draftable_claim_count} blocked={self.blocked_claim_count} "
            f"draft={'present' if self.draft else 'None'}"
        )


# ---------------------------------------------------------------------------
# Legacy result alias — kept for Phase 3 test compatibility
# ---------------------------------------------------------------------------

@dataclass
class DraftSectionGateResult:
    """
    Phase 3 gate-only result shape. Preserved for backward test compatibility.
    New code should use DraftSectionResult.
    """
    article_id: str
    section_id: str
    run_id: str
    draftable_claims: list[ClaimSupportResult] = field(default_factory=list)
    blocked_claims: list[ClaimSupportResult] = field(default_factory=list)
    injected_figures: dict[str, float] = field(default_factory=dict)
    gate_passed: bool = False
    gate_failure_reason: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def draftable_claim_ids(self) -> list[str]:
        return [r.claim_id for r in self.draftable_claims]

    @property
    def blocked_claim_ids(self) -> list[str]:
        return [r.claim_id for r in self.blocked_claims]

    def summary(self) -> str:
        return (
            f"DraftSectionGate article={self.article_id} section={self.section_id} "
            f"gate_passed={self.gate_passed} "
            f"draftable={len(self.draftable_claims)} blocked={len(self.blocked_claims)} "
            f"figures={len(self.injected_figures)}"
        )


# ---------------------------------------------------------------------------
# Main workflow function
# ---------------------------------------------------------------------------

async def draft_section(
    article_id: str,
    section_id: str,
    run_id: str,
    settings: WoodwardSettings,
    records: RecordsRepo,
    ledger: LedgerRepo,
    canon: CanonManifest,
    provider_client: Any = None,  # If None, return gate result only (Phase 3 mode)
    canon_hash: str = "",
) -> DraftSectionResult:
    """
    Full Phase 4 implementation.

    Gate steps always run. Draft steps run only if provider_client is provided.

    Gate failure does NOT raise — gate_passed=False captures the reason.
    Only BlockedClaimError from a critical (right_of_reply_required + blocked) claim
    hard-stops the workflow via PublicSourceGate.gate_draft_context().

    Injected figures come ONLY from canon.get_locked_figures() — never from LLM output.

    Args:
        article_id: Article identifier
        section_id: Section identifier within the article
        run_id: Unique run identifier for artifact storage
        settings: WoodwardSettings
        records: RecordsRepo instance
        ledger: LedgerRepo instance
        canon: CanonManifest
        provider_client: LLM client (OpenAIClient or compatible). If None, gate-only mode.
        canon_hash: Canon hash string to embed in result
    """
    logger.info(
        f"draft_section: article={article_id} section={section_id} "
        f"run_id={run_id} llm={'yes' if provider_client else 'gate-only'}"
    )

    gate = PublicSourceGate()
    checker = ClaimSupportChecker()
    policy: SourcePolicy = canon.source_policy

    # ------------------------------------------------------------------
    # Step 1: Load claims for this article from records.db
    # ------------------------------------------------------------------
    all_claims: list[Claim] = await records.get_claims_for_article(article_id)

    if not all_claims:
        logger.warning(
            f"draft_section: no claims found in records.db for article '{article_id}'. "
            "Seeding from canon may not have been run yet."
        )

    # ------------------------------------------------------------------
    # Step 2: Run public_source_gate.gate_draft_context()
    # ------------------------------------------------------------------
    try:
        safe_claims: list[Claim] = gate.gate_draft_context(all_claims, policy)
    except BlockedClaimError as e:
        logger.error(f"draft_section: gate_draft_context raised BlockedClaimError: {e}")
        return DraftSectionResult(
            article_id=article_id,
            section_id=section_id,
            run_id=run_id,
            gate_passed=False,
            gate_failure_reason=f"CRITICAL_BLOCKED_CLAIM: {e}",
            canon_hash=canon_hash,
        )

    # ------------------------------------------------------------------
    # Step 3: Run claim_support_checker.check_batch()
    # ------------------------------------------------------------------
    claim_ids = [c.claim_id for c in safe_claims]
    check_results: list[ClaimSupportResult] = await checker.check_batch(
        claim_ids, records, policy
    )

    draftable, blocked = checker.filter_to_draftable(check_results)

    # Build claim lookup for context assembly
    draftable_claim_ids: set[str] = {r.claim_id for r in draftable}
    draftable_claim_objects = [c for c in safe_claims if c.claim_id in draftable_claim_ids]

    # ------------------------------------------------------------------
    # Step 4: Check for banned claim text patterns
    # ------------------------------------------------------------------
    all_texts = [c.text for c in safe_claims]
    try:
        gate.assert_no_banned_claims(all_texts, canon.banned_claims)
    except BlockedClaimError as e:
        logger.error(f"draft_section: banned claim pattern detected: {e}")
        return DraftSectionResult(
            article_id=article_id,
            section_id=section_id,
            run_id=run_id,
            draftable_claim_count=len(draftable),
            blocked_claim_count=len(blocked),
            draftable_claims=draftable,
            blocked_claims=blocked,
            gate_passed=False,
            gate_failure_reason=f"BANNED_CLAIM_PATTERN: {e}",
            canon_hash=canon_hash,
        )

    # ------------------------------------------------------------------
    # Step 5: Inject locked figures from canon
    # ------------------------------------------------------------------
    injected_figures: dict[str, float] = {}
    for fig in canon.get_locked_figures():
        injected_figures[fig.figure_id] = fig.value

    logger.info(
        f"draft_section: {len(injected_figures)} locked figures injected "
        f"for article '{article_id}'"
    )

    # ------------------------------------------------------------------
    # Gate decision
    # ------------------------------------------------------------------
    if not draftable and all_claims:
        gate_passed = False
        gate_failure_reason = (
            f"No draftable claims remain after gate for article '{article_id}'. "
            f"All {len(check_results)} claims were blocked."
        )
        logger.warning(gate_failure_reason)
    else:
        gate_passed = True
        gate_failure_reason = None

    if not gate_passed:
        return DraftSectionResult(
            article_id=article_id,
            section_id=section_id,
            run_id=run_id,
            draftable_claim_count=len(draftable),
            blocked_claim_count=len(blocked),
            draftable_claims=draftable,
            blocked_claims=blocked,
            injected_figures=injected_figures,
            gate_passed=False,
            gate_failure_reason=gate_failure_reason,
            canon_hash=canon_hash,
        )

    # ------------------------------------------------------------------
    # Step 6: Return gate-only result if no provider_client (Phase 3 mode)
    # ------------------------------------------------------------------
    if provider_client is None:
        logger.info(
            f"draft_section: gate-only mode (no provider_client) — "
            f"returning without LLM call"
        )
        return DraftSectionResult(
            article_id=article_id,
            section_id=section_id,
            run_id=run_id,
            draftable_claim_count=len(draftable),
            blocked_claim_count=len(blocked),
            draftable_claims=draftable,
            blocked_claims=blocked,
            injected_figures=injected_figures,
            gate_passed=True,
            gate_failure_reason=None,
            canon_hash=canon_hash,
        )

    # ------------------------------------------------------------------
    # Step 7: Assemble ContextPacket via ContextAssembler
    # ------------------------------------------------------------------
    assembler = ContextAssembler()
    context: ContextPacket = await assembler.assemble(
        article_id=article_id,
        section_id=section_id,
        run_id=run_id,
        task_profile="article_draft",
        draftable_claims=draftable_claim_objects,
        canon=canon,
        records=records,
        ledger=ledger,
        canon_hash=canon_hash,
    )

    logger.info(
        f"draft_section: context assembled — "
        f"claims={len(context.draftable_claims)} "
        f"chunks={len(context.support_context)} "
        f"figures={len(context.locked_figures)}"
    )

    # ------------------------------------------------------------------
    # Step 8: Call ArticleDrafter.draft_section()
    # ------------------------------------------------------------------
    from src.services.article_drafter import ArticleDrafter

    drafter = ArticleDrafter(settings=settings, provider_client=provider_client)

    try:
        draft: DraftSectionResponse = await drafter.draft_section(
            context=context,
            records=records,
        )
    except HallucinatedContextError as exc:
        logger.error(
            f"draft_section: HallucinatedContextError — hard-stopping: {exc}"
        )
        # Hard-stop: hallucinated context_ids are a build failure
        raise

    # ------------------------------------------------------------------
    # Step 9: context_id validation already done inside ArticleDrafter
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Step 10: Write runs/{run_id}/draft_{section_id}.json
    # ------------------------------------------------------------------
    artifact_path: Optional[str] = None
    runs_path = settings.runs_path_obj / run_id
    try:
        runs_path.mkdir(parents=True, exist_ok=True)
        artifact_file = runs_path / f"draft_{section_id}.json"

        artifact_data = {
            "article_id": article_id,
            "section_id": section_id,
            "run_id": run_id,
            "gate_passed": True,
            "draftable_claim_count": len(draftable),
            "blocked_claim_count": len(blocked),
            "canon_hash": canon_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "draft": draft.model_dump(),
        }

        artifact_file.write_text(
            json.dumps(artifact_data, indent=2, default=str),
            encoding="utf-8",
        )
        artifact_path = str(artifact_file)
        logger.info(f"draft_section: artifact written to {artifact_path}")

    except Exception as exc:
        logger.error(f"draft_section: failed to write artifact: {exc}")
        # Artifact write failure does not hard-stop — log and continue

    result = DraftSectionResult(
        article_id=article_id,
        section_id=section_id,
        run_id=run_id,
        gate_passed=True,
        gate_failure_reason=None,
        draft=draft,
        context=context,
        draftable_claim_count=len(draftable),
        blocked_claim_count=len(blocked),
        draftable_claims=draftable,
        blocked_claims=blocked,
        injected_figures=injected_figures,
        canon_hash=canon_hash,
        artifact_path=artifact_path,
    )

    logger.info(result.summary())
    return result
