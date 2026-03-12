"""
src/workflows/verify_figure.py
verify_figure — the primary figure verification workflow.
Loads canon, hashes it, validates it, then verifies a single locked figure
against its ledger.db derivation.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from schemas.canonical import CanonManifest
from src.core.exceptions import CanonValidationError, FigureMismatchError
from src.core.hashing import CanonHash
from src.core.logging import get_logger, set_run_id
from src.core.settings import WoodwardSettings
from src.repositories.canonical_repo import CanonicalRepo
from src.repositories.ledger_repo import LedgerRepo
from src.services.canonical_lock_service import CanonicalLockService
from src.services.figure_verifier import FigureVerificationResult, FigureVerifier
from src.services.vendor_alias_resolver import VendorAliasResolver

logger = get_logger(__name__)


@dataclass
class VerificationReport:
    """Full report from the verify_figure workflow."""
    run_id: str
    figure_id: str
    derivation_id: Optional[str]
    computed_value: Optional[float]
    canonical_value: float
    status: str         # "pass" | "fail" | "no_derivation" | "canon_error"
    canon_hash: str     # combined_hash from CanonHash
    timestamp: str
    notes: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "figure_id": self.figure_id,
            "derivation_id": self.derivation_id,
            "computed_value": self.computed_value,
            "canonical_value": self.canonical_value,
            "status": self.status,
            "canon_hash": self.canon_hash,
            "timestamp": self.timestamp,
            "notes": self.notes,
            "error": self.error,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


async def verify_figure(
    figure_id: str,
    settings: WoodwardSettings,
    run_id: Optional[str] = None,
) -> VerificationReport:
    """
    Execute the verify_figure workflow.

    Steps:
    1. Establish run_id and set logging context
    2. Load canon from canonical_path
    3. Emit canon hash to runs/{run_id}/canon_hash.json
    4. Validate canon (hard-stop on error)
    5. Open ledger.db
    6. Run figure_verifier.verify()
    7. Write runs/{run_id}/verification_report.json
    8. Return VerificationReport

    Raises:
        CanonValidationError: if canonical files are invalid (hard-stop)
        FigureMismatchError: NOT raised here — the report captures the mismatch.
            The caller decides whether to hard-stop.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]

    set_run_id(run_id)
    logger.info(f"verify_figure: starting run_id={run_id} figure_id={figure_id}")

    canonical_path = settings.canonical_path_obj
    runs_path = settings.runs_path_obj
    ledger_db_path = settings.ledger_db_path
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Step 1: Load and validate canon
    lock_service = CanonicalLockService()

    try:
        lock_service.validate_canon(canonical_path)
        logger.info("Canon validation: PASS")
    except CanonValidationError as e:
        logger.error(f"Canon validation FAILED: {e}")
        report = VerificationReport(
            run_id=run_id,
            figure_id=figure_id,
            derivation_id=None,
            computed_value=None,
            canonical_value=0.0,
            status="canon_error",
            canon_hash="",
            timestamp=timestamp,
            error=str(e),
        )
        _write_report(report, runs_path, run_id)
        raise  # hard-stop

    # Step 2: Emit canon hash
    canon_hash = lock_service.emit_canon_hash(canonical_path, runs_path, run_id)
    logger.info(f"Canon hash: {canon_hash.combined_hash[:16]}...")

    # Step 3: Load canon manifest
    repo = CanonicalRepo(canonical_path)
    canon = repo.load_all()

    # Step 4: Check figure exists in canon
    figure = canon.get_figure(figure_id)
    if figure is None:
        report = VerificationReport(
            run_id=run_id,
            figure_id=figure_id,
            derivation_id=None,
            computed_value=None,
            canonical_value=0.0,
            status="no_derivation",
            canon_hash=canon_hash.combined_hash,
            timestamp=timestamp,
            notes=f"Figure '{figure_id}' not found in canonical manifest",
        )
        _write_report(report, runs_path, run_id)
        return report

    # Step 5: Run figure verification
    ledger = LedgerRepo(ledger_db_path)
    verifier = FigureVerifier()

    try:
        result: FigureVerificationResult = await verifier.verify(figure_id, canon, ledger)
        logger.info(
            f"Figure verification: {result.status} "
            f"computed={result.computed_value} canonical={result.canonical_value}"
        )
    except Exception as e:
        logger.error(f"Figure verification error: {e}")
        report = VerificationReport(
            run_id=run_id,
            figure_id=figure_id,
            derivation_id=None,
            computed_value=None,
            canonical_value=figure.value,
            status="fail",
            canon_hash=canon_hash.combined_hash,
            timestamp=timestamp,
            error=str(e),
        )
        _write_report(report, runs_path, run_id)
        return report

    report = VerificationReport(
        run_id=run_id,
        figure_id=result.figure_id,
        derivation_id=result.derivation_id,
        computed_value=result.computed_value,
        canonical_value=result.canonical_value,
        status=result.status,
        canon_hash=canon_hash.combined_hash,
        timestamp=timestamp,
        notes=result.notes,
    )

    _write_report(report, runs_path, run_id)
    logger.info(f"verify_figure complete: status={report.status}")

    return report


def _write_report(
    report: VerificationReport, runs_path: Path, run_id: str
) -> None:
    """Write the verification report to runs/{run_id}/verification_report.json."""
    run_dir = runs_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "verification_report.json"
    report_path.write_text(report.to_json(), encoding="utf-8")
    logger.info(f"Report written to {report_path}")
