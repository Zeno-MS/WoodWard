#!/usr/bin/env python3
"""
seed_claim_support.py

Seed records.db with claim_support rows and source documents for all verified
claims that have support_chain_complete=1 but are missing ClaimSupport entries.

This script is idempotent — uses INSERT OR IGNORE.

Usage:
    cd /Volumes/WD_BLACK/Desk2/Projects/WoodWard
    python3 db/seeds/seed_claim_support.py
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RECORDS_DB = PROJECT_ROOT / "db" / "records.db"


def main() -> int:
    print("=== SEED CLAIM_SUPPORT FOR VERIFIED CLAIMS ===")
    print(f"Records DB: {RECORDS_DB}")
    print()

    if not RECORDS_DB.exists():
        print(f"FATAL: records.db not found at {RECORDS_DB}")
        return 1

    conn = sqlite3.connect(str(RECORDS_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # --- Source documents ---
    documents = [
        ("doc_ospi_f195_fy2425", "OSPI F-195 Financial Report FY2024-25",
         "financial_report", "public_record"),
        ("doc_doj_maxim_settlement_2011", "DOJ Press Release: Maxim Healthcare Settlement 2011",
         "press_release", "public_record"),
        ("doc_cumulative_fiscal_rollup", "VPS Cumulative Staffing Vendor Fiscal Rollup FY2020-26",
         "fiscal_analysis", "public_record"),
    ]

    for doc_id, title, doc_type, source_class in documents:
        conn.execute(
            "INSERT OR IGNORE INTO documents (doc_id, title, doc_type, source_class) "
            "VALUES (?, ?, ?, ?)",
            (doc_id, title, doc_type, source_class),
        )
        print(f"  DOC  {doc_id}")

    # --- Claim support rows ---
    supports = [
        (
            "sup_fy2425_total_001",
            "claim_fy2425_total_spending",
            "doc_warrant_register_fy2425",
            None,
            "$13,326,622 total for primary 5 staffing vendors in FY2024-25",
            "figure_reference",
        ),
        (
            "sup_object7_overage_001",
            "claim_object7_overage",
            "doc_ospi_f195_fy2425",
            None,
            "Object 7 actual $47,331,056 minus budget $36,738,206 = $10,592,850 overage",
            "figure_reference",
        ),
        (
            "sup_cumulative_32m_001",
            "claim_cumulative_32m",
            "doc_cumulative_fiscal_rollup",
            None,
            "$32,189,236 cumulative across FY2020-21 through FY2025-26 for primary 5 vendors",
            "figure_reference",
        ),
        (
            "sup_maxim_fraud_001",
            "claim_maxim_fraud_settlement",
            "doc_doj_maxim_settlement_2011",
            None,
            "Maxim Healthcare Services Inc. agreed to pay $150 million to resolve federal fraud charges",
            "direct_quote",
        ),
    ]

    for support in supports:
        conn.execute(
            "INSERT OR IGNORE INTO claim_support "
            "(support_id, claim_id, doc_id, chunk_id, quote, support_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            support,
        )
        print(f"  SUP  {support[0]} -> {support[1]}")

    conn.commit()

    # Verify
    cursor = conn.execute(
        "SELECT cs.claim_id, cs.doc_id FROM claim_support cs ORDER BY cs.claim_id"
    )
    rows = cursor.fetchall()
    print(f"\nTotal claim_support rows: {len(rows)}")
    for r in rows:
        print(f"  {r[0]} -> {r[1]}")

    conn.close()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
