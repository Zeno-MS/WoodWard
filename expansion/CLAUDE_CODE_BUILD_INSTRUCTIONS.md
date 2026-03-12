# Claude Code Build Instructions — Woodward Core v2

> This document captures the full build instruction set for Woodward Core v2.
> It is the source-of-truth for what was implemented and why.
> Generated: 2026-03-12

---

## Preamble: Read First

Read and obey `WOODWARD_ISOLATION_BOUNDARIES.md` first. That file's rules are non-negotiable and override any default behavior.

---

## Context Files to Read Before Building

1. `expansion/REDLINE_ENACTMENT_MEMO.md`
2. `expansion/WOODWARD_CORE_V2_ENACTMENT_PLAN.md`
3. `CONTEXT_HANDOFF.md`
4. `VPS_Investigation_Evidence/EXECUTIVE_SUMMARY.md`
5. `VPS_Investigation_Evidence/01_Payment_Data/vendor_summary_by_year.csv`

---

## Non-Negotiable Guardrails

1. Do **NOT** modify any Cicero files.
2. Do **NOT** import or reference Cicero's legal prompts, legal skills, legal schemas, legal citation logic.
3. Do **NOT** use `eyecite`.
4. Default embeddings: **OpenAI `text-embedding-3-small`** (NOT kanon-2).
5. Woodward is **investigative journalism software**, not legal-brief software.
6. LLMs are **stateless workers**. Project state lives in canonical files, SQLite databases, and run artifacts.
7. **SQLite (`ledger.db`) is authoritative for money.** No graph database.
8. No publication-bound claim may pass without a public-citable support chain.
9. Build failures must **hard-stop**.

---

## Locked Figures

Seed these into `canonical/figures.yaml`. These values are locked and must not be altered:

| Figure | Value |
|--------|-------|
| FY24-25 staffing-vendor total | $13,326,622 |
| Cumulative baseline | ~$32.1M ($32,189,236) |
| Amergis FY24-25 | $10,970,973 |
| Object 7 budget FY24-25 | $36,738,206 |
| Object 7 actual FY24-25 | $47,331,056 |
| Object 7 overage FY24-25 | $10,592,850 |
| Board estimate for Amergis (July 9 2024 consent agenda) | ~$3,000,000 |
| OSPI advance requested | $21,367,552 |
| OSPI advance approved | $8,700,000 |

---

## Vendors

Seed these into `canonical/vendor_scope.yaml`:

- **Amergis** (formerly Maxim Healthcare) — primary staffing vendor
- **Aveanna Healthcare** — tracked separately, excluded from $32.1M canonical total
- **Stepping Stones** — tracked separately, excluded from $32.1M canonical total

---

## Files to Create

### 1. `pyproject.toml`

Full pyproject.toml with:

```toml
[project]
name = "woodward"
requires-python = ">=3.11"
```

Dependencies:

```
pydantic>=2
pydantic-settings>=2
fastapi
uvicorn
aiosqlite
pandas
pyyaml
openai
anthropic
google-generativeai
lancedb
pdfplumber
python-dotenv
rich
typer
pytest
pytest-asyncio
```

**NO** `eyecite`, **NO** legal citation tooling.

Scripts entry point:

```toml
[project.scripts]
woodward = "src.cli.main:app"
```

---

### 2. `.env.example`

Include vars for:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
WOODWARD_ENV=development
WOODWARD_INVESTIGATION=vps_2026
WOODWARD_DB_PATH=./db
WOODWARD_CANONICAL_PATH=./canonical
WOODWARD_RUNS_PATH=./runs
WOODWARD_LANCEDB_PATH=./lancedb
```

---

### 3. `.gitignore`

Standard Python gitignore plus:

```
.env
db/*.db
runs/
backups/
lancedb/
```

---

### 4. `Makefile`

Targets: `install`, `test`, `lint`, `canon-validate`, `canon-hash`, `migrate`, `clean`

The `canon-validate` target must call `woodward canon validate` and exit non-zero on failure.

---

### 5. `canonical/schema_version.yaml`

```yaml
schema_version: "1.0.0"
created: "2026-03-12"
investigation: "vps_2026"
locked_by: "woodward-core-v2"
```

---

### 6. `canonical/figures.yaml`

Each figure must have:

- `figure_id` (snake_case)
- `display_label`
- `value` (numeric, exact)
- `display_value` (formatted string like `"$13,326,622"`)
- `fiscal_year` or `date_context`
- `source_of_truth` (e.g. `"ledger.db/fiscal_rollups"` or `"board_minutes_july_9_2024"`)
- `derivation_id` (reference to derivation record)
- `status` (`"locked"` | `"provisional"` | `"superseded"`)
- `notes`

---

### 7. `canonical/vendor_scope.yaml`

Each entry must have:

- `vendor_id`
- `canonical_name`
- `aliases` (list)
- `rebrand_history` (list of `{from, to, effective_date}`)
- `canonical_total_included` (bool) — whether included in $32.1M canonical total
- `notes`

---

### 8. `canonical/articles.yaml`

Seed with 4 articles (article_1 through article_4). Each must have:

- `article_id`
- `title`
- `status` (`"locked_baseline"` | `"draft"` | `"published"`)
- `file_path` (relative to `investigations/vps_2026/`)
- `locked` (bool)
- `notes`

---

### 9. `canonical/claims_registry.yaml`

Seed with at minimum 3 key claims:

1. "VPS paid $10,970,973 to Amergis in FY24-25" — status: verified, public_citable: true
2. "Board approved Amergis at ~$3M on July 9, 2024 consent agenda" — status: verified, public_citable: true
3. "Amergis contract has no spending cap" — status: blocked, public_citable: false, right_of_reply_required: true, notes: "Contract text not yet in public record"

Each claim must have: `claim_id`, `text`, `article_id`, `status`, `public_citable`, `support_chain_complete`, `right_of_reply_required`, `stale`, `notes`

---

### 10. `canonical/banned_claims.yaml`

Include at minimum:

- Any claim implying Amergis intentionally defrauded VPS (motive language)
- Any claim citing internal non-public documents as primary source
- Any claim about individual employee intent

Format: list of `{ban_id, text_pattern, reason, added_date}`

---

### 11. `canonical/source_policy.yaml`

Define allowed source classes:

```yaml
public_record: allowed
public_reporting: allowed
public_records_response: allowed
public_agency_finding: allowed
internal_nonpublic: blocked
memory_only: blocked
insider_awareness: blocked
webapp_export: pending_review
```

---

### 12. `schemas/canonical.py`

Pydantic v2 models for:

- `CanonicalFigure`
- `VendorScope`
- `VendorAlias`
- `RebrandHistory`
- `ArticleRecord`
- `ClaimRecord`
- `BannedClaim`
- `SourcePolicy`
- `CanonManifest` (top-level container)
- `SchemaVersion`

Each model must have full field validation. `CanonicalFigure` must validate that `status` is one of the allowed values. `ClaimRecord` must validate publication_status against source_policy rules.

---

### 13. `schemas/llm_contracts.py`

Pydantic v2 models for:

- `FactualAssertion` (text, context_ids: list[str], claim_ids: list[str], figure_ids: list[str])
- `DraftSectionResponse` (section_id, article_id, content, assertions: list[FactualAssertion], metadata)
- `AdversarialFinding` (finding_id, severity: "blocker"|"warning"|"note", description, affected_claim_id)
- `AdversarialReviewResponse` (section_id, findings: list[AdversarialFinding], pass_build: bool)
- `ReplyPacketResponse` (thread_id, recipient, questions_answered, outstanding_claims, packet_markdown)

---

### 14. `schemas/ledger_models.py`

Pydantic v2 models matching the `ledger.db` schema:

- `Vendor`, `VendorAlias`, `SourceDocument`, `Payment`, `FiscalRollup`, `FigureDerivation`, `FigureLock`, `DedupAudit`

---

### 15. `schemas/records_models.py`

Pydantic v2 models matching `records.db`:

- `Document`, `Chunk`, `Claim`, `ClaimSupport`, `PublicationBlock`

---

### 16. `schemas/comms_models.py`

Pydantic v2 models matching `comms.db`:

- `Organization`, `Recipient`, `QuestionSet`, `Thread`, `Message`, `ResponseWindow`, `ArticleDependency`

---

### 17. `src/core/settings.py`

Use `pydantic-settings` `BaseSettings`. Load from `.env`. Include:

- `openai_api_key`, `anthropic_api_key`, `google_api_key`
- `woodward_env`, `woodward_investigation`
- `db_path`, `canonical_path`, `runs_path`, `lancedb_path`
- `default_embedding_model = "text-embedding-3-small"`
- `default_llm_model = "gpt-4o"`

---

### 18. `src/core/hashing.py`

Functions:

- `hash_file(path: Path) -> str` — SHA-256 of a single file
- `hash_directory(path: Path) -> dict[str, str]` — `{relative_path: sha256}` for all files in dir
- `hash_canon(canonical_path: Path) -> CanonHash` — hash the entire `canonical/` directory and return a `CanonHash` object with timestamp, individual hashes, and combined hash

`CanonHash` must be a dataclass or Pydantic model with: `timestamp`, `individual_hashes`, `combined_hash`, `schema_version`

---

### 19. `src/core/exceptions.py`

Custom exceptions:

- `WoodwardError` (base)
- `CanonValidationError`
- `FigureMismatchError`
- `BlockedClaimError`
- `UnsupportedClaimError`
- `PublicationBlockedError`
- `HallucinatedContextError`
- `ScopeUndeclaredError`
- `DenominatorMixError`
- `MigrationError`

---

### 20. `src/core/types.py`

Type aliases:

```python
FigureId = str
ClaimId = str
ArticleId = str
VendorId = str
RunId = str
SourceClass = Literal["public_record", "public_reporting", "public_records_response",
                      "public_agency_finding", "internal_nonpublic", "memory_only",
                      "insider_awareness", "webapp_export"]
ClaimStatus = Literal["draft", "verified", "blocked", "superseded", "pending_review"]
FigureStatus = Literal["locked", "provisional", "superseded"]
```

---

### 21. `src/repositories/canonical_repo.py`

`CanonicalRepo` class with:

- `load_figures() -> list[CanonicalFigure]`
- `load_vendor_scope() -> list[VendorScope]`
- `load_articles() -> list[ArticleRecord]`
- `load_claims() -> list[ClaimRecord]`
- `load_banned_claims() -> list[BannedClaim]`
- `load_source_policy() -> SourcePolicy`
- `load_all() -> CanonManifest`
- `validate_all() -> None` — raises `CanonValidationError` on any schema failure

---

### 22. DB Migrations

#### `db/migrations/ledger/001_init.sql`

Tables: `vendors`, `vendor_aliases`, `source_documents`, `payments`, `fiscal_rollups`, `figure_derivations`, `figure_locks`, `dedup_audit`

#### `db/migrations/records/001_init.sql`

Tables: `documents`, `chunks`, `claims`, `claim_support`, `publication_blocks`

#### `db/migrations/comms/001_init.sql`

Tables: `organizations`, `recipients`, `question_sets`, `threads`, `messages`, `response_windows`, `article_dependencies`

---

### 23. `src/repositories/ledger_repo.py`

`LedgerRepo` class using `aiosqlite`:

- `async get_vendor(vendor_id: str) -> Vendor | None`
- `async get_fiscal_rollup(vendor_id: str, fiscal_year: str) -> FiscalRollup | None`
- `async get_figure_derivation(derivation_id: str) -> FigureDerivation | None`
- `async get_figure_lock(figure_id: str) -> FigureLock | None`
- `async upsert_figure_lock(lock: FigureLock) -> None`
- `async compute_vendor_total(vendor_id: str, fiscal_year: str) -> float`
- A `db_connection()` async context manager that sets WAL and FK pragmas

---

### 24. `src/repositories/records_repo.py`

`RecordsRepo` class with standard CRUD for claims, claim support, and publication blocks.

---

### 25. `src/repositories/comms_repo.py`

`CommsRepo` class with thread and response window queries.

---

### 26. `src/services/canonical_lock_service.py`

`CanonicalLockService`:

- `validate_canon(canonical_path: Path) -> None`
- `emit_canon_hash(canonical_path: Path, runs_path: Path, run_id: str) -> CanonHash`
- `check_figure_lock(figure_id: str, computed_value: float, canon: CanonManifest) -> None`

---

### 27. `src/services/vendor_alias_resolver.py`

`VendorAliasResolver`:

- `resolve(name: str, vendor_scope: list[VendorScope]) -> VendorScope | None`
- `assert_canonical(vendor_id: str, vendor_scope: list[VendorScope]) -> VendorScope`
- `get_all_aliases(vendor_id: str, vendor_scope: list[VendorScope]) -> list[str]`

---

### 28. `src/services/scope_reconciler.py`

`ScopeReconciler`:

- `validate_article_scope(...)`
- `validate_denominator_consistency(...)`

---

### 29. `src/services/figure_verifier.py`

`FigureVerifier`:

- `async verify(figure_id: str, canon: CanonManifest, ledger: LedgerRepo) -> FigureVerificationResult`

---

### 30. `src/services/public_source_gate.py`

`PublicSourceGate`:

- `is_allowed(source_class: SourceClass, policy: SourcePolicy) -> bool`
- `filter_claims(claims: list[Claim], policy: SourcePolicy) -> list[Claim]`
- `gate_draft_context(claims: list[Claim], policy: SourcePolicy) -> list[Claim]`

---

### 31. `src/workflows/verify_figure.py`

`verify_figure` workflow:

- Input: `figure_id`, `run_id`, `settings`
- Steps: load canon → emit hash → validate → resolve scope → verify → write report
- Output: `VerificationReport`

---

### 32. `src/bridge/export_handoff.py`

`export_handoff`:

- Assembles paste-ready markdown handoff packet
- Includes: locked figures, open claims, open right-of-reply threads, pending publication blocks
- Writes to `runs/{run_id}/handoff_{article_id}.md`

---

### 33. `src/bridge/ingest_manual_draft.py`

`ingest_manual_draft`:

- Input: `markdown_text`, `article_id`, `source="webapp_export"`
- Extracts claims via simple regex/heuristic (NOT LLM)
- Creates `Claim` records with `status="pending_review"`, `public_citable=False`
- **NEVER** sets `canonical=True` or `status="verified"` automatically

---

### 34. `src/bridge/compare_dual_run.py`

`compare_dual_run`:

- Input: `run_id_a`, `run_id_b`
- Compares figure values, claim counts, pass/fail status
- Returns comparison report as markdown

---

### 35. `src/cli/main.py`

Typer CLI app with commands:

```
woodward canon validate
woodward canon hash
woodward verify figure <figure_id>
woodward bridge export [--article <id>] [--section <id>]
woodward db migrate
woodward db status
```

---

### 36. `src/core/logging.py`

Structured logging using Python `logging` + `rich`. Log level from settings. Include `run_id` in all log records when available.

---

### 37. Tests

#### Unit Tests

- `src/tests/unit/test_canonical_validation.py`
- `src/tests/unit/test_vendor_alias_resolver.py`
- `src/tests/unit/test_figure_verifier.py`
- `src/tests/unit/test_public_source_gate.py`
- `src/tests/unit/test_hashing.py`

#### Integration Tests

- `src/tests/integration/test_db_migrations.py`
- `src/tests/integration/test_verify_figure_workflow.py`

All tests must have real assertions, not stubs.

---

## Additional Notes

1. The `canonical/` YAML files are the most important deliverable. Use real locked data.
2. All Python code must target Python 3.11+. Use `from __future__ import annotations` where needed.
3. Use `uuid.uuid4()` for generating IDs in seeds/fixtures.
4. The Makefile `canon-validate` target must exit non-zero on failure.
5. The DB migration runner must: read all SQL files in order from `db/migrations/{db_name}/*.sql`, execute them, and track applied migrations in a `_migrations` table in each DB.
6. Integration tests must use `tmp_path` pytest fixture — do not write to the real `db/` directory.

---

## Start With

```
pyproject.toml
.env.example
canonical/figures.yaml
canonical/vendor_scope.yaml
```

Then proceed in order through all files listed above.
