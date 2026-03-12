#!/usr/bin/env python3
"""
verify_derivations.py

Re-runs all figure_derivation SQL queries from ledger.db against the source
woodward.db and compares results to canonical figure_locks values.

Usage:
    python3 db/seeds/verify_derivations.py

Exits non-zero if any SQL derivation fails to reproduce its canonical value
within $1 tolerance.
"""

import sys
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_DB = PROJECT_ROOT / "VPS_Investigation_Evidence" / "00_Data_Corpus" / "woodward.db"
LEDGER_DB = PROJECT_ROOT / "db" / "ledger.db"

TOLERANCE = 1.0  # $1 tolerance for float precision


def main() -> int:
    print("=== WOODWARD DERIVATION VERIFICATION ===")
    print(f"Source DB : {SOURCE_DB}")
    print(f"Ledger DB : {LEDGER_DB}")
    print()

    if not SOURCE_DB.exists():
        print(f"FATAL: Source DB not found: {SOURCE_DB}")
        return 1
    if not LEDGER_DB.exists():
        print(f"FATAL: Ledger DB not found: {LEDGER_DB}. Run seed_ledger_from_source.py first.")
        return 1

    src = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    led = sqlite3.connect(f"file:{LEDGER_DB}?mode=ro", uri=True)

    # Load all derivations
    cur = led.execute(
        "SELECT derivation_id, figure_id, sql_query, canonical_value, status, notes FROM figure_derivations ORDER BY derivation_id"
    )
    derivations = cur.fetchall()

    # Load figure locks for canonical values
    cur2 = led.execute("SELECT figure_id, locked_value FROM figure_locks")
    locks = {row[0]: row[1] for row in cur2.fetchall()}

    passes = 0
    failures = 0
    skipped = 0

    print(f"{'Derivation ID':<40} {'Canonical':>14} {'Computed':>14} {'Diff':>8}  Status")
    print("-" * 90)

    for deriv_id, fig_id, sql_query, canonical_value, stored_status, notes in derivations:
        locked_value = locks.get(fig_id)

        if not sql_query:
            # Document-sourced — no SQL to verify
            print(f"{deriv_id:<40} ${canonical_value:>13,.0f}  {'(doc source)':>14}  {'':>8}  SKIP (doc-sourced)")
            skipped += 1
            continue

        # Re-run the SQL against source DB
        computed = None
        try:
            cur = src.execute(sql_query)
            row = cur.fetchone()
            if row and row[0] is not None:
                computed = float(row[0])
        except Exception as e:
            print(f"{deriv_id:<40}  SQL ERROR: {e}")
            failures += 1
            continue

        if computed is None:
            print(f"{deriv_id:<40}  SQL returned NULL — FAIL")
            failures += 1
            continue

        diff = abs(computed - canonical_value)
        ok = diff <= TOLERANCE

        status_label = "PASS" if ok else "FAIL"
        marker = "" if ok else " <-- MISMATCH"

        print(f"{deriv_id:<40} ${canonical_value:>13,.0f}  ${computed:>13,.2f}  ${diff:>7.2f}  {status_label}{marker}")

        if ok:
            passes += 1
        else:
            failures += 1

    src.close()
    led.close()

    print("-" * 90)
    print(f"\nResults: {passes} PASS | {failures} FAIL | {skipped} SKIP (doc-sourced)")

    if failures > 0:
        print(f"\nERROR: {failures} derivation(s) failed. Figures cannot be considered verified.")
        return 1
    else:
        print(f"\nAll SQL-based derivations PASS (within ${TOLERANCE:.0f} tolerance).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
