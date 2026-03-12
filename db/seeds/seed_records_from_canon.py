#!/usr/bin/env python3
"""
seed_records_from_canon.py

Seed records.db with claims from canonical/claims_registry.yaml.

Rules:
  - Claims with status='verified' and public_citable=True are seeded as-is.
  - Claims with status='blocked' are seeded and get a corresponding publication_blocks row.
  - Uses upsert (INSERT OR REPLACE) so this script is idempotent and replayable.
  - ingest_source is set to 'canonical_seed' for all rows.

Usage:
    cd /Volumes/WD_BLACK/Desk2/Projects/WoodWard
    python3 db/seeds/seed_records_from_canon.py

Exits non-zero on any failure.
"""

import sys
import sqlite3
import uuid
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CANONICAL_DIR = PROJECT_ROOT / "canonical"
RECORDS_DB = PROJECT_ROOT / "db" / "records.db"
CLAIMS_YAML = CANONICAL_DIR / "claims_registry.yaml"


def load_claims_yaml() -> list[dict]:
    with open(CLAIMS_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("claims", [])


def run_migrations(db: sqlite3.Connection) -> None:
    """Apply any pending migrations in db/migrations/records/ before seeding."""
    migrations_dir = PROJECT_ROOT / "db" / "migrations" / "records"
    if not migrations_dir.exists():
        print(f"WARNING: migrations dir not found: {migrations_dir}")
        return

    sql_files = sorted(f for f in migrations_dir.iterdir() if f.suffix == ".sql")
    for sql_file in sql_files:
        sql = sql_file.read_text(encoding="utf-8")
        try:
            db.executescript(sql)
        except sqlite3.OperationalError as e:
            # Views may already exist — skip OperationalError on CREATE VIEW IF NOT EXISTS
            if "already exists" not in str(e).lower():
                raise
    db.commit()


def main() -> int:
    print("=== SEED RECORDS.DB FROM CANON CLAIMS REGISTRY ===")
    print(f"Canon     : {CLAIMS_YAML}")
    print(f"Records DB: {RECORDS_DB}")
    print()

    if not CLAIMS_YAML.exists():
        print(f"FATAL: claims_registry.yaml not found: {CLAIMS_YAML}")
        return 1

    RECORDS_DB.parent.mkdir(parents=True, exist_ok=True)

    claims = load_claims_yaml()
    if not claims:
        print("WARNING: No claims found in claims_registry.yaml — nothing to seed.")
        return 0

    con = sqlite3.connect(str(RECORDS_DB))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")

    # Ensure schema is up-to-date
    run_migrations(con)

    seeded = 0
    blocked_seeded = 0
    errors = 0

    for claim in claims:
        claim_id = claim.get("claim_id")
        if not claim_id:
            print(f"  SKIP: claim missing claim_id: {claim}")
            continue

        article_id = claim.get("article_id", "")
        text = claim.get("text", "")
        status = claim.get("status", "draft")
        public_citable = 1 if claim.get("public_citable", False) else 0
        support_chain_complete = 1 if claim.get("support_chain_complete", False) else 0
        right_of_reply_required = 1 if claim.get("right_of_reply_required", False) else 0
        stale = 1 if claim.get("stale", False) else 0

        try:
            con.execute(
                """
                INSERT INTO claims (
                    claim_id, article_id, text, status,
                    public_citable, support_chain_complete,
                    right_of_reply_required, stale,
                    ingest_source, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'canonical_seed', datetime('now','utc'), datetime('now','utc'))
                ON CONFLICT(claim_id) DO UPDATE SET
                    article_id              = excluded.article_id,
                    text                    = excluded.text,
                    status                  = excluded.status,
                    public_citable          = excluded.public_citable,
                    support_chain_complete  = excluded.support_chain_complete,
                    right_of_reply_required = excluded.right_of_reply_required,
                    stale                   = excluded.stale,
                    ingest_source           = excluded.ingest_source,
                    updated_at              = datetime('now','utc')
                """,
                (
                    claim_id, article_id, text, status,
                    public_citable, support_chain_complete,
                    right_of_reply_required, stale,
                ),
            )
            seeded += 1
            marker = ""

            # Seed a publication_block for blocked claims
            if status == "blocked":
                block_id = f"block_{claim_id}"
                notes_text = claim.get("notes", "") or ""
                reason = (
                    notes_text.strip()[:500]
                    if notes_text.strip()
                    else f"Canonical block for claim '{claim_id}'"
                )
                con.execute(
                    """
                    INSERT INTO publication_blocks (
                        block_id, claim_id, article_id, reason, blocking_since, resolved_at
                    )
                    VALUES (?, ?, ?, ?, datetime('now','utc'), NULL)
                    ON CONFLICT(block_id) DO NOTHING
                    """,
                    (block_id, claim_id, article_id, reason),
                )
                blocked_seeded += 1
                marker = " [BLOCKED — publication_block added]"

            print(f"  UPSERT {claim_id} (status={status}){marker}")

        except Exception as e:
            print(f"  ERROR {claim_id}: {e}")
            errors += 1

    con.commit()
    con.close()

    print()
    print(f"Results: {seeded} claims upserted | {blocked_seeded} publication_blocks seeded | {errors} errors")

    if errors > 0:
        print(f"\nERROR: {errors} claim(s) failed to seed.")
        return 1

    print("\nRecords.db seeded from canon claims registry successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
