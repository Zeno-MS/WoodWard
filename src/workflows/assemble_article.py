"""
src/workflows/assemble_article.py
assemble_article workflow — final article build.

Rules:
1. Run publication_gate.assert_passes() first — hard-stop if fails.
2. Assemble sections in order.
3. Strip all internal support IDs ([ctx:xxx], [claim:xxx]) from final output.
4. Output is clean Markdown journalism — NOT legal brief format.
5. Append a canonical figures table at the end (transparency).
6. Write runs/{run_id}/article_{article_id}_final.md (public clean version).
7. Write runs/{run_id}/article_{article_id}_with_scaffolding.md (internal version).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from schemas.canonical import CanonManifest
from src.core.exceptions import PublicationBlockedError
from src.repositories.comms_repo import CommsRepo
from src.repositories.ledger_repo import LedgerRepo
from src.repositories.records_repo import RecordsRepo
from src.services.publication_gate import PublicationGate, PublicationGateResult

logger = logging.getLogger(__name__)

# Patterns stripped from final public output
# Matches [ctx:xxx], [claim:xxx], [fig:xxx], [support:xxx]
_SCAFFOLDING_PATTERN = re.compile(
    r"\["
    r"(?:ctx|claim|fig|support)"
    r":"
    r"[^\]]*"
    r"\]",
    re.IGNORECASE,
)


@dataclass
class ArticleAssemblyResult:
    """
    Result from assemble_article.

    final_markdown: Clean public version — all internal scaffolding stripped.
    scaffolded_markdown: Internal version with support IDs intact.
    Both are written to runs/{run_id}/.
    """
    run_id: str
    article_id: str
    final_markdown: str = ""
    scaffolded_markdown: str = ""
    section_count: int = 0
    total_word_count: int = 0
    figures_table: str = ""
    publication_gate_result: Optional[PublicationGateResult] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    canon_hash: str = ""
    artifact_path_final: Optional[str] = None
    artifact_path_scaffolded: Optional[str] = None


async def assemble_article(
    article_id: str,
    section_results: list,   # list[DraftSectionResult]
    run_id: str,
    settings,                # WoodwardSettings
    records: RecordsRepo,
    comms: CommsRepo,
    ledger: LedgerRepo,
    canon: CanonManifest,
    canon_hash: str = "",
) -> ArticleAssemblyResult:
    """
    Assemble the final article from a list of DraftSectionResult objects.

    Steps:
    1. Assert publication gate passes (hard-stop on failure).
    2. Order sections by section_id.
    3. Concatenate draft content into scaffolded version.
    4. Build canonical figures table from locked_figures used across sections.
    5. Strip support scaffolding for final public version.
    6. Write both versions to runs/{run_id}/.
    7. Return ArticleAssemblyResult.
    """
    logger.info(
        f"assemble_article: article={article_id} run_id={run_id} "
        f"sections={len(section_results)}"
    )

    # ------------------------------------------------------------------
    # Step 1: Assert publication gate passes — hard-stop if fails
    # ------------------------------------------------------------------
    gate = PublicationGate()
    try:
        gate_result = await gate.check(
            article_id=article_id,
            records=records,
            comms=comms,
            ledger=ledger,
            canon=canon,
            draft_result=section_results,
            canon_hash=canon_hash,
        )
    except Exception as e:
        logger.error(f"assemble_article: gate check error: {e}")
        raise

    if not gate_result.passed:
        logger.error(
            f"assemble_article: gate FAIL for article='{article_id}' — "
            f"raising PublicationBlockedError"
        )
        raise PublicationBlockedError(
            article_id=article_id,
            reasons=gate_result.failure_reasons,
        )

    # ------------------------------------------------------------------
    # Step 2: Order sections by section_id
    # ------------------------------------------------------------------
    sorted_sections = sorted(
        section_results,
        key=lambda r: r.section_id if hasattr(r, "section_id") else "",
    )

    # ------------------------------------------------------------------
    # Step 3: Concatenate draft content (scaffolded version)
    # ------------------------------------------------------------------
    sections_content: list[str] = []
    all_figures_used: list[str] = []

    for sr in sorted_sections:
        if hasattr(sr, "draft") and sr.draft is not None:
            section_text = sr.draft.content or ""
            sections_content.append(section_text)
            # Collect figures used in this section
            if sr.draft.figures_used:
                all_figures_used.extend(sr.draft.figures_used)
        elif hasattr(sr, "draftable_claims") and sr.gate_passed:
            # Gate-only mode: no prose content
            sections_content.append(
                f"<!-- Section {getattr(sr, 'section_id', 'unknown')} — draft not yet generated -->"
            )

    scaffolded_body = "\n\n---\n\n".join(sections_content) if sections_content else ""

    # ------------------------------------------------------------------
    # Step 4: Build canonical figures table from locked_figures used
    # ------------------------------------------------------------------
    figures_used_unique = list(dict.fromkeys(all_figures_used))  # deduplicate, preserve order
    figures_table = build_figures_table(figures_used_unique, canon)

    # Assemble internal (scaffolded) markdown
    scaffolded_md_parts = []
    if scaffolded_body:
        scaffolded_md_parts.append(scaffolded_body)
    if figures_table:
        scaffolded_md_parts.append("\n\n---\n\n## Figures Used\n\n" + figures_table)

    scaffolded_markdown = "\n\n".join(scaffolded_md_parts).strip()

    # ------------------------------------------------------------------
    # Step 5: Strip support scaffolding for final public version
    # ------------------------------------------------------------------
    final_markdown_body = strip_scaffolding(scaffolded_body)
    final_md_parts = []
    if final_markdown_body:
        final_md_parts.append(final_markdown_body)
    if figures_table:
        final_md_parts.append("\n\n---\n\n## Figures Used\n\n" + figures_table)

    final_markdown = "\n\n".join(final_md_parts).strip()

    # Word count (final version)
    total_word_count = len(final_markdown.split())

    # ------------------------------------------------------------------
    # Step 6: Write both versions to runs/{run_id}/
    # ------------------------------------------------------------------
    runs_path = settings.runs_path_obj / run_id
    artifact_path_final: Optional[str] = None
    artifact_path_scaffolded: Optional[str] = None

    try:
        runs_path.mkdir(parents=True, exist_ok=True)

        final_file = runs_path / f"article_{article_id}_final.md"
        final_file.write_text(final_markdown, encoding="utf-8")
        artifact_path_final = str(final_file)
        logger.info(f"assemble_article: final article written to {final_file}")

        scaffolded_file = runs_path / f"article_{article_id}_with_scaffolding.md"
        scaffolded_file.write_text(scaffolded_markdown, encoding="utf-8")
        artifact_path_scaffolded = str(scaffolded_file)
        logger.info(
            f"assemble_article: scaffolded article written to {scaffolded_file}"
        )
    except Exception as e:
        logger.error(f"assemble_article: failed to write artifacts: {e}")

    # ------------------------------------------------------------------
    # Step 7: Return result
    # ------------------------------------------------------------------
    result = ArticleAssemblyResult(
        run_id=run_id,
        article_id=article_id,
        final_markdown=final_markdown,
        scaffolded_markdown=scaffolded_markdown,
        section_count=len(sorted_sections),
        total_word_count=total_word_count,
        figures_table=figures_table,
        publication_gate_result=gate_result,
        canon_hash=canon_hash,
        artifact_path_final=artifact_path_final,
        artifact_path_scaffolded=artifact_path_scaffolded,
    )

    logger.info(
        f"assemble_article: done — "
        f"article={article_id} sections={result.section_count} "
        f"words={total_word_count} gate=PASS"
    )
    return result


def strip_scaffolding(content: str) -> str:
    """
    Remove internal support markers from content.

    Patterns stripped:
    - [ctx:xxx]
    - [claim:xxx]
    - [fig:xxx]
    - [support:xxx]

    Uses regex — does not strip real prose content.
    Cleans up any trailing whitespace left by stripping inline markers.
    """
    if not content:
        return content
    stripped = _SCAFFOLDING_PATTERN.sub("", content)
    # Clean up multiple spaces left by inline marker removal
    stripped = re.sub(r"  +", " ", stripped)
    # Clean up spaces before punctuation (e.g. "fact . Next" -> "fact. Next")
    stripped = re.sub(r" ([.,;:!?])", r"\1", stripped)
    return stripped.strip()


def build_figures_table(figures_used: list[str], canon: CanonManifest) -> str:
    """
    Build a Markdown table of figures used in the article.

    Columns: Figure | Value | Source | Status

    Only includes figures actually referenced in the article sections.
    Figures not found in canon are noted as 'unknown'.
    """
    if not figures_used:
        return ""

    rows: list[str] = []
    header = "| Figure | Value | Source | Status |"
    separator = "|--------|-------|--------|--------|"
    rows.append(header)
    rows.append(separator)

    for fig_id in figures_used:
        fig = canon.get_figure(fig_id)
        if fig:
            display_label = fig.display_label or fig_id
            display_value = fig.display_value or str(fig.value)
            source = fig.source_of_truth or "—"
            status = fig.status or "unknown"
            rows.append(
                f"| {display_label} | {display_value} | {source} | {status} |"
            )
        else:
            rows.append(f"| {fig_id} | — | — | not in canon |")

    return "\n".join(rows)
