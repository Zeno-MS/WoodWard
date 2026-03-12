"""
src/tests/unit/test_reply_planner.py
Unit tests for ReplyPlanner.
Uses mock repos.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from schemas.comms_models import ArticleDependency, Recipient, ResponseWindow, Thread
from schemas.records_models import Claim
from src.services.reply_planner import ReplyPlanner, ReplyRequirement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_claim(
    claim_id: str,
    article_id: str,
    right_of_reply_required: int = 1,
    status: str = "blocked",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        article_id=article_id,
        text=f"Claim text for {claim_id}",
        status=status,
        public_citable=0 if status == "blocked" else 1,
        support_chain_complete=0 if status == "blocked" else 1,
        right_of_reply_required=right_of_reply_required,
        stale=0,
        ingest_source="canonical_seed",
    )


def _make_thread(
    thread_id: str,
    recipient_id: str,
    status: str = "awaiting_response",
) -> Thread:
    return Thread(
        thread_id=thread_id,
        recipient_id=recipient_id,
        subject=f"Thread: {thread_id}",
        status=status,
    )


def _make_dep(
    dep_id: str,
    article_id: str,
    thread_id: str,
    claim_id: str,
    resolved: int = 0,
) -> ArticleDependency:
    return ArticleDependency(
        dep_id=dep_id,
        article_id=article_id,
        thread_id=thread_id,
        claim_id=claim_id,
        dependency_type="right_of_reply",
        resolved=resolved,
    )


def _make_response_window(
    window_id: str,
    thread_id: str,
    deadline: str = "2026-03-20",
    status: str = "open",
    publication_blocking: int = 1,
) -> ResponseWindow:
    return ResponseWindow(
        window_id=window_id,
        thread_id=thread_id,
        deadline=deadline,
        status=status,
        publication_blocking=publication_blocking,
    )


def _make_recipient(recipient_id: str, name: str, org_id: str = "org1") -> Recipient:
    return Recipient(
        recipient_id=recipient_id,
        org_id=org_id,
        name=name,
        role="Director",
    )


def _make_records(claims: list[Claim]) -> MagicMock:
    records = MagicMock()
    records.get_claims_for_article = AsyncMock(return_value=claims)
    records.get_claim = AsyncMock(
        side_effect=lambda cid: next((c for c in claims if c.claim_id == cid), None)
    )
    return records


def _make_comms(
    deps: list[ArticleDependency],
    threads: list[Thread],
    blocking_windows: list[ResponseWindow],
    recipients: dict[str, Recipient] | None = None,
) -> MagicMock:
    comms = MagicMock()
    comms.get_article_dependencies = AsyncMock(return_value=deps)
    comms.get_threads_for_article = AsyncMock(return_value=threads)
    comms.get_publication_blocking_windows = AsyncMock(return_value=blocking_windows)
    if recipients:
        comms.get_recipient = AsyncMock(
            side_effect=lambda rid: recipients.get(rid)
        )
    else:
        comms.get_recipient = AsyncMock(return_value=None)
    return comms


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reply_requirements_loaded_for_article():
    """RoR claims for an article are returned as ReplyRequirement objects."""
    claims = [
        _make_claim("claim_1", "article_1", right_of_reply_required=1),
        _make_claim("claim_2", "article_1", right_of_reply_required=0, status="verified"),
    ]
    deps = [
        _make_dep("dep_1", "article_1", "thread_sao", "claim_1"),
    ]
    threads = [_make_thread("thread_sao", "kathleen_cooper")]
    windows = [_make_response_window("rw_1", "thread_sao")]
    recipients = {"kathleen_cooper": _make_recipient("kathleen_cooper", "Kathleen Cooper")}

    records = _make_records(claims)
    comms = _make_comms(deps, threads, windows, recipients)

    planner = ReplyPlanner()
    reqs = await planner.get_requirements("article_1", records, comms)

    # Only claim_1 has right_of_reply_required=1
    assert len(reqs) == 1
    req = reqs[0]
    assert req.claim_id == "claim_1"
    assert req.article_id == "article_1"
    assert req.thread_id == "thread_sao"
    assert req.recipient_name == "Kathleen Cooper"
    assert req.publication_blocking is True
    assert req.deadline == "2026-03-20"


@pytest.mark.asyncio
async def test_blocking_requirements_subset_of_all():
    """get_blocking_requirements returns only publication-blocking ones."""
    claims = [
        _make_claim("claim_blocking", "article_1", right_of_reply_required=1),
        _make_claim("claim_non_blocking", "article_1", right_of_reply_required=1),
    ]
    deps = [
        _make_dep("dep_1", "article_1", "thread_blocking", "claim_blocking"),
        _make_dep("dep_2", "article_1", "thread_non", "claim_non_blocking"),
    ]
    threads = [
        _make_thread("thread_blocking", "kathleen_cooper"),
        _make_thread("thread_non", "brett_b"),
    ]
    # Only thread_blocking has a publication-blocking window
    windows = [_make_response_window("rw_1", "thread_blocking", publication_blocking=1)]

    records = _make_records(claims)
    comms = _make_comms(deps, threads, windows)

    planner = ReplyPlanner()
    all_reqs = await planner.get_requirements("article_1", records, comms)
    blocking_reqs = await planner.get_blocking_requirements("article_1", records, comms)

    assert len(all_reqs) == 2
    assert len(blocking_reqs) == 1
    assert blocking_reqs[0].claim_id == "claim_blocking"
    assert blocking_reqs[0].publication_blocking is True


@pytest.mark.asyncio
async def test_no_requirements_for_article_with_no_ror_claims():
    """Returns empty list when no claims have right_of_reply_required=1."""
    claims = [
        _make_claim("claim_verified", "article_2", right_of_reply_required=0, status="verified"),
    ]
    records = _make_records(claims)
    comms = _make_comms([], [], [])

    planner = ReplyPlanner()
    reqs = await planner.get_requirements("article_2", records, comms)

    assert reqs == []


@pytest.mark.asyncio
async def test_pending_status_when_no_thread():
    """Status is 'pending' when there is a RoR claim but no thread."""
    claims = [_make_claim("claim_orphan", "article_3", right_of_reply_required=1)]
    records = _make_records(claims)
    comms = _make_comms(deps=[], threads=[], blocking_windows=[])

    planner = ReplyPlanner()
    reqs = await planner.get_requirements("article_3", records, comms)

    assert len(reqs) == 1
    assert reqs[0].status == "pending"
    assert reqs[0].thread_id is None
    assert reqs[0].publication_blocking is False


@pytest.mark.asyncio
async def test_format_summary_shows_blocking():
    """format_summary includes PUBLICATION-BLOCKING section when applicable."""
    planner = ReplyPlanner()
    reqs = [
        ReplyRequirement(
            claim_id="claim_1",
            claim_text="VPS has no spending cap in Amergis contract.",
            article_id="article_1",
            thread_id="thread_sao",
            recipient_id="kathleen_cooper",
            recipient_name="Kathleen Cooper",
            status="sent",
            publication_blocking=True,
            deadline="2026-03-20",
        ),
        ReplyRequirement(
            claim_id="claim_2",
            claim_text="VPS never conducted competitive bidding.",
            article_id="article_1",
            thread_id=None,
            recipient_id=None,
            recipient_name=None,
            status="pending",
            publication_blocking=False,
            deadline=None,
        ),
    ]
    summary = planner.format_summary(reqs)

    assert "PUBLICATION-BLOCKING" in summary
    assert "claim_1" in summary
    assert "Kathleen Cooper" in summary
    assert "2026-03-20" in summary
    assert "NON-BLOCKING" in summary
    assert "claim_2" in summary
