# New Chat Handoff — Project WoodWard (February 26, 2026)

## Objective
Continue the WoodWard investigative series. The project has completed Article 2 ("The Accountability Void") and fully locked the mathematical and structural data foundations for Article 3 ("The Systemic Trap") via Dispatch #31.

## Current Status (End of Session — February 26, 2026)

### Article 2: The Accountability Void
- **Status: COMPLETE & PUBLICATION READY**
- Chief's editorial reviews fully integrated. Fabricated dates (Sept 1) corrected to verified records (July 9). Unverified 6% premium figures removed. 
- "Special education teachers" explicitly injected into the narrative alongside SLPs and nurses per user instruction.
- Output files: `workspaces/results/ARTICLE_2_PUBLICATION_READY.md` and `workspaces/results/RIGHT_OF_REPLY_TRANSMISSION_READY.md`.

### Article 3: The Systemic Trap (Data Foundation)
- **Status: DATA LOCKED & VERIFIED (Dispatch #31)**
- Target roles for "Amergis Education" formally analyzed: Paraprofessionals, SPED Teachers (added this session), and SLPs/RNs.
- **Directive A (Internal Baseline):** Fully loaded costs established (Para $39.47/hr, SPED Teacher $61.02/hr, SLP/RN $67.76/hr). Includes VEA/VAESP base, SEBB, DRS, and 7.65% FICA.
- **Directive B (Lost Efficiency):** Sensitivity matrix locked at $45, $75, and $180/hr vendor bands. $13.3M spend mathematically evaluated.
- **Directive C (Peer Normalization):** VPS spends $2,274.77 per pupil on Object 7 (+$113 more than Evergreen despite serving fewer students).
- **Directive D (Attrition Proxy):** S-275 217 FTE reduction correlates directly with the $13.3M vendor spike.
- **New Narrative Pillar (Explanation D):** Chief approved "IDEA compliance risk management" as the fourth structural explanation for outsourcing (districts buying legal insurance rather than just plugging holes). 

### Database & Environment Status
- **SQLite** (`data/woodward.db`): Contains 55,191 deduped payment records. Primary source of truth for all query validations.
- **Neo4j DB Migration**: A complete Neo4j database wipe/re-ingestion plan exists in `IMPLEMENTATION_PLAN.md` and `VS_CODE_HANDOFF.md` but is currently PENDING execution. If graph analytics are heavily required soon, phase 0 of that specific plan must be initiated.
- **LanceDB**: Vector sidecar maintains local board docs and contract queries.
- **No PRR filing remains absolute policy** — source anonymity protection.

## What Comes Next (Priority Order FOR NEW CHAT)
1. **Draft Article 3:** Instruct Neo/Woodward to draft "Article 3: The Systemic Trap" using the parameters in `/workspaces/dispatches/TO_JOURNALIST/31_article3_master_extraction.md` and the four pillars defined above.
2. **Review Draft Constraints:** Ensure SPED teachers are prominently featured in the text, and do NOT use the phrase "compliance theater" (per Chief's strict order).
3. **Right of Reply:** Draft Special Services Right-of-Reply questions (currently parked in earlier documents) to accompany Article 3 once the draft is greenlit.

## Key Dispatches (Read These First in New Chat)
- **Dispatch #31 (CONTROLLING FOR ART 3):** `workspaces/dispatches/TO_JOURNALIST/31_article3_master_extraction.md` — The exact tabular schema Neo requested to build Article 3.
- **Article 2 Final:** `workspaces/results/ARTICLE_2_PUBLICATION_READY.md` — The tone and structural predecessor to Article 3.
- **Dispatch #28 (CONTROLLING FOR ART 2):** `workspaces/dispatches/TO_JOURNALIST/28_numbers_control_canonical_baseline.md` — The canonical overarching dollar figures.

## Team Architecture
- **Chief** — Editorial authority. Issues rulings on figures, framing, and publication clearance.
- **Woodward** — Drafts narrative prose. Evidence-tags every claim. Requests [PROOF] promotion.
- **Neo** — Data architecture and integrity. Verifies math and graph queries. Issues structural warnings.
- **Sentinel** — Adversarial reviewer / Devil's Advocate. Enforces narrative boundaries. Drafts Right of Reply.
- **Antigravity (Architect)** — Data forensics, query execution, database management, dispatch production. Relay for all AI personas.
