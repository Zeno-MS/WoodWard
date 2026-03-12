# New Chat Handoff — WoodWard

## Objective
Drive accountability for Vancouver Public Schools' $13.3M staffing vendor spending (FY2024-25) via three simultaneous tracks: journalism (reporter pitch), oversight (SAO referral), and public pressure (records requests + board questions). Woodward Core v2 runtime is now **operationally complete** — all 7 phases accepted, 205 tests pass.

## Current Status (2026-03-12)

### Woodward Core v2 — COMPLETE

All phases accepted. System is operational.

| Phase | Status | Key Deliverable |
|-------|--------|-----------------|
| 0 — Canon freeze | **DONE** | canonical/ YAML files + hash + validate CLI |
| 1 — SQLite kernel | **DONE** | ledger.db, records.db, comms.db + migrations |
| 1B — Seed from woodward.db | **DONE** | 9/9 locked figures replayable from SQL derivations |
| 2 — Figure enforcement | **DONE** | figure_verifier, vendor_alias_resolver, scope_reconciler |
| 3 — Provenance gate | **DONE** | claim_support_checker, public_source_gate |
| 4 — Structured LLM drafting | **DONE** | article_drafter, adversarial_review, DraftSectionResponse contracts |
| 5 — Bridge layer | **DONE** | export_handoff, ingest_manual_draft, compare_dual_run. Live LLM test passed. |
| 6 — Publication control | **DONE** | reply_planner, publication_gate, assemble_article. comms.db seeded with real correspondence. |
| 7 — Audit + backup | **DONE** | audit_runner (5/5 checks pass), backup_service (create/list/restore/verify) |

**Tests:** 205 passed, 1 skipped (live LLM test requires API key — already validated manually)

**Audit report:** `runs/audit_20260312_180501.json` — 5/5 checks PASS, 0 issues

**CLI commands available:**
- `woodward canon validate` / `woodward canon hash`
- `woodward verify figure <figure_id>`
- `woodward bridge export --article <id> --section <id>`
- `woodward reply plan <article_id>` / `woodward reply build <article_id>`
- `woodward publish check <article_id>` / `woodward publish assemble <article_id>`
- `woodward audit run` / `woodward audit check <name>`
- `woodward backup create` / `woodward backup list` / `woodward backup restore <id>`

### 9 Locked Figures — All Verified
| Figure ID | Value | Source |
|-----------|-------|--------|
| fy2425_staffing_vendor_total | $13,326,622 | SQL derivation (PASS) |
| amergis_fy2425_total | $10,970,973 | SQL derivation (PASS) |
| cumulative_staffing_baseline | $32,189,236 | CSV source (PASS) |
| object7_budget_fy2425 | $36,738,206 | SQL derivation (PASS) |
| object7_actual_fy2425 | $47,331,056 | Doc source (PASS) |
| object7_overage_fy2425 | $10,592,850 | Doc source (PASS) |
| board_amergis_estimate_july2024 | $3,000,000 | Doc source (PASS) |
| ospi_advance_requested | $21,367,552 | Doc source (PASS) |
| ospi_advance_approved | $8,700,000 | Doc source (PASS) |

### Investigation Deliverables (09_Deliverables/)

| Track | File | Status |
|-------|------|--------|
| 1 — Journalism | `01_Reporter_Package/REPORTER_PITCH.md` | Ready to send |
| 1 — Journalism | `01_Reporter_Package/FIGURES_SHEET.md` | Ready to attach |
| 1 — Journalism | `01_Reporter_Package/SOURCE_VERIFICATION_LIST.md` | Ready to attach |
| 1 — Journalism | `01_Reporter_Package/START_HERE_REPORTER_GUIDE.md` | Ready to attach |
| 1 — Journalism | `01_Reporter_Package/HOW_THE_KEY_NUMBERS_WERE_BUILT.md` | Ready to attach |
| 1 — Journalism | `01_Reporter_Package/MANUAL_CROSSCHECKS.md` | Ready to attach |
| 2 — Oversight | `02_SAO_Oversight/SAO_OVERSIGHT_MEMO.md` | Ready to submit |
| 3 — Records | `03_Records_Requests/PUBLIC_RECORDS_REQUESTS.md` | 7 ready-to-file PRRs |
| 4 — Pressure | `04_Public_Pressure/PUBLIC_QUESTIONS.md` | 3 repeatable questions |
| 5 — Tracker | `05_Tracker/ACCOUNTABILITY_TRACKER.md` | Live operational status |
| — | `QUARANTINE_MANUALS/` | Fact verification, data gaps, PRR guides |

### Expansion Documents (expansion/)

| File | Purpose |
|------|---------|
| `WOODWARD_CORE_V2_ENACTMENT_PLAN.md` | Full 7-phase migration plan |
| `REDLINE_ENACTMENT_MEMO.md` | Component-by-component keep/rename/delete/replace map |
| `ARCHITECT_ACCEPTANCE_CHECKLIST.md` | Phase gate checklist for supervising Claude Code |
| `CLAUDE_CODE_BUILD_INSTRUCTIONS.md` | Exact build prompt used for v2 implementation |
| `WOODWARD_ARCHITECTURE_SPEC.md` | Legacy architecture spec (reference only, not runtime blueprint) |
| `WOODWARD_ISOLATION_BOUNDARIES.md` | Mandatory guardrail: no Cicero legal content crossover |

### Core Investigation Summary
- VPS cut 260+ positions in March 2024 during declared fiscal emergency
- Same FY2024-25: paid $13.3M to staffing vendors; $10.97M to Amergis (formerly Maxim Healthcare)
- Board approved Amergis at "~$3M" on consent agenda (July 9, 2024). Actual: $10.97M — 366% over estimate
- Contract: auto-renewal, uncapped rates, no spending cap, 30% conversion fee, no competitive bid
- Maxim Healthcare: $150M federal fraud settlement (2011); VPS signed new MSA 10 years later
- Emergency borrowing 3 consecutive years; fund balance $7M → $195,180; $20.15M projected deficit FY26-27

### Live Threads (from 07_Right_of_Reply responses)
| Contact | Status |
|---------|--------|
| Kathleen Cooper, SAO Comms Director | **Engaged** — asked "are you a reporter?" Needs response before SAO memo can land. |
| Shawn Lewis, OSPI Director of SAFS | **Responded** — confirmed advance amounts |
| Clark County Treasurer | **Redirected** to GovQA public records system |
| All VPS/Board contacts (12 sent) | **No responses** |

### SAO Thread — Critical Next Step
Cooper's question ("are you a reporter?") needs an answer before the oversight memo lands. Options:
- Identify as a citizen researcher / concerned taxpayer (honest, gets memo through as citizen concern)
- Identify as working with a reporter (only if true)
- Don't respond to Cooper; instead file memo through SAO's public online tip form (bypasses her)

### What Does NOT Exist Yet
- The 7 PRRs in `03_Records_Requests/` are drafted but **none have been filed**
- No reporter has been pitched yet (Kimberly Cortez is warmest lead)
- SAO memo has not been submitted

## Recommended Next Actions

### Investigation Actions
1. Decide how to handle the SAO/Cooper thread → respond or route around
2. Send reporter pitch to Kimberly Cortez (or next-warmest contact) with 3 attachments
3. File Records Request #2 ($3M/$11M variance documents) first — highest yield
4. Distribute the 3 public questions to union or parent contacts for board meeting

### Engineering — Post-v2 Opportunities
1. Ingest remaining warrant register PDFs into ledger.db for full payment coverage
2. Run `woodward publish assemble article_2` end-to-end with live LLM to produce first v2-generated article draft
3. Build LanceDB retrieval index from records.db documents for RAG-backed drafting
4. Extend comms.db with additional right-of-reply contacts as outreach proceeds

## Key Files

### Runtime
- `canonical/figures.yaml` — 9 locked figures (source of truth)
- `canonical/claims_registry.yaml` — 8 claims with publication status
- `canonical/banned_claims.yaml` — 8 banned claims/figures
- `canonical/vendor_scope.yaml` — vendor definitions + Amergis/Maxim rebrand
- `db/ledger.db` — monetary truth (vendors, payments, derivations, fiscal rollups)
- `db/records.db` — documents, claims, support chains, publication blocks
- `db/comms.db` — organizations, recipients, threads, messages, response windows
- `runs/` — audit reports, draft artifacts, verification reports
- `backups/` — timestamped backup snapshots

### Investigation
- `VPS_Investigation_Evidence/09_Deliverables/README.md` — full map of all deliverables
- `VPS_Investigation_Evidence/EXECUTIVE_SUMMARY.md` — one-page case summary
- `VPS_Investigation_Evidence/INVESTIGATION_BACKGROUND_BRIEFING.md` — full background
- `VPS_Investigation_Evidence/08_Rewrites/CHANGE_STRATEGY.md` — strategic framework
- `VPS_Investigation_Evidence/07_Right_of_Reply/INDEX.md` — all 24 communications logged
- `VPS_Investigation_Evidence/01_Payment_Data/vendor_summary_by_year.csv` — all payment data

### Architecture
- `expansion/WOODWARD_CORE_V2_ENACTMENT_PLAN.md` — v2 migration plan
- `expansion/REDLINE_ENACTMENT_MEMO.md` — component disposition map
- `expansion/ARCHITECT_ACCEPTANCE_CHECKLIST.md` — phase gate checklist
- `expansion/WOODWARD_ISOLATION_BOUNDARIES.md` — mandatory guardrail
- `CICERO_STRUCTURAL_AUDIT.md` — Cicero architecture audit (reference only)

## Model Awareness
- Active model: **Claude Sonnet 4.6**
- Sessions used: Claude Opus 4.6 (1M context) for build, Sonnet for handoff

## Constraints / Do Not Redo
- Do NOT re-analyze the original 4-part articles — they are reference material, not deliverables
- Do NOT cite S.H., 102 Wn. App. 468 — wrong case (attorney sanctions, not judicial investigation)
- Do NOT import Cicero legal prompts, schemas, citation logic, or legal-domain content
- Do NOT use Neo4j as monetary truth — ledger.db is sole monetary authority
- Do NOT let article prose originate canonical figures — all figures from canon
- Do NOT treat manual/webapp drafts as canonical — they enter as pending_review
- The evidence package methodology is sound — 25,578 deduplicated warrant records from 153 PDFs
- Aveanna Healthcare and Stepping Stones are tracked separately, excluded from canonical $32.2M total
- The canonical 5-year figure is $32,189,236 (includes FY25-26 partial); through FY24-25 only: $28,728,737

## Notes
- 2026-02-15 | Bootstrapped WoodWard handoff tooling
- 2026-03-06 through 2026-03-09 | Multiple prior bootstraps (no substantive work logged)
- 2026-03-11 | Took over project. Audited full evidence package. Built 09_Deliverables (5 tracks, 8 files). Built CICERO_STRUCTURAL_AUDIT.md.
- 2026-03-12 | Phase 0+1 ACCEPTED: Canon freeze (YAML schemas + hash + validation). SQLite kernel (ledger/records/comms DBs + migrations + seeds).
- 2026-03-12 | Phase 2 ACCEPTED: figure_verifier, vendor_alias_resolver, scope_reconciler. Object 7 = Purchased Services, object_code=5 in woodward.db.
- 2026-03-12 | Phase 3 ACCEPTED: claim_support_checker, public_source_gate hardened, records.db seeded (8 claims, 2 publication_blocks). 93/93 tests.
- 2026-03-12 | Phase 4 ACCEPTED: context_assembler (task profiles), article_drafter (context_id validation, HallucinatedContextError hard-stop), adversarial_review (8 typed categories), review_draft workflow. 151/151 tests.
- 2026-03-12 | Phase 5 ACCEPTED: bridge layer (export_handoff, ingest_manual_draft, compare_dual_run). Live LLM draft test passed — Article 2 procurement overview: gate passed, 9 figures injected, $10,970,973 in output, all context_ids resolved. 190/190 tests.
- 2026-03-12 | Phase 6 ACCEPTED: reply_planner, publication_gate (5 conditions), build_reply_packet, assemble_article. comms.db seeded: 4 orgs, 5 recipients, 3 threads (vps_ror/sao_cooper/ospi_lewis), publication-blocking response window (sao_cooper, deadline 2026-03-20). 190/190 tests.
- 2026-03-12 | Phase 7 ACCEPTED: audit_runner (5 checks: figures, support chains, banned refs, orphaned claims, missing docs — all PASS). backup_service (create/list/restore/verify). 15 new tests. 205/205 total PASS.
- 2026-03-12 | Phase 1B ACCEPTED: Seeded ledger.db from woodward.db. Fixed derivation status validation (added csv_source, doc_source). Set computed_value for doc-sourced derivations. All 9 locked figures verify PASS.
- 2026-03-12 | MILESTONE: Woodward Core v2 operationally complete. Webapp no longer required as project memory. Canonical state in YAML + SQLite + run artifacts.

_Generated: 2026-03-12 (v2 complete)_
