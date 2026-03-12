# WoodWard Improvement Plan (March 6, 2026)

## Context

This plan replaces the five previous assessment documents in this folder (now prefixed `DEPRECATED_`). Those documents were technically competent but strategically misaligned with WoodWard's actual needs. A full code-level review of their claims is in [ASSESSMENT_REVIEW_2026-03-06.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/guidance/ASSESSMENT_REVIEW_2026-03-06.md) — **read that document first** before beginning any implementation. It explains what the original assessments got right, what they missed, and what recommendations would break existing working systems.

> [!CAUTION]
> **Do not** demote SQLite, refactor loader scripts into an `app/` module hierarchy, add a React/Node.js frontend, build a FastAPI service layer, or mine code from `workspaces/Cicero_Clone/`. The assessment review explains why each of these would break WoodWard.

## Project Direction

WoodWard is an **active, expanding investigation** into Vancouver Public Schools' staffing vendor spending. It is not a product company building a newsroom platform. Every improvement must directly accelerate the journalism.

The investigation is expanding to:
- New data sources beyond current warrant registers and F-195 budgets
- Additional FOIA/PRR (Public Records Act) requests to multiple agencies
- Peer district comparisons for Evergreen SD #114 and Battle Ground SD #119
- Potential new counterparties beyond the current right-of-reply set
- Journalist handoff of the evidence package

## Guiding Principles

1. **Never break what works.** The current scripts, databases, and evidence package are actively producing results. Improve them in place; do not reorganize.
2. **Build for the investigation, not for a product.** Every change should answer: "Does this help file a records request, ingest new data, strengthen a claim, or prepare evidence for handoff?"
3. **Lightweight over heavyweight.** Markdown files, CSV trackers, Makefile wrappers, and agent workflows — not Pydantic models, FastAPI endpoints, or React components.
4. **Respect the existing architecture.** SQLite is the canonical tabular store. Neo4j is the relationship graph. LanceDB is the semantic sidecar. Filesystem is source-of-record. Do not change these roles.

---

## Phase 1: Fix Known Defects

**Timeline: Day 1**
**Zero investigative output needed — pure infrastructure hygiene**

### 1.1 Fix hardcoded credentials

**Problem:** `ingest_payments.py`, `ingest_board_governance.py`, and `verify_ingestion.py` all hardcode Neo4j URI and credentials directly in the source code, despite `.env` already containing the correct values.

**Fix:**
- Add `python-dotenv` to the project dependencies
- At the top of each script, add:
  ```python
  from dotenv import load_dotenv
  import os
  load_dotenv()
  NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7688")
  NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "woodward_secure_2024"))
  ```
- Remove the hardcoded `NEO4J_URI` and `NEO4J_AUTH` constants
- Verify each script still works identically after the change

**Files to modify:**
- `scripts/loaders/ingest_payments.py` (lines 21-23)
- `scripts/loaders/ingest_board_governance.py` (lines 6-7)
- `scripts/verify_ingestion.py` (lines 3-4)
- Any other scripts in `scripts/loaders/` or `scripts/analysis/` that hardcode these values (grep for `7688` and `woodward_secure`)

**Verification:** Run `verify_ingestion.py` after changes — output should match the pre-change output exactly.

### 1.2 Add `.env` to `.gitignore`

**Problem:** If `.env` is not already in `.gitignore`, pushing to any remote would leak credentials.

**Fix:** Verify `.env` is in `.gitignore`. If not, add it.

**File to check:** `.gitignore`

---

## Phase 2: FOIA/PRR Pipeline

**Timeline: Day 1-2**
**This is the highest-value new infrastructure the assessments entirely missed.**

### 2.1 Create a FOIA/PRR tracker

**Purpose:** Unify the currently scattered tracking of public records requests into a single operational view.

**Create:** `VPS_Investigation_Evidence/08_FOIA_Tracker/FOIA_TRACKER.md`

**Format:** Structured markdown table with the following columns:

```markdown
# FOIA / Public Records Request Tracker

## Active Requests

| ID | Agency | Subject | Date Filed | Deadline | Status | Response Summary | Docs Received | Related Claims |
|----|--------|---------|------------|----------|--------|------------------|---------------|----------------|
| PRR-001 | VPS | Staffing agency MSAs (Amergis/Maxim/Soliant) | — | — | DRAFT | — | — | Art.1 ¶12, Art.2 ¶8 |
| PRR-002 | VPS | Itemized invoices by role/school | — | — | DRAFT | — | — | Art.1 ¶15 |
| PRR-003 | VPS | HR vacancy and time-to-fill data | — | — | DRAFT | — | — | Art.4 ¶3 |
| PRR-004 | VPS | Purchasing authority / delegation docs | — | — | DRAFT | — | — | Art.2 ¶22 |
| PRR-005 | VPS | Inter-fund borrowing resolutions | — | — | DRAFT | — | — | Art.1 ¶30 |
| PRR-006 | VPS | F-196 annual financial statements | — | — | DRAFT | — | — | Art.1 ¶5 |
| ROR-001 | Clark County Treasurer | Cash-flow interventions | 2026-02-27 | 2026-03-06 | RESPONDED | Directed to GovQA portal | 20_cnty_treasurer*.md | Art.1 ¶28 |
| ROR-002 | OSPI | Cash-flow advances, SPED compliance | 2026-02-27 | 2026-03-06 | RESPONDED | Two responses received (Lewis, Kha) | 22_shawn_lewis*.md, 23_doua_kha*.md | Art.2 ¶14 |
| ROR-003 | SAO | Audit scope, Purchased Services controls | 2026-02-27 | 2026-03-06 | RESPONDED | Cooper response | SAO_Cooper*.md | Art.2 ¶19 |

## Status Legend
- DRAFT = Request written but not filed
- SENT = Filed, awaiting acknowledgment
- ACKNOWLEDGED = Agency confirmed receipt
- PARTIAL = Some records received, more pending
- COMPLETE = All responsive records received
- DENIED = Request denied (document exemption cited)
- APPEALED = Denial appealed
- NON-RESPONSE = Past deadline with no response
```

**Data sources to populate from:**
- `workspaces/results/PUBLIC_RECORDS_REQUEST.md` — the existing 6-part PRR draft (these become PRR-001 through PRR-006)
- `VPS_Investigation_Evidence/07_Right_of_Reply/INDEX.md` — the 24-row right-of-reply index
- `PHASE_1_TASKS.md` — outstanding records request tasks

### 2.2 Create a parameterized FOIA request template

**Purpose:** Make it trivial to generate new RCW 42.56 requests for different agencies and record types.

**Create:** `VPS_Investigation_Evidence/08_FOIA_Tracker/PRR_TEMPLATE.md`

**Content:** A fill-in-the-blanks version of the existing PRR at `workspaces/results/PUBLIC_RECORDS_REQUEST.md`, with clearly marked placeholders for:
- `[AGENCY_NAME]` and `[AGENCY_ADDRESS]`
- `[RECORDS_OFFICER_EMAIL]`
- `[REQUEST_ITEMS]` — modular sections that can be mixed and matched
- `[DATE_RANGE_START]` and `[DATE_RANGE_END]`
- `[ENTITY_NAMES]` — the specific vendors/people/contracts being requested
- `[FEE_THRESHOLD]`

Include pre-built request modules for common record types:
- Staffing agency contracts and MSAs
- Itemized invoices
- HR vacancy and recruitment data
- Purchasing authority and delegation documents
- Inter-fund borrowing resolutions
- Budget reports (F-195, F-196)
- Board meeting minutes and consent agendas
- Email correspondence on specified topics

### 2.3 Create a PRR filing agent workflow

**Purpose:** Extend the proven OSPI response logging workflow pattern to cover the full PRR lifecycle.

**Create:** `.agents/workflows/prr_filing.md`

**Workflow steps:**
1. Generate request from template (fill placeholders, select modules)
2. Save completed request to `VPS_Investigation_Evidence/08_FOIA_Tracker/Requests/`
3. Update `FOIA_TRACKER.md` with new row (status: SENT, deadline calculated)
4. When response arrives: analyze content, extract evidence value, update tracker status
5. File received documents in appropriate evidence subdirectory
6. Update `[UNRESOLVED]` markers in articles if new data resolves them

### 2.4 Automated PRR deadline calculator

**Purpose:** Washington PRA requires 5 business day responses. Automate the deadline math.

**Create:** `scripts/prr_deadline.py`

**Behavior:** Given a filing date, calculate and display the 5-business-day response deadline (excluding weekends and WA state holidays). Optionally update the `FOIA_TRACKER.md` table.

---

## Phase 3: Data Source Management

**Timeline: Day 2-3**
**Critical for investigation expansion — tracking what you have and what you need.**

### 3.1 Create a data source registry

**Purpose:** Replace the current pattern where source coverage knowledge lives in the investigator's head.

**Create:** `VPS_Investigation_Evidence/DATA_SOURCE_REGISTRY.md`

**Format:**

```markdown
# Data Source Registry

## Obtained Sources

| Source | Type | Date Range | Obtained Via | Ingested To | Gaps |
|--------|------|-----------|-------------|------------|------|
| Warrant registers | Payment data | FY 2018-2025 | OSPI download | SQLite → Neo4j | None known |
| F-195 budget reports | Budget data | FY 2022-2025 | OSPI/VPS website | SQLite → Neo4j | FY 2023-24 actuals may be missing |
| SAO audit reports | Audit findings | FY 2019-2024 | SAO website | Filesystem only | Not ingested to graph |
| Board meeting minutes | Governance | 2020-2025 | BoardDocs (chunked) | LanceDB → Neo4j | Automated access blocked |
| S-275 salary data | Personnel | FY 2022-2024 | OSPI/manual | SQLite → Neo4j | Pre-2022 missing |

## Needed Sources (Not Yet Obtained)

| Source | Type | Needed For | How to Obtain | PRR ID |
|--------|------|-----------|--------------|--------|
| Amergis MSA and rate schedules | Contract terms | Agency premium calculation | PRR to VPS | PRR-001 |
| Itemized invoices by role/school | Placement detail | Role-level spending analysis | PRR to VPS | PRR-002 |
| HR vacancy reports | Staffing gaps | Internal capacity proof | PRR to VPS | PRR-003 |
| Purchasing authority docs | Governance | Approval threshold evidence | PRR to VPS | PRR-004 |
| Evergreen SD #114 Object 7 data | Peer budget | Outlier comparison | OSPI + PRR | — |
| Battle Ground SD #119 Object 7 data | Peer budget | Outlier comparison | OSPI + PRR | — |
| VEA collective bargaining agreement | Salary schedules | Cost comparison baseline | Union request | — |
```

**Populate from:** Filesystem inventory of `VPS_Investigation_Evidence/`, `documents/`, `data/`, and the articles' `[UNRESOLVED]` markers.

### 3.2 Extract all `[UNRESOLVED]` markers

**Purpose:** Create an instant priority list mapping every evidence gap to the specific PRR or data source that would close it.

**Create:** `scripts/extract_unresolved.py`

**Behavior:**
- Grep all `.md` files in `VPS_Investigation_Evidence/06_Articles/` for `[UNRESOLVED]`
- For each match, extract: filename, line number, surrounding context, and the associated data request
- Output a summary table to `VPS_Investigation_Evidence/UNRESOLVED_CLAIMS.md`
- Cross-reference against `FOIA_TRACKER.md` to show which PRRs would resolve which markers

### 3.3 Create new-source ingestion checklist

**Purpose:** When a PRR response or new data arrives, provide a repeatable workflow for getting it into the system.

**Create:** `guidance/NEW_SOURCE_INGESTION_CHECKLIST.md`

**Checklist:**
1. Save raw files to the appropriate `VPS_Investigation_Evidence/` subdirectory
2. Log the source in `DATA_SOURCE_REGISTRY.md`
3. If tabular data: create or update a loader script in `scripts/loaders/` to extract into SQLite
4. If relationship data: ingest to Neo4j using existing patterns from `ingest_payments.py`
5. If document/text data: chunk and index in LanceDB using patterns from `bridge_lancedb.py`
6. Run `verify_ingestion.py` to confirm graph integrity
7. Update `FOIA_TRACKER.md` status for the generating PRR
8. Run `scripts/extract_unresolved.py` to check if any `[UNRESOLVED]` markers can now be resolved
9. If markers resolved: update the article text and move status to VERIFIED

### 3.4 Create agent workflow for new-source ingestion

**Create:** `.agents/workflows/new_source_ingestion.md`

**Purpose:** Agent-assisted version of the ingestion checklist. When the user drops new files and says "ingest this," the agent follows the documented steps.

---

## Phase 4: Investigation Expansion Tools

**Timeline: Day 3-5**
**Directly produces new investigative capability.**

### 4.1 Peer district data acquisition

**Purpose:** Strengthen the outlier argument by adding Object 7 actuals for Evergreen SD #114 and Battle Ground SD #119.

**Existing patterns to follow:**
- `scripts/loaders/download_camas.py`
- `scripts/loaders/download_tacoma.py`
- `scripts/loaders/load_peer_budgets_neo4j.py`

**Create:**
- `scripts/loaders/download_evergreen.py`
- `scripts/loaders/download_battleground.py`

**Data target:** F-195 Object 7 (Purchased Services) totals and per-pupil normalization for FY 2020-2025. Should use the same fiscal year logic and normalization as existing peer scripts.

**Ingestion:** Load to Neo4j using `load_peer_budgets_neo4j.py` patterns, creating `District` and `FiscalYear` nodes with `SPENT_ON_OBJECT7` relationships.

### 4.2 Peer district comparison framework

**Purpose:** Formalize the comparison so it is reproducible and extensible.

**Create:** `scripts/analysis/peer_comparison_framework.py`

**Behavior:**
- Pull Object 7 data for all comparison districts from Neo4j
- Normalize by enrollment (per-pupil)
- Calculate VPS as a multiple of peer average
- Output comparison table and chart-ready CSV
- Flag any years where peer data is missing

**Reuses:** `vendor_normalization.py` patterns, `load_peer_budgets_neo4j.py` data

### 4.3 Board meeting monitoring keywords

**Purpose:** Catch new board actions relevant to the investigation as they happen.

**Create:** `scripts/analysis/board_monitor.py`

**Behavior:**
- Accept a path to newly downloaded board packet PDFs or minutes
- Search for configurable keywords: `Amergis`, `Maxim`, `Soliant`, `Pioneer`, `staffing`, `Object 7`, `purchased services`, `contract renewal`, `inter-fund`
- Report matches with context
- Optionally append findings to a `BOARD_MONITOR_LOG.md`

---

## Phase 5: Evidence Package Hardening

**Timeline: Day 5-6**
**Strengthens the handoff package. Addresses valid assessor feedback.**

### 5.1 Generate exhibit index

**Purpose:** Map every major claim to its exact source file and page/table.

**Create:** `scripts/generate_exhibit_index.py`

**Behavior:**
- Parse articles in `06_Articles/` for citation patterns
- For each citation, resolve to a file in `05_Source_Documents/` or `01_Payment_Data/`
- Output `VPS_Investigation_Evidence/EXHIBIT_INDEX.md` — a table mapping claim → source file → page/section

### 5.2 Generate response status memo

**Purpose:** One-page summary of right-of-reply status for journalist handoff.

**Create:** `VPS_Investigation_Evidence/RESPONSE_STATUS_MEMO.md`

**Derived from:** `07_Right_of_Reply/INDEX.md`

**Format:**
- How many requests sent, to whom (grouped by role: administrators, board, union, oversight agencies)
- How many responded, how many did not respond
- Summary of each response received
- Outstanding requests and deadlines
- Non-responsive parties and documentation of outreach attempts

### 5.3 Response analysis templates

**Purpose:** Standardize how different categories of responses are processed.

**Create:** `guidance/RESPONSE_ANALYSIS_TEMPLATES.md`

**Include templates for:**
- **Full compliance response** — verification checklist, filing protocol, claims update procedure
- **Partial response with exemptions** — exemption documentation format, appeal letter template citing RCW 42.56.210(3)
- **Non-response past deadline** — documentation format, follow-up template with daily penalty citation per RCW 42.56.565
- **Redirect to another agency** — chain-of-custody tracking, new PRR generation using template

### 5.4 Evidence chain-of-custody log

**Purpose:** Document exactly how each piece of evidence was obtained — proves provenance.

**Create:** `VPS_Investigation_Evidence/CHAIN_OF_CUSTODY.md`

**Format:**

```markdown
| Evidence ID | Description | Obtained From | Date Requested | Date Received | Format | Filed At | Hash |
|-------------|-------------|---------------|----------------|---------------|--------|----------|------|
```

**Populate from:** Existing evidence package filesystem, `INDEX.md`, and `FOIA_TRACKER.md`.

---

## Phase 6: Operational Documentation

**Timeline: Day 6-7**
**Makes the system operable by someone other than the original architect.**

### 6.1 Create a script runbook

**Purpose:** Document which scripts to run, in what order, with what arguments.

**Create:** `guidance/RUNBOOK.md`

**Sections:**
1. **System startup** — how to bring up Neo4j via Docker Compose, verify connectivity
2. **Data ingestion sequence** — ordered list of loader scripts with expected inputs and outputs
3. **Validation** — how to run `verify_ingestion.py` and what to expect
4. **Analysis** — which analysis scripts produce investigation-relevant output (vs. which are one-off exploratory)
5. **Evidence packaging** — how to generate the exhibit index, response memo, and export bundles
6. **FOIA workflow** — how to use the PRR template, tracker, and deadline calculator

### 6.2 Document store responsibilities

**Purpose:** Make explicit what is currently implicit about where data lives.

**Add to:** `guidance/RUNBOOK.md` (as a section)

**Content:**
| Store | Role | Examples |
|-------|------|----------|
| SQLite (`data/woodward.db`) | Canonical tabular source | Payments, salaries, budget line items |
| Neo4j (`woodward-neo4j`) | Relationship graph | Vendor→Payment→FiscalYear, Board→AgendaItem→Contract |
| LanceDB (`data/lancedb/`) | Semantic search | Contract clause search, document chunk retrieval |
| Filesystem (`VPS_Investigation_Evidence/`) | Source-of-record | PDFs, emails, board packets, articles |
| Filesystem (`documents/`) | Working documents | F-195 files, SAO audits, contracts |

### 6.3 GovQA and agency intake reference

**Purpose:** Document known filing mechanisms for each target agency.

**Create:** `VPS_Investigation_Evidence/08_FOIA_Tracker/AGENCY_INTAKE_REFERENCE.md`

**Content:**
| Agency | Records Contact | Intake Method | Notes |
|--------|----------------|---------------|-------|
| VPS | publicrecords@vansd.org | Email | 5 business days per RCW 42.56.520 |
| OSPI | commteam@k12.wa.us | Email | May redirect to specific program staff |
| SAO | webmaster@sao.wa.gov | Email | |
| Clark County Treasurer | treasoff@clark.wa.gov | GovQA portal | Directed to GovQA in Feb 2026 response |
| WA Secretary of State | — | ccfs.sos.wa.gov | Self-service corporate filings search |

---

## Phase 7: Lightweight Claims Tracking

**Timeline: Day 7-8 (after core infrastructure is stable)**
**Adapted from assessor recommendation — lightweight version, not the full data model.**

### 7.1 Create a claims tracker

**Purpose:** As the investigation expands, track which assertions are verified, which need more evidence, and which are blocked on outstanding PRRs.

**Create:** `VPS_Investigation_Evidence/CLAIMS_TRACKER.md`

**Format:**

```markdown
| Claim ID | Article | Claim Summary | Status | Primary Source | Source Gaps | Blocking PRR | Rebuttal Status |
|----------|---------|---------------|--------|----------------|-------------|-------------|-----------------|
| C-001 | Art.1 | VPS spent $X on staffing agencies FY24-25 | VERIFIED | Warrant registers | None | — | No response from VPS |
| C-002 | Art.1 | Amergis premium exceeds internal cost by Y% | UNRESOLVED | — | MSA rate schedules | PRR-001 | — |
```

**Status values:** DRAFT, UNRESOLVED (missing source), VERIFIED (source-backed), DISPUTED (rebuttal received), PUBLISHED

> [!IMPORTANT]
> This is a **markdown table**, not a database model. Do not build Pydantic classes, Neo4j nodes, or an API for this. If and when the tracker outgrows a markdown file (100+ claims across multiple investigations), reconsider.

### 7.2 Source coverage validation script

**Purpose:** Programmatically check which claims lack primary sources.

**Create:** `scripts/validate_source_coverage.py`

**Behavior:**
- Parse `CLAIMS_TRACKER.md`
- For each claim with status UNRESOLVED, report the missing source and blocking PRR
- For each claim with status VERIFIED, confirm the cited source file exists on disk
- Output a coverage report: % of claims verified, list of gaps, list of stale entries

---

## Implementation Order Summary

| Phase | What | Priority | Effort | Depends On |
|-------|------|----------|--------|------------|
| 1 | Fix credentials, .gitignore | **P0** | 30 min | Nothing |
| 2 | FOIA tracker, template, workflow, deadline calc | **P0** | 3-4 hours | Nothing |
| 3 | Data source registry, `[UNRESOLVED]` extraction, ingestion checklist | **P1** | 3-4 hours | Phase 2 |
| 4 | Peer district scripts, comparison framework, board monitor | **P1** | 4-5 hours | Phase 1 |
| 5 | Exhibit index, response memo, analysis templates, chain of custody | **P2** | 4-5 hours | Phase 2 |
| 6 | Runbook, store docs, agency intake reference | **P2** | 2-3 hours | Phases 1-4 |
| 7 | Claims tracker, source coverage validation | **P3** | 2-3 hours | Phases 2-3 |

**Realistic total:** 20-25 hours of focused work across 7-8 days.

---

## Things NOT in This Plan (and Why)

These were recommended in the original assessments. They remain excluded.

| Excluded Item | Why |
|---------------|-----|
| FastAPI service layer | The investigation does not need HTTP endpoints. Scripts and agent workflows are sufficient. |
| React/Node.js frontend | Adds an entire technology stack to a Python project. Not the right interface for an expanding investigation. |
| `app/` package hierarchy | Would break working import paths in loader scripts without adding capability. See [assessment review](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/guidance/ASSESSMENT_REVIEW_2026-03-06.md), §1 and §4. |
| Pydantic domain models | Heavyweight for the current need. Markdown trackers serve the same purpose at this stage. |
| SQLite demotion | SQLite IS the canonical tabular source. Neo4j is derived from it. See [assessment review](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/guidance/ASSESSMENT_REVIEW_2026-03-06.md), §1. |
| Cicero_Clone code mining | Different project, different domain, different schema. See [assessment review](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/guidance/ASSESSMENT_REVIEW_2026-03-06.md), §4. |
| Multi-user collaboration features | Single-operator investigation. Agent workflows handle coordination. |
| Contradiction detection / stale-claim alerts | Product features for a later stage. |

---

## Reference Documents

- [ASSESSMENT_REVIEW_2026-03-06.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/guidance/ASSESSMENT_REVIEW_2026-03-06.md) — Full code-level review of the original assessments. **Read this first.**
- [PUBLIC_RECORDS_REQUEST.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/workspaces/results/PUBLIC_RECORDS_REQUEST.md) — Existing 6-part PRR draft (basis for PRR-001 through PRR-006)
- [PHASE_1_TASKS.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/PHASE_1_TASKS.md) — Original Phase 1 task tracking
- [07_Right_of_Reply/INDEX.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/VPS_Investigation_Evidence/07_Right_of_Reply/INDEX.md) — Current right-of-reply tracking
- [ospi_response_logging.md](file:///Volumes/WD_BLACK/Desk2/Projects/WoodWard/.agents/workflows/ospi_response_logging.md) — Existing agent workflow to extend
