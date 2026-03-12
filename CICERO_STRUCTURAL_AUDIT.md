# Cicero Structural Audit
*Comprehensive architecture report for designing a parallel system (Woodward)*

---

## 1. Project Overview

**Cicero** is a production-grade legal AI orchestrator built for Washington State family law appellate work. It coordinates multiple LLM agents ("Council of Models"), retrieves from four specialized Neo4j graph databases plus LanceDB vector store, and produces verified legal briefs with citation checking.

- **Language**: Python 3.11+
- **Framework**: FastAPI (API), asyncio throughout
- **Project root**: `/Volumes/WD_BLACK/Desk2/Projects/Cicero`
- **Key dependencies**: `neo4j>=5.15`, `openai>=1.0.0`, `google-generativeai`, `anthropic`, `lancedb`, `fastapi`, `uvicorn`, `pydantic>=2.0`, `pydantic-settings>=2.0`, `tqdm`, `pdfplumber`

---

## 2. Directory Structure (Non-data files only)

```
Cicero/
├── cicero.py                    # Placeholder main (legacy)
├── Cicero.command               # Bash launcher (kills port 8000, starts API, opens browser)
├── case_config.json             # Case metadata for brief assembly
├── requirements.txt
├── pytest.ini
├── .env                         # All API keys and DB URIs
├── README.md
├── MANUAL.md                    # Architecture manual
├── INFRASTRUCTURE.md            # Database status
├── CONTEXT_HANDOFF.md           # Inter-session handoff state
├── CONTEXT_HANDOFF_WORKFLOW.md  # Token tracking protocol
├── OPCRAWLER_DB_GUIDE.md        # SQLite OPCrawler schema docs
│
├── src/
│   ├── main.py                  # RAGSystem — top-level orchestrator
│   ├── cli.py                   # CLI interface
│   │
│   ├── core/
│   │   ├── config.py            # AppConfig (env vars, DB connections, model roles)
│   │   ├── constants.py         # Legal Cypher graph patterns
│   │   ├── models.py            # LLM model registry (GPT-5.4, o3, Gemini, etc.)
│   │   ├── types.py             # RetrievalResult, SourceType, StoreResult
│   │   └── settings.py          # Neo4jClusterSettings dataclass
│   │
│   ├── agents/
│   │   ├── base.py              # AsyncLLMClient (OpenAI + Gemini unified)
│   │   ├── brainbase.py         # BrainBaseLoader (external system prompts)
│   │   ├── council.py           # Council — multi-agent drafting pipeline
│   │   ├── citation_verifier.py # Citation verification against Neo4j
│   │   └── validators/
│   │       └── rap_compliance.py # RAP 10.3/10.4 compliance checks
│   │
│   ├── orchestration/
│   │   ├── router.py            # QueryRouter (LLM + heuristic classification)
│   │   ├── coordinator.py       # RetrievalCoordinator (parallel search, RRF fusion)
│   │   ├── context.py           # ContextBuilder (token-budgeted prompt assembly)
│   │   └── reranker.py          # CrossEncoderReranker (currently CPU-disabled)
│   │
│   ├── adapters/
│   │   ├── base.py              # Abstract BaseAdapter contract
│   │   ├── neo4j.py             # Neo4jAdapter (vector + graph + fulltext)
│   │   └── lancedb.py           # LanceDBAdapter (vector-only)
│   │
│   ├── services/
│   │   ├── drafting.py          # DraftingService (brief generation pipeline)
│   │   ├── embedding.py         # EmbeddingService (caching, provider routing)
│   │   └── ingestion.py         # IngestionService (batch document processing)
│   │
│   ├── skills/
│   │   └── wa_appeals/
│   │       ├── drafter/
│   │       │   └── brief_drafter.py    # 5-stage sequential brief drafter
│   │       ├── logic/
│   │       │   ├── argument_builder.py # CREAC argument construction
│   │       │   ├── authority_validator.py # Authority chain validation
│   │       │   ├── issue_spotter.py    # Legal issue identification
│   │       │   └── shepardizer.py      # Case treatment/validity checking
│   │       └── validators/
│   │           └── rap_compliance.py   # Duplicate of agents/validators/
│   │
│   ├── ingest/
│   │   └── legal_document_processor.py # Semantic chunking + eyecite + kanon-2
│   │
│   ├── ingestion/
│   │   └── processor.py         # PDF text extraction + sentence chunking
│   │
│   ├── assembly/
│   │   └── engine.py            # DOCX brief assembly (RAP formatting)
│   │
│   ├── modules/
│   │   ├── candidate_generator/
│   │   │   ├── engine.py        # Case candidate ranking (SQLite OPCrawler)
│   │   │   ├── models.py        # Pydantic models for candidates
│   │   │   ├── court_listener.py # CourtListener API client + disk cache
│   │   │   ├── security.py      # Input sanitization
│   │   │   └── validity.py      # Case validity/deprecation checking
│   │   └── forms/
│   │       └── adapter.py       # Appellate form PDF filler
│   │
│   ├── api/
│   │   └── server.py            # FastAPI server (530 lines)
│   │
│   └── utils/
│       └── metadata.py          # Filing metadata extraction
│
├── tests/
│   ├── agents/                  # Council, citation verifier, brainbase tests
│   ├── acceptance/              # AT1-AT4: isolation, hybrid, degradation, context
│   ├── integration/             # Retrieval scoring, ingestion
│   ├── api/                     # Server endpoint tests
│   └── modules/                 # Candidate generator tests
│
├── scripts/
│   ├── production_run_cjc.py    # Production CJC argument generation
│   ├── query_theory.py          # Theory-of-case querying
│   ├── repair_empty_opinions.py # Data repair
│   ├── ingest_manual/           # Manual case ingestion pipeline
│   ├── audit/                   # Data integrity audits
│   ├── diagnostics/             # System diagnostics
│   ├── db/                      # Database utilities
│   ├── queries/                 # Saved Cypher queries
│   └── utils/                   # Shared script utilities
│
├── cases/61813-3-II/            # Active case files
│   ├── case_config.json
│   ├── briefs/opening/          # Final brief outputs
│   └── record/                  # Court record documents
│
├── docs/
│   ├── schema/                  # JSON schema dumps for all 4 Neo4j databases
│   ├── hardening/               # Master plans v1-v4.1, audit reports
│   └── research/                # Background research
│
├── drafts/                      # Draft outputs, test results, audit data
├── form_filler/                 # Standalone appellate form filler
├── ui/                          # Simple HTML frontend
└── .github/prompts/             # GitHub Copilot prompt definitions
```

---

## 3. The Four Database Pillars

### 3a. legaldb (CaseLawDB — "The Jurist")
- **Purpose**: Controlling legal precedent, case opinions, holdings, citations
- **Node count**: ~24,700 (63 Opinions, 21,142 Chunks, 1,268 Authorities, 209 ForeignCaseFacts, 139 Holdings)
- **Key relationships**: `[:HAS_CHUNK]`, `[:NEXT]` (sequential chains), `[:CITES]`, `[:CITES_OPINION]`, `[:CITES_AUTHORITY]`, `[:HAS_HOLDING]`, `[:HAS_FACT]`
- **Vector indexes**: `chunk_embedding` (768d), `holding_embedding` (768d), `casefact_embedding` (768d)
- **Fulltext indexes**: `chunk_text_search`, `document_content`, `caselaw_case_name`
- **Embedding model**: Isaacus kanon-2-embedder at 768 dimensions
- **Env vars**: `CASELAW_NEO4J_URI`, `CASELAW_NEO4J_USERNAME`, `CASELAW_NEO4J_PASSWORD`, `CASELAW_NEO4J_DATABASE`

### 3b. casedb (MyCaseDB — "The Historian")
- **Purpose**: Case-specific facts, filings, parties, record documents
- **Node count**: 923 (694 Chunks, 301 Documents, 122 Cases, 53 Authorities, 47 Filings, 2 Parties)
- **Key relationships**: `[:HAS_CHUNK]`, `[:NEXT]`, `[:CITES]`, `[:CONTAINS]`
- **Vector index**: `legal_chunk_embeddings` (on Chunk.embedding)
- **Env vars**: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`

### 3c. strategydb (BrainBase — "The Strategist")
- **Purpose**: Legal skills, strategy modules, entity relationships
- **Node count**: 798 (365 Entities, 235 Skills, 129 Documents, 52 Parties, 12 Submodules, 5 Modules)
- **Key relationships**: `[:USES]` (708), `[:HAS_SKILL]` (243), `[:CONTAINS]` (12)
- **Vector index**: `cicero_embeddings` (on Skill.embedding)
- **Env vars**: `BRAINBASE_NEO4J_URI`, `BRAINBASE_NEO4J_USERNAME`, `BRAINBASE_NEO4J_PASSWORD`, `BRAINBASE_NEO4J_DATABASE`

### 3d. sentineldb ("The Sentinel")
- **Purpose**: Operational/communications tracking — filings, deadlines, persons
- **Node count**: 10 (5 Filings, 4 Persons, 1 Deadline)
- **Designed for**: Messages, CommunicationPatterns, Events (indexes exist but minimal data)
- **Env vars**: `SENTINEL_NEO4J_URI`, `SENTINEL_NEO4J_USERNAME`, `SENTINEL_NEO4J_PASSWORD`, `SENTINEL_NEO4J_DATABASE`

### 3e. LanceDB (Local vector store — "The Librarian")
- **Purpose**: Rules, formatting guides, procedural knowledge
- **Location**: Local filesystem
- **Config**: `LANCE_DB_PATH` env var

### 3f. OPCrawler (SQLite)
- **Purpose**: Case candidate discovery pipeline
- **Tables**: `cases` (metadata, filepath, url), `analysis` (issue scores, outcomes, quotes)
- **Used by**: `candidate_generator/engine.py`

---

## 4. Agents / Brains

### 4a. Council Agents (defined in `src/agents/council.py`)

The Council is a multi-agent pipeline where specialized agents draft in parallel, critique each other, and a Judge synthesizes:

| Agent Role | Purpose | Model (from config) | System Prompt Source |
|-----------|---------|---------------------|---------------------|
| **Logician** | CREAC structure, Stasis Theory analysis (Conjecture/Definition/Quality/Translation) | Configurable | Module1_Codex |
| **Historian** | Statement of facts with record citations (RP/CP) | Configurable | Module3_Strategist |
| **Orator** | Persuasive polish, rhetorical refinement, RAP compliance | Configurable | Module2_Orator |
| **Fact Checker** | Validate claims against original facts, check citations | Configurable | Module1_Codex |
| **Judge** | Final synthesis combining all drafts, removing fabrications | Configurable | Module3_Strategist |
| **Orchestrator** | System-level coordination | Configurable | Module5_Architect |
| **Researcher** | RAG query construction | Configurable | Module5_Architect |

### 4b. Council Pipeline Flow

```
User Issue + Facts
    │
    ▼
[1. Research Phase] — RAG query → retrieval → authority context
    │
    ▼
[2. Parallel Drafting] — Logician + Historian + Orator (concurrent)
    │
    ▼
[3. Adversarial Critique] — Each agent critiques others (Logic / Facts / Tone)
    │
    ▼
[4. Citation Verification] — All citations checked against legaldb
    │
    ▼
[5. Fact Checking] — Claims validated, severity levels assigned
    │
    ▼
[6. Refinement Loop] — Re-draft if CRITICAL issues found (max 1 retry)
    │
    ▼
[7. Judge Synthesis] — Final unified brief
```

### 4c. BrainBase System Prompts (External)

System prompts live in `/Volumes/WD_BLACK/Desk2/Projects/BrainBase/BrainCrate/Brains/`:

| Module | Submodules | Role |
|--------|-----------|------|
| **Module1_Codex** | SubA_WA_Div_II (Appellate Procedural), SubB_Clark_County (Family Law Specialist) | Legal knowledge base |
| **Module2_Orator** | SubA_Narrative (Advocacy Strategist), SubB_Brief_Drafting (Legal Writing Editor) | Persuasive writing |
| **Module3_Strategist** | SubA_Judicial_Misconduct (Ethics Analyst), SubB_Contempt_Enforcement (Enforcement), SubC_Appellate_Standards | Strategy |
| **Module4_Psychologist** | SubA_Adversary (HCP Specialist), SubB_Child_Centered (Family Systems) | Behavioral analysis |
| **Module5_Architect** | SubA_System_Prompts (Drafting Assistant), SubB_Infrastructure (RAG Specialist), SubC_OSINT (Investigative Journalist) | System/ops |

Each system prompt follows a standard format:
```markdown
## ROLE AND IDENTITY
## SCOPE (IN/OUT)
## HARD CONSTRAINTS
## TONE
## QUERY ROUTING (FACTUAL → Vector, PROCEDURAL → Skill, RELATIONAL → Graph)
## AVAILABLE SKILLS
## OUTPUT FORMAT
```

---

## 5. Skills

### 5a. WA Appeals Skills (`src/skills/wa_appeals/`)

| Skill | File | Purpose |
|-------|------|---------|
| **BriefDrafter** | `drafter/brief_drafter.py` | 5-stage sequential drafting (Discovery → Outlining → CREAC Drafting → Refinement → Assembly) |
| **ArgumentBuilder** | `logic/argument_builder.py` | CREAC argument construction from issue + authority |
| **AuthorityValidator** | `logic/authority_validator.py` | Authority chain validation against database |
| **IssueSpotter** | `logic/issue_spotter.py` | Legal issue identification from facts |
| **Shepardizer** | `logic/shepardizer.py` | Case treatment/validity checking (good law assessment) |
| **RAP Compliance** | `validators/rap_compliance.py` | Required sections check (RAP 10.3), word count (RAP 10.4), citation format validation |

### 5b. BrainBase Skills (from system prompts)

Each submodule prompt declares available skills, e.g., Module3_Strategist/SubA_Judicial_Misconduct declares:
- `draft-judicial-conduct-complaint-substance`
- `format-and-submit-judicial-complaint`
- `file-cr-60b-motion-misconduct`
- `apply-appearance-of-fairness-test`
- `argue-structural-error-reversal`
- `enforce-judicial-disqualification-cjc-2-11`
- `identify-prohibited-judicial-investigation`
- etc.

These are declarative skill names in the prompt; the Council's BrainBaseLoader loads them from local `SKILL.md` files in `src/skills/`.

---

## 6. Routing / Orchestration Logic

### 6a. Query Router (`src/orchestration/router.py`)

Two-tier classification:
1. **LLM-based**: Sends query + classification prompt to configured model → expects JSON `{"strategy": "vector_only|graph_only|hybrid", "reasoning": "..."}`
2. **Heuristic fallback**: If LLM fails, pattern-matches keywords:
   - Graph triggers: "cite", "citing", "cited by", "authority chain", "overrule"
   - Vector triggers: "what is", "explain", "define", "meaning"
   - Default: **hybrid** (safest — never misses graph relationships)

JSON extraction uses robust brace-finding fallback for malformed LLM output (especially Gemini).

### 6b. Retrieval Coordinator (`src/orchestration/coordinator.py`)

1. Health-check all adapters (async ping with timeout)
2. Execute retrieval across healthy adapters in parallel
3. **Reciprocal Rank Fusion (RRF)** with k=60 to merge ranked lists
4. **Source diversity weighting**: `reingested=1.3x`, `curated=1.1x`, `legacy=0.7x`
5. Deduplication by content fingerprint
6. Optional cross-encoder reranking (disabled on CPU)

### 6c. Context Builder (`src/orchestration/context.py`)

Token-budgeted prompt assembly with source-type allocation:
- **Strategy** (from strategydb): 20% cap
- **Record** (from casedb): 20% floor
- **Case Law** (from legaldb): 60% minimum
- Uses tiktoken for token counting
- Preserves citation keys in assembled context

---

## 7. LLM Provider Configuration

### 7a. Supported Providers

| Provider | Implementation | Models |
|----------|---------------|--------|
| **OpenAI** | `openai` SDK via `AsyncLLMClient._call_openai()` | GPT-5.4, GPT-5.2, o3, o3-mini, GPT-4.5 |
| **Google Gemini** | `google-generativeai` SDK via `AsyncLLMClient._call_gemini()` | gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash-001 |
| **Anthropic** | Listed in requirements but not directly in AsyncLLMClient | (Available but not wired into Council) |

### 7b. Model Registry (`src/core/models.py`)

14 known models with context windows and output limits:
```
gpt-5.4:         200K context, 32K output
gpt-5.2:         200K context, 32K output
o3:              200K context, 100K output (reasoning model)
o3-mini:         200K context, 100K output (reasoning model)
gpt-4.5-preview: 128K context, 16K output
gemini-2.5-pro:  1M context, 65K output
gemini-2.5-flash: 1M context, 65K output
gemini-2.0-flash-001: 1M context, 8K output
```

### 7c. Model Selection

**Per-role assignment** in `AppConfig`:
```python
COUNCIL_ORCHESTRATOR_MODEL = "gpt-5.4"
COUNCIL_RESEARCHER_MODEL = "gpt-5.4"
COUNCIL_LOGICIAN_MODEL = "gemini-2.5-pro"
COUNCIL_HISTORIAN_MODEL = "gpt-5.4"
COUNCIL_ORATOR_MODEL = "gemini-2.5-pro"
COUNCIL_FACT_CHECKER_MODEL = "gpt-5.4"
COUNCIL_JUDGE_MODEL = "gpt-5.4"
```

Provider auto-detected from model name prefix ("gemini-" → Google, else → OpenAI). O-series models use `max_completion_tokens` instead of `max_tokens`.

### 7d. Embedding Provider

**Isaacus kanon-2-embedder** at 768 dimensions (legal-domain-specific):
- API: `POST https://api.isaacus.com/v1/embeddings`
- Shared library: `knight_lib/embeddings/client.py`
- Used by both Cicero and the LegalDocumentProcessor

---

## 8. Shared Infrastructure

### 8a. knight-lib (`/Volumes/WD_BLACK/Desk2/Projects/knight-lib/`)

Shared across Cicero and Sentinel:
- `knight_lib/adapters/neo4j.py` — `Neo4jAdapter` (sync) + `AsyncNeo4jAdapter` with explicit database enforcement
- `knight_lib/embeddings/client.py` — `embed_text()` and `embed_batch()` using Isaacus API
- `knight_lib/config/` — Shared configuration
- `knight_lib/models/` — Shared data models

### 8b. BrainBase (`/Volumes/WD_BLACK/Desk2/Projects/BrainBase/`)

External system prompt repository:
```
BrainCrate/
├── Brains/          # system_prompt_compact.md files (12 prompts across 5 modules)
├── Classified/      # Classified materials per module
├── Articles/        # Source articles per module
├── Golden/          # Golden examples per module
├── Clustered/       # Clustered knowledge per module
├── Extracted/       # Extracted knowledge per module
├── Graphs/          # Knowledge graphs per module
└── Logs/            # Processing logs
```

---

## 9. Data Flow: User Input to Final Output

```
User: "Draft an argument about judicial misconduct under CJC 2.9"
    │
    ├─[1]─► DraftingService.draft_brief()
    │           │
    │           ├─[2]─► BrainBaseLoader.get_agent_prompt("logician")
    │           │           → Loads Module1_Codex system prompt
    │           │
    │           ├─[3]─► RAGSystem.query("CJC 2.9 judicial misconduct")
    │           │           │
    │           │           ├─[3a]─► EmbeddingService.embed(query)
    │           │           │           → Isaacus kanon-2 → 768d vector
    │           │           │
    │           │           ├─[3b]─► QueryRouter.classify(query)
    │           │           │           → LLM: "This is HYBRID" (or heuristic fallback)
    │           │           │
    │           │           ├─[3c]─► RetrievalCoordinator.retrieve(query, vector, strategy=HYBRID)
    │           │           │           ├── Neo4j legaldb: vector search + graph pattern
    │           │           │           ├── Neo4j casedb: vector search
    │           │           │           ├── Neo4j strategydb: skill search
    │           │           │           └── LanceDB: vector search
    │           │           │           → RRF fusion → source diversity weighting → dedupe
    │           │           │
    │           │           └─[3d]─► ContextBuilder.build(results, token_budget=8000)
    │           │                       → Token-budgeted prompt with citations
    │           │
    │           ├─[4]─► Council.draft_brief(issue, facts, authority_context)
    │           │           ├── Logician (CREAC + Stasis Theory) ──┐
    │           │           ├── Historian (Facts + Record cites)   ├── Parallel
    │           │           └── Orator (Persuasion + RAP)         ──┘
    │           │           │
    │           │           ├── Adversarial Critique (cross-review)
    │           │           ├── CitationVerifier.verify_document(draft)
    │           │           │       → Checks every citation against legaldb Neo4j
    │           │           ├── Fact Checker (claim validation)
    │           │           ├── Refinement (if critical issues, max 1 retry)
    │           │           └── Judge Synthesis (final unified draft)
    │           │
    │           └─[5]─► AssemblyEngine.assemble(sections, case_config)
    │                       → DOCX with RAP 10.3 formatting
    │
    └─► Final brief (DOCX + JSON metadata)
```

---

## 10. Output Persistence

- **Draft JSON**: Stored in `drafts/` with version numbering (v1, v2, etc.)
- **Final DOCX**: Assembled in `cases/{case_number}/briefs/opening/`
- **Neo4j**: Citation verification creates `[:CITES_AUTHORITY]` relationships in legaldb
- **Draft Vault**: API server maintains in-memory vault of recent drafts
- **Logs**: `logs/` directory for ingestion and embedding operations

---

## 11. Non-Obvious Patterns

1. **Stasis Theory framework**: The Logician agent uses classical rhetorical Stasis Theory (Conjecture → Definition → Quality → Translation) to structure legal arguments. This is not a standard LLM prompting pattern.

2. **Provenance-based scoring**: Retrieval results are weighted by how they were ingested: `reingested` (verified re-processing) gets 1.3x boost, `curated` (manual) gets 1.1x, `legacy` (old pipeline) gets 0.7x penalty.

3. **"Id." citation chain tracking**: The citation verifier maintains state across a document to resolve "Id." and "Id. at N" references — it tracks the last verified citation to resolve short-form citations sequentially.

4. **Graceful degradation**: If any adapter fails health check, the system automatically degrades to use only healthy adapters. The `metadata.degraded` flag signals partial results.

5. **Legal abbreviation protection**: Sentence splitting protects legal abbreviations (v., U.S., Id., Wn., App., P.2d, etc.) from being treated as sentence boundaries.

6. **Explicit database enforcement**: The knight-lib Neo4j adapter *requires* the database parameter at init time and raises `ValueError` if omitted — this prevents accidental writes to the wrong database (there are 5+ databases on the same Neo4j instance).

7. **External brain loading with versioning**: BrainBase prompts are loaded from the filesystem with SHA256 hashing for version tracking. This allows prompt updates without code changes.

8. **Context handoff protocol**: The project maintains `.context_handoff_state.json` and `CONTEXT_HANDOFF.md` for inter-session state transfer between AI instances (different Claude sessions, Gemini, etc.).

9. **OPCrawler as case discovery**: A separate SQLite database (OPCrawler) is used for initial case candidate discovery before cases are ingested into the Neo4j graph. The candidate generator scores cases across multiple issue lanes with weighted ranking.

10. **Three embedding types in legaldb**: Chunks (general text), Holdings (legal conclusions), and ForeignCaseFacts (facts from cited cases) each have their own vector indexes, allowing targeted retrieval by content type.
