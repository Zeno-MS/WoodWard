# Handoff Workflow (Context-Aware)

Use this each session so new chats inherit clean project state.

## Files
- `handoff_state_peer_spending_gap.json` → structured source of truth
- `HANDOFF_peer_spending_gap.md` → generated handoff for new chats
- `handoff_manager.py` → updater/generator utility

## Model-Aware Setup (run once or when switching models)
```bash
python3 handoff_manager.py --list-models
python3 handoff_manager.py --set-model "GPT-5.3-Codex"
```

If `--tokens-total` is omitted, the manager uses the active model's context window automatically.

## Quick Start
From `TO_ACCOUNTANT/` run:

```bash
python3 handoff_manager.py \
  --set-model "GPT-5.3-Codex" \
  --tokens-used 75000 \
  --add-note "Session checkpoint after source review"
```

This will:
1. Update context usage in the JSON state.
2. Recompute warning/critical status using active model window.
3. Regenerate `HANDOFF_peer_spending_gap.md`.

## Typical Session Commands

### 1) Add progress + context check
```bash
python3 handoff_manager.py \
  --set-status "Validated Tacoma budget page section mapping" \
  --add-next "Extract Object 7 totals from Tacoma 2023-24 PDF" \
  --tokens-used 82000
```

### 2) Add blocker/source
```bash
python3 handoff_manager.py \
  --add-blocker "Drive PDF requires authenticated browser session" \
  --add-source "https://example-link"
```

### 3) Adjust thresholds
```bash
python3 handoff_manager.py --warn-percent 70 --critical-percent 85
```

## New Chat Protocol
1. Run `handoff_manager.py` with current token usage.
2. Open `HANDOFF_peer_spending_gap.md`.
3. Paste that file into a new chat as the only history payload.
4. Continue work from `Next Actions`.

## Exactly What To Do And When
- **Below Warning**: continue work; run checkpoint update every major block or every 3–5 tool calls.
- **At/Above Warning**: finish only current micro-task, checkpoint now, compress notes, prepare handoff.
- **At/Above Critical**: stop work in current chat, run final checkpoint, immediately start fresh chat from handoff.

Example checkpoint command:
```bash
python3 handoff_manager.py --tokens-used <CURRENT_USED> --add-note "Checkpoint"
```

## Context Policy
- **Warning**: >= 70%
- **Critical**: >= 85%
- At **Critical**, immediately start a fresh chat using generated handoff.
