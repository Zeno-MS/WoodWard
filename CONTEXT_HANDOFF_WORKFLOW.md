# Context Handoff Workflow

## Commands
- List models: `python3 /Users/chrisknight/Projects/scripts/context_handoff_manager.py --list-models`
- Initialize project: `python3 /Users/chrisknight/Projects/scripts/context_handoff_manager.py --project-dir . --init`
- Set model: `python3 /Users/chrisknight/Projects/scripts/context_handoff_manager.py --project-dir . --set-model "GPT-5.3-Codex"`
- Checkpoint: `python3 /Users/chrisknight/Projects/scripts/context_handoff_manager.py --project-dir . --tokens-used <N> --add-note "Checkpoint"`
- Strict guard (fail at warning+): `python3 /Users/chrisknight/Projects/scripts/context_handoff_manager.py --project-dir . --tokens-used <N> --strict --strict-level warning`

## Exactly What To Do
- Below warning: keep working; checkpoint every major block.
- At warning: finish micro-task, checkpoint, prepare handoff.
- At critical: stop and immediately start fresh chat with `CONTEXT_HANDOFF.md`.
