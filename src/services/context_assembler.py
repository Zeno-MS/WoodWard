"""
src/services/context_assembler.py
Context assembler — builds the ContextPacket passed to the LLM drafter.

Task profiles determine what gets included:
- article_draft: records + ledger + claims (balanced)
- figure_verification: ledger-heavy
- adversarial_review: records + claims + ledger
- reply_packet: comms-heavy

Key invariants:
1. locked_figures always comes from canon — never from records or LLM output
2. support_context comes from records.db chunks linked to draftable claims
3. task_instructions injected from a constant template, not from prior LLM output
4. blocked/pending claims must NOT appear in draftable_claims (caller's responsibility)
"""
from __future__ import annotations

import logging
from typing import Any

from schemas.canonical import CanonManifest
from schemas.llm_contracts import ContextPacket
from src.repositories.ledger_repo import LedgerRepo
from src.repositories.records_repo import RecordsRepo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task instruction templates — embedded as constants, never from LLM output
# ---------------------------------------------------------------------------

ARTICLE_DRAFT_INSTRUCTIONS = """
You are a journalist drafting a section for an investigative article about Vancouver Public Schools' staffing vendor spending.

MANDATORY RULES:
1. Use ONLY the figures in the locked_figures dict. Do not invent, round, or modify any dollar amount.
2. Every factual assertion in your output must map to a context_id from the support_context provided.
3. Unresolved questions (marked as blocked claims) must be stated as questions, not facts.
4. Do not attribute motive, intent, or wrongdoing to any individual.
5. Write in plain journalistic prose. No legal language. No pleading tone.
6. Right-of-reply claims must appear in right_of_reply_flags, not as assertions.
7. Return a DraftSectionResponse JSON object. Do not return plain prose.

GROUNDING:
- Locked figures (use exactly): {locked_figures}
- Available claims (these are verified, public-citable): {claim_count} claims
- Support context: {chunk_count} source document excerpts
"""

ADVERSARIAL_REVIEW_INSTRUCTIONS = """
You are an adversarial editor reviewing a draft section for publication readiness.

Your job: find problems, not fix them. Return structured findings only.

Check for:
1. overclaim — any assertion stated as fact that is not fully supported
2. unsupported_math — any figure that does not appear in locked_figures
3. scope_drift — vendor totals that mix included/excluded vendors
4. weak_attribution — "the district" or passive constructions that obscure the source
5. right_of_reply_gap — claims about named individuals or specific decisions that need a response opportunity
6. motive_language — any language implying intent or culpability without public evidence
7. denominator_issue — mixing budgeted and actual figures without disclosure
8. hallucinated_context — any assertion with a context_id that does not appear in the support context

Severity:
- blocker: must be fixed before any publication
- warning: should be fixed but does not block
- note: optional improvement

Return an AdversarialReviewResponse JSON. Do not narrate — only return the structured object.
"""

REPLY_PACKET_INSTRUCTIONS = """
You are a journalist composing a right-of-reply outreach packet.

Your job: draft a professional, factual letter requesting comment on specific claims.

MANDATORY RULES:
1. Reference only the claims listed in the draftable_claims list.
2. Do not make new factual assertions — only reference verified claims.
3. Do not attribute bad faith or motive to the recipient.
4. Return a ReplyPacketResponse JSON object.
"""

TASK_INSTRUCTION_TEMPLATES: dict[str, str] = {
    "article_draft": ARTICLE_DRAFT_INSTRUCTIONS,
    "adversarial_review": ADVERSARIAL_REVIEW_INSTRUCTIONS,
    "reply_packet": REPLY_PACKET_INSTRUCTIONS,
    "figure_verification": ARTICLE_DRAFT_INSTRUCTIONS,  # ledger-heavy; uses same base instructions
}


# ---------------------------------------------------------------------------
# ContextAssembler
# ---------------------------------------------------------------------------

class ContextAssembler:
    """
    Assembles a ContextPacket from canon, ledger, and records repositories.

    Caller is responsible for pre-filtering draftable_claims — this class
    does not apply the PublicSourceGate or ClaimSupportChecker itself.
    It trusts the caller to pass only approved claims.
    """

    TASK_PROFILES: dict[str, dict[str, Any]] = {
        "article_draft": {
            "max_claims": 20,
            "max_support_chunks": 15,
            "include_figures": True,
            "instructions_template": "article_draft",
        },
        "adversarial_review": {
            "max_claims": 30,
            "max_support_chunks": 20,
            "include_figures": True,
            "instructions_template": "adversarial_review",
        },
        "reply_packet": {
            "max_claims": 10,
            "max_support_chunks": 5,
            "include_figures": False,
            "instructions_template": "reply_packet",
        },
        "figure_verification": {
            "max_claims": 5,
            "max_support_chunks": 10,
            "include_figures": True,
            "instructions_template": "figure_verification",
        },
    }

    async def assemble(
        self,
        article_id: str,
        section_id: str,
        run_id: str,
        task_profile: str,
        draftable_claims: list,  # Already filtered by PublicSourceGate — must not contain blocked claims
        canon: CanonManifest,
        records: RecordsRepo,
        ledger: LedgerRepo,
        canon_hash: str = "",
    ) -> ContextPacket:
        """
        Assemble a ContextPacket for the given task profile.

        Key rules:
        1. locked_figures comes from canon — never from records or LLM output
        2. support_context comes from records.db chunks linked to draftable claims
        3. task_instructions is injected from a template constant
        4. blocked/pending claims must not appear in draftable_claims (caller's responsibility)
        5. Profile limits (max_claims, max_support_chunks) are enforced here
        """
        if task_profile not in self.TASK_PROFILES:
            raise ValueError(
                f"Unknown task_profile '{task_profile}'. "
                f"Must be one of: {list(self.TASK_PROFILES.keys())}"
            )

        profile = self.TASK_PROFILES[task_profile]
        max_claims: int = profile["max_claims"]
        max_chunks: int = profile["max_support_chunks"]
        include_figures: bool = profile["include_figures"]
        instructions_key: str = profile["instructions_template"]

        logger.info(
            f"ContextAssembler.assemble: article={article_id} section={section_id} "
            f"task_profile={task_profile} claims_in={len(draftable_claims)}"
        )

        # --- Step 1: Enforce blocked claims invariant -----------------------
        # Defensively verify no blocked claims slipped through
        safe_claims = []
        for claim in draftable_claims:
            status = getattr(claim, "status", None) or (
                claim.get("status") if isinstance(claim, dict) else None
            )
            if status == "blocked":
                logger.error(
                    f"ContextAssembler: blocked claim {getattr(claim, 'claim_id', '?')} "
                    "attempted to enter context packet — dropping"
                )
                continue
            safe_claims.append(claim)

        # Enforce profile limit
        if len(safe_claims) > max_claims:
            logger.warning(
                f"ContextAssembler: truncating claims from {len(safe_claims)} to {max_claims} "
                f"per task_profile='{task_profile}'"
            )
            safe_claims = safe_claims[:max_claims]

        # --- Step 2: Serialize claims to dicts --------------------------------
        serialized_claims: list[dict] = []
        for claim in safe_claims:
            if isinstance(claim, dict):
                serialized_claims.append(claim)
            else:
                # Try Pydantic model first
                model_dump = getattr(claim, "model_dump", None)
                if model_dump is not None and callable(model_dump):
                    result = model_dump()
                    if isinstance(result, dict):
                        serialized_claims.append(result)
                        continue
                # Dataclass fallback
                import dataclasses
                if dataclasses.is_dataclass(claim):
                    serialized_claims.append(dataclasses.asdict(claim))
                else:
                    # Last resort: build dict from known attributes
                    serialized_claims.append({
                        "claim_id": getattr(claim, "claim_id", ""),
                        "status": getattr(claim, "status", ""),
                        "text": getattr(claim, "text", ""),
                        "article_id": getattr(claim, "article_id", ""),
                        "right_of_reply_required": getattr(claim, "right_of_reply_required", 0),
                        "public_citable": getattr(claim, "public_citable", 0),
                        "support_chain_complete": getattr(claim, "support_chain_complete", 0),
                        "stale": getattr(claim, "stale", 0),
                    })

        # --- Step 3: Gather support context from records.db ------------------
        support_context: list[dict] = []
        seen_chunk_ids: set[str] = set()

        for claim in safe_claims:
            if len(support_context) >= max_chunks:
                break

            claim_id = (
                claim.get("claim_id")
                if isinstance(claim, dict)
                else getattr(claim, "claim_id", None)
            )
            if not claim_id:
                continue

            try:
                supports = await records.get_claim_support(claim_id)
            except Exception as exc:
                logger.warning(
                    f"ContextAssembler: could not fetch support for claim '{claim_id}': {exc}"
                )
                continue

            for support in supports:
                if len(support_context) >= max_chunks:
                    break

                chunk_id = support.chunk_id
                doc_id = support.doc_id

                if chunk_id and chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk_id)
                    # Try to load the chunk content
                    chunk_content = support.quote or ""
                    doc_title = ""

                    if doc_id:
                        try:
                            doc = await records.get_document(doc_id)
                            if doc:
                                doc_title = doc.title or doc_id
                        except Exception:
                            doc_title = doc_id or ""

                    support_context.append({
                        "chunk_id": chunk_id,
                        "doc_id": doc_id or "",
                        "content": chunk_content,
                        "doc_title": doc_title,
                        "source_class": "",  # available if doc has source_class
                        "claim_id": claim_id,
                    })
                elif doc_id and not chunk_id:
                    # doc-level support without a specific chunk
                    doc_key = f"doc:{doc_id}"
                    if doc_key not in seen_chunk_ids:
                        seen_chunk_ids.add(doc_key)
                        doc_title = ""
                        doc_source_class = ""
                        try:
                            doc = await records.get_document(doc_id)
                            if doc:
                                doc_title = doc.title or doc_id
                                doc_source_class = doc.source_class or ""
                        except Exception:
                            doc_title = doc_id

                        support_context.append({
                            "chunk_id": "",
                            "doc_id": doc_id,
                            "content": support.quote or "",
                            "doc_title": doc_title,
                            "source_class": doc_source_class,
                            "claim_id": claim_id,
                        })

        logger.info(
            f"ContextAssembler: gathered {len(support_context)} support chunks "
            f"(limit={max_chunks}) for {len(safe_claims)} claims"
        )

        # --- Step 4: Locked figures from canon (never from LLM or records) ---
        locked_figures: dict[str, str] = {}
        if include_figures:
            for fig in canon.get_locked_figures():
                locked_figures[fig.figure_id] = fig.display_value

        logger.info(
            f"ContextAssembler: {len(locked_figures)} locked figures injected "
            f"(include_figures={include_figures})"
        )

        # --- Step 5: Build task instructions from template -------------------
        template = TASK_INSTRUCTION_TEMPLATES.get(instructions_key, ARTICLE_DRAFT_INSTRUCTIONS)
        task_instructions = template.format(
            locked_figures=locked_figures,
            claim_count=len(safe_claims),
            chunk_count=len(support_context),
        )

        # --- Step 6: Assemble the packet -------------------------------------
        packet = ContextPacket(
            article_id=article_id,
            section_id=section_id,
            run_id=run_id,
            task_profile=task_profile,
            locked_figures=locked_figures,
            draftable_claims=serialized_claims,
            support_context=support_context,
            task_instructions=task_instructions,
            canon_hash=canon_hash,
        )

        logger.info(
            f"ContextAssembler: packet assembled — "
            f"claims={len(serialized_claims)} chunks={len(support_context)} "
            f"figures={len(locked_figures)}"
        )

        return packet
