# Dispatch #37 — Chief's YELLOW Corrections for Article 3

**Date:** February 27, 2026  
**From:** Neo (Verification) + Woodward (Corrections)  
**To:** Christopher  
**Re:** Resolving Chief's YELLOW review — Publication-blocking errors and significant issues

---

## PUBLICATION-BLOCKING ERRORS

### 1. ❌ Wrong Governor → ✅ Fix: Bob Ferguson
**Line ~188.** Article says "Governor Jay Inslee." Inslee's term ended January 2025. **Bob Ferguson** was inaugurated January 15, 2025, and signed SB 5263 on **May 19, 2025**.

> **Action:** Replace `Governor Jay Inslee` with `Governor Bob Ferguson`.

---

### 2. ❌ Wrong Signing Date → ✅ Fix: May 19, 2025
**Line ~188.** Article says "May 6, 2025." Per the official legislative record (app.leg.wa.gov) and LegiScan, the bill was **delivered to the Governor on April 27, 2025** and **signed May 19, 2025** (Chapter 368, Laws of 2025).

> **Action:** Replace `May 6, 2025` with `May 19, 2025`.

---

## SIGNIFICANT ISSUES

### 3. ❌ $870M Figure Lacks Attribution → ✅ Fix: Add Sponsor Attribution
The $870M figure is an **advocate/sponsor characterization** ("roughly $870 million over four fiscal years"), not an official fiscal note. The original Senate version projected much higher costs; the enacted version was a compromise.

> **Action:** Change to:
> `directs an estimated **$870 million** in additional state funding to districts over four years, according to the bill's sponsors`

---

### 4. ❌ Multiplier Range Wrong → ✅ Fix: Use 1.16
**This is the biggest substantive correction.** The article says "approximately **1.53–1.64 times** the basic education allocation." The enacted session law (5263-S2.SL.pdf) sets the special education excess cost multiplier at a flat **1.16** — replacing the prior tiered structure. The 1.5289 figure was from the *original* bill proposal, not the enacted law.

The enacted text reads: `special education cost multiplier rate of 1.16`

> **Action:** Replace `increases the special education funding multiplier to approximately **1.53–1.64 times** the basic education allocation` with:
> `sets the special education excess cost multiplier at **1.16**, replacing the prior tiered rate structure`

---

### 5. ✅ Vote Tallies — Minor Precision Fix
The article says "97–0 in the House and 48–0 in the Senate." Per official roll calls:
- **Senate:** 48 yeas, 0 nays, 1 excused (March 12, 2025)
- **House (initial):** 97 yeas, 0 nays, 1 excused (April 16, 2025)
- **House (final, after conference):** 95 yeas, 0 nays, 3 excused

The "97–0" and "48–0" are substantively correct for the characterization "unanimous in both chambers." No change strictly required, but could add "(with excusals)" for precision.

> **Action (optional):** Append "— unanimous in both chambers, with only excused absences" for precision without changing the characterization.

---

## MODERATE ISSUES

### 6. ✅ $349,709 Baseline — CONFIRMED
Traces to Dispatch #28 canonical baseline table (FY 2020-2021 staffing vendor total: $349,709 / 1.17% of Object 7). Used consistently across Articles 1, 2, and 3, Right of Reply, and all dispatches. **No change needed.**

### 7. ⚠️ $5,000 / 30% Placement Fee — Minor Precision Fix
The article says `$5,000 placement fee (or 30% of annual salary)`. The actual Maxim MSA language (Section 1.1, verified in Dispatch #25) is:

> *"a placement fee equal to the greater of: five thousand dollars ($5,000) or the sum of thirty percent (30%) of such personnel's annualized salary"*

The "or" in Article 3 is imprecise — it should say **"the greater of"** to match the contract.

> **Action:** Change `**$5,000 placement fee** (or **30% of annual salary**)` to:
> `**a placement fee equal to the greater of $5,000 or 30% of annualized salary**`

### 8. Two Files Are Identical — Pub-Ready Scrub Required
After all content corrections are applied to `ARTICLE_3_PUBLICATION_READY.md`, do a scrub pass:
- Strip internal cross-references ("As documented in Article 2")
- Remove section numbering (I, II, III...)
- Remove "What Comes Next" teaser apparatus
- Keep "What This Investigation Does Not Claim" verbatim
- The editorial draft preserves the working version with all internal references

> **Action:** Apply content corrections to both files first, then do the pub-ready scrub on `ARTICLE_3_PUBLICATION_READY.md` only.

---

## EXECUTION SEQUENCE

| Step | Action | File |
|------|--------|------|
| 1 | Fix governor: Inslee → Ferguson | Both |
| 2 | Fix date: May 6 → May 19 | Both |
| 3 | Add $870M attribution | Both |
| 4 | Fix multiplier: 1.53–1.64 → 1.16 | Both |
| 5 | Fix placement fee: "or" → "the greater of" | Both |
| 6 | (Optional) Precision on vote tallies | Both |
| 7 | Pub-ready scrub | `ARTICLE_3_PUBLICATION_READY.md` only |
| 8 | Return to Chief for GREEN clearance | — |

**Say "go" and I will execute all corrections in a single pass.**
