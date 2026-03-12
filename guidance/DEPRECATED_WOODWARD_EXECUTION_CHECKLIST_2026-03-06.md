# WoodWard Execution Checklist (March 6, 2026)

## Purpose
This is the practical follow-on to the build plan and implementation plan.

It answers:
- what to do first
- what files to create or edit
- what order to work in
- what success looks like at each step

This is intentionally tactical.

---

## Working Rule
Do not start with frontend polish.

The correct order is:
1. app skeleton
2. config
3. domain models
4. repository layer
5. service layer
6. API routes
7. provenance workflows
8. minimal UI
9. exports
10. tests

---

## Step 1: Create the App Skeleton

### Create
- `app/__init__.py`
- `app/main.py`
- `app/config.py`
- `app/api/__init__.py`
- `app/api/routes/__init__.py`
- `app/models/__init__.py`
- `app/repositories/__init__.py`
- `app/services/__init__.py`
- `app/workflows/__init__.py`
- `app/exports/__init__.py`
- `app/jobs/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`

### Goal
Establish one canonical application root instead of continuing to split logic across scripts and workspaces.

### Done when
- the repo has a stable app package
- there is a clear place for new implementation work

---

## Step 2: Centralize Configuration

### Create or edit
- `app/config.py`

### Add support for
- Neo4j URI
- Neo4j username
- Neo4j password
- Neo4j database name
- LanceDB path
- source documents root
- guidance/export output root
- optional SQLite path

### Recommended follow-up
- update environment loading strategy so config is not scattered across scripts

### Done when
- all new app code can import one config source
- no new modules hardcode connection settings

---

## Step 3: Add a Minimal App Entrypoint

### Create or edit
- `app/main.py`

### Implement
- FastAPI app initialization
- health route
- route registration stub

### Minimum endpoints
- `GET /health`
- `GET /ready`

### Done when
- the app can start locally as a service
- there is one obvious backend entrypoint

---

## Step 4: Define the Core Domain Models

### Create
- `app/models/claim.py`
- `app/models/evidence.py`
- `app/models/response.py`
- `app/models/entity.py`
- `app/models/review.py`
- `app/models/investigation.py`

### Implement first
#### `claim.py`
Add:
- `ClaimStatus`
- `ClaimType`
- `Claim`

#### `evidence.py`
Add:
- `EvidenceBundle`
- `SourceReference`
- `SourceExcerpt`

#### `response.py`
Add:
- `ResponseRequestStatus`
- `ResponseRequest`
- `Response`

#### `review.py`
Add:
- `ReviewType`
- `ReviewDecision`

### Done when
- the reporting workflow has typed internal objects
- claim/evidence/rebuttal work can stop living only in markdown

---

## Step 5: Build Repository Layer

### Create
- `app/repositories/neo4j_claim_repository.py`
- `app/repositories/neo4j_entity_repository.py`
- `app/repositories/neo4j_evidence_repository.py`
- `app/repositories/neo4j_response_repository.py`
- `app/repositories/lancedb_document_repository.py`
- `app/repositories/file_document_repository.py`

### Mine existing logic from
- `scripts/loaders/ingest_payments.py`
- `scripts/loaders/ingest_board_governance.py`
- `scripts/analysis/query_contracts.py`
- `workspaces/Cicero_Clone/src/adapters/neo4j.py`

### Implement first
#### Neo4j entity repository
Support:
- vendor lookup
- person lookup
- organization lookup
- contract lookup

#### Neo4j claim repository
Support:
- create claim
- get claim
- list claims
- update claim status

#### LanceDB document repository
Support:
- semantic document search
- contract clause search
- chunk retrieval by source metadata

### Done when
- app services no longer need raw database code inline
- common data access patterns are reusable

---

## Step 6: Build Core Services

### Create
- `app/services/search_service.py`
- `app/services/claim_service.py`
- `app/services/evidence_service.py`
- `app/services/entity_service.py`
- `app/services/governance_service.py`
- `app/services/vendor_service.py`
- `app/services/rebuttal_service.py`
- `app/services/export_service.py`

### Implement first
#### `entity_service.py`
Support:
- get vendor detail
- get contract detail
- get board meeting detail

#### `claim_service.py`
Support:
- create claim
- attach evidence reference
- update verification state
- retrieve claim detail

#### `search_service.py`
Support:
- search entities
- search documents
- search contracts

#### `evidence_service.py`
Support:
- claim-to-source trace
- aggregate breakdown lookup

### Done when
- the application has usable backend logic for reporting workflows

---

## Step 7: Add the First API Routes

### Create
- `app/api/routes/search.py`
- `app/api/routes/claims.py`
- `app/api/routes/entities.py`
- `app/api/routes/evidence.py`

### Implement first endpoints
#### Search
- `GET /search/entities`
- `GET /search/documents`
- `GET /search/contracts`

#### Claims
- `GET /claims`
- `GET /claims/{id}`
- `POST /claims`
- `PATCH /claims/{id}`

#### Entities
- `GET /vendors/{name}`
- `GET /contracts/{id}`
- `GET /board/meetings`

#### Evidence
- `GET /evidence/trace/{claim_id}`
- `GET /evidence/aggregate-breakdown`

### Done when
- the backend exposes the first meaningful reporting endpoints

---

## Step 8: Implement Provenance Workflow

### Create
- `app/workflows/claim_trace.py`
- `app/workflows/source_coverage.py`
- `app/workflows/publication_readiness.py`

### Implement first
#### `claim_trace.py`
Return for a claim:
- linked evidence bundles
- source documents
- excerpts
- graph trace metadata
- rebuttal status

#### `source_coverage.py`
Report:
- claims without primary support
- claims missing rebuttal
- claims supported only by inferred links
- missing year/document coverage

### Done when
- the system can answer “show me exactly what supports this claim” without manual digging

---

## Step 9: Formalize Right-of-Reply Tracking

### Create
- `app/api/routes/rebuttals.py`
- `app/services/rebuttal_service.py`
- `app/repositories/neo4j_response_repository.py`

### Implement first features
- create response request
- list outstanding requests
- mark deadline
- attach response text
- link requests and responses to claims

### Data to capture
- recipient
- role
- organization
- date sent
- deadline
- topic
- linked claims
- received response status
- follow-up needed

### Done when
- right-of-reply is a system feature instead of only a folder pattern

---

## Step 10: Wrap Existing Ingestion into App Jobs

### Create
- `app/jobs/refresh_payments.py`
- `app/jobs/refresh_governance.py`
- `app/jobs/refresh_documents.py`
- `app/jobs/validate_graph.py`

### Refactor from
- `scripts/loaders/ingest_payments.py`
- `scripts/loaders/ingest_board_governance.py`
- `scripts/loaders/ingest_salaries.py`
- `scripts/loaders/load_f195_v3.py`

### Job outputs should report
- processed count
- created/updated count
- missing source files
- discrepancy count
- summary totals

### Done when
- ingestion is repeatable through a named job path
- the backend can be refreshed without relying on scattered scripts

---

## Step 11: Build the Minimal Frontend

### Create
- `frontend/package.json`
- `frontend/src/main.*`
- `frontend/src/App.*`
- `frontend/src/pages/Dashboard.*`
- `frontend/src/pages/Search.*`
- `frontend/src/pages/ClaimDetail.*`
- `frontend/src/pages/VendorDetail.*`
- `frontend/src/pages/RebuttalTracker.*`
- `frontend/src/lib/api.*`

### First pages to implement
#### Dashboard
Show:
- claim status counts
- open rebuttals
- source coverage warnings
- recent ingest status

#### Search page
Allow:
- entity search
- document search
- contract search
- claim search

#### Claim detail page
Show:
- claim text
- status
- evidence
- rebuttal state
- linked sources

#### Vendor detail page
Show:
- spending trend
- linked contracts
- linked board approvals
- linked claims

### Done when
- a reporter can perform core investigation tasks without Python

---

## Step 12: Add Export Support

### Create
- `app/exports/evidence_bundle.py`
- `app/exports/exhibit_index.py`
- `app/exports/editor_memo.py`
- `app/exports/claim_table.py`
- `app/exports/right_of_reply_summary.py`

### Implement first outputs
- claim verification table
- exhibit index
- right-of-reply summary memo
- evidence appendix bundle

### Done when
- the system can generate newsroom-useful artifacts without manual assembly

---

## Step 13: Add Tests

### Create
- `tests/unit/test_config.py`
- `tests/unit/test_claim_models.py`
- `tests/unit/test_vendor_normalization.py`
- `tests/unit/test_claim_service.py`
- `tests/integration/test_neo4j_health.py`
- `tests/integration/test_claim_trace.py`
- `tests/integration/test_payment_ingest.py`
- `tests/integration/test_exports.py`

### Test first
- config loads
- vendor normalization stability
- claim creation/update
- evidence trace path generation
- graph health check
- export generation

### Done when
- critical logic has regression protection
- ingestion and evidence workflows are not trust-based

---

## Immediate Work Queue
If work starts right now, do these in order.

### Queue A: First files to create
1. `app/__init__.py`
2. `app/config.py`
3. `app/main.py`
4. `app/models/claim.py`
5. `app/models/evidence.py`
6. `app/models/response.py`
7. `app/repositories/neo4j_entity_repository.py`
8. `app/repositories/neo4j_claim_repository.py`
9. `app/services/entity_service.py`
10. `app/services/claim_service.py`
11. `app/api/routes/entities.py`
12. `app/api/routes/claims.py`

### Queue B: First files to refactor from existing code
1. `scripts/loaders/ingest_payments.py`
2. `scripts/loaders/ingest_board_governance.py`
3. `scripts/loaders/vendor_normalization.py`
4. `scripts/analysis/query_contracts.py`
5. `workspaces/Cicero_Clone/src/adapters/neo4j.py`

### Queue C: First UI files
1. `frontend/package.json`
2. `frontend/src/App.*`
3. `frontend/src/lib/api.*`
4. `frontend/src/pages/Dashboard.*`
5. `frontend/src/pages/Search.*`
6. `frontend/src/pages/ClaimDetail.*`

---

## Definition of Success for Version 1
WoodWard Version 1 is successful when a journalist can:
- search vendors, contracts, documents, and claims
- open a claim and see what supports it
- trace a major number to source evidence
- see whether rebuttal is complete
- export a claim table or evidence bundle
- do all of that without writing Python or Cypher

That is the threshold to hit.

---

## Final Recommendation
Do not split implementation across too many experiments.

The fastest usable path is:
1. create the `app/` package
2. define claims/evidence/rebuttals as data
3. build the API layer
4. implement provenance and rebuttal workflows
5. add the thinnest possible UI

Everything else should support those goals.
