#!/usr/bin/env python3
"""
seed_ledger_from_source.py

Seeds ledger.db from the source woodward.db.
- Connects read-only to woodward.db
- Runs migrations to create ledger.db if needed
- Seeds vendors, aliases, payments (deduplicated), fiscal_rollups, source_documents,
  figure_derivations, and figure_locks
- Prints a summary at the end

Run from WoodWard project root:
    python3 db/seeds/seed_ledger_from_source.py
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # WoodWard/
SOURCE_DB = PROJECT_ROOT / "VPS_Investigation_Evidence" / "00_Data_Corpus" / "woodward.db"
MIGRATION_SQL = PROJECT_ROOT / "db" / "migrations" / "ledger" / "001_init.sql"
TARGET_DB = PROJECT_ROOT / "db" / "ledger.db"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def iso_date(d: str) -> str | None:
    """Convert MM/DD/YYYY or MM/DD/YY to YYYY-MM-DD. Returns None on bad input."""
    if not d:
        return None
    d = d.strip()
    if len(d) == 10:
        # MM/DD/YYYY
        return f"{d[6:10]}-{d[0:2]}-{d[3:5]}"
    elif len(d) == 8:
        # MM/DD/YY
        return f"20{d[6:8]}-{d[0:2]}-{d[3:5]}"
    return None


def fiscal_year_label(iso: str) -> str | None:
    """Return 'FYXXXX-XX' label for an ISO date string based on Sept 1 cutoff."""
    if not iso or len(iso) < 7:
        return None
    year = int(iso[0:4])
    month = int(iso[5:7])
    if month >= 9:
        fy_start = year
        fy_end = year + 1
    else:
        fy_start = year - 1
        fy_end = year
    return f"FY{fy_start}-{str(fy_end)[2:]}"


def make_id(*parts) -> str:
    """Create a deterministic short ID from parts."""
    raw = "_".join(str(p) for p in parts)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Vendor definitions
# ---------------------------------------------------------------------------
VENDORS = [
    ("amergis",         "AMERGIS HEALTHCARE STAFFING INC"),
    ("maxim",           "MAXIM HEALTHCARE SERVICES INC"),
    ("procare",         "PROCARE THERAPY"),
    ("soliant",         "SOLIANT HEALTH LLC"),
    ("pioneer",         "PIONEER HEALTHCARE SERVICES LLC"),
    ("aveanna",         "AVEANNA HEALTHCARE"),
    ("stepping_stones", "THE STEPPING STONES GROUP LLC"),
]

# All known payee name variants in woodward.db → vendor_id
VENDOR_ALIASES = {
    "amergis": [
        "AMERGIS HEALTHCARE STAFFING INC",
        "Amergis Healthcare Staffing Inc",
        "AMERGIS HEALTHCARE",
    ],
    "maxim": [
        "MAXIM HEALTHCARE SERVICES INC",
        "Maxim Healthcare Services Inc",
        "MAXIM HEALTHCARE",
        "Maxim Healthcare Services",
    ],
    "procare": [
        "PROCARE THERAPY",
        "ProCare Therapy",
        "Procare Therapy",
        "PROCARE THERAPY INC",
    ],
    "soliant": [
        "SOLIANT HEALTH LLC",
        "Soliant Health LLC",
        "SOLIANT HEALTH",
        "Soliant Health",
    ],
    "pioneer": [
        "PIONEER HEALTHCARE SERVICES LLC",
        "Pioneer Healthcare Services LLC",
        "PIONEER HEALTHCARE",
        "Pioneer Healthcare",
    ],
    "aveanna": [
        "AVEANNA HEALTHCARE",
        "Aveanna Healthcare",
        "AVEANNA HEALTHCARE LLC",
    ],
    "stepping_stones": [
        "THE STEPPING STONES GROUP LLC",
        "Stepping Stones Group",
        "STEPPING STONES GROUP",
        "The Stepping Stones Group LLC",
        "THE STEPPING STONES GROUP",
    ],
}

# Build a lookup: exact_upper_payee → vendor_id
PAYEE_TO_VENDOR = {}
for vid, aliases in VENDOR_ALIASES.items():
    for alias in aliases:
        PAYEE_TO_VENDOR[alias.upper()] = vid


# ---------------------------------------------------------------------------
# Source documents
# ---------------------------------------------------------------------------
SOURCE_DOCUMENTS = [
    {
        "doc_id": "vendor_summary_by_year_csv",
        "title": "VPS Vendor Summary by Year",
        "doc_type": "payment_summary",
        "fiscal_year": "FY2020-21 through FY2025-26",
        "source_class": "public_record",
        "file_path": "VPS_Investigation_Evidence/01_Payment_Data/vendor_summary_by_year.csv",
        "url": None,
        "date_acquired": "2026-02-01",
        "notes": "Canonical CSV reconciliation of vendor payments by fiscal year. Grand total $32,189,236 includes FY25-26 partial.",
    },
    {
        "doc_id": "board_minutes_july_9_2024",
        "title": "VPS Board Meeting Minutes July 9 2024 - Amergis Approval",
        "doc_type": "board_minutes",
        "fiscal_year": "FY2024-25",
        "source_class": "public_record",
        "file_path": "VPS_Investigation_Evidence/05_Source_Documents/Board_Minutes_July_9_2024_Amergis_Approval.pdf",
        "url": None,
        "date_acquired": "2026-02-01",
        "notes": "Amergis contract approved as consent agenda item. Stated approximate cost ~$3,000,000.",
    },
    {
        "doc_id": "ospi_response_shawn_lewis",
        "title": "OSPI Response - Shawn Lewis SAFS Director - Financial Advance",
        "doc_type": "ospi_correspondence",
        "fiscal_year": "FY2024-25",
        "source_class": "public_record",
        "file_path": "VPS_Investigation_Evidence/05_Source_Documents/OSPI_Shawn_Lewis_Response.pdf",
        "url": None,
        "date_acquired": "2026-02-01",
        "notes": "Confirms VPS requested $21,367,552 state financial advance; $8,700,000 approved. Source: Shawn Lewis, Director of SAFS.",
    },
    {
        "doc_id": "vps_f195_fy2425",
        "title": "VPS F-195 Financial Report FY2024-25",
        "doc_type": "ospi_f195",
        "fiscal_year": "FY2024-25",
        "source_class": "public_record",
        "file_path": "VPS_Investigation_Evidence/05_Source_Documents/VPS_2024-25_F-195.pdf",
        "url": None,
        "date_acquired": "2026-02-01",
        "notes": "OSPI F-195 financial report. Object 5 (Purchased Services) budget $36,738,206; actual $47,331,056.",
    },
]


# ---------------------------------------------------------------------------
# Figure derivations (9 locked figures)
# ---------------------------------------------------------------------------
# SQL queries run against SOURCE woodward.db (woodward.db)
# For non-SQL figures, sql_query is '' and derivation_source is noted.

FIGURE_DERIVATIONS = [
    {
        "derivation_id": "deriv_fy2425_staffing_total",
        "figure_id": "fy2425_staffing_vendor_total",
        "canonical_value": 13326622.0,
        "sql_query": (
            "WITH deduped AS ("
            "SELECT DISTINCT payee, document_date, amount FROM payments "
            "WHERE upper(payee) IN ('AMERGIS HEALTHCARE STAFFING INC','MAXIM HEALTHCARE SERVICES INC') "
            "OR upper(payee) LIKE '%PROCARE%' "
            "OR upper(payee) LIKE '%SOLIANT%' "
            "OR upper(payee) LIKE '%PIONEER HEALTHCARE SERVICES%'"
            "), parsed AS ("
            "SELECT amount, "
            "CASE WHEN length(document_date)=10 THEN substr(document_date,7,4)||'-'||substr(document_date,1,2)||'-'||substr(document_date,4,2) "
            "WHEN length(document_date)=8 THEN '20'||substr(document_date,7,2)||'-'||substr(document_date,1,2)||'-'||substr(document_date,4,2) "
            "END as iso_date FROM deduped"
            ") SELECT SUM(amount) FROM parsed WHERE iso_date >= '2024-09-01' AND iso_date <= '2025-08-31'"
        ),
        "notes": (
            "Primary 5 staffing vendors FY24-25 (Sept 1 2024 - Aug 31 2025). "
            "Payees: Amergis, Maxim, ProCare, Soliant, Pioneer Healthcare Services. "
            "Excludes Aveanna and Stepping Stones per vendor_scope.yaml. "
            "Deduplication: DISTINCT on (payee, document_date, amount)."
        ),
    },
    {
        "derivation_id": "deriv_amergis_fy2425",
        "figure_id": "amergis_fy2425_total",
        "canonical_value": 10970973.0,
        "sql_query": (
            "WITH deduped AS ("
            "SELECT DISTINCT payee, document_date, amount FROM payments "
            "WHERE upper(payee) LIKE '%AMERGIS%'"
            "), parsed AS ("
            "SELECT amount, "
            "CASE WHEN length(document_date)=10 THEN substr(document_date,7,4)||'-'||substr(document_date,1,2)||'-'||substr(document_date,4,2) "
            "WHEN length(document_date)=8 THEN '20'||substr(document_date,7,2)||'-'||substr(document_date,1,2)||'-'||substr(document_date,4,2) "
            "END as iso_date FROM deduped"
            ") SELECT SUM(amount) FROM parsed WHERE iso_date >= '2024-09-01' AND iso_date <= '2025-08-31'"
        ),
        "notes": (
            "Total paid to Amergis Healthcare (payee LIKE '%AMERGIS%') in FY24-25. "
            "Represents 82.3% of $13,326,622 staffing vendor total. "
            "366% above board-approved $3M estimate (July 9, 2024 consent agenda)."
        ),
    },
    {
        "derivation_id": "deriv_cumulative_5vendor",
        "figure_id": "cumulative_staffing_baseline",
        "canonical_value": 32189236.0,
        "sql_query": "",  # CSV source — DB total through FY24-25 is $28,728,737; FY25-26 partial in CSV
        "notes": (
            "Canonical value $32,189,236 sourced from vendor_summary_by_year_csv Grand Total row. "
            "Includes FY2025-26 partial. "
            "DB-only total through FY2024-25 (5-vendor deduped): $28,728,737. "
            "derivation_source='vendor_summary_by_year_csv'. "
            "SQL over source DB returns $32,319,347 (all years, includes Pioneer Trust Bank which is NOT Pioneer Healthcare Services). "
            "canonical_value matches CSV which uses cleaner vendor disambiguation."
        ),
    },
    {
        "derivation_id": "deriv_obj7_budget_fy2425",
        "figure_id": "object7_budget_fy2425",
        "canonical_value": 36738206.0,
        "sql_query": (
            "SELECT bi.amount FROM budget_items bi "
            "JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id "
            "JOIN budget_objects bo ON bi.object_id = bo.id "
            "WHERE fy.year_label = '2024-2025' AND bo.object_code = 5 AND bi.scope = 'BUDGETED'"
        ),
        "notes": (
            "VPS adopted budget for Object 5 (Purchased Services) FY2024-25. "
            "Note: In woodward.db, object_code=5 is 'Purchased Services' (not Object 7 as labeled in F-195). "
            "The figure matches $36,738,206 from OSPI F-195 report. "
            "Source document: vps_f195_fy2425. scope='BUDGETED' in budget_items table."
        ),
    },
    {
        "derivation_id": "deriv_obj7_actual_fy2425",
        "figure_id": "object7_actual_fy2425",
        "canonical_value": 47331056.0,
        "sql_query": "",  # No SPENT row in budget_items for FY24-25 — sourced from F-195 report
        "notes": (
            "VPS actual spending in Object 5/7 (Purchased Services) FY2024-25 = $47,331,056. "
            "Source: OSPI F-195 financial report (vps_f195_fy2425). "
            "No SPENT row exists in woodward.db budget_items for FY24-25 — most recent SPENT data is FY23-24. "
            "derivation_source='vps_f195_fy2425'. "
            "Staffing vendors represent 28.16% of this total ($13,326,622 / $47,331,056)."
        ),
    },
    {
        "derivation_id": "deriv_obj7_overage_fy2425",
        "figure_id": "object7_overage_fy2425",
        "canonical_value": 10592850.0,
        "sql_query": "",  # Computed as actual - budget
        "notes": (
            "Derived: object7_actual_fy2425 ($47,331,056) minus object7_budget_fy2425 ($36,738,206) = $10,592,850. "
            "References derivations deriv_obj7_actual_fy2425 and deriv_obj7_budget_fy2425. "
            "DENOMINATOR WARNING: do not combine with staffing_vendor_total without explicit disclosure."
        ),
    },
    {
        "derivation_id": "deriv_board_estimate_july2024",
        "figure_id": "board_amergis_estimate_july2024",
        "canonical_value": 3000000.0,
        "sql_query": "",  # Public document source
        "notes": (
            "Board approved Amergis contract on July 9, 2024 consent agenda with approximate cost ~$3,000,000. "
            "derivation_source='board_minutes_july_9_2024'. "
            "Actual FY24-25 spending was $10,970,973 — 366% variance. "
            "The tilde prefix in display_value (~$3,000,000) is intentional per source language."
        ),
    },
    {
        "derivation_id": "deriv_ospi_advance_requested",
        "figure_id": "ospi_advance_requested",
        "canonical_value": 21367552.0,
        "sql_query": "",  # Public document source
        "notes": (
            "Amount requested by VPS from OSPI as a state financial advance. "
            "Confirmed by Shawn Lewis, OSPI Director of School Apportionment and Financial Services (SAFS). "
            "derivation_source='ospi_response_shawn_lewis'."
        ),
    },
    {
        "derivation_id": "deriv_ospi_advance_approved",
        "figure_id": "ospi_advance_approved",
        "canonical_value": 8700000.0,
        "sql_query": "",  # Public document source
        "notes": (
            "Amount approved by OSPI for state financial advance. "
            "Confirmed by Shawn Lewis, OSPI Director of SAFS. "
            "Represents 40.7% of the $21,367,552 requested. "
            "derivation_source='ospi_response_shawn_lewis'."
        ),
    },
]


# ---------------------------------------------------------------------------
# Fiscal year ranges (Sept 1 - Aug 31)
# ---------------------------------------------------------------------------
FISCAL_YEARS = [
    ("FY2020-21", "2020-09-01", "2021-08-31"),
    ("FY2021-22", "2021-09-01", "2022-08-31"),
    ("FY2022-23", "2022-09-01", "2023-08-31"),
    ("FY2023-24", "2023-09-01", "2024-08-31"),
    ("FY2024-25", "2024-09-01", "2025-08-31"),
    ("FY2025-26", "2025-09-01", "2026-08-31"),
]


# ---------------------------------------------------------------------------
# Main seed logic
# ---------------------------------------------------------------------------
def run_migrations(tgt: sqlite3.Connection) -> None:
    """Run ledger/001_init.sql if not already applied."""
    tgt.execute("CREATE TABLE IF NOT EXISTS _migrations (migration_id TEXT PRIMARY KEY, applied_at TEXT, checksum TEXT)")
    tgt.commit()
    cur = tgt.execute("SELECT migration_id FROM _migrations WHERE migration_id='ledger/001_init'")
    if cur.fetchone():
        print("  Migration ledger/001_init already applied — skipping.")
        return
    sql = MIGRATION_SQL.read_text()
    tgt.executescript(sql)
    checksum = hashlib.sha256(sql.encode()).hexdigest()[:16]
    tgt.execute(
        "INSERT INTO _migrations(migration_id, applied_at, checksum) VALUES (?,?,?)",
        ("ledger/001_init", now_utc(), checksum),
    )
    tgt.commit()
    print("  Migration ledger/001_init applied.")


def seed_vendors(tgt: sqlite3.Connection) -> int:
    count = 0
    for vid, name in VENDORS:
        tgt.execute(
            "INSERT OR IGNORE INTO vendors(vendor_id, canonical_name) VALUES (?,?)",
            (vid, name),
        )
        if tgt.execute("SELECT changes()").fetchone()[0]:
            count += 1
    tgt.commit()
    return count


def seed_vendor_aliases(tgt: sqlite3.Connection) -> int:
    count = 0
    for vid, aliases in VENDOR_ALIASES.items():
        for alias in aliases:
            alias_id = make_id("alias", vid, alias)
            tgt.execute(
                "INSERT OR IGNORE INTO vendor_aliases(alias_id, vendor_id, alias) VALUES (?,?,?)",
                (alias_id, vid, alias),
            )
            if tgt.execute("SELECT changes()").fetchone()[0]:
                count += 1
    tgt.commit()
    return count


def seed_source_documents(tgt: sqlite3.Connection) -> int:
    count = 0
    for doc in SOURCE_DOCUMENTS:
        tgt.execute(
            """INSERT OR IGNORE INTO source_documents
               (doc_id, title, doc_type, fiscal_year, source_class, file_path, url, date_acquired, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                doc["doc_id"], doc["title"], doc["doc_type"], doc["fiscal_year"],
                doc["source_class"], doc["file_path"], doc.get("url"), doc.get("date_acquired"), doc.get("notes"),
            ),
        )
        if tgt.execute("SELECT changes()").fetchone()[0]:
            count += 1
    tgt.commit()
    return count


def seed_payments(src: sqlite3.Connection, tgt: sqlite3.Connection) -> tuple[int, int]:
    """Copy deduplicated payments from source. Returns (inserted, skipped)."""
    cur = src.execute("SELECT DISTINCT payee, document_date, amount FROM payments")
    rows = cur.fetchall()

    inserted = 0
    skipped = 0
    ts = now_utc()

    for payee, doc_date, amount in rows:
        vid = PAYEE_TO_VENDOR.get(payee.upper() if payee else "")
        if vid is None:
            skipped += 1
            continue

        iso = iso_date(doc_date)
        if iso is None:
            skipped += 1
            continue

        fy = fiscal_year_label(iso)
        if fy is None:
            skipped += 1
            continue

        payment_id = make_id("pay", payee, doc_date, amount)
        tgt.execute(
            """INSERT OR IGNORE INTO payments(payment_id, vendor_id, amount, fiscal_year, payment_date)
               VALUES (?,?,?,?,?)""",
            (payment_id, vid, amount, fy, iso),
        )
        if tgt.execute("SELECT changes()").fetchone()[0]:
            inserted += 1

    tgt.commit()
    return inserted, skipped


def seed_fiscal_rollups(tgt: sqlite3.Connection) -> int:
    """Compute and insert fiscal_rollups from payments table in ledger.db."""
    # Delete existing rollups first (idempotent re-seed)
    tgt.execute("DELETE FROM fiscal_rollups")
    tgt.commit()

    cur = tgt.execute(
        """SELECT vendor_id, fiscal_year, SUM(amount), COUNT(*)
           FROM payments
           GROUP BY vendor_id, fiscal_year"""
    )
    rows = cur.fetchall()

    count = 0
    ts = now_utc()
    for vid, fy, total, n in rows:
        rollup_id = make_id("rollup", vid, fy)
        tgt.execute(
            """INSERT OR REPLACE INTO fiscal_rollups
               (rollup_id, vendor_id, fiscal_year, total_amount, payment_count, computed_at)
               VALUES (?,?,?,?,?,?)""",
            (rollup_id, vid, fy, total, n, ts),
        )
        count += 1

    tgt.commit()
    return count


def compute_derivation_value(src: sqlite3.Connection, sql: str) -> float | None:
    """Run sql against source DB and return scalar result."""
    if not sql:
        return None
    try:
        cur = src.execute(sql)
        row = cur.fetchone()
        if row and row[0] is not None:
            return float(row[0])
    except Exception as e:
        print(f"    WARNING: SQL execution error: {e}")
    return None


def seed_figure_derivations(src: sqlite3.Connection, tgt: sqlite3.Connection) -> tuple[int, int, int]:
    """Seed figure_derivations. Returns (total, verified, mismatches)."""
    verified = 0
    mismatches = 0
    ts = now_utc()

    for deriv in FIGURE_DERIVATIONS:
        sql = deriv["sql_query"]
        canonical = deriv["canonical_value"]

        computed = compute_derivation_value(src, sql) if sql else None

        if computed is not None:
            diff = abs(computed - canonical)
            if diff <= 1.0:
                status = "verified"
                verified += 1
                print(f"    VERIFIED: {deriv['derivation_id']} — computed={computed:,.2f} canonical={canonical:,.0f} diff={diff:.2f}")
            else:
                status = "mismatch"
                mismatches += 1
                print(f"    MISMATCH: {deriv['derivation_id']} — computed={computed:,.2f} canonical={canonical:,.0f} diff={diff:.2f}")
        else:
            # No SQL — document-sourced figure
            status = "csv_source" if "csv" in deriv["notes"].lower() else "doc_source"
            print(f"    DOC SOURCE: {deriv['derivation_id']} — canonical={canonical:,.0f} (no SQL)")

        tgt.execute(
            """INSERT OR REPLACE INTO figure_derivations
               (derivation_id, figure_id, sql_query, computed_value, canonical_value, status, computed_at, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                deriv["derivation_id"],
                deriv["figure_id"],
                sql,
                computed,
                canonical,
                status,
                ts,
                deriv["notes"],
            ),
        )

    tgt.commit()
    return len(FIGURE_DERIVATIONS), verified, mismatches


def seed_figure_locks(tgt: sqlite3.Connection) -> int:
    """Seed figure_locks from FIGURE_DERIVATIONS canonical values."""
    count = 0
    ts = now_utc()
    for deriv in FIGURE_DERIVATIONS:
        lock_id = make_id("lock", deriv["figure_id"])
        tgt.execute(
            """INSERT OR REPLACE INTO figure_locks
               (lock_id, figure_id, locked_value, locked_at, locked_by)
               VALUES (?,?,?,?,?)""",
            (lock_id, deriv["figure_id"], deriv["canonical_value"], ts, "woodward-core-v2/seed"),
        )
        if tgt.execute("SELECT changes()").fetchone()[0]:
            count += 1
    tgt.commit()
    return count


def main():
    print("=== WOODWARD LEDGER SEED ===")
    print(f"Source DB : {SOURCE_DB}")
    print(f"Target DB : {TARGET_DB}")
    print(f"Migration : {MIGRATION_SQL}")
    print()

    # Verify source exists
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Source DB not found: {SOURCE_DB}")
    if not MIGRATION_SQL.exists():
        raise FileNotFoundError(f"Migration SQL not found: {MIGRATION_SQL}")

    # Ensure target directory exists
    TARGET_DB.parent.mkdir(parents=True, exist_ok=True)

    # Open connections
    src = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    tgt = sqlite3.connect(str(TARGET_DB))
    tgt.execute("PRAGMA journal_mode=WAL")
    tgt.execute("PRAGMA foreign_keys=ON")

    try:
        print("--- Migrations ---")
        run_migrations(tgt)

        print("\n--- Vendors ---")
        v_count = seed_vendors(tgt)
        print(f"  Inserted {v_count} new vendors (7 total)")

        print("\n--- Vendor aliases ---")
        a_count = seed_vendor_aliases(tgt)
        print(f"  Inserted {a_count} new aliases")

        print("\n--- Source documents ---")
        sd_count = seed_source_documents(tgt)
        print(f"  Inserted {sd_count} source documents")

        print("\n--- Payments (deduplicated) ---")
        pay_inserted, pay_skipped = seed_payments(src, tgt)
        print(f"  Inserted {pay_inserted} payments, skipped {pay_skipped} (non-target vendors or bad dates)")

        print("\n--- Fiscal rollups ---")
        rollup_count = seed_fiscal_rollups(tgt)
        print(f"  Computed {rollup_count} vendor×fiscal-year rollups")

        # Show FY24-25 totals for verification
        print("\n  FY24-25 rollup verification:")
        cur = tgt.execute(
            "SELECT vendor_id, total_amount, payment_count FROM fiscal_rollups WHERE fiscal_year='FY2024-25' ORDER BY total_amount DESC"
        )
        for row in cur.fetchall():
            print(f"    {row[0]:20s}  ${row[1]:>14,.2f}  ({row[2]} payments)")
        cur = tgt.execute(
            "SELECT SUM(total_amount) FROM fiscal_rollups WHERE fiscal_year='FY2024-25' AND vendor_id IN ('amergis','maxim','procare','soliant','pioneer')"
        )
        total_fy2425 = cur.fetchone()[0] or 0
        print(f"    {'5-vendor FY24-25 total':20s}  ${total_fy2425:>14,.2f}  (should be ~$13,326,622)")

        print("\n--- Figure derivations ---")
        deriv_total, deriv_verified, deriv_mismatches = seed_figure_derivations(src, tgt)

        print("\n--- Figure locks ---")
        lock_count = seed_figure_locks(tgt)
        print(f"  Inserted/updated {lock_count} figure locks")

        # Summary
        print()
        print("=" * 45)
        print("=== SEED COMPLETE ===")
        print(f"Vendors:           {len(VENDORS)}")
        print(f"Vendor aliases:    {sum(len(v) for v in VENDOR_ALIASES.values())}")
        print(f"Payments:          {pay_inserted}")
        print(f"Fiscal rollups:    {rollup_count}")
        print(f"Source documents:  {len(SOURCE_DOCUMENTS)}")
        print(f"Figure derivations:{deriv_total} ({deriv_verified} verified, {deriv_mismatches} mismatches)")
        print(f"Figure locks:      {lock_count}")

        # Quick integrity check
        cur = tgt.execute("SELECT COUNT(*) FROM payments")
        total_pay = cur.fetchone()[0]
        print(f"\nIntegrity check: {total_pay} payments in ledger.db")

        if deriv_mismatches > 0:
            print(f"\nWARNING: {deriv_mismatches} derivation(s) have mismatches — run verify_derivations.py for details")
        else:
            print("\nAll SQL-based derivations verified within $1 tolerance.")

    finally:
        src.close()
        tgt.close()


if __name__ == "__main__":
    main()
