"""
src/services/backup_service.py
BackupService — creates, lists, restores, and verifies backups of
db/*.db, canonical/, and runs/ directories.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.core.logging import get_logger
from src.core.settings import WoodwardSettings

logger = get_logger(__name__)


class BackupService:
    """
    Manages backups of the Woodward data layer.

    Backups include:
      - db/*.db files (ledger.db, records.db, comms.db)
      - canonical/ directory (YAML files)
      - Latest runs/ content (for audit trail continuity)

    Restores recover db/ and canonical/ only. runs/ are not restored
    to preserve the audit trail.
    """

    def __init__(self, settings: WoodwardSettings) -> None:
        self.db_path = settings.db_path_obj
        self.canonical_path = settings.canonical_path_obj
        self.runs_path = settings.runs_path_obj
        self.backups_path = self._resolve_backups_path(settings)

    @staticmethod
    def _resolve_backups_path(settings: WoodwardSettings) -> Path:
        """Resolve the backups directory. Defaults to ./backups relative to db_path parent."""
        # backups_path is a sibling of db_path
        return settings.db_path_obj.parent / "backups"

    def create_backup(self) -> str:
        """
        Copy db/*.db, canonical/, and runs/ to backups/backup_YYYYMMDD_HHMMSS/.
        Returns the backup_id (directory name).
        """
        now = datetime.now(timezone.utc)
        backup_id = f"backup_{now.strftime('%Y%m%d_%H%M%S')}"
        backup_dir = self.backups_path / backup_id

        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy database files
        db_backup = backup_dir / "db"
        db_backup.mkdir(exist_ok=True)
        for db_file in self.db_path.glob("*.db"):
            shutil.copy2(str(db_file), str(db_backup / db_file.name))
            logger.info(f"Backed up: {db_file.name}")

        # Copy canonical directory
        canonical_backup = backup_dir / "canonical"
        if self.canonical_path.is_dir():
            shutil.copytree(
                str(self.canonical_path),
                str(canonical_backup),
                dirs_exist_ok=True,
            )
            logger.info("Backed up: canonical/")

        # Copy runs directory
        runs_backup = backup_dir / "runs"
        if self.runs_path.is_dir():
            shutil.copytree(
                str(self.runs_path),
                str(runs_backup),
                dirs_exist_ok=True,
            )
            logger.info("Backed up: runs/")

        logger.info(f"Backup created: {backup_id}")
        return backup_id

    def list_backups(self) -> list[dict]:
        """
        List all backups with id, timestamp, and size.
        Returns a list of dicts sorted by timestamp (newest first).
        """
        if not self.backups_path.is_dir():
            return []

        backups: list[dict] = []
        for entry in sorted(self.backups_path.iterdir(), reverse=True):
            if not entry.is_dir() or not entry.name.startswith("backup_"):
                continue

            # Calculate total size
            total_size = sum(
                f.stat().st_size
                for f in entry.rglob("*")
                if f.is_file()
            )

            # Parse timestamp from name
            try:
                ts_str = entry.name.replace("backup_", "")
                ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                timestamp = ts.isoformat() + "Z"
            except ValueError:
                timestamp = "unknown"

            backups.append({
                "backup_id": entry.name,
                "timestamp": timestamp,
                "size_bytes": total_size,
                "size_mb": round(total_size / (1024 * 1024), 2),
                "path": str(entry),
            })

        return backups

    def restore_backup(self, backup_id: str) -> None:
        """
        Restore db/*.db and canonical/ from a backup.
        Does NOT restore runs/ to preserve audit trail integrity.

        Raises:
            FileNotFoundError: if the backup directory does not exist
            ValueError: if the backup is invalid (missing expected files)
        """
        backup_dir = self.backups_path / backup_id
        if not backup_dir.is_dir():
            raise FileNotFoundError(f"Backup not found: {backup_dir}")

        if not self.verify_backup(backup_id):
            raise ValueError(f"Backup '{backup_id}' failed verification — files may be corrupt")

        # Restore database files
        db_backup = backup_dir / "db"
        if db_backup.is_dir():
            for db_file in db_backup.glob("*.db"):
                target = self.db_path / db_file.name
                shutil.copy2(str(db_file), str(target))
                logger.info(f"Restored: {db_file.name}")

        # Restore canonical directory
        canonical_backup = backup_dir / "canonical"
        if canonical_backup.is_dir():
            # Remove existing canonical files, then copy from backup
            if self.canonical_path.is_dir():
                shutil.rmtree(str(self.canonical_path))
            shutil.copytree(
                str(canonical_backup),
                str(self.canonical_path),
            )
            logger.info("Restored: canonical/")

        logger.info(f"Restore complete from: {backup_id}")

    def verify_backup(self, backup_id: str) -> bool:
        """
        Check that backup files exist and are not empty.
        Returns True if the backup passes basic verification.
        """
        backup_dir = self.backups_path / backup_id
        if not backup_dir.is_dir():
            return False

        # Check that db/ subdirectory exists and has at least one .db file
        db_backup = backup_dir / "db"
        if not db_backup.is_dir():
            return False

        db_files = list(db_backup.glob("*.db"))
        if not db_files:
            return False

        # Verify no .db file is zero bytes
        for db_file in db_files:
            if db_file.stat().st_size == 0:
                return False

        # Check that canonical/ subdirectory exists
        canonical_backup = backup_dir / "canonical"
        if not canonical_backup.is_dir():
            return False

        # Check at least one YAML file exists in canonical backup
        yaml_files = list(canonical_backup.glob("*.yaml"))
        if not yaml_files:
            return False

        return True
