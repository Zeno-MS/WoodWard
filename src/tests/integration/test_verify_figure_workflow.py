"""
tests/integration/test_verify_figure_workflow.py
Integration tests for the verify_figure workflow.
Uses tmp_path and real canonical/migration infrastructure.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.db_migrator import DbMigrator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def migrations_root() -> Path:
    here = Path(__file__).parent
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent / "db" / "migrations"
    return Path("db") / "migrations"


@pytest.fixture
def valid_canonical_dir(tmp_path: Path) -> Path:
    """Create a minimal canonical dir with one locked figure."""
    canon = tmp_path / "canonical"
    canon.mkdir()

    (canon / "schema_version.yaml").write_text(
        "schema_version: '1.0.0'\ncreated: '2026-03-12'\ninvestigation: test\nlocked_by: test\n"
    )
    (canon / "figures.yaml").write_text(textwrap.dedent("""\
        figures:
          - figure_id: test_staffing_total
            display_label: "Test Staffing Total"
            value: 13326622
            display_value: "$13,326,622"
            fiscal_year: "FY2024-25"
            source_of_truth: "ledger.db/fiscal_rollups"
            derivation_id: "deriv_test_staffing"
            status: locked
            notes: "Test figure for integration test"
    """))
    (canon / "vendor_scope.yaml").write_text(textwrap.dedent("""\
        vendors:
          - vendor_id: amergis
            canonical_name: "Amergis Healthcare"
            aliases: ["Maxim Healthcare"]
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
    (canon / "claims_registry.yaml").write_text("claims: []\n")
    (canon / "banned_claims.yaml").write_text("banned_claims: []\n")
    (canon / "source_policy.yaml").write_text(textwrap.dedent("""\
        source_classes:
          - source_class: public_record
            status: allowed
            description: "Official documents"
            citation_requirement: "Title and date"
    """))

    return canon


@pytest.fixture
def settings_with_tmp_paths(tmp_path: Path, valid_canonical_dir: Path):
    """Create a WoodwardSettings-like object using tmp_path directories."""
    from src.core.settings import WoodwardSettings

    db_dir = tmp_path / "db"
    db_dir.mkdir()
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    # Use environment variable override
    settings = WoodwardSettings(
        _env_file=None,
        **{
            "WOODWARD_DB_PATH": str(db_dir),
            "WOODWARD_CANONICAL_PATH": str(valid_canonical_dir),
            "WOODWARD_RUNS_PATH": str(runs_dir),
            "WOODWARD_LANCEDB_PATH": str(tmp_path / "lancedb"),
        }
    )
    return settings


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verify_figure_produces_report(
    tmp_path: Path,
    valid_canonical_dir: Path,
    migrations_root: Path,
) -> None:
    """verify_figure workflow must produce a VerificationReport."""
    from src.core.settings import WoodwardSettings
    from src.workflows.verify_figure import verify_figure

    db_dir = tmp_path / "db"
    db_dir.mkdir()
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    # Run migrations
    migrator = DbMigrator()
    await migrator.migrate_all(db_dir, migrations_root)

    # Create settings pointing to tmp directories
    settings = WoodwardSettings.model_construct(
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        env="development",
        investigation="test",
        db_path=str(db_dir),
        canonical_path=str(valid_canonical_dir),
        runs_path=str(runs_dir),
        lancedb_path=str(tmp_path / "lancedb"),
        log_level="WARNING",
        default_embedding_model="text-embedding-3-small",
        default_llm_model="gpt-4o",
    )

    run_id = "test_run_001"
    report = await verify_figure("test_staffing_total", settings, run_id)

    # Report must exist
    assert report is not None
    assert report.run_id == run_id
    assert report.figure_id == "test_staffing_total"
    assert report.canonical_value == 13326622
    # No derivation in empty DB — should be no_derivation status
    assert report.status in ("no_derivation", "pass", "fail", "canon_error")


@pytest.mark.asyncio
async def test_verify_figure_writes_run_artifact(
    tmp_path: Path,
    valid_canonical_dir: Path,
    migrations_root: Path,
) -> None:
    """verify_figure workflow must write verification_report.json and canon_hash.json."""
    from src.core.settings import WoodwardSettings
    from src.workflows.verify_figure import verify_figure

    db_dir = tmp_path / "db"
    db_dir.mkdir()
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    migrator = DbMigrator()
    await migrator.migrate_all(db_dir, migrations_root)

    settings = WoodwardSettings.model_construct(
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        env="development",
        investigation="test",
        db_path=str(db_dir),
        canonical_path=str(valid_canonical_dir),
        runs_path=str(runs_dir),
        lancedb_path=str(tmp_path / "lancedb"),
        log_level="WARNING",
        default_embedding_model="text-embedding-3-small",
        default_llm_model="gpt-4o",
    )

    run_id = "test_run_002"
    await verify_figure("test_staffing_total", settings, run_id)

    # Check artifacts were written
    run_dir = runs_dir / run_id
    assert run_dir.exists(), f"Run directory {run_dir} was not created"

    report_file = run_dir / "verification_report.json"
    assert report_file.exists(), "verification_report.json was not written"

    canon_hash_file = run_dir / "canon_hash.json"
    assert canon_hash_file.exists(), "canon_hash.json was not written"

    # Report must be valid JSON
    report_data = json.loads(report_file.read_text())
    assert report_data["run_id"] == run_id
    assert report_data["figure_id"] == "test_staffing_total"
    assert "status" in report_data
    assert "canon_hash" in report_data
    assert "timestamp" in report_data


@pytest.mark.asyncio
async def test_verify_figure_no_derivation_status(
    tmp_path: Path,
    valid_canonical_dir: Path,
    migrations_root: Path,
) -> None:
    """An empty ledger.db should produce status='no_derivation' (not an error)."""
    from src.core.settings import WoodwardSettings
    from src.workflows.verify_figure import verify_figure

    db_dir = tmp_path / "db"
    db_dir.mkdir()
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    migrator = DbMigrator()
    await migrator.migrate_all(db_dir, migrations_root)

    settings = WoodwardSettings.model_construct(
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        env="development",
        investigation="test",
        db_path=str(db_dir),
        canonical_path=str(valid_canonical_dir),
        runs_path=str(runs_dir),
        lancedb_path=str(tmp_path / "lancedb"),
        log_level="WARNING",
        default_embedding_model="text-embedding-3-small",
        default_llm_model="gpt-4o",
    )

    run_id = "test_run_003"
    report = await verify_figure("test_staffing_total", settings, run_id)

    # Empty DB has no derivation — must return no_derivation, not raise
    assert report.status == "no_derivation"
    assert report.computed_value is None


@pytest.mark.asyncio
async def test_verify_figure_with_seeded_derivation(
    tmp_path: Path,
    valid_canonical_dir: Path,
    migrations_root: Path,
) -> None:
    """A seeded derivation with the correct value should produce status='pass'."""
    import aiosqlite
    from src.core.settings import WoodwardSettings
    from src.workflows.verify_figure import verify_figure

    db_dir = tmp_path / "db"
    db_dir.mkdir()
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    migrator = DbMigrator()
    await migrator.migrate_all(db_dir, migrations_root)

    # Seed a derivation with the correct value
    ledger_db = db_dir / "ledger.db"
    async with aiosqlite.connect(str(ledger_db)) as db:
        await db.execute(
            "INSERT INTO figure_derivations "
            "(derivation_id, figure_id, sql_query, computed_value, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "deriv_test_staffing",
                "test_staffing_total",
                "SELECT 13326622.0",
                13326622.0,
                "verified",
            ),
        )
        await db.commit()

    settings = WoodwardSettings.model_construct(
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        env="development",
        investigation="test",
        db_path=str(db_dir),
        canonical_path=str(valid_canonical_dir),
        runs_path=str(runs_dir),
        lancedb_path=str(tmp_path / "lancedb"),
        log_level="WARNING",
        default_embedding_model="text-embedding-3-small",
        default_llm_model="gpt-4o",
    )

    run_id = "test_run_004"
    report = await verify_figure("test_staffing_total", settings, run_id)

    assert report.status == "pass"
    assert report.computed_value == 13326622.0
    assert report.canonical_value == 13326622.0
