-- records/001_init.sql
-- Initial schema for records.db
-- Stores public documents, text chunks, claims, support chains, and publication blocks.

CREATE TABLE IF NOT EXISTS _migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    checksum TEXT
);

-- Public documents ingested for the investigation
CREATE TABLE IF NOT EXISTS documents (
    doc_id          TEXT PRIMARY KEY,
    title           TEXT,
    doc_type        TEXT,   -- 'board_minutes', 'ospi_report', 'news_article', 'contract', etc.
    source_class    TEXT,   -- maps to source_policy.yaml classes
    file_path       TEXT,
    date            TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_source_class ON documents(source_class);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);

-- Text chunks extracted from documents (for retrieval)
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,
    doc_id          TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    embedding_id    TEXT,   -- reference to LanceDB entry (not stored here)
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);

-- Claims — the atomic units of publishable assertions
CREATE TABLE IF NOT EXISTS claims (
    claim_id                TEXT PRIMARY KEY,
    article_id              TEXT,
    text                    TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'draft',
                            -- draft | verified | blocked | superseded | pending_review
    public_citable          INTEGER NOT NULL DEFAULT 0,  -- 0=False, 1=True
    support_chain_complete  INTEGER NOT NULL DEFAULT 0,
    right_of_reply_required INTEGER NOT NULL DEFAULT 0,
    stale                   INTEGER NOT NULL DEFAULT 0,
    ingest_source           TEXT,  -- 'canonical_seed', 'webapp_export', 'manual', etc.
    created_at              TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at              TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    CHECK(status IN ('draft', 'verified', 'blocked', 'superseded', 'pending_review')),
    -- A blocked claim cannot be public_citable
    CHECK(NOT (status = 'blocked' AND public_citable = 1))
);

CREATE INDEX IF NOT EXISTS idx_claims_article ON claims(article_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_public_citable ON claims(public_citable);

-- Trigger to auto-update updated_at on any claims change
CREATE TRIGGER IF NOT EXISTS claims_updated_at
    AFTER UPDATE ON claims
    FOR EACH ROW
    BEGIN
        UPDATE claims SET updated_at = datetime('now', 'utc') WHERE claim_id = NEW.claim_id;
    END;

-- Support chains — links claims to their public-citable document evidence
CREATE TABLE IF NOT EXISTS claim_support (
    support_id      TEXT PRIMARY KEY,
    claim_id        TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    doc_id          TEXT REFERENCES documents(doc_id),
    chunk_id        TEXT REFERENCES chunks(chunk_id),
    quote           TEXT,   -- exact quote from the source document
    support_type    TEXT,   -- 'direct_quote' | 'paraphrase' | 'figure_reference' | 'context'
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_claim_support_claim ON claim_support(claim_id);

-- Publication blocks — explicit blocks on publishing a claim in an article
CREATE TABLE IF NOT EXISTS publication_blocks (
    block_id        TEXT PRIMARY KEY,
    claim_id        TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    article_id      TEXT,
    reason          TEXT NOT NULL,
    blocking_since  TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    resolved_at     TEXT    -- NULL means still active
);

CREATE INDEX IF NOT EXISTS idx_pub_blocks_claim ON publication_blocks(claim_id);
CREATE INDEX IF NOT EXISTS idx_pub_blocks_article ON publication_blocks(article_id);
CREATE INDEX IF NOT EXISTS idx_pub_blocks_active ON publication_blocks(resolved_at)
    WHERE resolved_at IS NULL;
