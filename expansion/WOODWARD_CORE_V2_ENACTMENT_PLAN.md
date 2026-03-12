# Woodward Core v2 — Full Enactment Plan

This is a **compatibility-first migration plan**, not a greenfield rebuild. It preserves the current editorial surface, the locked baselines, the public-source rule, and the existing investigation outputs, while replacing the runtime core with a smaller, stricter, workflow-driven system. The current spec is still built around multi-agent pipelines, Neo4j-heavy database layers, and Cicero-shaped abstractions, even though it correctly states that `paymentsdb` is the canonical source of truth for dollar figures and that the isolation rules must prevent legal-domain carryover.

---

# 1. Executive Objective

The objective is to move Woodward from:

- chat-thread state
- broad multi-brain orchestration
- mixed canonical/noncanonical numeric state
- manual webapp dependency

to:

- canonical machine-readable state
- deterministic figure verification
- public-source-gated drafting
- workflow-based execution
- artifact-based memory
- gradual webapp demotion

This is necessary because the current architecture still spreads important truth across `paymentsdb`, Neo4j graphs, LanceDB, prompts, and editorial pipelines, while the live investigation already depends on locked baselines like **$13,326,622 FY24–25**, **~$32.1M cumulative**, and public-source-only publication rules.

---

# 2. What Stays Unchanged

These are preserved exactly unless explicitly superseded.

**Editorial rules stay:**
- Public evidence only for publication
- Evidence-grade discipline
- No motive language
- Antigravity remains in the data lane, not the narrative lane

**Architectural guardrails stay:**
- Cicero infrastructure patterns may be borrowed
- Legal prompts, schemas, citation logic, skills, and agent identities may not be ported
- Woodward's prompts, skills, and schemas must be written from scratch for journalism

**Current factual locks stay:**
- FY24–25 staffing-vendor total: **$13,326,622**
- Cumulative baseline: **$32.1M**
- September 15, 2025 VAESP date
- The four locked article outputs remain the working baseline during migration

---

# 3. The v2 Runtime Model

## 3.1 Canon Layer

This becomes the anti-drift core.

Files:
- `canonical/figures.yaml`
- `canonical/vendor_scope.yaml`
- `canonical/articles.yaml`
- `canonical/claims_registry.yaml`
- `canonical/banned_claims.yaml`
- `canonical/source_policy.yaml`

**Rule:** No narrative workflow is allowed to originate a number, vendor scope, or publication-allowed claim. Those must come from canon or declared derivations.

This is the main change from the current architecture, which still centers the runtime around agents, skills, and graph-backed retrieval flows rather than a first-class canon state.

## 3.2 Data Layer

Replace the current "four Neo4j pillars + SQLite + LanceDB" approach with a simpler core:

- `ledger.db` — monetary and tabular truth
- `records.db` — public documents, chunks, claims, support chains
- `comms.db` — outreach, right-of-reply, publication dependencies
- LanceDB — retrieval only, never canonical truth

The current spec defines `evidencedb`, `casedb`, `skillsdb`, and `trackingdb` as major graph layers. v2 demotes those concepts into either SQLite structures or optional derived projections.

## 3.3 Service Layer

Core services:
- `figure_verifier`
- `vendor_alias_resolver`
- `scope_reconciler`
- `claim_support_checker`
- `public_source_gate`
- `context_assembler`
- `article_drafter`
- `adversarial_review`
- `reply_planner`
- `publication_gate`
- `audit_runner`
- `run_registry`

This replaces the current spec's emphasis on skills + brains + editorial board pipeline as the primary runtime.

## 3.4 Orchestration Layer

The orchestrator becomes API-first and contract-first:
- Each LLM call has a schema
- Each task has allowed inputs
- Each run produces artifacts
- Failed validation triggers retry or hard stop

This keeps the good part of the existing `router/coordinator/context/pipeline` model while making it deterministic.

## 3.5 Compatibility Bridge

Woodward remains usable during migration via:
- `bridge export_handoff`
- `bridge ingest_manual_draft`
- `bridge compare_dual_run`

This is not in the current architecture spec, but it is essential for preserving the current investigation while migration happens.

---

# 4. The Enactment Phases

## Phase 0 — Freeze, Quarantine, and Baseline Lock

**Duration:** 2–4 days

### Goal
Preserve today's working state without changing behavior.

### Tasks
1. Create `canonical/` directory and schemas
2. Encode locked figures from the handoff
3. Register the four current article files in `articles.yaml`
4. Create `banned_claims.yaml` and `banned_figures.yaml`
5. Add SHA-256 state hashing for the entire canon directory
6. Mark every imported legacy item with `ingest_source = legacy_webapp_export`
7. Create `schema_version.yaml`

### Required Outputs
- Valid canonical files
- Boot-time canon validator
- Canon hash generator
- Initial banned figure set

### Acceptance Tests
- Boot fails on malformed `figures.yaml`
- Canon hash is emitted at run start
- All four article files are registered
- Stale figures are blocked from new builds
- Imported legacy data cannot be treated as canonical until reviewed

### Why First
The current handoff already treats a narrow set of baselines as safe and explicitly bans unsupported/private/internal claims. Phase 0 turns that from prose discipline into machine-enforced state.

---

## Phase 1 — Database Kernel and Minimal Ingest

**Duration:** 1–2 weeks

### Goal
Stand up the smallest real source-of-truth layer.

### Tasks
1. Build `ledger.db` schema
2. Build `records.db` schema
3. Build `comms.db` schema
4. Use `aiosqlite`, WAL, and foreign keys
5. Ingest only the minimum current numeric state:
   - Annual vendor-spend trajectory
   - FY24–25 Object 7 budget and actual
   - Amergis/Maxim combined total
6. Ingest the four article files into `records.db` as documents
7. Ingest the minimum public documents needed for Articles 2–4
8. Configure LanceDB only for retrieval

### Required Outputs
- Three live SQLite DBs
- Seed scripts
- Initial source documents table
- Derivation table for locked figures

### Acceptance Tests
- `ledger.db` reproduces **$13,326,622**
- `ledger.db` reproduces **$47,331,056**
- `ledger.db` reproduces **$36,738,206**
- `ledger.db` reproduces **$10,592,850**
- `records.db` can distinguish public vs blocked source classes
- No figure can be sourced from LanceDB or article prose alone

### Why This Phase Is Earlier Than the Current Spec
The current architecture spec delays real database population until Week 7–8, after brains and pipelines are already built. That sequencing is backwards for a deterministic system.

---

## Phase 2 — Figure Verification and Scope Control

**Duration:** 1 week

### Goal
Eliminate numeric drift and scope ambiguity first.

### Tasks
1. Implement `figure_verifier`
2. Implement `vendor_alias_resolver`
3. Implement `scope_reconciler`
4. Implement declared derivations for all locked figures
5. Implement figure-lock comparison at run time
6. Add mixed-denominator detection
7. Add article-specific vendor-scope rules

### Required Outputs
- `verify_figure` workflow
- `vendor_scope.yaml`
- Derivation manifest
- Alias map
- Denominator rules

### Acceptance Tests
- Article 2's annual trajectory is reproduced exactly
- Article 3's FY24–25 overspend is reproduced exactly
- Amergis/Maxim combined total is reproducible
- Using a wrong alias or undeclared scope causes failure
- Mixing budgeted and actual denominators without disclosure causes failure

### Why This Comes Before Drafting
Article 2 and Article 3 already depend heavily on reusable numeric structure. Their table logic is the fastest path to replacing webapp dependence with deterministic execution. Article 2 explicitly uses the $3M board-presented estimate, the $10,970,973 Amergis actual, and the broader $28M governance question; Article 3 explicitly uses the $36,738,206 budget, $47,331,056 actual, and $10,592,850 overspend.

---

## Phase 3 — Provenance Enforcement and Claim Gating

**Duration:** 1 week

### Goal
Ensure the system can only publish from public-citable support chains.

### Tasks
1. Implement `public_source_gate`
2. Implement `claim_support_checker`
3. Expand `claims_registry.yaml`
4. Create `publication_blocks` in `records.db`
5. Add claim statuses: `draft`, `verified`, `blocked`, `superseded`
6. Add source classes:
   - **Allowed:** `public_record`, `public_reporting`, `public_records_response`, `public_agency_finding`
   - **Blocked:** `internal_nonpublic`, `memory_only`, `insider_awareness`

### Required Outputs
- Claim registry loader
- Support-chain validator
- Publication block engine
- Source policy file

### Acceptance Tests
- Unresolved Amergis contract-continuity claims remain blocked
- Unresolved board-authorization claims remain blocked
- Article 2 HR gap stays phrased as an unanswered public-record question
- Article 4 compliance claims pass public-source validation
- Any claim lacking a public-citable chain is stripped before draft assembly

### Why This Matters
The handoff explicitly states that claims grounded only in private internal knowledge, insider-only awareness, memory of nonpublic materials, intuition, or undocumented extrapolation may not be published. v2 makes that a hard runtime rule.

---

## Phase 4 — Structured Drafting and Adversarial Review

**Duration:** 1–2 weeks

### Goal
Replace fragile prose drafting with contract-driven drafting.

### Tasks
1. Implement `context_assembler` with task profiles instead of static 40/30/15/15 allocation
2. Implement `article_drafter` with structured output contracts
3. Implement inline support mapping for publication-bound drafts
4. Implement `adversarial_review`
5. Add build failure on:
   - Uncited factual assertions
   - Hallucinated context IDs
   - Blocker vulnerabilities

### Required Outputs
- `DraftSectionResponse`
- `AdversarialReviewResponse`
- Support-ID stripping for final publication render
- `review_draft` workflow

### Acceptance Tests
- Every factual assertion in a publication-bound section maps to valid context IDs
- Hallucinated context IDs fail the build
- Adversarial review returns structured vulnerability objects
- Drafts with blocker vulnerabilities cannot advance to assembly

### Why This Improves on the Current Spec
The current architecture spec envisions parallel drafting, critique, verification, and editor synthesis, but still assumes a narrative-first multi-agent editorial board. v2 keeps the critique function but forces structured outputs and hard validation.

---

## Phase 5 — Compatibility Bridge and Dual-Run Migration

**Duration:** 1 week

### Goal
Keep the current Woodward process alive while the new engine proves itself.

### Tasks
1. Build `bridge export_handoff`
2. Build `bridge ingest_manual_draft`
3. Build `bridge compare_dual_run`
4. Create one-way ingestion rules:
   - Webapp drafts enter as `pending_review`
   - No webapp prose becomes canonical automatically
5. Run side-by-side tests:
   - Webapp vs v2 figure verification
   - Webapp vs v2 section drafting

### Required Outputs
- Bridge CLI
- Dual-run comparison report
- Manual draft quarantine rules

### Acceptance Tests
- Export produces clean paste-ready packets
- Ingested manual drafts are noncanonical by default
- No ingested claim enters canon without source linking
- At least one figure workflow and one section workflow achieve parity

### Why This Phase Is Essential
The constraint is not "design the perfect future platform." It is "keep current Woodward usable while migrating away from webapp dependency."

---

## Phase 6 — Correspondence and Publication Control

**Duration:** 1 week

### Goal
Link claims, outreach, and final build.

### Tasks
1. Implement `reply_planner`
2. Implement `build_reply_packet`
3. Link `comms.db` threads to article IDs and claim IDs
4. Add response windows and publication-blocking dependencies
5. Implement `publication_gate`
6. Implement `assemble_article`

### Required Outputs
- Reply packet workflow
- Threaded correspondence model
- Article dependency registry
- Publication gate report
- Article build command

### Acceptance Tests
- Right-of-reply-dependent claims surface before build
- Publication-blocking claims stop final assembly
- Article 1 unresolved contract assertions cannot render as fact
- Article 2 cannot assemble if it mixes denominator logic improperly
- Final public render strips internal support scaffolding

### Why This Is Needed
The current architecture spec has `trackingdb` and correspondence concepts, but v2 makes them operationally tied to claims and article build status.

---

## Phase 7 — Audit, Backups, and Demotion of Webapp State

**Duration:** 3–5 days

### Goal
Make the new system durable enough that the webapp becomes optional.

### Tasks
1. Implement `run_nightly_audit`
2. Implement:
   - `verify_all_figures`
   - `verify_support_chains`
   - `detect_stale_figure_references`
   - `detect_orphaned_claims`
3. Add local backups
4. Add encrypted off-machine backups
5. Perform restore test
6. Reclassify webapp usage as:
   - Strategic editorial drafting
   - Hard writing passes
   - One-off reasoning
   - **Not:** project memory, figure store, or source-of-truth tracker

### Required Outputs
- Audit report
- Backup manifest
- Restore test log

### Acceptance Tests
- Nightly audit catches broken support chain
- Nightly audit catches banned figure references
- Restore test succeeds
- At least three recurring workflows run end-to-end without webapp memory dependence

---

# 5. The First 30 Days

## Week 1
- Canon schemas
- Canon hash
- `articles.yaml`
- `banned_claims.yaml`
- `banned_figures.yaml`
- Seed locked figures
- Choose SQLite schema and naming

## Week 2
- Build `ledger.db`
- Seed Article 2 and Article 3 numeric state
- Implement `verify_figure`
- Add derivation manifests

## Week 3
- Implement `vendor_alias_resolver`
- Implement `scope_reconciler`
- Implement `public_source_gate`
- Start `claims_registry.yaml`

## Week 4
- Implement `DraftSectionResponse`
- Implement `article_drafter`
- Implement `adversarial_review`
- Build `bridge export_handoff`

That 30-day sequence gets off the webapp fastest on the most fragile tasks.

---

# 6. Article-Specific Migration Order

## Wave 1 — Article 2 and Article 3 (First)

**Why:**
- Shared numeric substrate
- Highest figure-reuse density
- Strongest immediate payoff from deterministic verification

Article 2: board-presented $3,000,000 estimate vs. $10,970,973 actual Amergis spending.
Article 3: FY24–25 Object 7 budget-versus-actual overspend logic ($36,738,206 budgeted / $47,331,056 actual / $10,592,850 overage).

## Wave 2 — Article 1 (Second)

**Why:**
- Best test bed for blocked claims
- Best place to prove unresolved questions stay unresolved
- Strongest need for vendor-scope and contract-continuity fencing

Article 1 explicitly separates documented facts from "questions that remain," including the Amergis agreement architecture and the board authorization for the Maxim-to-Amergis transition.

## Wave 3 — Article 4 (Third)

**Why:**
- Best stress test for public-source gating
- Broadest mix of public reporting, state findings, and policy framing
- Date lock reuse and support-chain enforcement matter most here

Article 4 uses public reporting, OSPI facts, and the September 15, 2025 tentative-agreement date.

---

# 7. Roles in Enactment

## Architect
- Approves canon locks
- Decides supersession of figures/claims
- Approves reply packets
- Approves migration cutover by workflow

## Antigravity
- Extraction
- SQL derivations
- Scrape output normalization
- Reproducible numerical analysis
- **No narrative drafting authority**

## Woodward v2 Runtime
- Drafting
- Structured section generation
- Adversarial review
- Publication assembly
- Artifact generation

## Neo / Sentinel Equivalent Functions
Whether or not they remain separate personas, their functions become:
- Data verification
- Cross-check validation
- Parity comparison
- Audit confirmation

---

# 8. Enactment Rules — Hard-Coded

1. `ledger.db` is the sole monetary source of truth.
2. No claim may enter a publication-bound draft without a public-citable support chain.
3. No unresolved claim may silently promote itself to publishable fact.
4. No figure may originate in article prose.
5. No webapp output becomes canonical automatically.
6. Every publication-bound factual sentence must be support-mapped during build.
7. Build failures stop the run; they do not degrade into guesswork.

---

# 9. The Exact First Sprint

Deliver these and stop:

- `canonical/figures.yaml`
- `canonical/vendor_scope.yaml`
- `canonical/articles.yaml`
- `canonical/claims_registry.yaml` — initial seed
- `ledger.db` with Article 2 and Article 3 numeric state
- `figure_verifier`
- `vendor_alias_resolver`
- `scope_reconciler`
- `public_source_gate`
- `bridge export_handoff`

If that sprint lands cleanly, Woodward immediately gains:
- Canonical numeric enforcement
- Blocked-claim enforcement
- Exportable handoff packets
- A real path away from webapp-as-memory

---

# 10. Definition of Successful Enactment

Plan v2 is successfully enacted when all of these are true:

- The current locked figures are replayable from declared derivations
- The current four article outputs remain usable throughout migration
- Unresolved Article 1 and Article 2 governance questions remain blocked until supported
- Articles 2 and 3 can regenerate numeric sections without prose-originated math
- Article 4 can pass a public-source publication gate
- Manual webapp outputs are quarantined, not canonized
- The webapp is no longer required to hold project state

---

# 11. Next Executable Deliverable

A **redline enactment memo** that maps:

| Current `WOODWARD_ARCHITECTURE_SPEC.md` Component | Action | v2 Replacement | Priority | Migration Dependency |
|-----------------------------------------------------|--------|----------------|----------|----------------------|
| (component) | keep / rename / delete / replace | (replacement) | (P0–P3) | (dependency) |

That is the cleanest bridge from strategy to build.

---

*Source: Woodward Core v2 enactment plan — anchored to current architecture spec, isolation file, handoff, and article files. Generated 2026-03-12.*
