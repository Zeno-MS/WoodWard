---
name: "handoff"
description: "Create an execution-ready handoff using the project context_handoff protocol and a copy-paste resume prompt"
argument-hint: "Optional focus for next session"
agent: "agent"
---
Generate a handoff for this project using the established toolkit in this order of precedence:

1) If `CONTEXT_HANDOFF_WORKFLOW.md` and `.context_handoff_state.json` exist, follow that protocol.
2) Use `CONTEXT_HANDOFF.md` as the canonical continuity artifact.
3) If a `handoffs/` directory and explicit handoff file convention exist, include that as an additional artifact, not a replacement.

Requirements:
- Do not invent a competing handoff process.
- Preserve existing project protocol and naming conventions.
- Prefer concrete repo state over abstract narrative.
- Include files changed, validation performed, remaining tasks, and constraints.
- Do not include secrets.

Output format:

First section:

`Protocol update commands:`

Then emit a fenced `bash` block with project-root commands to update handoff state, for example:
- `./context_handoff --tokens-used <N> --set-status "..." --add-note "..." --add-next "..."`

Second section:

`Paste this into the new chat:`

Then emit one fenced `md` block with:
- One-line resume instruction
- Context
- Completed work
- Files changed or relevant
- Validation done
- Current assumptions/runtime facts
- Next task
- Constraints / do-not-redo
- Known follow-ups

Style:
- Concise, operational, execution-focused.
- Bullets over long prose.