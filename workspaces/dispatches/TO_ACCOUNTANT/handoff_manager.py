#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MODEL_PROFILES = {
    "Claude Opus 4.6": {
        "context_tokens": 1000000,
        "multiplier": 3,
        "notes": "Approximate; 1M beta tier, tool-specific limits may be lower."
    },
    "Claude Opus 4.6 (fast)": {
        "context_tokens": 200000,
        "multiplier": 3,
        "notes": "Fast tier often uses reduced context."
    },
    "Claude Sonnet 4.5": {
        "context_tokens": 200000,
        "multiplier": None,
        "notes": "Approximate API/tooling limit."
    },
    "Claude Haiku 4.5": {
        "context_tokens": 200000,
        "multiplier": None,
        "notes": "Approximate API/tooling limit."
    },
    "Claude Opus 4.1": {
        "context_tokens": 200000,
        "multiplier": 10,
        "notes": "Legacy expensive tier in some pricing tables."
    },
    "Gemini 3 Pro": {
        "context_tokens": 1000000,
        "multiplier": None,
        "notes": "Approximate; tool implementations may cap lower."
    },
    "Gemini 2.5 Pro": {
        "context_tokens": 2000000,
        "multiplier": None,
        "notes": "Approximate upper bound in long-context tiers."
    },
    "Gemini 3 Flash": {
        "context_tokens": 1000000,
        "multiplier": None,
        "notes": "Approximate; optimized for long-context throughput."
    },
    "GPT-5.3-Codex": {
        "context_tokens": 272000,
        "multiplier": None,
        "notes": "Approximate Copilot input context; output budget is separate."
    },
    "GPT-5.3-Codex-Spark": {
        "context_tokens": 128000,
        "multiplier": None,
        "notes": "Fast tier with smaller context window."
    },
    "GPT-5.2": {
        "context_tokens": 128000,
        "multiplier": None,
        "notes": "Approximate standard context."
    },
    "GPT-5.1": {
        "context_tokens": 128000,
        "multiplier": None,
        "notes": "Approximate standard context."
    },
    "GPT-5.1-Codex": {
        "context_tokens": 128000,
        "multiplier": None,
        "notes": "Approximate standard context."
    },
    "GPT-4o": {
        "context_tokens": 128000,
        "multiplier": 0,
        "notes": "Often low-cost in bundled dev-tool pricing."
    },
    "GPT-4.1": {
        "context_tokens": 128000,
        "multiplier": None,
        "notes": "Approximate previous generation context."
    },
    "Raptor Mini": {
        "context_tokens": 264000,
        "multiplier": 0,
        "notes": "Approximate IDE-tuned code model context."
    },
    "Grok Code Fast 1": {
        "context_tokens": 128000,
        "multiplier": None,
        "notes": "Estimated based on public beta specs."
    }
}


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_unique(items: list, new_items: list) -> list:
    for value in new_items:
        if value and value not in items:
            items.append(value)
    return items


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def context_level(percent_used: float, warn: float, critical: float) -> str:
    if percent_used >= critical:
        return "CRITICAL"
    if percent_used >= warn:
        return "WARNING"
    return "OK"


def infer_tokens_total(cw: dict, state: dict) -> int | None:
    explicit_total = cw.get("tokens_total")
    if explicit_total is not None:
        return explicit_total
    active_model = state.get("active_model")
    profiles = state.get("model_profiles", {})
    if active_model and active_model in profiles:
        return profiles[active_model].get("context_tokens")
    return None


def immediate_instruction(level: str) -> list[str]:
    if level == "CRITICAL":
        return [
            "Stop adding new analysis in this chat.",
            "Run one final checkpoint update command.",
            "Start a fresh chat using only HANDOFF_peer_spending_gap.md."
        ]
    if level == "WARNING":
        return [
            "Finish only the current micro-task.",
            "Run a checkpoint update now and trim noisy details into notes/files.",
            "Start a new chat before beginning another major task."
        ]
    return [
        "Continue current work.",
        "Re-check context after each major work block or after 3-5 tool calls."
    ]


def trigger_plan(tokens_used: int | None, tokens_total: int | None, warn: float, critical: float) -> list[str]:
    warn_tokens = int(tokens_total * warn / 100) if tokens_total is not None else None
    critical_tokens = int(tokens_total * critical / 100) if tokens_total is not None else None
    lines = []

    if warn_tokens is None or critical_tokens is None:
        lines.append("Set tokens total (or active model) so warning/critical trigger points can be computed.")
        lines.append("Use: --set-model \"GPT-5.3-Codex\" or provide --tokens-total explicitly.")
        return lines

    lines.append(f"At WARNING ({warn:.0f}% = {warn_tokens} tokens): checkpoint + summarize + prepare handoff.")
    lines.append(f"At CRITICAL ({critical:.0f}% = {critical_tokens} tokens): stop and immediately start new chat from handoff.")

    if tokens_used is None:
        lines.append("Current tokens used unknown; pass --tokens-used to get exact 'next trigger' guidance.")
        return lines

    if tokens_used < warn_tokens:
        lines.append(f"Next trigger: WARNING in {warn_tokens - tokens_used} tokens.")
    elif tokens_used < critical_tokens:
        lines.append(f"Next trigger: CRITICAL in {critical_tokens - tokens_used} tokens.")
    else:
        lines.append("You are at/over CRITICAL; switch chats now.")
    return lines


def render_handoff(state: dict) -> str:
    cw = state["context_window"]
    percent = cw.get("percent_used")
    warn = cw.get("warn_percent", 70)
    critical = cw.get("critical_percent", 85)
    profiles = state.get("model_profiles", {})
    active_model = state.get("active_model")
    active_profile = profiles.get(active_model) if active_model else None

    inferred_total = infer_tokens_total(cw, state)
    tokens_used = cw.get("tokens_used")

    if tokens_used is not None and inferred_total is not None:
        percent = round((tokens_used / inferred_total) * 100, 2)
        cw["percent_used"] = percent
        cw["tokens_total"] = inferred_total

    if percent is None:
        cw_line = "- Status: **UNKNOWN** (no context usage input yet)"
        level = "UNKNOWN"
        cw_actions = ["Capture usage with --tokens-used (and optionally --tokens-total)."]
    else:
        level = context_level(float(percent), float(warn), float(critical))
        tokens_total = inferred_total
        checked = cw.get("last_checked") or "(not set)"
        token_text = ""
        if tokens_used is not None and tokens_total is not None:
            token_text = f" | {tokens_used}/{tokens_total} tokens"
        cw_line = f"- Status: **{level}** at **{percent:.1f}%**{token_text} (checked: {checked})"
        cw_actions = immediate_instruction(level)

    plan_lines = trigger_plan(tokens_used, inferred_total, float(warn), float(critical))

    lines = []
    lines.append(f"# New Chat Handoff — {state['project_name']}")
    lines.append("")
    lines.append("## Objective")
    lines.append(state["objective"])
    lines.append("")
    lines.append("## Targets")
    for target in state["targets"]:
        lines.append(f"- {target}")
    lines.append("")
    lines.append("## CSV Output")
    lines.append("```csv")
    lines.extend(state["csv_template"])
    lines.append("```")
    lines.append("")
    lines.append("## Current Status")
    for item in state["status_summary"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Context Window Watch")
    lines.append(cw_line)
    lines.append(f"- Thresholds: warning at {warn}% | critical at {critical}%")
    lines.append("- Immediate instruction:")
    for action in cw_actions:
        lines.append(f"  - {action}")
    lines.append("- Trigger plan:")
    for action in plan_lines:
        lines.append(f"  - {action}")
    lines.append("")
    lines.append("## Model Awareness")
    if active_model:
        lines.append(f"- Active model: **{active_model}**")
        if active_profile:
            lines.append(f"- Approx context window: **{active_profile.get('context_tokens')} tokens**")
            mult = active_profile.get("multiplier")
            if mult is not None:
                lines.append(f"- Cost multiplier hint: **{mult}x**")
            notes = active_profile.get("notes")
            if notes:
                lines.append(f"- Notes: {notes}")
    else:
        lines.append("- Active model not set. Use --set-model to enable model-aware triggers.")
    lines.append(f"- Tracked models: {len(profiles)}")
    lines.append("")
    lines.append("## Key Sources")
    for src in state["sources"]:
        lines.append(f"- {src}")
    lines.append("")
    lines.append("## Next Actions")
    for action in state["next_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Blockers")
    for blocker in state["blockers"]:
        lines.append(f"- {blocker}")
    lines.append("")
    if state.get("notes"):
        lines.append("## Notes")
        for note in state["notes"][-10:]:
            lines.append(f"- {note}")
        lines.append("")
    lines.append("## Workspace Artifacts")
    for artifact in state["artifacts"]:
        lines.append(f"- {artifact}")
    lines.append("")
    lines.append(f"_Generated: {now_utc()}_")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update handoff state and regenerate handoff markdown.")
    parser.add_argument("--state-file", default="handoff_state_peer_spending_gap.json")
    parser.add_argument("--handoff-file", default="HANDOFF_peer_spending_gap.md")

    parser.add_argument("--set-status", action="append", default=[], help="Append a status bullet.")
    parser.add_argument("--add-source", action="append", default=[])
    parser.add_argument("--add-next", action="append", default=[])
    parser.add_argument("--add-blocker", action="append", default=[])
    parser.add_argument("--add-note", action="append", default=[])
    parser.add_argument("--add-artifact", action="append", default=[])

    parser.add_argument("--tokens-used", type=int)
    parser.add_argument("--tokens-total", type=int)
    parser.add_argument("--percent-used", type=float)
    parser.add_argument("--warn-percent", type=float)
    parser.add_argument("--critical-percent", type=float)
    parser.add_argument("--checked-at")
    parser.add_argument("--set-model", help="Set active model name from model_profiles.")
    parser.add_argument("--list-models", action="store_true", help="Print available model profiles and exit.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when context level meets strict threshold.")
    parser.add_argument(
        "--strict-level",
        choices=["warning", "critical"],
        default="warning",
        help="Strict threshold: warning (default) or critical."
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    state_path = Path(args.state_file).resolve()
    handoff_path = Path(args.handoff_file).resolve()

    state = load_state(state_path)

    state.setdefault("model_profiles", DEFAULT_MODEL_PROFILES)
    state.setdefault("active_model", "GPT-5.3-Codex")

    if args.list_models:
        for name, meta in state["model_profiles"].items():
            context_tokens = meta.get("context_tokens")
            multiplier = meta.get("multiplier")
            mult_text = f" | multiplier={multiplier}x" if multiplier is not None else ""
            print(f"- {name}: {context_tokens} tokens{mult_text}")
        return

    model_was_set = False
    if args.set_model:
        if args.set_model not in state["model_profiles"]:
            known = ", ".join(state["model_profiles"].keys())
            raise SystemExit(f"Unknown model '{args.set_model}'. Known models: {known}")
        state["active_model"] = args.set_model
        model_was_set = True

    state["status_summary"] = add_unique(state.get("status_summary", []), args.set_status)
    state["sources"] = add_unique(state.get("sources", []), args.add_source)
    state["next_actions"] = add_unique(state.get("next_actions", []), args.add_next)
    state["blockers"] = add_unique(state.get("blockers", []), args.add_blocker)
    state["artifacts"] = add_unique(state.get("artifacts", []), args.add_artifact)

    if args.add_note:
        notes = state.get("notes", [])
        for note in args.add_note:
            if note:
                notes.append(f"{now_utc()} | {note}")
        state["notes"] = notes[-100:]

    cw = state.get("context_window", {})
    if args.warn_percent is not None:
        cw["warn_percent"] = args.warn_percent
    if args.critical_percent is not None:
        cw["critical_percent"] = args.critical_percent

    if args.percent_used is not None:
        cw["percent_used"] = float(args.percent_used)
    elif args.tokens_used is not None and args.tokens_total:
        cw["percent_used"] = round((args.tokens_used / args.tokens_total) * 100, 2)

    if args.tokens_used is not None:
        cw["tokens_used"] = args.tokens_used
    if args.tokens_total is not None:
        cw["tokens_total"] = args.tokens_total
    elif model_was_set:
        active_model = state.get("active_model")
        model_meta = state.get("model_profiles", {}).get(active_model, {})
        inferred = model_meta.get("context_tokens")
        if inferred is not None:
            cw["tokens_total"] = inferred
    elif cw.get("tokens_total") is None:
        inferred = infer_tokens_total(cw, state)
        if inferred is not None:
            cw["tokens_total"] = inferred

    if args.checked_at:
        cw["last_checked"] = args.checked_at
    elif args.percent_used is not None or (args.tokens_used is not None and args.tokens_total is not None):
        cw["last_checked"] = now_utc()
    elif args.tokens_used is not None:
        cw["last_checked"] = now_utc()

    if cw.get("tokens_used") is not None and cw.get("tokens_total"):
        cw["percent_used"] = round((cw["tokens_used"] / cw["tokens_total"]) * 100, 2)

    state["context_window"] = cw

    save_state(state_path, state)
    handoff_path.write_text(render_handoff(state), encoding="utf-8")

    percent = state["context_window"].get("percent_used")
    if percent is None:
        level = "UNKNOWN"
    else:
        level = context_level(float(percent), float(cw.get("warn_percent", 70)), float(cw.get("critical_percent", 85)))

    print(f"Updated state: {state_path}")
    print(f"Regenerated handoff: {handoff_path}")
    print(f"Context status: {level} ({percent if percent is not None else 'n/a'}%)")
    if state.get("active_model"):
        print(f"Active model: {state['active_model']}")

    if args.strict:
        if args.strict_level == "warning" and level in {"WARNING", "CRITICAL"}:
            print("Strict mode triggered at warning threshold.")
            sys.exit(2)
        if args.strict_level == "critical" and level == "CRITICAL":
            print("Strict mode triggered at critical threshold.")
            sys.exit(2)


if __name__ == "__main__":
    main()
