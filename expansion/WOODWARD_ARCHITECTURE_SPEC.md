# WOODWARD: Investigative Intelligence Platform
## Architecture Specification v1.0

*Designed to mirror Cicero's Council-of-Models, BrainBase, multi-database, and skills architecture for investigative journalism.*

---

## 1. System Overview

**Woodward** is a local-first investigative journalism AI platform built for the VPS investigation and extensible to future investigations. It coordinates multiple LLM agents (an "Editorial Board"), retrieves from specialized databases containing payment records, public documents, and investigation state, and produces verified investigative outputs with source citation.

- **Language**: Python 3.11+ (matching Cicero)
- **Framework**: FastAPI (API), asyncio throughout
- **Project root**: `/Volumes/WD_BLACK/Desk2/Projects/Woodward`
- **Key dependencies**: `neo4j>=5.15`, `openai>=1.0.0`, `google-generativeai`, `anthropic`, `lancedb`, `fastapi`, `uvicorn`, `pydantic>=2.0`, `pydantic-settings>=2.0`, `sqlite3`, `pandas`
- **Shared infra**: `knight-lib` (Neo4j adapter + embeddings client, same as Cicero)

---

## 2. Directory Structure

```
Woodward/
├── woodward.py                     # Entry point
├── Woodward.command                # Bash launcher (matches Cicero pattern)
├── investigation_config.json       # Active investigation metadata
├── requirements.txt
├── pytest.ini
├── .env                            # API keys, DB URIs
├── README.md
├── MANUAL.md                       # Architecture manual
├── CONTEXT_HANDOFF.md              # Inter-session state (Cicero pattern)
│
├── src/
│   ├── main.py                     # InvestigationSystem — top-level orchestrator
│   ├── cli.py                      # CLI interface
│   │
│   ├── core/
│   │   ├── config.py               # AppConfig (env vars, DB connections, model roles)
│   │   ├── constants.py            # Investigation-specific patterns, evidence tags
│   │   ├── models.py               # LLM model registry
│   │   ├── types.py                # RetrievalResult, SourceType, EvidenceGrade
│   │   └── settings.py             # Database cluster settings
│   │
│   ├── agents/
│   │   ├── base.py                 # AsyncLLMClient (OpenAI + Gemini + Anthropic)
│   │   ├── brainbase.py            # BrainBaseLoader (external system prompts)
│   │   ├── editorial_board.py      # EditorialBoard — multi-agent pipeline
│   │   ├── source_verifier.py      # Agent-level: orchestrates figure/claim verification across all databases
│   │   └── validators/
│   │       ├── redaction_scanner.py # Agent-level: invokes utils/redaction.py pattern library
│   │       ├── evidence_grader.py  # [PROOF]/[STRONG INFERENCE]/[SUSPICION] grading
│   │       └── defamation_check.py # Language calibration for legal risk
│   │
│   ├── orchestration/
│   │   ├── router.py               # QueryRouter (task classification)
│   │   ├── coordinator.py          # RetrievalCoordinator (parallel search, fusion)
│   │   ├── context.py              # ContextBuilder (token-budgeted assembly)
│   │   └── pipeline.py             # Pipeline definitions (YAML-driven)
│   │
│   ├── adapters/
│   │   ├── base.py                 # Abstract BaseAdapter
│   │   ├── neo4j.py                # Neo4jAdapter (reuse knight-lib)
│   │   ├── lancedb.py              # LanceDBAdapter (document vectors)
│   │   └── sqlite.py               # SQLiteAdapter (payment database)
│   │
│   ├── services/
│   │   ├── drafting.py             # DraftingService (article generation pipeline)
│   │   ├── embedding.py            # EmbeddingService
│   │   ├── ingestion.py            # Document ingestion (PDFs, CSVs, BoardDocs)
│   │   └── records.py              # PublicRecordsService (PRR tracking, templates)
│   │
│   ├── skills/
│   │   └── vps_investigation/
│   │       ├── drafter/
│   │       │   └── article_drafter.py     # Multi-stage article drafting
│   │       ├── analysis/
│   │       │   ├── payment_analyzer.py    # Vendor payment analysis
│   │       │   ├── cost_modeler.py        # Internal vs. vendor cost comparison
│   │       │   ├── budget_analyzer.py     # F-195 Object 7 analysis
│   │       │   ├── personnel_analyzer.py  # S-275 workforce analysis
│   │       │   └── peer_comparator.py     # Cross-district comparison
│   │       ├── governance/
│   │       │   ├── contract_analyzer.py   # MSA clause analysis
│   │       │   ├── board_action_tracker.py # Consent agenda vs action item tracking
│   │       │   └── policy_tracker.py      # Board Policy 6220 revision tracking
│   │       ├── compliance/
│   │       │   ├── idea_checker.py        # IDEA/IEP compliance analysis
│   │       │   ├── restraint_tracker.py   # Restraint data analysis
│   │       │   └── ospi_complaint.py      # SECC complaint analysis
│   │       └── validators/
│   │           ├── figure_verifier.py     # Cross-check figures against source docs
│   │           └── source_tracer.py       # Trace every claim to primary source
│   │
│   ├── ingest/
│   │   ├── warrant_register_parser.py     # PDF extraction + dedup pipeline
│   │   ├── boarddocs_scraper.py           # BoardDocs agenda/minutes extraction
│   │   ├── ospi_data_loader.py            # F-195, S-275 data loading
│   │   └── document_processor.py          # General document chunking + embedding
│   │
│   ├── assembly/
│   │   ├── article_engine.py              # Markdown article assembly
│   │   ├── evidence_package.py            # Package assembly for journalist handoff
│   │   └── memo_engine.py                 # SAO memo, public records request assembly
│   │
│   ├── api/
│   │   └── server.py                      # FastAPI server
│   │
│   └── utils/
│       ├── metadata.py                    # Source metadata extraction
│       ├── cost_tracker.py                # API cost tracking
│       └── redaction.py                   # Pattern library used by agents/validators/redaction_scanner.py
│
├── tests/
│   ├── agents/                    # Editorial board, source verifier tests
│   ├── acceptance/                # End-to-end pipeline tests
│   ├── integration/               # Retrieval, ingestion tests
│   └── skills/                    # Per-skill unit tests
│
├── scripts/
│   ├── production_run_article.py  # Production article generation
│   ├── verify_figures.py          # Canonical figure verification
│   ├── ingest_warrant_registers.py # Batch warrant register ingestion
│   ├── audit/                     # Data integrity audits
│   ├── diagnostics/               # System diagnostics
│   └── db/                        # Database utilities
│
├── investigations/
│   └── vps_2026/                  # Active investigation
│       ├── investigation_config.json
│       ├── articles/              # Final article outputs
│       ├── evidence_package/      # Journalist handoff package
│       ├── correspondence/        # Right-of-reply, agency responses
│       └── source_documents/      # Raw PDFs, contracts, OSPI data
│
├── docs/
│   ├── schema/                    # Database schema docs
│   ├── architecture/              # System architecture docs
│   └── methodology/               # Investigation methodology docs
│
├── drafts/                        # Draft outputs, test results
└── ui/                            # Simple HTML frontend (VS Code webview)
```

---

## 3. The Database Layer (Mirroring Cicero's Four Pillars)

### 3a. evidencedb (Neo4j — "The Ledger")
- **Purpose**: Financial evidence. Payment records, vendor relationships, budget data, contract terms, and board governance actions authorizing vendor spending.
- **Architecture pattern from**: Cicero's legaldb (authoritative source of truth pattern). Schema is entirely new.
- **Node types**: `Payment`, `Vendor`, `FiscalYear`, `Contract`, `ContractClause`, `BudgetLine`, `WarrantRegister`, `BoardAction`
- **Key relationships**: `[:PAID_TO]`, `[:IN_FISCAL_YEAR]`, `[:GOVERNED_BY]`, `[:CONTAINS_CLAUSE]`, `[:SOURCED_FROM]`, `[:APPROVED_VIA]`, `[:REFERENCES]`
- **Vector indexes**: `payment_embedding`, `clause_embedding`
- **Why Neo4j**: The vendor-to-payment-to-contract-to-fiscal-year graph is inherently relational. Graph queries like "show all payments to entities related to Maxim across all fiscal years including rebrand" are natural Cypher.

### 3b. casedb (Neo4j — "The Record")
- **Purpose**: Investigation-specific documents. Articles, dossiers, correspondence, timeline events, people and organizations.
- **Architecture pattern from**: Cicero's casedb (case record pattern). Schema is entirely new.
- **Node types**: `Article`, `Dossier`, `Person`, `Organization`, `TimelineEvent`, `Correspondence`, `Claim`
- **Key relationships**: `[:AUTHORED_BY]`, `[:REFERENCES]`, `[:OCCURRED_ON]`, `[:SUPPORTS_CLAIM]`, `[:CONTRADICTS]`
- **Vector indexes**: `article_chunk_embedding`, `claim_embedding`

### 3c. skillsdb (Neo4j — "The Strategist")
- **Purpose**: Investigation skills, strategy modules, methodology. The "how to investigate" knowledge.
- **Architecture pattern from**: Cicero's strategydb (skills pattern). Content is entirely new.
- **Node types**: `Skill`, `Module`, `Submodule`, `Methodology`, `RegulatoryFramework`
- **Key relationships**: `[:HAS_SKILL]`, `[:USES]`, `[:CONTAINS]`
- **Vector indexes**: `skill_embedding`
- **Content**: RCW 42.56 procedures, OSPI oversight framework, SAO audit methodology, defamation law framework, fair report privilege, IDEA compliance requirements, Washington procurement law

### 3d. trackingdb (Neo4j — "The Watch")
- **Purpose**: Operational tracking. Right-of-reply status, journalist contacts, records request status, deadlines, agency responses.
- **Architecture pattern from**: Cicero's sentineldb (tracking pattern). Schema is entirely new.
- **Node types**: `Contact`, `Correspondence`, `Deadline`, `RecordsRequest`, `AgencyResponse`, `StatusUpdate`
- **Key relationships**: `[:SENT_TO]`, `[:RESPONDED_WITH]`, `[:DUE_BY]`, `[:FILED_WITH]`

### 3e. LanceDB (Local vector store — "The Archive")
- **Purpose**: Full-text semantic search across all source documents. The 153 warrant register PDFs, OSPI reports, OPB/InvestigateWest articles, Columbian coverage.
- **Architecture pattern from**: Cicero's LanceDB (vector store pattern). Content is entirely new.
- **Embedding**: OpenAI text-embedding-3-small (1536d) as default. Evaluate alternatives after testing. See ISOLATION_BOUNDARIES.md for guidance on embedding model selection.

### 3f. paymentsdb (SQLite — "The Receipts")
- **Purpose**: The existing warrant register payment database. 25,578 deduplicated records. This is the canonical source of truth for all dollar figures.
- **Architecture pattern from**: Cicero's OPCrawler (structured data workhorse pattern). This database already exists.
- **Tables**: `payments` (date, payee, amount, warrant_number, fiscal_year), `vendors` (normalized names, aliases), `dedup_audit` (duplicate tracking)
- **Note**: This database already exists from the investigation. Woodward wraps it, doesn't rebuild it.

---

## 4. The Editorial Board (Mirroring Cicero's Council)

### 4a. Agent Roles

| Agent Role | Purpose | Default Model | Brain Module |
|-----------|---------|---------------|-------------|
| **Data Analyst** | Structured reasoning about numbers, cost models, budget analysis. Queries paymentsdb and evidencedb. Never writes prose. | gemini-2.5-pro (1M context) | Module1_DataScience |
| **Investigator** | Facts, sources, timeline, record citations. Traces claims to primary documents. Builds the evidentiary backbone. | gpt-4o | Module2_Investigation |
| **Writer** | Narrative prose, journalistic style, human voice. Integrates data and evidence into readable stories. No em dashes. | gpt-4o | Module3_Journalism |
| **Verifier** | Cross-checks every claim against source documents. Assigns evidence grades. Catches hallucinations. | gpt-4o | Module1_DataScience |
| **Source Protector** | Scans all outputs for identifying patterns, operational language, role-specific details. Runs before anything leaves the system. The anonymity gate. | gpt-4o-mini (cheap, fast, pattern-matching) | Module3_Journalism/SubB_Source_Protection |
| **Editor** | Final synthesis. Editorial judgment, language calibration, legal risk, proportionality, narrative force. The quality gate. | claude-sonnet-4-6 | Module4_Editorial |
| **Chief** | System coordination. Task routing, pipeline management, context allocation. | gpt-4o | Module5_Operations |
| **OSINT Researcher** | Web search, public records, BoardDocs scraping, OSPI data retrieval, news monitoring. | gemini-2.5-flash (cheap, fast) | Module5_Operations |

### 4b. Editorial Board Pipeline (Mirroring Council Pipeline)

```
User: "Draft a section on the $3M estimate vs $11M actual spending"
    |
    v
[1. Research Phase]
    |-- OSINT Researcher: searches evidencedb + paymentsdb for relevant records
    |-- Data Analyst: pulls canonical figures, computes variance
    |-- Investigator: identifies primary sources (BoardDocs agenda item, warrant registers)
    |
    v
[2. Parallel Drafting]
    |-- Data Analyst: produces verified figure table with source citations
    |-- Investigator: assembles factual narrative backbone with evidence grades
    |-- Writer: drafts prose section with human voice
    |   (all three run concurrently)
    |
    v
[3. Adversarial Critique]
    |-- Data Analyst critiques Writer's numbers
    |-- Investigator critiques Writer's source attributions
    |-- Writer critiques Data Analyst's readability
    |-- Verifier critiques ALL for unsupported claims
    |
    v
[4. Source Verification]
    |-- Every figure checked against paymentsdb
    |-- Every citation checked against evidencedb/casedb
    |-- Evidence grades assigned: [PROOF] / [STRONG INFERENCE] / [SUSPICION] / [UNRESOLVED]
    |
    v
[5. Redaction Scan]
    |-- Source Protector scans for identifying patterns
    |-- Operational language check (codenames, dispatch numbers, team refs)
    |-- Role-specific detail check
    |
    v
[6. Refinement Loop]
    |-- If CRITICAL issues found, re-draft (max 1 retry, matching Cicero)
    |
    v
[7. Editor Synthesis]
    |-- Final unified output
    |-- Language calibration (assertion strength matched to evidence strength)
    |-- Legal risk assessment
    |-- Publication recommendation: GREEN / YELLOW / RED / HOLD
    |
    v
Final Output (Markdown + metadata JSON)
```

---

## 5. BrainBase System Prompts

**Location:** `/Volumes/WD_BLACK/Desk2/Projects/Woodward/BrainBase/` (Woodward has its own BrainBase, separate from Cicero's. Do NOT share Cicero's BrainBase directory.)

### 5a. Module Structure (5 Modules / 15 Brains)

```
BrainBase/
├── BrainCrate/
│   ├── Brains/
│   │   ├── Module1_DataScience/
│   │   │   ├── SubA_Financial_Analysis/
│   │   │   │   └── system_prompt_compact.md     # Payment analysis, cost modeling
│   │   │   ├── SubB_Personnel_Analysis/
│   │   │   │   └── system_prompt_compact.md     # S-275, workforce analysis
│   │   │   └── SubC_Budget_Analysis/
│   │   │       └── system_prompt_compact.md     # F-195, Object 7 analysis
│   │   │
│   │   ├── Module2_Investigation/
│   │   │   ├── SubA_Public_Records/
│   │   │   │   └── system_prompt_compact.md     # RCW 42.56, PRR strategy
│   │   │   ├── SubB_Corporate_Research/
│   │   │   │   └── system_prompt_compact.md     # Vendor history, DOJ, rebrands
│   │   │   └── SubC_Governance/
│   │   │       └── system_prompt_compact.md     # Board actions, procurement, policy
│   │   │
│   │   ├── Module3_Journalism/
│   │   │   ├── SubA_Narrative/
│   │   │   │   └── system_prompt_compact.md     # Investigative narrative writing
│   │   │   ├── SubB_Source_Protection/
│   │   │   │   └── system_prompt_compact.md     # Anonymity, redaction, OPSEC
│   │   │   └── SubC_Right_of_Reply/
│   │   │       └── system_prompt_compact.md     # Fairness, response drafting
│   │   │
│   │   ├── Module4_Editorial/
│   │   │   ├── SubA_Legal_Risk/
│   │   │   │   └── system_prompt_compact.md     # Defamation, fair report, opinion
│   │   │   ├── SubB_Evidence_Calibration/
│   │   │   │   └── system_prompt_compact.md     # Language-to-evidence matching
│   │   │   └── SubC_Adversarial/
│   │   │       └── system_prompt_compact.md     # Red team, district defense sim
│   │   │
│   │   └── Module5_Operations/
│   │       ├── SubA_Orchestration/
│   │       │   └── system_prompt_compact.md     # Task routing, pipeline management
│   │       ├── SubB_OSINT/
│   │       │   └── system_prompt_compact.md     # Web research, BoardDocs, OSPI
│   │       └── SubC_Tracking/
│   │           └── system_prompt_compact.md     # Deadlines, contacts, status
│   │
│   ├── Classified/        # Per-module classified materials
│   ├── Articles/          # Source articles per module
│   ├── Golden/            # Golden examples (exemplar outputs)
│   └── Extracted/         # Extracted knowledge per module
```

### 5b. Standard System Prompt Format (Matching Cicero)

Every brain follows the same structure:

```markdown
## ROLE AND IDENTITY
[Who this agent is, what it does, its editorial personality]

## SCOPE
### IN SCOPE
[What this agent handles]
### OUT OF SCOPE
[What gets routed elsewhere]

## HARD CONSTRAINTS
[Non-negotiable rules: no em dashes, no hallucinated figures, etc.]

## TONE
[Voice guidelines: human, natural, no AI eccentricities]

## QUERY ROUTING
- FINANCIAL QUERY → paymentsdb + evidencedb (Data Analyst)
- SOURCE QUERY → casedb + LanceDB (Investigator)
- NARRATIVE QUERY → casedb context → Writer
- VERIFICATION QUERY → all databases (Verifier)

## AVAILABLE SKILLS
[List of skills this agent can invoke]

## OUTPUT FORMAT
[Expected output structure]
```

### 5c. Example Brain: Module3_Journalism / SubA_Narrative

```markdown
## ROLE AND IDENTITY

You are the Writer. Your job is to turn verified evidence and structured
analysis into investigative journalism that reads like it was written by
a human reporter with 20 years of experience. You write for readers, not
for lawyers and not for academics.

You believe that data appendices do not change institutions. Stories do.

## SCOPE

### IN SCOPE
- Drafting narrative sections from verified data and sourced facts
- Integrating human voices (public testimony, quotes from reporting)
- Structuring investigative narratives with narrative momentum
- Translating complex financial mechanics into plain language

### OUT OF SCOPE
- Generating or verifying numbers (route to Data Analyst)
- Making legal risk judgments (route to Editor)
- Source protection decisions (route to Source Protector)
- Assigning evidence grades (route to Verifier)

## HARD CONSTRAINTS
- NEVER use em dashes or en dashes. Use commas, periods, or restructure.
- NEVER use: genuinely, honestly, straightforward, notably, importantly,
  it is worth noting, delve, tapestry, landscape, nuanced, multifaceted
- NEVER fabricate quotes. Use only quotes sourced from published reporting.
- NEVER state a figure without receiving it from the Data Analyst pipeline.
- NEVER use bullet points in narrative prose.
- EVERY person mentioned must be identified by their actual title and role.
- Write in active voice. Short sentences. Concrete details.

## TONE
Human. Direct. Controlled anger beneath professional calm. The writing
should make the reader feel something without telling them what to feel.
Let the facts carry the weight.

## QUERY ROUTING
- Need a number? → Data Analyst
- Need a source citation? → Investigator
- Need a legal check? → Editor
- Need a comparison? → Data Analyst (peer_comparator skill)

## AVAILABLE SKILLS
- article_drafter.draft_section(topic, evidence, voice_notes)
- article_drafter.integrate_testimony(quote_source, context)
- article_drafter.write_transition(from_section, to_section)

## OUTPUT FORMAT
Markdown prose. No headers within a section. Natural paragraph flow.
Tables only when data density demands them. Source attributions woven
into the text, not footnoted.
```

---

## 6. Skills (Built From Scratch for Investigation Domain)

### 6a. Investigation Skills (`src/skills/vps_investigation/`)

| Skill | File | Purpose |
|-------|------|---------|
| **ArticleDrafter** | `drafter/article_drafter.py` | Multi-stage article drafting (Research > Outline > Draft > Refine > Assemble) |
| **PaymentAnalyzer** | `analysis/payment_analyzer.py` | Vendor payment trajectory, year-over-year growth, concentration analysis |
| **CostModeler** | `analysis/cost_modeler.py` | Internal fully-loaded cost vs. vendor bill rate comparison |
| **BudgetAnalyzer** | `analysis/budget_analyzer.py` | F-195 Object 7 analysis, budgeted vs. actual variance |
| **PersonnelAnalyzer** | `analysis/personnel_analyzer.py` | S-275 FTE analysis, salary tier composition, attrition patterns |
| **PeerComparator** | `analysis/peer_comparator.py` | Cross-district Object 7 comparison (VPS vs. Evergreen, etc.) |
| **ContractAnalyzer** | `governance/contract_analyzer.py` | MSA clause extraction and analysis (auto-renewal, rate caps, conversion fees) |
| **BoardActionTracker** | `governance/board_action_tracker.py` | Consent agenda vs. action item tracking, vendor authorization history |
| **PolicyTracker** | `governance/policy_tracker.py` | Board Policy 6220 revision tracking and analysis |
| **IDEAChecker** | `compliance/idea_checker.py` | IDEA non-delegable duty analysis, IEP service delivery assessment |
| **RestraintTracker** | `compliance/restraint_tracker.py` | Restraint data tracking, post-ban violation analysis |
| **OSPIComplaintAnalyzer** | `compliance/ospi_complaint.py` | SECC complaint analysis, service-minute delivery assessment |
| **FigureVerifier** | `validators/figure_verifier.py` | Cross-check every figure against paymentsdb/OSPI source |
| **SourceTracer** | `validators/source_tracer.py` | Trace every claim to its primary source document |
| **RedactionScanner** | `validators/redaction_scanner.py` | Source protection: scan for identifying patterns |
| **EvidenceGrader** | `validators/evidence_grader.py` | Assign [PROOF]/[STRONG INFERENCE]/[SUSPICION]/[UNRESOLVED] |
| **DefamationChecker** | `validators/defamation_check.py` | Flag legally hazardous formulations |

**NOTE:** All skills are built from scratch. No skills are ported from Cicero. See `WOODWARD_ISOLATION_BOUNDARIES.md` for the full contamination prevention checklist.

### 6b. Skill Invocation Pattern (Matching Cicero's BrainBase skill declarations)

Each submodule prompt declares its available skills:

```markdown
## AVAILABLE SKILLS
- `payment_analyzer.trajectory(vendor, start_fy, end_fy)` — Payment growth curve
- `payment_analyzer.concentration(fiscal_year)` — Vendor market share
- `cost_modeler.compare(role, vendor_rate, schedule_step)` — Internal vs. vendor cost
- `cost_modeler.lost_efficiency(total_spend, avg_rate, avg_internal)` — Premium calculation
- `budget_analyzer.object7_variance(fiscal_year)` — Budgeted vs. actual
- `budget_analyzer.object7_share(fiscal_year)` — Staffing share of Object 7
```

Skills are implemented as Python classes with typed inputs/outputs:

```python
class PaymentAnalyzer:
    def __init__(self, sqlite_adapter: SQLiteAdapter, neo4j_adapter: Neo4jAdapter):
        self.payments_db = sqlite_adapter
        self.evidence_db = neo4j_adapter

    async def trajectory(
        self, vendor: str, start_fy: str, end_fy: str
    ) -> PaymentTrajectory:
        """Compute payment trajectory for a vendor across fiscal years."""
        query = """
            SELECT fiscal_year, SUM(amount) as total
            FROM payments
            WHERE payee_normalized LIKE ?
            AND fiscal_year BETWEEN ? AND ?
            GROUP BY fiscal_year
            ORDER BY fiscal_year
        """
        results = self.payments_db.execute(query, [f"%{vendor}%", start_fy, end_fy])
        return PaymentTrajectory(
            vendor=vendor,
            data=results,
            growth_rate=self._compute_growth(results),
            source="paymentsdb: 25,578 deduplicated warrant register records"
        )
```

---

## 7. Orchestration (Mirroring Cicero's Router + Coordinator + ContextBuilder)

### 7a. Query Router (`src/orchestration/router.py`)

Two-tier classification (matching Cicero):

```python
class QueryRouter:
    """Classify incoming requests to the appropriate pipeline."""

    TASK_TYPES = {
        "financial_analysis": ["payment", "cost", "budget", "vendor", "Object 7", "premium"],
        "source_verification": ["verify", "check", "confirm", "source", "cite"],
        "narrative_drafting": ["write", "draft", "rewrite", "article", "section"],
        "adversarial_review": ["review", "critique", "red team", "defense", "weakness"],
        "records_research": ["BoardDocs", "OSPI", "public record", "PRR", "warrant register"],
        "tracking_update": ["deadline", "status", "response", "contact", "right of reply"],
    }

    async def classify(self, query: str) -> TaskClassification:
        # LLM-based classification first
        try:
            return await self._llm_classify(query)
        except Exception:
            # Heuristic fallback (matching Cicero's pattern)
            return self._heuristic_classify(query)
```

### 7b. Context Builder (`src/orchestration/context.py`)

Token-budgeted assembly with investigation-specific allocation:

```python
# Context budget allocation (mirroring Cicero's 60/20/20)
CONTEXT_ALLOCATION = {
    "evidence":      0.40,  # evidencedb + paymentsdb (canonical figures)
    "source_docs":   0.30,  # casedb + LanceDB (articles, documents)
    "methodology":   0.15,  # skillsdb (investigation methods, legal framework)
    "tracking":      0.15,  # trackingdb (status, correspondence)
}
```

### 7c. Pipeline Definitions (YAML-driven)

```yaml
# pipelines/article_draft.yaml
name: Article Drafting Pipeline
description: Full pipeline from topic to publication-ready section

steps:
  - name: research
    agents: [osint_researcher, data_analyst]
    parallel: true
    databases: [paymentsdb, evidencedb, casedb]
    output: research_context.json

  - name: parallel_draft
    agents: [data_analyst, investigator, writer]
    parallel: true
    input: research_context.json
    output: drafts/

  - name: adversarial_critique
    agents: [data_analyst, investigator, writer, verifier]
    mode: cross_review  # each critiques the others
    input: drafts/
    output: critiques/

  - name: source_verification
    agents: [verifier]
    databases: [paymentsdb, evidencedb]
    input: drafts/
    output: verification_report.json

  - name: redaction_scan
    agents: [source_protector]
    input: drafts/
    output: redaction_report.json

  - name: refinement
    condition: "verification_report.critical_issues > 0"
    max_retries: 1
    agents: [writer, data_analyst]
    input: [drafts/, critiques/, verification_report.json]
    output: refined_drafts/

  - name: editor_synthesis
    agents: [editor]
    input: [refined_drafts/, verification_report.json, redaction_report.json]
    output: final_section.md
    metadata: publication_status.json  # GREEN/YELLOW/RED/HOLD
```

```yaml
# pipelines/figure_verification.yaml
name: Full Figure Verification
description: Cross-check every canonical figure against source data

steps:
  - name: extract_claims
    agents: [verifier]
    input: ${article_file}
    output: claims.json

  - name: verify_each
    agents: [data_analyst]
    databases: [paymentsdb, evidencedb]
    input: claims.json
    loop: true  # iterate over each claim
    output: verified_claims.json

  - name: grade_evidence
    agents: [verifier]
    input: verified_claims.json
    output: evidence_report.md
```

```yaml
# pipelines/redaction_full.yaml
name: Full Redaction Sweep
description: Scan all outputs for source-identifying patterns

steps:
  - name: pattern_scan
    agents: [source_protector]
    input: ${output_directory}
    patterns:
      - "location 1014"
      - "your (position|role|job)"
      - "insider|internal"
      - "I (work|am employed)"
      - "codename|architect|chief|sentinel|antigravity|neo|woodward"
      - "dispatch|briefing|handoff"
      - "AnythingLLM"
    output: redaction_report.md
```

---

## 8. LLM Provider Configuration (Extending Cicero's Pattern)

### 8a. Supported Providers (Adding Anthropic to Cicero's OpenAI + Gemini)

| Provider | Implementation | Primary Use | Models |
|----------|---------------|------------|--------|
| **OpenAI** | `openai` SDK via `AsyncLLMClient._call_openai()` | Drafting, fact-checking | gpt-4o, gpt-4o-mini, o3-mini |
| **Google Gemini** | `google-generativeai` via `AsyncLLMClient._call_gemini()` | Long-context analysis, cheap bulk work | gemini-2.5-pro, gemini-2.5-flash |
| **Anthropic** | `anthropic` SDK via `AsyncLLMClient._call_anthropic()` | Editorial review, legal caution | claude-sonnet-4-6, claude-haiku-4-5 |

### 8b. Per-Role Model Assignment (Matching Cicero's config pattern)

```python
# src/core/config.py
class AppConfig(BaseSettings):
    # Editorial Board model assignments
    BOARD_DATA_ANALYST_MODEL: str = "gemini-2.5-pro"
    BOARD_INVESTIGATOR_MODEL: str = "gpt-4o"
    BOARD_WRITER_MODEL: str = "gpt-4o"
    BOARD_VERIFIER_MODEL: str = "gpt-4o"
    BOARD_SOURCE_PROTECTOR_MODEL: str = "gpt-4o-mini"
    BOARD_EDITOR_MODEL: str = "claude-sonnet-4-6"
    BOARD_CHIEF_MODEL: str = "gpt-4o"
    BOARD_OSINT_MODEL: str = "gemini-2.5-flash"

    # Cheap models for high-volume tasks
    BULK_CLASSIFICATION_MODEL: str = "gemini-2.5-flash"
    BULK_EXTRACTION_MODEL: str = "gpt-4o-mini"
    BULK_EMBEDDING_MODEL: str = "text-embedding-3-small"
```

### 8c. Provider Auto-Detection (Extending Cicero's pattern to 3 providers)

```python
def _get_provider(self, model: str) -> str:
    if model.startswith("gemini-"):
        return "google"
    elif model.startswith("claude-"):
        return "anthropic"
    elif model.startswith("o3") or model.startswith("o1"):
        return "openai"  # reasoning models
    else:
        return "openai"  # default
```

---

## 9. Data Flow: User Input to Final Output

```
User: "Draft a section on the $3M board estimate vs $11M actual"
    |
    |-[1]--> Chief routes to: article_draft pipeline
    |
    |-[2]--> BrainBaseLoader loads:
    |           Data Analyst ← Module1_DataScience/SubA_Financial_Analysis
    |           Investigator ← Module2_Investigation/SubC_Governance
    |           Writer ← Module3_Journalism/SubA_Narrative
    |
    |-[3]--> Research Phase (parallel):
    |           |
    |           |--> Data Analyst queries paymentsdb:
    |           |      "SELECT SUM(amount) FROM payments
    |           |       WHERE payee_normalized LIKE '%amergis%'
    |           |       AND fiscal_year = '2024-25'"
    |           |      → $10,970,973 [PROOF: paymentsdb row count 4,231]
    |           |
    |           |--> Investigator queries evidencedb:
    |           |      "MATCH (ba:BoardAction)-[:REFERENCES]->(v:Vendor {name:'Amergis'})
    |           |       WHERE ba.fiscal_year = '2024-25'
    |           |       RETURN ba.description, ba.estimated_cost"
    |           |      → "Approximate Cost: $3,000,000" [PROOF: BoardDocs 2024-07-09]
    |           |
    |           |--> OSINT Researcher queries LanceDB:
    |                  → Retrieved context about consent agenda mechanism
    |
    |-[4]--> ContextBuilder assembles (token budget 8000):
    |           40% evidence: verified figures + source citations
    |           30% source docs: BoardDocs excerpt, article 2 relevant section
    |           15% methodology: consent agenda governance framework
    |           15% tracking: right-of-reply status for this claim
    |
    |-[5]--> Parallel Drafting:
    |           Data Analyst → figure table with variance calculation
    |           Investigator → factual backbone with primary source chain
    |           Writer → narrative prose section
    |
    |-[6]--> Adversarial Critique (cross-review)
    |
    |-[7]--> FigureVerifier.verify_all(draft)
    |           → Checks $10,970,973 against paymentsdb: MATCH
    |           → Checks $3,000,000 against BoardDocs: MATCH
    |           → Checks $13,326,622 total: MATCH
    |
    |-[8]--> RedactionScanner.scan(draft)
    |           → 0 identifying patterns found
    |
    |-[9]--> Editor synthesis:
    |           → Language calibration: all assertions matched to evidence grade
    |           → Legal risk: documented fact, not inference — GREEN
    |           → Publication status: GREEN
    |
    |---> Final section (Markdown + metadata JSON)
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Scaffold project structure matching directory tree above
- [ ] Port `AsyncLLMClient` from Cicero, add Anthropic adapter
- [ ] Wire `knight-lib` Neo4j adapter for evidencedb and casedb
- [ ] Build SQLiteAdapter wrapping existing paymentsdb
- [ ] Implement QueryRouter with heuristic fallback
- [ ] Implement ContextBuilder with investigation-specific allocation
- [ ] Build CLI interface for basic query → response

### Phase 2: Brains + Skills (Week 3-4)
- [ ] Create BrainBase directory structure (5 modules, 13 submodules)
- [ ] Write all 13 system prompts in standard format
- [ ] Port BrainBaseLoader from Cicero
- [ ] Implement core skills: PaymentAnalyzer, CostModeler, FigureVerifier
- [ ] Implement RedactionScanner
- [ ] Build EvidenceGrader

### Phase 3: Editorial Board Pipeline (Week 5-6)
- [ ] Implement EditorialBoard (mirroring Council)
- [ ] Build parallel drafting with asyncio
- [ ] Build adversarial critique (cross-review step)
- [ ] Build source verification pipeline
- [ ] Build editor synthesis step
- [ ] Implement YAML pipeline parser and executor

### Phase 4: Database Population (Week 7-8)
- [ ] Ingest 153 warrant register PDFs into LanceDB
- [ ] Build evidencedb graph from payment data
- [ ] Build casedb graph from articles, dossiers, correspondence
- [ ] Populate skillsdb with investigation methodology
- [ ] Populate trackingdb from accountability tracker

### Phase 5: Assembly + Integration (Week 9-10)
- [ ] Build article assembly engine (Markdown output)
- [ ] Build evidence package assembly
- [ ] Build FastAPI server
- [ ] Build VS Code webview UI
- [ ] End-to-end acceptance testing
- [ ] Production run: regenerate unified article through full pipeline

---

## 11. What to Tell Claude Code

**CRITICAL: Paste the contents of `WOODWARD_ISOLATION_BOUNDARIES.md` into the Claude Code session BEFORE giving any build instructions. That document defines what cannot be carried over from Cicero.**

Then paste this instruction to begin Phase 1:

"Read the WOODWARD_ISOLATION_BOUNDARIES.md document first. Every rule in it is mandatory.

Build the Woodward project scaffolding at `/Volumes/WD_BLACK/Desk2/Projects/Woodward` following the directory structure in the architecture spec. Start with:
1. The full directory tree (empty files with docstrings describing purpose)
2. `requirements.txt` with all dependencies (include anthropic SDK, do NOT include eyecite)
3. `.env.example` with all required environment variables (including ANTHROPIC_API_KEY)
4. `src/core/config.py` using Cicero's BaseSettings PATTERN but with all-new investigation-specific settings and model assignments. No legal domain content.
5. `src/core/models.py` with the full model registry including Anthropic models (claude-sonnet-4-6, claude-haiku-4-5). No Cicero model names carried over verbatim.
6. `src/agents/base.py` using Cicero's AsyncLLMClient PATTERN with Anthropic adapter added. No legal-specific prompt handling.
7. `src/agents/brainbase.py` using Cicero's BrainBaseLoader PATTERN pointed at Woodward's own BrainBase directory.
8. `src/adapters/sqlite.py` wrapping the existing paymentsdb at investigations/vps_2026/woodward.db.

Do NOT modify any Cicero files. Use knight-lib as a shared dependency for Neo4j adapter and config base only. Do NOT import or reference anything from Cicero's skills, brains, schemas, or constants. Every skill, brain, and schema in Woodward is written from scratch."
