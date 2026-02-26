# WoodWard Neo4j Re-Ingestion — VS Code Handoff

**Prepared by:** Antigravity IDE + VS Code (GitHub Copilot)  
**Last Updated:** February 19, 2026  
**Purpose:** Wipe and rebuild the WoodWard Neo4j knowledge graph from raw source files. **Neo4j becomes the single analytical store**, replacing the fragmented SQLite/CSV/LanceDB architecture. SQLite and CSVs are consumed as migration inputs and decommissioned as query targets. LanceDB is kept only as a vector search sidecar, bridged to the graph via `lance_id` on Document nodes.

> [!IMPORTANT]
> **READ FIRST:** The detailed, phased implementation plan with all code, cypher, exit gates, risk register, and file manifest is in `IMPLEMENTATION_PLAN.md`. This handoff gives you the context and ground truth you need to execute that plan. Nothing has been executed yet — phases 0-10 are all pending.

---

## 1. CONNECTION DETAILS

### Neo4j (Docker Container: `woodward-neo4j`)

| Parameter | Value |
|---|---|
| **Protocol** | `neo4j://localhost:7688` |
| **Bolt Port** | `7688` (mapped from container `7687`) |
| **HTTP Browser** | `http://localhost:7475` (mapped from `7474`) |
| **Username** | `neo4j` |
| **Password** | `woodward_secure_2024` |
| **Database** | `neo4j` (default) |
| **Image** | `neo4j:5.15.0` |
| **APOC Plugin** | Enabled |
| **Heap** | 512MB initial / 1GB max |
| **Volumes** | `~/neo4j/woodward/data`, `~/neo4j/woodward/logs`, `~/neo4j/woodward/import` |
| **Docker Compose** | `~/Projects/WoodWard/docker-compose.yml` |
| **Container Status** | Verified UP as of Feb 19, 2026 |

> [!IMPORTANT]
> Use `neo4j://` scheme, NOT `bolt://`. The `bolt://` scheme triggers an "Unsupported authentication token" error with this configuration.

> [!WARNING]
> This is a **separate instance** from CaseLawDB (which runs on standard ports `7474`/`7687`). Do NOT connect to the wrong instance.

### .env File (`~/Projects/WoodWard/.env`) — NEEDS FIX
```env
NEO4J_URI=bolt://localhost:7688   # ← BUG: Update this to neo4j://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=woodward_secure_2024
SQLITE_DB=data/woodward.db
LANCEDB_PATH=data/vectors/
```
**First action in Phase 0:** Change `bolt://` → `neo4j://`.

---

## 2. ARCHITECTURE DECISION

### Before (Current — Fragmented)
```
SQLite ──┐
CSVs  ───┤──→ Ad-hoc Python scripts ──→ Matplotlib charts
LanceDB ─┘                              Manual cross-referencing
Neo4j (23 test nodes, unused)
```

### After (Target — Unified Graph + Vector)
```
┌─────────────────────────────────────────────┐
│              NEO4J GRAPH                    │
│  (Single source of truth for all queries)   │
│                                             │
│  Payments ← Vendors ← Contracts            │
│  Budget Objects ← Fiscal Years             │
│  Board Meetings → Agenda Items → Votes     │
│  Employees → Organizations                 │
│  Documents (with lance_id bridge)          │
└──────────────┬──────────────────────────────┘
               │ lance_id FK
               ▼
       ┌───────────────┐
       │   LanceDB     │
       │ (Vector sidecar│
       │  for semantic  │
       │  search only)  │
       └───────────────┘
```

**Neo4j is the database.** LanceDB is kept because re-embedding 992 chunks would cost OpenAI API money for zero gain. It is queried only for semantic search; results join back to the graph via `lance_id` on `(:Document)` nodes.

**SQLite is decommissioned after migration.** It remains on disk as an archival artifact but is no longer queried by any analysis script.

---

## 3. CRITICAL ENTITY: THE AMERGIS CORPORATE CHAIN

> [!CAUTION]
> **This is the single most important normalization requirement.** The investigation's primary target vendor uses THREE names that are the SAME legal entity. Getting this wrong breaks every investigative query.

| Name as it appears | Where it appears | Era |
|---------------------|------------------|-----|
| **MAXIM HEALTHCARE SERVICES INC** | SQLite `payee` (299 records, $28.2M), PDF filenames, LanceDB content | Pre-2022, overlaps through 2024 |
| **AMERGIS HEALTHCARE STAFFING INC** | SQLite `payee` (99 records, $39M) | 2023-24 onward |
| **Amergis Education** | Board meeting minutes in LanceDB: *"Recommendation to Approve a Client Services Agreement Between the Vancouver Public Schools and Amergis Education (formerly Maxim Healthcare) for VPS Students for the 2024-25 SY"* | Board approval language for 2024-25 contracts |

**All three names normalize to: `"Amergis/Maxim"`**

Corporate facts:
- **Parent company:** Maxim Healthcare Services (Columbia, MD)
- **Rebrand year:** 2022
- **Fraud history:** $150M Medicaid fraud settlement (2011) — billing for services not rendered, falsified timesheets
- **Transition fingerprint:** In 2022-23, VPS paid Maxim $14.4M and Amergis $0. By 2024-25, Maxim received $46,625 and Amergis received $11.89M. Same entity, new name.
- **Combined total in SQLite:** $67,255,003.75

### Pioneer Disambiguation (Four Separate Entities)

| Payee in SQLite | Normalized Name | Type | Investigation Target? |
|-----------------|----------------|------|----------------------|
| PIONEER HEALTHCARE SERVICES LLC | Pioneer Healthcare | Staffing Agency | **YES** |
| PIONEER TRUST BANK/CORP INC | Pioneer Trust Bank | Bank | NO |
| PIONEER CREDIT RECEOVERY | Pioneer Credit Recovery | Collections | NO |
| PIONEER ATHLETICS | Pioneer Athletics | Supply | NO |

---

## 4. CURRENT STATE (Verified by Audit — Feb 19, 2026)

### Neo4j — Test Seed Data (WIPE THIS)
- **23 nodes**: 9 `BudgetObject`, 6 `Person`, 4 `Organization`, 3 `FiscalYear`, 1 unlabeled
- **30 relationships**: 20 `SPENT`, 5 `GOVERNS`, 3 `PART_OF`, 1 `EMPLOYED_BY`, 1 `HAS_BUDGET`
- This is test data. Safe to wipe via `MATCH (n) DETACH DELETE n;`

### SQLite (`data/woodward.db`, 33.9MB) — Migration Input (Read-Only After)

**Table: `payments`** — 55,191 rows, the core dataset.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `source_file` | TEXT | PDF filename the payment was extracted from |
| `source_path` | TEXT | Full path to source PDF |
| `document_date` | TEXT | Date on the warrant register document |
| `entry_date` | TEXT | Payment entry date (format: `MM/DD/YYYY`) |
| `payee` | TEXT | Vendor/payee name (4,442 unique) |
| `amount` | REAL | Payment amount in USD |
| `raw_line` | TEXT | Original text line from the PDF |
| `created_at` | TIMESTAMP | Ingestion timestamp |

**Reconciliation Targets (must match exactly in Neo4j after ingestion):**

| Metric | Value |
|--------|-------|
| Total rows | 55,191 |
| Total payment volume | $1,280,735,263.81 |
| Unique payees | 4,442 |
| Unique source files | 125 |
| Entry date range | 01/02/2024 to 12/31/2025 |
| AMERGIS HEALTHCARE STAFFING INC | 99 records, $39,039,941.67 |
| MAXIM HEALTHCARE SERVICES INC | 299 records, $28,215,062.08 |
| SOLIANT HEALTH LLC | 182 records, $2,472,914.44 |
| PIONEER HEALTHCARE SERVICES LLC | 58 records, $268,175.00 |

**Other SQLite tables (all empty or trivial):** `fiscal_years` (3 rows), `budget_objects` (9 rows), `budget_items` (20 rows). Tables `vendors`, `vendor_contracts`, `vendor_payments`, `people`, `board_votes`, `documents` are all 0 rows. Schema in `data/schema.sql`.

### LanceDB (`data/lancedb/woodward_contracts.lance`) — Keep as Vector Sidecar

| Metric | Value |
|--------|-------|
| Total chunks | 992 |
| Unique source_document_ids | **55** (not 193 — only 55 of 193 PDFs were embedded) |
| Embedding model | `text-embedding-3-small` (OpenAI, 1536 dims) |
| Columns | `id`, `content`, `embedding`, `source_document_id`, `citation_key`, `chunk_index`, `workspace_id`, `metadata` |
| Chunks mentioning "Amergis Education" | **8** (from 3 source docs — board meeting minutes) |
| Chunks mentioning "Amergis" (any form) | **16** |

> [!TIP]
> **Do NOT re-embed.** Create `(:Document)` nodes in Neo4j with a `lance_id` property matching the LanceDB `source_document_id`. This bridges graph queries to vector search.

### Scraped PDFs — 193 Files
**Location:** `workspaces/VPS-Board-Scraper/documents/contracts/`

| Prefix | Actual Count (verified) | Content Types |
|--------|------------------------|---------------|
| `Amergis_*` | 24 | Warrant registers, meeting minutes |
| `Maxim_*` | **84** | Contracts, warrant registers, meeting minutes |
| `Pioneer_*` | **35** | Contracts, meeting minutes, warrant registers |
| `Soliant_*` | **50** | Contracts, warrant registers, meeting minutes |

Three document types are mixed: (1) Board Warrant Registers (already in SQLite), (2) Master Service Agreements (already in LanceDB), (3) Board Meeting Minutes (need LLM extraction for votes).

---

## 5. ALL DATA SOURCES — COMPLETE INVENTORY

| Source | Location | Size | Records | Status |
|--------|----------|------|---------|--------|
| SQLite `payments` | `data/woodward.db` | 33.9MB | 55,191 rows | **Input** — consume into Neo4j |
| SQLite budget tables | `data/woodward.db` | tiny | 3 FYs, 20 items | Already in `load_budget.cypher` |
| LanceDB | `data/lancedb/` | ~50MB | 992 chunks / 55 docs | **Keep** — bridge via `lance_id` |
| Scraped PDFs | `workspaces/VPS-Board-Scraper/documents/contracts/` | ~200MB | 193 files | Already parsed into SQLite + LanceDB |
| Top40 Salary CSVs | `data/salaries/Top40_*.csv` | 10KB | 5 files × 40 records | **Input** → Employee nodes |
| VPS Salary Summaries | `data/salaries/VPS_*.csv` | 10KB | 2 files | **Input** |
| S-275 Full Exports | `data/salaries/S275_*.csv` | **886MB** | 5 years statewide | Optional — filter `codist=06037` for VPS |
| F-195 Budget PDFs | `documents/F195/` | 12MB | 4 files | Already extracted; `load_budget.cypher` |
| OSPI Staffing XLSX | `data/ospi/StaffingTables_2324.xlsx` | 686KB | 1 file | **Input** → peer benchmarks |
| Staffing Benchmark CSV | `data/ospi/Staffing_Benchmark_2324.csv` | **0KB** | Empty | Needs regeneration from XLSX |
| VPS Staffing Trend CSV | `data/ospi/VPS_Staffing_Trend_5yr.csv` | **0KB** | Empty | Needs regeneration |
| Vendor Spending Annual | `documents/visualizations/vendor_spending_annual.csv` | **0KB** | Empty | Regenerate from Neo4j |
| SPED Contractor Annual | `documents/visualizations/sped_contractor_annual.csv` | **0KB** | Empty | Regenerate from Neo4j |
| Cost Comparison | `documents/cost_comparison.csv` | 1KB | ~10 roles | **Input** → CostBenchmark nodes |
| Budget Cypher | `data/load_budget.cypher` | small | 3 FYs × ~7 objs | Ready to load into Neo4j |
| Neo4j Schema Cypher | `data/neo4j_schema.cypher` | small | Seed data | Needs expansion per IMPLEMENTATION_PLAN.md |

---

## 6. PROPOSED NEO4J GRAPH SCHEMA

### Node Labels

```cypher
(:Organization {name, type, ubi, enrollment_2024, hq, notes})
  // type: "School District", "Staffing Agency", "Department", "Parent Company"

(:Person {name, role, position, start_date, salary, notes})
  // role: "Superintendent", "Board Member", "Director", "CFO"

(:FiscalYear {label, start_date, end_date})
  // label: "2024-25", start_date: date("2024-09-01"), end_date: date("2025-08-31")
  // WA school fiscal year: September 1 – August 31

(:BudgetObject {name, object_code, description})
  // name: "Purchased Services", object_code: 5

(:Vendor {name, normalized_name, vendor_type, parent_company, notes})
  // name: raw payee from SQLite (preserved for provenance)
  // normalized_name: "Amergis/Maxim" (for both AMERGIS and MAXIM payees)
  // vendor_type: "Staffing Agency", "Bank", "Collections", "Supply", "Unknown"

(:Payment {amount, entry_date, document_date, raw_line, source_file})
  // entry_date stored as Neo4j date() type (YYYY-MM-DD), not MM/DD/YYYY string
  // Individual warrant register line items (55k nodes)

(:Contract {contract_number, description, start_date, end_date, total_value, vendor_name, notes})
  // Parsed from MSA PDFs and board minutes

(:BoardMeeting {date, type, source_file})
  // type: "Regular", "Special", "Committee of the Whole"

(:AgendaItem {number, section, description, dollar_amount})
  // section: "Consent Agenda", "Action Item", "Discussion"

(:Document {filename, document_type, lance_id, lance_chunk_count, mentions_amergis_education})
  // lance_id: bridges to LanceDB source_document_id for vector search
  // document_type: "Warrant Register", "Contract/Minutes", "Board Meeting Minutes", "F-195"

(:Employee {name, position, salary, fte, year})
  // From S-275 / Top40 data (VPS only)
  // Composite unique key: (name, year)

(:CostBenchmark {role, contractor_hourly_mid, contractor_annual, inhouse_annual, premium_dollars, premium_percent})
  // From cost_comparison.csv
```

### Relationship Types

```cypher
// Organizational Structure
(Person)-[:EMPLOYED_BY {position, start_date}]->(Organization)
(Person)-[:GOVERNS]->(Organization)
(Organization)-[:PART_OF]->(Organization)       // VPS departments → VPS
(Vendor)-[:SUBSIDIARY_OF {since, notes}]->(Organization)   // Amergis → Maxim parent
(Vendor)-[:REBRANDED_FROM {year}]->(Vendor)     // Amergis → Maxim (rebrand 2022)

// Financial Flow (THE CORE — "Follow the Money")
(Organization)-[:HAS_BUDGET]->(FiscalYear)
(FiscalYear)-[:SPENT {amount, formatted, source}]->(BudgetObject)
(Vendor)-[:RECEIVED_PAYMENT]->(Payment)
(Payment)-[:IN_FISCAL_YEAR]->(FiscalYear)
(Payment)-[:EXTRACTED_FROM]->(Document)
(Vendor)-[:SPENT_IN_YEAR {total_amount, payment_count}]->(FiscalYear)  // Materialized aggregate

// Contract Chain
(Vendor)-[:PARTY_TO]->(Contract)
(Organization)-[:PARTY_TO]->(Contract)
(Contract)-[:APPROVED_AT]->(BoardMeeting)
(Contract)-[:COVERS_PERIOD]->(FiscalYear)

// Board Governance
(BoardMeeting)-[:HAS_ITEM]->(AgendaItem)
(AgendaItem)-[:AUTHORIZES]->(Contract)
(Person)-[:VOTED {vote: "YES"|"NO"|"ABSTAIN"|"ABSENT"}]->(AgendaItem)
(Person)-[:ATTENDED]->(BoardMeeting)

// Staffing
(Employee)-[:WORKS_FOR]->(Organization)
(Employee)-[:EMPLOYED_IN]->(FiscalYear)
```

### Constraints & Indexes

```cypher
// Uniqueness Constraints
CREATE CONSTRAINT vendor_name IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE;
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT org_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE;
CREATE CONSTRAINT doc_filename IF NOT EXISTS FOR (d:Document) REQUIRE d.filename IS UNIQUE;
CREATE CONSTRAINT fy_label IF NOT EXISTS FOR (fy:FiscalYear) REQUIRE fy.label IS UNIQUE;
CREATE CONSTRAINT budget_obj_code IF NOT EXISTS FOR (bo:BudgetObject) REQUIRE bo.object_code IS UNIQUE;

// Composite Constraints
CREATE CONSTRAINT employee_key IF NOT EXISTS FOR (e:Employee) REQUIRE (e.name, e.year) IS UNIQUE;
CREATE CONSTRAINT meeting_unique IF NOT EXISTS FOR (m:BoardMeeting) REQUIRE (m.date, m.type) IS UNIQUE;

// Performance Indexes
CREATE INDEX payment_amount IF NOT EXISTS FOR (p:Payment) ON (p.amount);
CREATE INDEX payment_entry_date IF NOT EXISTS FOR (p:Payment) ON (p.entry_date);
CREATE INDEX payment_source_file IF NOT EXISTS FOR (p:Payment) ON (p.source_file);
CREATE INDEX vendor_normalized IF NOT EXISTS FOR (v:Vendor) ON (v.normalized_name);
CREATE INDEX vendor_type IF NOT EXISTS FOR (v:Vendor) ON (v.vendor_type);
CREATE INDEX person_role IF NOT EXISTS FOR (p:Person) ON (p.role);
CREATE INDEX doc_type IF NOT EXISTS FOR (d:Document) ON (d.document_type);
CREATE INDEX doc_lance_id IF NOT EXISTS FOR (d:Document) ON (d.lance_id);
CREATE INDEX employee_position IF NOT EXISTS FOR (e:Employee) ON (e.position);
CREATE INDEX org_type IF NOT EXISTS FOR (o:Organization) ON (o.type);
```

---

## 7. VENDOR NORMALIZATION MAP

This must be implemented as a Python module (`scripts/loaders/vendor_normalization.py`) used by all ingestion scripts. The full code is in `IMPLEMENTATION_PLAN.md` Phase 2.

```python
VENDOR_ALIASES = {
    # === THE PRIMARY TARGET: Amergis/Maxim (SAME ENTITY) ===
    "AMERGIS HEALTHCARE STAFFING INC": {
        "normalized_name": "Amergis/Maxim",
        "vendor_type": "Staffing Agency",
        "parent_company": "Maxim Healthcare Services",
        "aliases": ["Amergis Education", "Amergis Healthcare", "Amergis Staffing",
                    "AMERGIS EDUCATION", "AMERGIS EDUCATION STAFFING"],
        "notes": "Rebranded from Maxim Healthcare Staffing in 2022. $150M Medicaid fraud settlement (2011).",
    },
    "MAXIM HEALTHCARE SERVICES INC": {
        "normalized_name": "Amergis/Maxim",
        "vendor_type": "Staffing Agency",
        "parent_company": "Maxim Healthcare Services",
        "aliases": ["Maxim Healthcare Staffing", "Maxim Healthcare"],
        "notes": "Pre-rebrand name. Same entity as Amergis Healthcare Staffing.",
    },
    "SOLIANT HEALTH LLC": {
        "normalized_name": "Soliant Health",
        "vendor_type": "Staffing Agency",
        "parent_company": None,
        "aliases": ["Soliant"],
        "notes": "Competitor to Amergis in VPS staffing ecosystem.",
    },
    "PIONEER HEALTHCARE SERVICES LLC": {
        "normalized_name": "Pioneer Healthcare",
        "vendor_type": "Staffing Agency",
        "parent_company": None,
        "aliases": [],
        "notes": "Staffing agency — investigation target.",
    },
    "PIONEER TRUST BANK/CORP INC": {
        "normalized_name": "Pioneer Trust Bank",
        "vendor_type": "Bank",
        "parent_company": None,
        "aliases": [],
        "notes": "Financial institution. NOT a staffing vendor.",
    },
    "PIONEER CREDIT RECEOVERY": {
        "normalized_name": "Pioneer Credit Recovery",
        "vendor_type": "Collections",
        "parent_company": None,
        "aliases": [],
        "notes": "Collections agency. Unrelated to staffing.",
    },
    "PIONEER ATHLETICS": {
        "normalized_name": "Pioneer Athletics",
        "vendor_type": "Supply",
        "parent_company": None,
        "aliases": [],
        "notes": "Athletic supplies. Unrelated to staffing.",
    },
}

TARGET_VENDORS = {"Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"}
```

---

## 8. KEY QUERIES THE GRAPH MUST SUPPORT

```cypher
// 1. Total payments to target vendors by fiscal year
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
WHERE v.normalized_name IN ["Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"]
RETURN v.normalized_name, fy.label, sum(p.amount) as total, count(p) as payments
ORDER BY fy.label, total DESC;

// 2. Amergis/Maxim rebrand timeline (THE KEY INVESTIGATIVE QUERY)
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
WHERE v.normalized_name = "Amergis/Maxim"
RETURN v.name, fy.label, count(p) as payments, sum(p.amount) as total
ORDER BY fy.label, v.name;
// Shows: Maxim declining, Amergis exploding — same entity

// 3. Purchased Services as % of total budget
MATCH (fy:FiscalYear)-[s:SPENT]->(bo:BudgetObject)
WITH fy, sum(s.amount) as total_budget,
     sum(CASE WHEN bo.name = "Purchased Services" THEN s.amount ELSE 0 END) as obj7
RETURN fy.label, obj7, total_budget, round(obj7/total_budget * 100, 2) as pct
ORDER BY fy.label;

// 4. Vendor payment frequency per warrant register (consent agenda opacity)
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:EXTRACTED_FROM]->(d:Document)
WHERE v.normalized_name = "Amergis/Maxim"
RETURN d.filename, count(p) as payment_count, sum(p.amount) as meeting_total
ORDER BY meeting_total DESC;

// 5. Superintendent salary vs. contractor spending trajectory
MATCH (e:Employee {name: "Jeff Snell"})-[:EMPLOYED_IN]->(fy:FiscalYear)
OPTIONAL MATCH (fy)<-[s:SPENT_IN_YEAR]-(v:Vendor {normalized_name: "Amergis/Maxim"})
RETURN fy.label, e.salary as supt_salary, s.total_amount as amergis_total
ORDER BY fy.label;
```

---

## 9. EXECUTION STATUS

**All phases are PENDING.** Nothing has been executed yet. The new chat should begin by executing Phase 0 from `IMPLEMENTATION_PLAN.md`.

| Phase | Description | Duration | Status |
|-------|-------------|----------|--------|
| 0 | Environment Stabilization (fix .env, verify container) | 30 min | **PENDING** |
| 1 | Wipe + Schema Creation (constraints, indexes) | 30 min | **PENDING** |
| 2 | Vendor Normalization Layer (Python module) | 1 hr | **PENDING** |
| 3 | Seed Reference Data (orgs, people, FYs, budget objects) | 30 min | **PENDING** |
| 4 | **Ingest Payments + Vendors + Documents** (55k records) | **2-3 hrs** | **PENDING** |
| 5 | Ingest Budget Data (load_budget.cypher) | 30 min | **PENDING** |
| 6 | LanceDB ↔ Neo4j Bridge (55 Document nodes) | 45 min | **PENDING** |
| 7 | Ingest Salary/Staffing Data (Top40 CSVs) | 1 hr | **PENDING** |
| 8 | Ingest Derived Analysis Data (cost comparison) | 30 min | **PENDING** |
| 9 | Board Governance Data (LLM extraction — parallel track) | 2+ days | **PENDING** |
| 10 | Final Verification + Query Validation | 1 hr | **PENDING** |

**Estimated total: ~7-8 hours** (Phases 0-8, 10). Phase 9 is a parallel 2+ day track.

---

## 10. FILE MAP (Quick Reference)

```
~/Projects/WoodWard/
├── .env                          # Connection credentials (NEEDS FIX: bolt→neo4j)
├── docker-compose.yml            # Neo4j container config
├── IMPLEMENTATION_PLAN.md        # ← FULL PHASED PLAN WITH ALL CODE AND EXIT GATES
├── VS_CODE_HANDOFF.md            # ← THIS FILE
├── VPS_INVESTIGATION_MASTER_PLAN_v2.md  # Investigation strategy (context only)
├── data/
│   ├── woodward.db               # SQLite (55k payments) — MIGRATION INPUT
│   ├── woodward.db.bak           # (to be created in Phase 0)
│   ├── schema.sql                # Old relational schema (archival)
│   ├── neo4j_schema.cypher       # Current seed data (to be replaced in Phase 1)
│   ├── load_budget.cypher        # Budget MERGE commands (load in Phase 5)
│   ├── vendor_mentions.csv       # Currently empty
│   ├── lancedb/                  # Vector DB (992 chunks, 55 docs) — KEEP
│   ├── ospi/                     # OSPI staffing data + XLSX
│   └── salaries/                 # Top40 CSVs + 886MB S-275 full exports
├── documents/
│   ├── F195/                     # 4 budget PDFs
│   ├── contracts/                # Empty (contracts in scraper dir)
│   ├── visualizations/           # Charts + analysis CSVs (some 0KB — regenerate)
│   └── cost_comparison.csv       # Role-level cost analysis (1KB — has data)
├── scripts/
│   ├── audit_sources.py          # Source audit script (already created)
│   ├── analysis/                 # Existing analysis scripts
│   │   ├── inspect_neo4j.py      # Neo4j connection test
│   │   ├── inspect_sqlite.py     # SQLite inspection (deprecated after migration)
│   │   ├── analyze_vendors.py    # Vendor spending charts
│   │   ├── board_vote_analysis.py # GPT-4o board action extraction from LanceDB
│   │   ├── query_contracts.py    # LanceDB semantic search
│   │   ├── cost_comparison.py    # Contractor vs. in-house cost analysis
│   │   ├── extract_salaries.py   # S-275 → Top40 extraction
│   │   ├── benchmarking.py       # Peer district comparison from XLSX
│   │   └── ...
│   ├── loaders/                  # ← TO BE CREATED (Phase 2-8)
│   │   ├── vendor_normalization.py
│   │   ├── ingest_payments.py
│   │   ├── ingest_salaries.py
│   │   ├── bridge_lancedb.py
│   │   ├── ingest_budget.py
│   │   └── seed_reference.py
│   ├── verify_ingestion.py       # ← TO BE CREATED (Phase 10)
│   └── run_full_ingestion.py     # ← TO BE CREATED (orchestrator)
├── workspaces/
│   ├── VPS-Board-Scraper/
│   │   ├── documents/contracts/  # 193 scraped PDFs
│   │   ├── smart_scraper.py      # BoardDocs scraper (BLOCKED by anti-bot)
│   │   └── board_scraper.py      # Basic BoardDocs API probe
│   ├── Cicero_Clone/src/
│   │   └── adapters/neo4j.py     # Async Neo4j adapter (reference code)
│   ├── Architecture/
│   │   └── osint_research.md     # Amergis=Maxim OSINT findings
│   ├── results/
│   │   └── WOODWARD_DRAFT_1.md   # Draft investigative article
│   └── dispatches/               # Agent communication files
```

---

## 11. PYTHON DEPENDENCIES

```
neo4j>=5.0
lancedb>=0.4
sqlite3          # stdlib
pandas
pdfplumber       # If re-parsing PDFs
openpyxl         # For .xlsx files
```

---

## 12. VERIFICATION CHECKLIST (Post-Ingestion)

**0% tolerance on financial amounts.** These are exact records.

| Check | Neo4j Query | Expected Value |
|-------|-------------|----------------|
| Total payments | `MATCH (p:Payment) RETURN count(p)` | 55,191 |
| Total amount | `MATCH (p:Payment) RETURN sum(p.amount)` | $1,280,735,263.81 |
| Amergis total | `MATCH (v:Vendor {name:"AMERGIS HEALTHCARE STAFFING INC"})-[:RECEIVED_PAYMENT]->(p) RETURN sum(p.amount)` | $39,039,941.67 |
| Maxim total | `MATCH (v:Vendor {name:"MAXIM HEALTHCARE SERVICES INC"})-[:RECEIVED_PAYMENT]->(p) RETURN sum(p.amount)` | $28,215,062.08 |
| Amergis+Maxim combined | `MATCH (v:Vendor WHERE v.normalized_name = "Amergis/Maxim")-[:RECEIVED_PAYMENT]->(p) RETURN sum(p.amount)` | $67,255,003.75 |
| Soliant total | same pattern | $2,472,914.44 |
| Pioneer Healthcare total | same pattern | $268,175.00 |
| Unique vendors | `MATCH (v:Vendor) RETURN count(v)` | 4,442 |
| Unique documents | `MATCH (d:Document) RETURN count(d)` | ≥125 (125 from SQLite + up to 55 from LanceDB) |
| LanceDB bridge | `MATCH (d:Document) WHERE d.lance_id IS NOT NULL RETURN count(d)` | 55 |
| No orphan payments | `MATCH (p:Payment) WHERE NOT (p)<-[:RECEIVED_PAYMENT]-() RETURN count(p)` | 0 |
| No orphan FY links | `MATCH (p:Payment) WHERE NOT (p)-[:IN_FISCAL_YEAR]->() RETURN count(p)` | 0 |
| Pioneer dedup | `MATCH (v:Vendor) WHERE v.name CONTAINS 'PIONEER' RETURN v.name, v.vendor_type` | 4 distinct entities, correct types |
| No Amergis Education dupe | `MATCH (v:Vendor) WHERE v.name CONTAINS 'Education' RETURN v` | 0 rows |
| Run all 5 key queries from Section 8 | Each returns non-empty, consistent results | ✓ |
