# New Chat Handoff — Project WoodWard

## Objective
Continue the WoodWard investigative series. The project has completed a full data recalibration cycle: deduplication of Neo4j payments, re-extraction of F-195 budget data from source PDFs, patching of the SQLite database, and a five-layer verification process culminating in manual spot-checks against source warrant register PDFs. All figures are now anchored to Dispatch #28 (the canonical numbers-control document) and verified via Dispatch #29 (GREEN clearance queries).

## Current Status (End of Session — February 25, 2026)

### Investigation Phase: Part II Draft Authorization
- **Part II Status: YELLOW → GREEN** (pending Chief's formal GREEN issuance after reviewing Dispatch #29)
- Chief has authorized Woodward to begin drafting Part II ("The Accountability Void") using the locked figures below
- All four staff members (Chief, Woodward, Neo, Sentinel) have processed Dispatches 26-28
- Dispatch #29 (verification queries) is ready for relay to the team

### Locked Figures (Canonical — Dispatch #28 Controls)

**FY-Bucketed Staffing Vendor Shares (Chief's Actual/Actual Methodology):**
- FY 2020-21: $349,709 / $29,960,026 = **1.17%** [PROOF]
- FY 2021-22: $2,142,124 / $26,727,867 = **8.01%** [PROOF — budgeted denom, disclosure req'd]
- FY 2022-23: $6,232,403 / $42,056,089 = **14.82%** [PROOF]
- FY 2023-24: $6,677,879 / $43,420,672 = **15.38%** [PROOF]
- FY 2024-25: $13,326,622 / $47,331,056 = **28.16%** [PROOF — pending Chief GREEN]

**All-Time Vendor Totals (Deduped):**
- Amergis Healthcare: $15,748,411 (48.9%)
- Maxim Healthcare: $12,326,099 (38.3%)
- **Combined Amergis/Maxim: $28,074,510 (87.2%)**
- ProCare Therapy: $2,926,334 (9.1%)
- Soliant Health: $1,069,180 (3.3%)
- Pioneer Healthcare: $119,213 (0.4%)
- **Grand Total: $32,189,236**

**Budgeted Object 7 Trend (Austerity Contradiction):**
- FY20-21 $24,288,629 → FY24-25 $36,738,206 = **51.2% increase** during austerity cycle

### Database Status
- **Neo4j** (`bolt://localhost:7688`, auth: `neo4j/woodward_secure_2024`): 25,578 deduped payment records. Verified clean — zero warrant number overlap, sequential warrant numbering confirmed.
- **SQLite** (`data/woodward.db`): PATCHED. `budget_items` table rebuilt with verified F-195 PDF data + new `scope` column (BUDGETED/SPENT). 112 rows, all tagged.
- **LanceDB** (`data/lancedb/woodward_contracts`): 5,367+ document chunks from board packets, contract PDFs, warrant registers, meeting minutes.
- **BoardDocs SQLite** (`workspaces/VPS-Board-Scraper/data/board_meetings.db`): Meetings, agenda items, attachments from Aug 2020–Aug 2025.

### Verified Evidence (Cleared for Publication)
- Auto-renewal clause in Maxim MSA [VERIFIED]
- $5,000 placement fee / conversion penalty [VERIFIED]
- Rate increase mechanism (uncapped) [VERIFIED]
- Consent agenda shift (Action Items → Consent by 2024) [PROOF]
- "Formerly Maxim" board acknowledgment (June 2024 Committee of the Whole) [PROOF]
- Mascot/CrowdStrike/$3M contract sandwich on same consent vote [PROOF]
- No emergency waivers ever declared for staffing vendors [PROOF — negative finding]
- RCW 28A.335.190 analysis — professional services not covered by competitive bid mandate [PROOF]
- Policy 6220 revised 5 times (2021-2025) without adding staffing bid requirements [PROOF]

### Narrative Boundaries (Sentinel-Enforced)
- **No cover-up rhetoric** — board acknowledged "formerly Maxim"; frame as failure of public scrutiny, not deception
- **Precise scope language** — "budgeted" vs "actual" must be stated explicitly
- **ProCare integration** — third-largest vendor proves systemic outsourcing, not isolated relationship
- **No multipliers** (Chief) — use raw dollar figures, not "38x" or "24-fold"
- **No PRR filing** — source anonymity protection. All evidence comes from publicly accessible records only.

## What Comes Next (Priority Order)
1. **Relay Dispatch #29** to team → Chief issues GREEN
2. **Woodward drafts Part II framework** using Dispatch #28 locked figures
3. **Sentinel drafts Right of Reply questions** for Blechschmidt and Fish
4. **Article 2 full rewrite** — existing draft at `workspaces/results/ARTICLE_2_THE_ACCOUNTABILITY_VOID.md` is STALE (uses $11.89M, 25.13%, incorrect board framing). Needs complete rewrite per Dispatch #28 parameters.
5. **Article 3 planning** — not started; requires peer district staffing data

## Key Dispatches (Read These First)
- **Dispatch #28 (CONTROLLING):** `workspaces/dispatches/TO_JOURNALIST/28_numbers_control_canonical_baseline.md` — The single controlling reference for all Article 2 figures
- **Dispatch #29:** `workspaces/dispatches/TO_JOURNALIST/29_verification_queries_green_clearance.md` — Verification queries + manual spot-checks for GREEN clearance
- **Dispatch #27:** `workspaces/dispatches/TO_JOURNALIST/27_object7_reconciliation.md` — F-195 Budgeted vs Actual extraction
- **Dispatch #26:** `workspaces/dispatches/TO_JOURNALIST/26_data_pulls_for_article2.md` — Neo4j vendor totals, governance edges, procurement policy text
- **Dispatch #25:** `workspaces/dispatches/TO_JOURNALIST/25_board_scrape_contract_terms.md` — MSA contract terms (auto-renewal, placement fee)
- **Dispatch #16:** `workspaces/dispatches/TO_JOURNALIST/16_master_data_correction_briefing.md` — Original deduplication master correction (partially superseded by #28)

## Items Outside Current Evidence Scope
These are not available through publicly accessible records and will NOT be pursued via PRR:
- Full current Amergis MSA (2021-22 terms are proven from board packets)
- Designated Signers resolution attachment (P6210 policy documented; names are not)
- HR vacancy data (Fish recruitment section stays scaffolding per Chief)
- Invoices / line-item detail

## Environment Notes
- **Docker/Neo4j:** Container `woodward-neo4j` with `restart: unless-stopped`. Bolt: `localhost:7688`, HTTP: `localhost:7475`. Auth: `neo4j/woodward_secure_2024`.
- **RCW 28A.335.190:** Full statute text at project root (`RCW 28A.335.190.pdf`). Key: $75K competitive bid threshold for equipment/supplies; professional services NOT enumerated.
- **F-195 text extractions:** Cached at `/tmp/*.txt` (may not persist across reboots). Re-extract with `pdftotext -layout` from `documents/F195/` or `For_NotebookLM/`.
- **Verified F-195 JSON:** `/tmp/f195_all_objects.json` — all Objects 1-9, Budgeted + Actual, all years. Also ingested into `woodward.db`.

## Team Architecture
- **Chief** — Editorial authority. Issues rulings on figures, framing, and publication clearance.
- **Woodward** — Drafts narrative prose. Evidence-tags every claim. Requests [PROOF] promotion via data pulls.
- **Neo** — Data architecture and integrity. Verifies math and graph queries. Issues structural warnings.
- **Sentinel** — Adversarial reviewer / Devil's Advocate. Enforces narrative boundaries. Drafts Right of Reply.
- **Antigravity (Architect)** — Data forensics, query execution, database management, dispatch production. Relays between team members. Only entity that touches databases directly.

## Critical Protocol
- **No AI communicates directly with another.** Architect (Antigravity) relays between team members.
- **No figures from Dispatch #16 or earlier** unless confirmed by Dispatch #28.
- **Source anonymity is paramount.** No PRR filings. All evidence from public records only.
