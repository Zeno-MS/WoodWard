# Assessment Review — WoodWard Guidance Documents (March 6, 2026)

## Purpose

This document is an independent, code-verified review of the five assessment files placed in `WoodWard/guidance/` on March 6, 2026. It evaluates each assessment against the **actual codebase, filesystem, and operational reality** of the WoodWard project.

The goal is not to agree or disagree generically, but to determine:

1. Which observations are accurate and actionable
2. Which observations are accurate but misleading in priority or framing
3. Which recommendations would **break existing valid processes**
4. Which recommendations reveal that **the assessor missed something already in place**

---

## Documents Reviewed

| Document | Size | Focus |
|----------|------|-------|
| `WOODWARD_APP_ASSESSMENT_2026-03-06.md` | 586 lines | Overall system evaluation |
| `JOURNALIST_HANDOFF_ASSESSMENT_2026-03-06.md` | 53 lines | Evidence package readiness |
| `WOODWARD_BUILD_PLAN_2026-03-06.md` | 554 lines | Phased development roadmap |
| `WOODWARD_EXECUTION_CHECKLIST_2026-03-06.md` | 499 lines | Tactical implementation queue |
| `WOODWARD_IMPLEMENTATION_PLAN_2026-03-06.md` | 729 lines | Detailed implementation sequence |

---

## Overall Impression

The assessor clearly spent meaningful time with the repo and produced work that is more thoughtful than a typical AI assessment. The technical observations about the code are largely accurate. The strategic framing — that WoodWard is a strong research backend without an app layer — is a fair characterization.

**However, the assessments have a systematic blind spot.** They repeatedly describe WoodWard as if its only future is to become a general-purpose investigative journalist platform. While it is true that WoodWard started as a single-investigation forensic evidence system for the VPS staffing vendor story, the **investigation is expanding** — with plans to find additional data sources and create mechanisms for FOIA/PRR handoffs. That expansion changes which recommendations are premature and which are genuinely useful.

With that context, the assessments split into three categories:

1. **Recommendations that are correct and now timely** — things like improving data source tracking, structuring ingestion for repeatability, and formalizing the records-request pipeline.
2. **Recommendations that remain premature** — full web UI, React frontend, multi-user collaboration features, and complex service layers.
3. **Gaps the assessments never addressed** — FOIA request generation and tracking, new data source discovery and ingestion workflows, and making the system easier for collaborators to hand off records requests.

None of the assessments mention public records requests, FOIA strategy, or data acquisition workflows at all. That is a significant omission given that the investigation already has a fully drafted [6-part PRR](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/workspaces/results/PUBLIC_RECORDS_REQUEST.md), a [Phase 1 task list](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/PHASE_1_TASKS.md) tracking outstanding records requests, multiple `[UNRESOLVED]` markers in articles tied to PRR-dependent data, and a Clark County Treasurer response that directed the investigation to their GovQA portal.

---

## Assessment-by-Assessment Review

### 1. `WOODWARD_APP_ASSESSMENT_2026-03-06.md`

#### What the assessor got right

- **"WoodWard has a good backend brain, but almost no finished app body."** Correct. There is no web UI, no API layer, no frontend. The system is script-driven and filesystem-organized. That is accurate.

- **Hardcoded credentials.** Verified. `ingest_payments.py` (line 22-23), `ingest_board_governance.py` (line 6-7), and `verify_ingestion.py` (line 3-4) all hardcode `NEO4J_URI` and `NEO4J_AUTH` directly. The `.env` file exists but is not loaded by the scripts — they duplicate the values. This is a real issue.

- **Governance parsing is heuristic and fragile.** Verified. `ingest_board_governance.py` uses regex-based date extraction (lines 9-27), pattern-matching vote extraction (lines 29-40), and keyword-based vendor detection (lines 42-54). The vote logic defaults to "Unknown/Not Specified" and assumes all unknown votes are unanimous YES for board member linking (lines 193-198). This is correctly identified as prototype-grade.

- **Neo4j is now a working component.** Verified. The `docker-compose.yml` runs `woodward-neo4j` on ports 7475/7688 with working memory config and APOC plugins. The assessor's observation that this changes Neo4j from aspirational to operational is correct and important.

- **Script sprawl is real.** `scripts/analysis/` contains 39 files. Many are one-off exploratory scripts (`find_fish_blechschmidt.py`, `debug_search.py`, `inspect_sqlite.py`). The assessor is right that this creates maintenance burden over time.

#### What the assessor got wrong or missed

- **"There is no durable claims system."** This is technically true — there is no `Claim` model in code — but it misses the editorial reality. The four articles in `06_Articles/` *are* the claims system in practice. Each article is structured around specific, numbered assertions with citations back to evidence. That said, with the investigation expanding, a lightweight claims tracker (even a structured markdown or CSV file mapping each major assertion to its evidence status, source documents, and `[UNRESOLVED]` tag) would become genuinely useful for managing the growing number of threads. The assessor's full Pydantic-model-in-Neo4j approach is still overkill, but the underlying need becomes real at scale.

- **"Right-of-reply tracking is a folder convention."** This is the assessor's biggest miss. The right-of-reply system in `07_Right_of_Reply/` is **substantially more than a folder convention**:
  - `INDEX.md` is a structured 24-row table tracking every request: status, date, recipient, and subject
  - `Sent_Requests/` contains 20 individual files with full email text, headers, and timestamps
  - `Received_Responses/` contains 4 response files with full text
  - There is a **dedicated agent workflow** at `.agents/workflows/ospi_response_logging.md` that defines a formal protocol for ingesting new responses, updating the index, and maintaining the log
  - The workflow specifies how to analyze response content, extract evidence value, update outstanding question counts, and file source material

  This is not a perfect database, but calling it "a folder habit" is dismissive. It is a tracked, indexed, workflow-backed process that is actively managing 20+ communications across multiple counterparties. For a single investigation, this is adequate.

- **"There is no provenance UI."** True but misleading. The provenance *data* is solid: `verify_ingestion.py` runs 5 structured investigative queries that trace payments → vendors → fiscal years → governance → board meetings. The `EXTRACTED_FROM` relationship on every Payment node links back to the source warrant register. The `IN_FISCAL_YEAR` relationship links to fiscal year context. The vendor normalization module (`vendor_normalization.py`) is a genuine shared library with alias chains, parent company tracking, and explicit notes about which entities are investigation targets vs. unrelated. It is correct that there is no UI for this, but the data-level provenance is stronger than the assessment implies.

- **"No formal test coverage around ingestion correctness."** Partially wrong. `ingest_payments.py` (lines 131-139) runs post-ingestion validation that reports total payment counts, total amounts, vendor counts, and document counts. `verify_ingestion.py` runs 5 named investigative queries that effectively function as integration tests (spending trajectories, rebrand handoff evidence, budget tracking, superintendent salary comparison, governance paths). These are not pytest unit tests, but they are not nothing.

#### Recommendations that would break things

- **"Keep SQLite only as staging/archive input."** Dangerous. `data/woodward.db` is 33MB and is the **primary source of truth** for payment records. `ingest_payments.py` reads from SQLite to populate Neo4j. If SQLite were demoted prematurely, the ingestion pipeline breaks. SQLite is not an optional archive — it is the canonical tabular store from which the graph is built. As the investigation expands and new data sources come in, SQLite becomes *more* important as the tabular staging ground, not less.

- **"Replace script sprawl with commands or services."** Correct in principle, and with investigation expansion this becomes a more valid concern. As new data sources are added, having 50+ one-off scripts gets genuinely hard to manage. The right move is not a FastAPI service layer, but a simpler consolidation: a `Makefile` or `scripts/run.sh` wrapper that documents which scripts to run and in what order, as a practical middle ground.

---

### 2. `JOURNALIST_HANDOFF_ASSESSMENT_2026-03-06.md`

#### What the assessor got right

- **"80% to 85% ready."** This is a fair estimate. The evidence package is comprehensive but has known gaps.

- **"Article 1 and Article 2 are strong."** Verified. `article_1_the_austerity_paradox.md` (32KB) and `article_2_the_accountability_void.md` (23KB) are full-length investigative articles with substantial citation depth.

- **"The package language sometimes overstates completeness."** Valid editorial caution. The distinction between "verified" and "pending secondary verification" matters in handoff packaging.

- **"Missing VPS 2023-24 F-195/F-195F source files."** Worth checking. `documents/F195/` contains 19 files, but whether the specific 2023-24 actuals are present needs verification before handoff.

#### What the assessor got wrong or missed

- **"A claim-to-source exhibit index is needed."** Useful but not a blocker. The articles already cite sources inline. An exhibit index is polish, not prerequisite.

- **"A district-response status memo is needed."** Already substantially covered by `INDEX.md` in `07_Right_of_Reply/`. The index shows exactly who was contacted, when, and who responded. What it does *not* show in structured form is the content of non-responses (i.e., "did not reply" entries). A one-page summary distilling INDEX.md into a status memo would take 30 minutes — this is not a structural gap.

- **"Full Amergis contract history"** and **"rate-escalation timeline."** These are public-records-request items, not items the system architecture can produce. The assessor conflates "data WoodWard should contain" with "system capability WoodWard is missing." That said, these are exactly the kinds of items that a FOIA tracking system should surface as outstanding requests — the assessor identified real gaps but attributed them to the wrong cause.

---

### 3. `WOODWARD_BUILD_PLAN_2026-03-06.md`

#### Overall assessment

This is a competent software architecture plan for building an investigative journalism platform from scratch. With investigation expansion planned, more of this plan becomes relevant than it would for a one-and-done handoff — but it is still significantly overbuilt for the actual need.

#### What the assessor got right

- **Phased approach.** The sequence (stabilize → model → service → workflow → UI) is sound engineering practice.

- **"Do not try to build a broad newsroom platform."** Good instinct, but the plan then proceeds to describe a 6-phase, 8-12 week build that IS a broad platform: FastAPI backend, React frontend, user roles, annotations, version history, contradiction detection, stale-claim alerts. That is product-company thinking.

- **Store responsibility definitions.** The assessment's proposed store-responsibility split (Neo4j for relationships, LanceDB for semantic search, filesystem for source documents, SQLite for staging) is reasonable and matches the implied architecture that already exists.

#### What the assessor got wrong

- **Timeline: "8 to 12 weeks."** For a solo investigator who is simultaneously doing journalism, this remains unrealistic. Even with expansion plans, the build should be incremental and driven by investigative needs, not by a product roadmap.

- **Phase 1 claim model with status enums, owner fields, legal review status, and article refs.** With investigation expansion, a *lightweight* version of this becomes useful — not a full Pydantic model with Neo4j persistence, but something like a structured CSV or markdown table mapping claims to status, source documents, and outstanding PRRs. The assessor's instinct is right; the proposed implementation weight is wrong.

- **"Right-of-reply should be a system feature, not a folder convention."** The assessor missed that there IS a system feature — the OSPI response logging workflow provides a defined protocol with specific file paths, analysis steps, and index update procedures. It is just implemented as an agent workflow rather than a web application. However, as the investigation expands to additional counterparties, the current `INDEX.md` table will need to be supplemented — potentially with a dedicated `FOIA_TRACKER.md` for public records requests (see new section below).

---

### 4. `WOODWARD_EXECUTION_CHECKLIST_2026-03-06.md`

#### Overall assessment

This is the most operationally dangerous document in the set. It prescribes a 13-step implementation sequence that would consume weeks of engineering time and produce zero investigative output.

#### What the assessor got right

- **Step ordering is correct if you were building a product.** App skeleton → config → models → repositories → services → routes → workflows → UI → exports → tests is textbook clean architecture.

#### What would break things

- **Step 5: "Mine existing logic from `workspaces/Cicero_Clone/src/adapters/neo4j.py`."** This file is part of an entirely different project (Cicero, a RAG system for case law research). It is in a `Cicero_Clone` workspace inside WoodWard. Using it as a foundation for WoodWard's repository layer would create a dependency on a separate project's code patterns and potentially import Cicero's schema assumptions, which are irrelevant to WoodWard's investigation domain.

- **Step 10: "Refactor `ingest_payments.py`, `ingest_board_governance.py`, `ingest_salaries.py`, `load_f195_v3.py` into app jobs."** These scripts work today and are actively used. Refactoring them into a `app/jobs/` module means they must be re-tested, the import paths change, and any existing workflow or documentation that references `scripts/loaders/` becomes stale. This is unnecessary churn for a system that is actively producing results.

- **Step 11: "Build frontend, create `frontend/package.json`."** This introduces an entirely new technology layer (Node.js, React) into a Python investigation project. The investigator would need to manage npm dependencies, a build pipeline, and a separate dev server. For a single-user local tool, this adds complexity with no proportional benefit before handoff.

#### What the assessor missed

- `scripts/verify_ingestion.py` already provides repeatable validation queries. The checklist calls for building `tests/integration/test_neo4j_health.py` and `tests/integration/test_payment_ingest.py` — those already exist in simpler form.

- The `.env` file already centralizes configuration. The scripts don't use it (that's a real bug), but the config source exists. Step 2 should be "make the scripts load from `.env`" — not "create a new `app/config.py` Pydantic model."

---

### 5. `WOODWARD_IMPLEMENTATION_PLAN_2026-03-06.md`

#### Overall assessment

This is the build plan restated with more implementation detail. With investigation expansion in mind, more of this becomes directionally relevant, but the implementation weight remains disproportionate to the operational need.

#### What the assessor got right

- **"Do not rebuild everything at once."** Good principle, but the document then describes 10 phases that would rebuild everything at once.

- **"Files remain canonical source artifacts."** Correct and important. The filesystem-as-source-of-record pattern is appropriate for this domain.

- **Sprint 1 task list.** If WoodWard were pivoting to product development, this would be the right first sprint.

#### What the assessor got wrong

- **"SQLite should stop being the main analysis surface."** As noted above, SQLite *is* the canonical source for payment records. The graph is derived from it. Demoting it is premature and risky.

- **"Stop relying on `workspaces/Cicero_Clone/src/` as if it were the app core."** Nobody is relying on it as the app core. It exists in the workspace as reference code from a related project. The assessor appears to have interpreted its presence as an architectural dependency, when it is actually just a code sample that lives in the directory tree.

- **Phase 6: "Move shared logic into app modules — date normalization, vendor normalization."** `vendor_normalization.py` is ALREADY a shared module. It is imported by `ingest_payments.py` at line 13. Moving it to `app/shared/vendor_normalization.py` would break the existing import without adding any new capability.

---

## Summary of Findings

### Things the assessor got right

| Finding | Verified? | Severity |
|---------|-----------|----------|
| Hardcoded credentials in scripts | ✅ Yes | Medium — `.env` exists but is unused by scripts |
| No web UI or API layer | ✅ Yes | True but premature as a priority |
| Governance parsing is heuristic | ✅ Yes | Known limitation, documented in code comments |
| Script sprawl in `scripts/analysis/` | ✅ Yes | 39 files, many one-off |
| Neo4j is now operational | ✅ Yes | Important infrastructure milestone |
| Strong editorial methodology | ✅ Yes | 4 full articles, structured evidence package |
| No formal test suite | ✅ Partially | Validation scripts exist but not in pytest |

### Things the assessor missed

| Missed item | What actually exists |
|-------------|---------------------|
| Right-of-reply is "just a folder" | `INDEX.md` with 24 tracked comms, agent workflow protocol, structured send/receive directories |
| No ingestion validation | `verify_ingestion.py` with 5 named investigative queries, post-ingest count/sum reporting |
| No shared modules | `vendor_normalization.py` is already a shared library imported by `ingest_payments.py` |
| No configuration source | `.env` exists with all connection parameters (scripts just don't use it) |
| Cicero_Clone is an architectural dependency | It is a reference workspace, not a dependency |

### Recommendations that would break WoodWard

| Recommendation | Why it breaks things |
|----------------|---------------------|
| Demote SQLite to staging/archive only | It IS the canonical payment source; Neo4j is derived from it |
| Refactor loader scripts into `app/jobs/` | Breaks working import paths, documentation, and workflows |
| Move `vendor_normalization.py` to `app/` | Breaks `ingest_payments.py` import at line 13 |
| Add React frontend | Introduces Node.js dependency stack into a Python project pre-handoff |
| Build 10-phase implementation plan now | Delays investigation handoff by months with no direct investigative benefit |
| Mine code from `Cicero_Clone` adapter | Wrong project; different domain schema and assumptions |

---

## What the Assessments Entirely Missed: FOIA/PRR Infrastructure

None of the five assessments mention public records requests, FOIA strategy, or data acquisition workflows. This is the biggest blind spot in the entire assessment package, especially given that:

- A fully drafted [6-part public records request](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/workspaces/results/PUBLIC_RECORDS_REQUEST.md) already exists, targeting staffing agency contracts, itemized invoices, HR vacancy data, purchasing authority documents, inter-fund borrowing resolutions, and F-196 financial statements.
- [PHASE_1_TASKS.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/PHASE_1_TASKS.md) lists "File public records request" as an outstanding task.
- Multiple `[UNRESOLVED]` markers in the articles are explicitly tied to PRR-dependent data (e.g., the Amergis MSA needed to calculate the actual agency premium).
- The Clark County Treasurer's response in `20_cnty_treasurer_general_delivery_right_of_reply.md` directed the investigation to their GovQA portal — a structured intake system with its own tracking requirements.
- Existing download scripts (`download_sao_audits.py`, `download_sao_direct.py`, `download_camas.py`, `download_tacoma.py`, `fetch_peer_f195s.py`) show that WoodWard already has an active data-acquisition layer that the assessments never acknowledged.

For an expanding investigation, the FOIA/PRR pipeline is the highest-value infrastructure gap — not a service layer or a React frontend.

---

## What Should Actually Happen Next

With investigation expansion planned, the priority list shifts. Some assessor recommendations that were premature for a one-off handoff become relevant now. But the new requirements around FOIA and data source expansion come first.

### Tier 1: Immediate priorities (high-value, low-cost)

1. **Fix the `.env` usage.** Make `ingest_payments.py`, `ingest_board_governance.py`, and `verify_ingestion.py` load from `.env` instead of hardcoding credentials. This is a 20-minute fix that addresses a real security concern without disrupting anything.

2. **Create a FOIA/PRR tracker.** A structured `FOIA_TRACKER.md` (or a simple SQLite table) in the evidence package that tracks:
   - Request ID
   - Target agency (VPS, OSPI, Clark County, SAO)
   - Date filed
   - Statutory deadline (5 business days for WA PRA)
   - Status (draft / sent / acknowledged / partial response / complete / appealed / denied)
   - Response summary
   - Documents received (linked to file paths)
   - Outstanding follow-ups
   - Related claims/articles

   This would unify the existing PRR draft, the right-of-reply INDEX.md, and the PHASE_1_TASKS.md tracking into a single operational view. The OSPI response logging workflow (`.agents/workflows/ospi_response_logging.md`) should be extended to cover all PRR responses, not just OSPI.

3. **Create a FOIA request handoff template.** A standardized template that makes it easy to generate new RCW 42.56 requests for different agencies and record types. The existing PRR at `PUBLIC_RECORDS_REQUEST.md` is a strong model — what is needed is a parameterized version where you can swap in the agency, record types, date ranges, and entity names. This makes it trivial to generate PRRs for peer districts (Evergreen, Battle Ground, Camas) or new agencies.

4. **Generate the exhibit index.** The assessor correctly identified this as a gap. A simple script that reads the article files and produces a claim-to-source table would be high-value, low-cost.

5. **Distill `INDEX.md` into a one-page response status memo.** Not a new system — just a summary document extracted from the data that already exists.

### Tier 2: Investigation expansion infrastructure

6. **Create a data source registry.** As the investigation expands to new sources, there should be a single document (or lightweight database table) that inventories:
   - Every data source WoodWard has obtained (warrant registers, F-195s, SAO audits, board minutes, etc.)
   - Date range covered
   - How it was obtained (OSPI portal, PRR, web scrape, manual download)
   - Ingestion status (raw / loaded to SQLite / loaded to Neo4j / loaded to LanceDB)
   - Known gaps (missing years, missing file types)

   This replaces the current pattern where source coverage knowledge lives in the investigator's head and in scattered task lists.

7. **Build a new-source ingestion checklist.** When a new data source arrives (e.g., a PRR response with 200 pages of invoices), there should be a documented workflow for:
   - Filing the raw documents in the evidence package
   - Extracting tabular data to SQLite
   - Loading relationships to Neo4j
   - Indexing documents in LanceDB
   - Updating the data source registry
   - Flagging which `[UNRESOLVED]` markers in the articles can now be resolved

8. **Consolidate script execution into a runbook.** Not a FastAPI service — just a `RUNBOOK.md` or `Makefile` that documents the standard operating procedure: which scripts to run, in what order, with what arguments, and what output to expect. This makes it possible for a collaborator to run the ingestion pipeline without needing to study 39 analysis scripts.

9. **Add peer district data acquisition scripts.** The investigation already has `download_camas.py` and `download_tacoma.py`. Expanding the peer comparison to Evergreen SD #114 and Battle Ground SD #119 (as listed in `PHASE_1_TASKS.md`) requires similar download-and-ingest scripts, plus corresponding PRRs for Object 7 actuals.

10. **Extend the agent workflow system.** The OSPI response logging workflow is a proven pattern. Create similar workflows for:
    - PRR filing (generate request → file → track deadline → log response)
    - New data source ingestion (receive files → file in evidence → extract → ingest → validate)
    - Claim resolution (when new data resolves an `[UNRESOLVED]` marker → update article → update tracker)

### Tier 3: Assessor recommendations that now gain relevance

With investigation expansion, these assessor suggestions — previously premature — become worth considering on a longer timeline:

11. **Lightweight claims/evidence tracker.** Not the full Pydantic-model-in-Neo4j system the assessor proposed, but a structured markdown or CSV file mapping each major assertion to its evidence status, source documents, and `[UNRESOLVED]` tag. This becomes genuinely useful when tracking dozens of claims across multiple article drafts.

12. **Source coverage validation script.** The assessor's suggestion to build a script that reports which claims lack primary sources, which years are missing, and which relationships are inferred rather than verified becomes more valuable as data sources multiply. This could be a simple Python script that cross-references the claims tracker against the data source registry.

13. **Formalize store responsibilities.** The assessor's proposed split (Neo4j for relationships, LanceDB for semantic search, filesystem for source documents, SQLite for tabular staging) is already the *de facto* architecture. Documenting it explicitly helps when onboarding new data sources — each new source needs to know which stores it flows into.

### Things to still not do

- Do not build a FastAPI service layer. The investigation does not need HTTP endpoints.
- Do not add a React frontend. A web UI is not the right interface for expanding an investigation.
- Do not refactor working loader scripts into a new `app/` module hierarchy. Consolidate with documentation, not with import path changes.
- Do not deprecate SQLite. It gets MORE important as new tabular data sources arrive.
- Do not build multi-user collaboration features. Expand the agent workflow system instead.

---

## Additional Improvements Beyond the Assessments

These are improvements I recommend that none of the five assessments addressed:

### 1. Automated deadline tracking for PRRs

Washington's PRA (RCW 42.56.520) requires agencies to respond within 5 business days. When filing multiple PRRs across different agencies, deadline math becomes error-prone. A simple script or calendar integration that calculates and tracks response deadlines from filing dates would prevent missed follow-up windows.

### 2. GovQA portal integration notes

The Clark County Treasurer response directed the investigation to their GovQA tracking system. Other WA agencies may use similar portals. A reference document listing known intake mechanisms per agency (email, web form, GovQA, SecureExchange, etc.) would save time on future request filing.

### 3. Response analysis templates

The OSPI response logging workflow is good, but it could be extended with structured analysis templates for common response types:
- **Full compliance response** — what to check, how to file, how to update claims
- **Partial response with exemptions** — how to document claimed exemptions, how to draft appeal letters
- **Non-response past deadline** — how to document, template for follow-up with penalty citation
- **Redirect to another agency** — how to track the chain of custody

### 4. Evidence chain-of-custody log

As the investigation expands, documenting exactly how each piece of evidence was obtained becomes legally important. A simple log that records: what was requested, from whom, when filed, when received, in what format, and where stored. This is stronger than just having the files — it proves the provenance of the evidence itself.

### 5. `[UNRESOLVED]` tag extraction

The articles already use `[UNRESOLVED]` markers to flag claims that depend on data not yet obtained. A simple grep-based script that extracts all `[UNRESOLVED]` markers across articles and maps them to the specific PRR or data source needed would create an instant priority list for the investigation expansion. Several of these are already known:
- Amergis MSA and hourly rates → PRR Request 1
- Itemized invoices by role/school → PRR Request 2
- HR vacancy and time-to-fill data → PRR Request 3
- Purchasing authority thresholds → PRR Request 4

### 6. Peer district comparison framework

The investigation already has download scripts for Camas and Tacoma data. Formalizing a comparison framework — same fiscal years, same Object codes, same normalization logic — for 4-5 peer districts would strengthen the outlier argument substantially. This should reuse the existing `vendor_normalization.py` patterns and the `load_peer_budgets_neo4j.py` loader.

### 7. Board meeting monitoring

As the investigation expands, monitoring new VPS board meetings for relevant agenda items (contract renewals, staffing approvals, budget amendments) would catch developments in real-time. This could be a lightweight periodic task that checks BoardDocs or board packet PDFs for keywords.

---

## Final Verdict

The assessments are **technically competent but strategically incomplete**. They describe real gaps in WoodWard's application layer and offer reasonable engineering solutions. With investigation expansion planned, approximately a third of their recommendations gain genuine relevance — particularly around data model clarity, ingestion repeatability, and source coverage validation.

However, the assessments entirely missed WoodWard's most important infrastructure need: **a FOIA/PRR pipeline**. The investigation already has the building blocks (a drafted PRR, an agent workflow for response logging, download scripts for public data sources), but these are not yet connected into a repeatable system for filing, tracking, and ingesting public records requests at scale.

The ten highest-value actions, in priority order:

| # | Action | Source | Effort |
|---|--------|--------|--------|
| 1 | Fix hardcoded credentials — load from `.env` | Assessor (validated) | 20 min |
| 2 | Create FOIA/PRR tracker | New recommendation | 1-2 hours |
| 3 | Create parameterized FOIA request template | New recommendation | 1 hour |
| 4 | Extract all `[UNRESOLVED]` markers into a priority list | New recommendation | 30 min |
| 5 | Create a data source registry | New recommendation | 1-2 hours |
| 6 | Generate exhibit index | Assessor (validated) | 1 hour |
| 7 | Create new-source ingestion checklist | New recommendation | 1 hour |
| 8 | Build script execution runbook (`RUNBOOK.md`) | Assessor (adapted) | 1-2 hours |
| 9 | Extend agent workflows for PRR filing and data ingestion | New recommendation | 2-3 hours |
| 10 | Add peer district data acquisition for Evergreen and Battle Ground | Assessor + investigation need | 2-3 hours |

The assessor's larger recommendations (FastAPI, React frontend, multi-user collaboration, full claim model) remain premature. The investigation should expand its reach first, systematize its records-request pipeline, and build infrastructure only where it directly accelerates the journalism.
