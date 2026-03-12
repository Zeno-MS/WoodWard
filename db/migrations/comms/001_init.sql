-- comms/001_init.sql
-- Initial schema for comms.db
-- Tracks outreach, right-of-reply correspondence, response windows,
-- and article publication dependencies.

CREATE TABLE IF NOT EXISTS _migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    checksum TEXT
);

-- Organizations contacted (VPS, OSPI, Amergis, SAO, media outlets, etc.)
CREATE TABLE IF NOT EXISTS organizations (
    org_id      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    org_type    TEXT,   -- 'district' | 'agency' | 'media' | 'union' | 'advocacy' | 'government' | 'other'
    notes       TEXT
);

CREATE INDEX IF NOT EXISTS idx_orgs_type ON organizations(org_type);

-- Individual recipients within organizations
CREATE TABLE IF NOT EXISTS recipients (
    recipient_id    TEXT PRIMARY KEY,
    org_id          TEXT REFERENCES organizations(org_id),
    name            TEXT,
    role            TEXT,
    email           TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_recipients_org ON recipients(org_id);

-- Question sets — structured right-of-reply questions per article
CREATE TABLE IF NOT EXISTS question_sets (
    qset_id     TEXT PRIMARY KEY,
    article_id  TEXT,
    questions   TEXT,   -- JSON array of question strings
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_qsets_article ON question_sets(article_id);

-- Correspondence threads (one per contact/subject combination)
CREATE TABLE IF NOT EXISTS threads (
    thread_id       TEXT PRIMARY KEY,
    recipient_id    TEXT REFERENCES recipients(recipient_id),
    subject         TEXT,
    status          TEXT,   -- open | awaiting_response | responded | closed | publication_blocked
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status);
CREATE INDEX IF NOT EXISTS idx_threads_recipient ON threads(recipient_id);

-- Trigger to auto-update threads.updated_at
CREATE TRIGGER IF NOT EXISTS threads_updated_at
    AFTER UPDATE ON threads
    FOR EACH ROW
    BEGIN
        UPDATE threads SET updated_at = datetime('now', 'utc') WHERE thread_id = NEW.thread_id;
    END;

-- Individual messages within a thread
CREATE TABLE IF NOT EXISTS messages (
    msg_id      TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL REFERENCES threads(thread_id) ON DELETE CASCADE,
    direction   TEXT,   -- 'outbound' | 'inbound' | 'internal'
    content     TEXT,
    sent_at     TEXT,
    notes       TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);

-- Response windows — deadlines for receiving a reply before publication
CREATE TABLE IF NOT EXISTS response_windows (
    window_id               TEXT PRIMARY KEY,
    thread_id               TEXT NOT NULL REFERENCES threads(thread_id) ON DELETE CASCADE,
    deadline                TEXT,
    status                  TEXT,   -- open | expired | responded | waived
    publication_blocking    INTEGER NOT NULL DEFAULT 0  -- 0=False, 1=True
);

CREATE INDEX IF NOT EXISTS idx_response_windows_thread ON response_windows(thread_id);
CREATE INDEX IF NOT EXISTS idx_response_windows_blocking
    ON response_windows(publication_blocking)
    WHERE publication_blocking = 1;

-- Article dependencies — links specific claims/articles to required thread resolutions
-- A resolved=0 dependency with a publication_blocking response window
-- must stop article assembly.
CREATE TABLE IF NOT EXISTS article_dependencies (
    dep_id              TEXT PRIMARY KEY,
    article_id          TEXT,
    thread_id           TEXT REFERENCES threads(thread_id),
    claim_id            TEXT,
    dependency_type     TEXT,   -- 'right_of_reply' | 'public_records_response' | 'agency_confirmation' | 'editorial_approval'
    resolved            INTEGER NOT NULL DEFAULT 0  -- 0=False, 1=True
);

CREATE INDEX IF NOT EXISTS idx_article_deps_article ON article_dependencies(article_id);
CREATE INDEX IF NOT EXISTS idx_article_deps_unresolved ON article_dependencies(resolved)
    WHERE resolved = 0;
