# WoodWard Implementation Plan (March 6, 2026)

## Purpose
This document translates the WoodWard build plan into a concrete implementation sequence tied to the current repository structure.

It is written to answer one question:

**What should be built, in what order, in which parts of this repo, to turn WoodWard into a usable investigative journalist workbench?**

---

## Current Baseline

### What is already in place
- Neo4j is running and queryable through the Compose-managed `woodward-neo4j` service.
- Neo4j already contains meaningful investigation data:
  - payments
  - vendors
  - employees
  - documents
  - board meetings
  - contracts
  - agenda items
- SQLite still exists as a major source database in `data/woodward.db`.
- LanceDB exists and is used for semantic search over contracts and documents.
- There are multiple ingestion and analysis scripts in `scripts/loaders/` and `scripts/analysis/`.
- There is an embryonic reusable adapter layer in `workspaces/Cicero_Clone/src/`.
- There is no real app layer yet.

### What is still missing
- canonical domain model for claims/evidence/rebuttals
- unified local API
- journalist-facing UI
- structured right-of-reply workflow
- structured fact-check and legal review workflow
- reproducible export pipeline for publication support

---

## Implementation Principles

### 1. Do not rebuild everything at once
The repo already has useful code. The goal is to consolidate and formalize, not to start over.

### 2. Neo4j should become the primary investigative database
Use Neo4j as the core relationship and workflow store.

### 3. LanceDB stays as a sidecar
Do not waste time replacing the vector search layer if it is already useful.

### 4. Files remain canonical source artifacts
Source PDFs, email exports, and evidence packages stay on disk.

### 5. SQLite should stop being the main analysis surface
Keep it as an ingest/archive/debugging source unless a specific table remains operationally useful.

### 6. Build the service layer before building the UI
Otherwise the app will become a thin wrapper around more script sprawl.

---

## Proposed Implementation Structure

### New top-level code areas to add
Recommended new directories:

```text
WoodWard/
├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── repositories/
│   ├── workflows/
│   └── exports/
├── frontend/
│   ├── src/
│   └── public/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
```

### What stays where
- `scripts/loaders/`: ingestion utilities and data-loading jobs
- `scripts/analysis/`: exploratory analysis and dev-only diagnostics
- `guidance/`: planning and handoff docs
- `documents/`, `emails/`, `VPS_Investigation_Evidence/`: source and publication artifacts
- `workspaces/Cicero_Clone/src/`: mine reusable code from here, but do not keep app architecture split across `workspaces/`

---

## Phase 1: Create the App Backbone

### Goal
Introduce a stable code structure for the real application without breaking the current repo.

### Tasks
#### 1. Create app directories
Add:
- `app/api/`
- `app/models/`
- `app/repositories/`
- `app/services/`
- `app/workflows/`
- `app/exports/`
- `tests/unit/`
- `tests/integration/`

#### 2. Create configuration module
Add:
- `app/config.py`

Move toward centralized settings for:
- Neo4j URI
- Neo4j credentials
- LanceDB path
- source root paths
- export output paths
- optional SQLite path

#### 3. Create application entrypoint
Add:
- `app/main.py`

This should be the root for the future FastAPI service.

### Deliverables
- stable application package root
- centralized config
- service entrypoint

### Suggested order
1. `app/config.py`
2. `app/main.py`
3. base package layout

---

## Phase 2: Define the Canonical Domain Model

### Goal
Stop treating the investigation as scripts plus prose. Represent the reporting workflow directly in code and data.

### Files to create
- `app/models/claim.py`
- `app/models/evidence.py`
- `app/models/response.py`
- `app/models/entity.py`
- `app/models/investigation.py`
- `app/models/review.py`

### Minimum domain objects
#### Claim
Fields:
- `id`
- `title`
- `text`
- `claim_type`
- `status`
- `confidence`
- `owner`
- `created_at`
- `updated_at`
- `article_refs`
- `legal_review_status`
- `fact_check_status`
- `rebuttal_status`

#### EvidenceBundle
Fields:
- `id`
- `claim_id`
- `summary`
- `evidence_type`
- `strength`
- `graph_trace`
- `source_refs`

#### SourceReference
Fields:
- `id`
- `document_path`
- `document_type`
- `page_ref`
- `chunk_ref`
- `quote_text`
- `hash`

#### ResponseRequest
Fields:
- `id`
- `recipient_name`
- `recipient_role`
- `organization`
- `date_sent`
- `deadline`
- `status`
- `topic`
- `question_set`
- `linked_claim_ids`

#### Response
Fields:
- `id`
- `request_id`
- `sender`
- `date_received`
- `summary`
- `full_text`
- `quote_candidates`
- `linked_claim_ids`

#### ReviewDecision
Fields:
- `id`
- `claim_id`
- `review_type`
- `reviewer`
- `status`
- `notes`
- `timestamp`

### Deliverables
- typed internal model definitions
- a shared vocabulary for engineering and editorial work

---

## Phase 3: Create Repository Layer for Neo4j and LanceDB

### Goal
Separate business logic from raw database calls.

### Files to create
- `app/repositories/neo4j_claim_repository.py`
- `app/repositories/neo4j_entity_repository.py`
- `app/repositories/neo4j_evidence_repository.py`
- `app/repositories/neo4j_response_repository.py`
- `app/repositories/lancedb_document_repository.py`
- `app/repositories/file_document_repository.py`

### Responsibilities
#### Neo4j repositories
Handle:
- claim create/read/update
- entity retrieval
- evidence linking
- response tracking
- relationship traversal
- timeline retrieval

#### LanceDB repository
Handle:
- semantic search
- chunk retrieval
- chunk metadata access

#### File repository
Handle:
- source document metadata
- path resolution
- evidence package output

### Existing code to mine
From existing repo:
- `workspaces/Cicero_Clone/src/adapters/neo4j.py`
- `scripts/analysis/query_contracts.py`
- `scripts/loaders/ingest_payments.py`

### Deliverables
- stable data access boundary
- fewer direct database calls scattered through scripts

---

## Phase 4: Build the Core Service Layer

### Goal
Implement the logic journalists actually need.

### Files to create
- `app/services/search_service.py`
- `app/services/claim_service.py`
- `app/services/evidence_service.py`
- `app/services/entity_service.py`
- `app/services/governance_service.py`
- `app/services/vendor_service.py`
- `app/services/rebuttal_service.py`
- `app/services/export_service.py`

### Service responsibilities
#### Search service
- keyword entity search
- semantic document search
- hybrid contract clause search
- investigation-wide lookup

#### Claim service
- create claim
- update claim
- attach evidence
- attach article references
- retrieve claim status

#### Evidence service
- generate claim-to-source trace
- drill aggregate totals to rows/nodes/docs
- return source coverage status

#### Entity service
- vendor detail page data
- organization detail page data
- person detail page data
- contract link maps

#### Governance service
- retrieve board meetings
- retrieve agenda items
- retrieve vendor approvals
- retrieve vote patterns

#### Vendor service
- vendor spending by year
- contract set by vendor
- parent/rebrand chain
- payment anomalies

#### Rebuttal service
- create and track response requests
- attach responses
- summarize unresolved rebuttal gaps

#### Export service
- evidence appendix generation
- exhibit index generation
- editor memo generation
- claim table generation

### Deliverables
- the operational logic of the application exists independent of UI

---

## Phase 5: Add the Local API

### Goal
Expose the service layer through a stable interface.

### Files to create
- `app/api/routes/search.py`
- `app/api/routes/claims.py`
- `app/api/routes/entities.py`
- `app/api/routes/evidence.py`
- `app/api/routes/governance.py`
- `app/api/routes/rebuttals.py`
- `app/api/routes/exports.py`

### Recommended initial endpoints
#### Search
- `GET /search/entities`
- `GET /search/documents`
- `GET /search/contracts`

#### Claims
- `GET /claims`
- `GET /claims/{id}`
- `POST /claims`
- `PATCH /claims/{id}`
- `GET /claims/{id}/evidence`

#### Entities
- `GET /vendors/{name}`
- `GET /organizations/{name}`
- `GET /people/{name}`
- `GET /contracts/{id}`

#### Evidence
- `GET /evidence/trace/{claim_id}`
- `GET /evidence/source-coverage`
- `GET /evidence/aggregate-breakdown`

#### Governance
- `GET /board/meetings`
- `GET /board/actions`
- `GET /board/vendors/{vendor}`

#### Rebuttals
- `GET /responses/requests`
- `POST /responses/requests`
- `POST /responses`
- `GET /responses/by-claim/{claim_id}`

#### Exports
- `GET /exports/evidence-bundle/{investigation_id}`
- `GET /exports/claim-table/{article_id}`
- `GET /exports/exhibit-index/{article_id}`

### Deliverables
- backend usable via HTTP locally
- UI no longer coupled directly to DB calls

---

## Phase 6: Refactor Existing Ingestion into Repeatable Jobs

### Goal
Keep the current ingestion logic, but make it more deterministic and reusable.

### Existing files to preserve/refactor
- `scripts/loaders/ingest_payments.py`
- `scripts/loaders/ingest_board_governance.py`
- `scripts/loaders/ingest_salaries.py`
- `scripts/loaders/load_f195_v3.py`
- `scripts/loaders/vendor_normalization.py`

### Tasks
#### 1. Move shared logic into app modules
Example targets:
- date normalization
- vendor normalization
- fiscal year bucketing
- source path resolution

#### 2. Wrap ingestion in explicit commands
Suggested command entrypoints:
- `python -m app.jobs.refresh_payments`
- `python -m app.jobs.refresh_governance`
- `python -m app.jobs.refresh_contract_index`
- `python -m app.jobs.validate_graph`

#### 3. Add validation outputs
Each ingest run should report:
- records processed
- nodes created/updated
- relationships created/updated
- missing source files
- known discrepancy counts

### Files to add
- `app/jobs/refresh_payments.py`
- `app/jobs/refresh_governance.py`
- `app/jobs/refresh_documents.py`
- `app/jobs/validate_graph.py`

### Deliverables
- repeatable, named ingestion jobs
- reduced dependency on script-by-script tribal knowledge

---

## Phase 7: Implement Source Provenance and Claim Traceability

### Goal
Make every major claim inspectable.

### Files to create
- `app/workflows/claim_trace.py`
- `app/workflows/source_coverage.py`
- `app/workflows/publication_readiness.py`

### Core features to implement
#### 1. Claim trace graph
Given a claim, return:
- linked evidence bundles
- linked documents
- relevant graph path
- relevant source excerpts
- verification state
- rebuttal state

#### 2. Aggregate breakdown
Given a number like vendor total by year, return:
- query path used
- linked payments
- linked documents
- date logic used
- any warnings

#### 3. Source coverage report
Return:
- claims missing primary sources
- claims missing rebuttal
- claims linked only to inferred relationships
- missing year/file coverage

### Deliverables
- publication risk becomes visible before drafting final output

---

## Phase 8: Build the Minimal Frontend

### Goal
Provide a usable investigative surface for reporters and editors.

### Proposed frontend directory
- `frontend/src/`

### Recommended pages
#### 1. Dashboard
- investigation status
- claim counts by state
- open rebuttals
- missing-source alerts

#### 2. Search page
- entity search
- contract search
- document search
- claim search

#### 3. Claim detail page
- claim text
- evidence list
- rebuttal state
- verification notes
- linked excerpts
- article usage

#### 4. Entity detail page
- person/vendor/organization/contract summary
- linked payments
- linked approvals
- linked claims
- timeline

#### 5. Document viewer page
- metadata
- excerpts/chunks
- linked claims
- linked entities

#### 6. Rebuttal tracker page
- requests sent
- deadlines
- received responses
- unresolved gaps

### Technical recommendation
Keep the UI thin and practical.

Do not optimize for style yet. Optimize for:
- evidence visibility
- quick drilldown
- low-friction review
- reproducible export support

### Deliverables
- reporter can use the system without writing code
- editor can inspect support for claims without repo spelunking

---

## Phase 9: Build Export and Publication Support

### Goal
Turn internal work into publication-support artifacts quickly.

### Files to create
- `app/exports/evidence_bundle.py`
- `app/exports/exhibit_index.py`
- `app/exports/editor_memo.py`
- `app/exports/claim_table.py`
- `app/exports/right_of_reply_summary.py`

### Export outputs to support
- journalist handoff memo
- evidence appendix
- exhibit index
- claim verification table
- right-of-reply status memo
- editor review memo

### Deliverables
- less manual assembly at the end of the reporting process
- faster newsroom handoff

---

## Phase 10: Add Testing and Validation

### Goal
Protect the numbers and core logic.

### Tests to add
#### Unit tests
- vendor normalization
- fiscal year bucketing
- claim status transitions
- response status handling
- source reference formatting

#### Integration tests
- payment ingest into Neo4j
- governance ingest into Neo4j
- LanceDB query wrappers
- evidence trace generation
- export generation

#### Validation scripts
- compare graph totals against expected canonical totals
- validate node/relationship counts after ingest
- detect duplicate or orphaned entities
- report missing evidence links

### Files to add
- `tests/unit/test_vendor_normalization.py`
- `tests/unit/test_claim_service.py`
- `tests/integration/test_payment_ingest.py`
- `tests/integration/test_claim_trace.py`
- `tests/integration/test_exports.py`

### Deliverables
- major numbers become regression-protected
- ingestion mistakes become detectable earlier

---

## Immediate First Sprint
If implementation begins now, this is the right first sprint.

### Sprint goal
Create the minimal backbone for a real app.

### Sprint tasks
1. Create `app/` package structure.
2. Add `app/config.py` and `app/main.py`.
3. Create domain models for `Claim`, `EvidenceBundle`, `ResponseRequest`, and `Response`.
4. Build Neo4j repository layer for claims and entities.
5. Build minimal FastAPI routes for:
   - `GET /search/entities`
   - `GET /vendors/{name}`
   - `GET /claims/{id}`
   - `POST /claims`
6. Add first validation script for graph health and key totals.
7. Document standard startup in a short operations note.

### Sprint output
At the end of the first sprint, WoodWard should have:
- an actual app skeleton
- a real backend entrypoint
- canonical claim objects
- stable query access for core investigation entities

---

## Second Sprint

### Sprint goal
Make the backend genuinely useful to reporting workflows.

### Tasks
1. Implement evidence trace workflow.
2. Implement rebuttal tracker backend.
3. Add document search endpoints.
4. Build export service for claim table and exhibit index.
5. Start frontend with:
   - dashboard
   - search page
   - claim page
   - vendor page

---

## Third Sprint

### Sprint goal
Make the UI operational for real investigative use.

### Tasks
1. Finish entity detail views.
2. Add document viewer.
3. Add right-of-reply page.
4. Add publication readiness summary.
5. Add test coverage for major claim and evidence workflows.

---

## Key Repo Refactoring Recommendations

### Refactor now
- consolidate shared logic out of `scripts/analysis/` and `scripts/loaders/`
- stop relying on `workspaces/Cicero_Clone/src/` as if it were the app core
- move reusable code into `app/`

### Leave alone for now
- evidence package folders
- source document storage layout
- existing guidance markdowns
- article drafts

### Deprecate gradually
- one-off analysis scripts that duplicate service logic
- duplicated planning files once the app becomes self-describing

---

## Risks to Manage

### 1. Overbuilding before the core workflows exist
Do not spend time on polish before claim/evidence/rebuttal workflows are functional.

### 2. Letting the script ecosystem remain the real backend
If new logic keeps landing in ad hoc scripts instead of `app/`, the architecture will keep drifting.

### 3. Treating Neo4j as a dump instead of a model
The graph should not just store imported facts. It should represent the reporting workflow.

### 4. Building UI before provenance is solid
A pretty interface over weak traceability will create false confidence.

---

## Final Execution Recommendation
If you want the cleanest path forward, implement in this order:

1. `app/` package and config
2. canonical domain models
3. Neo4j/LanceDB repository layer
4. FastAPI service layer
5. evidence trace and rebuttal workflow
6. minimal frontend
7. export pipeline
8. tests and validation hardening

That is the shortest path from the current WoodWard repo to a credible investigative journalist application.
