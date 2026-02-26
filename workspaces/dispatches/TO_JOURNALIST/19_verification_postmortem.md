# Dispatch #19: VERIFICATION PROTOCOL POST-MORTEM
## Root Cause Analysis: The $27.9M Inflation Event

**To:** CHIEF
**From:** Antigravity (Architect)
**Date:** February 24, 2026
**Classification:** INTERNAL — Process Correction

---

## 1. CHIEF'S QUESTION (VERBATIM)

> "The original AP warrant confirmation you brought me — the $27,904,822.80 figure — came from the Neo4j database before deduplication. What was the source of your confidence in that figure when you reported it? I need to understand whether there was a manual verification step that was bypassed or whether the database was the only source."

---

## 2. ROOT CAUSE

The $27.9M figure was derived from a **single source**: an aggregate Cypher query against the Neo4j payment database. No independent manual verification step was performed against a primary document (such as the F-195 budget filing or a district-published AP report) before the figure was promoted to narrative status.

### How the duplicates entered the database:

Board Warrant Registers are published as PDFs containing **all vendor payments in a given warrant cycle**. When the team filed Public Records Requests for staffing vendors, the **same warrant register PDF** was returned under multiple search queries:

- `Amergis_16_...pdf` → Ingested
- `Maxim_98_...pdf` → Same warrant register, ingested again
- `Soliant_49_...pdf` → Same warrant register, ingested a third time

Each copy was loaded into Neo4j independently. The ingestion pipeline had **no deduplication gate** (e.g., hashing on warrant number + vendor + amount + date). The result: 29,613 of 55,191 records were duplicates, inflating totals by approximately 2.5x.

### Why it wasn't caught:

1. **No cross-check requirement existed.** The team treated the Neo4j database as a verified single source of truth after ingestion, without requiring a "second source confirmation" step (e.g., comparing the database total against the F-195 Object 7 figure or a district-published vendor summary).
2. **Confirmation bias.** The inflated $27.9M figure aligned with the team's narrative hypothesis about excessive agency spending. A larger number was not questioned because it supported the anticipated story.
3. **No Sentinel review of raw data.** Sentinel's adversarial review was applied to the *narrative drafts* but not to the *underlying database queries* that produced the anchor figures.

---

## 3. THE FIX (ALREADY IMPLEMENTED)

- **29,613 duplicate records permanently purged** from Neo4j on February 23, 2026.
- Database now holds exactly **25,578 unique payment records**.
- Corrected figures issued as **Dispatch #16** (mandatory correction, supersedes all prior dispatches).
- All project files, drafts, and NotebookLM exports purged of inflated figures.

---

## 4. PROTOCOL CHANGES (PROPOSED)

To prevent recurrence, the following gates are proposed for the verification architecture:

### Gate 1: Ingestion Deduplication
All future data ingestion into Neo4j must include a deduplication step. At minimum: hash on `(warrant_date, vendor_name, amount, warrant_number)` and reject duplicate records at ingest time.

### Gate 2: Two-Source Confirmation
**No database-derived figure may enter a draft or dispatch without being cross-checked against at least one independent primary source.** Acceptable second sources include:
- OSPI F-195 budget filings
- District-published financial summaries
- SAO audit reports
- Raw warrant register PDFs (manual spot-check of 3+ individual records)

### Gate 3: Sentinel Data Review
Sentinel's adversarial review scope is expanded to include **input data validation**, not just narrative review. Before any aggregate figure is promoted to "PROOF" status, Sentinel must independently verify the query logic and sample the underlying records.

### Gate 4: Magnitude Sanity Check
Any figure that exceeds **50% of a budget category** or represents a **year-over-year increase exceeding 5x** triggers an automatic hold for manual verification before it can be cited in any draft.

---

## 5. CURRENT STATUS

- **Dispatch #16** is the controlling source of truth for all staffing-vendor figures.
- **A new discrepancy has been identified by Neo** (see Dispatch #20): the Object 7 budget figure used as denominator ($47,331,056) does not match the district's official FY24-25 F-195 PDF ($36,738,206). This is being investigated immediately under the new Two-Source Confirmation protocol.
- The team is operational and the verification architecture is stronger for having failed once.

---

**Architect's assessment:** The gap was architectural, not individual. The system did not require a second-source confirmation step, and it should have. The proposed four gates above close the hole. Requesting Chief's approval to formalize these as standing protocol.
