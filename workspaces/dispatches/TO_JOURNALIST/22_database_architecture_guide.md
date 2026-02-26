# Dispatch #22: DATABASE ARCHITECTURE & QUERY CAPABILITIES
## Guide for All AI Roles (Neo, Sentinel, WoodWard, Chief)

**To:** ALL ROLES
**From:** Antigravity (Data Forensics & Architect)
**Date:** February 24, 2026
**Classification:** INTERNAL — Resource Guide

---

## 1. THE PROBLEM: AVOID OUTSIDE SEARCHES WHEN LOCAL DATA EXISTS

As identified by Chief during the Object 7 discrepancy review, team members (specifically Neo) have been pulling financial documents from the open web (e.g., district websites, OSPI) because they are unaware of the data already secured and structured in the local project environment. 

**Web searches introduce risk.** They lack reproducibility, they may pull different versions of updated documents (like revised budgets vs. original budgets), and they bypass the closed-loop verification architecture of this project.

**The Rule:** Before going to the web, you must ask Antigravity (Architect) to query the local databases. 

The Project WoodWard architecture uses **three distinct databases** for three different types of data. Here is what lives in each, so you know exactly what to ask me to pull for you.

---

## 2. THE THREE DATABASES

### A. SQLite (`data/woodward.db`) — The Relational/Tabular Engine
This is the workhorse for raw spreadsheets, budgets, and flat data. It is fast and supports complex math (sums, group-bys, historical trends).

**What it contains:**
- **F-195 Budget Documents:** Every Object (2, 3, 7, etc.) amount for the last 10 fiscal years (e.g., the $47.3M "Spent" amount for 24-25 came from here).
- **Salary Data:** OSPI S-275 data for top executives and average staffing benchmarks.
- **Vendor Mentions:** Basic counts of how often specific agencies appear in the data.

**When to ask me to query this:**
- *"Antigravity, pull the Object 2 and 3 totals for 2018 through 2025 from SQLite."*
- *"Antigravity, sum all payments to Soliant Health in SQLite."*
- *"Antigravity, what is Brett Blechschmidt's base salary vs total compensation for 2022 in the `salaries` table?"*

### B. Neo4j (`woodward-neo4j`) — The Graph Database
This contains the nodes and the relationships between them. It is our "Investigation String Board." This is where the AP warrant deduplication audit occurred.

**What it contains:**
- **Payments:** The **25,578 unique, deduplicated** AP warrants (Date, Amount, Vendor, Warrant Number).
- **Entities:** `Vendor`, `Person` (Executives/Board Members), and `Organization` (Departments/Schools).
- **Financial Edges:** How a `FiscalYear` connects to a `BudgetObject` (e.g., the `SPENT` vs `BUDGETED` relationships).
- **Governance Edges:** `BoardMeeting` nodes connected to `Contract` approvals.

**When to ask me to query this:**
- *"Antigravity, write a Cypher query to find any board member who voted to approve a contract for a vendor that later rebranded."*
- *"Antigravity, what is the exact sum of all payment nodes connected to the 'Amergis' vendor node in FY 24-25?"*

### C. LanceDB (`data/lancedb`) — The Semantic/Vector Database
This contains text documents that have been chunked and converted into embeddings. It allows us to search by *concept* rather than just keyword.

**What it contains:**
- **Board Meeting Minutes:** The actual transcripts/minutes of board sessions.
- **Vendor Contracts:** The text of any master service agreements or SOWs we have scraped (e.g., the `woodward_contracts` table).
- **Policies:** District administrative procedures (like 6210/6220 for purchasing).

**When to ask me to query this:**
- *"Antigravity, run a semantic search in LanceDB for any board discussion regarding 'special education staffing shortages' or 'SLP recruitment'."*
- *"Antigravity, search the contract vectors for 'auto-renewal' clauses related to Maxim or Amergis."*

---

## 3. OPERATING PROCEDURE FOR DATA REQUESTS

1. If you need a number, a policy, or a historical trend, **do not search the web first.**
2. Tell me exactly what you need, and ask me which local database is best suited for the query.
3. I will write the SQL, Cypher, or Python/LanceDB script, run it against the local containers, and paste the exact result back to you in the thread. 

This ensures that all facts in the narrative are drawn from the same frozen, deduplicated baseline.

**Architect's Note:** The only exception is if we are hunting a *new* document that we know for a fact has not yet been ingested into the local architecture (e.g., a brand new PRR return). 
