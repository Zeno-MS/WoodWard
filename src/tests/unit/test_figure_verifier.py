"""
tests/unit/test_figure_verifier.py
Unit tests for FigureVerifier.
Uses mock ledger repos to avoid database dependencies in unit tests.
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schemas.canonical import CanonicalFigure, CanonManifest
from schemas.ledger_models import FigureDerivation
from src.core.exceptions import FigureMismatchError
from src.services.figure_verifier import FigureVerificationResult, FigureVerifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_figure(
    figure_id: str = "test_fig",
    value: float = 13326622.0,
    status: str = "locked",
) -> CanonicalFigure:
    return CanonicalFigure(
        figure_id=figure_id,
        display_label="Test Figure",
        value=value,
        display_value=f"${value:,.0f}",
        fiscal_year="FY2024-25",
        source_of_truth="ledger.db/fiscal_rollups",
        derivation_id=f"deriv_{figure_id}",
        status=status,
    )


def _make_canon(figures: list[CanonicalFigure]) -> CanonManifest:
    """Create a minimal CanonManifest with just figures."""
    from schemas.canonical import SchemaVersion, SourcePolicy
    return CanonManifest(
        schema_version=SchemaVersion(
            schema_version="1.0.0",
            created="2026-03-12",
            investigation="test",
            locked_by="test",
        ),
        figures=figures,
        vendors=[],
        articles=[],
        claims=[],
        banned_claims=[],
        source_policy=SourcePolicy(source_classes=[]),
    )


def _make_derivation(
    figure_id: str,
    computed_value: Optional[float] = None,
    derivation_id: str = "deriv_test",
    sql_query: str = "SELECT 13326622.0",
) -> FigureDerivation:
    return FigureDerivation(
        derivation_id=derivation_id,
        figure_id=figure_id,
        sql_query=sql_query,
        computed_value=computed_value,
        canonical_value=None,
        status="computed",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_figure_matches_lock_passes() -> None:
    """When computed_value matches canonical value, status should be 'pass'."""
    figure = _make_figure("test_fig", value=13326622.0)
    canon = _make_canon([figure])

    derivation = _make_derivation("test_fig", computed_value=13326622.0)

    mock_ledger = MagicMock()
    mock_ledger.get_derivation_for_figure = AsyncMock(return_value=derivation)

    verifier = FigureVerifier()
    result = await verifier.verify("test_fig", canon, mock_ledger)

    assert result.status == "pass"
    assert result.computed_value == 13326622.0
    assert result.canonical_value == 13326622.0
    assert result.passed is True


@pytest.mark.asyncio
async def test_figure_mismatch_raises_error() -> None:
    """When computed_value differs from canonical, verify_and_raise should raise FigureMismatchError."""
    figure = _make_figure("test_fig", value=13326622.0)
    canon = _make_canon([figure])

    # Computed value is off by $100,000 — well above tolerance
    derivation = _make_derivation("test_fig", computed_value=13226622.0)

    mock_ledger = MagicMock()
    mock_ledger.get_derivation_for_figure = AsyncMock(return_value=derivation)

    verifier = FigureVerifier()

    with pytest.raises(FigureMismatchError) as exc_info:
        await verifier.verify_and_raise("test_fig", canon, mock_ledger)

    error = exc_info.value
    assert error.context["figure_id"] == "test_fig"
    assert error.context["computed_value"] == 13226622.0
    assert error.context["canonical_value"] == 13326622.0


@pytest.mark.asyncio
async def test_figure_mismatch_returns_fail_status() -> None:
    """verify() (non-raising) should return status='fail' on mismatch."""
    figure = _make_figure("test_fig", value=13326622.0)
    canon = _make_canon([figure])

    derivation = _make_derivation("test_fig", computed_value=99999.0)  # Very wrong

    mock_ledger = MagicMock()
    mock_ledger.get_derivation_for_figure = AsyncMock(return_value=derivation)

    verifier = FigureVerifier()
    result = await verifier.verify("test_fig", canon, mock_ledger)

    assert result.status == "fail"
    assert result.passed is False


@pytest.mark.asyncio
async def test_missing_derivation_returns_no_derivation_status() -> None:
    """When no derivation record exists in ledger.db, status should be 'no_derivation'."""
    figure = _make_figure("test_fig", value=13326622.0)
    canon = _make_canon([figure])

    mock_ledger = MagicMock()
    mock_ledger.get_derivation_for_figure = AsyncMock(return_value=None)

    verifier = FigureVerifier()
    result = await verifier.verify("test_fig", canon, mock_ledger)

    assert result.status == "no_derivation"
    assert result.computed_value is None
    assert result.derivation_id is None


@pytest.mark.asyncio
async def test_unknown_figure_returns_no_derivation() -> None:
    """Verifying a figure_id not in canon should return no_derivation."""
    canon = _make_canon([])  # Empty figures list

    mock_ledger = MagicMock()
    mock_ledger.get_derivation_for_figure = AsyncMock(return_value=None)

    verifier = FigureVerifier()
    result = await verifier.verify("nonexistent_figure", canon, mock_ledger)

    assert result.status == "no_derivation"


@pytest.mark.asyncio
async def test_figure_within_tolerance_passes() -> None:
    """A computed value within the tolerance (1.0) should pass."""
    figure = _make_figure("test_fig", value=13326622.0)
    canon = _make_canon([figure])

    # Off by 0.5 — within default tolerance of 1.0
    derivation = _make_derivation("test_fig", computed_value=13326622.5)

    mock_ledger = MagicMock()
    mock_ledger.get_derivation_for_figure = AsyncMock(return_value=derivation)

    verifier = FigureVerifier()
    result = await verifier.verify("test_fig", canon, mock_ledger)

    assert result.status == "pass"


@pytest.mark.asyncio
async def test_derivation_sql_executed_when_no_precomputed_value(tmp_path) -> None:
    """When derivation has no computed_value, the SQL query should be executed against ledger.db."""
    import aiosqlite
    from src.repositories.ledger_repo import LedgerRepo
    from src.services.db_migrator import DbMigrator
    from pathlib import Path

    # Build a real (temp) ledger.db with the derivation seeded
    db_path = tmp_path / "ledger.db"
    migrations_root = Path(__file__).parent
    # Find the actual migrations root
    for parent in [Path(__file__).parent, *Path(__file__).parents]:
        if (parent / "pyproject.toml").exists():
            migrations_root = parent / "db" / "migrations"
            break

    migrator = DbMigrator()
    await migrator.migrate(db_path, migrations_root, "ledger")

    # Seed a derivation with no pre-computed value — SQL must be run
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute(
            "INSERT INTO figure_derivations (derivation_id, figure_id, sql_query, computed_value, status) "
            "VALUES (?, ?, ?, ?, ?)",
            ("deriv_sql_test", "test_fig", "SELECT 1000.0", None, "pending"),
        )
        await db.commit()

    figure = _make_figure("test_fig", value=1000.0)
    canon = _make_canon([figure])

    ledger = LedgerRepo(db_path)
    verifier = FigureVerifier()
    result = await verifier.verify("test_fig", canon, ledger)

    # The SQL query "SELECT 1000.0" returns 1000.0 which matches canonical 1000.0
    assert result.status == "pass"
    assert result.computed_value == 1000.0
