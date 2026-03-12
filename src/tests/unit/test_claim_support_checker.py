"""
tests/unit/test_claim_support_checker.py
Unit tests for ClaimSupportChecker.
Uses mock RecordsRepo to avoid database dependencies.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from schemas.canonical import SourcePolicy
from schemas.records_models import Claim, ClaimSupport
from src.services.claim_support_checker import ClaimSupportChecker, ClaimSupportResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_claim(
    claim_id: str = "test_claim",
    status: str = "verified",
    public_citable: int = 1,
    support_chain_complete: int = 1,
    right_of_reply_required: int = 0,
    stale: int = 0,
    article_id: str = "article_2",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        article_id=article_id,
        text=f"Test claim text for {claim_id}",
        status=status,
        public_citable=public_citable,
        support_chain_complete=support_chain_complete,
        right_of_reply_required=right_of_reply_required,
        stale=stale,
        ingest_source="canonical_seed",
    )


def _make_support(claim_id: str = "test_claim") -> ClaimSupport:
    return ClaimSupport(
        support_id=f"sup_{claim_id}",
        claim_id=claim_id,
        doc_id="doc_001",
        support_type="direct_quote",
        quote="A supporting quote from a public record.",
    )


def _make_policy() -> SourcePolicy:
    return SourcePolicy(source_classes=[])


def _make_records(
    claim: Claim | None,
    support_docs: list[ClaimSupport] | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.get_claim = AsyncMock(return_value=claim)
    mock.get_claim_support = AsyncMock(return_value=support_docs or [])
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verified_public_claim_is_draftable() -> None:
    """A fully verified, public-citable claim with a support row is draftable."""
    claim = _make_claim("claim_1", status="verified", public_citable=1, support_chain_complete=1)
    records = _make_records(claim, support_docs=[_make_support("claim_1")])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_1", records, policy)

    assert result.draftable is True
    assert result.reason == "ok"
    assert result.right_of_reply_warning is False


@pytest.mark.asyncio
async def test_blocked_claim_is_not_draftable() -> None:
    """A claim with status='blocked' must not be draftable regardless of other fields."""
    # Blocked claims cannot have public_citable=1 (model validator enforces this)
    claim = _make_claim("claim_blocked", status="blocked", public_citable=0, support_chain_complete=0)
    records = _make_records(claim, support_docs=[])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_blocked", records, policy)

    assert result.draftable is False
    assert result.reason == "blocked_status"


@pytest.mark.asyncio
async def test_pending_review_claim_is_not_draftable() -> None:
    """A claim with status='pending_review' must not be draftable."""
    claim = _make_claim("claim_pending", status="pending_review", public_citable=0, support_chain_complete=0)
    records = _make_records(claim, support_docs=[])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_pending", records, policy)

    assert result.draftable is False
    assert result.reason == "not_verified"


@pytest.mark.asyncio
async def test_claim_without_support_chain_is_not_draftable() -> None:
    """A verified claim with support_chain_complete=0 must not be draftable."""
    claim = _make_claim("claim_incomplete", status="verified", public_citable=1, support_chain_complete=0)
    records = _make_records(claim, support_docs=[])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_incomplete", records, policy)

    assert result.draftable is False
    assert result.reason == "no_support_chain"


@pytest.mark.asyncio
async def test_verified_claim_with_no_support_docs_is_not_draftable() -> None:
    """
    A claim that has support_chain_complete=1 but zero ClaimSupport rows in records.db
    must not be draftable (support_chain_complete flag alone is not sufficient).
    """
    claim = _make_claim("claim_nosupport", status="verified", public_citable=1, support_chain_complete=1)
    # No support documents returned
    records = _make_records(claim, support_docs=[])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_nosupport", records, policy)

    assert result.draftable is False
    assert result.reason == "no_public_support_docs"


@pytest.mark.asyncio
async def test_right_of_reply_claim_warns_but_does_not_block_draft() -> None:
    """
    A verified claim with right_of_reply_required=True should be draftable
    but must carry right_of_reply_warning=True in the result.
    """
    claim = _make_claim(
        "claim_ror",
        status="verified",
        public_citable=1,
        support_chain_complete=1,
        right_of_reply_required=1,
    )
    records = _make_records(claim, support_docs=[_make_support("claim_ror")])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_ror", records, policy)

    assert result.draftable is True
    assert result.reason == "ok"
    assert result.right_of_reply_warning is True


@pytest.mark.asyncio
async def test_nonexistent_claim_is_not_draftable() -> None:
    """A claim_id not found in records.db must return draftable=False."""
    records = _make_records(claim=None, support_docs=[])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("does_not_exist", records, policy)

    assert result.draftable is False
    assert result.reason == "not_verified"


@pytest.mark.asyncio
async def test_check_batch_returns_all_results() -> None:
    """check_batch returns one result per claim_id in the input list."""
    claim_1 = _make_claim("c1", status="verified", public_citable=1, support_chain_complete=1)
    claim_2 = _make_claim("c2", status="blocked", public_citable=0, support_chain_complete=0)

    mock = MagicMock()
    mock.get_claim = AsyncMock(side_effect=lambda cid: claim_1 if cid == "c1" else claim_2)
    mock.get_claim_support = AsyncMock(return_value=[_make_support("c1")])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    results = await checker.check_batch(["c1", "c2"], mock, policy)

    assert len(results) == 2
    assert results[0].claim_id == "c1"
    assert results[0].draftable is True
    assert results[1].claim_id == "c2"
    assert results[1].draftable is False


def test_filter_to_draftable_splits_correctly() -> None:
    """filter_to_draftable correctly partitions results into draftable and blocked."""
    r1 = ClaimSupportResult(claim_id="c1", draftable=True, reason="ok")
    r2 = ClaimSupportResult(claim_id="c2", draftable=False, reason="blocked_status")
    r3 = ClaimSupportResult(claim_id="c3", draftable=True, reason="ok", right_of_reply_warning=True)

    checker = ClaimSupportChecker()
    draftable, blocked = checker.filter_to_draftable([r1, r2, r3])

    assert len(draftable) == 2
    assert len(blocked) == 1
    assert draftable[0].claim_id == "c1"
    assert draftable[1].claim_id == "c3"
    assert blocked[0].claim_id == "c2"


@pytest.mark.asyncio
async def test_draft_claim_is_not_draftable() -> None:
    """A claim with status='draft' (not yet verified) must not be draftable."""
    claim = _make_claim("claim_draft", status="draft", public_citable=0, support_chain_complete=0)
    records = _make_records(claim, support_docs=[])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_draft", records, policy)

    assert result.draftable is False
    assert result.reason == "not_verified"


@pytest.mark.asyncio
async def test_not_public_citable_claim_is_not_draftable() -> None:
    """A verified claim with public_citable=0 must not be draftable."""
    claim = _make_claim("claim_private", status="verified", public_citable=0, support_chain_complete=1)
    records = _make_records(claim, support_docs=[_make_support("claim_private")])
    policy = _make_policy()

    checker = ClaimSupportChecker()
    result = await checker.check("claim_private", records, policy)

    assert result.draftable is False
    assert result.reason == "not_public_citable"
