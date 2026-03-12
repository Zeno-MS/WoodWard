"""
src/bridge/compare_dual_run.py
compare_dual_run — compares two run artifacts side-by-side.
Used for parity testing: webapp vs v2, or two different v2 runs.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


def _load_run_artifact(runs_path: Path, run_id: str, filename: str) -> Optional[dict]:
    """Load a JSON artifact from a run directory."""
    artifact_path = runs_path / run_id / filename
    if not artifact_path.exists():
        return None
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load {artifact_path}: {e}")
        return None


def _load_all_run_artifacts(runs_path: Path, run_id: str) -> dict:
    """Load all known artifacts for a run."""
    artifacts: dict = {"run_id": run_id}

    # Try to load each known artifact type
    for artifact_name in [
        "verification_report.json",
        "canon_hash.json",
    ]:
        data = _load_run_artifact(runs_path, run_id, artifact_name)
        if data is not None:
            artifacts[artifact_name] = data

    # Check for handoff files
    run_dir = runs_path / run_id
    if run_dir.exists():
        handoff_files = list(run_dir.glob("handoff_*.md"))
        artifacts["handoff_files"] = [f.name for f in handoff_files]

    return artifacts


def compare_dual_run(
    run_id_a: str,
    run_id_b: str,
    runs_path: Path,
) -> str:
    """
    Compare two run artifacts and return a markdown comparison report.

    Compares:
    - Figure values and verification status
    - Canon hashes (to confirm same canonical state)
    - Pass/fail status
    - Available artifacts

    Returns a markdown string.
    """
    logger.info(f"compare_dual_run: A={run_id_a} B={run_id_b}")

    run_a = _load_all_run_artifacts(runs_path, run_id_a)
    run_b = _load_all_run_artifacts(runs_path, run_id_b)

    timestamp = datetime.utcnow().isoformat() + "Z"
    lines: list[str] = []

    lines.append("# Dual Run Comparison Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Run A:** `{run_id_a}`")
    lines.append(f"**Run B:** `{run_id_b}`")
    lines.append("")

    # --- Canon Hash Comparison ---
    lines.append("## Canon Hash Comparison")
    lines.append("")

    hash_a = run_a.get("canon_hash.json", {})
    hash_b = run_b.get("canon_hash.json", {})

    combined_a = hash_a.get("combined_hash", "NOT FOUND")
    combined_b = hash_b.get("combined_hash", "NOT FOUND")
    schema_a = hash_a.get("schema_version", "—")
    schema_b = hash_b.get("schema_version", "—")

    hash_match = combined_a == combined_b and combined_a != "NOT FOUND"
    lines.append(f"| Property | Run A | Run B | Match |")
    lines.append(f"|----------|-------|-------|-------|")
    lines.append(
        f"| Combined Hash | `{combined_a[:16]}...` | `{combined_b[:16]}...` | "
        f"{'MATCH' if hash_match else 'MISMATCH'} |"
    )
    lines.append(
        f"| Schema Version | `{schema_a}` | `{schema_b}` | "
        f"{'MATCH' if schema_a == schema_b else 'MISMATCH'} |"
    )
    lines.append("")

    if not hash_match and combined_a != "NOT FOUND" and combined_b != "NOT FOUND":
        lines.append(
            "> **WARNING:** Canon hashes differ between runs. "
            "These runs were not operating on the same canonical state. "
            "Comparison may not be meaningful."
        )
        lines.append("")

    # --- Figure Verification Comparison ---
    lines.append("## Figure Verification")
    lines.append("")

    report_a = run_a.get("verification_report.json", {})
    report_b = run_b.get("verification_report.json", {})

    if report_a or report_b:
        lines.append("| Property | Run A | Run B | Match |")
        lines.append("|----------|-------|-------|-------|")

        for key in ["figure_id", "status", "computed_value", "canonical_value", "derivation_id"]:
            val_a = str(report_a.get(key, "—"))
            val_b = str(report_b.get(key, "—"))
            match = "MATCH" if val_a == val_b else "MISMATCH"
            lines.append(f"| {key} | `{val_a}` | `{val_b}` | {match} |")

        lines.append("")

        # Status summary
        status_a = report_a.get("status", "NOT FOUND")
        status_b = report_b.get("status", "NOT FOUND")

        if status_a == "pass" and status_b == "pass":
            lines.append("**Result: BOTH RUNS PASSED**")
        elif status_a == status_b:
            lines.append(f"**Result: Both runs have status={status_a}**")
        else:
            lines.append(f"**Result: DIVERGENT — Run A={status_a}, Run B={status_b}**")
        lines.append("")
    else:
        lines.append("_No verification reports found for one or both runs._")
        lines.append("")

    # --- Artifacts Comparison ---
    lines.append("## Available Artifacts")
    lines.append("")
    lines.append("| Artifact | Run A | Run B |")
    lines.append("|----------|-------|-------|")

    all_artifacts = set(
        list(run_a.keys()) + list(run_b.keys())
    ) - {"run_id"}

    for artifact in sorted(all_artifacts):
        present_a = "YES" if artifact in run_a else "—"
        present_b = "YES" if artifact in run_b else "—"
        lines.append(f"| `{artifact}` | {present_a} | {present_b} |")
    lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")

    issues: list[str] = []
    if not hash_match and combined_a != "NOT FOUND" and combined_b != "NOT FOUND":
        issues.append("Canon hashes differ — runs were not on the same canonical state")
    if report_a.get("status") != report_b.get("status"):
        issues.append(
            f"Figure verification status differs: A={report_a.get('status')} B={report_b.get('status')}"
        )

    if not issues:
        lines.append("**No divergence detected between runs.**")
    else:
        lines.append("**Divergences detected:**")
        for issue in issues:
            lines.append(f"- {issue}")
    lines.append("")
    lines.append("---")
    lines.append("_Generated by Woodward Core v2 — compare_dual_run_")

    report_md = "\n".join(lines)

    # Write to the A run's directory
    output_path = runs_path / run_id_a / f"dual_run_compare_{run_id_b}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md, encoding="utf-8")
    logger.info(f"Comparison report written to {output_path}")

    return report_md
