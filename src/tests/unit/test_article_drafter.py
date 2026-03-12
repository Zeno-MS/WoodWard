"""
src/tests/unit/test_article_drafter.py
Unit tests for ArticleDrafter and ContextAssembler.
All LLM provider calls are mocked — no real API calls.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schemas.llm_contracts import (
    ContextPacket,
    DraftSectionResponse,
    FactualAssertion,
)
from src.core.exceptions import HallucinatedContextError
from src.services.article_drafter import ArticleDrafter
from src.services.context_assembler import ContextAssembler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_context_packet(
    locked_figures: dict | None = None,
    draftable_claims: list | None = None,
    support_context: list | None = None,
) -> ContextPacket:
    return ContextPacket(
        article_id="article_2",
        section_id="sec_intro",
        run_id="run_test_001",
        task_profile="article_draft",
        locked_figures=locked_figures or {
            "amergis_fy2425_total": "$10,970,973",
            "fy2425_staffing_vendor_total": "$13,326,622",
        },
        draftable_claims=draftable_claims or [
            {
                "claim_id": "claim_amergis_fy2425_payment",
                "text": "VPS paid $10,970,973 to Amergis in FY24-25",
                "status": "verified",
                "right_of_reply_required": 0,
            }
        ],
        support_context=support_context or [
            {
                "chunk_id": "chunk_001",
                "doc_id": "doc_warrant_register",
                "content": "Amergis payment records totaling $10,970,973",
                "doc_title": "VPS Warrant Register FY24-25",
                "source_class": "public_record",
                "claim_id": "claim_amergis_fy2425_payment",
            }
        ],
        canon_hash="abc123",
    )


def make_valid_draft_response(context: ContextPacket) -> DraftSectionResponse:
    """Make a valid DraftSectionResponse that references real IDs from context."""
    return DraftSectionResponse(
        section_id=context.section_id,
        article_id=context.article_id,
        content="Vancouver Public Schools paid $10,970,973 to Amergis in FY2024-25.",
        assertions=[
            FactualAssertion(
                text="Vancouver Public Schools paid $10,970,973 to Amergis in FY2024-25.",
                context_ids=["chunk_001"],
                claim_ids=["claim_amergis_fy2425_payment"],
                figure_ids=["amergis_fy2425_total"],
            )
        ],
        figures_used=["amergis_fy2425_total"],
        word_count=12,
    )


def make_mock_provider(response: DraftSectionResponse) -> AsyncMock:
    """Create a mock provider client that returns the given response."""
    provider = AsyncMock()
    provider.complete_structured = AsyncMock(return_value=response)
    return provider


# ---------------------------------------------------------------------------
# ArticleDrafter — context_id validation tests
# ---------------------------------------------------------------------------

class TestArticleDrafterContextIdValidation:
    """Tests that _validate_context_ids raises on hallucinated IDs."""

    def test_drafter_raises_on_hallucinated_context_id(self):
        """If an assertion references a chunk_id not in support_context, must raise."""
        context = make_context_packet()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        bad_response = DraftSectionResponse(
            section_id="sec_intro",
            article_id="article_2",
            content="VPS paid vendors.",
            assertions=[
                FactualAssertion(
                    text="VPS paid vendors.",
                    context_ids=["chunk_DOES_NOT_EXIST"],  # Hallucinated
                )
            ],
        )

        with pytest.raises(HallucinatedContextError):
            drafter._validate_context_ids(bad_response, context)

    def test_drafter_raises_on_missing_context_ids(self):
        """An assertion with context_ids pointing to nonexistent IDs must raise."""
        context = make_context_packet(support_context=[
            {
                "chunk_id": "chunk_real",
                "doc_id": "doc_real",
                "content": "Real content",
                "doc_title": "Real Doc",
                "source_class": "public_record",
                "claim_id": "claim_amergis_fy2425_payment",
            }
        ])
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        bad_response = DraftSectionResponse(
            section_id="sec_intro",
            article_id="article_2",
            content="VPS paid vendors.",
            assertions=[
                FactualAssertion(
                    text="VPS paid vendors.",
                    context_ids=["chunk_real", "chunk_HALLUCINATED"],  # Second is bad
                )
            ],
        )

        with pytest.raises(HallucinatedContextError) as exc_info:
            drafter._validate_context_ids(bad_response, context)
        assert "chunk_HALLUCINATED" in str(exc_info.value)

    def test_drafter_passes_when_context_ids_are_valid(self):
        """Valid context_ids should not raise."""
        context = make_context_packet()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        good_response = make_valid_draft_response(context)
        # Should not raise
        drafter._validate_context_ids(good_response, context)

    def test_drafter_validates_claim_ids_against_draftable_claims(self):
        """claim_id in assertion that is not in draftable_claims must raise."""
        context = make_context_packet()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        bad_response = DraftSectionResponse(
            section_id="sec_intro",
            article_id="article_2",
            content="Something.",
            assertions=[
                FactualAssertion(
                    text="Something.",
                    claim_ids=["claim_DOES_NOT_EXIST"],  # Not in draftable_claims
                )
            ],
        )

        with pytest.raises(HallucinatedContextError):
            drafter._validate_context_ids(bad_response, context)

    def test_drafter_validates_figure_ids_against_locked_figures(self):
        """figure_id in assertion not in locked_figures must raise."""
        context = make_context_packet()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        bad_response = DraftSectionResponse(
            section_id="sec_intro",
            article_id="article_2",
            content="VPS spent millions.",
            assertions=[
                FactualAssertion(
                    text="VPS spent millions.",
                    figure_ids=["figure_HALLUCINATED"],  # Not in locked_figures
                )
            ],
        )

        with pytest.raises(HallucinatedContextError):
            drafter._validate_context_ids(bad_response, context)


# ---------------------------------------------------------------------------
# ArticleDrafter — prompt building tests
# ---------------------------------------------------------------------------

class TestArticleDrafterPromptBuilding:
    def test_drafter_injects_locked_figures_in_prompt(self):
        """Locked figures must appear in the prompt string."""
        context = make_context_packet(locked_figures={
            "amergis_fy2425_total": "$10,970,973",
        })
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        prompt = drafter._build_prompt(context)

        assert "amergis_fy2425_total" in prompt
        assert "$10,970,973" in prompt

    def test_drafter_includes_draftable_claims_in_prompt(self):
        """Draftable claim IDs and text must appear in the prompt."""
        context = make_context_packet()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        prompt = drafter._build_prompt(context)

        assert "claim_amergis_fy2425_payment" in prompt

    def test_drafter_includes_support_context_in_prompt(self):
        """Support context chunk IDs must appear in the prompt."""
        context = make_context_packet()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=MagicMock())

        prompt = drafter._build_prompt(context)

        assert "chunk_001" in prompt


# ---------------------------------------------------------------------------
# ArticleDrafter — full async draft_section test (mocked LLM)
# ---------------------------------------------------------------------------

class TestArticleDrafterDraftSection:
    @pytest.mark.asyncio
    async def test_drafter_validates_draft_section_response_schema(self):
        """A valid LLM response should be returned parsed and validated."""
        context = make_context_packet()
        valid_response = make_valid_draft_response(context)
        provider = make_mock_provider(valid_response)

        records_mock = AsyncMock()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=provider)

        result = await drafter.draft_section(context=context, records=records_mock)

        assert result.section_id == "sec_intro"
        assert result.article_id == "article_2"
        assert len(result.assertions) == 1
        provider.complete_structured.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_drafter_hard_stops_on_hallucinated_context_id(self):
        """If LLM returns a hallucinated context_id, must raise HallucinatedContextError."""
        context = make_context_packet()

        bad_response = DraftSectionResponse(
            section_id="sec_intro",
            article_id="article_2",
            content="Some claim.",
            assertions=[
                FactualAssertion(
                    text="Some claim.",
                    context_ids=["chunk_HALLUCINATED_BY_LLM"],
                )
            ],
        )
        provider = make_mock_provider(bad_response)

        records_mock = AsyncMock()
        drafter = ArticleDrafter(settings=MagicMock(), provider_client=provider)

        with pytest.raises(HallucinatedContextError):
            await drafter.draft_section(context=context, records=records_mock)


# ---------------------------------------------------------------------------
# ContextAssembler tests
# ---------------------------------------------------------------------------

class TestContextAssembler:
    def _make_canon(
        self,
        locked_figures: list | None = None,
        banned_claims: list | None = None,
    ):
        """Build a minimal CanonManifest mock."""
        from schemas.canonical import CanonManifest, CanonicalFigure, SourcePolicy, SchemaVersion

        canon = MagicMock(spec=CanonManifest)
        canon.get_locked_figures.return_value = locked_figures or []
        canon.banned_claims = banned_claims or []
        return canon

    def _make_locked_figure(self, figure_id: str, display_value: str):
        fig = MagicMock()
        fig.figure_id = figure_id
        fig.display_value = display_value
        fig.value = 10970973.0
        fig.status = "locked"
        return fig

    def _make_claim(
        self,
        claim_id: str = "claim_001",
        status: str = "verified",
        right_of_reply_required: int = 0,
    ) -> dict:
        """Return claim as a plain dict so Pydantic ContextPacket accepts it."""
        return {
            "claim_id": claim_id,
            "status": status,
            "right_of_reply_required": right_of_reply_required,
            "text": f"Test claim {claim_id}",
            "article_id": "article_2",
            "public_citable": 1,
            "support_chain_complete": 1,
            "stale": 0,
        }

    @pytest.mark.asyncio
    async def test_context_assembler_uses_task_profile_correctly(self):
        """article_draft profile should include figures and use max_claims=20."""
        canon = self._make_canon(
            locked_figures=[self._make_locked_figure("amergis_fy2425_total", "$10,970,973")]
        )
        records = AsyncMock()
        records.get_claim_support.return_value = []
        ledger = AsyncMock()

        claims = [self._make_claim("claim_001")]

        assembler = ContextAssembler()
        packet = await assembler.assemble(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="article_draft",
            draftable_claims=claims,
            canon=canon,
            records=records,
            ledger=ledger,
            canon_hash="hash123",
        )

        assert packet.article_id == "article_2"
        assert packet.task_profile == "article_draft"
        # Figures should be included for article_draft
        assert "amergis_fy2425_total" in packet.locked_figures
        assert packet.locked_figures["amergis_fy2425_total"] == "$10,970,973"

    @pytest.mark.asyncio
    async def test_context_assembler_reply_packet_excludes_figures(self):
        """reply_packet profile has include_figures=False."""
        canon = self._make_canon(
            locked_figures=[self._make_locked_figure("amergis_fy2425_total", "$10,970,973")]
        )
        records = AsyncMock()
        records.get_claim_support.return_value = []
        ledger = AsyncMock()

        assembler = ContextAssembler()
        packet = await assembler.assemble(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="reply_packet",
            draftable_claims=[],
            canon=canon,
            records=records,
            ledger=ledger,
        )

        # reply_packet has include_figures=False
        assert packet.locked_figures == {}

    @pytest.mark.asyncio
    async def test_context_assembler_never_includes_blocked_claims(self):
        """Blocked claims must be silently dropped, never included."""
        canon = self._make_canon()
        records = AsyncMock()
        records.get_claim_support.return_value = []
        ledger = AsyncMock()

        blocked_claim = self._make_claim("claim_blocked", status="blocked")
        verified_claim = self._make_claim("claim_verified", status="verified")

        assembler = ContextAssembler()
        packet = await assembler.assemble(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="article_draft",
            draftable_claims=[blocked_claim, verified_claim],
            canon=canon,
            records=records,
            ledger=ledger,
        )

        # Only the verified claim should appear
        claim_ids_in_packet = [c.get("claim_id") for c in packet.draftable_claims]
        assert "claim_blocked" not in claim_ids_in_packet
        assert "claim_verified" in claim_ids_in_packet

    @pytest.mark.asyncio
    async def test_context_assembler_enforces_max_claims_per_profile(self):
        """article_draft profile max_claims=20 — excess should be truncated."""
        canon = self._make_canon()
        records = AsyncMock()
        records.get_claim_support.return_value = []
        ledger = AsyncMock()

        # 25 claims — exceeds max_claims=20
        claims = [self._make_claim(f"claim_{i:03d}") for i in range(25)]

        assembler = ContextAssembler()
        packet = await assembler.assemble(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="article_draft",
            draftable_claims=claims,
            canon=canon,
            records=records,
            ledger=ledger,
        )

        assert len(packet.draftable_claims) <= 20

    @pytest.mark.asyncio
    async def test_context_assembler_invalid_task_profile_raises(self):
        """Unknown task_profile must raise ValueError."""
        canon = self._make_canon()
        records = AsyncMock()
        ledger = AsyncMock()

        assembler = ContextAssembler()
        with pytest.raises(ValueError, match="Unknown task_profile"):
            await assembler.assemble(
                article_id="article_2",
                section_id="sec_1",
                run_id="run_001",
                task_profile="bad_profile",
                draftable_claims=[],
                canon=canon,
                records=records,
                ledger=ledger,
            )

    @pytest.mark.asyncio
    async def test_context_assembler_canon_hash_embedded_in_packet(self):
        """canon_hash must be passed through to the ContextPacket."""
        canon = self._make_canon()
        records = AsyncMock()
        records.get_claim_support.return_value = []
        ledger = AsyncMock()

        assembler = ContextAssembler()
        packet = await assembler.assemble(
            article_id="article_2",
            section_id="sec_1",
            run_id="run_001",
            task_profile="article_draft",
            draftable_claims=[],
            canon=canon,
            records=records,
            ledger=ledger,
            canon_hash="sha256_deadbeef",
        )

        assert packet.canon_hash == "sha256_deadbeef"
