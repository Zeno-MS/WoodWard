"""
src/tests/unit/test_llm_contracts.py
Unit tests for schemas/llm_contracts.py Pydantic models.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.llm_contracts import (
    AdversarialFinding,
    AdversarialReviewResponse,
    ContextPacket,
    DraftSectionResponse,
    FactualAssertion,
    ReplyPacketResponse,
)


# ---------------------------------------------------------------------------
# FactualAssertion tests
# ---------------------------------------------------------------------------

class TestFactualAssertion:
    def test_assertion_with_context_ids_is_valid(self):
        a = FactualAssertion(
            text="VPS paid $10,970,973 to Amergis.",
            context_ids=["chunk_001"],
            claim_ids=[],
            figure_ids=[],
        )
        assert a.has_support() is True

    def test_assertion_with_claim_ids_is_valid(self):
        a = FactualAssertion(
            text="The board approved Amergis at $3M.",
            context_ids=[],
            claim_ids=["claim_board_3m_estimate"],
            figure_ids=[],
        )
        assert a.has_support() is True

    def test_assertion_with_figure_ids_is_valid(self):
        a = FactualAssertion(
            text="Amergis total was $10,970,973.",
            context_ids=[],
            claim_ids=[],
            figure_ids=["amergis_fy2425_total"],
        )
        assert a.has_support() is True

    def test_assertion_with_no_support_has_support_false(self):
        a = FactualAssertion(
            text="Something happened.",
            context_ids=[],
            claim_ids=[],
            figure_ids=[],
        )
        assert a.has_support() is False

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError):
            FactualAssertion(text="   ", context_ids=["ctx_1"])

    def test_confidence_default_is_high(self):
        a = FactualAssertion(
            text="VPS paid vendors.",
            context_ids=["ctx_1"],
        )
        assert a.confidence == "high"

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValidationError):
            FactualAssertion(
                text="VPS paid vendors.",
                context_ids=["ctx_1"],
                confidence="extreme",  # type: ignore
            )


# ---------------------------------------------------------------------------
# DraftSectionResponse tests
# ---------------------------------------------------------------------------

class TestDraftSectionResponse:
    def test_valid_response_constructs(self):
        resp = DraftSectionResponse(
            section_id="sec_1",
            article_id="article_2",
            content="VPS paid $10,970,973 to Amergis in FY2024-25.",
            assertions=[
                FactualAssertion(
                    text="VPS paid $10,970,973 to Amergis in FY2024-25.",
                    context_ids=["chunk_001"],
                    figure_ids=["amergis_fy2425_total"],
                )
            ],
            word_count=10,
        )
        assert resp.passes_support_check() is True

    def test_draft_section_response_requires_context_ids_per_assertion(self):
        """Assertion with no context_ids, claim_ids, or figure_ids must fail validation."""
        with pytest.raises(ValidationError):
            DraftSectionResponse(
                section_id="sec_1",
                article_id="article_2",
                content="Something happened.",
                assertions=[
                    FactualAssertion(
                        text="Something happened.",
                        context_ids=[],
                        claim_ids=[],
                        figure_ids=[],
                    )
                ],
                word_count=2,
            )

    def test_passes_support_check_true_when_all_supported(self):
        resp = DraftSectionResponse(
            section_id="sec_1",
            article_id="article_2",
            content="VPS paid vendors.",
            assertions=[
                FactualAssertion(
                    text="VPS paid vendors.",
                    context_ids=["chunk_abc"],
                )
            ],
        )
        assert resp.passes_support_check() is True

    def test_empty_assertions_passes(self):
        resp = DraftSectionResponse(
            section_id="sec_1",
            article_id="article_2",
            content="Background section with no specific claims.",
            assertions=[],
        )
        assert resp.passes_support_check() is True

    def test_unresolved_questions_and_ror_flags_default_empty(self):
        resp = DraftSectionResponse(
            section_id="sec_1",
            article_id="article_2",
            content="Some content.",
            assertions=[
                FactualAssertion(text="Some fact.", context_ids=["ctx_1"])
            ],
        )
        assert resp.unresolved_questions == []
        assert resp.right_of_reply_flags == []


# ---------------------------------------------------------------------------
# AdversarialFinding tests
# ---------------------------------------------------------------------------

class TestAdversarialFinding:
    def test_valid_finding_constructs(self):
        f = AdversarialFinding(
            finding_id="f001",
            severity="blocker",
            category="overclaim",
            description="Assertion stated as fact without support.",
            affected_text="VPS committed fraud.",
        )
        assert f.is_blocker is True

    def test_adversarial_finding_severity_is_validated(self):
        """Invalid severity must raise."""
        with pytest.raises(ValidationError):
            AdversarialFinding(
                finding_id="f002",
                severity="critical",  # type: ignore — not a valid literal
                category="overclaim",
                description="Test.",
                affected_text="Test text.",
            )

    def test_adversarial_finding_category_is_validated(self):
        """Invalid category must raise."""
        with pytest.raises(ValidationError):
            AdversarialFinding(
                finding_id="f003",
                severity="warning",
                category="bad_category",  # type: ignore
                description="Test.",
                affected_text="Test text.",
            )

    def test_warning_is_not_blocker(self):
        f = AdversarialFinding(
            finding_id="f004",
            severity="warning",
            category="weak_attribution",
            description="Source not specified.",
            affected_text="The district said.",
        )
        assert f.is_blocker is False

    def test_note_is_not_blocker(self):
        f = AdversarialFinding(
            finding_id="f005",
            severity="note",
            category="scope_drift",
            description="Consider clarifying vendor scope.",
            affected_text="Vendor spending.",
        )
        assert f.is_blocker is False

    def test_optional_fields_default_none(self):
        f = AdversarialFinding(
            finding_id="f006",
            severity="warning",
            category="motive_language",
            description="Test.",
            affected_text="Test.",
        )
        assert f.affected_claim_id is None
        assert f.suggestion is None


# ---------------------------------------------------------------------------
# AdversarialReviewResponse tests
# ---------------------------------------------------------------------------

class TestAdversarialReviewResponse:
    def test_pass_build_false_when_blockers_present(self):
        """pass_build cannot be True when blocker_count > 0."""
        with pytest.raises(ValidationError):
            AdversarialReviewResponse(
                section_id="sec_1",
                findings=[
                    AdversarialFinding(
                        finding_id="f001",
                        severity="blocker",
                        category="overclaim",
                        description="Blocker present.",
                        affected_text="Problematic text.",
                    )
                ],
                blocker_count=1,
                warning_count=0,
                pass_build=True,  # Must fail — blocker_count=1
            )

    def test_pass_build_true_when_no_blockers(self):
        r = AdversarialReviewResponse(
            section_id="sec_1",
            findings=[],
            blocker_count=0,
            warning_count=0,
            pass_build=True,
        )
        assert r.pass_build is True

    def test_pass_build_false_with_zero_blockers_allowed(self):
        r = AdversarialReviewResponse(
            section_id="sec_1",
            findings=[],
            blocker_count=0,
            warning_count=0,
            pass_build=False,
        )
        assert r.pass_build is False

    def test_get_blockers_returns_only_blockers(self):
        r = AdversarialReviewResponse(
            section_id="sec_1",
            findings=[
                AdversarialFinding(
                    finding_id="b1",
                    severity="blocker",
                    category="overclaim",
                    description="Blocker.",
                    affected_text="text",
                ),
                AdversarialFinding(
                    finding_id="w1",
                    severity="warning",
                    category="weak_attribution",
                    description="Warning.",
                    affected_text="text",
                ),
            ],
            blocker_count=1,
            warning_count=1,
            pass_build=False,
        )
        assert len(r.get_blockers()) == 1
        assert r.get_blockers()[0].finding_id == "b1"

    def test_reviewer_notes_default_empty_string(self):
        r = AdversarialReviewResponse(
            section_id="sec_1",
            findings=[],
            blocker_count=0,
            warning_count=0,
            pass_build=True,
        )
        assert r.reviewer_notes == ""


# ---------------------------------------------------------------------------
# ContextPacket tests
# ---------------------------------------------------------------------------

class TestContextPacket:
    def test_context_packet_locked_figures_are_strings(self):
        """locked_figures must be dict[str, str] — display values only."""
        packet = ContextPacket(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="article_draft",
            locked_figures={
                "amergis_fy2425_total": "$10,970,973",
                "fy2425_staffing_vendor_total": "$13,326,622",
            },
        )
        assert isinstance(packet.locked_figures["amergis_fy2425_total"], str)
        assert packet.locked_figures["amergis_fy2425_total"] == "$10,970,973"

    def test_context_packet_invalid_task_profile_raises(self):
        with pytest.raises(ValidationError):
            ContextPacket(
                article_id="article_2",
                section_id="sec_1",
                run_id="run_001",
                task_profile="bad_profile",  # type: ignore
            )

    def test_context_packet_defaults_empty_collections(self):
        packet = ContextPacket(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="article_draft",
        )
        assert packet.locked_figures == {}
        assert packet.draftable_claims == []
        assert packet.support_context == []
        assert packet.task_instructions == ""
        assert packet.canon_hash == ""

    def test_all_task_profiles_are_valid(self):
        for profile in ["article_draft", "figure_verification", "adversarial_review", "reply_packet"]:
            packet = ContextPacket(
                article_id="article_1",
                section_id="sec_1",
                run_id="run_001",
                task_profile=profile,  # type: ignore
            )
            assert packet.task_profile == profile


# ---------------------------------------------------------------------------
# ReplyPacketResponse tests
# ---------------------------------------------------------------------------

class TestReplyPacketResponse:
    def test_valid_reply_packet_constructs(self):
        r = ReplyPacketResponse(
            thread_id="thread_001",
            recipient_name="Superintendent Jane Smith",
            article_id="article_1",
            questions=["What was the rationale for the contract renewal?"],
            affected_claims=["claim_amergis_no_spending_cap"],
            deadline_recommendation="10 business days",
            packet_markdown="Dear Superintendent Smith,\n\nWe are writing to...",
            publication_blocking=True,
        )
        assert r.publication_blocking is True
        assert r.recipient_name == "Superintendent Jane Smith"

    def test_publication_blocking_defaults_false(self):
        r = ReplyPacketResponse(
            thread_id="t1",
            recipient_name="Test Recipient",
            article_id="article_1",
        )
        assert r.publication_blocking is False

    def test_legacy_recipient_alias(self):
        r = ReplyPacketResponse(
            thread_id="t1",
            recipient_name="Test Recipient",
            article_id="article_1",
        )
        assert r.recipient == "Test Recipient"

    def test_legacy_outstanding_claims_alias(self):
        r = ReplyPacketResponse(
            thread_id="t1",
            recipient_name="Test Recipient",
            article_id="article_1",
            affected_claims=["claim_abc"],
        )
        assert r.outstanding_claims == ["claim_abc"]
