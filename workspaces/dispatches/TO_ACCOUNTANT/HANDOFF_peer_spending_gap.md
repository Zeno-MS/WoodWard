# New Chat Handoff — Peer Spending Gap (Object 7)

## Objective
Find Object 7 (Purchased Services) totals for Evergreen (06114) and Tacoma (27010) for 2022-23 and 2023-24.

## Targets
- Evergreen School District (Clark County) — 06114
- Tacoma School District — 27010

## CSV Output
```csv
District,Year,Object_7_Total
Evergreen,2022-23,
Evergreen,2023-24,
Tacoma,2022-23,
Tacoma,2023-24,
```

## Current Status
- Located district budget landing pages and candidate F-195 sources.
- Google Drive-hosted PDFs may require browser/authenticated access.
- OSPI SAFS portal appears interactive (dropdown-driven).

## Context Window Watch
- Status: **OK** at **27.6%** | 75000/272000 tokens (checked: 2026-02-15T08:02:10+00:00)
- Thresholds: warning at 70% | critical at 85%
- Immediate instruction:
  - Continue current work.
  - Re-check context after each major work block or after 3-5 tool calls.
- Trigger plan:
  - At WARNING (70% = 190400 tokens): checkpoint + summarize + prepare handoff.
  - At CRITICAL (85% = 231200 tokens): stop and immediately start new chat from handoff.
  - Next trigger: WARNING in 115400 tokens.

## Model Awareness
- Active model: **GPT-5.3-Codex**
- Approx context window: **272000 tokens**
- Notes: Approximate Copilot input context; output budget is separate.
- Tracked models: 17

## Key Sources
- https://sites.google.com/evergreenps.org/budget-fiscal-services/budget
- https://www.tacomaschools.org/fs/pages/7712
- https://ospi.k12.wa.us/policy-funding/school-apportionment/safs-report
- https://reportcard.ospi.k12.wa.us/

## Next Actions
- Open each district F-195 for 2022-23 and 2023-24 in a real browser/automation.
- Search each PDF for 'Object 7' or 'Purchased Services'.
- Record totals and populate CSV rows.

## Blockers
- Static fetch tools may fail on JS-driven pages or authenticated Google Drive resources.

## Notes
- 2026-02-15T07:46:29+00:00 | Validation run after automation setup
- 2026-02-15T07:46:40+00:00 | Added automation artifacts to handoff inventory
- 2026-02-15T08:01:33+00:00 | Enabled model-aware context policy from Feb 2026 model table
- 2026-02-15T08:01:54+00:00 | Synced tokens_total to active model context window
- 2026-02-15T08:02:10+00:00 | Validated model-context override behavior

## Workspace Artifacts
- 01_peer_spending_gap.txt
- 01_peer_spending_gap_RESEARCH_FINDINGS.md
- HANDOFF_peer_spending_gap.md
- handoff_manager.py
- handoff_state_peer_spending_gap.json
- HANDOFF_WORKFLOW.md

_Generated: 2026-02-15T08:02:10+00:00_
