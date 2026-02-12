# WoodWard Data Strategy: The "Red Database"

## Core Philosophy: Provenance & Linkage

Every data point must trace back to a verifiable source document (PDF page, URL). The architecture prioritizes **graph relationships** (who knows who, who paid whom) over simple tabular data, but uses relational structures for financial aggregation.

---

> [!CAUTION]
> ## 🔒 STRICT DATABASE SEGREGATION POLICY
> 
> **All WoodWard databases are completely isolated from existing projects.**
> 
> | Database | WoodWard Location | Existing Projects | Shared? |
> |----------|-------------------|-------------------|---------|
> | **SQLite** | `WoodWard/data/woodward.db` | CramLaw, LanceEmbed DBs | ❌ NO |
> | **Neo4j** | `~/neo4j/woodward/` (port 7688) | CaseLawDB (port 7687) | ❌ NO |
> | **LanceDB** | `WoodWard/data/vectors/` | `LanceEmbed/` vectors | ❌ NO |
> | **Files** | `WoodWard/documents/` | N/A | ❌ NO |
> 
> **Enforcement:**
> - All WoodWard scripts use hardcoded paths within the `WoodWard/` project directory.
> - Neo4j runs on a **different port** with **separate credentials**.
> - No shared `.env` files — WoodWard has its own config.

---

## 1. Storage Architecture (Hybrid)

### A. Raw Evidence (Filesystem)
**Location:** `documents/` and `data/raw/`
- **PDFs:** F-195s, Board Minutes, Contracts.
- **Naming Convention:** `[Source]_[Year-Month-Day]_[Description].pdf` (e.g., `VPS_2024-25_F-195.pdf`)
- **Metadata:** Sidecar JSON files for provenance (URL, download date, hash).

### B. Structured Financials (SQLite)
**Location:** `data/woodward.db`
- **Why SQLite?** Portable, serverless, excellent for SQL analysis of millions of budget rows.
- **Key Tables:**
  - `budget_items` (year, object_code, amount, description)
  - `vendor_payments` (vendor_id, date, amount, contract_ref)
  - `salary_schedules` (position, step, amount, year)

### C. The Knowledge Graph (Neo4j)

> [!IMPORTANT]
> **Complete Segregation from CaseLawDB.** WoodWard will use a **separate Neo4j instance** on a different port (e.g., 7688) with its own data directory (`~/neo4j/woodward/`). Zero data crossover with your legal research database.

**Location:** `~/neo4j/woodward/` (separate instance, port 7688)
- **Why Neo4j?** To find hidden connections (e.g., "Board Member X approved Contract Y for Vendor Z which employs X's spouse").
- **Node Types:** `Person`, `Organization`, `Contract`, `Meeting`, `Vote`, `Document`.
- **Edge Types:** `EMPLOYED_BY`, `VOTED_FOR`, `SIGNED`, `MENTIONED_IN`.

### D. Semantic Search (LanceDB / Chroma)
**Location:** `data/vectors/`
- **Purpose:** RAG (Retrieval Augmented Generation) for identifying "soft" connections in text (e.g., confusing board discussion summaries).
- **Implementation:** Chunk PDFs -> Embed -> Store vectors.

---

## 2. Data Flow Pipeline

1.  **Ingest:** Download PDF -> `documents/`
2.  **Extract:** Python scripts (pypdf/OCR) -> JSON/CSV in `data/processed/`
3.  **Load:**
    -   Financials -> `woodward.db` (SQLite)
    -   Entities/Relations -> `Neo4j`
    -   Text Chunks -> `LanceDB`
4.  **Analyze:**
    -   SQL for "Show me total Object 7 growth vs enrollment"
    -   Cypher for "Show me all vendors connected to Board Member A"

---

## 3. Directory Structure

```text
WoodWard/
├── documents/          # Original PDFs (F-195, Minutes)
├── data/
│   ├── raw/            # Scraped HTML, raw text dumps
│   ├── processed/      # Cleaned CSVs, JSONs
│   ├── woodward.db     # SQLite database
│   └── vectors/        # Vector store (LanceDB)
├── scripts/
│   ├── extractors/     # PDF -> Text/CSV
│   ├── loaders/        # CSV -> DB/Neo4j
│   └── analysis/       # SQL/Cypher queries
└── workspaces/         # Investigation zones (like F195-Analysis)
```

## 4. Immediate Next Steps

1.  **Initialize SQLite DB:** Create schema for `budget_items`.
2.  **Refine F-195 Extractor:** Output to CSV, then load into SQLite.
3.  **Spike Neo4j:** Create a simple graph of the 5 Directors and the Superintendent.
