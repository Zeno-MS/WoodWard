"""
src/services/article_drafter.py
Article drafter — assembles context, calls LLM with structured output contract,
validates all assertions have resolvable context_ids.

Hard rules:
- context_id validation is a hard-stop — no silent degradation
- Hallucinated context_ids raise HallucinatedContextError (not retried)
- DraftSectionResponse validation failures raise ValueError
- Injected figures come from ContextPacket.locked_figures (canon only)
"""
from __future__ import annotations

import json
import logging
from typing import Any

from schemas.llm_contracts import ContextPacket, DraftSectionResponse
from src.core.exceptions import HallucinatedContextError
from src.repositories.records_repo import RecordsRepo

logger = logging.getLogger(__name__)

# System prompt for article drafter — injected by code, never from LLM output
ARTICLE_DRAFTER_SYSTEM_PROMPT = """
You are a structured output generator for an investigative journalism system.

You must return ONLY a valid JSON object matching the DraftSectionResponse schema.
Do not include any prose outside the JSON object.

Schema requirements:
- section_id: string (copy from input)
- article_id: string (copy from input)
- content: string (Markdown prose)
- assertions: list of {text, context_ids, claim_ids, figure_ids, confidence}
  - Every factual sentence in content must have an entry here
  - context_ids must reference chunk_id or doc_id values from the support_context
  - claim_ids must reference claim_id values from draftable_claims
  - figure_ids must reference figure_id values from locked_figures
  - No assertion may have empty context_ids, claim_ids, AND figure_ids simultaneously
  - confidence MUST be one of the exact strings: "high", "medium", or "low" — NOT a number
- unresolved_questions: list of strings (open questions, not stated as facts)
- right_of_reply_flags: list of strings (claims needing right-of-reply)
- figures_used: list of figure_id strings referenced in content
- word_count: integer
"""


class ArticleDrafter:
    """
    Calls the LLM provider with a ContextPacket, parses the structured response,
    and validates all context_ids in assertions resolve to real records.
    """

    def __init__(self, settings: Any, provider_client: Any) -> None:
        """
        Args:
            settings: WoodwardSettings instance
            provider_client: OpenAIClient or compatible async client
                             with complete_structured() method
        """
        self.settings = settings
        self.client = provider_client

    async def draft_section(
        self,
        context: ContextPacket,
        records: RecordsRepo,
    ) -> DraftSectionResponse:
        """
        Call LLM with context packet, parse structured response,
        validate all context_ids resolve to real records.

        Raises HallucinatedContextError if any context_id in assertions
        does not match a chunk_id or doc_id in the context packet.

        Raises ValueError if DraftSectionResponse fails Pydantic validation.

        Does NOT retry on hallucination — hard-stop and report.
        """
        logger.info(
            f"ArticleDrafter.draft_section: article={context.article_id} "
            f"section={context.section_id} run_id={context.run_id}"
        )

        prompt = self._build_prompt(context)

        logger.debug(
            f"ArticleDrafter: calling LLM — "
            f"claims={len(context.draftable_claims)} "
            f"chunks={len(context.support_context)} "
            f"figures={len(context.locked_figures)}"
        )

        # Call provider — raises on API error or parse failure
        response: DraftSectionResponse = await self.client.complete_structured(
            prompt=prompt,
            system_prompt=ARTICLE_DRAFTER_SYSTEM_PROMPT,
            response_model=DraftSectionResponse,
            temperature=0.3,
        )

        logger.info(
            f"ArticleDrafter: received draft — "
            f"assertions={len(response.assertions)} "
            f"word_count={response.word_count}"
        )

        # Hard-stop validation: all context_ids must resolve
        self._validate_context_ids(response, context)

        logger.info(
            f"ArticleDrafter: context_id validation passed for section='{context.section_id}'"
        )

        return response

    def _validate_context_ids(
        self,
        response: DraftSectionResponse,
        context: ContextPacket,
    ) -> None:
        """
        Check every context_id in every assertion resolves to a real record.

        Valid IDs = chunk_ids and doc_ids in context.support_context.
        Also accepts claim_ids from context.draftable_claims and
        figure_ids from context.locked_figures.

        Raises HallucinatedContextError with list of bad IDs if any found.
        """
        # Build the set of valid IDs from the context packet
        valid_context_ids: set[str] = set()
        for chunk in context.support_context:
            if chunk.get("chunk_id"):
                valid_context_ids.add(chunk["chunk_id"])
            if chunk.get("doc_id"):
                valid_context_ids.add(chunk["doc_id"])

        valid_claim_ids: set[str] = set()
        for claim in context.draftable_claims:
            if isinstance(claim, dict):
                cid = claim.get("claim_id")
            else:
                cid = getattr(claim, "claim_id", None)
            if cid:
                valid_claim_ids.add(cid)

        valid_figure_ids: set[str] = set(context.locked_figures.keys())

        bad_ids: list[str] = []

        for assertion in response.assertions:
            for ctx_id in assertion.context_ids:
                if ctx_id and ctx_id not in valid_context_ids:
                    bad_ids.append(f"context_id:{ctx_id}")

            for claim_id in assertion.claim_ids:
                if claim_id and claim_id not in valid_claim_ids:
                    bad_ids.append(f"claim_id:{claim_id}")

            for fig_id in assertion.figure_ids:
                if fig_id and fig_id not in valid_figure_ids:
                    bad_ids.append(f"figure_id:{fig_id}")

        if bad_ids:
            # Deduplicate while preserving order
            seen: set[str] = set()
            deduped: list[str] = []
            for b in bad_ids:
                if b not in seen:
                    seen.add(b)
                    deduped.append(b)

            logger.error(
                f"ArticleDrafter: hallucinated context IDs in section='{response.section_id}': "
                f"{deduped}"
            )

            # Raise on first bad ID (include full list in message)
            first = deduped[0].split(":", 1)
            ref_type = first[0] if len(first) == 2 else "context_id"
            ref_id = first[1] if len(first) == 2 else deduped[0]

            raise HallucinatedContextError(
                ref_type=ref_type,
                ref_id=f"{ref_id} (all bad: {deduped})",
                section_id=response.section_id,
            )

    def _build_prompt(self, context: ContextPacket) -> str:
        """Build the full prompt string from the context packet."""
        parts: list[str] = []

        parts.append(f"=== DRAFT TASK ===")
        parts.append(f"article_id: {context.article_id}")
        parts.append(f"section_id: {context.section_id}")
        parts.append(f"run_id: {context.run_id}")
        parts.append("")

        # Inject task instructions from context packet (already formatted by ContextAssembler)
        if context.task_instructions:
            parts.append("=== TASK INSTRUCTIONS ===")
            parts.append(context.task_instructions)
            parts.append("")

        # Locked figures — these are ground truth, must not be altered
        parts.append("=== LOCKED FIGURES (use exactly as shown, do not alter) ===")
        if context.locked_figures:
            for fig_id, display_value in context.locked_figures.items():
                parts.append(f"  {fig_id}: {display_value}")
        else:
            parts.append("  (none)")
        parts.append("")

        # Draftable claims — verified, public-citable
        parts.append(f"=== DRAFTABLE CLAIMS ({len(context.draftable_claims)} total) ===")
        for i, claim in enumerate(context.draftable_claims):
            if isinstance(claim, dict):
                cid = claim.get("claim_id", "?")
                text = claim.get("text", "")
                ror = claim.get("right_of_reply_required", 0)
            else:
                cid = getattr(claim, "claim_id", "?")
                text = getattr(claim, "text", "")
                ror = getattr(claim, "right_of_reply_required", 0)

            ror_note = " [RIGHT-OF-REPLY REQUIRED — flag in right_of_reply_flags, do not assert as fact]" if ror else ""
            parts.append(f"  [{i+1}] claim_id={cid}{ror_note}")
            parts.append(f"      {text}")
        parts.append("")

        # Support context — source document excerpts
        parts.append(f"=== SUPPORT CONTEXT ({len(context.support_context)} excerpts) ===")
        for i, chunk in enumerate(context.support_context):
            chunk_id = chunk.get("chunk_id") or chunk.get("doc_id", "?")
            doc_title = chunk.get("doc_title", "")
            content = chunk.get("content", "")
            claim_id = chunk.get("claim_id", "")
            parts.append(
                f"  [{i+1}] chunk_id={chunk_id} doc='{doc_title}' supports claim={claim_id}"
            )
            if content:
                parts.append(f"      \"{content[:300]}\"")
        parts.append("")

        parts.append("=== OUTPUT ===")
        parts.append(
            "Return a DraftSectionResponse JSON object. "
            "Every factual assertion in content must have a corresponding entry in assertions[] "
            "with at least one valid context_id, claim_id, or figure_id from the lists above."
        )

        return "\n".join(parts)
