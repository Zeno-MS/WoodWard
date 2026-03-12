# WOODWARD ISOLATION BOUNDARIES
## What Claude Code Must NOT Carry Over from Cicero

*This document is mandatory reading before any Woodward implementation work. Paste it into every Claude Code session that touches Woodward.*

---

## The Rule

Woodward borrows Cicero's **architectural patterns** (how agents are structured, how pipelines flow, how BrainBase loads prompts, how adapters connect to databases). It does NOT borrow Cicero's **domain content** (legal knowledge, legal skills, legal prompts, legal schemas, legal embeddings).

Think of it this way: Woodward uses the same blueprints as the Cicero building, but everything inside the rooms is different. The walls, plumbing, and electrical are the same. The furniture, books, and tools are completely different.

---

## Specific Contamination Points to Block

### 1. BrainBase Prompts: Write Fresh, Do Not Port

**DO NOT** port any system prompt text from Cicero's BrainBase. Every Woodward brain must be written from scratch for the investigative journalism domain.

Specifically, do not carry over:
- Stasis Theory (Conjecture/Definition/Quality/Translation) -- this is a legal argument framework, not a journalism framework
- CREAC structure (Conclusion/Rule/Explanation/Application/Conclusion) -- this is legal brief structure
- Any reference to RAP (Rules of Appellate Procedure)
- Any reference to CJC (Code of Judicial Conduct)
- Any reference to RCW citations as legal authority (Woodward uses RCW references as public records law, not as case authority)
- Any reference to "holdings," "rulings," "motions," "briefs," or "appellate"
- The Logician's classical rhetoric framework
- The Orator's persuasive legal advocacy voice
- The Historian's record citation format (RP/CP page references)

**WHAT TO DO INSTEAD:** Write all 15 Woodward system prompts from scratch using the ROLE/SCOPE/CONSTRAINTS/TONE/ROUTING/SKILLS/OUTPUT template structure from Cicero, but with investigative journalism content. The example Writer brain in the architecture spec shows the correct pattern.

### 2. Skills: Build New, Do Not Fork

**DO NOT** fork, copy, or adapt any skill from `src/skills/wa_appeals/`. Every Woodward skill is new.

Skills that must NOT appear in Woodward:
- `argument_builder.py` (CREAC argument construction)
- `authority_validator.py` (legal authority chain validation)
- `issue_spotter.py` (legal issue identification)
- `shepardizer.py` (case treatment/validity checking)
- `rap_compliance.py` (RAP formatting rules)
- `brief_drafter.py` (legal brief staging)

**WHAT TO DO INSTEAD:** Build the skills listed in the architecture spec Section 6a. These are entirely different: PaymentAnalyzer, CostModeler, BudgetAnalyzer, ContractAnalyzer, FigureVerifier, RedactionScanner, etc. None of these exist in Cicero.

### 3. Database Schemas: New Graphs, New Nodes

**DO NOT** reuse node types or relationship types from Cicero's Neo4j schemas.

Cicero node types that must NOT appear in Woodward:
- `Opinion`, `Holding`, `Authority`, `ForeignCaseFact` (legal domain)
- `Chunk` with legal embeddings (Woodward chunks are financial/journalistic documents)
- `[:CITES]`, `[:CITES_OPINION]`, `[:CITES_AUTHORITY]`, `[:HAS_HOLDING]` (legal citation graph)

Woodward uses its own node types:
- `Payment`, `Vendor`, `FiscalYear`, `Contract`, `ContractClause`, `BudgetLine`, `WarrantRegister`
- `Article`, `Dossier`, `Person`, `Organization`, `TimelineEvent`, `BoardAction`, `Correspondence`, `Claim`
- `Skill`, `Module`, `Submodule`, `Methodology`
- `Contact`, `Deadline`, `RecordsRequest`, `AgencyResponse`

### 4. Embeddings: Different Domain, Possibly Different Model

**DO NOT** assume Isaacus kanon-2 embeddings are appropriate for Woodward. Kanon-2 is a legal-domain-specific embedding model at 768 dimensions. It was chosen for Cicero because it understands legal language, case citations, and statutory references.

Woodward's documents are financial records, journalistic articles, government budget reports, and public meeting minutes. These are not legal texts.

**WHAT TO DO INSTEAD:** Default to OpenAI `text-embedding-3-small` (1536d) or `text-embedding-3-large` (3072d) for Woodward embeddings unless testing shows kanon-2 performs well on financial/journalistic text. If kanon-2 is used, it must be a deliberate decision after evaluation, not an automatic carry-over.

### 5. Citation Verification: Different Meaning

In Cicero, "citation verification" means checking that a legal citation (e.g., "In re Marriage of Kovacs, 121 Wn.2d 795") actually exists in the legaldb Neo4j database and that the quoted text matches.

In Woodward, "source verification" means checking that a factual claim (e.g., "$10,970,973 paid to Amergis in FY24-25") matches the canonical data in paymentsdb or a primary source document.

**DO NOT** port `citation_verifier.py` from Cicero. The "Id." handler, the pin-cite matching, the legal abbreviation protection -- none of that applies. Build `source_verifier.py` and `figure_verifier.py` from scratch.

### 6. Council Agent Names: Different Roles

The agent names change because the roles are fundamentally different:

| Cicero Agent | Woodward Agent | Why Different |
|-------------|---------------|--------------|
| Logician | Data Analyst | Legal reasoning vs. financial analysis |
| Historian | Investigator | Court record citations vs. primary source tracing |
| Orator | Writer | Legal persuasion vs. journalistic narrative |
| Fact Checker | Verifier | Legal claim validation vs. figure/source verification |
| (no parallel) | Source Protector | New role: anonymity and redaction scanning |
| Judge | Editor | Legal synthesis vs. editorial judgment |
| Orchestrator | Chief | Same role, different domain context |
| Researcher | OSINT Researcher | Case law research vs. public records/web research |

**DO NOT** use the names Logician, Historian, Orator, or Judge in Woodward. These carry legal connotations. Use Data Analyst, Investigator, Writer, Verifier, Source Protector, Editor, Chief, OSINT Researcher.

### 7. Constants and Patterns

**DO NOT** carry over `src/core/constants.py` from Cicero. That file contains legal Cypher graph patterns for case law traversal. Woodward needs its own constants for:
- Evidence grade tags: `[PROOF]`, `[STRONG INFERENCE]`, `[SUSPICION]`, `[UNRESOLVED]`
- Redaction patterns (source protection regex)
- Canonical investigation figures (locked data points)
- Fiscal year bucketing rules (Sept 1 - Aug 31)

### 8. Assembly Engine

Cicero's `assembly/engine.py` produces DOCX files formatted per RAP 10.3 (appellate brief formatting rules). Woodward produces Markdown articles, CSV data exports, and evidence packages.

**DO NOT** port the DOCX assembly engine or any RAP formatting logic. Build `article_engine.py`, `evidence_package.py`, and `memo_engine.py` from scratch.

### 9. Ingestion Pipeline

Cicero's `legal_document_processor.py` uses `eyecite` for legal citation extraction and `semchunk` for semantic chunking of court opinions.

Woodward's ingestion pipeline processes:
- Warrant register PDFs (tabular financial data, not prose)
- BoardDocs meeting minutes and agendas
- OSPI F-195 budget reports and S-275 personnel data
- News articles from The Columbian, OPB, InvestigateWest

**DO NOT** use `eyecite` in Woodward. It is a legal citation extraction library. Woodward needs `pdfplumber` or `tabula` for tabular PDF extraction, and standard text processing for news articles and meeting minutes.

---

## What CAN Be Shared (via knight-lib)

These infrastructure components are domain-agnostic and safe to share:

- `knight_lib/adapters/neo4j.py` -- Neo4j connection adapter (sync and async). Database-agnostic.
- `knight_lib/config/` -- Base configuration patterns. Domain-agnostic.
- `knight_lib/models/` -- Shared Pydantic base models. Domain-agnostic.

The embedding client (`knight_lib/embeddings/client.py`) can be shared as infrastructure, but the embedding MODEL choice must be re-evaluated for Woodward's domain.

## What CAN Be Ported (Architecture Only)

These files can be ported with domain content replaced:

| Cicero File | Port To Woodward | What Changes |
|------------|-----------------|-------------|
| `src/agents/base.py` (AsyncLLMClient) | `src/agents/base.py` | Add Anthropic adapter. Remove legal-specific prompt handling. |
| `src/agents/brainbase.py` (BrainBaseLoader) | `src/agents/brainbase.py` | Point to Woodward's BrainBase directory. Same loading mechanism. |
| `src/agents/council.py` (Council) | `src/agents/editorial_board.py` | Same parallel-draft-critique-synthesize pattern. Different agent names, roles, and prompts. |
| `src/orchestration/router.py` (QueryRouter) | `src/orchestration/router.py` | Same two-tier classification pattern. Different task categories and keywords. |
| `src/orchestration/coordinator.py` | `src/orchestration/coordinator.py` | Same parallel retrieval + RRF fusion. Different adapter set and source weights. |
| `src/orchestration/context.py` (ContextBuilder) | `src/orchestration/context.py` | Same token-budgeted assembly. Different allocation percentages (40/30/15/15 instead of 60/20/20). |
| `src/core/config.py` (AppConfig) | `src/core/config.py` | Same BaseSettings pattern. Different env vars and model assignments. |
| `src/core/models.py` (model registry) | `src/core/models.py` | Add Anthropic models. Same registry pattern. |
| `src/api/server.py` (FastAPI) | `src/api/server.py` | Same server pattern. Different endpoints. |

---

## Verification Checklist

Before any Woodward code is committed, verify:

- [ ] No file imports anything from `src/skills/wa_appeals/`
- [ ] No system prompt contains the words: stasis, CREAC, RAP, CJC, appellate, brief, holding, ruling, motion
- [ ] No database schema uses node types: Opinion, Holding, Authority, ForeignCaseFact
- [ ] No code imports `eyecite`
- [ ] No relationship type uses: CITES_OPINION, CITES_AUTHORITY, HAS_HOLDING, HAS_FACT (legal graph)
- [ ] Agent names are: Data Analyst, Investigator, Writer, Verifier, Source Protector, Editor, Chief, OSINT Researcher (not Logician, Historian, Orator, Judge)
- [ ] Embedding model choice is documented and justified for the journalism/financial domain
- [ ] Assembly engine outputs Markdown, not DOCX with RAP formatting
- [ ] Context allocation is 40/30/15/15 (evidence/sources/methodology/tracking), not 60/20/20 (caselaw/case/strategy)
- [ ] All constants in `constants.py` are investigation-specific, not legal-specific
