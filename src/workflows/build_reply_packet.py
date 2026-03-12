"""
src/workflows/build_reply_packet.py
build_reply_packet workflow — assembles a right-of-reply outreach packet.

Output is a Markdown document suitable for email/letter.

No-LLM path: build packet from claim texts using a fixed template.
LLM path: use provider_client to draft a professional journalism letter
          (ReplyPacketResponse contract from llm_contracts.py).

Writes: runs/{run_id}/reply_packet_{recipient_id}.md
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from schemas.canonical import CanonManifest
from src.core.settings import WoodwardSettings
from src.repositories.comms_repo import CommsRepo
from src.repositories.records_repo import RecordsRepo
from src.services.reply_planner import ReplyPlanner

logger = logging.getLogger(__name__)

# Default response deadline if none is set in a response window
_DEFAULT_DEADLINE = "10 business days from receipt of this message"


@dataclass
class ReplyPacketResult:
    """
    Result from the build_reply_packet workflow.

    packet_markdown is the actual letter/email text — clean Markdown,
    professional journalism tone, NOT a legal demand letter.
    """
    run_id: str
    article_id: str
    recipient_id: str
    recipient_name: str
    questions: list[str] = field(default_factory=list)
    affected_claim_ids: list[str] = field(default_factory=list)
    packet_markdown: str = ""
    publication_blocking: bool = False
    deadline_recommendation: str = _DEFAULT_DEADLINE
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    canon_hash: str = ""


# ---------------------------------------------------------------------------
# Template builder (no-LLM path)
# ---------------------------------------------------------------------------

def _build_packet_from_template(
    recipient_name: str,
    org_name: str,
    claims: list,
    deadline: str,
) -> tuple[str, list[str]]:
    """
    Build a right-of-reply packet from a fixed journalistic template.
    Returns (packet_markdown, questions_list).

    Letter rules:
    - Professional journalism tone
    - States what will be published (factual, no motive language)
    - Asks specific questions per claim
    - Sets a clear deadline
    - NOT a legal demand letter
    """
    questions: list[str] = []
    claim_lines: list[str] = []
    question_lines: list[str] = []

    for i, claim in enumerate(claims, start=1):
        claim_lines.append(f"{i}. {claim.text}")
        # Derive a specific question from the claim text
        q = _claim_to_question(claim.text)
        questions.append(q)
        question_lines.append(f"{i}. {q}")

    claims_block = "\n".join(claim_lines) if claim_lines else "  (No specific claims listed)"
    questions_block = "\n".join(question_lines) if question_lines else "  (No questions generated)"

    packet = f"""Dear {recipient_name},

I am preparing an article about Vancouver Public Schools' staffing vendor spending for fiscal year 2024–25.

The article will report the following verified facts:

{claims_block}

Before publication, I am offering {org_name} the opportunity to respond to the following questions:

{questions_block}

Please respond by {deadline}.

---

[Journalist signature — to be completed before sending]
"""
    return packet.strip(), questions


def _claim_to_question(claim_text: str) -> str:
    """Convert a claim text into a specific question for the right-of-reply packet."""
    text = claim_text.strip().rstrip(".")
    # Simple conversion: "X does Y" -> "Can you confirm or address the following: X does Y?"
    return f"Can you confirm, clarify, or provide context for the following: {text}?"


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

async def build_reply_packet(
    article_id: str,
    recipient_id: str,
    run_id: str,
    settings: WoodwardSettings,
    records: RecordsRepo,
    comms: CommsRepo,
    canon: CanonManifest,
    provider_client: Any = None,
) -> ReplyPacketResult:
    """
    Build a right-of-reply outreach packet for a specific recipient.

    Steps:
    1. Load right-of-reply requirements for article + recipient.
    2. Load affected claims.
    3. If provider_client is None: build packet from claim texts only (no LLM).
    4. If provider_client: use LLM to draft professional letter (ReplyPacketResponse).
    5. Write runs/{run_id}/reply_packet_{recipient_id}.md.
    6. Return ReplyPacketResult.
    """
    logger.info(
        f"build_reply_packet: article={article_id} recipient={recipient_id} "
        f"run_id={run_id} llm={'yes' if provider_client else 'no-llm'}"
    )

    planner = ReplyPlanner()

    # Step 1: Load requirements for this article (all, then filter to recipient)
    all_reqs = await planner.get_requirements(article_id, records, comms)
    recipient_reqs = [r for r in all_reqs if r.recipient_id == recipient_id]

    # Step 2: Load affected claims
    affected_claim_ids = [r.claim_id for r in recipient_reqs]
    affected_claims = []
    for cid in affected_claim_ids:
        claim = await records.get_claim(cid)
        if claim is not None:
            affected_claims.append(claim)

    # If no requirements tied to this specific recipient, fall back to all RoR claims
    if not affected_claims:
        logger.warning(
            f"build_reply_packet: no requirements found for recipient '{recipient_id}' "
            f"in article '{article_id}' — falling back to all RoR claims"
        )
        all_claims = await records.get_claims_for_article(article_id)
        affected_claims = [c for c in all_claims if c.right_of_reply_required == 1]
        affected_claim_ids = [c.claim_id for c in affected_claims]

    # Resolve recipient details
    recipient = await comms.get_recipient(recipient_id)
    recipient_name = recipient.name if recipient else recipient_id
    org_name = "your organization"
    if recipient and recipient.org_id:
        org = await comms.get_organization(recipient.org_id)
        if org:
            org_name = org.name

    # Determine publication-blocking status and deadline
    publication_blocking = any(r.publication_blocking for r in recipient_reqs)
    deadline = _DEFAULT_DEADLINE
    for r in recipient_reqs:
        if r.deadline:
            deadline = r.deadline
            break

    deadline_recommendation = (
        f"by {deadline}" if not deadline.startswith("by ") and not deadline.startswith("10 ")
        else deadline
    )

    # Step 3/4: Build the packet
    if provider_client is None:
        # No-LLM path: use fixed template
        packet_markdown, questions = _build_packet_from_template(
            recipient_name=recipient_name or recipient_id,
            org_name=org_name,
            claims=affected_claims,
            deadline=deadline_recommendation,
        )
        logger.info(
            f"build_reply_packet: no-LLM path — "
            f"built packet with {len(questions)} questions from {len(affected_claims)} claims"
        )
    else:
        # LLM path: use ReplyPacketResponse contract
        from schemas.llm_contracts import ReplyPacketResponse
        from src.services.context_assembler import ContextAssembler

        # Build a simple context for the LLM
        thread_id = recipient_reqs[0].thread_id if recipient_reqs else f"{article_id}_{recipient_id}"

        prompt = (
            f"You are a professional investigative journalist preparing a right-of-reply letter.\n\n"
            f"Article: {article_id}\n"
            f"Recipient: {recipient_name} at {org_name}\n\n"
            f"The article will report these verified facts:\n"
            + "\n".join(f"- {c.text}" for c in affected_claims)
            + "\n\nDraft a professional right-of-reply letter. "
            "Rules: factual tone, no motive language, specific questions only, "
            "set a clear response deadline. NOT a legal demand letter.\n\n"
            f"Deadline: {deadline_recommendation}"
        )

        try:
            response: ReplyPacketResponse = await provider_client.complete_structured(
                prompt=prompt,
                output_schema=ReplyPacketResponse,
                system_prompt=(
                    "You are a professional investigative journalist. "
                    "Your output must be factual, non-accusatory, and ask specific verifiable questions."
                ),
            )
            packet_markdown = response.packet_markdown
            questions = response.questions
            publication_blocking = publication_blocking or response.publication_blocking
            logger.info(
                f"build_reply_packet: LLM path — "
                f"built packet with {len(questions)} questions"
            )
        except Exception as e:
            logger.error(
                f"build_reply_packet: LLM call failed, falling back to template: {e}"
            )
            packet_markdown, questions = _build_packet_from_template(
                recipient_name=recipient_name or recipient_id,
                org_name=org_name,
                claims=affected_claims,
                deadline=deadline_recommendation,
            )

    # Step 5: Write artifact
    runs_path = settings.runs_path_obj / run_id
    try:
        runs_path.mkdir(parents=True, exist_ok=True)
        artifact_file = runs_path / f"reply_packet_{recipient_id}.md"
        artifact_file.write_text(packet_markdown, encoding="utf-8")
        logger.info(f"build_reply_packet: packet written to {artifact_file}")
    except Exception as e:
        logger.error(f"build_reply_packet: failed to write artifact: {e}")

    # Step 6: Return result
    result = ReplyPacketResult(
        run_id=run_id,
        article_id=article_id,
        recipient_id=recipient_id,
        recipient_name=recipient_name or recipient_id,
        questions=questions,
        affected_claim_ids=affected_claim_ids,
        packet_markdown=packet_markdown,
        publication_blocking=publication_blocking,
        deadline_recommendation=deadline_recommendation,
        canon_hash="",  # No canon hash from CanonManifest directly
    )

    logger.info(
        f"build_reply_packet: done — "
        f"article={article_id} recipient={recipient_id} "
        f"questions={len(questions)} blocking={publication_blocking}"
    )
    return result
