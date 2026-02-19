# WoodWard Neo4j Re-Ingestion — Implementation Plan

**Prepared by:** VS Code (GitHub Copilot)  
**Date:** February 19, 2026  
**Objective:** Wipe and rebuild the WoodWard Neo4j knowledge graph from raw source files, replacing the fragmented SQLite/CSV/LanceDB architecture with a unified graph + vector strategy. Neo4j becomes the **single analytical store**. SQLite, CSVs, and LanceDB are consumed as migration inputs and will no longer be the primary query targets.

---

## GROUND TRUTH (From Source Audit)

### What Exists Now (Inputs to Consume)

| Source | Records | Size | Status |
|--------|---------|------|--------|
| SQLite `payments` table | 55,191 rows | 33.9MB | **Primary** — all warrant register line items |
| SQLite budget tables | 3 fiscal years, 9 objects, 20 items | tiny | F-195 extracts, budget cypher already generated |
| SQLite relational tables | vendors, contracts, people, votes, documents | **ALL EMPTY** | Schema-only; never populated |
| LanceDB `woodward_contracts` | 992 chunks from 55 unique source docs | ~50MB | Embedded contract/minutes text — **KEEP as vector sidecar** |
| Scraped PDFs | 193 files (24 Amergis, 84 Maxim, 35 Pioneer, 50 Soliant) | ~200MB | Three doc types mixed: warrant registers, MSAs, board minutes |
| S-275 Personnel CSVs | 5 years statewide (~886MB total) | 886MB | Filter on `codist=06037` for VPS |
| Top40 Salary CSVs | 5 files, ~200 records | 10KB | Pre-extracted from S-275 |
| F-195 Budget PDFs | 4 files (2 annual, 2 outlook) | 12MB | 2024-25 and 2025-26 |
| OSPI Staffing XLSX | 1 file (2023-24) | 686KB | District-level staffing benchmarks |
| Pre-computed CSVs | cost_comparison.csv (1KB), others **empty** (0KB) | <2KB | vendor_spending_annual, sped_contractor_annual, staffing benchmarks **all 0KB** |
| Neo4j (current) | 23 nodes, 30 relationships | trivial | Test seed data — **WIPE** |

### Critical Entity: The Amergis Corporate Chain

The investigation's primary target vendor has three names that are **the same legal entity**:

| Name as it appears | Context | Era |
|---------------------|---------|-----|
| **MAXIM HEALTHCARE SERVICES INC** | SQLite `payee`, PDF filenames, LanceDB content | Pre-2022, overlap through 2024 |
| **AMERGIS HEALTHCARE STAFFING INC** | SQLite `payee` (99 records, $39M) | 2023-24 onward |
| **Amergis Education** | Board minutes in LanceDB ("Amergis Education (formerly Maxim Healthcare)") | Board approval language for 2024-25 SY contracts |

These three names map to **one normalized entity: "Amergis/Maxim"** with:
- `parent_company`: "Maxim Healthcare Services" (Columbia, MD)
- `vendor_type`: "Staffing Agency"
- `fraud_history`: "$150M Medicaid fraud settlement (2011)"
- `rebrand_year`: 2022

Pioneer disambiguation (four separate entities):

| Payee in SQLite | Normalized Name | Type | Related? |
|-----------------|----------------|------|----------|
| PIONEER HEALTHCARE SERVICES LLC | Pioneer Healthcare | Staffing Agency | **YES — target** |
| PIONEER TRUST BANK/CORP INC | Pioneer Trust Bank | Bank | NO |
| PIONEER CREDIT RECEOVERY | Pioneer Credit Recovery | Collections | NO |
| PIONEER ATHLETICS | Pioneer Athletics | Supply | NO |

---

## ARCHITECTURE DECISION

### Before (Fragmented)
```
SQLite ──┐
CSVs  ───┤──→ Ad-hoc Python scripts ──→ Matplotlib charts
LanceDB ─┘                              Manual cross-referencing
Neo4j (23 test nodes, unused)
```

### After (Unified Graph + Vector)
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

**Neo4j is the database.** LanceDB is kept only because re-embedding 992 chunks would cost OpenAI API money and time for zero gain. It is queried only when semantic search is needed, and results are joined back to the graph via `lance_id` on `(:Document)` nodes.

**SQLite is decommissioned after migration.** It remains on disk as an archival artifact but is no longer queried by any analysis script.

---

## PHASE 0: ENVIRONMENT STABILIZATION (30 min)

### 0.1 Fix `.env` Protocol
The `.env` currently uses `bolt://` which causes auth errors with this Neo4j config.

```diff
- NEO4J_URI=bolt://localhost:7688
+ NEO4J_URI=neo4j://localhost:7688
```

### 0.2 Verify Neo4j Container Health
```bash
docker ps --filter "name=woodward-neo4j"
# Must show: Up, ports 7475:7474 and 7688:7687
python3 scripts/analysis/inspect_neo4j.py
# Must connect successfully via neo4j:// scheme
```

### 0.3 Install/Verify Python Dependencies
```bash
pip install neo4j lancedb pandas pdfplumber openpyxl
```

### 0.4 Create Backup of Current SQLite
```bash
cp data/woodward.db data/woodward.db.bak
```

### Exit Gate
- [ ] `neo4j://localhost:7688` connects successfully
- [ ] Python driver version ≥ 5.0 confirmed
- [ ] `.env` uses `neo4j://` scheme

---

## PHASE 1: WIPE + SCHEMA CREATION (30 min)

### 1.1 Wipe All Existing Neo4j Data
```cypher
MATCH (n) DETACH DELETE n;
CALL apoc.schema.assert({}, {});  -- Drop all constraints and indexes
```

### 1.2 Create Constraints (Uniqueness + Existence)

```cypher
// Node uniqueness constraints
CREATE CONSTRAINT vendor_name IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE;
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT org_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE;
CREATE CONSTRAINT doc_filename IF NOT EXISTS FOR (d:Document) REQUIRE d.filename IS UNIQUE;
CREATE CONSTRAINT fy_label IF NOT EXISTS FOR (fy:FiscalYear) REQUIRE fy.label IS UNIQUE;
CREATE CONSTRAINT employee_key IF NOT EXISTS FOR (e:Employee) REQUIRE (e.name, e.year) IS UNIQUE;
CREATE CONSTRAINT budget_obj_code IF NOT EXISTS FOR (bo:BudgetObject) REQUIRE bo.object_code IS UNIQUE;

// Composite constraints
CREATE CONSTRAINT meeting_unique IF NOT EXISTS FOR (m:BoardMeeting) REQUIRE (m.date, m.type) IS UNIQUE;
```

### 1.3 Create Performance Indexes

```cypher
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

### Exit Gate
- [ ] `SHOW CONSTRAINTS` returns all constraints above
- [ ] `SHOW INDEXES` returns all indexes above
- [ ] `MATCH (n) RETURN count(n)` returns 0

---

## PHASE 2: VENDOR NORMALIZATION LAYER (1 hour)

This is the most critical piece. Every downstream query depends on correct vendor identity resolution. Build this as a Python module (`scripts/loaders/vendor_normalization.py`) that is imported by all ingestion scripts.

### 2.1 Complete Vendor Alias Map

```python
VENDOR_ALIASES = {
    # === THE PRIMARY TARGET: Amergis/Maxim (SAME ENTITY) ===
    "AMERGIS HEALTHCARE STAFFING INC": {
        "normalized_name": "Amergis/Maxim",
        "vendor_type": "Staffing Agency",
        "parent_company": "Maxim Healthcare Services",
        "aliases": ["Amergis Education", "Amergis Healthcare", "Amergis Staffing"],
        "notes": "Rebranded from Maxim Healthcare Staffing in 2022. $150M Medicaid fraud settlement (2011).",
    },
    "MAXIM HEALTHCARE SERVICES INC": {
        "normalized_name": "Amergis/Maxim",
        "vendor_type": "Staffing Agency",
        "parent_company": "Maxim Healthcare Services",
        "aliases": ["Maxim Healthcare Staffing", "Maxim Healthcare"],
        "notes": "Pre-rebrand name. Same entity as Amergis Healthcare Staffing.",
    },

    # === SOLIANT ===
    "SOLIANT HEALTH LLC": {
        "normalized_name": "Soliant Health",
        "vendor_type": "Staffing Agency",
        "parent_company": None,
        "aliases": ["Soliant"],
        "notes": "Competitor to Amergis in VPS staffing ecosystem.",
    },

    # === PIONEER — FOUR DIFFERENT ENTITIES ===
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

# Target vendors for investigative queries
TARGET_VENDORS = {"Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"}

def normalize_vendor(raw_payee: str) -> dict:
    """Given a raw payee string from SQLite, return normalization metadata.
    Returns dict with: normalized_name, vendor_type, parent_company, notes.
    For unknown vendors, returns a default with normalized_name = raw_payee."""
    upper = raw_payee.strip().upper()
    if upper in VENDOR_ALIASES:
        return VENDOR_ALIASES[upper]
    # Fuzzy fallback: check if any alias substring matches
    for canonical, meta in VENDOR_ALIASES.items():
        for alias in meta.get("aliases", []):
            if alias.upper() in upper or upper in alias.upper():
                return meta
    # Unknown vendor
    return {
        "normalized_name": raw_payee.strip(),
        "vendor_type": "Unknown",
        "parent_company": None,
        "notes": None,
    }
```

### 2.2 Fiscal Year Resolver

Payment `entry_date` is `MM/DD/YYYY`. Washington school fiscal year runs September 1 – August 31.

```python
from datetime import datetime

def entry_date_to_fiscal_year(entry_date_str: str) -> str:
    """Convert MM/DD/YYYY to fiscal year label like '2024-25'."""
    dt = datetime.strptime(entry_date_str, "%m/%d/%Y")
    if dt.month >= 9:  # Sep-Dec → first year of FY
        return f"{dt.year}-{str(dt.year + 1)[2:]}"
    else:  # Jan-Aug → second year of FY
        return f"{dt.year - 1}-{str(dt.year)[2:]}"
```

### 2.3 Date Normalizer

Store all dates in Neo4j as ISO 8601 (`YYYY-MM-DD`) or Neo4j `date()` type, not as `MM/DD/YYYY` strings.

```python
def normalize_date(date_str: str) -> str | None:
    """Convert MM/DD/YYYY to YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None
```

### Exit Gate
- [ ] `normalize_vendor("AMERGIS HEALTHCARE STAFFING INC")["normalized_name"]` → `"Amergis/Maxim"`
- [ ] `normalize_vendor("MAXIM HEALTHCARE SERVICES INC")["normalized_name"]` → `"Amergis/Maxim"`
- [ ] `normalize_vendor("PIONEER TRUST BANK/CORP INC")["normalized_name"]` → `"Pioneer Trust Bank"`
- [ ] `normalize_vendor("PIONEER HEALTHCARE SERVICES LLC")["normalized_name"]` → `"Pioneer Healthcare"`
- [ ] `entry_date_to_fiscal_year("10/15/2024")` → `"2024-25"`
- [ ] `entry_date_to_fiscal_year("03/15/2024")` → `"2023-24"`

---

## PHASE 3: SEED REFERENCE DATA (30 min)

### 3.1 Organizations

Create the organizational hierarchy that all other nodes connect to.

```cypher
// School District
MERGE (vps:Organization {name: "Vancouver Public Schools"})
SET vps.type = "School District",
    vps.ubi = "601-223-961",
    vps.enrollment_2024 = 22500;

// Departments
MERGE (hr:Organization {name: "VPS Human Resources"})
SET hr.type = "Department";
MERGE (finance:Organization {name: "VPS Finance & Operations"})
SET finance.type = "Department";
MERGE (sped:Organization {name: "VPS Special Education"})
SET sped.type = "Department";

MATCH (dept:Organization) WHERE dept.type = "Department"
MATCH (vps:Organization {name: "Vancouver Public Schools"})
MERGE (dept)-[:PART_OF]->(vps);

// Parent Company
MERGE (maxim_parent:Organization {name: "Maxim Healthcare Services"})
SET maxim_parent.type = "Parent Company",
    maxim_parent.hq = "Columbia, MD",
    maxim_parent.notes = "$150M Medicaid fraud settlement (2011). DPA and CIA imposed.";
```

### 3.2 People (VPS Leadership)

```cypher
MERGE (supt:Person {name: "Jeff Snell"})
SET supt.role = "Superintendent", supt.start_date = date("2020-07-01");

MERGE (b1:Person {name: "Tracie Brennan"})
SET b1.role = "Board Member", b1.position = "President";
MERGE (b2:Person {name: "Kyle Sproul"})
SET b2.role = "Board Member", b2.position = "Vice President";
MERGE (b3:Person {name: "Mark Stoker"})
SET b3.role = "Board Member";
MERGE (b4:Person {name: "Krysta Shendruck"})
SET b4.role = "Board Member";
MERGE (b5:Person {name: "Liz Darling"})
SET b5.role = "Board Member";

MATCH (supt:Person {name: "Jeff Snell"}), (vps:Organization {name: "Vancouver Public Schools"})
MERGE (supt)-[:EMPLOYED_BY {position: "Superintendent"}]->(vps);

MATCH (b:Person WHERE b.role = "Board Member"), (vps:Organization {name: "Vancouver Public Schools"})
MERGE (b)-[:GOVERNS]->(vps);
```

### 3.3 Fiscal Years

Create all fiscal years that appear in the data (derived from payment date range + budget data).

```cypher
UNWIND [
  {label: "2019-20", start: date("2019-09-01"), end: date("2020-08-31")},
  {label: "2020-21", start: date("2020-09-01"), end: date("2021-08-31")},
  {label: "2021-22", start: date("2021-09-01"), end: date("2022-08-31")},
  {label: "2022-23", start: date("2022-09-01"), end: date("2023-08-31")},
  {label: "2023-24", start: date("2023-09-01"), end: date("2024-08-31")},
  {label: "2024-25", start: date("2024-09-01"), end: date("2025-08-31")},
  {label: "2025-26", start: date("2025-09-01"), end: date("2026-08-31")}
] AS fy
MERGE (f:FiscalYear {label: fy.label})
SET f.start_date = fy.start, f.end_date = fy.end;

MATCH (vps:Organization {name: "Vancouver Public Schools"}), (fy:FiscalYear)
MERGE (vps)-[:HAS_BUDGET]->(fy);
```

### 3.4 Budget Objects

```cypher
UNWIND [
  {code: 1, name: "Certificated Salaries", desc: "Teacher and certificated staff salaries"},
  {code: 2, name: "Classified Salaries", desc: "Support staff and classified employee salaries"},
  {code: 3, name: "Employee Benefits", desc: "Benefits and payroll taxes"},
  {code: 4, name: "Supplies", desc: "Supplies, instructional resources, noncapitalized items"},
  {code: 5, name: "Purchased Services", desc: "Contracted services from external vendors (Object 7)"},
  {code: 6, name: "Travel", desc: "Travel and conference expenses"},
  {code: 7, name: "Capital Outlay", desc: "Equipment and capital purchases"},
  {code: 8, name: "Other", desc: "Miscellaneous expenditures"},
  {code: 9, name: "Transfers", desc: "Inter-fund transfers"}
] AS bo
MERGE (b:BudgetObject {object_code: bo.code})
SET b.name = bo.name, b.description = bo.desc;
```

### Exit Gate
- [ ] `MATCH (n) RETURN labels(n), count(n)` shows Organization, Person, FiscalYear, BudgetObject nodes
- [ ] VPS has 3 departments linked via `:PART_OF`
- [ ] 7 fiscal years exist
- [ ] Superintendent and 5 board members linked to VPS

---

## PHASE 4: INGEST PAYMENTS + VENDORS + DOCUMENTS (2-3 hours)

This is the largest ingestion — 55,191 payment records from SQLite → Neo4j. It simultaneously creates Vendor nodes (with normalization), Payment nodes, Document nodes, and FiscalYear linkage.

### 4.1 Build the Ingestion Script

**File:** `scripts/loaders/ingest_payments.py`

**Architecture:**
1. Read all 55,191 rows from SQLite `payments` table
2. For each row, apply `normalize_vendor()` and `entry_date_to_fiscal_year()`
3. Batch UNWIND into Neo4j in batches of 500
4. Each batch creates/merges: `Vendor`, `Document`, `Payment`, `FiscalYear`
5. Each batch creates relationships: `RECEIVED_PAYMENT`, `EXTRACTED_FROM`, `IN_FISCAL_YEAR`

**Key Cypher (per batch):**
```cypher
UNWIND $batch AS p

// Vendor (with normalization metadata)
MERGE (v:Vendor {name: p.payee})
ON CREATE SET
  v.normalized_name = p.normalized_name,
  v.vendor_type = p.vendor_type,
  v.parent_company = p.parent_company,
  v.notes = p.vendor_notes

// Document (source warrant register PDF)
MERGE (d:Document {filename: p.source_file})
ON CREATE SET d.document_type = "Warrant Register"

// Fiscal Year
MERGE (fy:FiscalYear {label: p.fiscal_year})

// Payment node (CREATE, not MERGE — each row is unique)
CREATE (pay:Payment {
  amount: p.amount,
  entry_date: date(p.entry_date_iso),
  document_date: p.document_date,
  raw_line: p.raw_line,
  source_file: p.source_file
})

// Relationships
MERGE (v)-[:RECEIVED_PAYMENT]->(pay)
MERGE (pay)-[:EXTRACTED_FROM]->(d)
MERGE (pay)-[:IN_FISCAL_YEAR]->(fy)
```

### 4.2 Corporate Structure Relationships

After payment ingestion, link Amergis to Maxim parent:

```cypher
// Amergis is a rebrand of Maxim Healthcare Staffing, subsidiary of Maxim Healthcare Services
MATCH (amergis:Vendor {name: "AMERGIS HEALTHCARE STAFFING INC"})
MATCH (maxim:Vendor {name: "MAXIM HEALTHCARE SERVICES INC"})
MATCH (parent:Organization {name: "Maxim Healthcare Services"})
MERGE (amergis)-[:SUBSIDIARY_OF {since: date("2022-01-01"), notes: "Rebrand from Maxim Healthcare Staffing"}]->(parent)
MERGE (maxim)-[:SUBSIDIARY_OF]->(parent)
MERGE (amergis)-[:REBRANDED_FROM {year: 2022}]->(maxim)
```

### 4.3 Vendor-to-Organization Payment Summary Edges (Materialized Aggregates)

For high-performance investigative queries, create summary relationships:

```cypher
// For each target vendor + fiscal year, create a summary edge
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
WHERE v.normalized_name IN ["Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"]
WITH v, fy, sum(p.amount) AS total, count(p) AS payment_count
MERGE (v)-[s:SPENT_IN_YEAR]->(fy)
SET s.total_amount = total, s.payment_count = payment_count;
```

### Expected Results
- **~55,000** `Payment` nodes
- **~4,442** `Vendor` nodes (raw payee names preserved; `normalized_name` property handles dedup)
- **~125** `Document` nodes (warrant register PDFs)
- **~4-5** `FiscalYear` nodes (from payment dates)
- **~55,000** `:RECEIVED_PAYMENT` relationships
- **~55,000** `:EXTRACTED_FROM` relationships
- **~55,000** `:IN_FISCAL_YEAR` relationships

### Exit Gate — Reconciliation (MANDATORY)
These checks compare Neo4j totals against SQLite source-of-truth:

| Check | Query | Expected |
|-------|-------|----------|
| Total payments | `MATCH (p:Payment) RETURN count(p)` | 55,191 |
| Total amount | `MATCH (p:Payment) RETURN sum(p.amount)` | $1,280,735,263.81 |
| Amergis total | `MATCH (v:Vendor {name:"AMERGIS HEALTHCARE STAFFING INC"})-[:RECEIVED_PAYMENT]->(p) RETURN sum(p.amount)` | $39,039,941.67 |
| Maxim total | `MATCH (v:Vendor {name:"MAXIM HEALTHCARE SERVICES INC"})-[:RECEIVED_PAYMENT]->(p) RETURN sum(p.amount)` | $28,215,062.08 |
| Amergis+Maxim combined | `MATCH (v:Vendor WHERE v.normalized_name = "Amergis/Maxim")-[:RECEIVED_PAYMENT]->(p) RETURN sum(p.amount)` | $67,255,003.75 |
| Soliant total | `...` | $2,472,914.44 |
| Pioneer Healthcare total | `...` | $268,175.00 |
| Unique vendors | `MATCH (v:Vendor) RETURN count(v)` | 4,442 |
| Unique documents | `MATCH (d:Document) RETURN count(d)` | 125 |
| No Amergis Education dupes | `MATCH (v:Vendor) WHERE v.name CONTAINS 'AMERGIS' RETURN v.name, v.normalized_name` | All map to "Amergis/Maxim" |
| Pioneer dedup | `MATCH (v:Vendor) WHERE v.name CONTAINS 'PIONEER' RETURN v.name, v.vendor_type` | 4 distinct entities with correct types |

**Tolerance:** 0% variance on amounts. These are exact financial records.

---

## PHASE 5: INGEST BUDGET DATA (30 min)

### 5.1 Load Budget Line Items

Use the existing `data/load_budget.cypher` which already has MERGE semantics for 3 fiscal years × multiple budget objects.

```bash
cat data/load_budget.cypher | cypher-shell -u neo4j -p woodward_secure_2024 -a neo4j://localhost:7688
# OR run via Python driver
```

### 5.2 Verify Budget Trajectory

```cypher
MATCH (fy:FiscalYear)-[s:SPENT]->(bo:BudgetObject {name: "Purchased Services"})
RETURN fy.label, s.amount ORDER BY fy.label;
```

Expected:
| Fiscal Year | Purchased Services |
|-------------|-------------------|
| 2022-23 | $42,056,089 |
| 2023-24 | $43,420,672 |
| 2024-25 | $47,331,056 |

### Exit Gate
- [ ] 3 fiscal years × 7-9 budget objects = ~20 `SPENT` relationships
- [ ] Purchased Services trend: $42M → $43.4M → $47.3M confirmed

---

## PHASE 6: LANCEDB ↔ NEO4J BRIDGE (45 min)

### 6.1 Create Document Nodes for LanceDB Sources

LanceDB has 55 unique `source_document_id` values. For each, create a `(:Document)` node in Neo4j with a `lance_id` property. Many of these documents are already created as warrant register sources in Phase 4 — this phase adds the ones that aren't (contracts, board minutes) and sets the `lance_id` property on all of them.

```python
import lancedb
db = lancedb.connect("data/lancedb")
tbl = db.open_table("woodward_contracts")
df = tbl.to_pandas()

# Get unique source documents with metadata
sources = df.groupby("source_document_id").agg(
    chunk_count=("id", "count"),
    first_citation=("citation_key", "first"),
).reset_index()

# For each source, MERGE a Document node with lance_id
for _, row in sources.iterrows():
    session.run("""
        MERGE (d:Document {filename: $filename})
        ON CREATE SET d.document_type = "Contract/Minutes",
                      d.lance_id = $lance_id,
                      d.lance_chunk_count = $chunk_count
        ON MATCH SET  d.lance_id = $lance_id,
                      d.lance_chunk_count = $chunk_count
    """,
    filename=row["source_document_id"],
    lance_id=row["source_document_id"],
    chunk_count=int(row["chunk_count"]))
```

### 6.2 Classify Documents by Type

Using LanceDB content, tag Document nodes with more specific types:

```python
# For documents with Amergis Education board approval language
for _, row in amergis_education_chunks.iterrows():
    # These are board meeting minutes
    session.run("""
        MATCH (d:Document {lance_id: $lance_id})
        SET d.document_type = "Board Meeting Minutes",
            d.mentions_amergis_education = true
    """, lance_id=row["source_document_id"])
```

### Exit Gate
- [ ] `MATCH (d:Document) WHERE d.lance_id IS NOT NULL RETURN count(d)` → 55 (all LanceDB sources bridged)
- [ ] `MATCH (d:Document) RETURN d.document_type, count(d)` shows Warrant Register, Contract/Minutes, Board Meeting Minutes

---

## PHASE 7: INGEST SALARY/STAFFING DATA (1 hour)

### 7.1 Top 40 Salaries (Fast Path)

5 pre-extracted CSVs, ~200 records total. Create `(:Employee)` nodes linked to VPS and fiscal years.

```python
import pandas as pd
import glob

for csv_file in sorted(glob.glob("data/salaries/Top40_*.csv")):
    df = pd.read_csv(csv_file)
    year_code = csv_file.split("_")[-1].replace(".csv", "")
    # Map year codes to fiscal year labels
    fy_map = {"1920": "2019-20", "2021": "2020-21", "2122": "2021-22",
              "2223": "2022-23", "2324": "2023-24"}
    fy_label = fy_map.get(year_code, year_code)

    batch = []
    for _, row in df.iterrows():
        batch.append({
            "name": row["FullName"],
            "salary": float(row["tfinsal"]),
            "position": row.get("Position", "Unknown"),
            "year": fy_label
        })

    session.run("""
        UNWIND $batch AS e
        MERGE (emp:Employee {name: e.name, year: e.year})
        SET emp.salary = e.salary,
            emp.position = e.position
        WITH emp, e
        MERGE (fy:FiscalYear {label: e.year})
        MERGE (emp)-[:EMPLOYED_IN]->(fy)
        WITH emp
        MATCH (vps:Organization {name: "Vancouver Public Schools"})
        MERGE (emp)-[:WORKS_FOR]->(vps)
    """, batch=batch)
```

### 7.2 VPS-Only S-275 Data (Optional — Large)

The 5 S-275 CSVs total ~886MB statewide. Filter on `codist IN ('06037', '6037')` for VPS-only records. This gives deeper staffing trend data (all employees, not just top 40).

**Decision point:** Do this only if the Top 40 data is insufficient for the investigation's staffing analysis needs. The S-275 data adds hundreds of VPS employees per year but requires significant processing time.

### 7.3 Staffing Benchmarks

Load the OSPI staffing benchmark data for peer district comparison:

```python
# data/ospi/Staffing_Benchmark_2324.csv (if non-empty)
# OR regenerate from StaffingTables_2324.xlsx using scripts/analysis/benchmarking.py
```

Create peer `(:Organization)` nodes and link staffing metrics:

```cypher
MERGE (evg:Organization {name: "Evergreen School District"})
SET evg.type = "School District", evg.district_code = "06114";

MERGE (spk:Organization {name: "Spokane Public Schools"})
SET spk.type = "School District", spk.district_code = "32081";
// ... etc
```

### Exit Gate
- [ ] `MATCH (e:Employee) RETURN count(e)` → ~200 (5 years × 40)
- [ ] `MATCH (e:Employee {name: "Jeff Snell"}) RETURN e.salary, e.year` → shows salary trend
- [ ] Jeff Snell 2023-24 salary = $356,835 (or close — from OSPI S-275)

---

## PHASE 8: INGEST DERIVED ANALYSIS DATA (30 min)

### 8.1 Cost Comparison (Contractor vs. In-House)

The `documents/cost_comparison.csv` contains per-role contractor rate vs. in-house cost data. Load as properties on Vendor nodes or as dedicated `(:CostBenchmark)` nodes.

```cypher
UNWIND $roles AS r
CREATE (cb:CostBenchmark {
  role: r.role,
  contractor_hourly_mid: r.contractor_hourly,
  contractor_annual: r.contractor_annual,
  inhouse_annual: r.inhouse_annual,
  premium_dollars: r.premium_dollars,
  premium_percent: r.premium_pct
})
```

### 8.2 Regenerate Empty CSVs

The following CSVs are 0KB and need to be regenerated from Neo4j data (not from SQLite anymore):

```python
# vendor_spending_annual.csv — now query Neo4j
MATCH (v:Vendor)-[s:SPENT_IN_YEAR]->(fy:FiscalYear)
WHERE v.normalized_name IN ["Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"]
RETURN v.normalized_name, fy.label, s.total_amount
ORDER BY fy.label;

# sped_contractor_annual.csv — aggregate all staffing agency vendors by FY
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
WHERE v.vendor_type = "Staffing Agency"
RETURN fy.label, sum(p.amount) as total_sped_contractor
ORDER BY fy.label;
```

### Exit Gate
- [ ] Cost benchmark data queryable in Neo4j
- [ ] Analysis CSVs can be regenerated entirely from Neo4j queries (no SQLite dependency)

---

## PHASE 9: BOARD GOVERNANCE DATA (Parallel Track — 2+ days)

This phase depends on either:
- (a) Successful BoardDocs scraping (currently blocked by anti-bot), OR
- (b) Manual extraction from the 193 scraped PDFs, OR
- (c) LLM-assisted extraction from LanceDB chunks (the `board_vote_analysis.py` approach)

### 9.1 Extract Board Actions from LanceDB Content

The existing `scripts/analysis/board_vote_analysis.py` uses GPT-4o to extract structured board actions from LanceDB chunks. This is the most viable path since BoardDocs scraping is blocked.

**Output:** `(:BoardMeeting)`, `(:AgendaItem)`, `:HAS_ITEM`, `:VOTED`, `:AUTHORIZES` nodes and relationships.

### 9.2 Specific Amergis Education Board Approval

The LanceDB audit found explicit references to:
> "Recommendation to Approve a Client Services Agreement Between the Vancouver Public Schools and **Amergis Education (formerly Maxim Healthcare)** for VPS Students for the 2024-25 SY"

This should be extracted as a specific `(:AgendaItem)` linked to a `(:Contract)` linked to the Amergis `(:Vendor)` node.

### 9.3 Contract Nodes

For any MSA/contract text found in LanceDB, create `(:Contract)` nodes:

```cypher
CREATE (c:Contract {
  description: "Client Services Agreement — Amergis Education (formerly Maxim Healthcare) — 2024-25 SY",
  vendor_name: "AMERGIS HEALTHCARE STAFFING INC",
  start_date: date("2024-09-01"),
  notes: "Board minutes refer to entity as 'Amergis Education'"
})
WITH c
MATCH (v:Vendor {name: "AMERGIS HEALTHCARE STAFFING INC"})
MATCH (vps:Organization {name: "Vancouver Public Schools"})
MERGE (v)-[:PARTY_TO]->(c)
MERGE (vps)-[:PARTY_TO]->(c)
```

### Exit Gate
- [ ] Board meeting + agenda item nodes exist for vendor contract approvals
- [ ] At least the Amergis Education 2024-25 contract approval is represented
- [ ] `:AUTHORIZES` chain from AgendaItem to Contract to Vendor is queryable

---

## PHASE 10: FINAL VERIFICATION + QUERY VALIDATION (1 hour)

### 10.1 Node/Relationship Census

```cypher
// Node counts by label
MATCH (n) RETURN labels(n) AS label, count(n) AS count ORDER BY count DESC;

// Relationship counts by type
MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC;
```

### 10.2 Run All 5 Investigative Queries

**Query 1: Total payments to target vendors by fiscal year**
```cypher
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
WHERE v.normalized_name IN ["Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"]
RETURN v.normalized_name, fy.label, sum(p.amount) as total, count(p) as payments
ORDER BY fy.label, total DESC;
```

**Query 2: Amergis/Maxim combined — the rebrand timeline**
```cypher
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
WHERE v.normalized_name = "Amergis/Maxim"
RETURN v.name, fy.label, count(p) as payments, sum(p.amount) as total
ORDER BY fy.label, v.name;
```
This should show the handoff: Maxim payments declining, Amergis payments exploding, same normalized entity.

**Query 3: Purchased Services as % of total budget**
```cypher
MATCH (fy:FiscalYear)-[s:SPENT]->(bo:BudgetObject)
WITH fy, sum(s.amount) as total_budget,
     sum(CASE WHEN bo.name = "Purchased Services" THEN s.amount ELSE 0 END) as obj7
RETURN fy.label, obj7, total_budget, round(obj7/total_budget * 100, 2) as pct
ORDER BY fy.label;
```

**Query 4: Vendor payment frequency per warrant register (consent agenda opacity)**
```cypher
MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:EXTRACTED_FROM]->(d:Document)
WHERE v.normalized_name = "Amergis/Maxim"
RETURN d.filename, count(p) as payment_count, sum(p.amount) as meeting_total
ORDER BY meeting_total DESC;
```

**Query 5: Superintendent salary vs. contractor spending trajectory**
```cypher
MATCH (e:Employee {name: "Jeff Snell"})-[:EMPLOYED_IN]->(fy:FiscalYear)
OPTIONAL MATCH (fy)<-[s:SPENT_IN_YEAR]-(v:Vendor {normalized_name: "Amergis/Maxim"})
RETURN fy.label, e.salary as supt_salary, s.total_amount as amergis_total
ORDER BY fy.label;
```

### 10.3 Data Integrity Checks

```cypher
// Orphan payments (no vendor)
MATCH (p:Payment) WHERE NOT (p)<-[:RECEIVED_PAYMENT]-() RETURN count(p);
// Expected: 0

// Orphan payments (no fiscal year)
MATCH (p:Payment) WHERE NOT (p)-[:IN_FISCAL_YEAR]->() RETURN count(p);
// Expected: 0

// Duplicate normalized vendors for same entity
MATCH (v:Vendor)
WITH v.normalized_name AS norm, collect(v.name) AS names
WHERE size(names) > 1
RETURN norm, names;
// Expected: "Amergis/Maxim" → ["AMERGIS HEALTHCARE STAFFING INC", "MAXIM HEALTHCARE SERVICES INC"]
//           (This is CORRECT — two payee names, one normalized entity)

// Verify no Amergis Education as a separate Vendor node
MATCH (v:Vendor) WHERE v.name CONTAINS "Education" RETURN v;
// Expected: 0 rows (Amergis Education is not a payee in SQLite — it appears only in board minutes)
```

### 10.4 Decommission Verification

Confirm that every analysis query previously run against SQLite can now be answered entirely from Neo4j:

| Previous SQLite Query | Neo4j Equivalent | Verified |
|----------------------|-------------------|----------|
| `SELECT payee, sum(amount) FROM payments GROUP BY payee` | `MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p) RETURN v.name, sum(p.amount)` | [ ] |
| `SELECT * FROM payments WHERE payee LIKE '%AMERGIS%'` | `MATCH (v:Vendor {normalized_name:"Amergis/Maxim"})-[:RECEIVED_PAYMENT]->(p) RETURN p` | [ ] |
| Budget trend from `budget_items` table | `MATCH (fy)-[s:SPENT]->(bo) RETURN fy.label, bo.name, s.amount` | [ ] |
| Vendor spending annual CSV | `MATCH (v)-[s:SPENT_IN_YEAR]->(fy) RETURN ...` | [ ] |

---

## EXECUTION ORDER SUMMARY

| Phase | Duration | Depends On | Nodes Created | Key Risk |
|-------|----------|------------|---------------|----------|
| 0. Environment | 30 min | — | 0 | Wrong protocol → auth failure |
| 1. Schema | 30 min | Phase 0 | 0 | Constraint conflicts with existing data |
| 2. Normalization | 1 hr | — | 0 (library) | Missing vendor alias → wrong grouping |
| 3. Seed Data | 30 min | Phase 1 | ~25 | Incorrect fiscal year boundaries |
| 4. **Payments** | **2-3 hrs** | Phases 1-3 | **~60,000** | **Batch failures, date parse errors, amount drift** |
| 5. Budget | 30 min | Phase 1, 3 | ~20 rels | Existing cypher may need schema adjustments |
| 6. LanceDB Bridge | 45 min | Phase 1, 4 | ~55 docs | Filename mismatch between SQLite and LanceDB |
| 7. Salaries | 1 hr | Phase 1, 3 | ~200 | S-275 CSV column name variations |
| 8. Derived Data | 30 min | Phase 4 | ~15 | Empty CSVs need regeneration |
| 9. Governance | 2+ days | Phase 6 | Variable | BoardDocs scraper blocked; LLM extraction needed |
| 10. Verification | 1 hr | All | 0 | Reconciliation failures |

**Total estimated time (Phases 0-8, 10):** ~7-8 hours of implementation  
**Phase 9 (Governance):** Parallel track, 2+ days (includes LLM API calls for extraction)

---

## RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Amergis Education appears as future payee in new warrant registers | Medium | High — breaks normalization | Add "AMERGIS EDUCATION" to VENDOR_ALIASES map now, pointing to "Amergis/Maxim" |
| Neo4j heap exhaustion on 55k Payment batch load | Low | Medium | Batch size 500, `dbms.memory.heap.max_size=1G` already set |
| LanceDB `source_document_id` doesn't match SQLite `source_file` | High | Medium | Fuzzy match on truncated filename; manual mapping table for mismatches |
| Date format inconsistencies in SQLite `entry_date` | Medium | High | Validate all dates parse as MM/DD/YYYY before ingestion; dead-letter non-conforming rows |
| BoardDocs scraper remains blocked | High | Medium | Use LLM extraction from existing LanceDB chunks as fallback (already implemented in `board_vote_analysis.py`) |
| S-275 CSV column names vary between years | Medium | Low | Inspect headers per file; use column-name mapping dict |

---

## FILES TO CREATE / MODIFY

### New Files
| File | Purpose |
|------|---------|
| `scripts/loaders/vendor_normalization.py` | Vendor alias map, fiscal year resolver, date normalizer |
| `scripts/loaders/ingest_payments.py` | SQLite → Neo4j payment ingestion pipeline |
| `scripts/loaders/ingest_salaries.py` | Top40 CSVs → Neo4j Employee nodes |
| `scripts/loaders/bridge_lancedb.py` | LanceDB → Neo4j Document node bridge |
| `scripts/loaders/ingest_budget.py` | Load budget cypher via Python driver (replaces cypher-shell) |
| `scripts/loaders/seed_reference.py` | Create Organizations, People, FiscalYears, BudgetObjects |
| `scripts/verify_ingestion.py` | Post-ingestion reconciliation checks |
| `scripts/run_full_ingestion.py` | Orchestrator: runs Phases 1-8 in order |

### Modified Files
| File | Change |
|------|--------|
| `.env` | Fix `NEO4J_URI` from `bolt://` to `neo4j://` |
| `data/neo4j_schema.cypher` | Replace with expanded schema from Phase 1 |

### Deprecated (No longer primary query targets after migration)
| File | Status |
|------|--------|
| `data/woodward.db` | Archival — keep on disk but no scripts query it |
| `data/schema.sql` | Archival — documents the old relational schema |
| `scripts/analysis/inspect_sqlite.py` | Deprecated — replaced by `verify_ingestion.py` |
