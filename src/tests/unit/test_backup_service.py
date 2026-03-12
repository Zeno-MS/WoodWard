"""
tests/unit/test_backup_service.py
Unit tests for BackupService.
Uses tmp_path fixtures for isolated filesystem operations.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.services.backup_service import BackupService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_project(tmp_path: Path) -> MagicMock:
    """Create a realistic project directory structure and return a mock settings object."""
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir()
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()

    # Create mock database files with content
    (db_dir / "ledger.db").write_bytes(b"ledger database content " * 100)
    (db_dir / "records.db").write_bytes(b"records database content " * 100)
    (db_dir / "comms.db").write_bytes(b"comms database content " * 100)

    # Create canonical YAML files
    (canonical_dir / "figures.yaml").write_text("figures: []\n", encoding="utf-8")
    (canonical_dir / "claims_registry.yaml").write_text("claims: []\n", encoding="utf-8")
    (canonical_dir / "schema_version.yaml").write_text(
        "schema_version: '1.0.0'\ncreated: '2026-03-12'\ninvestigation: test\nlocked_by: test\n",
        encoding="utf-8",
    )

    # Create a run artifact
    run_dir = runs_dir / "test_run_001"
    run_dir.mkdir()
    (run_dir / "canon_hash.json").write_text('{"hash": "abc123"}', encoding="utf-8")

    settings = MagicMock()
    settings.db_path_obj = db_dir
    settings.canonical_path_obj = canonical_dir
    settings.runs_path_obj = runs_dir
    settings.backups_path_obj = backups_dir

    return settings


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_create_backup_produces_files(tmp_path: Path) -> None:
    """create_backup should create a backup directory with db/, canonical/, and runs/ subdirs."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    backup_id = svc.create_backup()

    backup_dir = svc.backups_path / backup_id
    assert backup_dir.is_dir()

    # Check db files were copied
    assert (backup_dir / "db" / "ledger.db").is_file()
    assert (backup_dir / "db" / "records.db").is_file()
    assert (backup_dir / "db" / "comms.db").is_file()

    # Check canonical was copied
    assert (backup_dir / "canonical" / "figures.yaml").is_file()
    assert (backup_dir / "canonical" / "claims_registry.yaml").is_file()

    # Check runs were copied
    assert (backup_dir / "runs" / "test_run_001" / "canon_hash.json").is_file()


def test_list_backups_returns_created(tmp_path: Path) -> None:
    """list_backups should return all created backups."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    # Create two backups
    bid1 = svc.create_backup()
    # Need a small delay or unique name — use direct second create
    import time
    time.sleep(1.1)
    bid2 = svc.create_backup()

    backups = svc.list_backups()
    backup_ids = [b["backup_id"] for b in backups]

    assert bid1 in backup_ids
    assert bid2 in backup_ids
    assert len(backups) >= 2

    # Check that each backup has expected fields
    for b in backups:
        assert "backup_id" in b
        assert "timestamp" in b
        assert "size_bytes" in b
        assert "size_mb" in b
        assert b["size_bytes"] > 0


def test_restore_backup_recovers_state(tmp_path: Path) -> None:
    """Restoring a backup should recover db files and canonical to the backup state."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    # Create a backup
    backup_id = svc.create_backup()

    # Modify the original files
    (settings.db_path_obj / "ledger.db").write_bytes(b"MODIFIED ledger content")
    (settings.canonical_path_obj / "figures.yaml").write_text(
        "figures:\n  - figure_id: modified\n", encoding="utf-8"
    )

    # Verify files are modified
    assert (settings.db_path_obj / "ledger.db").read_bytes() == b"MODIFIED ledger content"

    # Restore from backup
    svc.restore_backup(backup_id)

    # Verify files are restored to original state
    restored_ledger = (settings.db_path_obj / "ledger.db").read_bytes()
    assert restored_ledger == b"ledger database content " * 100

    restored_figures = (settings.canonical_path_obj / "figures.yaml").read_text(encoding="utf-8")
    assert restored_figures == "figures: []\n"


def test_verify_backup_detects_corruption(tmp_path: Path) -> None:
    """verify_backup should return False if critical files are missing or empty."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    # Create a backup
    backup_id = svc.create_backup()

    # Verify it passes initially
    assert svc.verify_backup(backup_id) is True

    # Corrupt: empty out a db file
    backup_dir = svc.backups_path / backup_id
    (backup_dir / "db" / "ledger.db").write_bytes(b"")

    assert svc.verify_backup(backup_id) is False


def test_verify_backup_returns_false_for_nonexistent(tmp_path: Path) -> None:
    """verify_backup should return False for a backup that doesn't exist."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    assert svc.verify_backup("backup_nonexistent") is False


def test_restore_nonexistent_backup_raises(tmp_path: Path) -> None:
    """restore_backup should raise FileNotFoundError for a missing backup."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    with pytest.raises(FileNotFoundError):
        svc.restore_backup("backup_nonexistent")


def test_list_backups_empty_dir(tmp_path: Path) -> None:
    """list_backups should return empty list when no backups exist."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    backups = svc.list_backups()
    assert backups == []


def test_backup_id_format(tmp_path: Path) -> None:
    """Backup IDs should follow the backup_YYYYMMDD_HHMMSS format."""
    settings = _setup_project(tmp_path)
    svc = BackupService(settings)

    backup_id = svc.create_backup()

    assert backup_id.startswith("backup_")
    # Should be backup_YYYYMMDD_HHMMSS
    parts = backup_id.replace("backup_", "").split("_")
    assert len(parts) == 2
    assert len(parts[0]) == 8  # YYYYMMDD
    assert len(parts[1]) == 6  # HHMMSS
