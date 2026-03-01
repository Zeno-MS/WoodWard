# Project WoodWard: Fact-Check Issue Log

## Article 1: "The Receipt" (The Austerity Paradox)
- **Status:** ✅ VERIFIED.
- **Financial Figures Check:** The major financial claims ($13.3M total in FY24-25, $10.97M to Amergis) exactly match the *deduplicated* query of `woodward.db`. The journalist's assertion that data was "after deduplication of 29,613 duplicate records caused by multi-vendor warrant register overlaps" is completely correct. Dispatch #40 raised a false alarm because the queries did not apply the DISTINCT (document_date, payee, amount) logic designed to strip out the multi-scrape overlap. The article's Table IV aligns with pristine deduplicated database totals.
- **Corporate History:** Maxim $150M settlement in 2011 is accurately stated (cross-referenced with DOJ press release). Amergis rebrand in 2022 is accurate.
- **Cost Premium Calculation:** Weighted average premium of ~15% and 'Lost Efficiency' math matches the side-by-side SEBB/DRS analysis from earlier phases.
- **Conclusion:** No publication barriers found. Facts are mathematically and historically durable.

## Article 2: "The Consent Agenda" (The Accountability Void)
- **Status:** ✅ VERIFIED.
- **Financial Claims Check:** The cumulative $32.18M figure and vendor breakdown matches the locked deduplicated baseline established prior to the multi-vendor triplication scraper bug. The 51.2% growth in Object 7 budgeting is correct relative to the F-195s.
- **Legal/Governance Check:** RCW 28A.335.190 and VPS Board Policy 6220 are accurately cited. The search showing zero use of the "emergency waiver" mechanism is confirmed.
- **Meeting Chronologies:** The "Cash Flow Crisis" timeline (Interfund loans and Registered Warrants) aligns with previously documented board actions from 2023-2025.
- **Conclusion:** No publication barriers found. Governance sequence is factually and legally defensible.

## Article 3: "The Systemic Trap"
- **Status:** ✅ VERIFIED.
- **Cost Model Check:** The "fully loaded" baseline ($56.8K for Para, $87.8K for SPED teacher) perfectly aligns with the SEBB ($1,178/mo) and DRS (9.11%) tables constructed and verified in prior data phases.
- **Vendor Premium:** The 22.9% premium at the $75/hr mid-rate mathematically checks out against the internal fully-loaded hourly rate of $61.02.
- **Peer Comparison:** Vancouver and Evergreen F-195 budgeted vs. actual calculations are mathematically sound and properly contextualized as unplanned overspend.
- **Note:** Legislative citations (SB 5263) appear to have been shifted to Article 4 or removed during the final publication scrub; this is an editorial choice, not a factual inaccuracy.
- **Conclusion:** No publication barriers found. Economic models are rigorous.

## Article 4: "The Classroom"
- **Status:** ✅ VERIFIED.
- **Reporting Citations Check:** OPB reporting (Colin Bailey/Cara Bailey, 1,110 restraints in 16-17, 776 in 22-23) accurately cited.
- **State Findings Check:** OSPI SECC 21-32 details (960 of 1575 minutes delivered, deficit of 615 due to substitutes, six of twelve IEP goals unprogressed) accurately cited from the 2021 state decision.
- **Labor Action Check:** VAESP strike authorization (80% / 800+ staff) and tentative agreement (Sept 15, 2025) are chronologically exact.
- **Treasurer Quote Note:** The Treasurer's Dec 9, 2025 quote regarding "long, ongoing operating loans" was *omitted* from the final locked draft. This is an editorial spacing choice by Woodward, not a factual error.
- **Conclusion:** No publication barriers found. External reporting and internal state oversight records used defensively.

---
**FINAL RECONCILIATION SUMMARY (Sentinel / Antigravity):**
The initial data collision alarm regarding the $70.7M vendor sum vs the $32.1M article sum was fully resolved. The scraper had ingested the exact same multi-vendor board PDFs up to 3 times depending on search terms (e.g. searching for Amergis vs Maxim pulling the same master doc).

However, Woodward's articles *had already correctly applied strict deduplication logic* (grouping DISTINCT combinations of document date, payee, and amount). When evaluating the deduplicated database, **Article 1, 2, 3, and 4 are mathematically flawless.**

## OVERALL ASSESSMENT: 🟢 ALL FOUR ARTICLES GREEN AND CLEARED FOR PUBLICATION.
