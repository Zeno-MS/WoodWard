-- ledger/001_init.sql
-- Initial schema for ledger.db — the sole monetary source of truth.
-- All dollar figures for publication must originate here.
-- Uses WAL mode and foreign keys (set at connection time, not here).

-- Migration tracking table (created in every db)
CREATE TABLE IF NOT EXISTS _migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    checksum TEXT
);

-- Core vendor registry
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id   TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Vendor name aliases (for deduplication and historical rebrand tracking)
CREATE TABLE IF NOT EXISTS vendor_aliases (
    alias_id        TEXT PRIMARY KEY,
    vendor_id       TEXT NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    alias           TEXT NOT NULL,
    effective_from  TEXT,
    effective_to    TEXT,
    UNIQUE(vendor_id, alias)
);

CREATE INDEX IF NOT EXISTS idx_vendor_aliases_alias ON vendor_aliases(alias);

-- Source documents (warrant register PDFs, OSPI reports, board minutes, etc.)
CREATE TABLE IF NOT EXISTS source_documents (
    doc_id          TEXT PRIMARY KEY,
    title           TEXT,
    doc_type        TEXT,   -- 'warrant_register', 'board_minutes', 'ospi_f195', etc.
    fiscal_year     TEXT,
    source_class    TEXT,   -- maps to source_policy.yaml classes
    file_path       TEXT,
    url             TEXT,
    date_acquired   TEXT,
    notes           TEXT
);

-- Individual payment records (warrant-level granularity)
CREATE TABLE IF NOT EXISTS payments (
    payment_id      TEXT PRIMARY KEY,
    vendor_id       TEXT NOT NULL REFERENCES vendors(vendor_id),
    amount          REAL NOT NULL CHECK(amount >= 0),
    fiscal_year     TEXT NOT NULL,
    payment_date    TEXT,
    warrant_number  TEXT,
    doc_id          TEXT REFERENCES source_documents(doc_id),
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_payments_vendor_fy ON payments(vendor_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_payments_fiscal_year ON payments(fiscal_year);

-- Pre-computed fiscal year rollups (sum of payments per vendor per year)
-- These are the authoritative aggregated figures used in publication.
CREATE TABLE IF NOT EXISTS fiscal_rollups (
    rollup_id       TEXT PRIMARY KEY,
    vendor_id       TEXT NOT NULL REFERENCES vendors(vendor_id),
    fiscal_year     TEXT NOT NULL,
    total_amount    REAL NOT NULL CHECK(total_amount >= 0),
    payment_count   INTEGER,
    source_doc_ids  TEXT,   -- JSON array of doc_ids that contributed to this rollup
    computed_at     TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    UNIQUE(vendor_id, fiscal_year)
);

CREATE INDEX IF NOT EXISTS idx_fiscal_rollups_vendor ON fiscal_rollups(vendor_id);
CREATE INDEX IF NOT EXISTS idx_fiscal_rollups_fy ON fiscal_rollups(fiscal_year);

-- Figure derivation records — prove how locked figures were computed
-- sql_query must be replayable against this database to reproduce computed_value
CREATE TABLE IF NOT EXISTS figure_derivations (
    derivation_id   TEXT PRIMARY KEY,
    figure_id       TEXT NOT NULL,
    sql_query       TEXT NOT NULL,   -- the exact SQL used to compute the value
    computed_value  REAL,
    canonical_value REAL,
    status          TEXT DEFAULT 'pending',  -- pending | computed | verified | mismatch
    computed_at     TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_figure_derivations_figure ON figure_derivations(figure_id);

-- Figure locks — one row per locked figure, matched to canon/figures.yaml
-- A lock failure at run time is a hard-stop build error.
CREATE TABLE IF NOT EXISTS figure_locks (
    lock_id         TEXT PRIMARY KEY,
    figure_id       TEXT NOT NULL UNIQUE,
    locked_value    REAL NOT NULL CHECK(locked_value >= 0),
    locked_at       TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    locked_by       TEXT,   -- 'woodward-core-v2' or run_id
    canon_hash      TEXT    -- combined_hash from CanonHash at time of lock
);

-- Deduplication audit trail (for warrant register processing)
CREATE TABLE IF NOT EXISTS dedup_audit (
    audit_id        TEXT PRIMARY KEY,
    source          TEXT,   -- 'warrant_register_all_years', etc.
    total_records   INTEGER,
    dedup_records   INTEGER,
    method          TEXT,   -- 'warrant_number_exact', 'composite_key', etc.
    run_at          TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);
