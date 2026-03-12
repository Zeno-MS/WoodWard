"""
src/bridge/ingest_manual_draft.py
ingest_manual_draft — ingests a manually written or webapp-exported draft
into records.db as pending_review claims.

CRITICAL RULE:
- All ingested claims are set to status='pending_review', public_citable=False
- NEVER sets status='verified' or canonical=True automatically
- webapp_export claims must be manually reviewed before they can be used

This is the one-way import gate from webapp-as-memory to canonical state.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from schemas.records_models import Claim
from src.core.logging import get_logger
from src.repositories.records_repo import RecordsRepo

logger = get_logger(__name__)

# Simple heuristics for extracting claim-like sentences from markdown text.
# These patterns identify:
# 1. Sentences containing dollar figures (likely factual claims)
# 2. Sentences with key verbs of assertion (paid, approved, voted, contracted, etc.)
# 3. Sentences with percentage figures
# 4. Bullet points starting with factual language

_DOLLAR_PATTERN = re.compile(r"\$[\d,]+(?:\.\d{2})?")
_PERCENT_PATTERN = re.compile(r"\d+(?:\.\d+)?%")
_ASSERTION_VERBS = re.compile(
    r"\b(paid|approved|voted|contracted|spent|budgeted|authorized|exceeded|"
    r"requested|received|borrowed|cut|eliminated|hired|employed|engaged|"
    r"renewed|signed|executed)\b",
    re.IGNORECASE,
)

# Minimum sentence length to consider as a claim
_MIN_CLAIM_LENGTH = 30


def _split_into_sentences(text: str) -> list[str]:
    """
    Split markdown text into candidate sentences.
    Handles:
    - Bullet points
    - Numbered lists
    - Regular paragraph sentences
    """
    sentences = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Strip markdown formatting from the line
        line = re.sub(r"^#+\s*", "", line)     # headers
        line = re.sub(r"^[-*+]\s*", "", line)   # bullet points
        line = re.sub(r"^\d+\.\s*", "", line)   # numbered lists
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)  # bold
        line = re.sub(r"\*(.+?)\*", r"\1", line)       # italic
        line = re.sub(r"`(.+?)`", r"\1", line)          # inline code

        if len(line) < _MIN_CLAIM_LENGTH:
            continue

        # Split on sentence boundaries (. ! ?) but be careful about abbreviations
        sub_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", line)
        sentences.extend(s.strip() for s in sub_sentences if s.strip())

    return sentences


def _is_factual_claim(sentence: str) -> bool:
    """
    Heuristically identify whether a sentence is a factual assertion.
    Returns True if the sentence contains financial figures, percentages,
    or strong assertion verbs.
    """
    if _DOLLAR_PATTERN.search(sentence):
        return True
    if _PERCENT_PATTERN.search(sentence):
        return True
    if _ASSERTION_VERBS.search(sentence):
        return True
    return False


async def ingest_manual_draft(
    markdown_text: str,
    article_id: str,
    records_db_path: Path,
    source: str = "webapp_export",
    dry_run: bool = False,
) -> list[str]:
    """
    Extract factual claims from a markdown text and insert them into records.db
    as pending_review claims.

    Args:
        markdown_text: The markdown text to process
        article_id: The article this draft belongs to
        records_db_path: Path to records.db
        source: Ingest source label (default: 'webapp_export')
        dry_run: If True, extract and return claim IDs without writing to DB

    Returns:
        List of claim_ids that were created (or would be created in dry_run mode)

    IMPORTANT:
        - All created claims have status='pending_review'
        - All created claims have public_citable=0
        - NEVER sets status='verified' or canonical=True
    """
    logger.info(
        f"ingest_manual_draft: article_id={article_id} source={source} "
        f"text_length={len(markdown_text)} dry_run={dry_run}"
    )

    sentences = _split_into_sentences(markdown_text)
    logger.debug(f"Extracted {len(sentences)} candidate sentences")

    claim_candidates = [s for s in sentences if _is_factual_claim(s)]
    logger.info(
        f"Identified {len(claim_candidates)} factual claim candidates "
        f"from {len(sentences)} sentences"
    )

    if not claim_candidates:
        logger.warning("No factual claims identified in the provided text")
        return []

    # Build Claim objects — ALL set to pending_review, NOT public_citable
    now = datetime.utcnow().isoformat()
    claims: list[Claim] = []

    for text in claim_candidates:
        claim_id = f"claim_{uuid.uuid4().hex[:12]}"
        claim = Claim(
            claim_id=claim_id,
            article_id=article_id,
            text=text,
            status="pending_review",
            public_citable=0,           # NEVER auto-set to True
            support_chain_complete=0,   # Requires manual review
            right_of_reply_required=0,
            stale=0,
            ingest_source=source,
            created_at=now,
            updated_at=now,
        )
        claims.append(claim)

    claim_ids = [c.claim_id for c in claims]

    if dry_run:
        logger.info(f"dry_run=True: would have created {len(claims)} claims")
        return claim_ids

    # Write to records.db
    repo = RecordsRepo(records_db_path)
    for claim in claims:
        await repo.upsert_claim(claim)

    logger.info(
        f"Ingested {len(claims)} claims into records.db "
        f"(all status=pending_review, public_citable=False)"
    )

    return claim_ids
