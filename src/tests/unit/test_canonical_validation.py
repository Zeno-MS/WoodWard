"""
tests/unit/test_canonical_validation.py
Unit tests for canonical YAML loading and validation.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from schemas.canonical import CanonicalFigure, ClaimRecord
from src.core.exceptions import CanonValidationError
from src.repositories.canonical_repo import CanonicalRepo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_canon_dir(tmp_path: Path) -> Path:
    """Create a minimal valid canonical directory."""
    canon = tmp_path / "canonical"
    canon.mkdir()

    (canon / "schema_version.yaml").write_text(
        "schema_version: '1.0.0'\ncreated: '2026-03-12'\ninvestigation: test\nlocked_by: test\n"
    )
    (canon / "figures.yaml").write_text(textwrap.dedent("""\
        figures:
          - figure_id: test_figure_1
            display_label: "Test Figure"
            value: 13326622
            display_value: "$13,326,622"
            fiscal_year: "FY2024-25"
            source_of_truth: "ledger.db/fiscal_rollups"
            derivation_id: "deriv_test_1"
            status: locked
            notes: "Test figure"
    """))
    (canon / "vendor_scope.yaml").write_text(textwrap.dedent("""\
        vendors:
          - vendor_id: test_vendor
            canonical_name: "Test Vendor Inc"
            aliases: []
            rebrand_history: []
            canonical_total_included: true
    """))
    (canon / "articles.yaml").write_text(textwrap.dedent("""\
        articles:
          - article_id: article_1
            title: "Test Article"
            status: locked_baseline
            file_path: "test/article_1.md"
            locked: true
    """))
    (canon / "claims_registry.yaml").write_text(textwrap.dedent("""\
        claims:
          - claim_id: claim_test_1
            text: "VPS paid $13,326,622 to vendors"
            article_id: article_1
            status: verified
            public_citable: true
            support_chain_complete: true
            right_of_reply_required: false
            stale: false
    """))
    (canon / "banned_claims.yaml").write_text(textwrap.dedent("""\
        banned_claims:
          - ban_id: ban_001
            text_pattern: "Any claim implying fraud"
            reason: "Motive language"
            added_date: "2026-03-12"
    """))
    (canon / "source_policy.yaml").write_text(textwrap.dedent("""\
        source_classes:
          - source_class: public_record
            status: allowed
            description: "Official government documents"
            citation_requirement: "Document title and date"
    """))

    return canon


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_figures_yaml_loads(valid_canon_dir: Path) -> None:
    """A well-formed figures.yaml should load without errors."""
    repo = CanonicalRepo(valid_canon_dir)
    figures = repo.load_figures()
    assert len(figures) == 1
    assert figures[0].figure_id == "test_figure_1"
    assert figures[0].value == 13326622
    assert figures[0].status == "locked"


def test_malformed_figures_yaml_raises_canon_error(tmp_path: Path) -> None:
    """A YAML parse error in figures.yaml must raise CanonValidationError."""
    canon = tmp_path / "canonical"
    canon.mkdir()

    # Write deliberately broken YAML
    (canon / "figures.yaml").write_text("figures:\n  - : invalid: yaml: here: [unclosed\n")

    with pytest.raises(CanonValidationError):
        repo = CanonicalRepo(canon)
        repo.load_figures()


def test_locked_figure_value_matches(valid_canon_dir: Path) -> None:
    """Locked figure value must match the known seed value."""
    repo = CanonicalRepo(valid_canon_dir)
    figures = repo.load_figures()
    amergis_fig = figures[0]
    assert amergis_fig.value == 13326622


def test_unknown_status_raises_validation_error(tmp_path: Path) -> None:
    """A figure with an unknown status value must fail Pydantic validation."""
    canon = tmp_path / "canonical"
    canon.mkdir()

    (canon / "figures.yaml").write_text(textwrap.dedent("""\
        figures:
          - figure_id: bad_status_fig
            display_label: "Bad Status"
            value: 100
            display_value: "$100"
            fiscal_year: "FY2024-25"
            source_of_truth: "test"
            derivation_id: "test"
            status: "invalid_status_value"
    """))

    with pytest.raises(CanonValidationError) as exc_info:
        repo = CanonicalRepo(canon)
        repo.load_figures()

    assert "invalid_status_value" in str(exc_info.value) or "status" in str(exc_info.value)


def test_blocked_claim_cannot_be_public_citable(tmp_path: Path) -> None:
    """A blocked claim with public_citable=True must raise a validation error."""
    with pytest.raises(Exception):
        ClaimRecord(
            claim_id="c1",
            text="test claim",
            article_id="article_1",
            status="blocked",
            public_citable=True,       # Invalid combination
            support_chain_complete=False,
            right_of_reply_required=True,
            stale=False,
        )


def test_all_canonical_files_validate_together(valid_canon_dir: Path) -> None:
    """validate_all() must succeed when all files are valid."""
    repo = CanonicalRepo(valid_canon_dir)
    repo.validate_all()  # Must not raise


def test_missing_figure_file_raises_canon_error(tmp_path: Path) -> None:
    """Missing figures.yaml must raise CanonValidationError."""
    canon = tmp_path / "canonical"
    canon.mkdir()
    # Don't create figures.yaml

    with pytest.raises(CanonValidationError):
        repo = CanonicalRepo(canon)
        repo.load_figures()
