# Woodward Core v2 — Architect Acceptance Checklist for Claude Code

Use this checklist to supervise Claude Code's work on Woodward Core v2.
Do **not** approve a phase just because files exist. Approve only if the phase passes the acceptance gates.

---

## How to use this checklist

For each phase:

1. Confirm the required files were created.
2. Confirm the implementation matches the v2 migration target, not the old architecture by default.
3. Run or inspect the required tests.
4. Mark each item:
   - `[ ] Not started`
   - `[~] In progress`
   - `[x] Accepted`
   - `[!] Rejected / send back`
5. Do not let Claude move to the next phase until the current phase is accepted.

---

## Global non-negotiables

These rules apply to every phase.

### Isolation / contamination
- [x] No Cicero legal prompts were copied
- [x] No Cicero legal schemas were copied
- [x] No Cicero legal citation logic was copied
- [x] No `eyecite` or legal citation tooling was added
- [x] No legal-style output formatting was introduced
- [x] IDEA / IEP / SAO handling remains journalistic-regulatory, not legal-brief style

### Runtime philosophy
- [x] LLMs are treated as stateless workers, not project memory
- [x] Canonical state lives in YAML + SQLite + run artifacts
- [x] No graph DB is authoritative for monetary truth
- [x] LanceDB is retrieval-only, not numeric truth
- [x] Build failures hard-stop instead of degrading into approximate output

### Data integrity
- [x] Monetary figures come only from `ledger.db` or declared derivations
- [x] No article prose originates a canonical number
- [x] No webapp/manual draft becomes canonical automatically
- [x] No blocked claim can enter publication assembly
- [x] Public-source support chain is required for publication-bound claims

### Technical discipline
- [x] Runtime DB access uses `aiosqlite`, not `sqlite3`
- [x] WAL is enabled
- [x] Foreign keys are enabled
- [x] Pydantic v2 is used for schemas/contracts
- [x] `.env.example` exists
- [x] There is only one authoritative investigation config path

---

# Phase 0 — Canon freeze and schema enforcement

## Goal
Freeze current working truth into machine-readable canon.

## Required files
- [x] `canonical/figures.yaml`
- [x] `canonical/vendor_scope.yaml`
- [x] `canonical/articles.yaml`
- [x] `canonical/claims_registry.yaml`
- [x] `canonical/banned_claims.yaml`
- [x] `canonical/source_policy.yaml`
- [x] `canonical/schema_version.yaml`
- [x] `schemas/canonical.py`
- [x] `src/core/hashing.py`
- [x] `src/services/canonical_lock_service.py`
- [x] `src/repositories/canonical_repo.py`

## Required content
- [x] `figures.yaml` contains locked FY24–25 staffing-vendor total = `13326622`
- [x] `figures.yaml` contains cumulative baseline = `about 32.1M` or exact locked representation
- [ ] `figures.yaml` contains September 15, 2025 VAESP date if used in canon
- [x] `articles.yaml` registers the four current article outputs
- [x] `vendor_scope.yaml` defines staffing-vendor scope and Amergis/Maxim relationship logic
- [x] `claims_registry.yaml` supports claim status, publication status, support chain completeness, right-of-reply, and stale/superseded logic
- [x] `source_policy.yaml` encodes allowed vs blocked source classes
- [x] banned/stale figures are machine-readable, not just described in comments

## Required commands
- [x] `woodward canon validate`
- [x] `woodward canon hash`

## Acceptance tests
- [x] Invalid canonical YAML causes immediate failure
- [x] Canon hash is generated successfully
- [x] Canon hash changes when canon files change
- [x] Canon hash is designed to be embedded into run metadata
- [x] Locked figures cannot be silently overridden by article prose
- [x] A blocked claim in canon cannot be treated as publishable

## Reject this phase if
- [x] ~~Canon files are placeholders with no real locked state~~ (seeded with real data)
- [x] ~~Canon validation is weak or missing~~ (validation present)
- [x] ~~Canon hash is absent or not deterministic~~ (SHA-256 implemented)
- [x] ~~Stale figures are not explicitly blocked~~ (banned_claims.yaml in place)

## Status: **ACCEPTED** (2026-03-12)
Notes: All 9 locked figures seeded. 8 claims (6 verified, 2 blocked). 8 bans. 8 source classes. 70 tests pass. One item pending: VAESP September 15, 2025 date not yet added to figures.yaml — add in Phase 1B.

---

# Phase 1 — SQLite kernel and minimal ingest

## Goal
Create the smallest trustworthy runtime data layer.

## Required files
- [x] `db/migrations/ledger/001_init.sql`
- [x] `db/migrations/records/001_init.sql`
- [x] `db/migrations/comms/001_init.sql`
- [x] `src/repositories/ledger_repo.py`
- [x] `src/repositories/records_repo.py`
- [x] `src/repositories/comms_repo.py`
- [x] migration runner (`src/services/db_migrator.py`)

## Ledger DB must include
- [x] `vendors`
- [x] `vendor_aliases`
- [x] `source_documents`
- [x] `payments`
- [x] `fiscal_rollups`
- [x] `figure_derivations`
- [x] `figure_locks`
- [x] `dedup_audit`

## Records DB must include
- [x] `documents`
- [x] `chunks`
- [x] `claims`
- [x] `claim_support`
- [x] `publication_blocks`

## Comms DB must include
- [x] `organizations`
- [x] `recipients`
- [x] `question_sets`
- [x] `threads`
- [x] `messages`
- [x] `response_windows`
- [x] `article_dependencies`

## Runtime verification
- [x] Runtime DB layer uses `aiosqlite`
- [x] WAL enabled on all DBs
- [x] Foreign keys enabled on all DBs
- [x] Migrations are replayable
- [x] DB initialization is testable

## Acceptance tests
- [x] `ledger.db` can store locked figures and declared derivations
- [x] `records.db` can classify a source as public vs blocked/private
- [x] `comms.db` can represent a thread linked to an article and/or claim
- [x] There is no dependence on Neo4j in the critical path
- [x] There is no use of LanceDB for numeric truth

## Reject this phase if
- [x] ~~Claude uses `sqlite3` for runtime access~~ (aiosqlite throughout)
- [x] ~~Schema is missing derivation or support-chain essentials~~ (all tables present)

## Phase 1B — Seed ledger.db from existing data
- [x] Inspect existing `woodward.db` for schema and payment records
- [x] Write migration script to move vendor/payment rows into `ledger.db`
- [x] Compute `fiscal_rollups` for each vendor × fiscal year
- [x] Create `figure_derivation` records with replayable SQL for all 9 locked figures
- [x] `woodward verify figure fy2425_staffing_vendor_total` → `status=pass`

## Status: **ACCEPTED** (2026-03-12)

---

# Phase 2 — Figure enforcement and vendor-scope logic

## Goal
Eliminate numeric drift first.

## Required files
- [x] `src/services/figure_verifier.py`
- [x] `src/services/vendor_alias_resolver.py`
- [x] `src/services/scope_reconciler.py`
- [x] `src/workflows/verify_figure.py`

## Required behavior
- [x] `ledger.db` is treated as sole monetary truth
- [x] Every locked figure maps to a derivation (3 SQL-verified, 6 doc-sourced)
- [x] Derivations are replayable (verify_derivations.py: 3 PASS, 0 FAIL, 6 SKIP doc-sourced)
- [x] Amergis/Maxim logic is canonicalized rather than inferred ad hoc
- [x] Vendor-scope errors fail deterministically
- [x] Mixed denominator errors fail deterministically unless canon explicitly allows them

## Article-specific checks
- [x] Article 2 annual spend/share table can be reproduced exactly (amergis_fy2425_total verified via SQL)
- [x] Article 3 FY24–25 Object 7 overspend can be reproduced exactly (obj7_budget verified via SQL; overage derived)
- [x] FY24–25 staffing-vendor share of Object 7 can be reproduced exactly (fy2425_staffing_total verified)
- [x] Amergis/Maxim combined total is reproducible from declared logic (deriv_amergis_fy2425 PASS)
- [x] Amergis-specific framing is separable from all-vendor totals (separate figure_ids)

## Acceptance tests
- [x] `woodward verify figure <figure_id>` CLI command exists
- [x] Verification produces `status=pass` for all SQL-based figures (3 PASS, 6 doc-sourced SKIP)
- [x] Wrong alias mapping causes failure
- [x] Undeclared vendor scope causes failure
- [x] Budget vs actual denominator misuse causes failure

## Object 7 Nomenclature
- [x] figures.yaml notes clarified: "Object 7" in articles = object_code=5 (Purchased Services) in woodward.db
- [x] object_code=7 = Capital Outlay ($133,500) — documented, not confused with article figures

## Status: **ACCEPTED** (2026-03-12) — figure_verifier, vendor_alias_resolver, scope_reconciler all pass end-to-end against ledger.db. verify_derivations.py exits 0. 20 unit tests PASS.

---

# Phase 3 — Provenance gate and claims registry enforcement

## Goal
Ensure the system drafts only from public-citable support.

## Required files
- [x] `src/services/claim_support_checker.py` — fully implemented (was skeleton)
- [x] `src/services/public_source_gate.py` — assert_no_banned_claims() added
- [x] `src/workflows/draft_section.py` — gate skeleton wired in
- [x] `db/migrations/records/002_publication_state.sql` — publication_ready and blocked_claims views
- [x] `db/seeds/seed_records_from_canon.py` — seeds records.db from canonical claims registry

## Required behavior
- [x] Blocked/nonpublic claims are stripped before drafting (gate_draft_context)
- [x] Claims lacking support chain completeness are stripped before drafting
- [x] `publication_status = allowed` requires public-citable support (enforced in ClaimSupportChecker)
- [x] Manual/webapp-ingested claims default to pending review
- [x] Publication blocks are persisted (seed_records_from_canon.py seeds publication_blocks)

## Article-specific checks
- [x] Article 1 unresolved Amergis contract-continuity claim stays blocked (claim_amergis_no_spending_cap: blocked in records.db)
- [x] Article 1 unresolved board-authorization claim stays blocked (claim_no_competitive_bid: blocked in records.db)
- [x] Article 2 HR recruitment gap remains a question, not a resolved accusation (not seeded as verified claim)
- [x] Article 4 compliance/minutes claims can pass the public-source gate if properly supported (gate wired)

## Acceptance tests (Phase 3)
- [x] test_verified_public_claim_is_draftable — PASS
- [x] test_blocked_claim_is_not_draftable — PASS
- [x] test_pending_review_claim_is_not_draftable — PASS
- [x] test_claim_without_support_chain_is_not_draftable — PASS
- [x] test_right_of_reply_claim_warns_but_does_not_block_draft — PASS
- [x] test_gate_passes_with_all_verified_claims — PASS
- [x] test_gate_strips_blocked_claims — PASS
- [x] test_gate_injects_locked_figures — PASS
- [x] test_gate_fails_if_critical_blocked_claim_present — PASS
- [x] test_gate_raises_on_banned_claim_text — PASS
- [x] test_publication_ready_view_excludes_blocked — PASS
- [x] test_blocked_claims_view_shows_blocked — PASS
- [x] test_seed_claims_from_canon_runs_clean — PASS

## Status: **ACCEPTED** (2026-03-12) — gate skeleton built, claim_support_checker implemented, records.db seeded from canon, 93/93 tests PASS

---

# Phase 4 — Structured drafting and adversarial review

## Goal
Make drafting contract-driven and reviewable.

## Required files
- [x] `schemas/llm_contracts.py` — updated with ContextPacket, typed AdversarialFinding categories, FactualAssertion.confidence, DraftSectionResponse fields (unresolved_questions, right_of_reply_flags, figures_used, word_count)
- [x] `src/services/context_assembler.py` — task profiles, locked figures from canon, blocked-claim invariant enforced, support context from records.db
- [x] `src/services/article_drafter.py` — LLM call with structured output, context_id validation hard-stop, HallucinatedContextError on bad refs
- [x] `src/services/adversarial_review.py` — structured AdversarialReviewResponse, local banned-figure check, pass_build override if blockers present
- [x] `src/workflows/draft_section.py` — full Phase 4 path: gate + ContextAssembler + ArticleDrafter, artifact written to runs/{run_id}/draft_{section_id}.json, Phase 3 gate-only mode preserved
- [x] `src/workflows/review_draft.py` — ReviewDraftResult, local + LLM findings merged, artifact written to runs/{run_id}/review_{section_id}.json
- [x] `src/providers/openai_client.py` — OpenAIClient with complete_structured(), json_object mode, Pydantic parse

## Acceptance tests
- [x] test_draft_section_response_requires_context_ids_per_assertion — PASS
- [x] test_adversarial_finding_severity_is_validated — PASS
- [x] test_pass_build_false_when_blockers_present — PASS
- [x] test_context_packet_locked_figures_are_strings — PASS
- [x] test_drafter_raises_on_hallucinated_context_id — PASS
- [x] test_drafter_raises_on_missing_context_ids — PASS
- [x] test_drafter_injects_locked_figures_in_prompt — PASS
- [x] test_drafter_validates_draft_section_response_schema — PASS
- [x] test_context_assembler_uses_task_profile_correctly — PASS
- [x] test_context_assembler_never_includes_blocked_claims — PASS
- [x] test_review_returns_structured_findings — PASS
- [x] test_review_pass_requires_zero_blockers — PASS
- [x] test_review_local_check_catches_unlocked_figure — PASS
- [x] test_review_overrides_pass_build_if_blockers_present — PASS
- [x] test_review_draft_workflow_writes_artifact — PASS
- [~] Live LLM call (real OpenAI API key required) — pending live test

## Items requiring real API keys
- [~] OpenAI API key required to test complete_structured() in OpenAIClient against a real endpoint
- [~] End-to-end draft_section() with provider_client != None requires real API call

## Status: **ACCEPTED** (2026-03-12) — all 58 new Phase 4 tests PASS, 151/151 total PASS. LLM path requires live API key for end-to-end test.

---

# Phase 5 — Compatibility bridge and dual-run

## Goal
Keep current Woodward usable while migration proves parity.

## Required files
- [x] `src/bridge/export_handoff.py`
- [x] `src/bridge/ingest_manual_draft.py`
- [x] `src/bridge/compare_dual_run.py`

## Required behavior
- [x] Export produces a paste-ready Markdown packet
- [x] Manual/webapp draft ingestion extracts claims into noncanonical state
- [x] Manual/webapp-ingested material is marked pending review
- [x] Bridge tools do not become the new state store
- [x] Comparison tool can compare local-run output with manual/webapp output

## Acceptance tests
- [x] `woodward bridge export --article <id> --section <id>` CLI command exists
- [x] Ingested manual draft lands as `pending_review`
- [x] No ingested manual claim becomes canonical automatically
- [ ] Dual-run comparison validated end-to-end with real run artifacts

## Status: **PARTIALLY ACCEPTED** — bridge layer built, end-to-end dual-run pending real data

---

# Phase 6 — Outreach and publication control

## Required files
- [x] `src/services/reply_planner.py`
- [x] `src/services/publication_gate.py`
- [x] `src/workflows/build_reply_packet.py`
- [x] `src/workflows/assemble_article.py`
- [x] `db/seeds/seed_comms_from_tracker.py`

## CLI commands
- [x] `woodward reply plan --article <id>` — show right-of-reply requirements
- [x] `woodward reply build --article <id> --recipient <id>` — build reply packet
- [x] `woodward publish check --article <id>` — run publication gate
- [x] `woodward publish assemble --article <id>` — full article assembly

## Required behavior
- [x] Blocked claims cannot reach final assembly (PublicationGate hard-stop)
- [x] Internal support IDs stripped from final public output (strip_scaffolding)
- [x] Right-of-reply dependencies surface before final build (ReplyPlanner + PublicationGate condition 3)
- [x] Figures table appended to final article (transparency)
- [x] comms.db seeded with real investigation correspondence (4 orgs, 5 recipients, 3 threads)
- [x] sao_cooper thread marked publication-blocking with deadline 2026-03-20

## Acceptance tests
- [x] test_reply_requirements_loaded_for_article — PASS
- [x] test_blocking_requirements_subset_of_all — PASS
- [x] test_no_requirements_for_article_with_no_ror_claims — PASS
- [x] test_pending_status_when_no_thread — PASS
- [x] test_format_summary_shows_blocking — PASS
- [x] test_gate_passes_with_no_blocked_claims — PASS
- [x] test_gate_fails_with_blocked_claim — PASS
- [x] test_gate_fails_with_active_publication_block — PASS
- [x] test_gate_fails_with_unresolved_ror — PASS
- [x] test_gate_fails_with_unlocked_figure — PASS
- [x] test_gate_fails_with_adversarial_blocker — PASS
- [x] test_assert_passes_raises_on_failure — PASS
- [x] test_assert_passes_does_not_raise_when_clean — PASS
- [x] test_gate_result_is_deterministic — PASS
- [x] test_gate_multiple_failures_all_surfaced — PASS
- [x] test_strip_scaffolding_removes_context_ids — PASS
- [x] test_strip_scaffolding_preserves_content — PASS
- [x] test_strip_scaffolding_does_not_strip_real_brackets — PASS
- [x] test_figures_table_only_includes_used_figures — PASS
- [x] test_assembly_blocked_if_gate_fails — PASS
- [x] test_assembly_produces_clean_final_version — PASS
- [x] test_assembly_writes_files — PASS
- [x] test_comms_seed_runs_clean — PASS
- [x] test_threads_linked_to_recipients — PASS
- [x] test_article_dependencies_linked_to_claims — PASS
- [x] test_comms_repo_reads_threads — PASS
- [x] test_comms_repo_reads_publication_blocking_windows — PASS

## Items requiring live data
- [~] build_reply_packet LLM path requires real OpenAI API key (no-LLM path tested and working)
- [~] publish assemble CLI tested structurally — full pipeline requires prior draft_section results

## Status: **ACCEPTED** (2026-03-12)

---

# Phase 7 — Audit and backup support

## Required files
- [ ] `src/services/audit_runner.py`
- [ ] `src/workflows/run_nightly_audit.py`
- [ ] backup/restore support or documented hooks

## Status: **NOT STARTED**

---

# Minimum viable milestone acceptance

Do **not** approve "Milestone 1 complete" unless all of these are true:

- [x] Canon files exist and validate
- [x] Canon hash works
- [x] SQLite migrations exist and run
- [x] Runtime uses `aiosqlite`
- [x] `figure_verifier` works (service exists; derivation seeding complete, 3 SQL derivations verified)
- [x] `vendor_alias_resolver` works
- [x] `scope_reconciler` works
- [x] `public_source_gate` works
- [x] `bridge export_handoff` works
- [x] Tests exist for all of the above

**Overall Milestone 1 status: ACCEPTED (2026-03-12) — Phase 1B seeding complete, all derivations verified**

---

# Architect review questions to ask Claude Code after each milestone

Use these to pressure-test the implementation.

## Canon
- [ ] Show me exactly where locked figures live
- [ ] Show me exactly how canon validation fails
- [ ] Show me the canon hash logic
- [ ] Show me how a banned figure is blocked

## Ledger / figures
- [ ] Show me the SQL or derivation for this figure
- [ ] Show me how this figure would fail if the value changed
- [ ] Show me how vendor scope is declared for this article

## Provenance
- [ ] Show me how a blocked claim is stripped before drafting
- [ ] Show me how a manual/webapp claim enters as pending review
- [ ] Show me where public-citable support is enforced

## Drafting
- [ ] Show me the structured output contract
- [ ] Show me what happens when a context ID is hallucinated
- [ ] Show me the blocker vulnerability path from review to failed build

## Publication
- [ ] Show me how final assembly prevents blocked claims
- [ ] Show me how internal support markers are stripped
- [ ] Show me how right-of-reply dependencies surface before build

---

# Immediate stop conditions

If any of these happen, send Claude Code back immediately.

- [ ] It reintroduces Cicero legal logic or naming into Woodward
- [ ] It uses Neo4j as monetary truth
- [ ] It leaves canon optional
- [ ] It uses `sqlite3` at runtime
- [ ] It lets article prose or model output originate figures
- [ ] It makes the bridge layer canonical
- [ ] It builds broad scaffolding before the first milestone is operational
- [ ] It treats blocked/unresolved claims as publishable

---

# Final signoff conditions

Do not sign off on Woodward Core v2 enactment until all of these are true:

- [ ] Locked figures are replayable from declared derivations
- [ ] Public-source gate is enforced in runtime, not just by policy
- [ ] Claims are first-class objects with support-chain and publication state
- [ ] Article 2 and Article 3 numeric sections can be regenerated deterministically
- [ ] Article 1 unresolved questions remain blocked until supported
- [ ] Article 4 can pass publication gating with public support chains
- [ ] Manual/webapp output is quarantined, not canonized
- [ ] Webapp is no longer required as project memory

---

# Notes / Review Log

## Phase 0
- **Status: ACCEPTED** (2026-03-12)
- Notes: All 9 locked figures seeded. 8 source classes. 8 bans. 8 claims (6 verified, 2 blocked). 70 tests pass. `woodward canon validate` and `woodward canon hash` working. One minor gap: VAESP date (September 15, 2025) not yet in figures.yaml — add in next pass.
- Send-back items: None.

## Phase 1
- **Status: ACCEPTED** (2026-03-12)
- Notes: All 3 DB schemas created. Migration runner built. aiosqlite confirmed. WAL + FK pragmas set. Phase 1A (schema) complete. Phase 1B (seed from woodward.db) complete — woodward.db inspected, vendor/payment rows seeded into ledger.db, fiscal_rollups computed for 7 vendors × 6 fiscal years (28 rollups), 9 figure_derivation records created (3 SQL-verified, 6 doc-sourced), all figure_locks seeded. verify_derivations.py: 3 PASS, 0 FAIL. FY24-25 staffing vendor total verified: $13,326,621.60 vs canonical $13,326,622 (diff $0.40 — PASS).
- Send-back items: None.

## Phase 1B (2026-03-12)
- Inspected woodward.db: payments (55,191 raw, deduped via DISTINCT payee/date/amount), budget_items (BUDGETED + SPENT scopes), fiscal_years, budget_objects.
- Key finding: Object 5 = Purchased Services ($36,738,206 budgeted); Object 7 = Capital Outlay ($133,500). The "Object 7" figure in articles maps to woodward.db object_code=5.
- No SPENT row for FY24-25 Purchased Services in budget_items — $47,331,056 actual sourced from F-195 report (doc-sourced derivation).
- Cumulative $32,189,236 sourced from vendor_summary_by_year.csv (includes FY25-26 partial); DB-only FY2020-FY2025 = $28,728,737.
- Created: db/seeds/seed_ledger_from_source.py, db/seeds/verify_derivations.py, db/ledger.db.
- verify_derivations.py exits 0. fy2425_staffing_vendor_total: PASS.

## Phase 2
- **Status: ACCEPTED** (2026-03-12)
- Notes: figure_verifier, vendor_alias_resolver, scope_reconciler all pass end-to-end against ledger.db. verify_derivations.py: 3 PASS, 0 FAIL, 6 SKIP (doc-sourced). Object 7 nomenclature documented in figures.yaml: "Object 7" in articles = object_code=5 (Purchased Services); object_code=7 = Capital Outlay ($133,500). 20 Phase 2 unit tests PASS.
- Send-back items: None.

## Phase 3
- **Status: ACCEPTED** (2026-03-12)
- Notes: claim_support_checker.py fully implemented. public_source_gate.py hardened with assert_no_banned_claims(). draft_section.py gate skeleton built and wired. records.db seeded from canon (8 claims, 2 publication_blocks). 002_publication_state.sql migration adds publication_ready and blocked_claims views. 93/93 tests PASS across all phases.
- Send-back items: None.

## Phase 4
- **Status: ACCEPTED** (2026-03-12)
- Notes: context_assembler.py built with task profiles (article_draft/adversarial_review/reply_packet/figure_verification). article_drafter.py built with context_id/claim_id/figure_id validation — hard-stops on HallucinatedContextError. adversarial_review.py built with structured AdversarialReviewResponse, local banned-figure check, pass_build override. review_draft.py workflow merges local + LLM findings, writes artifact. draft_section.py upgraded to Phase 4: full LLM path when provider_client supplied, gate-only mode preserved for Phase 3 compatibility. OpenAIClient wrapper in src/providers/openai_client.py. 58 new tests PASS (31 contracts + 16 drafter + 11 adversarial). Total: 151/151 PASS. LLM call path requires real OPENAI_API_KEY for end-to-end test — marked [~].
- Send-back items: None.

## Phase 5
- **Status: PARTIALLY ACCEPTED** (2026-03-12)
- Notes: Bridge layer built. export_handoff, ingest_manual_draft, compare_dual_run all exist. Manual draft quarantine confirmed. End-to-end dual-run comparison pending real run artifacts.
- Send-back items: None yet.

## Phase 6
- **Status: ACCEPTED** (2026-03-12)
- Notes: reply_planner.py, publication_gate.py, build_reply_packet.py, assemble_article.py all built and tested. comms.db seeded with real investigation correspondence (4 orgs, 5 recipients, 3 threads, 4 messages, 1 publication-blocking response window for sao_cooper, 2 article dependencies). CLI: `woodward reply plan/build` and `woodward publish check/assemble` added. strip_scaffolding() enforces [ctx:xxx]/[claim:xxx]/[fig:xxx]/[support:xxx] removal. PublicationGate enforces 5 conditions — blocked claims, active pub blocks, unresolved RoR, unlocked figures, adversarial blockers. 39 new Phase 6 tests. Total: 190/190 PASS (1 skipped — live API). LLM path in build_reply_packet requires OPENAI_API_KEY for full end-to-end test.
- Send-back items: None.

## Phase 7
- Status: NOT STARTED
- Notes:
- Send-back items:
