# Dispatch #20: OBJECT 7 DENOMINATOR RECONCILIATION
## Priority Assignment for Neo

**To:** NEO
**From:** Antigravity (Architect)
**Date:** February 24, 2026
**Classification:** PRIORITY 1 — Publication-Blocking

---

## 1. THE PROBLEM

You identified a critical discrepancy in your latest response. We have **two conflicting Object 7 figures** for FY 2024-25:

| Source | Object 7 (Purchased Services) | Basis |
|--------|-------------------------------|-------|
| Dispatch #16 (team figure) | **$47,331,056** | "OSPI F-195 budget documents loaded into SQLite" |
| District-hosted F-195 PDF | **$36,738,206** | General Fund Expenditure Summary by Objects |

**Difference:** $10,592,850 (28.8% variance)

This means our published claim — that staffing agencies consume **25.13%** of Object 7 — may be wrong. The percentage depends entirely on which denominator is correct. Both cannot be right for the same accounting scope.

---

## 2. YOUR ASSIGNMENT

### Step 1: Identify the source of $47,331,056

Trace the $47,331,056 figure back to its original source document. Possible explanations:
- **All-funds Object 7** (General Fund + ASB + Capital Projects + Debt Service + Transportation), not just General Fund
- **Actuals** from a different fiscal period vs. **budgeted** amounts
- **A different F-195 revision** (districts file amended budgets)
- **An error in the SQLite ingestion pipeline** (wrong column, wrong row, or cross-contamination from another district)

### Step 2: Pull the official F-195 Object 7 figures for all years

From the district-hosted F-195 PDFs (vansd.org budget repository), extract the **General Fund Object 7 (Purchased Services)** line from the **Expenditure Summary by Objects** page for each available fiscal year. Present them in this format:

| Fiscal Year | Object 7 (General Fund, Budgeted) | Source Document | Page/Section |
|-------------|-----------------------------------|-----------------|--------------|
| 2020-2021 | $ _______ | [link] | [page] |
| 2021-2022 | $ _______ | [link] | [page] |
| 2022-2023 | $ _______ | [link] | [page] |
| 2023-2024 | $ _______ | [link] | [page] |
| 2024-2025 | $ _______ | [link] | [page] |

### Step 3: Recalculate the staffing agency share

Using the **verified General Fund Object 7 figures** from Step 2, recalculate the staffing agency share for each fiscal year using the corrected numerators from Dispatch #16 Section 3A:

| Fiscal Year | Staffing Spend (D#16) | Object 7 (Verified) | Corrected Share |
|-------------|----------------------|---------------------|-----------------|
| 2020-2021 | $377,585 | $ _______ | ___% |
| 2021-2022 | $2,030,404 | $ _______ | ___% |
| 2022-2023 | $6,128,296 | $ _______ | ___% |
| 2023-2024 | $6,464,972 | $ _______ | ___% |
| 2024-2025 | $11,895,076 | $ _______ | ___% |

### Step 4: Also pull Objects 2 and 3 (Priority 2 from prior session)

While you are in the F-195 PDFs, also extract:
- **Object 2 (Certificated Salaries)** and **Object 3 (Classified Salaries)** for each year
- **Total General Fund Expenditures** for each year

This will support the Object 2/3 vs Object 7 trend analysis needed for the "salary-to-contractor shift" hypothesis.

---

## 3. VERIFICATION TAGS

All figures you report must carry one of these tags:
- **[VERIFIED]** — Extracted directly from a named primary source document with page/section citation
- **[CALCULATED]** — Arithmetic performed on [VERIFIED] inputs, with formula shown
- **[UNRESOLVED]** — Cannot be confirmed from available sources; requires additional records

---

## 4. URGENCY

**This is the #1 blocker for Article 2.** No percentage claim about agency spending can be published until we know which Object 7 denominator is correct and why. The current "25.13%" figure in Dispatch #16 is **suspended** pending your output.

---

## 5. ANTI-HALLUCINATION PROTOCOL REMINDER

Do not estimate, interpolate, or fill in any value you cannot directly extract from a primary document. If a year's F-195 is unavailable from the district website, report it as **[NOT AVAILABLE]** and specify what alternative source could fill the gap.
