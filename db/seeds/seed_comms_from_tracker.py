#!/usr/bin/env python3
"""
db/seeds/seed_comms_from_tracker.py

Seed comms.db with real right-of-reply correspondence data from the VPS investigation tracker.

Organizations, recipients, threads, messages, response windows, and article dependencies
are seeded from the actual investigation state as of 2026-03-12.

Rules:
  - Uses sqlite3 (seed scripts only — not runtime aiosqlite).
  - INSERT OR REPLACE for idempotent re-runs.
  - All thread statuses must match comms.db allowed values.

Usage:
    cd /Volumes/WD_BLACK/Desk2/Projects/WoodWard
    python3 db/seeds/seed_comms_from_tracker.py

Exits non-zero on any failure.
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COMMS_DB = PROJECT_ROOT / "db" / "comms.db"
MIGRATIONS_DIR = PROJECT_ROOT / "db" / "migrations" / "comms"


def run_migrations(db: sqlite3.Connection) -> None:
    """Apply comms migrations before seeding."""
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for mf in migration_files:
        sql = mf.read_text(encoding="utf-8")
        db.executescript(sql)
    db.commit()


def seed_organizations(db: sqlite3.Connection) -> None:
    rows = [
        ("vps",     "Vancouver Public Schools",              "district", None),
        ("sao",     "Washington State Auditor's Office",     "agency",   None),
        ("ospi",    "Office of Superintendent of Public Instruction", "agency", None),
        ("amergis", "Amergis Healthcare Staffing",           "other",    None),
    ]
    db.executemany(
        "INSERT OR REPLACE INTO organizations (org_id, name, org_type, notes) VALUES (?, ?, ?, ?)",
        rows,
    )
    db.commit()
    print(f"  Seeded {len(rows)} organizations.")


def seed_recipients(db: sqlite3.Connection) -> None:
    rows = [
        ("brett_blechschmidt", "vps",     "Brett Blechschmidt", "Interim Superintendent",      None, None),
        ("jeff_fish",          "vps",     "Jeff Fish",           "Executive Director of HR",    None, None),
        ("kathleen_cooper",    "sao",     "Kathleen Cooper",     "Director of Communications",  None, None),
        ("shawn_lewis",        "ospi",    "Shawn Lewis",         "Director of SAFS",            None, None),
        ("katie_arkoosh",      "vps",     "Katie Arkoosh",       "Board Member",                None, None),
    ]
    db.executemany(
        "INSERT OR REPLACE INTO recipients "
        "(recipient_id, org_id, name, role, email, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    db.commit()
    print(f"  Seeded {len(rows)} recipients.")


def seed_threads(db: sqlite3.Connection) -> None:
    # statuses must be in: open | awaiting_response | responded | closed | publication_blocked
    rows = [
        (
            "vps_ror_feb27",
            "brett_blechschmidt",
            "Right of Reply — VPS Staffing Vendor Spending",
            "closed",   # no_response maps to closed (no further action expected)
        ),
        (
            "sao_cooper",
            "kathleen_cooper",
            "Oversight Concern — VPS Vendor Spending Controls",
            "awaiting_response",
        ),
        (
            "ospi_lewis",
            "shawn_lewis",
            "VPS Emergency Borrowing Inquiry",
            "responded",
        ),
    ]
    db.executemany(
        "INSERT OR REPLACE INTO threads "
        "(thread_id, recipient_id, subject, status) "
        "VALUES (?, ?, ?, ?)",
        rows,
    )
    db.commit()
    print(f"  Seeded {len(rows)} threads.")


def seed_messages(db: sqlite3.Connection) -> None:
    rows = [
        # sao_cooper thread: outbound ~March 1, inbound response ~March 3
        (
            "msg_sao_cooper_out_1",
            "sao_cooper",
            "outbound",
            (
                "I am reaching out regarding oversight concerns about Vancouver Public Schools' "
                "staffing vendor spending. VPS paid approximately $10.97 million to Amergis Healthcare "
                "(formerly Maxim Healthcare) in FY2024-25, against a board-approved estimate of ~$3 million. "
                "I am requesting comment and information about any ongoing or planned SAO review of "
                "VPS vendor spending controls."
            ),
            "2026-03-01T09:00:00",
            "Initial outreach to SAO communications director.",
        ),
        (
            "msg_sao_cooper_in_1",
            "sao_cooper",
            "inbound",
            'Asked: "Are you a reporter? If so, for what outlet?"',
            "2026-03-03T14:22:00",
            "Cooper's reply — has not confirmed whether investigation is underway.",
        ),
        # ospi_lewis thread: responded ~March 2
        (
            "msg_ospi_lewis_out_1",
            "ospi_lewis",
            "outbound",
            (
                "I am inquiring about the emergency borrowing request submitted by Vancouver Public Schools "
                "for FY2024-25. Specifically: the amount VPS requested, the amount OSPI approved, "
                "and any conditions placed on the approval."
            ),
            "2026-02-28T10:00:00",
            "Initial inquiry on emergency advance.",
        ),
        (
            "msg_ospi_lewis_in_1",
            "ospi_lewis",
            "inbound",
            (
                "Confirmed: VPS requested $21,367,552. OSPI approved $8.7 million. "
                "Approval was conditional on VPS's submitted repayment plan."
            ),
            "2026-03-02T11:45:00",
            "Shawn Lewis confirmed advance amounts on record.",
        ),
    ]
    db.executemany(
        "INSERT OR REPLACE INTO messages "
        "(msg_id, thread_id, direction, content, sent_at, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    db.commit()
    print(f"  Seeded {len(rows)} messages.")


def seed_response_windows(db: sqlite3.Connection) -> None:
    rows = [
        # sao_cooper is publication-blocking — awaiting response
        (
            "rw_sao_cooper_1",
            "sao_cooper",
            "2026-03-20",
            "open",
            1,   # publication_blocking = True
        ),
    ]
    db.executemany(
        "INSERT OR REPLACE INTO response_windows "
        "(window_id, thread_id, deadline, status, publication_blocking) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    db.commit()
    print(f"  Seeded {len(rows)} response windows.")


def seed_article_dependencies(db: sqlite3.Connection) -> None:
    rows = [
        # article_1: claim_amergis_no_spending_cap depends on sao_cooper thread — unresolved
        (
            "dep_art1_sao_cooper_amergis_cap",
            "article_1",
            "sao_cooper",
            "claim_amergis_no_spending_cap",
            "right_of_reply",
            0,
        ),
        # article_2: claim_board_approved_3m depends on sao_cooper thread — unresolved
        (
            "dep_art2_sao_cooper_board",
            "article_2",
            "sao_cooper",
            "claim_board_approved_3m",
            "right_of_reply",
            0,
        ),
    ]
    db.executemany(
        "INSERT OR REPLACE INTO article_dependencies "
        "(dep_id, article_id, thread_id, claim_id, dependency_type, resolved) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    db.commit()
    print(f"  Seeded {len(rows)} article dependencies.")


def main() -> None:
    if not COMMS_DB.parent.exists():
        print(f"ERROR: DB directory does not exist: {COMMS_DB.parent}", file=sys.stderr)
        sys.exit(1)

    print(f"Seeding comms.db at: {COMMS_DB}")

    db = sqlite3.connect(str(COMMS_DB))
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")

    try:
        run_migrations(db)
        print("  Migrations applied.")

        seed_organizations(db)
        seed_recipients(db)
        seed_threads(db)
        seed_messages(db)
        seed_response_windows(db)
        seed_article_dependencies(db)

        # Summary
        counts = {}
        for table in [
            "organizations", "recipients", "threads", "messages",
            "response_windows", "article_dependencies",
        ]:
            row = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0]

        print("\n  Final table counts:")
        for table, count in counts.items():
            print(f"    {table}: {count}")

        print("\ncomms.db seeded successfully.")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        db.close()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
