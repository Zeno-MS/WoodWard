# OPERATION ACCOUNTABILITY: MASTER INVESTIGATION PLAN
## Vancouver Public Schools — The Object 7 Investigation
### Classification: OPERATIONAL | Version 2.0 | February 6, 2026

---

## REVISION NOTES (v1.0 → v2.0)
- Added **Part 0: The Toolkit** — complete platform-role mapping with operational security classifications
- Restructured **Phase 1 and Phase 2** task assignments to leverage Antigravity IDE as Neo's primary execution environment with parallel agent dispatching
- Added **AI Studio** as the prompt testing and cross-verification layer
- Added **tool-specific security classifications** (Cloud vs. Local) throughout
- Refined **Neo prompts** to specify execution environment and output format
- Added **Verification Protocol** using model-switching in Antigravity for critical calculations
- Expanded **AnythingLLM** role for sensitive document processing
- All other content (Situational Assessment, Theory of Case, Evidence Architecture, Phases 3-7, OpSec, Editorial Notes) carried forward with minor refinements

---

## CHIEF'S SITUATIONAL ASSESSMENT

Before we run a single task, I need to be honest with you about what you have and what you don't.

### What You Have (Strengths)
- **A compelling hypothesis** backed by structural logic: VPS claims a $35M deficit while simultaneously maintaining inelastic, uncapped payments to private staffing agencies through Object 7.
- **A documented regulatory mechanism** (McCleary → Levy Swap → SEBB → Agency Trap) that explains *how* this happened. This causal chain is well-sourced.
- **Three strong research documents** that synthesize public records, SAO audits, board minutes, and budget data into a coherent forensic narrative.
- **A multi-AI team** with clearly defined roles and complementary capabilities.
- **A deep toolkit** — Antigravity IDE's multi-agent orchestration, Colab's data processing, AnythingLLM's local RAG, and cross-verification capabilities across four distinct AI providers.
- **Insider knowledge** of the district's operations.

### What You Don't Have (Gaps — and these are publication-blocking)
1. **No specific dollar figures for annual vendor payments.** Your documents describe the *pattern* of spending but do not contain extracted, year-by-year totals for Soliant, Amergis, or Pioneer. The "Contractor Spending" doc references individual warrant checks ($7,500 here, $3,050 there) but never totals them. Without annual totals, you cannot calculate the "Lost Efficiency" number that the briefing calls "your headline."
2. **No actual F-195 data in your files.** Your documents *reference* F-195 forms repeatedly but the actual Object 7 line-item figures are not present in any uploaded material. You have narrative descriptions of trends ("Sharp Increase," "Inelastic") but not the numbers behind them.
3. **No Master Service Agreement (MSA) text.** The briefing correctly identifies the Amergis MSA as a key document, but you don't have it. Without it, claims about "variable rate billing" and "uncapped" contracts are inference, not proof.
4. **No direct comparison data.** You assert Amergis charges ~$85/hr vs. ~$45/hr internal cost. These figures appear in your research docs but are not sourced to a specific VPS document or invoice. Where do these numbers come from? If they're estimates, they must be labeled as such.
5. **No right of reply.** Zero contact with district administration, board members, or the vendor companies. This is appropriate at this stage, but it's a hard prerequisite before any publication.
6. **Your research documents contain sourcing problems.** Several citations point to documents from *other districts* (Aberdeen, Ridgefield, Battle Ground, Laguna Beach, Ingham ISD in Michigan, Harris County TX). These are used to establish regional patterns, which is legitimate — but some passages blur the line between "this happened at VPS" and "this happened at a comparable district." A hostile reader will exploit every instance.

### Bottom Line Assessment
**Status: RED — Not ready for publication. Ready for structured investigation.**

You have excellent *intelligence* — a strong analytical framework with a clear theory of the case. What you need now is *evidence* — specific, primary-source documentation that either proves or disproves the hypothesis. The master plan below is designed to get you from RED to GREEN.

---

## PART 0: THE TOOLKIT — PLATFORM ROLES AND SECURITY CLASSIFICATIONS

Every tool in the arsenal has a specific role. Using the wrong tool for the wrong task wastes time or — worse — creates security exposure. Here's the definitive mapping.

### Platform-Role Matrix

| Platform | Role in Operation | Primary User | Security Class | Best For |
|----------|------------------|--------------|----------------|----------|
| **Claude Opus 4.5 Pro** | Chief — Editorial oversight, evidence evaluation, legal/ethical review | Architect | **CLOUD** — Anthropic servers | Long-form synthesis, editorial review, adversarial analysis, strategic planning |
| **ChatGPT 5.2 Plus** | Neo — Forensic analysis, data extraction, OSINT; Woodward — Narrative drafting, systemic analysis | Architect (relay) | **CLOUD** — OpenAI servers | Structured data analysis, rapid hypothesis generation, narrative construction |
| **Google Antigravity IDE** | **Primary workbench** — Multi-agent orchestration, code execution, browser automation, parallel task dispatch | Architect + Neo agents | **CLOUD** — Google servers | Running multiple analysis tasks simultaneously; code that needs editor + terminal + browser access; visual verification of outputs |
| **Google Colab Pro** | **Data processing pipeline** — Heavy computation, notebook-style iterative analysis | Architect + Neo | **CLOUD** — Google servers | Large dataset processing, GPU-accelerated analysis, persistent notebook workflows, matplotlib visualization |
| **Google AI Studio** | **Prompt laboratory + verification layer** — Test prompts before deployment, cross-verify critical claims via Gemini 3 Pro | Architect | **CLOUD** — Google servers | Prompt prototyping, running Gemini as independent verification against Claude/ChatGPT outputs, multimodal document analysis |
| **GitHub + Copilot Pro** | **Repository + version control** — Store investigation code, data pipelines, and analysis scripts | Architect | **CLOUD** — Microsoft servers; use PRIVATE repos only | Version-controlled analysis scripts, collaboration artifacts, code review |
| **Perplexity Pro** | **Real-time OSINT** — Web research with citations, source discovery, fact verification | Architect | **CLOUD** — Perplexity servers | Live web searches with cited sources, corporate entity research, verifying claims against current public records |
| **Gemini 3 Pro** (via AI Studio or Antigravity) | **Cross-verification + large context** — Alternative analysis, document processing with 1M token context | Architect | **CLOUD** — Google servers | Processing entire F-195 documents in single context, alternative interpretation of data, breaking ties between conflicting AI outputs |
| **NotebookLM Pro** | **Investigation memory** — Source synthesis, knowledge management, document Q&A | Architect | **CLOUD** — Google servers | Maintaining investigation continuity across sessions, generating audio overviews for review, cross-referencing source documents |
| **AnythingLLM** | **Secure local processing** — Sensitive document RAG, source-identifying material | Architect | **LOCAL** — Your iMac only | Anything involving insider knowledge, source-identifying details, draft communications, operational planning that references your position |

### Security Classification Rules

**CLOUD tools (all except AnythingLLM):**
- Never input information that could only be known by someone in your specific position
- Never input names of potential sources or whistleblowers
- Never input draft communications that identify you as an insider
- Treat all inputs as potentially discoverable
- Safe for: public records analysis, publicly available documents, general research, code execution

**LOCAL tools (AnythingLLM):**
- Use for any analysis that requires insider context
- Use for drafting communications where your identity must be protected
- Use for processing documents obtained through your employment (if any — note: we recommend against using internal documents; see OpSec section)
- Use for maintaining the "source protection layer" of the investigation

### Antigravity IDE: Operational Configuration for This Investigation

Antigravity is your force multiplier. Here's how to configure it for investigative work:

**Recommended Mode:** Review-driven development
- The agent makes decisions and executes, but pauses at verification checkpoints for your approval
- This prevents autonomous actions on sensitive analysis without your sign-off

**Model Selection Strategy:**
- **Gemini 3 Pro** (default): Primary analysis work, data extraction, code generation
- **Claude Sonnet 4.5**: Cross-verification of critical calculations, alternative interpretation
- Switch models *per-task* based on what's being calculated — this is your built-in fact-checking layer

**Workspace Organization:**
```
Antigravity Workspaces:
├── VPS-F195-Analysis/        # F-195 data extraction and trend analysis
├── VPS-Vendor-Tracking/      # Consent agenda scraping, vendor payment tabulation
├── VPS-Peer-Comparison/      # Evergreen, Battle Ground, Camas comparison data
├── VPS-Premium-Calculation/  # Lost Efficiency / FTE conversion modeling
└── VPS-Visualization/        # Charts, graphs, publication-ready figures
```

**Key Advantage:** Antigravity's Manager view lets you dispatch agents into each workspace simultaneously. While one agent extracts F-195 data, another scrapes board agendas, and a third runs the peer comparison. Each produces Artifacts (task lists, implementation plans, screenshots, data outputs) that you verify before proceeding. This collapses what would be sequential weeks of work into parallel days.

### Cross-Verification Protocol (MANDATORY for Publication-Critical Numbers)

Any number that will appear in the final published story must survive the following:

1. **Primary calculation** — Run by Neo (ChatGPT 5.2) in Antigravity or Colab
2. **Independent verification** — Same calculation, same data, run by Gemini 3 Pro in AI Studio (or by switching models in Antigravity)
3. **Sanity check** — I (Chief, Claude Opus 4.5) review the methodology, assumptions, and outputs
4. **Manual spot-check** — Architect independently verifies at least one data point against the original source document by hand

If any step produces a discrepancy, we investigate before proceeding. Three AI models agreeing on a wrong number is still a wrong number — the manual spot-check is the kill switch.

---

## PART 1: THE THEORY OF THE CASE

### The Hypothesis (One Sentence)
Vancouver Public Schools is experiencing a structurally manufactured fiscal crisis in which a $35 million deficit — used to justify cutting 260+ classroom positions — coexists with millions in uncapped, minimally scrutinized payments to private staffing agencies whose costs are shielded from public oversight by their categorization as "Purchased Services" (Object 7) and their protection under federal IDEA mandates.

### The Causal Chain (What We Must Prove)

| Link | Claim | Evidence Needed | Current Status |
|------|-------|----------------|----------------|
| 1 | McCleary/Levy Swap capped district revenue autonomy | Legislative record, ESD 112 analysis | **PROVEN** — Public law, well-documented |
| 2 | SEBB implementation made direct hires cost-prohibitive for part-time/variable roles | SEBB mandate text, district budget projections showing cost increase | **STRONG INFERENCE** — $3M+ cost cited in research but needs primary source |
| 3 | District shifted staffing to Object 7 vendors instead of building internal capacity | F-195 Object 7 trend data (2015-2025), year-over-year | **SUSPICION** — Trend described narratively; actual numbers not yet extracted |
| 4 | Vendor payments are inelastic even during austerity | F-195 data showing Object 7 stable/rising while Object 2 (salaries) falls during 2024-25 cuts | **SUSPICION** — Logical inference, not yet documented with numbers |
| 5 | Consent agenda mechanism obscures cumulative vendor costs from public oversight | Board meeting minutes showing bundled approvals | **STRONG INFERENCE** — Pattern documented in multiple minutes |
| 6 | The vendor premium represents quantifiable "lost efficiency" | Bill rate vs. internal cost comparison; FTE conversion calculation | **SPECULATION** — $85 vs. $45 figures need sourcing |
| 7 | District had alternatives but chose not to pursue them | Evidence of recruitment failures, internal capacity-building attempts (or lack thereof) | **NOT YET INVESTIGATED** |

**The critical gap is Links 3, 4, and 6.** These require actual numbers from actual documents. Everything else is context and mechanism.

---

## PART 2: THE EVIDENCE ARCHITECTURE

### Tier 1: Primary Documents (Must Obtain)

These are the documents without which no story can be published.

| # | Document | Where to Get It | What It Proves | Assigned To |
|---|----------|-----------------|----------------|-------------|
| 1 | **F-195 Budget Reports (2018-2025)** — specifically Object 7 line items by program | OSPI public records portal (EDS system) or direct public records request to VPS | The actual dollar trajectory of Purchased Services spending | **Architect** (public records retrieval) → **Neo** (data extraction in Antigravity `VPS-F195-Analysis` workspace) |
| 2 | **F-195F (Actual Expenditure Reports)** — same Object 7 breakdowns | Same as above — these show what was *actually spent*, not just budgeted | Whether actual spending exceeded budgeted amounts for vendors | **Architect** → **Neo** (same workspace) |
| 3 | **Board Consent Agendas (2020-2025)** — all entries mentioning Soliant, Maxim, Amergis, Pioneer | VPS website board archives; BoardDocs if used | Cumulative approved contract values; frequency of renewals | **Neo** (Antigravity `VPS-Vendor-Tracking` workspace — browser agent can scrape board archives) |
| 4 | **Master Service Agreement(s) with Amergis** | Public records request under WA RCW 42.56 | Rate structures, term length, auto-renewal clauses, liability provisions | **Architect** (formal request) → **AnythingLLM** (local analysis once obtained) |
| 5 | **Safety Net Reimbursement Claims** | OSPI Safety Net records (may require records request) | How much of the vendor cost is subsidized by state reimbursement | **Architect** → **Perplexity** (initial research on what's publicly available) |
| 6 | **SAO Audit Reports for VPS (2019-2025)** | portal.sao.wa.gov (you have 2 already; need complete set) | Procurement findings, internal control weaknesses | **Neo** (Antigravity browser agent retrieval from SAO portal) |

### Tier 2: Comparative and Contextual Documents

| # | Document | Purpose | Tool |
|---|----------|---------|------|
| 7 | F-195 Object 7 data for Evergreen SD, Battle Ground SD, Camas SD | Establish whether VPS's vendor reliance is anomalous vs. peer districts | **Neo** (Antigravity `VPS-Peer-Comparison` workspace) |
| 8 | OSPI prototypical school staffing model | Quantify the gap between funded and actual SpEd staffing | **Perplexity** (source discovery) → **Gemini 3 Pro** (large-context analysis in AI Studio) |
| 9 | VEA and VAESP collective bargaining agreements (current) | Verify salary schedules to calculate true internal cost comparisons | **Architect** (you already have VEA CBA link in your research docs) → **NotebookLM** (source synthesis) |
| 10 | Amergis/Maxim corporate filings (WA Secretary of State) | Corporate structure, officers, registered agent | **Perplexity** (OSINT search) |
| 11 | Maxim Healthcare 2011 Medicaid fraud settlement records | Pattern of conduct (if officer overlap exists) | **Perplexity** (public record search) |

### Tier 3: Source Development (Handle With Extreme Care)

| Source Type | Value | Risk | Protocol |
|-------------|-------|------|----------|
| Current SpEd paraeducators | Working conditions, safety concerns, agency staff interactions | **HIGH** — identifiable by role/building; retaliation risk | Anonymous only; no identifying details in any draft |
| VEA/VAESP union leadership | Institutional perspective on staffing decisions | **MODERATE** — public-facing role reduces personal risk | On record preferred; verify willingness |
| Former board members | Governance culture, consent agenda practices | **LOW-MODERATE** — no longer in power | Background/on record |
| OSPI oversight staff | State-level perspective on VPS fiscal health | **LOW** — institutional source | Background initially |

**SOURCE PROTECTION PARAMOUNT:** Given your insider position, no human source development should occur until the documentary evidence phase is substantially complete. Documents don't have feelings, can't be intimidated, and don't change their story. Build the case on paper first. Human sources confirm and add color — they should never be the foundation.

---

## PART 3: THE WORKFLOW — SEVEN PHASES

### PHASE 1: Document Acquisition (Weeks 1-3)

**Objective:** Obtain all Tier 1 primary documents.

#### Architect Tasks (Manual / Public Records)
1. **File a public records request** with VPS under RCW 42.56 for:
   - F-195 and F-195F reports, fiscal years 2018-2025
   - All contracts, amendments, and addenda with Soliant Health, Maxim Healthcare Staffing, Amergis, and Pioneer Healthcare Services (2018-present)
   - All consent agenda items approving vendor contracts for staffing services (2020-present)
2. **Pull available F-195 data from OSPI website** — much of this is publicly available without a records request. Check the EDS portal first before waiting on the formal request.
3. **Search WA Secretary of State** business entity database for Amergis, Maxim Healthcare Staffing, Soliant Health LLC, Pioneer Healthcare Services.

#### Neo Tasks — Antigravity IDE (Dispatch as Parallel Agents)

**WORKSPACE 1: `VPS-F195-Analysis`**

Prompt for Neo (relay via ChatGPT, or dispatch directly in Antigravity with Gemini 3 Pro):
```
TASK: F-195 Data Extraction and Trend Analysis
ENVIRONMENT: Python with pandas, matplotlib
DATA SOURCE: OSPI Education Data System (eds.ospi.k12.wa.us) — 
Vancouver School District #37

EXTRACT the following for fiscal years 2018-2025:
1. Object 7 (Purchased Services) total expenditures by fund 
   (General Fund, Special Ed Fund, ASB if applicable)
2. Object 2 (Certificated Salaries) total expenditures
3. Object 3 (Classified Salaries) total expenditures
4. Total General Fund expenditures
5. Total General Fund revenue
6. FTE counts (certificated and classified)
7. Enrolled student FTE

OUTPUT FORMAT:
- CSV file: columns = fiscal_year, object_code, fund, amount, fte_count
- Summary table: Object 7 as % of General Fund by year
- Chart 1: Object 7 trend line (2018-2025) with enrollment overlay
- Chart 2: Object 7 % of General Fund vs. Object 2 % of General Fund
- Confidence note: Flag any years where data may be estimated or 
  incomplete

VERIFICATION: After generating outputs, describe your data sources 
and methodology so it can be independently reproduced.
```

**WORKSPACE 2: `VPS-Vendor-Tracking`**

```
TASK: Board Consent Agenda Mining
ENVIRONMENT: Python + browser automation
TARGET: VPS board meeting archives (vansd.org board section, or 
BoardDocs if that's the platform)

SEARCH all board meeting agendas and minutes from January 2020 
through December 2025 for any mention of:
- Soliant Health (or Soliant)
- Maxim Healthcare (or Maxim)
- Amergis
- Pioneer Healthcare (or Pioneer)

FOR EACH HIT, EXTRACT:
- Meeting date
- Agenda item number
- Agenda section (Consent Agenda vs. Action Item vs. Discussion)
- Description text
- Dollar amount (if stated)
- Vote outcome (if recorded separately from consent block)
- Whether the item was pulled from consent for individual discussion

OUTPUT:
- CSV spreadsheet of all vendor mentions
- Summary: Total number of vendor approvals by year
- Summary: Total dollar amount approved by vendor by year 
  (where amounts are stated)
- Flag: Any instances where vendor contracts were discussed 
  outside consent agenda
```

**WORKSPACE 3: `VPS-Peer-Comparison`**

```
TASK: Regional Peer District Object 7 Comparison
ENVIRONMENT: Python with pandas, matplotlib
DATA SOURCE: OSPI EDS — same as Workspace 1

EXTRACT Object 7 (Purchased Services) as % of General Fund for 
fiscal years 2018-2025 for:
- Vancouver SD #37
- Evergreen SD #114
- Battle Ground SD #119
- Camas SD #117

ALSO EXTRACT for each district:
- Total enrollment (FTE)
- Special Education enrollment (if available via OSPI)
- Object 7 per-pupil spending

OUTPUT:
- Comparative chart: Object 7 % of General Fund, all four districts
- Table: Object 7 per-pupil by district by year
- Analysis note: Is VPS an outlier? By what magnitude?
- Caveat: Note any differences in district size, SpEd population, 
  or reporting methodology that could explain divergence
```

#### Perplexity Tasks (Architect executes directly)

```
Search 1: "Amergis" OR "Maxim Healthcare Staffing" Washington State 
Secretary of State business entity filing

Search 2: "Maxim Healthcare" Medicaid fraud settlement 2011 
officers directors

Search 3: OSPI Safety Net reimbursement data Washington school 
districts public records

Search 4: Vancouver Public Schools F-195 budget report OSPI 
download site
```

#### AI Studio Task (Architect executes — Prompt Lab)

Before dispatching the Neo prompts above, test them in AI Studio with Gemini 3 Pro to verify:
- The OSPI EDS data structure matches what the prompts expect
- The search terms for board minutes will capture all relevant vendor mentions
- The F-195 object code structure is correct (Object 7 = Purchased Services)

This 10-minute validation step prevents wasting hours on prompts that target the wrong data format.

#### NotebookLM Task

Upload all three research documents (Contractor Spending, Budget Shortfall, Budget Deep Dive) plus the VEA CBA to a dedicated NotebookLM notebook. This becomes the investigation's persistent memory — queryable across sessions without re-uploading or re-explaining context.

#### Chief Checkpoint (End of Phase 1)
- Do we have actual Object 7 dollar figures? If no, the investigation pauses until we do.
- Have records requests been filed? What's the estimated response timeline?
- Has Neo's OSPI extraction been verified against at least one known data point from our research documents?
- Have Antigravity agents produced Artifacts (task lists, data outputs) that Architect has reviewed and approved?

---

### PHASE 2: Forensic Data Analysis (Weeks 3-5)

**Objective:** Transform raw financial data into the evidentiary backbone of the story.

#### Neo Tasks — Antigravity IDE `VPS-Premium-Calculation` Workspace

This is the critical workspace. The "Lost Efficiency" number lives here.

```
TASK: Vendor Premium and Lost Efficiency Calculation
ENVIRONMENT: Python with pandas, numpy
DATA SOURCES: 
- VEA CBA salary schedules (uploaded)
- SEBB employer contribution rates (from OSPI/HCA)
- DRS pension contribution rates (from DRS website)
- Vendor bill rates (from MSA if obtained, or from Amergis/Soliant 
  public job postings as proxy — CLEARLY LABEL if estimated)

STEP 1: INTERNAL COST MODEL
For each of these roles, calculate the fully-loaded annual cost 
of a direct-hire employee:
  a. Registered Nurse (RN) — Step 5 on classified salary schedule
  b. Speech-Language Pathologist (SLP) — MA+0, Step 5 on cert schedule
  c. Paraeducator/1:1 Health Aide — Step 5 on classified schedule

Fully-loaded cost = Base salary + SEBB employer contribution 
(monthly rate × 12) + DRS employer contribution (% of salary) + 
FICA/Medicare (7.65%) + L&I (estimated %) + unemployment insurance

Express as: annual cost AND hourly equivalent (based on contracted 
hours/year for each role)

STEP 2: VENDOR COST MODEL
For each role, identify the agency bill rate:
  a. If MSA is available: use contracted rates
  b. If MSA is NOT available: use Amergis/Soliant job posting rates 
     for SW Washington as proxy — MUST LABEL AS "ESTIMATED FROM 
     PUBLIC POSTINGS" with date of posting and URL
  c. Express as: hourly bill rate AND estimated annual cost 
     (based on same hours/year as internal model)

STEP 3: THE PREMIUM
For each role: Premium = (Vendor Annual Cost - Internal Annual Cost)
Premium % = Premium / Internal Annual Cost × 100

STEP 4: THE LOST EFFICIENCY NUMBER
Using total vendor payments from Phase 1 data:
  "For every $1M paid to Amergis, the district could have hired 
   [X] FTE [role] internally"
  
  Total 2024 vendor spend on staffing (if known) ÷ Internal 
  annual cost per FTE = Number of FTEs "lost" to the premium

STEP 5: SENSITIVITY ANALYSIS
Because bill rates may be estimated, run the calculation at three 
levels:
  - Conservative: Lowest plausible bill rate
  - Midpoint: Best estimate
  - High: Highest plausible bill rate

OUTPUT:
- Table: Side-by-side internal vs. vendor cost by role
- The Lost Efficiency number (with confidence range)
- Methodology statement suitable for publication 
  (transparent about estimates and assumptions)
- All source data with URLs and access dates

CRITICAL: Flag EVERY assumption. If a number is estimated rather 
than documented, say so explicitly. We publish what we can prove, 
not what we can calculate from guesses.
```

#### Verification Protocol (MANDATORY)

Once Neo produces the Lost Efficiency calculation:

1. **Architect:** Open AI Studio. Paste the same data inputs and methodology into Gemini 3 Pro. Ask it to independently calculate the same figures. Compare outputs.

2. **Architect:** In Antigravity, switch the `VPS-Premium-Calculation` workspace model from Gemini 3 Pro to Claude Sonnet 4.5. Ask it to review Neo's methodology and identify any errors or unsupported assumptions.

3. **Architect:** Manually verify one role's calculation by hand (e.g., RN salary from CBA + SEBB rate from HCA website + DRS rate from DRS website). Does your manual math match what the AI produced?

4. **I (Chief)** will review the complete calculation package — methodology, assumptions, data sources, and outputs — before any number is approved for use in the narrative.

**If all four checks agree:** The number is approved for Woodward's draft.
**If any check diverges:** We investigate the discrepancy before proceeding.

#### Antigravity `VPS-Visualization` Workspace

```
TASK: Publication-Ready Data Visualization
ENVIRONMENT: Python with matplotlib, seaborn

Using verified data from all prior workspaces, generate:

CHART 1: "The Divergence"
- Dual-axis line chart
- Left axis: Object 7 (Purchased Services) spending in dollars
- Right axis: Student enrollment (FTE)
- X-axis: Fiscal years 2018-2025
- Annotation: Mark ESSER period, $35M cuts, key policy changes

CHART 2: "The Inelasticity"
- Grouped bar chart
- Y-axis: % change from prior year
- Bars: Object 2 (Salaries) change vs. Object 7 (Purchased Services) change
- Focus: 2024-25 austerity year — if salaries dropped but 
  Object 7 didn't, this is the visual proof

CHART 3: "The Outlier" (if data supports it)
- Line chart comparing Object 7 as % of General Fund
- Lines: VPS vs. Evergreen vs. Battle Ground vs. Camas
- This chart only gets made if VPS is demonstrably an outlier

CHART 4: "The Premium"
- Stacked bar chart
- For each role (RN, SLP, Para): 
  Internal cost (blue) + Vendor premium (red) = Total vendor cost
- Include FTE equivalency annotation

STYLE: Clean, grayscale-friendly (must reproduce in newsprint). 
No chartjunk. Source citations on each chart.
Minimum font size 10pt. Export as both PNG (300dpi) and SVG.
```

#### Chief Checkpoint (End of Phase 2)
- Can we quantify the vendor premium with defensible numbers?
- Does the peer comparison show VPS is an outlier, or is this a regional pattern?
- Have all outputs passed the four-step Verification Protocol?
- Are the visualizations clear, accurate, and publication-ready?
- **CRITICAL:** Have we distinguished between documented facts and estimated figures throughout? Every chart and table must indicate which numbers are sourced from primary documents and which are modeled.

---

### PHASE 3: Narrative Architecture (Weeks 5-6)

**Objective:** Construct the story framework based on confirmed evidence.

**Woodward Tasks (relay via ChatGPT 5.2):**

```
Woodward: Based on the verified evidence package from Phase 2, 
construct the narrative architecture for the investigation. 

STORY STRUCTURE: "Follow the Money" (forensic, not emotional)

I. THE LEAD (Anecdotal or Data-Driven — your call, but sourced)
   Option A: Open with a specific board meeting where a $[X] vendor 
   contract was approved on consent agenda in under 60 seconds — same 
   meeting where teacher cuts were discussed for hours.
   Option B: Open with the Lost Efficiency number.

II. THE NUT GRAPH
   State the thesis in 2-3 sentences. This is NOT a story about a 
   budget deficit. It IS a story about how a school district's fiscal 
   crisis coexists with — and is partly driven by — millions in 
   uncapped payments to private staffing corporations whose costs are 
   structurally shielded from the austerity measures imposed on 
   classroom positions.

III. THE MECHANISM (How It Works)
   - The McCleary/SEBB regulatory squeeze (3 paragraphs max)
   - The "Agency Trap" cycle (burnout → vacancy → vendor → premium → 
     less money for retention → more burnout)
   - The consent agenda opacity

IV. THE NUMBERS (The Core)
   - Object 7 trajectory with enrollment overlay
   - Vendor-specific payment totals
   - The premium calculation / Lost Efficiency figure
   - Peer comparison (if VPS is an outlier)

V. THE DEFENSE (Fair Treatment)
   - IDEA mandates are real and non-negotiable
   - Labor shortages are real and regional
   - The district did not create McCleary or SEBB
   - Include district's response (once obtained)

VI. THE SYSTEMIC QUESTION
   - VPS problem or statewide structural problem?
   - What are other districts doing differently (if anything)?
   - What would a solution look like?

VII. THE CLOSE
   Return to the opening image/number.

TONE: Clinical, forensic, precise. Accountability story, not a 
hit piece. The villain is a SYSTEM, not a person.
Use "Structural Privatization" as the framing concept.
Do NOT use "Shadow Payroll" — implies intentional concealment 
we have not proven.

LANGUAGE RULES:
- "Records show" for documented facts
- "Analysis indicates" for our calculations
- "The district has stated" for their public positions
- "It remains unclear" for genuine gaps
- NEVER: "reportedly," "it is believed," "sources say" without 
  specificity

Deliver: 2,000-word draft with [BRACKETS] where specific 
numbers/evidence from Neo's verified analysis will be inserted.
```

**Review workflow:** Woodward's draft goes through NotebookLM first (check claims against source documents in the notebook), then to me (Chief) for the full five-phase editorial review.

#### Chief Checkpoint (End of Phase 3)

I will apply the full editorial review protocol to Woodward's draft:

**PHASE A — Evidentiary Audit:** Every bracketed claim traced to primary source. Every number verified against the Phase 2 outputs.

**PHASE B — Logic Check:** Map the causal chain. Identify inferential leaps. Test alternative explanations. Note where correlation is presented as causation.

**PHASE C — Language Calibration:** Compare assertion strength to evidence strength. Identify legally hazardous formulations. Suggest precise alternatives. Flag opinion presented as fact.

**PHASE D — Adversarial Review:** Articulate the strongest defense VPS could mount. Identify weakest narrative points. Anticipate PR counter-narratives. Recommend preemptive strengthening.

**PHASE E — Ethical Assessment:** Evaluate harm/benefit balance. Confirm right of reply compliance. Assess proportionality. Consider unintended consequences.

**PHASE F — Publication Recommendation:** GREEN / YELLOW / RED / HOLD

---

### PHASE 4: Adversarial Stress Test (Week 6)

**Objective:** Red-team the entire investigation before any external exposure.

**I (Chief) will produce: "The Devil's Advocate Brief"**

This document will articulate the strongest possible defense VPS could mount:

1. **"We had no choice"** — IDEA mandates are absolute; the district cannot legally deny services. Agency contracts exist because the labor market failed, not because the district failed.

2. **"Everyone does this"** — Peer districts use the same vendors. This is a statewide structural problem, not a VPS governance failure.

3. **"The numbers are misleading"** — Object 7 includes many categories beyond staffing agencies (utilities, contracted maintenance, technology services). Attributing the entire Object 7 increase to vendor staffing is analytically dishonest.

4. **"The consent agenda is standard practice"** — Every school board in Washington uses consent agendas. Singling out VPS is unfair.

5. **"The comparison is apples to oranges"** — VPS has a uniquely high-needs SpEd population that makes peer comparisons misleading.

**For each defense, I will assess:**
- Is it factually accurate? (If yes, we must acknowledge it.)
- Does it undermine our thesis? (If yes, we strengthen evidence or narrow claims.)
- Can we preemptively address it? (If yes, Woodward incorporates it.)

**Defense #3 is the most dangerous.** If we cannot disaggregate Object 7 into "staffing agency payments" vs. "other purchased services," our entire thesis rests on a category too broad to be conclusive. The MSA and vendor-specific payment data from board minutes are what solve this. If we don't have them by this phase, we have a problem.

---

### PHASE 5: Right of Reply (Weeks 7-8)

**Objective:** Fulfill ethical and legal obligations before publication.

**CRITICAL REQUIREMENT:** No story is published without right of reply. Period.

**Contacts Required:**
1. **VPS Communications Office** — Formal written questions with specific allegations and data points. Minimum 5 business days for response.
2. **Superintendent Jeff Snell** (or designee) — Same questions, routed through comms.
3. **VPS Board Chair** — Governance questions about consent agenda practices.
4. **Amergis Media Relations** — Questions about rate structures, WA school district contracts.
5. **OSPI** — Questions about Safety Net reimbursement patterns for VPS.

**The questions must be specific.** Not "Do you spend too much on vendors?" but:

*"Records indicate that VPS paid [specific amount] to Amergis/Maxim in fiscal year 2024 while simultaneously eliminating [number] classroom positions. Can you explain the district's rationale for maintaining these vendor expenditure levels during a period of significant budget reductions?"*

**SOURCE PROTECTION NOTE:** These questions will signal that someone is investigating. They must be crafted so they could plausibly come from a journalist, legislator, or community activist — not someone with insider operational knowledge. **Draft all right-of-reply communications in AnythingLLM (local), not in any cloud tool.** This is where your anonymity is most at risk. We should discuss the mechanism of delivery carefully before this phase begins.

---

### PHASE 6: Final Editorial Review (Week 8)

**I (Chief) will conduct the full publication review.**

GREEN/YELLOW/RED/HOLD assessment on:
- Every factual claim verified against primary source
- Language calibrated to evidence strength throughout
- District response fairly incorporated
- Legal exposure assessed (defamation, tortious interference)
- Source protection confirmed — no detail that could identify Architect
- Proportionality confirmed — public interest justifies the investigation
- All charts and data verified through Cross-Verification Protocol
- Methodology statement included and transparent

---

### PHASE 7: Publication Strategy (Weeks 9-10)

**Objective:** Get the story into public discourse while maintaining anonymity.

**Publication Channels (ranked by impact and safety):**

| Channel | Reach | Anonymity Risk | Mechanism |
|---------|-------|---------------|-----------|
| Tip to Columbian reporter | **HIGH** — local paper of record | **LOW** — standard journalist-source relationship | Encrypted contact; provide evidence package |
| Tip to KATU investigative team | **HIGH** — they've covered VPS budget already | **LOW** — same as above | Same |
| Letter to WA State Legislature (Education Committee) | **MEDIUM-HIGH** — triggers official inquiry | **MODERATE** — may generate records of submission | Via constituent channels; no personal identifiers |
| Submission to Clark County Today (opinion/analysis) | **MEDIUM** — engaged local audience | **MODERATE** — they've published Larry Roe's letters | Anonymous submission with evidence |
| OPB / NW Labor Press | **MEDIUM** — regional reach | **LOW** — both have covered this beat | Standard tip line |

**Recommended Primary Strategy:** Prepare a comprehensive evidence package (data, verified analysis, key documents, publication-ready charts, pre-written questions for the district) and deliver it to an established investigative reporter at The Columbian or KATU. Let a professional journalist carry the story. This maximizes both impact and your protection.

**The Evidence Package Should Include:**
- Executive summary (1 page) of findings
- All verified data tables and charts (with methodology notes)
- Copies of primary source documents (F-195s, board minutes, SAO audits)
- Pre-drafted questions for VPS administration
- A note on what the reporter can independently verify and how
- NO references to your identity, position, or insider access

---

## PART 4: OPERATIONAL SECURITY REMINDERS

1. **Never access VPS internal systems for investigation purposes.** All evidence must come from public records, public meetings, or publicly available databases.
2. **Never discuss the investigation on district networks, devices, or email.**
3. **AI conversations are not privileged.** Assume all cloud-based chat logs could theoretically be discoverable. Never include information that could only be known by someone in your specific position in any cloud tool.
4. **The investigation must be provable by any competent journalist starting from public sources.** If our evidence chain requires insider access at any point, that point must be removed or replaced.
5. **Washington is a two-party consent state for recording.** Do not record conversations without consent.
6. **Use AnythingLLM (local) for all sensitive operational planning.** Source protection analysis, identity-risk assessment, right-of-reply drafting, and any work that references your position within VPS — all local, never cloud.
7. **GitHub repository must be PRIVATE.** Never push investigation files to a public repo. Consider whether you even need GitHub for this — if it's just you, local version control (git without remote) may be safer.
8. **Antigravity workspace names should be generic** if you're concerned about Google-side logging. Use project codes instead of "VPS-Vendor-Tracking" if that's a concern for you.

---

## PART 5: IMMEDIATE NEXT ACTIONS

### This Week (Priority Order)

| # | Action | Owner | Tool | Deliverable |
|---|--------|-------|------|-------------|
| 1 | Pull available F-195 data from OSPI website for VPS (2018-2025) | Architect | Browser + Perplexity (to find direct download links) | Raw data files saved locally |
| 2 | File public records request for vendor contracts (MSAs, addenda) | Architect | Manual (email/web form to VPS) | Request confirmation with tracking number |
| 3 | Set up Antigravity workspaces (5 workspaces per structure above) | Architect | Antigravity IDE | Configured workspaces ready for agent dispatch |
| 4 | Upload research docs to NotebookLM notebook | Architect | NotebookLM Pro | Investigation memory system active |
| 5 | Test Neo prompts in AI Studio before dispatching | Architect | AI Studio (Gemini 3 Pro) | Validated prompt structures |
| 6 | Search WA SOS database for Amergis corporate filings | Architect | Perplexity Pro | Officers list, filing dates, registered agent |
| 7 | Dispatch Antigravity agents for Workspaces 1-3 simultaneously | Architect | Antigravity IDE (Manager view) | F-195 extraction, board agenda mining, and peer comparison running in parallel |
| 8 | Extract VEA CBA salary schedules for comparison calculation | Architect | Download from VEA link in research docs | Salary data by role and step |

### Before Any Writing Begins

Neo must deliver (verified through Cross-Verification Protocol):
- [ ] Object 7 annual totals (2018-2025) with source documents
- [ ] Vendor-specific payment totals (even if partial/estimated with stated methodology)
- [ ] Internal cost calculation based on actual CBA rates + SEBB + DRS
- [ ] The Lost Efficiency number (with sensitivity range and methodology statement)
- [ ] At least one peer district comparison on Object 7 as % of general fund

Without these five deliverables — verified across multiple models — Woodward does not start drafting. Narrative without numbers is opinion journalism. We're doing accountability journalism.

---

## PART 6: A NOTE ON THE BRIEFING YOU RECEIVED

The tactical briefing you shared is energetic and strategically sound in its instincts. But I have three editorial concerns with it:

**1. "Shadow Payroll" is inflammatory and unsupported.** The term implies deliberate concealment. What we have evidence of is *structural opacity* — vendor costs buried in Object 7 and approved through consent agendas. That's a governance design problem, not necessarily an intentional coverup. We use "Structural Privatization" until evidence supports a stronger characterization.

**2. "Financial heist" framing is premature.** A heist requires intent. What we can prove is a *systemic pattern* where regulatory constraints, labor market failures, and governance habits produced an outcome that disadvantages students and taxpayers. That's powerful enough without implying criminality we can't demonstrate.

**3. The Maxim/Amergis officer overlap question is interesting but potentially a dead end.** Even if the same officers ran both entities, a corporate rebrand is legal and common. The 2011 Medicaid fraud settlement is a matter of public record and worth noting as context, but connecting it to VPS's current contracts requires evidence that VPS *knew* about the settlement and contracted with Amergis *despite* it — or that the fraud pattern is repeating. Without that link, it's guilt by association. Pursue it, but don't build the story on it.

---

## CHIEF'S FINAL WORD

Christopher, you have the makings of a significant public interest investigation. The regulatory analysis in your research documents is genuinely excellent — it explains the *mechanism* of structural privatization better than most professional journalism I've seen on this topic. The causal chain from McCleary through SEBB to the Agency Trap is logical, well-sourced, and compelling.

What separates a strong hypothesis from a publishable story is primary documentation. The next three weeks should be spent on nothing but document acquisition and data extraction. Resist the urge to write. Resist the urge to frame. Get the numbers first. The story will write itself once we have them.

The toolkit upgrade changes the *speed* of this work, not the *sequence*. Antigravity lets you run five analysis tracks in parallel instead of one at a time. AI Studio lets you validate prompts before burning compute. The Cross-Verification Protocol ensures no single AI's confident hallucination becomes our published fact. But the fundamental constraint remains: we need primary documents. No tool, however powerful, can analyze data we don't yet possess.

Week 1 priorities: OSPI data pull, records request filed, Antigravity workspaces configured, NotebookLM loaded. Everything else follows from those.

We're operational. Let's get to work.

— Chief

---
*Document prepared by Chief (Investigative Editor) for Architect*  
*Operation Accountability | Version 2.0 | February 6, 2026*  
*Status: RED → Investigation Phase Active*  
*Next checkpoint: End of Phase 1 (Week 3)*
