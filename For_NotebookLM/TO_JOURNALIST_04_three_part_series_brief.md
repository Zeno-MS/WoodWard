# MISSION BRIEF: THE WOODWARD 3-PART SERIES
**To:** All Stations (Antigravity · NotebookLM · Gemini Gem · ChatGPT Pro · Claude Opus)
**From:** WoodWard (Chief Editor / Lead Analyst / Architect)
**Subject:** 3-Part Investigation Series — Structural Privatization at Vancouver Public Schools
**Version:** 2.1 — Post-History Review Edition
**Updated:** 2026-02-20

---

## PART A: THE NEWSROOM — AI PLATFORM ROLES & RELAY PROTOCOL

### The Architect (You, Chris)
You are the **human relay hub**. Every AI platform communicates with every other AI platform *through you*. No platform has direct access to another. Your job is to:
1. Copy outputs from one platform and paste them into another when directed
2. Make judgment calls when platforms disagree
3. Maintain the evidence chain — nothing gets published without your sign-off

### The Hub: Antigravity IDE (Gemini 3 Pro)
**Codename:** Antigravity
**Role:** Operations Center, Data Forensics, File Management, Draft Generation
**Strengths:** Code execution, database queries, file system access, structured analysis, parallel agent dispatch, artifact generation
**Cost Tier:** ★☆☆☆ (Included — use liberally)

**Owns:**
- All code execution (Python, SQL, data extraction)
- Database queries against `woodward.db` (25,578 payment records)
- File management — reading/writing all project files
- Draft generation (Article 1 complete; Articles 2 & 3 pending)
- Visualization generation (charts, tables)
- Export preparation (NotebookLM file bundles, handoff documents)
- Git version control of all project artifacts

**Relay Instructions for Antigravity:**
> When you need fact-checking, say: *"RELAY TO NOTEBOOKLM: [exact question]. Paste back the response with source citations."*
> When you need narrative polish, say: *"RELAY TO CHATGPT: [draft section + instructions]. Paste back the revised text."*
> When you need adversarial review, say: *"RELAY TO CLAUDE: [draft + specific concern]. Paste back the critique."*

---

### The Library: NotebookLM (Gemini 3.1 Pro)
**Codename:** The Library
**Role:** Source-Grounded Fact-Checker, Cross-Reference Engine, Citation Machine
**Strengths:** Persistent memory across 245+ uploaded source documents, grounded answers with exact citations, audio overview generation
**Cost Tier:** ★☆☆☆ (Included — use liberally)

**Sources Loaded:** (from `For_NotebookLM/` directory)
- 193 Board Meeting PDFs (2016–2025)
- All `woodward.db` tables exported as CSV (payments, vendors, contracts, board_votes)
- F-195 Budget PDFs (2024-25, 2025-26)
- Salary data (Top40 CSVs, 5-year trends, staffing benchmarks)
- Cost comparison CSV, vendor spending CSVs
- All 4 article drafts + series brief + master plan
- Both compass artifacts + investigative briefing
- All dispatches (journalist, accountant, legal)
- Contract clause analysis JSON

**Owns:**
- **Fact verification** — "Does the evidence support this claim? Cite the document."
- **Cross-referencing** — "Find every mention of [X] across all 193 board meetings."
- **Citation generation** — "What is the exact source for [claim]?"
- **Gap identification** — "What claims in this draft lack source support?"
- **Timeline construction** — "Build a chronology of [topic] from board minutes."
- **Audio overviews** — Generate podcast-style summaries for review away from screen

**Standard Prompts for NotebookLM:**

| Task | Prompt Template |
|------|----------------|
| **Fact-check a claim** | *"Verify: [specific claim]. Which source document confirms or contradicts this? Quote the exact passage."* |
| **Find all mentions** | *"Search all sources for mentions of [Amergis/consent agenda/Object 7/etc]. List each mention with document name and relevant excerpt."* |
| **Check draft against sources** | *"Here is a draft section: [paste]. For each factual claim, confirm it is supported by an uploaded source. Flag any unsupported claims."* |
| **Build timeline** | *"From the board meeting PDFs, construct a chronological timeline of all actions related to [staffing contracts/budget cuts/etc]."* |
| **Identify gaps** | *"Compare this article draft against all uploaded evidence. What important evidence exists in the sources that the draft does NOT mention?"* |

**Relay Instructions for NotebookLM:**
> When a fact cannot be verified, respond: *"UNVERIFIED — Send to Antigravity for database query: [specific SQL or file lookup needed]."*
> When you find a discrepancy, respond: *"DISCREPANCY FOUND — Send to Claude for adjudication: [describe the conflict between sources]."*

---

### The Persona: Gemini Gem (Gemini 3.1 Pro, Custom)
**Codename:** WoodWard (the Journalist Persona)
**Role:** Persistent Investigative Journalist Voice, Narrative Consistency, Tone Enforcement
**Strengths:** Custom system instruction = persistent persona across sessions, long context window, no session memory loss on persona
**Cost Tier:** ★☆☆☆ (Included — use liberally)

**Custom Gem System Instruction:**
```
You are WoodWard, an AI investigative journalist modeled after Bob Woodward.
Your voice: Professional, authoritative, clinical, cutting. Active voice. Name names.
Your method: "Follow the money." Always ask: "Who benefits?"
Your constraint: Never speculate without evidence. If a link is missing, demand it.
Your output: Publication-grade investigative prose. Not summaries — stories.
Forensic language only. No hyperbole. Cite numbers to the cent.
You are currently working on a 3-part series about fiscal mismanagement at
Vancouver Public Schools. The core finding: VPS paid $11.89M to Amergis
(formerly Maxim Healthcare, $150M fraud settlement) while cutting 260+ staff
and declaring a $35M deficit.
```

**Owns:**
- **Narrative drafting** — Write sections in the WoodWard voice with consistent tone
- **Tone enforcement** — Review drafts from other platforms and flag tone breaks
- **Rewriting** — Take data-heavy outputs from Antigravity and transform them into narrative prose
- **Interview question generation** — Draft right-of-reply questions for district officials
- **Headline and lede testing** — Generate multiple lede options for editorial selection

**Relay Instructions for Gemini Gem:**
> When you need raw data, say: *"I need the following from Antigravity: [specific data point/query]. Send me back the result and I will draft the passage."*
> When you need fact-checking, say: *"RELAY TO NOTEBOOKLM: Verify the following claims before I finalize this section: [list claims]."*

---

### The Thinker: ChatGPT Pro (GPT-5.2 Thinking)
**Codename:** Neo
**Role:** Deep Reasoning, Complex Analysis, Long-Form Drafting, Structural Editing
**Strengths:** Extended thinking mode for multi-step reasoning, strong narrative drafting, excellent at structural reorganization
**Cost Tier:** ★★☆☆ (Subscription — use for complex tasks)

**Owns:**
- **Structural editing** — "This draft has 7 sections. Should it have 5? Reorganize for maximum impact."
- **Complex calculations with reasoning** — Lost Efficiency extrapolations, sensitivity analysis, premium modeling
- **Adversarial defense testing** — "You are the VPS Communications Director. Poke holes in this article."
- **Legal risk review** — "Identify any claim in this draft that could expose the publisher to defamation liability."
- **Long-form drafting** — When a full article section needs to be written from a data brief
- **Cross-verification** — Independent recalculation of Antigravity's numbers (Phase 2 of verification protocol)

**Standard Prompts for ChatGPT:**

| Task | Prompt Template |
|------|----------------|
| **Structural edit** | *"Here is Article [N]. Evaluate the narrative structure. Is the argument building properly? Where does it lose momentum? Suggest a revised outline."* |
| **Devil's Advocate** | *"You are the VPS Superintendent's communications team. Read this article and draft your strongest possible rebuttal. Then, as the journalist, identify which rebuttals have merit and which are deflection."* |
| **Legal review** | *"Review this draft for defamation risk. Flag any assertion of fact that is not adequately sourced, any opinion presented as fact, and any implication of criminal conduct without sufficient evidence."* |
| **Recalculate** | *"Using ONLY the following data: [paste raw numbers]. Independently calculate [metric]. Show all work. Do NOT reference any prior calculation."* |

**Relay Instructions for ChatGPT:**
> When you need source verification, say: *"RELAY TO NOTEBOOKLM: Before I finalize this analysis, verify these data points against primary sources: [list]."*
> When your recalculation disagrees with Antigravity, say: *"DISCREPANCY — My calculation of [X] yields [Y], but Antigravity produced [Z]. Send both to Claude for adjudication."*

---

### The Judge: Claude Opus (Claude 4.6)
**Codename:** The Judge
**Role:** Final Editorial Review, Adversarial Stress Test, Discrepancy Adjudication, Ethical Review
**Strengths:** Exceptional nuance, careful reasoning, strong at identifying logical gaps and ethical concerns
**Cost Tier:** ★★★★ (Expensive — use surgically, not routinely)

**Use ONLY For:**
1. **Final article review** — After all other platforms have contributed, Claude does the last read before publication
2. **Discrepancy adjudication** — When Antigravity and ChatGPT disagree on a number or interpretation
3. **Ethical/legal stress test** — "Is this article fair? Does it give adequate weight to the district's defense?"
4. **Tone calibration** — "Is this clinical and forensic, or has it crossed into editorializing?"
5. **Publication readiness assessment** — GREEN / YELLOW / RED status with specific blockers

**Standard Prompts for Claude:**

| Task | Prompt Template |
|------|----------------|
| **Final review** | *"You are the senior editor at a Pulitzer-level investigative desk. This article will be published under your name. Read it. Would you sign off? If not, what must change?"* |
| **Adjudicate** | *"Two independent calculations produced different results for [metric]. Calculation A: [paste]. Calculation B: [paste]. Which is correct? Show your reasoning."* |
| **Fairness test** | *"Read this article as a VPS board member who genuinely believes they are doing their best in impossible circumstances. Is this article fair to that person? Where is it unfair?"* |
| **Publication decision** | *"Assess this article for publication readiness. Rate: GREEN (publish), YELLOW (fixable issues), RED (structural problems). List every issue."* |

**Relay Instructions for Claude:**
> When you identify a factual gap, say: *"RELAY TO NOTEBOOKLM: I need source confirmation for: [specific claim]. This is blocking publication."*
> When you need a rewrite, say: *"RELAY TO CHATGPT: Rewrite the following section. Problem: [describe issue]. Constraint: [describe requirement]. Maintain forensic tone."*
> When you need data, say: *"RELAY TO ANTIGRAVITY: Query the payments database for [specific question]. I need this to adjudicate a discrepancy."*

---

## PART B: THE RELAY PROTOCOL

### How Messages Flow

```
                    ┌──────────────┐
                    │  ARCHITECT   │
                    │   (Chris)    │
                    │  Human Hub   │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
     │ ANTIGRAVITY │ │ NOTEBOOK │ │  GEMINI GEM │
     │   (Hub)     │ │   LM     │ │ (WoodWard)  │
     │ Data+Code   │ │ Library  │ │   Voice     │
     └──────┬──────┘ └────┬─────┘ └──────┬──────┘
            │              │              │
            └──────┬───────┘              │
                   │                      │
            ┌──────▼──────┐        ┌──────▼──────┐
            │  CHATGPT    │        │   CLAUDE    │
            │   (Neo)     │        │  (Judge)    │
            │  Thinking   │        │  Final Edit │
            └─────────────┘        └─────────────┘
```

### Relay Message Format

When any AI says **"RELAY TO [PLATFORM]:"** — copy everything after the colon and paste it into the target platform. Then copy the response back. Always include the source:

> **From [Source Platform]:** [pasted response]

### The Ping-Pong Protocol

For iterative refinement, use this loop:

1. **Antigravity** generates raw draft section from data
2. **Architect** pastes draft into **Gemini Gem** → "Rewrite this in the WoodWard voice"
3. **Architect** pastes Gem output into **NotebookLM** → "Fact-check every claim. Cite sources."
4. **Architect** pastes fact-checked draft into **ChatGPT** → "Structural edit. Does this section earn its place?"
5. *(Only if needed)* **Architect** pastes near-final draft into **Claude** → "Final editorial review. Publication ready?"

### Cost-Optimization Rules

| Priority | Platform | When to Use |
|----------|----------|-------------|
| 1st | **NotebookLM** | Always try here first for any fact/source question |
| 2nd | **Gemini Gem** | Narrative drafting, voice consistency, rewriting |
| 3rd | **Antigravity** | Data queries, code, file ops, calculations, draft generation |
| 4th | **ChatGPT** | Complex reasoning, structural edits, devil's advocate, recalculation |
| 5th | **Claude** | Final review only — never for first drafts or routine questions |

**Rule of thumb:** If NotebookLM or the Gem can answer it, don't send it to ChatGPT. If ChatGPT can answer it, don't send it to Claude. Claude sees drafts exactly **once** — at the end.

---

## PART C: SERIES SKELETON (Unchanged Core — Updated Workflow)

### ARTICLE 1: The Austerity Paradox (Focus: The Numbers & The Rebrand)
**Status:** ✅ DRAFT COMPLETE → `ARTICLE_1_THE_AUSTERITY_PARADOX.md`

**Core Thesis:** In the exact year Vancouver Public Schools declared a $35M budget deficit and cut 260+ staff, it accelerated a massive, uncapped wealth transfer—$11.89 million—to a single private staffing corporation with a history of Medicaid fraud.

**Structure:**
1. **The Lede:** Contrast the 24-25 classroom cuts with the $11.89M wire transfers to Amergis.
2. **The "Object 7" Explosion:** How "Purchased Services" consumed 11.67% ($47.3M) of the budget while teacher salaries bled.
3. **The Stealth Rebrand:** Maxim Healthcare ($150M Medicaid fraud, 2011) → Amergis (2022). Zero public disclosure.
4. **The Handoff Data:** $14.4M (22-23, Maxim) → overlap (23-24) → $11.89M (24-25, Amergis).
5. **The Missing Ceiling:** The 2021 contract's Attachment A — uncapped rates, auto-renewal, 30-day rate changes.

**Remaining Workflow:**
| Step | Platform | Task |
|------|----------|------|
| 1 | **NotebookLM** | Fact-check every claim in Article 1 against uploaded sources |
| 2 | **ChatGPT** | Structural edit + Devil's Advocate rebuttal |
| 3 | **ChatGPT** | Legal risk review (defamation scan) |
| 4 | **Claude** | Final editorial review — GREEN/YELLOW/RED assessment |
| 5 | **Antigravity** | Incorporate all feedback, produce final draft |

---

### ARTICLE 2: The Accountability Void (Focus: Governance & Administrative Failure)
**Status:** 🟡 IN PROGRESS — Evidence gathered, draft not started

**Core Thesis:** A $28 million corporate pipeline does not build itself. It relies on the deliberate or severely negligent failure of HR and Finance, aided by a Board that rubber-stamps multi-million dollar contracts in seconds.

**Structure:**
1. **The Lede:** The "Consent Agenda" — how $11.89M is approved alongside minor facility repairs without debate.
2. **The Graph Data & Procurement Red Flags:** 82 separate Amergis/Maxim contract authorizations (2016–2025) amidst state auditor findings (2021, 2024) for procurement violations.
3. **The HR Failure (Jeff Fish) & The Shell Game:** Abandonment of SPED recruitment, masking central office bloat (48% growth despite enrollment drops) through title-repurposing, and ignoring a 29% SPED staff turnover fueled by safety crises.
4. **The Finance Failure (Brett Blechschmidt):** $35M austerity presented as unavoidable, ignoring the "ESSER Fiscal Cliff," while driving the district toward state takeover ("Binding Conditions") via three years of emergency borrowing.
5. **The Superintendent Contrast:** Jeff Snell's salary climb to $412,544 concurrent with privatization and a fund balance drawn down to $195,180.

**Drafting Workflow:**
| Step | Platform | Task |
|------|----------|------|
| 1 | **NotebookLM** | "Find every consent agenda item involving staffing contracts >$100K. List date, vendor, amount, and whether it was pulled for discussion." |
| 2 | **NotebookLM** | "Build a timeline of Jeff Fish's and Brett Blechschmidt's appearances in board minutes." |
| 3 | **Antigravity** | Query `woodward.db` for quarterly payment acceleration — build the "ramp" visualization |
| 4 | **Gemini Gem** | Draft Article 2 body sections in WoodWard voice from data brief |
| 5 | **ChatGPT** | Structural edit + adversarial defense test ("You are Jeff Fish's attorney…") |
| 6 | **NotebookLM** | Fact-check the draft against all sources |
| 7 | **Claude** | Final review — one pass, publication readiness |
| 8 | **Antigravity** | Final integration, file management, version control |

---

### ARTICLE 3: The Systemic Trap (Focus: The Premium & The Policy)
**Status:** 🔴 NOT STARTED — Requires Article 2 completion + peer data

**Core Thesis:** The district is trapped between federal mandates and state funding failures, forcing a 15-30% premium to middlemen. But instead of fighting the trap, leadership surrendered to it.

**Structure:**
1. **The Lede:** The specific math of "The Premium" — 13.8% for paras, 31.9% for behavior techs.
2. **The "Lost Efficiency" Calculation:** For every $1M to Amergis, VPS hemorrhages 2+ FTE equivalents.
3. **The SEBB / IDEA Squeeze & Out-of-District Costs:** Acknowledge the structural defense (state underfunding, massive $100k/student private placement costs) — then show why it's insufficient.
4. **The Cycle of Defeat (The Agency Trap):** How under-supporting direct-hire staff leads to turnover/violence (VAESP strike threat), forcing reliance on agencies, which drains funds needed to support direct hires.
5. **The Conclusion:** Call for a state audit of Object 7 spending statewide before more districts hit binding conditions.

**Drafting Workflow:**
| Step | Platform | Task |
|------|----------|------|
| 1 | **Antigravity** | Run sensitivity analysis on Lost Efficiency at conservative/mid/high bill rates |
| 2 | **Antigravity** | Extract peer district Object 7 data (Evergreen, Battle Ground, Camas) from OSPI |
| 3 | **ChatGPT** | Independent recalculation of all premium figures (cross-verification protocol) |
| 4 | **NotebookLM** | Verify SEBB/IDEA/McCleary claims against uploaded legislative sources |
| 5 | **Gemini Gem** | Draft Article 3 body sections in WoodWard voice |
| 6 | **ChatGPT** | "You are a state legislator defending the current funding model. Rebut this article." |
| 7 | **NotebookLM** | Final fact-check pass |
| 8 | **Claude** | Senior editor review — fairness test + publication readiness |
| 9 | **Antigravity** | Final integration, full series consistency check |

---

## PART D: CROSS-VERIFICATION PROTOCOL

Any number that appears in the final published story **must survive all four checks**:

| Check | Platform | Purpose |
|-------|----------|---------|
| 1. Primary calculation | **Antigravity** | Generate the number from raw data |
| 2. Independent recalculation | **ChatGPT** (Thinking mode) | Same data, same question, no prior answer shown |
| 3. Source verification | **NotebookLM** | "Does the primary source document support this number?" |
| 4. Editorial sanity check | **Claude** | "Is this number plausible? Does it pass the smell test?" |

**If any check fails:** Investigate before proceeding. Three AIs agreeing on a wrong number is still wrong. The Architect's manual spot-check is the final kill switch.

---

## PART E: QUICK-REFERENCE CHEAT SHEET

### "I need to…"

| Task | Go to… |
|------|--------|
| Query the payments database | **Antigravity** |
| Find something in a board meeting PDF | **NotebookLM** |
| Write a section in the WoodWard voice | **Gemini Gem** |
| Get a structural edit on a full article | **ChatGPT** |
| Stress-test a draft for fairness/legal risk | **ChatGPT** first, then **Claude** for final |
| Resolve a disagreement between platforms | **Claude** (adjudicator of last resort) |
| Generate a chart or visualization | **Antigravity** |
| Check if a claim is sourced | **NotebookLM** |
| Export files for another platform | **Antigravity** |
| Get a publication-readiness decision | **Claude** (one time, at the end) |

---

## STANDING ORDERS

1. **Clinical tone only.** No hyperbole. Forensic language. We follow the money.
2. **Every claim needs a receipt.** If NotebookLM can't find the source, the claim doesn't publish.
3. **Claude sees each article exactly once** — at the end, for final review. Don't waste the budget on iteration.
4. **When platforms disagree, the Architect decides** — informed by Claude's adjudication if needed.
5. **Version control everything.** Antigravity commits all drafts to the WoodWard repo after each major revision.
6. **Right of reply is mandatory.** No article publishes without documented questions sent to VPS.

---

*— WoodWard, Chief Editor*
*Brief v2.0 | Multi-AI Orchestration | 2026-02-20*
