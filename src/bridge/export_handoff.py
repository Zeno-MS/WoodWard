"""
src/bridge/export_handoff.py
export_handoff — assembles a paste-ready markdown handoff packet
for the current investigation state.

Designed to replace the webapp-as-memory pattern.
Output is deterministic and reproducible from canonical state + databases.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from schemas.canonical import CanonManifest
from src.core.logging import get_logger
from src.core.settings import WoodwardSettings
from src.repositories.canonical_repo import CanonicalRepo
from src.repositories.comms_repo import CommsRepo
from src.repositories.records_repo import RecordsRepo
from src.services.canonical_lock_service import CanonicalLockService

logger = get_logger(__name__)


async def export_handoff(
    settings: WoodwardSettings,
    article_id: Optional[str] = None,
    section_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> str:
    """
    Assemble a paste-ready markdown handoff packet.

    Includes:
    - Current locked figures from canon
    - Open/blocked claims (filtered by article_id if provided)
    - Open right-of-reply threads and response windows
    - Active publication blocks
    - Canon hash for provenance

    Returns the markdown string and writes to runs/{run_id}/handoff_{article_id or 'all'}.md
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]

    timestamp = datetime.utcnow().isoformat() + "Z"
    label = article_id or "all"

    logger.info(f"export_handoff: run_id={run_id} article_id={article_id}")

    canonical_path = settings.canonical_path_obj

    # Load canon
    lock_service = CanonicalLockService()
    lock_service.validate_canon(canonical_path)
    canon_hash = lock_service.emit_canon_hash(canonical_path, settings.runs_path_obj, run_id)

    repo = CanonicalRepo(canonical_path)
    canon = repo.load_all()

    # Build packet sections
    sections: list[str] = []

    # --- Header ---
    sections.append(f"# Woodward Handoff Packet")
    sections.append(f"\n**Generated:** {timestamp}")
    sections.append(f"**Run ID:** `{run_id}`")
    sections.append(f"**Investigation:** `{settings.investigation}`")
    sections.append(f"**Canon Hash:** `{canon_hash.combined_hash[:24]}...`")
    if article_id:
        sections.append(f"**Article Filter:** `{article_id}`")
    if section_id:
        sections.append(f"**Section Filter:** `{section_id}`")
    sections.append("")

    # --- Locked Figures ---
    sections.append("## Locked Figures")
    sections.append("")

    locked_figures = [f for f in canon.figures if f.status == "locked"]
    if locked_figures:
        sections.append("| Figure ID | Label | Value | Fiscal Year | Source |")
        sections.append("|-----------|-------|-------|-------------|--------|")
        for fig in locked_figures:
            fy = fig.fiscal_year or fig.date_context or "—"
            sections.append(
                f"| `{fig.figure_id}` | {fig.display_label} | "
                f"**{fig.display_value}** | {fy} | {fig.source_of_truth} |"
            )
    else:
        sections.append("_No locked figures found._")
    sections.append("")

    # --- Claims Status ---
    if article_id:
        claims = canon.get_claims_for_article(article_id)
    else:
        claims = canon.claims

    if claims:
        sections.append("## Claims Registry")
        sections.append("")
        sections.append(
            "| Claim ID | Status | Public Citable | Right of Reply | Text |"
        )
        sections.append("|----------|--------|---------------|---------------|------|")
        for claim in claims:
            ror = "YES" if claim.right_of_reply_required else "no"
            pc = "YES" if claim.public_citable else "no"
            text_short = claim.text[:80] + "..." if len(claim.text) > 80 else claim.text
            sections.append(
                f"| `{claim.claim_id}` | `{claim.status}` | {pc} | {ror} | {text_short} |"
            )
        sections.append("")

        # Blocked claims summary
        blocked = [c for c in claims if c.status == "blocked"]
        if blocked:
            sections.append("### Blocked Claims (require resolution before publication)")
            sections.append("")
            for claim in blocked:
                sections.append(f"**`{claim.claim_id}`** — {claim.text}")
                if claim.right_of_reply_required:
                    sections.append(
                        "  - Requires right-of-reply response before publishing"
                    )
                if claim.notes:
                    sections.append(f"  - Notes: {claim.notes}")
                sections.append("")

    # --- Right of Reply Threads (from comms.db if available) ---
    sections.append("## Right-of-Reply / Outreach Status")
    sections.append("")

    comms_db_path = settings.comms_db_path
    if comms_db_path.exists():
        try:
            comms_repo = CommsRepo(comms_db_path)
            open_windows = await comms_repo.get_publication_blocking_windows()
            open_threads = await comms_repo.get_open_threads()

            if article_id:
                article_deps = await comms_repo.get_unresolved_dependencies(article_id)
            else:
                article_deps = []

            if open_windows:
                sections.append(
                    f"**Publication-blocking response windows: {len(open_windows)}**"
                )
                sections.append("")
                for window in open_windows:
                    deadline = window.deadline or "no deadline set"
                    sections.append(f"- Thread `{window.thread_id}` — deadline: {deadline}")
                sections.append("")

            if open_threads:
                sections.append(f"**Open outreach threads: {len(open_threads)}**")
                for thread in open_threads:
                    subject = thread.subject or "(no subject)"
                    sections.append(f"- `{thread.thread_id}`: {subject} — status: {thread.status}")
                sections.append("")

            if article_deps:
                sections.append(f"**Unresolved article dependencies: {len(article_deps)}**")
                for dep in article_deps:
                    sections.append(
                        f"- `{dep.dep_id}` type={dep.dependency_type} claim={dep.claim_id}"
                    )
                sections.append("")

            if not open_windows and not open_threads:
                sections.append("_No open outreach threads or blocking windows._")
                sections.append("")

        except Exception as e:
            sections.append(f"_comms.db not available or empty: {e}_")
            sections.append("")
    else:
        sections.append("_comms.db not yet initialized. Run `woodward db migrate` first._")
        sections.append("")

    # --- Publication Blocks (from records.db if available) ---
    records_db_path = settings.records_db_path
    if records_db_path.exists() and article_id:
        try:
            records_repo = RecordsRepo(records_db_path)
            active_blocks = await records_repo.get_active_blocks(article_id)
            if active_blocks:
                sections.append("## Active Publication Blocks")
                sections.append("")
                for block in active_blocks:
                    sections.append(
                        f"- **Block `{block.block_id}`**: claim `{block.claim_id}` — {block.reason}"
                    )
                sections.append("")
        except Exception:
            pass

    # --- Banned Claims Reminder ---
    sections.append("## Banned Claim Patterns (DO NOT PUBLISH)")
    sections.append("")
    for ban in canon.banned_claims:
        sections.append(f"- **[{ban.ban_id}]** {ban.text_pattern}")
    sections.append("")

    # --- Footer ---
    sections.append("---")
    sections.append(
        f"_Woodward Core v2 — This packet was generated deterministically from "
        f"canonical state + databases. It is paste-ready for editorial handoff._"
    )

    packet = "\n".join(sections)

    # Write to runs directory
    runs_path = settings.runs_path_obj
    run_dir = runs_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output_file = run_dir / f"handoff_{label}.md"
    output_file.write_text(packet, encoding="utf-8")
    logger.info(f"Handoff written to {output_file}")

    return packet
