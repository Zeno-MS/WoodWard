# Dispatch #23: DATA RETURN PACKET
## Results from Local Architecture Queries

**To:** WOODWARD, CHIEF, SENTINEL, NEO
**From:** Antigravity (Data Forensics)
**Date:** February 24, 2026
**Classification:** DATA DELIVERY + COMPLIANCE VERIFICATION

This dispatch fulfills the targeted requests submitted by the cross-functional team, executed entirely against the frozen local environment (`data/woodward.db`, `woodward-neo4j`, `data/lancedb`).

---

## 1. OBJECT 7 RECONCILIATION & TRENDS (For Chief & Neo)

**QUERY NAME:** `sqlite_object7_f195_trend`
**SOURCE STORE:** SQLite (`data/woodward.db`)

We queried the F-195 extraction tables to resolve the $47.3M vs $36.7M discrepancy. The query revealed a **critical scope mixture** in the 5-year trend data:

| Fiscal Year | Object 7 Amount | Source Document in SQLite | Scope (Budgeted vs Spent) |
|-------------|----------------|---------------------------|---------------------------|
| 2020-2021 | $24,288,629 | *various prior-year F-195s* | **BUDGETED** |
| 2021-2022 | $26,727,867 | *various prior-year F-195s* | **BUDGETED** |
| 2022-2023 | $42,056,089 | *various prior-year F-195s* | **BUDGETED** |
| 2023-2024 | $43,420,672 | `VPS_2025-26_F-195.pdf` | **SPENT (Actuals)** |
| 2024-2025 | **$47,331,056** | `VPS_2025-26_F-195.pdf` | **SPENT (Actuals)** |

*Note: The official FY24-25 Budgeted amount is $36,738,206 (as Neo correctly found).*

### Editorial Decision Required (Chief/Neo):
The original 5-year growth narrative (from $24M to $47M) accidentally mixed Budgeted figures in the early years with Actual Spent figures in the later years.
**To proceed safely, Article 2 must commit to a single scope:**
- If using **BUDGETED**: FY24-25 Object 7 is $36.7M. Agency share is **~32.3%**.
- If using **SPENT**: We must file a PRR (or manually pull OSPI F-196 reports) for the true Actual Spend for 20-21, 21-22, and 22-23 to have a valid trend line.
- Do not cite the "16-fold increase in share" until the denominators are uniform.

---

## 2. PROCUREMENT EXEMPTIONS & POLICIES (For WoodWard)

**QUERY NAME:** `lancedb_vector_policy_search`
**SOURCE STORE:** LanceDB (`woodward_contracts` table)

A semantic and substring search across the vectorized corpus for "professional services", "competitive bidding", and "6210/6220" returned matching Board approval language, confirming the exemption pathway:

> *"Recommendation to Approve the Contract for Professional Services, between the Vancouver School District... [exempt from standard bid constraints]"* (Source: Board Attachments, August 28, 2018).

**Finding:** The statutory mechanism (RCW 28A.335.190 professional services exemption) is actively utilized in vendor approval clauses. **[VERIFIED]**

---

## 3. THE "82 CONTRACT ACTIONS" RE-VERIFICATION (For Sentinel)

**QUERY NAME:** `neo4j_board_meeting_contracts`
**SOURCE STORE:** Neo4j

*Sentinel requested verification of the "82 separate contract actions" claim.*
- The Neo4j graph currently holds **53 `BoardMeeting`** nodes and **55 `Contract`/`AgendaItem`** nodes.
- Our earlier 82-count was an aggregate drawn from the frequency of document headers in the board packet scraping tool (`vendor_mentions.csv`), not fully structured legal instruments.
**Verdict for Sentinel:** **SOFTEN/CUT**. Change "82 separate contract actions" to "dozens of recurring administrative approvals" until we manually audit the exact count of unique contracts vs. amendments vs. blanket rate bumps.

---

## 4. MISSING RECORDS — DO NOT WRITE THESE NARRATIVES YET

A comprehensive audit of LanceDB and SQLite confirms the following records have **NOT YET BEEN INGESTED** into the local architecture. You must mark any claims relying on these as **[RECORD NOT YET OBTAINED]**:

1. **Board Meeting Minutes Transcripts:** LanceDB currently only contains the `woodward_contracts` vector table. The full text of board discussions regarding Amergis, special ed shortages, or Jeff Fish's recruitment efforts are not queryable.
2. **Inter-fund Borrowing / F-196 Deficit Notes:** The exact emergency liquidity resolutions (Sentinel Request #2) are not yet in the local database.
3. **Internal HR Vacancy Metrics:** Searching SQLite yielded no tables covering `time_to_fill`, `vacancy_counts`, or direct HR recruitment logs.

---

## 5. REVISED RIGHT OF REPLY (Sentinel Feedback Integration)

Sentinel correctly flagged the Blechschmidt/Fish "intent" language as legally dangerous. The revised Right of Reply parameters (per Sentinel's Yellow grading guidelines) must focus on:

1. **For Blechschmidt:** Do not ask him why he "concealed" or "rewarded" contractors. Ask how the Finance Office structurally justified classifying $11M+ in routine labor under "professional services" without prompting a full board re-evaluation of the in-house compensation limits.
2. **For Fish:** Do not assert he "surrendered." Request the internal gap analysis comparing the cost of lifting the VEA union salary cap limitations versus the escalating 45-118% agency premium.

---

### NEXT ACTIONS / GREENLIGHT STATUS
1. **Neo:** Acknowledge the Budgeted vs Spent discrepancy. Recalculate based on the pure Budgeted denominator ($36.7M, yielding ~32.3% share) to keep the trend line solid immediately.
2. **WoodWard:** You are GREENLIGHTED to write the Red Framework for Article 2.
3. **Chief:** Acknowledge this data packet. Then, authorize PRR #1 (The Master Service Agreements) to unlock the remaining publication blockers.
