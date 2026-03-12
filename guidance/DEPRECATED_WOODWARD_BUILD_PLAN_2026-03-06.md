# WoodWard Build Plan (March 6, 2026)

## Objective
Turn WoodWard from a strong investigative backend and analyst-operated research environment into a usable **investigative journalist workbench**.

This plan assumes:
- WoodWard remains **local-first**
- Neo4j is the **primary analytical graph**
- LanceDB remains a **semantic search sidecar**
- raw files remain on disk as canonical source artifacts
- the product is built first for a **lead reporter + editor/fact-check/legal collaborators**, not for the general public

---

## Product Goal
Build a focused app that lets a journalist do five things reliably:

1. Search the investigation corpus
2. Trace claims back to primary evidence
3. Review entities, contracts, board actions, and payment trails
4. Track right-of-reply and verification status
5. Export publication-ready evidence bundles

---

## Build Strategy
Do not try to build a broad newsroom platform.

Build a **narrow investigative workbench** optimized for:
- public-records investigations
- budget and payment forensics
- vendor relationship tracing
- board/governance oversight analysis
- claim verification and publication prep

The build should happen in four layers:

1. Infrastructure stabilization
2. Data model and service layer
3. Investigative workflow layer
4. Journalist-facing UI and exports

---

## Phase 0: Stabilize Core Infrastructure

### Goal
Make the current backend reliable, repeatable, and safe to build on.

### Why this phase matters
Right now the repo works, but too much depends on operator knowledge and script-by-script execution.

### Deliverables
- Neo4j Compose startup is fixed and documented
- service startup commands are repeatable
- data-store roles are explicitly defined
- ingestion and verification commands are standardized

### Tasks
- Keep the current Neo4j Compose fix in place.
- Document the standard runtime path for Neo4j in a dedicated operations note.
- Define store responsibilities clearly:
  - Neo4j: entities, claims, relationships, approvals, evidence links
  - LanceDB: semantic search only
  - filesystem: source-of-record documents
  - SQLite: staging/archive input only unless explicitly retained for tabular debugging
- Create a small set of standard terminal tasks:
  - `rebuild-graph`
  - `refresh-payments`
  - `refresh-contract-index`
  - `refresh-governance`
  - `validate-totals`
  - `validate-source-coverage`
- Add a basic health check script that verifies:
  - Neo4j connectivity
  - LanceDB table presence
  - required source folders exist
  - expected node counts after ingest

### Exit criteria
- A new session can bring the system up without manual improvisation.
- The graph can be rebuilt from known inputs with a standard command path.
- Store roles are no longer ambiguous.

---

## Phase 1: Establish the Canonical Data Model

### Goal
Create the core objects that a journalist app actually needs.

### Why this phase matters
Right now WoodWard has data and scripts, but not a durable domain model for reporting work.

### Core entities to add or formalize
- `Claim`
- `EvidenceBundle`
- `SourceDocument`
- `SourceExcerpt`
- `ResponseRequest`
- `Response`
- `ReviewDecision`
- `TimelineEvent`
- `Investigation`
- `Person`
- `Organization`
- `Contract`
- `BoardMeeting`
- `AgendaItem`
- `Payment`
- `FiscalYear`

### Key relationships to support
- `CLAIM_SUPPORTED_BY`
- `CLAIM_DISPUTED_BY`
- `CLAIM_REFERENCES`
- `CLAIM_USED_IN`
- `REQUEST_SENT_TO`
- `RESPONSE_TO`
- `REVIEWED_BY`
- `EXCERPT_FROM`
- `HAS_EXHIBIT`
- `PART_OF_INVESTIGATION`
- `MENTIONED_IN`
- `AUTHORIZES`
- `RECEIVED_PAYMENT`

### Claim model requirements
Each `Claim` should include:
- claim text
- normalized claim type
- status: draft, under review, verified, disputed, blocked, published
- confidence level
- owner
- last reviewed at
- linked article/briefing usage
- rebuttal status
- legal review status
- notes

### Response workflow model requirements
Each `ResponseRequest` should include:
- recipient name
- role
- organization
- date sent
- deadline
- topic
- question set
- current status
- linked claims
- linked documents

Each `Response` should include:
- sender
- received date
- response summary
- quoted response text
- relevance to claims
- open follow-up questions

### Exit criteria
- Claims are first-class data, not just prose in markdown.
- Rebuttals and verification are structured, not scattered.
- Evidence can be attached to claims directly.

---

## Phase 2: Build the Internal Service Layer

### Goal
Stop turning every new question into a new Python script.

### Why this phase matters
Without a service layer, the system remains an analyst toolkit instead of an application.

### Recommended implementation
Use a lightweight local API layer, likely FastAPI.

### Service responsibilities
- entity lookup
- claim lookup
- payment aggregation queries
- board/governance queries
- contract clause search
- evidence trace queries
- right-of-reply tracking
- export generation

### Recommended API groups
#### 1. Search
- `search/entities`
- `search/documents`
- `search/contracts`
- `search/claims`

#### 2. Investigations
- `investigations/list`
- `investigations/detail`
- `investigations/timeline`

#### 3. Claims
- `claims/create`
- `claims/update`
- `claims/list`
- `claims/detail`
- `claims/evidence`
- `claims/rebuttals`

#### 4. Evidence
- `evidence/document`
- `evidence/excerpts`
- `evidence/graph-trace`
- `evidence/source-coverage`

#### 5. Governance and vendors
- `vendors/detail`
- `vendors/spending-trend`
- `vendors/contracts`
- `board/meetings`
- `board/actions`

#### 6. Publication support
- `exports/evidence-bundle`
- `exports/editor-memo`
- `exports/exhibit-index`
- `exports/claim-table`

### Engineering rules for the service layer
- move shared logic out of one-off scripts
- treat Neo4j as the default graph query backend
- use LanceDB only for semantic search retrieval
- keep file provenance attached at the API boundary
- return IDs and source references consistently

### Exit criteria
- The most common questions can be answered through stable endpoints.
- Analysts no longer need to inspect individual scripts to retrieve core facts.
- The backend behaves like a product surface.

---

## Phase 3: Build Provenance and Verification Features

### Goal
Make every important figure and assertion auditable.

### Why this phase matters
This is the feature that makes the difference between “interesting analysis” and “publication-safe investigative tooling.”

### Required capabilities
#### 1. Claim-to-source trace
For any claim, the system should show:
- exact supporting documents
- excerpts or rows used
- graph path used to derive the claim
- any derived calculations
- any missing or disputed support

#### 2. Aggregate-to-row drilldown
For any major total, the system should show:
- total figure
- query logic used
- underlying rows or linked nodes
- source files
- fiscal-year logic

#### 3. Verification statuses
Add structured statuses such as:
- unreviewed
- source-backed
- partially backed
- disputed
- blocked by missing source
- legally sensitive
- ready for publication

#### 4. Source coverage reporting
The system should be able to answer:
- which claims lack primary sources
- which years/files are missing
- which relationships are inferred rather than verified
- which articles contain weakly supported lines

### Exit criteria
- Every core claim can be audited quickly.
- Missing-source risk becomes visible early.
- Fact-checking becomes systematic rather than memory-based.

---

## Phase 4: Build Right-of-Reply and Editorial Workflow

### Goal
Support the actual reporting lifecycle, not just analysis.

### Why this phase matters
Investigative journalism is not finished when the number is calculated. It is finished when the claim is verified, challenged, answered, reviewed, and prepared for publication.

### Required workflow modules
#### 1. Right-of-reply tracker
Track:
- contacts
- organizations
- question sets
- sent dates
- deadlines
- responses received
- nonresponses
- unresolved follow-up

#### 2. Editorial review status
Track:
- reporter review
- editor review
- fact-check review
- legal review
- publication approval

#### 3. Timeline and tasking
Track:
- open investigative leads
- blockers
- next actions
- related claims
- related entities
- urgency

#### 4. Publication readiness view
For each article or memo, show:
- claims included
- evidence strength
- rebuttal completeness
- source gaps
- legal flags
- exhibits available

### Exit criteria
- The system knows what is verified, what is still pending, and what is publishable.
- Rebuttal management becomes a product feature rather than a folder habit.

---

## Phase 5: Build the Journalist-Facing UI

### Goal
Make the system usable by reporters and editors without requiring them to operate through scripts.

### Recommended approach
Build a minimal web UI over the service layer.

### Core UI surfaces
#### 1. Investigation dashboard
Show:
- current investigation status
- claim counts by status
- pending rebuttals
- missing source alerts
- recent ingestion activity

#### 2. Entity pages
For `Vendor`, `Person`, `Organization`, `Contract`, `BoardMeeting`:
- summary
- linked claims
- linked documents
- linked payments or votes
- timeline view

#### 3. Claim pages
Show:
- claim text
- evidence list
- rebuttal status
- verification notes
- related excerpts
- related article usage

#### 4. Document viewer
Show:
- original document metadata
- chunk or excerpt matches
- linked claims
- linked entities
- page references

#### 5. Search interface
Support:
- keyword search
- semantic contract search
- entity search
- claim search
- timeline filtering

#### 6. Export tools
Allow one-click generation of:
- evidence appendix
- exhibit index
- editor memo
- journalist handoff packet
- claim verification table

### Exit criteria
- A journalist can do core reporting work without dropping into Python.
- An editor can review evidence status without reading raw repo files.
- The UI is thin, but operationally useful.

---

## Phase 6: Add Publication and Collaboration Features

### Goal
Make the tool safe and effective for multi-person investigative work.

### Features to add
- user roles: reporter, editor, fact-checker, legal reviewer
- annotations and comments
- version history for claims
- change tracking for evidence and exports
- review decisions with timestamps
- conflict flags when evidence changes after approval

### Optional but valuable
- contradiction detection
- stale-claim alerts after new data ingestion
- automatic prompt generation for follow-up records requests
- assisted exhibit generation for publication packages

### Exit criteria
- Multiple collaborators can use the system safely.
- Claim state changes are visible and attributable.
- Publication materials are reproducible.

---

## Recommended Technical Stack

### Backend
- FastAPI for local service/API
- Neo4j as core graph store
- LanceDB as semantic search sidecar
- filesystem as source document store
- optional SQLite retained only as staging/archive input

### Frontend
- lightweight React app or similar thin client
- emphasize clarity and evidence workflow over ornamental UI

### Supporting tools
- Pydantic models for domain objects
- background task runner for ingest and indexing
- structured logging
- export templates for Markdown and appendix generation

---

## Immediate Engineering Priorities
If execution starts now, these should happen first.

### Priority 1
Create an internal `woodward_core` or equivalent shared library to unify logic currently spread across scripts.

### Priority 2
Define and implement the canonical data model for:
- Claim
- ResponseRequest
- Response
- EvidenceBundle
- SourceExcerpt

### Priority 3
Create a local FastAPI service with a minimal but stable set of endpoints for search, claims, vendors, governance, and evidence.

### Priority 4
Build a source-coverage and totals-validation layer.

### Priority 5
Build the first minimal UI:
- search
- entity detail
- claim detail
- evidence drilldown
- rebuttal tracker

---

## Things Not To Do Yet
To avoid wasting time, do not prioritize these early:
- broad public-facing portal
- generic chatbot shell as the main interface
- polished design system before core workflows exist
- complex auth if the product is still single-user local-first
- over-optimizing vector search before claim/provenance workflows are in place
- replacing all scripts before the core service layer exists

---

## Suggested Milestones

### Milestone 1: Operational Backbone
- Neo4j stable
- ingest commands standardized
- service layer skeleton created
- canonical data model defined

### Milestone 2: Investigative Core
- claims implemented
- evidence trace implemented
- rebuttal tracking implemented
- core search endpoints working

### Milestone 3: Reporter Workbench
- entity pages
- claim pages
- document viewer
- export bundles

### Milestone 4: Editorial Readiness
- review states
- fact-check workflow
- publication readiness tracking
- reproducible evidence packages

---

## Practical Timeline
A realistic build sequence, assuming focused work and no major ingestion surprises:

- **Phase 0-1:** 1 to 2 weeks
- **Phase 2-3:** 2 to 3 weeks
- **Phase 4-5:** 3 to 4 weeks
- **Phase 6:** 2 to 3 weeks

Total practical path to a credible first-version investigative app:
**8 to 12 weeks**

That assumes disciplined scope.

---

## Final Recommendation
The right next move is not more draft writing and not more disconnected scripts.

The right next move is to build the system around three first-class concepts:
- **Claim**
- **Evidence**
- **Response**

And to expose those through:
- a unified local API
- a thin investigative UI
- a reproducible export pipeline

That is the shortest path from WoodWard as a powerful repo to WoodWard as a real investigative journalist app.
