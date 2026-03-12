"""
src/tests/unit/test_adversarial_review.py
Unit tests for AdversarialReviewer and review_draft workflow.
All LLM provider calls are mocked — no real API calls.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schemas.llm_contracts import (
    AdversarialFinding,
    AdversarialReviewResponse,
    ContextPacket,
    DraftSectionResponse,
    FactualAssertion,
)
from src.services.adversarial_review import AdversarialReviewer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_context_packet(locked_figures: dict | None = None) -> ContextPacket:
    return ContextPacket(
        article_id="article_2",
        section_id="sec_intro",
        run_id="run_test_001",
        task_profile="adversarial_review",
        locked_figures=locked_figures or {
            "amergis_fy2425_total": "$10,970,973",
            "fy2425_staffing_vendor_total": "$13,326,622",
        },
        draftable_claims=[
            {
                "claim_id": "claim_amergis_fy2425_payment",
                "text": "VPS paid $10,970,973 to Amergis in FY24-25",
                "status": "verified",
            }
        ],
        support_context=[
            {
                "chunk_id": "chunk_001",
                "doc_id": "doc_001",
                "content": "Payment records",
                "doc_title": "Warrant Register",
                "source_class": "public_record",
                "claim_id": "claim_amergis_fy2425_payment",
            }
        ],
        canon_hash="abc123",
    )


def make_draft(assertions: list[FactualAssertion] | None = None) -> DraftSectionResponse:
    return DraftSectionResponse(
        section_id="sec_intro",
        article_id="article_2",
        content="Vancouver Public Schools paid $10,970,973 to Amergis in FY2024-25.",
        assertions=assertions or [
            FactualAssertion(
                text="Vancouver Public Schools paid $10,970,973 to Amergis.",
                context_ids=["chunk_001"],
                claim_ids=["claim_amergis_fy2425_payment"],
                figure_ids=["amergis_fy2425_total"],
            )
        ],
        figures_used=["amergis_fy2425_total"],
        word_count=12,
    )


def make_clean_review_response(section_id: str = "sec_intro") -> AdversarialReviewResponse:
    return AdversarialReviewResponse(
        section_id=section_id,
        article_id="article_2",
        findings=[],
        blocker_count=0,
        warning_count=0,
        pass_build=True,
        reviewer_notes="No issues found.",
    )


def make_review_with_blocker() -> AdversarialReviewResponse:
    return AdversarialReviewResponse(
        section_id="sec_intro",
        article_id="article_2",
        findings=[
            AdversarialFinding(
                finding_id="f_blocker_001",
                severity="blocker",
                category="overclaim",
                description="Assertion stated as fact without support.",
                affected_text="VPS committed fraud.",
                affected_claim_id=None,
            )
        ],
        blocker_count=1,
        warning_count=0,
        pass_build=False,
        reviewer_notes="Blocker found.",
    )


def make_canon_with_banned_claims(banned_patterns: list[str]):
    """Create a minimal CanonManifest mock with banned claim patterns."""
    canon = MagicMock()
    ban_mocks = []
    for i, pattern in enumerate(banned_patterns):
        ban = MagicMock()
        ban.ban_id = f"ban_{i:03d}"
        ban.text_pattern = pattern
        ban.reason = f"Banned pattern: {pattern}"
        ban_mocks.append(ban)
    canon.banned_claims = ban_mocks

    # Locked figures
    fig = MagicMock()
    fig.figure_id = "amergis_fy2425_total"
    fig.display_value = "$10,970,973"
    fig.status = "locked"
    canon.get_locked_figures.return_value = [fig]
    canon.figures = [fig]

    return canon


# ---------------------------------------------------------------------------
# AdversarialReviewer — review() tests
# ---------------------------------------------------------------------------

class TestAdversarialReviewerReview:
    @pytest.mark.asyncio
    async def test_review_returns_structured_findings(self):
        """review() should return an AdversarialReviewResponse with findings."""
        provider = AsyncMock()
        clean_review = make_clean_review_response()
        provider.complete_structured = AsyncMock(return_value=clean_review)

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=provider)
        context = make_context_packet()
        draft = make_draft()

        result = await reviewer.review(draft=draft, context=context)

        assert isinstance(result, AdversarialReviewResponse)
        assert result.pass_build is True
        assert result.blocker_count == 0
        provider.complete_structured.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_review_pass_requires_zero_blockers(self):
        """If LLM returns blockers, pass_build must be False regardless of LLM claim."""
        # LLM incorrectly returns pass_build=True with a blocker
        # We need to construct this manually since Pydantic would reject it
        review_with_bad_pass = AdversarialReviewResponse(
            section_id="sec_intro",
            article_id="article_2",
            findings=[
                AdversarialFinding(
                    finding_id="b001",
                    severity="blocker",
                    category="overclaim",
                    description="Overclaim.",
                    affected_text="VPS committed fraud.",
                )
            ],
            blocker_count=1,
            warning_count=0,
            pass_build=False,  # Correct per Pydantic rule
            reviewer_notes="Has blocker.",
        )

        provider = AsyncMock()
        provider.complete_structured = AsyncMock(return_value=review_with_bad_pass)

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=provider)
        context = make_context_packet()
        draft = make_draft()

        result = await reviewer.review(draft=draft, context=context)

        # Must stay False — never True when blockers exist
        assert result.pass_build is False

    @pytest.mark.asyncio
    async def test_review_overrides_pass_build_if_blockers_present(self):
        """
        If LLM response somehow has pass_build=True with blockers (validator override via model_copy),
        AdversarialReviewer.review() must correct it to False.
        """
        # Build a response with blocker but pass_build=True by bypassing validation
        # Use model_construct to skip validators
        bad_pass_response = AdversarialReviewResponse.model_construct(
            section_id="sec_intro",
            article_id="article_2",
            findings=[
                AdversarialFinding(
                    finding_id="b001",
                    severity="blocker",
                    category="overclaim",
                    description="Overclaim.",
                    affected_text="VPS committed fraud.",
                )
            ],
            blocker_count=1,
            warning_count=0,
            pass_build=True,   # WRONG — reviewer must correct this
            reviewer_notes="Incorrect pass_build from LLM.",
            reviewed_at="2026-03-12T00:00:00",
            reviewer_model=None,
        )

        provider = AsyncMock()
        provider.complete_structured = AsyncMock(return_value=bad_pass_response)

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=provider)
        context = make_context_packet()
        draft = make_draft()

        result = await reviewer.review(draft=draft, context=context)

        # Override must have happened
        assert result.pass_build is False
        assert result.blocker_count == 1

    @pytest.mark.asyncio
    async def test_review_corrects_blocker_count_mismatch(self):
        """If LLM returns wrong blocker_count, it must be corrected from actual findings."""
        wrong_counts_response = AdversarialReviewResponse.model_construct(
            section_id="sec_intro",
            article_id="article_2",
            findings=[
                AdversarialFinding(
                    finding_id="b001",
                    severity="blocker",
                    category="overclaim",
                    description="Overclaim.",
                    affected_text="VPS committed fraud.",
                ),
                AdversarialFinding(
                    finding_id="b002",
                    severity="blocker",
                    category="unsupported_math",
                    description="Figure not locked.",
                    affected_text="$999M spent.",
                ),
            ],
            blocker_count=1,    # Wrong — should be 2
            warning_count=0,
            pass_build=False,
            reviewer_notes="Counts wrong.",
            reviewed_at="2026-03-12T00:00:00",
            reviewer_model=None,
        )

        provider = AsyncMock()
        provider.complete_structured = AsyncMock(return_value=wrong_counts_response)

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=provider)
        context = make_context_packet()
        draft = make_draft()

        result = await reviewer.review(draft=draft, context=context)

        assert result.blocker_count == 2


# ---------------------------------------------------------------------------
# AdversarialReviewer — local check tests
# ---------------------------------------------------------------------------

class TestAdversarialReviewerLocalCheck:
    def test_review_local_check_catches_unlocked_figure(self):
        """figure_id in assertion not locked in canon must be flagged."""
        canon = make_canon_with_banned_claims([])

        # Override locked figures to empty (no locked figures)
        canon.get_locked_figures.return_value = []

        # Figure exists in canon.figures but is not locked
        unlocked_fig = MagicMock()
        unlocked_fig.figure_id = "provisional_figure"
        unlocked_fig.status = "provisional"
        unlocked_fig.display_value = "$1,000,000"
        canon.figures = [unlocked_fig]

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=MagicMock())

        draft_with_unlocked_fig = make_draft(assertions=[
            FactualAssertion(
                text="VPS spent $1,000,000.",
                context_ids=["chunk_001"],
                figure_ids=["provisional_figure"],
            )
        ])

        findings = reviewer.check_for_blocked_figures(draft_with_unlocked_fig, canon)

        assert len(findings) > 0
        assert any(f.severity == "blocker" for f in findings)
        assert any("provisional_figure" in f.description for f in findings)

    def test_review_local_check_catches_banned_text_pattern(self):
        """Banned claim text in draft content must be flagged as a blocker."""
        canon = make_canon_with_banned_claims(["committed fraud"])

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=MagicMock())

        draft_with_banned = DraftSectionResponse(
            section_id="sec_intro",
            article_id="article_2",
            content="VPS officials committed fraud with vendor contracts.",
            assertions=[
                FactualAssertion(
                    text="VPS officials committed fraud.",
                    context_ids=["chunk_001"],
                )
            ],
        )

        findings = reviewer.check_for_blocked_figures(draft_with_banned, canon)

        assert len(findings) > 0
        assert any(f.severity == "blocker" for f in findings)
        assert any(f.category == "overclaim" for f in findings)

    def test_review_local_check_clean_draft_returns_empty(self):
        """Clean draft should return empty findings list."""
        canon = make_canon_with_banned_claims(["some_other_pattern"])

        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=MagicMock())

        clean_draft = make_draft()

        findings = reviewer.check_for_blocked_figures(clean_draft, canon)

        assert findings == []

    def test_review_local_check_hallucinated_figure_id_raises_blocker(self):
        """Figure ID in assertion that doesn't exist in canon at all must be flagged."""
        canon = make_canon_with_banned_claims([])
        # canon.figures only has amergis_fy2425_total
        reviewer = AdversarialReviewer(settings=MagicMock(), provider_client=MagicMock())

        draft_hallucinated = make_draft(assertions=[
            FactualAssertion(
                text="VPS spent the figure.",
                context_ids=["chunk_001"],
                figure_ids=["figure_DOES_NOT_EXIST_IN_CANON"],
            )
        ])

        findings = reviewer.check_for_blocked_figures(draft_hallucinated, canon)

        assert len(findings) > 0
        assert any(f.category == "hallucinated_context" for f in findings)
        assert any(f.severity == "blocker" for f in findings)


# ---------------------------------------------------------------------------
# review_draft workflow tests
# ---------------------------------------------------------------------------

class TestReviewDraftWorkflow:
    @pytest.mark.asyncio
    async def test_review_draft_workflow_writes_artifact(self):
        """review_draft should write a JSON artifact to runs/{run_id}/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock settings to use temp dir
            settings = MagicMock()
            settings.runs_path_obj = Path(tmpdir)

            canon = make_canon_with_banned_claims([])

            clean_review = make_clean_review_response()
            provider = AsyncMock()
            provider.complete_structured = AsyncMock(return_value=clean_review)

            from src.workflows.review_draft import review_draft

            draft = make_draft()
            context = make_context_packet()

            result = await review_draft(
                draft=draft,
                context=context,
                run_id="run_artifact_test",
                settings=settings,
                canon=canon,
                provider_client=provider,
            )

            assert result.can_advance is True
            assert result.artifact_path is not None

            # Verify the artifact file was written
            artifact = Path(result.artifact_path)
            assert artifact.exists()

            data = json.loads(artifact.read_text())
            assert data["section_id"] == "sec_intro"
            assert data["can_advance"] is True

    @pytest.mark.asyncio
    async def test_review_draft_can_advance_false_when_blockers(self):
        """can_advance must be False when any blocker exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = MagicMock()
            settings.runs_path_obj = Path(tmpdir)

            canon = make_canon_with_banned_claims([])

            review_with_blockers = make_review_with_blocker()
            provider = AsyncMock()
            provider.complete_structured = AsyncMock(return_value=review_with_blockers)

            from src.workflows.review_draft import review_draft

            draft = make_draft()
            context = make_context_packet()

            result = await review_draft(
                draft=draft,
                context=context,
                run_id="run_blocker_test",
                settings=settings,
                canon=canon,
                provider_client=provider,
            )

            assert result.can_advance is False
            assert len(result.blocker_ids) > 0

    @pytest.mark.asyncio
    async def test_review_draft_combines_local_and_llm_findings(self):
        """Local findings (banned patterns) plus LLM findings should both appear."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = MagicMock()
            settings.runs_path_obj = Path(tmpdir)

            # Ban pattern that appears in draft content
            canon = make_canon_with_banned_calls = make_canon_with_banned_claims(
                ["committed fraud"]
            )

            # LLM also returns a warning
            review_with_warning = AdversarialReviewResponse(
                section_id="sec_intro",
                article_id="article_2",
                findings=[
                    AdversarialFinding(
                        finding_id="llm_w001",
                        severity="warning",
                        category="weak_attribution",
                        description="Weak attribution.",
                        affected_text="The district.",
                    )
                ],
                blocker_count=0,
                warning_count=1,
                pass_build=True,
                reviewer_notes="One warning.",
            )
            provider = AsyncMock()
            provider.complete_structured = AsyncMock(return_value=review_with_warning)

            from src.workflows.review_draft import review_draft

            # Draft that contains banned pattern
            draft_with_banned = DraftSectionResponse(
                section_id="sec_intro",
                article_id="article_2",
                content="VPS officials committed fraud with vendor contracts.",
                assertions=[
                    FactualAssertion(
                        text="VPS officials committed fraud.",
                        context_ids=["chunk_001"],
                    )
                ],
            )
            context = make_context_packet()

            result = await review_draft(
                draft=draft_with_banned,
                context=context,
                run_id="run_combined_test",
                settings=settings,
                canon=make_canon_with_banned_calls,
                provider_client=provider,
            )

            # Local blocker + LLM warning = can_advance False
            total_findings = result.review.findings
            severities = {f.severity for f in total_findings}
            assert "blocker" in severities  # from local check
            assert "warning" in severities  # from LLM
            assert result.can_advance is False
