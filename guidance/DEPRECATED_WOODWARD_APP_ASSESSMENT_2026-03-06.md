# WoodWard App Assessment (March 6, 2026)

## Executive Verdict
WoodWard is **not yet an investigative-journalist app**.

It is a **serious investigative data and evidence system** with meaningful infrastructure already in place: SQLite, Neo4j, LanceDB, loaders, analysis scripts, evidence packaging, and a strong editorial/research methodology. But it still behaves like a **research workbench for a single power user**, not a product that a reporter, editor, or collaborating newsroom could use safely and efficiently.

My blunt assessment:
- **As a research engine:** strong
- **As an internal analyst toolkit:** usable
- **As an application:** weak
- **As an investigative journalist platform:** incomplete

If I had to summarize it in one sentence: **WoodWard has a good backend brain, but almost no finished app body.**

---

## What WoodWard Actually Is Today
At present, WoodWard is best understood as a hybrid of five things:

1. **An evidence repository**
   - Source documents, PDFs, board materials, contracts, emails, briefings, and article drafts are organized in the filesystem.

2. **A forensic data pipeline**
   - Data is ingested from warrant registers, F-195 reports, staffing exports, salary files, and board records.

3. **A multi-database investigation environment**
   - SQLite stores detailed tabular data.
   - Neo4j stores relationships and investigative entities.
   - LanceDB stores embedded document chunks for semantic search.

4. **A script-driven analyst toolkit**
   - Investigation tasks are performed through Python loaders and one-off analysis scripts.

5. **An editorial production environment**
   - The repo contains briefings, article drafts, handoff files, guidance, and publication-oriented narrative work.

That is a strong foundation, but it is not the same as having an app.

---

## What Is Working Well

### 1. The data model direction is correct
The project is moving toward the right architecture for investigative work:
- relational/tabular detail for raw payments and budgets
- graph structure for entities, approvals, governance, and relationships
- vector search for contracts and longform documents

That is the right shape for this domain.

### 2. Neo4j now works in a stable Compose path
I fixed the Neo4j runtime issue during this session.

Current state:
- `woodward-neo4j` runs cleanly under Compose on `7475` and `7688`
- both `neo4j` and `system` databases are online
- the graph contains substantive data, not just test seed data

Observed graph contents:
- `Payment`: 25,578 nodes
- `Vendor`: 4,442 nodes
- `Employee`: 240 nodes
- `Document`: 180 nodes
- `BoardMeeting`: 53 nodes
- `Contract`: 55 nodes
- `AgendaItem`: 55 nodes

Relationship types already loaded include:
- `RECEIVED_PAYMENT`
- `EXTRACTED_FROM`
- `IN_FISCAL_YEAR`
- `WORKS_FOR`
- `EMPLOYED_IN`
- `AUTHORIZES`
- `HAS_ITEM`
- `PARTY_TO`
- `VOTED`
- `BUDGETED`
- `REBRANDED_FROM`
- `SUBSIDIARY_OF`

This matters. Neo4j is no longer hypothetical here. It is a working component.

### 3. The repo already has meaningful investigative primitives
Representative examples:
- `scripts/loaders/ingest_payments.py`
- `scripts/loaders/ingest_board_governance.py`
- `scripts/loaders/vendor_normalization.py`
- `scripts/analysis/query_contracts.py`
- `scripts/analysis/analyze_vendors.py`
- `scripts/analysis/cost_comparison.py`

These are not toy files. They are the beginnings of a real investigative system.

### 4. The editorial thinking is unusually strong
The repo contains a lot of superficial or repetitive drafting material, but underneath that there is a serious editorial method:
- evidence-first framing
- source traceability
- repeated emphasis on rebuttal, verification, and primary records
- a clear theory of the story

That gives the project direction. Many projects have data and no editorial spine. WoodWard has the opposite problem: it has more editorial ambition than product maturity.

---

## What WoodWard Is Missing
This is the critical section.

### 1. There is no real app interface
There is no actual journalist-facing interface for the core jobs this system should support.

What exists instead:
- Python scripts
- Markdown instructions
- manual file handling
- ad hoc terminal queries
- hand-built workspaces
- dispatch-style prompts

That means the effective user right now is not “a journalist.” The effective user is “the project architect who understands the filesystem, the scripts, the story, and the quirks.”

That is not an app. That is an expert-operated environment.

### 2. The workflow is fragmented across too many layers
The repo still spreads work across:
- filesystem evidence folders
- SQLite
- Neo4j
- LanceDB
- raw CSVs
- derived CSVs
- Python scripts
- Markdown briefings
- article drafts
- manual external search processes

This fragmentation is survivable for one disciplined operator. It is a major liability for collaboration, reproducibility, and editorial trust.

### 3. There is no durable claims system
An investigative journalism app needs a core object stronger than “script output” or “article paragraph.” It needs a **claim model**.

For each claim, the system should know:
- exact wording
- current status
- supporting documents
- supporting rows or graph paths
- confidence level
- verification status
- rebuttal status
- publication readiness
- who last edited it
- when it changed

WoodWard does not currently appear to have this.

That is one of the biggest product gaps.

### 4. There is no editorial workflow engine
A serious investigative app should support:
- lead tracking
- evidence review
- source review
- right-of-reply tracking
- legal review
- fact-check status
- edit history
- publication approval gates

Right now that work is distributed across Markdown files, ad hoc notes, and human memory.

That is workable for a solo operator. It is weak for any newsroom-grade system.

### 5. There is no provenance UI
The data exists, but the system does not yet expose provenance in a journalist-friendly way.

A journalist app should let a user move cleanly from:
- headline figure
n- to aggregated query result
- to individual rows
- to source document
- to page/chunk
- to the exact text or record supporting the claim

WoodWard’s data model is moving in that direction, but the experience is still manual.

### 6. Governance and contract extraction are still brittle
`scripts/loaders/ingest_board_governance.py` is useful, but it is heuristic and fragile.

Current weaknesses include:
- rough date extraction
- rough vote extraction
- simplistic vendor detection
- broad assumptions about unanimous board voting
- contract creation based on inferred rather than authoritative identifiers

That is acceptable for exploratory graph-building. It is not sufficient for publication-grade governance claims without secondary verification.

### 7. The vector side is useful but not productized
The contract search layer is real, but `scripts/analysis/query_contracts.py` is still a script-oriented tool, not a user-facing investigative surface.

It prints results and writes dispatch bundles. That is fine internally, but it is not how reporters or editors should consume this information in a finished app.

### 8. The repo contains too much strategic and narrative duplication
There are many master plans, handoff files, status files, artifact files, workspaces, drafts, and historical notes. That is understandable in an active investigation, but as a product it becomes noise.

A real app should reduce duplication by making the system state queryable rather than repeatedly re-describing it in documents.

---

## Technical Assessment

### Current technical strengths
- local-first architecture
- clean project isolation from other databases
- meaningful graph schema already populated
- working loader structure
- usable semantic search sidecar
- evidence package generation discipline
- a clear move toward Neo4j as the analytical center

### Current technical weaknesses
- hardcoded credentials and local config assumptions
- many one-off scripts instead of a stable service layer
- no unified API
- no job orchestration layer
- no formal test coverage around ingestion correctness
- no central schema enforcement across all stores
- loader logic mixes extraction, normalization, and publishing responsibilities
- weak deduplication and provenance UI for article-ready facts

### Specific code-level observations
- `scripts/loaders/ingest_payments.py` is solid as an ingestion bridge, but it is still tightly coupled to local paths and a specific Neo4j endpoint.
- `scripts/loaders/ingest_board_governance.py` is a good prototype, but not a sufficiently reliable governance parser for critical claims.
- `scripts/analysis/query_contracts.py` proves the LanceDB layer is useful, but it is still a script for analysts, not a reusable application service.
- `workspaces/Cicero_Clone/src/adapters/neo4j.py` suggests there is the beginning of a reusable retrieval layer, but it is not yet WoodWard’s integrated app backbone.

---

## What Needs To Be Done To Make This an Investigative Journalist App
The right answer is not “add a pretty frontend.” The right answer is to build the missing operational middle layer between the databases and the reporting workflow.

### Phase 1: Turn WoodWard into a reliable investigative system
This is the first thing that must happen.

#### 1. Make Neo4j the primary relationship/query layer
Now that the service is fixed, the next step is to make it operationally central.

Do this:
- keep raw source storage on disk
- keep LanceDB as semantic sidecar
- keep SQLite only as staging/archive input if necessary
- route relationship-heavy investigative queries through Neo4j

Do not do this:
- continue splitting core truth across ad hoc SQLite queries, separate CSVs, and graph outputs without a unified access pattern

#### 2. Build a service layer
Create a small internal service, even if local-only, that exposes the important operations:
- search documents
- retrieve claim evidence
- retrieve vendor spending by year
- retrieve board approvals by vendor
- retrieve payment trails
- retrieve contract clauses
- retrieve source links for any aggregate claim

This can be a lightweight FastAPI app even if there is no public UI yet.

Without this, every new question keeps becoming a new script.

#### 3. Add a first-class claim registry
This is the single most important product feature after service unification.

Add entities like:
- `Claim`
- `EvidenceBundle`
- `ResponseRequest`
- `Response`
- `ReviewDecision`

Every major article assertion should become a claim object with linked sources and status.

#### 4. Add provenance as a first-class feature
Every aggregate needs traceability.

For example:
- claim: “Amergis received X in FY24-25”
- graph path: `Vendor -> Payment -> FiscalYear`
- supporting rows: payment IDs
- source documents: warrant register PDFs
- article usage: Article 1, Article 2

That traceability should be inspectable without reading code.

#### 5. Create repeatable ingestion commands
Right now the architecture is script-heavy.

You need standard commands such as:
- rebuild graph from source inputs
- refresh payment ingest
- refresh contract document index
- rebuild board governance edges
- validate source coverage
- validate totals against canonical expected outputs

This should be operationally deterministic.

---

## Phase 2: Build the journalist workflow layer
This is what turns a backend into an app.

### 1. Lead management
Track:
- open leads
- priority
- evidence status
- blocker
- next action
- owner
- linked entities

### 2. Source and document workspace
A journalist should be able to:
- open a vendor
- see all related contracts, board actions, payments, and notes
- open a board meeting
- see agenda items, approvals, and linked documents
- open a claim
- see all source support and rebuttal activity

### 3. Right-of-reply workflow
This should be a system feature, not a folder convention.

Needs:
- contact registry
- question sets
- sent dates
- response deadlines
- response status
- quoted response snippets
- unresolved questions
- publication readiness flag

### 4. Fact-check workflow
A finished investigative app must support:
- claim review
- number verification
- quote verification
- source completeness review
- legal risk review
- final publish signoff

### 5. Search designed for journalists, not engineers
A reporter should be able to ask:
- “show every board approval tied to Amergis or Maxim”
- “what is the support for the 3 million versus 11 million claim?”
- “which documents mention automatic renewal or placement fee?”
- “show every year where Object 7 overspent budget”

That should not require Python.

---

## Phase 3: Build the editorial product layer
This is what makes it feel like an investigative newsroom tool.

### Must-have features
- dashboard for the current investigation
- entity pages for vendors, officials, contracts, and districts
- claim pages with evidence and status
- timeline view
- document viewer with highlighted citations/chunks
- chart builder for publishable visuals
- export to reporter memo, editor memo, and evidence appendix

### Strongly recommended features
- contradiction detection
- missing-source alerts
- stale-claim alerts when new records arrive
- automatic exhibit index generation
- per-article claim bundles
- newsroom-style notebook or annotation system

---

## What Should Improve Immediately
These are the highest-value practical improvements.

### 1. Replace script sprawl with commands or services
The current repo has too many scripts that encode business logic in isolated places.

Immediate improvement:
- define a small set of supported operational commands
- move shared logic into reusable library modules
- reduce analyst dependence on file-by-file script knowledge

### 2. Normalize the data contract between stores
Right now the databases coexist, but the boundaries are not product-clean enough.

You should define clearly:
- what belongs in Neo4j
- what belongs in LanceDB
- what remains on disk only
- what is archival only
- what is deprecated

### 3. Add source coverage validation
Before publication, the system should be able to answer:
- which claims lack primary source support
- which years lack source files
- which entities have inferred but not verified relationships
- which contract years are missing
- which rebuttals are still absent

### 4. Reduce hardcoded assumptions
The current stack assumes:
- local file paths
- one user
- one machine
- one active investigation
- one credential set

That is fine for a prototype, but it blocks scale and collaboration.

### 5. Add tests around numbers that matter
You need automated validation for:
- annual payment totals
- vendor normalization outputs
- fiscal year bucketing
- graph node/edge counts after ingestion
- duplicate suppression
- consistency between tabular and graph aggregates

---

## Investigative Journalism Capability Gap
To be blunt, the largest gap is not technical. It is operational.

A real investigative-journalist app must help with:
- uncertainty
- disputed facts
- source insufficiency
- chronology
- accountability
- rebuttal
- legal defensibility
- publication workflow

WoodWard currently helps most with:
- data aggregation
- exploratory analysis
- narrative drafting
- evidence packaging

Those are useful, but not sufficient.

The project still needs to become better at:
- structured claim management
- structured editorial review
- structured rebuttal handling
- structured provenance exposure
- structured collaboration

That is the difference between “investigation in a repo” and “investigative app.”

---

## Recommended Product Direction
If I were setting the direction, I would not try to make this into a broad newsroom CMS. I would make it a **focused investigative workbench**.

### The correct product identity
WoodWard should become:
- a local-first investigative workbench
- optimized for public records, budget forensics, governance tracing, and vendor relationships
- built for one lead reporter plus editor/fact-check/legal collaborators

It should not try to be:
- a general-purpose writing app
- a general note-taking tool
- a generic RAG chatbot
- a broad document management suite

The narrow, strong product is better.

---

## Recommended Build Sequence

### Sequence 1: stabilize the backend
- keep the Neo4j Compose fix in place
- formalize Neo4j as the primary analytical graph
- keep LanceDB as semantic sidecar
- define a stable service/API layer

### Sequence 2: build the investigative model
- claims
- sources
- rebuttals
- entities
- relationships
- exhibits
- reviews

### Sequence 3: build the user workflows
- search
- timelines
- evidence drilldown
- claim review
- right-of-reply tracking
- export bundles

### Sequence 4: build the visual app shell
- lightweight web UI
- entity pages
- claim pages
- evidence explorer
- charts and exports

---

## Neo4j Changes Made In This Session
These changes should be considered part of the current system assessment.

### What was wrong
- `woodward-neo4j` failed under the stock Docker image startup path.
- The database store itself was healthy, but the default entrypoint path caused startup instability.
- A temporary manual container proved the data was intact and queryable.

### What was changed
`docker-compose.yml` was updated to:
- start Neo4j using a working terminal-style startup path
- use the current `server.memory.heap` env keys instead of deprecated `dbms.memory.heap` keys

### Result
- the Compose-managed `woodward-neo4j` service now starts successfully
- the original intended ports work again: `7475` and `7688`
- the graph is online and queryable through `cypher-shell`

### Product significance
This is more than a devops footnote.

It changes the assessment in two ways:
1. Neo4j can now be treated as an actually available component, not an aspirational one.
2. The project is closer to a usable investigative platform because one of its core infrastructure pieces is no longer operationally brittle.

That said, this does **not** by itself make WoodWard an app. It just removes one major blocker.

---

## Final Assessment
WoodWard is already valuable. It is just valuable in the wrong form.

Right now it is strongest as:
- an investigative backend
- a forensic evidence environment
- a power-user research system

It is weakest as:
- a product
- a collaborative reporting tool
- a journalist-facing app
- a publication workflow system

### My bottom line
If you want WoodWard to become a true investigative journalist app, the next major step is **not another article draft and not another isolated script**.

The next major step is to build the missing middle layer:
- service/API
- claim system
- provenance system
- rebuttal workflow
- investigative UI

That is what turns the current repo from a capable research operation into a real tool.

## Priority Recommendation
If you only do three things next, do these:

1. **Build a unified local API over Neo4j + LanceDB + source files.**
2. **Create a first-class claim/evidence/rebuttal data model.**
3. **Build a minimal investigative UI for search, entity drilldown, and claim verification.**

Everything else is secondary.
