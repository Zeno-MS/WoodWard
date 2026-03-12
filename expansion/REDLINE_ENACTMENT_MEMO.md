# Redline Transformation Memo — Woodward v2 Enactment

This memo maps the current Woodward architecture into the v2 migration target. It is a build document, not an editorial document.

Its job is to answer, for each major part of the current system:

- keep
- rename
- delete
- replace
- defer

It assumes the current controlling constraints remain in force:

- The current workflow is Architect → Neo / Sentinel / Chief / Woodward, with Antigravity in the data lane only and no AI output treated as a primary source
- Publication must remain grounded in publicly supportable sources only, with no motive language and no unsupported extrapolation
- The fresh-chat handoff baselines remain locked unless explicitly superseded, including FY24–25 staffing-vendor total **$13,326,622**, cumulative baseline **$32.1M**, and the Article 4 date **September 15, 2025**
- The isolation rules remain mandatory: Woodward may borrow Cicero's architectural patterns, but not its legal prompts, skills, schemas, citation logic, or legal-domain embeddings by default

---

## 1. Executive Verdict

The current architecture spec is useful as a **legacy design reference**, but it should not be implemented as written. It is still a Cicero-shaped investigative platform: multi-brain, Neo4j-heavy, pipeline-first, and broader than the current Woodward project actually needs. The isolation file is mostly good and should be kept as the standing guardrail document. The v2 target should be a smaller core centered on canon, deterministic workflows, and compatibility-first migration.

The transformation is:

- **Keep** the guardrails, editorial lane rules, and anti-hallucination posture
- **Replace** the runtime core
- **Rename** Cicero-adjacent structures that invite architectural drift
- **Defer** OPSEC-heavy local scrubber work unless and until it becomes a practical need

---

## 2. Top-Level Disposition

### Keep
- Isolation boundaries as mandatory pre-build guardrails
- Payments-as-canonical principle
- Article assembly and evidence-package concepts
- Anti-hallucination requirements
- Role separation between data verification, editorial judgment, and writing
- Local-first project posture
- API/server pattern in broad concept only

### Rename
- `paymentsdb` → `ledger.db` semantics
- `casedb` → `records.db`
- `trackingdb` → `comms.db`
- `skillsdb` → remove as a primary runtime store; convert to code/services plus optional methodology artifacts
- `editorial_board` language may remain conceptually, but not as the primary implementation unit

### Replace
- Graph-centered multi-database runtime
- Static 40/30/15/15 context allocation
- Brains/skills/pipelines as the main execution unit
- End-stage redaction-first emphasis
- Late database population sequence
- Webapp/chat memory as de facto project state

### Delete
- Any Cicero-derived legal content, naming, citation logic, or node/relationship assumptions
- Any legal formatting inheritance in memo/article assembly
- Any plan to let article prose, graphs, or model memory originate canonical figures

### Defer
- Heavy local semantic scrubber / airgap
- Zero-retention/provider-policy engineering as a top-tier milestone
- Richer UI/webview work
- Any graph projection work beyond optional later exploration

---

## 3. Redline by Section of the Current Architecture

### Section 1 — System Overview

**Current:** The spec defines Woodward as a local-first investigative journalism AI platform designed to mirror Cicero's Council-of-Models, BrainBase, multi-database, and skills architecture, with FastAPI, asyncio, Neo4j, LanceDB, and sqlite3.

**Action: Replace**

**v2 rewrite:** Reframe the system overview around these principles:
- Woodward Core v2 is a compatibility-first migration system
- Project state lives in canon + SQLite + run artifacts
- LLMs are stateless workers, not the place where the project lives
- Graphs are optional and derivative, not authoritative
- The primary unit of execution is the workflow, not the brain

**Why:** The current framing encourages "port Cicero, then adapt," when the real requirement is "preserve Woodward's current outputs while shrinking drift and webapp dependence."

---

### Section 2 — Directory Structure

**Current:** The current tree includes `investigation_config.json`, `.env`, `CONTEXT_HANDOFF.md`, agents, orchestration, adapters, multiple DB adapters, validators, orchestration YAML pipeline support, and various services and utilities.

**Action: Replace substantially**

**Keep:**
- `src/core/`
- Provider adapters in some form
- Ingestion modules in some form
- Article assembly in some form
- Tests
- API entry point in some form

**Rename / replace:**
- Add `canonical/`
- Add `db/ledger.db`, `db/records.db`, `db/comms.db`
- Add `schemas/`
- Add `bridge/`
- Add `runs/`
- Replace `CONTEXT_HANDOFF.md` as state with canonical files + run manifests
- Keep `.env.example`, not only `.env`

**Delete or demote:**
- Any expectation that the directory tree itself is proof of architectural completeness
- Orphan modules without a workflow contract

**Why:** The current tree is broader than the current need and contains structural ambiguity. The v2 tree must reflect runtime truth, not aspirational breadth.

---

### Section 3 — Database Architecture

**Current:** The current architecture uses multiple named stores: `paymentsdb` as canonical dollar truth, `evidencedb`, `casedb`, `skillsdb`, `trackingdb`, LanceDB.

**Action: Replace**

**v2 mapping:**
- `paymentsdb` principle survives, but the runtime store becomes `ledger.db`
- `evidencedb` + much of `casedb` collapse into `records.db`
- `trackingdb` becomes `comms.db`
- `skillsdb` is removed as a primary data store
- LanceDB remains retrieval-only

**Hard rule:** `ledger.db` is the sole monetary source of truth. Every publication figure must either come directly from `ledger.db`, or be a declared derivation whose SQL/query is stored and replayable.

**Why:** The current spec correctly says payments are canonical, but still leaves too many neighboring truth surfaces alive. v2 hardens the principle.

---

### Section 4 — Agents / Brains / Modules

**Current:** The architecture and isolation docs still assume an Editorial Board / Council pattern, 15 Woodward prompts, module/submodule/brain structure, and named agents including Source Protector, Data Analyst, Investigator, Editor, Chief, and OSINT Researcher.

**Action: Keep conceptually, replace operationally**

**Keep** as editorial metaphors and prompt roles:
- Writer
- Verifier / source verifier
- Editor / adversarial reviewer
- Chief
- OSINT-style retrieval roles

**Replace** — the primary implementation unit becomes the workflow:
- `verify_figure`
- `draft_section`
- `review_draft`
- `build_reply_packet`
- `assemble_article`
- `run_nightly_audit`

**Why:** The current project's problem is not lack of personas. It is state drift and execution sprawl. Workflows are easier to test, migrate, and trust.

---

### Section 5 — Orchestration Layer

**Current:** The current spec uses `router.py`, `coordinator.py`, `context.py`, YAML pipeline execution, and an editorial board pipeline in Phase 3 with parallel drafting, critique, verification, and synthesis.

**Action: Keep partially, replace core behavior**

**Keep:**
- Router concept
- Coordinator concept
- Context assembly concept
- Adversarial review concept

**Replace:**
- YAML pipelines as the main execution substrate
- Agent-first orchestration
- Static token-budget allocation
- "Editorial board" as the default execution model for all tasks

**v2 rewrite:** Use an API-first orchestrator with strict contracts:
- Task type
- Allowed sources
- Injected locked figures
- Expected output schema
- Failure rules
- Support mapping requirements

**Why:** The current orchestration is elegant but too broad. v2 needs a narrower and more deterministic execution core.

---

### Section 6 — Skills / Validators / Methodology Layer

**Current:** The isolation doc correctly says Woodward skills must be built from scratch and not fork legal skills. The architecture spec includes figure verification, redaction, evidence grading, and defamation checking.

**Action: Split and reorder**

**Keep and elevate:**
- `figure_verifier`
- Source verification
- Evidence grading
- Adversarial / legal-risk calibration in journalistic mode

**Replace** — move from skill-graph centrality to code services:
- `vendor_alias_resolver`
- `scope_reconciler`
- `claim_support_checker`
- `public_source_gate`
- `publication_gate`

**Defer:**
- Semantic local scrubber / heavy Source Protector logic
- End-stage redaction as a central milestone

**Why:** Given current priorities, provenance and canon enforcement matter more than building a heavyweight privacy gate first.

---

### Section 7 — Context Builder

**Current:** The isolation file explicitly preserves a fixed 40/30/15/15 allocation for context building.

**Action: Replace**

**v2 rewrite** — use task profiles instead:
- Figure verification → ledger-heavy
- Article draft → records + ledger + claims
- Right-of-reply → comms + claims + records
- Adversarial review → records + claims + ledger
- Tracking review → comms-heavy

**Why:** A fixed global ratio is too blunt for the actual task surface.

---

### Section 8 — Assembly Engine

**Current:** The isolation file is strong here: do not port Cicero's DOCX/RAP assembly logic; build Markdown article engine, evidence package, and memo engine from scratch.

**Action: Keep, with clarification**

**Keep:**
- Markdown-first article assembly
- Evidence package assembly
- Memo engine as a journalism/admin artifact, not legal pleading logic

**Add:**
- Publication gate before final render
- Strip internal support IDs from public output
- Block unresolved claims from final assembly

**Why:** This is one of the strongest parts of the isolation file and is already aligned with v2.

---

### Section 9 — Ingestion Pipeline

**Current:** The isolation file correctly prohibits `eyecite` and legal citation extraction, and points Woodward toward warrant registers, BoardDocs, OSPI reports, and public reporting. It also notes the need for table-oriented PDF extraction.

**Action: Keep, reorder**

**Keep:**
- Public financial and reporting ingestion focus
- No legal citation tooling
- Journalistic / financial chunking, not legal chunking

**Replace:** Move ingest much earlier. Do not wait until late phases to populate the core stores.

**Add:**
- `legacy_export_ingest.py`
- Article ingest
- Derivation ingestion for locked figures
- Source classification on ingest: `public`, `public_quotable`, `blocked_private`, `unresolved`

**Why:** The current phase order is backwards for testable migration.

---

### Section 10 — Phase Plan / Build Sequence

**Current:** The spec's current build order places brains and skills earlier, editorial board pipeline in weeks 5–6, and database population in weeks 7–8.

**Action: Replace**

**v2 build order:**
1. Canon freeze
2. Database kernel
3. Figure verification
4. Vendor scope + alias logic
5. Public-source gate
6. Claims registry + support checking
7. Drafting contracts
8. Adversarial review
9. Bridge tools
10. Publication assembly
11. Audit + backups

**Why:** The fastest way off webapp dependence is to stabilize figures and claims before building elaborate orchestration.

---

### Section 11 — What to Tell Claude Code

**Current:** The spec tells Claude Code to start by building the full directory tree, requirements, config, model registry, base client, brain loader, and SQLite adapter wrapping the existing Woodward DB, using Cicero patterns but no legal domain content.

**Action: Replace**

**v2 instruction:** Tell Claude Code to build only the minimum migration kernel first:
- Canonical schemas
- `ledger.db`
- `records.db`
- `comms.db`
- `figure_verifier`
- `vendor_alias_resolver`
- `scope_reconciler`
- `public_source_gate`
- `bridge export_handoff`

**Why:** The current instruction encourages scaffolding breadth before operational truth.

---

## 4. Redline by Isolation Boundaries

### "The Rule"
**Current:** Borrow architectural patterns, not legal domain content.
**Action: Keep exactly.** This is the right rule.

---

### BrainBase Prompts
**Current:** Write fresh prompts from scratch and do not port Stasis, CREAC, RAP, CJC, holdings/rulings/motions/briefs/appellate language.
**Action: Keep, add one clause.**
Add: do not let IDEA/IEP or SAO memo work default into legal-brief reasoning or pleading tone.
**Why:** That is one of the remaining contamination backdoors.

---

### Skills
**Current:** Do not fork legal skills; build Woodward skills from scratch.
**Action: Keep, but reinterpret.**
Skills should become deterministic services or workflow helpers — not a graph-backed skill taxonomy that becomes a second state model.

---

### Database Schemas / Node Types
**Current:** Do not reuse Cicero legal node types; use Woodward's own types like Payment, Vendor, Contract, BudgetLine, Article, Dossier, Claim, Contact, Deadline, AgencyResponse.
**Action: Keep in spirit, replace in implementation.**
The domain model is right. The storage shape should shift from graph-first to SQLite-first.

---

### Embeddings
**Current:** Do not assume kanon-2; default to `text-embedding-3-small` or `large` unless testing proves otherwise.
**Action: Keep exactly.**
Add one enforcement rule: assert embedding dimensionality and namespace at runtime.

---

### Citation Verification Meaning
**Current:** Do not port Cicero citation verification; build source verification and figure verification from scratch.
**Action: Keep and elevate.** This becomes one of the central v2 services.

---

### Agent Names
**Current:** Do not use Logician, Historian, Orator, Judge; use Data Analyst, Investigator, Writer, Verifier, Source Protector, Editor, Chief, OSINT Researcher.
**Action: Keep conceptually, demote operationally.**
Fine for language and prompts. Do not let these names determine code architecture.

---

### Constants and Patterns
**Current:** Do not carry over Cicero constants; Woodward needs evidence tags, redaction patterns, canonical investigation figures, and fiscal year rules.
**Action: Keep, but move canonical figures out of constants and into canon files.**
That is a key v2 change.

---

### Assembly Engine
**Current:** Do not port DOCX/RAP logic; build article, evidence, and memo engines from scratch.
**Action: Keep exactly.**

---

### What Can Be Shared
**Current:** `knight-lib` adapters/config/models can be shared; async client, brain loader, council/editorial board pattern, router, coordinator, context builder, config, and model registry patterns can be ported with domain content replaced.
**Action: Keep narrowly.**

Use shared infra for:
- Adapters
- Config base
- Pydantic base models
- Provider client patterns (maybe)

Do not automatically port:
- Council/editorial board runtime as the main engine
- Static context weights
- Graph-heavy assumptions

---

### Verification Checklist
**Current:** The isolation file ends with a verification checklist before code is committed.
**Action: Keep, expand.**

Add v2-specific checks:
- `ledger.db` is sole monetary truth
- No blocked claims can assemble
- Every publication-bound factual sentence has a support map
- Manual webapp output is quarantined by default

---

## 5. Concrete Keep / Rename / Delete / Replace Summary

| Item | Action | Notes |
|------|--------|-------|
| `WOODWARD_ISOLATION_BOUNDARIES.md` | **Keep** | Mandatory guardrail file |
| Anti-hallucination architecture | **Keep** | Core requirement |
| Local-first posture | **Keep** | |
| Article engine / evidence package | **Keep** | |
| Source/figure verification concepts | **Keep** | Elevate to central services |
| Architect / Chief / Neo / Sentinel / Woodward lanes | **Keep** | |
| `paymentsdb` | **Rename** → `ledger.db` | |
| `casedb` | **Rename** → `records.db` | |
| `trackingdb` | **Rename** → `comms.db` | |
| `memo_engine.py` | **Keep, document** | Journalism/admin only |
| `skillsdb` | **Delete** | Not a primary runtime store |
| Legal citation/authority inheritance | **Delete** | |
| Graphs as canonical truth | **Delete** | |
| Late database population | **Delete** | Replace with early ingest |
| Static context builder (40/30/15/15) | **Replace** | Task-profiled allocator |
| Brains/pipelines as primary runtime | **Replace** | Workflows/contracts |
| End-stage scan emphasis | **Replace** | Provenance/publication gate emphasis |
| Generic council/editorial board runtime | **Replace** | Smaller deterministic services |
| Local semantic scrubber | **Defer** | |
| Heavy Source Protector / airgap | **Defer** | |
| Richer UI/webview | **Defer** | |
| Optional graph projections | **Defer** | |

---

## 6. Immediate Enactment Order

1. Freeze canon from current handoff rules and active article set
2. Build `ledger.db` and declared derivations
3. Build `figure_verifier`
4. Build `vendor_alias_resolver` and `scope_reconciler`
5. Build `records.db` and `public_source_gate`
6. Build `claims_registry.yaml` and support checker
7. Build `article_drafter` with structured output + support mapping
8. Build `adversarial_review`
9. Build `bridge export_handoff` and `bridge ingest_manual_draft`
10. Build publication gate and final assembly
11. Build audit and backups

---

## 7. Final Directive

Use the current architecture spec as a **component inventory**, not as the implementation blueprint.

Use the isolation boundaries as the **mandatory contamination guardrail**.

Use v2 as the **actual runtime and migration target**.

That is the cleanest path that preserves the current Woodward project while materially improving truth control, provenance discipline, and migration away from webapp dependence.

---

**Next step:** Turn this memo into a **Claude Code build instruction set** — one concrete build task per phase, with file targets, acceptance tests, and dependency order.

*Generated: 2026-03-12*
