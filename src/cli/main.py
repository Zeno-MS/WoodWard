"""
src/cli/main.py
Woodward Core v2 — CLI entry point.
All commands are accessible via `woodward <command> <subcommand>`.
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.core.exceptions import CanonValidationError, WoodwardError
from src.core.logging import configure_logging, get_logger
from src.core.settings import get_settings

app = typer.Typer(
    name="woodward",
    help="Woodward Core v2 — Investigative journalism verification platform",
    no_args_is_help=True,
)
canon_app = typer.Typer(help="Canonical file operations")
db_app = typer.Typer(help="Database operations")
verify_app = typer.Typer(help="Verification workflows")
bridge_app = typer.Typer(help="Bridge and handoff tools")
reply_app = typer.Typer(help="Right-of-reply planning and outreach")
publish_app = typer.Typer(help="Publication gate and article assembly")
audit_app = typer.Typer(help="Audit and integrity checks")
backup_app = typer.Typer(help="Backup and restore operations")

app.add_typer(canon_app, name="canon")
app.add_typer(db_app, name="db")
app.add_typer(verify_app, name="verify")
app.add_typer(bridge_app, name="bridge")
app.add_typer(reply_app, name="reply")
app.add_typer(publish_app, name="publish")
app.add_typer(audit_app, name="audit")
app.add_typer(backup_app, name="backup")

console = Console()
err_console = Console(stderr=True, style="bold red")
logger = get_logger(__name__)


def _get_canonical_path() -> Path:
    settings = get_settings()
    return settings.canonical_path_obj


def _get_runs_path() -> Path:
    settings = get_settings()
    return settings.runs_path_obj


# ---------------------------------------------------------------------------
# canon commands
# ---------------------------------------------------------------------------

@canon_app.command("validate")
def canon_validate() -> None:
    """
    Validate all canonical YAML files. Exits with code 1 on failure.
    This is the boot-time gate — run this before any workflow.
    """
    configure_logging()
    settings = get_settings()

    from src.repositories.canonical_repo import CanonicalRepo

    canonical_path = settings.canonical_path_obj

    console.print(f"[bold]Validating canonical files at:[/bold] {canonical_path}")

    try:
        repo = CanonicalRepo(canonical_path)
        repo.validate_all()
        console.print("[bold green]CANON VALIDATION: PASS[/bold green]")
        console.print(
            f"  Figures: {len(repo.load_figures())} | "
            f"Vendors: {len(repo.load_vendor_scope())} | "
            f"Articles: {len(repo.load_articles())} | "
            f"Claims: {len(repo.load_claims())} | "
            f"Bans: {len(repo.load_banned_claims())}"
        )
    except CanonValidationError as e:
        err_console.print(f"CANON VALIDATION FAILED: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"Unexpected error during validation: {e}")
        raise typer.Exit(code=1)


@canon_app.command("hash")
def canon_hash(
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if not provided)")
) -> None:
    """
    Hash the canonical directory and emit to stdout and runs/latest/canon_hash.json.
    """
    configure_logging()
    settings = get_settings()

    if run_id is None:
        run_id = f"hash_{uuid.uuid4().hex[:8]}"

    from src.services.canonical_lock_service import CanonicalLockService

    lock_service = CanonicalLockService()
    try:
        canon_hash_obj = lock_service.emit_canon_hash(
            settings.canonical_path_obj,
            settings.runs_path_obj,
            run_id,
        )
        console.print(f"[bold]Canon Hash[/bold]")
        console.print(f"  Run ID:         {run_id}")
        console.print(f"  Combined Hash:  {canon_hash_obj.combined_hash}")
        console.print(f"  Schema Version: {canon_hash_obj.schema_version}")
        console.print(f"  Timestamp:      {canon_hash_obj.timestamp}")
        console.print(f"  Files Hashed:   {len(canon_hash_obj.individual_hashes)}")
        console.print(
            f"\n[dim]Written to: {settings.runs_path_obj / run_id / 'canon_hash.json'}[/dim]"
        )
    except Exception as e:
        err_console.print(f"Canon hash failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# verify commands
# ---------------------------------------------------------------------------

@verify_app.command("figure")
def verify_figure_cmd(
    figure_id: str = typer.Argument(..., help="Figure ID to verify (from figures.yaml)"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if not provided)"),
    fail_on_mismatch: bool = typer.Option(
        True, help="Exit with code 1 if figure doesn't match canonical value"
    ),
) -> None:
    """
    Verify a locked figure against its ledger.db derivation.
    Exits with code 1 if the figure fails verification and --fail-on-mismatch is set.
    """
    configure_logging()
    settings = get_settings()

    if run_id is None:
        run_id = f"verify_{uuid.uuid4().hex[:8]}"

    from src.workflows.verify_figure import verify_figure

    try:
        report = asyncio.run(verify_figure(figure_id, settings, run_id))

        status_color = "green" if report.status == "pass" else (
            "yellow" if report.status == "no_derivation" else "red"
        )
        console.print(f"\n[bold]Figure Verification Report[/bold]")
        console.print(f"  Figure ID:        {report.figure_id}")
        console.print(f"  Canonical Value:  {report.canonical_value:,.2f}")
        console.print(f"  Computed Value:   {report.computed_value if report.computed_value is not None else 'N/A'}")
        console.print(f"  Derivation ID:    {report.derivation_id or 'None'}")
        console.print(f"  Status:           [{status_color}]{report.status.upper()}[/{status_color}]")
        if report.notes:
            console.print(f"  Notes:            {report.notes}")
        console.print(f"  Canon Hash:       {report.canon_hash[:16]}...")
        console.print(f"  Run ID:           {report.run_id}")

        if report.status == "fail" and fail_on_mismatch:
            err_console.print(
                f"\nFIGURE MISMATCH: {figure_id} — computed {report.computed_value} != canonical {report.canonical_value}"
            )
            raise typer.Exit(code=1)

    except CanonValidationError as e:
        err_console.print(f"Canon validation failed (hard-stop): {e}")
        raise typer.Exit(code=1)
    except WoodwardError as e:
        err_console.print(f"Woodward error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"Unexpected error: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# db commands
# ---------------------------------------------------------------------------

@db_app.command("migrate")
def db_migrate() -> None:
    """
    Run all pending database migrations for ledger.db, records.db, and comms.db.
    """
    configure_logging()
    settings = get_settings()

    from src.services.db_migrator import DbMigrator

    migrator = DbMigrator()
    db_root = settings.db_path_obj
    # Migrations are in db/migrations/ relative to the project root
    # Detect project root as parent of db_path
    project_root = db_root.parent if db_root.name == "db" else Path.cwd()
    migrations_root = project_root / "db" / "migrations"

    if not migrations_root.exists():
        # Try relative to current working directory
        migrations_root = Path("db") / "migrations"

    console.print(f"[bold]Running DB migrations[/bold]")
    console.print(f"  DB Root:         {db_root}")
    console.print(f"  Migrations Root: {migrations_root}")

    try:
        results = asyncio.run(migrator.migrate_all(db_root, migrations_root))
        for db_name, applied in results.items():
            if applied:
                console.print(
                    f"  [green]{db_name}[/green]: Applied {len(applied)} migration(s) — {applied}"
                )
            else:
                console.print(f"  [dim]{db_name}[/dim]: Up to date")
        console.print("[bold green]Migration complete.[/bold green]")
    except Exception as e:
        err_console.print(f"Migration failed: {e}")
        raise typer.Exit(code=1)


@db_app.command("status")
def db_status() -> None:
    """
    Show table counts for all three databases.
    """
    configure_logging()
    settings = get_settings()

    from src.repositories.comms_repo import CommsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.repositories.records_repo import RecordsRepo

    async def _get_all_counts() -> dict:
        counts: dict = {}

        if settings.ledger_db_path.exists():
            try:
                ledger = LedgerRepo(settings.ledger_db_path)
                counts["ledger.db"] = await ledger.get_table_counts()
            except Exception as e:
                counts["ledger.db"] = {"error": str(e)}
        else:
            counts["ledger.db"] = {"status": "not initialized"}

        if settings.records_db_path.exists():
            try:
                records = RecordsRepo(settings.records_db_path)
                counts["records.db"] = await records.get_table_counts()
            except Exception as e:
                counts["records.db"] = {"error": str(e)}
        else:
            counts["records.db"] = {"status": "not initialized"}

        if settings.comms_db_path.exists():
            try:
                comms = CommsRepo(settings.comms_db_path)
                counts["comms.db"] = await comms.get_table_counts()
            except Exception as e:
                counts["comms.db"] = {"error": str(e)}
        else:
            counts["comms.db"] = {"status": "not initialized"}

        return counts

    all_counts = asyncio.run(_get_all_counts())

    for db_name, table_counts in all_counts.items():
        console.print(f"\n[bold]{db_name}[/bold]")
        if isinstance(table_counts, dict):
            if "status" in table_counts:
                console.print(f"  {table_counts['status']}")
            elif "error" in table_counts:
                console.print(f"  [red]Error: {table_counts['error']}[/red]")
            else:
                table = Table(show_header=True, header_style="bold")
                table.add_column("Table")
                table.add_column("Rows", justify="right")
                for tname, count in sorted(table_counts.items()):
                    table.add_row(tname, str(count) if count >= 0 else "error")
                console.print(table)


# ---------------------------------------------------------------------------
# bridge commands
# ---------------------------------------------------------------------------

@bridge_app.command("export")
def bridge_export(
    article: Optional[str] = typer.Option(None, "--article", "-a", help="Filter by article ID"),
    section: Optional[str] = typer.Option(None, "--section", "-s", help="Filter by section ID"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if not provided)"),
) -> None:
    """
    Generate a paste-ready markdown handoff packet from current canonical state.
    """
    configure_logging()
    settings = get_settings()

    if run_id is None:
        run_id = f"export_{uuid.uuid4().hex[:8]}"

    from src.bridge.export_handoff import export_handoff

    try:
        packet = asyncio.run(
            export_handoff(
                settings=settings,
                article_id=article,
                section_id=section,
                run_id=run_id,
            )
        )
        console.print(packet)
        console.print(
            f"\n[dim]Written to: {settings.runs_path_obj / run_id}[/dim]",
            highlight=False,
        )
    except WoodwardError as e:
        err_console.print(f"Export failed: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"Unexpected error: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# reply commands (Phase 6)
# ---------------------------------------------------------------------------

@reply_app.command("plan")
def reply_plan(
    article: str = typer.Option(..., "--article", "-a", help="Article ID"),
) -> None:
    """
    Show right-of-reply requirements for an article.
    Lists all claims that need a response before publication, with blocking status.
    """
    configure_logging()
    settings = get_settings()

    from src.repositories.comms_repo import CommsRepo
    from src.repositories.records_repo import RecordsRepo
    from src.services.reply_planner import ReplyPlanner

    async def _run() -> None:
        records = RecordsRepo(settings.records_db_path)
        comms = CommsRepo(settings.comms_db_path)
        planner = ReplyPlanner()

        requirements = await planner.get_requirements(article, records, comms)

        if not requirements:
            console.print(f"[green]No right-of-reply requirements for article '{article}'.[/green]")
            return

        console.print(f"\n[bold]Right-of-Reply Requirements — article: {article}[/bold]")
        console.print(planner.format_summary(requirements))

    try:
        asyncio.run(_run())
    except Exception as e:
        err_console.print(f"reply plan failed: {e}")
        raise typer.Exit(code=1)


@reply_app.command("build")
def reply_build(
    article: str = typer.Option(..., "--article", "-a", help="Article ID"),
    recipient: str = typer.Option(..., "--recipient", "-r", help="Recipient ID"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if not provided)"),
) -> None:
    """
    Build a right-of-reply outreach packet for a specific recipient.
    Writes a Markdown letter to runs/{run_id}/reply_packet_{recipient_id}.md.
    """
    configure_logging()
    settings = get_settings()

    if run_id is None:
        run_id = f"reply_{uuid.uuid4().hex[:8]}"

    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.comms_repo import CommsRepo
    from src.repositories.records_repo import RecordsRepo
    from src.workflows.build_reply_packet import build_reply_packet

    async def _run() -> None:
        canon_repo = CanonicalRepo(settings.canonical_path_obj)
        canon = canon_repo.load_manifest()
        records = RecordsRepo(settings.records_db_path)
        comms = CommsRepo(settings.comms_db_path)

        result = await build_reply_packet(
            article_id=article,
            recipient_id=recipient,
            run_id=run_id,
            settings=settings,
            records=records,
            comms=comms,
            canon=canon,
        )

        console.print(f"\n[bold]Reply Packet Built[/bold]")
        console.print(f"  Article:      {result.article_id}")
        console.print(f"  Recipient:    {result.recipient_name} ({result.recipient_id})")
        console.print(f"  Questions:    {len(result.questions)}")
        console.print(f"  Claims:       {len(result.affected_claim_ids)}")
        console.print(f"  Blocking:     {'YES' if result.publication_blocking else 'no'}")
        console.print(f"  Deadline:     {result.deadline_recommendation}")
        console.print(f"\n[dim]Packet: {settings.runs_path_obj / run_id}/reply_packet_{recipient}.md[/dim]")
        console.print("\n--- Packet Preview ---\n")
        console.print(result.packet_markdown)

    try:
        asyncio.run(_run())
    except Exception as e:
        err_console.print(f"reply build failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# publish commands (Phase 6)
# ---------------------------------------------------------------------------

@publish_app.command("check")
def publish_check(
    article: str = typer.Option(..., "--article", "-a", help="Article ID"),
    canon_hash: Optional[str] = typer.Option(None, help="Canon hash for this run"),
) -> None:
    """
    Run the publication gate for an article.
    Checks all five conditions: blocked claims, publication blocks,
    right-of-reply, locked figures, adversarial review.
    Exits with code 1 if gate fails.
    """
    configure_logging()
    settings = get_settings()

    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.comms_repo import CommsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.repositories.records_repo import RecordsRepo
    from src.services.publication_gate import PublicationGate

    async def _run() -> None:
        canon_repo = CanonicalRepo(settings.canonical_path_obj)
        canon = canon_repo.load_manifest()
        records = RecordsRepo(settings.records_db_path)
        comms = CommsRepo(settings.comms_db_path)
        ledger = LedgerRepo(settings.ledger_db_path)

        gate = PublicationGate()
        result = await gate.check(
            article_id=article,
            records=records,
            comms=comms,
            ledger=ledger,
            canon=canon,
            canon_hash=canon_hash or "",
        )

        status_color = "green" if result.passed else "red"
        status_text = "PASS" if result.passed else "FAIL"

        console.print(f"\n[bold]Publication Gate — article: {article}[/bold]")
        console.print(f"  Status:              [{status_color}]{status_text}[/{status_color}]")
        console.print(f"  Blocked claims:      {result.blocked_claim_count}")
        console.print(f"  Unresolved RoR:      {result.unresolved_ror_count}")
        console.print(f"  Unlocked figures:    {result.unlocked_figure_count}")
        console.print(f"  Review blockers:     {result.review_blocker_count}")
        console.print(f"  Canon hash:          {result.canon_hash or '(none)'}")
        console.print(f"  Timestamp:           {result.timestamp}")

        if result.failure_reasons:
            console.print("\n[bold red]Failure reasons:[/bold red]")
            for reason in result.failure_reasons:
                console.print(f"  - {reason}")

        if not result.passed:
            raise typer.Exit(code=1)

    try:
        asyncio.run(_run())
    except typer.Exit:
        raise
    except Exception as e:
        err_console.print(f"publish check failed: {e}")
        raise typer.Exit(code=1)


@publish_app.command("assemble")
def publish_assemble(
    article: str = typer.Option(..., "--article", "-a", help="Article ID"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if not provided)"),
) -> None:
    """
    Assemble the final article. Requires publication gate to pass.
    Writes both a clean public version and an internal scaffolded version.
    Hard-stops if gate fails.
    """
    configure_logging()
    settings = get_settings()

    if run_id is None:
        run_id = f"assemble_{uuid.uuid4().hex[:8]}"

    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.comms_repo import CommsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.repositories.records_repo import RecordsRepo
    from src.workflows.assemble_article import assemble_article

    async def _run() -> None:
        canon_repo = CanonicalRepo(settings.canonical_path_obj)
        canon = canon_repo.load_manifest()
        records = RecordsRepo(settings.records_db_path)
        comms = CommsRepo(settings.comms_db_path)
        ledger = LedgerRepo(settings.ledger_db_path)

        # Note: section_results are empty in CLI invocation without a prior draft run.
        # In a full pipeline, these would come from draft_section workflow results.
        console.print(
            f"[yellow]Note: assembling with no section drafts — gate will still check for blocked claims.[/yellow]"
        )

        result = await assemble_article(
            article_id=article,
            section_results=[],
            run_id=run_id,
            settings=settings,
            records=records,
            comms=comms,
            ledger=ledger,
            canon=canon,
        )

        console.print(f"\n[bold green]Article Assembly Complete[/bold green]")
        console.print(f"  Article:       {result.article_id}")
        console.print(f"  Sections:      {result.section_count}")
        console.print(f"  Word count:    {result.total_word_count}")
        console.print(f"  Gate:          {'PASS' if result.publication_gate_result and result.publication_gate_result.passed else 'PASS (no gate)'}")
        if result.artifact_path_final:
            console.print(f"\n  Final:         {result.artifact_path_final}")
        if result.artifact_path_scaffolded:
            console.print(f"  Scaffolded:    {result.artifact_path_scaffolded}")

    try:
        asyncio.run(_run())
    except WoodwardError as e:
        err_console.print(f"PUBLICATION BLOCKED: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"publish assemble failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# audit commands (Phase 7)
# ---------------------------------------------------------------------------

@audit_app.command("run")
def audit_run() -> None:
    """
    Run the full audit. Writes report to runs/audit_YYYYMMDD_HHMMSS.json.
    Exits with code 1 if any check fails.
    """
    configure_logging()

    from src.workflows.run_nightly_audit import print_summary, run_nightly_audit

    try:
        report = asyncio.run(run_nightly_audit())
        print_summary(report)

        if report.overall_status != "pass":
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        err_console.print(f"Audit failed: {e}")
        raise typer.Exit(code=1)


@audit_app.command("check")
def audit_check(
    check_name: str = typer.Argument(
        ...,
        help="Check name: figures, support_chains, banned_refs, orphaned_claims, missing_docs",
    ),
) -> None:
    """
    Run a single named audit check.
    Valid names: figures, support_chains, banned_refs, orphaned_claims, missing_docs.
    """
    configure_logging()
    settings = get_settings()

    from src.repositories.canonical_repo import CanonicalRepo
    from src.repositories.comms_repo import CommsRepo
    from src.repositories.ledger_repo import LedgerRepo
    from src.repositories.records_repo import RecordsRepo
    from src.services.audit_runner import AuditRunner

    VALID_CHECKS = {
        "figures": "verify_all_locked_figures",
        "support_chains": "verify_support_chains",
        "banned_refs": "detect_stale_banned_references",
        "orphaned_claims": "detect_orphaned_claims",
        "missing_docs": "detect_missing_source_documents",
    }

    if check_name not in VALID_CHECKS:
        err_console.print(
            f"Unknown check: '{check_name}'. "
            f"Valid options: {', '.join(VALID_CHECKS.keys())}"
        )
        raise typer.Exit(code=1)

    async def _run() -> None:
        canonical_repo = CanonicalRepo(settings.canonical_path_obj)
        ledger_repo = LedgerRepo(settings.ledger_db_path)
        records_repo = RecordsRepo(settings.records_db_path)
        comms_repo = CommsRepo(settings.comms_db_path)

        runner = AuditRunner(
            settings=settings,
            canonical_repo=canonical_repo,
            ledger_repo=ledger_repo,
            records_repo=records_repo,
            comms_repo=comms_repo,
        )

        method_name = VALID_CHECKS[check_name]
        method = getattr(runner, method_name)
        result = await method()

        status_color = "green" if result.status == "pass" else "red"
        status_text = "PASS" if result.status == "pass" else "FAIL"

        console.print(f"\n[bold]Audit Check: {result.name}[/bold]")
        console.print(f"  Status: [{status_color}]{status_text}[/{status_color}]")
        console.print(f"  Issues: {result.count}")

        for detail in result.details:
            console.print(f"    {detail}")

        if result.status != "pass":
            raise typer.Exit(code=1)

    try:
        asyncio.run(_run())
    except typer.Exit:
        raise
    except Exception as e:
        err_console.print(f"Audit check failed: {e}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# backup commands (Phase 7)
# ---------------------------------------------------------------------------

@backup_app.command("create")
def backup_create() -> None:
    """
    Create a backup of db/*.db, canonical/, and runs/.
    Writes to backups/backup_YYYYMMDD_HHMMSS/.
    """
    configure_logging()
    settings = get_settings()

    from src.services.backup_service import BackupService

    try:
        svc = BackupService(settings)
        backup_id = svc.create_backup()

        console.print(f"\n[bold green]Backup created:[/bold green] {backup_id}")
        console.print(f"  Location: {svc.backups_path / backup_id}")

        # Verify the backup we just created
        if svc.verify_backup(backup_id):
            console.print("  Verification: [green]PASS[/green]")
        else:
            console.print("  Verification: [red]FAIL[/red]")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        err_console.print(f"Backup failed: {e}")
        raise typer.Exit(code=1)


@backup_app.command("list")
def backup_list() -> None:
    """
    List all available backups with ID, timestamp, and size.
    """
    configure_logging()
    settings = get_settings()

    from src.services.backup_service import BackupService

    svc = BackupService(settings)
    backups = svc.list_backups()

    if not backups:
        console.print("[dim]No backups found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Backup ID")
    table.add_column("Timestamp")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Valid", justify="center")

    for b in backups:
        valid = svc.verify_backup(b["backup_id"])
        table.add_row(
            b["backup_id"],
            b["timestamp"],
            str(b["size_mb"]),
            "[green]yes[/green]" if valid else "[red]no[/red]",
        )

    console.print(table)


@backup_app.command("restore")
def backup_restore(
    backup_id: str = typer.Argument(..., help="Backup ID to restore (e.g. backup_20260312_080000)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """
    Restore db/*.db and canonical/ from a named backup.
    Does NOT restore runs/ (audit trail is preserved).
    """
    configure_logging()
    settings = get_settings()

    from src.services.backup_service import BackupService

    svc = BackupService(settings)

    # Verify backup exists
    if not svc.verify_backup(backup_id):
        err_console.print(f"Backup '{backup_id}' not found or failed verification.")
        raise typer.Exit(code=1)

    if not yes:
        console.print(
            f"\n[bold yellow]WARNING:[/bold yellow] This will overwrite:\n"
            f"  - db/*.db (ledger.db, records.db, comms.db)\n"
            f"  - canonical/ (all YAML files)\n"
            f"\n  Source: {svc.backups_path / backup_id}\n"
        )
        confirm = typer.confirm("Proceed with restore?")
        if not confirm:
            console.print("[dim]Restore cancelled.[/dim]")
            raise typer.Exit(code=0)

    try:
        svc.restore_backup(backup_id)
        console.print(f"\n[bold green]Restore complete from:[/bold green] {backup_id}")
    except Exception as e:
        err_console.print(f"Restore failed: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
