"""
src/workflows/run_nightly_audit.py
Nightly audit workflow — runs the full audit, writes the report to runs/,
prints a summary, and returns an appropriate exit code.

Can be called:
  - As an async function: await run_nightly_audit(settings)
  - From CLI: woodward audit run
  - Standalone: python3 -m src.workflows.run_nightly_audit
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.core.logging import configure_logging, get_logger
from src.core.settings import WoodwardSettings, get_settings
from src.repositories.canonical_repo import CanonicalRepo
from src.repositories.comms_repo import CommsRepo
from src.repositories.ledger_repo import LedgerRepo
from src.repositories.records_repo import RecordsRepo
from src.services.audit_runner import AuditReport, AuditRunner

logger = get_logger(__name__)


async def run_nightly_audit(
    settings: WoodwardSettings | None = None,
) -> AuditReport:
    """
    Run the full audit, write the report to runs/audit_YYYYMMDD_HHMMSS.json,
    and return the AuditReport.
    """
    if settings is None:
        settings = get_settings()

    # Build repos
    canonical_repo = CanonicalRepo(settings.canonical_path_obj)
    ledger_repo = LedgerRepo(settings.ledger_db_path)
    records_repo = RecordsRepo(settings.records_db_path)
    comms_repo = CommsRepo(settings.comms_db_path)

    # Run audit
    runner = AuditRunner(
        settings=settings,
        canonical_repo=canonical_repo,
        ledger_repo=ledger_repo,
        records_repo=records_repo,
        comms_repo=comms_repo,
    )

    report = await runner.run_full_audit()

    # Write report to runs/
    now = datetime.now(timezone.utc)
    report_filename = f"audit_{now.strftime('%Y%m%d_%H%M%S')}.json"
    runs_path = settings.runs_path_obj
    runs_path.mkdir(parents=True, exist_ok=True)
    report_path = runs_path / report_filename

    report_path.write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8",
    )

    logger.info(f"Audit report written to: {report_path}")

    return report


def print_summary(report: AuditReport) -> None:
    """Print a human-readable summary of the audit report to stdout."""
    status_label = "PASS" if report.overall_status == "pass" else "FAIL"
    print(f"\n{'='*60}")
    print(f"  WOODWARD AUDIT REPORT — {status_label}")
    print(f"{'='*60}")
    print(f"  Timestamp:   {report.audit_timestamp}")
    print(f"  Canon Hash:  {report.canon_hash[:16]}...")
    print(f"  Overall:     {report.overall_status.upper()}")
    print()

    for check in report.checks:
        icon = "PASS" if check.status == "pass" else "FAIL"
        print(f"  [{icon}] {check.name} ({check.count} issue(s))")
        for detail in check.details:
            print(f"         {detail}")
        print()

    summary = report.summary
    print(f"  Summary: {summary.get('passed', 0)}/{summary.get('total_checks', 0)} checks passed")
    print(f"  Total issues: {summary.get('total_issues', 0)}")
    print(f"{'='*60}\n")


def main() -> int:
    """Entry point for standalone execution. Returns exit code."""
    configure_logging()
    report = asyncio.run(run_nightly_audit())
    print_summary(report)
    return 0 if report.overall_status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
