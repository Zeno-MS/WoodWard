# Dispatch #16: MASTER DATA CORRECTION BRIEFING
## ⚠️ ALL ROLES: READ IN FULL BEFORE WRITING OR CITING ANY FIGURE

**To:** WOODWARD, NEO, CHIEF, SENTINEL, NotebookLM Archive
**From:** Antigravity (Data Forensics)
**Date:** February 23, 2026
**Classification:** MANDATORY CORRECTION — Supersedes All Prior Dispatches

---

## 1. WHAT HAPPENED

On February 23, 2026, a comprehensive deduplication audit of the Neo4j payment database revealed that **29,613 of 55,191 payment records were duplicates**. The root cause: the same Board Warrant Register was downloaded multiple times under different vendor PRR search names (e.g., the April 8, 2025 warrant register was saved as `Maxim_98_...pdf`, `Soliant_49_...pdf`, AND `Amergis_16_...pdf`). Each copy was ingested independently, inflating totals by approximately 2x-3x.

**The previously reported "62%" Object 7 staffing share was a data artifact. The true figure is 25.13%.**

All duplicate records have been permanently purged from the Neo4j database. The corrected database now contains exactly **25,578 unique payment records**.

---

## 2. FIGURES YOU MUST DISCARD (DO NOT CITE)

| ❌ Old (Inflated) Figure | Context |
|--------------------------|---------|
| Amergis FY 24-25: $27,904,823 | Was ~2.5x inflated |
| Soliant FY 24-25: $1,502,581 | Was ~2.4x inflated |
| Total staffing spend FY 24-25: $29,454,029 | Was ~2.5x inflated |
| **Staffing share of Object 7: 62.23%** | **Was ~2.5x inflated** |
| Staffing share FY 22-23: 35.13% | Inflated |
| Staffing share FY 23-24: 32.18% | Inflated |
| 55,191 payment records | Pre-deduplication count |

---

## 3. CORRECTED FIGURES — THE ONLY NUMBERS SAFE TO PUBLISH

### 3A. Corrected Staffing Vendor Totals by Fiscal Year

| Fiscal Year | Staffing Vendor Spend | Object 7 Budget | Staffing Share |
|-------------|----------------------|-----------------|----------------|
| 2020-2021 | **$377,585** | $24,288,629 | **1.55%** |
| 2021-2022 | **$2,030,404** | $26,727,867 | **7.60%** |
| 2022-2023 | **$6,128,296** | $42,056,089 | **14.57%** |
| 2023-2024 | **$6,464,972** | $43,420,672 | **14.89%** |
| 2024-2025 | **$11,895,076** | $47,331,056 | **25.13%** |
| 2025-2026 (partial) | **$3,165,265** | $26,728,364 | 11.84% |

**Source:** Neo4j AP warrant records (post-dedup) cross-referenced against OSPI F-195 budget documents loaded into SQLite.

### 3B. Corrected Per-Vendor Breakdown (All Years Combined)

| Vendor Name | Relationship | Deduplicated Total |
|-------------|-------------|-------------------|
| AMERGIS HEALTHCARE STAFFING INC | Primary vendor (2024-present) | **$15,748,411** |
| MAXIM HEALTHCARE SERVICES INC | Predecessor to Amergis (2020-2023) | **$12,326,099** |
| SOLIANT HEALTH LLC | Secondary vendor | **$1,069,180** |
| AVEANNA HEALTHCARE | Home health nursing | **$695,200** |
| SUNBELT STAFFING LLC | Minor staffing vendor | **$99,670** |
| PIONEER HEALTHCARE SERVICES LLC | Minor staffing vendor | **$119,213** |
| ACCOUNTABLE HEALTHCARE STAFFING INC | Minor (1 payment) | **$3,825** |
| **TOTAL (all staffing vendors, all years)** | | **$30,061,597** |

### 3C. The Maxim → Amergis Corporate Lineage

This is critical context. Maxim Healthcare Services and Amergis Healthcare Staffing are the **same company following a rebrand**. The billing transition is visible in the data:

| Fiscal Year | Maxim Spend | Amergis Spend | Combined |
|-------------|-------------|---------------|----------|
| 2020-2021 | $320,529 | $0 | $320,529 |
| 2021-2022 | $1,886,173 | $0 | $1,886,173 |
| 2022-2023 | $5,908,104 | $0 | $5,908,104 |
| 2023-2024 | $4,195,578 | $1,849,732 | $6,045,310 |
| 2024-2025 | $15,716 | $10,970,973 | $10,986,689 |
| 2025-2026 | $0 | $2,927,705 | $2,927,705 |

**Narrative implication:** The district did not "switch" vendors. Maxim rebranded to Amergis. This is a single continuous vendor relationship spanning 6+ years.

### 3D. Corrected FY 2024-25 Vendor Breakdown

| Vendor | FY 24-25 Spend | Share of Staffing Total |
|--------|---------------|------------------------|
| Amergis (fka Maxim) | $10,970,973 | 92.2% |
| Soliant Health | $627,518 | 5.3% |
| Aveanna Healthcare | ~$200,000 est. | ~1.7% |
| All others | ~$96,585 | 0.8% |
| **TOTAL** | **$11,895,076** | **100%** |

---

## 4. FIGURES THAT REMAIN UNCHANGED AND VERIFIED

The following data points were NOT affected by the deduplication issue and remain mathematically verified:

### 4A. Internal Cost Model (Priority C) — UNCHANGED

| Role | District Fully-Loaded Rate | Agency Rate Range | Premium |
|------|---------------------------|-------------------|---------|
| SLP/RN (MA+0 Step 5) | **$68.92/hr** | $100-$150/hr | **45% to 118%** |
| Paraeducator (Step 3) | **$40.38/hr** | $50-$75/hr | **24% to 86%** |

**Annualized Lost Efficiency per FTE:**
- SLP/RN: **$41,964 to $109,464** per contractor per year
- Paraeducator: **$12,984 to $46,734** per contractor per year

**Source:** VEA CBA 2024-27, VAESP Salary Schedule 2024-25, SEBB employer rate ($1,178/mo), DRS rate (9.11%).

### 4B. Peer District Normalization (Priority D) — UNCHANGED

| District | K-12 Enrollment | Object 7 Budget | % of GF | Per Pupil |
|----------|----------------|-----------------|---------|-----------|
| **Tacoma** | 27,170 | $52,913,217 | 8.84% | **$1,947** |
| **Evergreen** | 22,570 | $45,935,389 | 10.93% | **$2,035** |
| **VPS** | 21,082 | $43,420,672 | 10.23% | **$2,060** |
| **Battle Ground** | 12,369 | $32,727,029 | 14.10% | **$2,646** |

**VPS 2024-25:** $47,331,056 / 20,807 students = **$2,275 per pupil** (vs. Evergreen $2,161)

**Source:** OSPI F-195 budget documents, K-12 FTE enrollment from F-195 summary pages.

### 4C. Executive Compensation (Priority 1) — UNCHANGED

| Name | Role | FY 23-24 Salary | FY 24-25 Salary |
|------|------|-----------------|-----------------|
| Jeff Fish | Director/Supervisor | $219,087 | $217,873 |
| William Oman | Other District Admin | $213,989 | $221,754 |
| James Gray | Other District Admin | $200,081 | $213,966 |
| Janell Ephraim | Other District Admin | $212,226 | $219,432 |

**Source:** OSPI S-275 Personnel Reporting via fiscal.wa.gov.

### 4D. Central Office Reductions — UNCHANGED
- Pre-cut FTE (2023-24): **480.63 FTE**
- Post-cut FTE (2024-25): **433.06 FTE**
- Net reduction: **47.57 FTE** (concentrated in support personnel, not executives)

---

## 5. THE CORRECTED NARRATIVE HOOK

### What You CAN Say (Legally Durable):
- "One in every four dollars Vancouver Public Schools spent on purchased services in 2024-25 went to private staffing agencies — a 16-fold increase from just four years prior."
- "The district paid $11.9 million to staffing agencies in FY 2024-25, with 92% flowing to a single vendor, Amergis Healthcare (formerly Maxim)."
- "Staffing agencies' share of the Object 7 budget grew from 1.55% in 2020-21 to 25.13% in 2024-25."
- "The district pays a 45% to 118% premium for agency SLPs/RNs over fully-loaded internal hires."
- "Vancouver spends $2,275 per student on purchased services, outpacing neighboring Evergreen by $114 per student despite having fewer students."

### What You CANNOT Say:
- ~~"62% of purchased services went to staffing agencies"~~ (inflated by duplicate data)
- ~~"$29.4 million went to Amergis"~~ (inflated by duplicate data)
- ~~"Nearly $28 million to a single vendor"~~ (inflated by duplicate data)

### The SPED Teacher Gap
Amergis Education also places **Special Education teachers** in the district. These placements are invisible in our data because all roles (SPED Teachers, SLPs, RNs, Paras) are bundled into a single lump-sum payment per warrant cycle. The invoicing detail that would reveal the role-level breakdown requires a **Public Records Request** for the Master Service Agreement and itemized invoices. This is the "Killer Request" (PRR #1) in the V3 Master Plan.

---

## 6. DATA SOURCES REFERENCE

| Data Point | Source | Location |
|------------|--------|----------|
| Object 7 budgets | OSPI F-195 PDFs | `data/woodward.db` (SQLite) |
| Vendor payments | Board Warrant Registers | Neo4j (25,578 unique records) |
| Salary schedules | VEA CBA 2024-27, VAESP 24-25 | `documents/contracts/VPS/` |
| SEBB rates | WA Health Care Authority | HCA.wa.gov |
| DRS rates | WA Dept. of Retirement Systems | DRS.wa.gov |
| Enrollment | OSPI F-195 summary pages | F-195 PDFs in `documents/F195/` |
| Executive salaries | OSPI S-275 | fiscal.wa.gov/K12/K12Salaries |

---
**This document is the single source of truth for all V3 AI roles. If any previously provided figure conflicts with this briefing, THIS BRIEFING CONTROLS.**
