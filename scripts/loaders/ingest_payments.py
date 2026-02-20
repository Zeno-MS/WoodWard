from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.loaders.vendor_normalization import (
    entry_date_to_fiscal_year,
    normalize_date,
    normalize_vendor,
)


SQLITE_DB = Path("data/woodward.db")
NEO4J_URI = "neo4j://localhost:7688"
NEO4J_AUTH = ("neo4j", "woodward_secure_2024")
BATCH_SIZE = 500


def stream_payments(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT payee, amount, document_date, entry_date, source_file, raw_line
        FROM payments
        ORDER BY id
        """
    )
    for payee, amount, document_date, entry_date, source_file, raw_line in cursor:
        norm = normalize_vendor(payee or "")
        entry_date_iso = normalize_date(entry_date)
        if not entry_date_iso:
            continue
        fy_label = entry_date_to_fiscal_year(entry_date)
        yield {
            "payee": (payee or "").strip(),
            "amount": float(amount or 0),
            "document_date": (document_date or "").strip() or None,
            "entry_date_iso": entry_date_iso,
            "source_file": (source_file or "").strip(),
            "raw_line": (raw_line or "").strip() or None,
            "fiscal_year": fy_label,
            "normalized_name": norm.get("normalized_name"),
            "vendor_type": norm.get("vendor_type"),
            "parent_company": norm.get("parent_company"),
            "vendor_notes": norm.get("notes"),
        }


BATCH_CYPHER = """
UNWIND $batch AS p
MERGE (v:Vendor {name: p.payee})
ON CREATE SET
  v.normalized_name = p.normalized_name,
  v.vendor_type = p.vendor_type,
  v.parent_company = p.parent_company,
  v.notes = p.vendor_notes

MERGE (d:Document {filename: p.source_file})
ON CREATE SET d.document_type = 'Warrant Register'

MERGE (fy:FiscalYear {label: p.fiscal_year})

CREATE (pay:Payment {
  amount: p.amount,
  entry_date: date(p.entry_date_iso),
  document_date: p.document_date,
  raw_line: p.raw_line,
  source_file: p.source_file
})

MERGE (v)-[:RECEIVED_PAYMENT]->(pay)
MERGE (pay)-[:EXTRACTED_FROM]->(d)
MERGE (pay)-[:IN_FISCAL_YEAR]->(fy)
"""


POST_CYPHER = [
    """
    MATCH (amergis:Vendor {name: 'AMERGIS HEALTHCARE STAFFING INC'})
    MATCH (maxim:Vendor {name: 'MAXIM HEALTHCARE SERVICES INC'})
    MATCH (parent:Organization {name: 'Maxim Healthcare Services'})
    MERGE (amergis)-[:SUBSIDIARY_OF {since: date('2022-01-01'), notes: 'Rebrand from Maxim Healthcare Staffing'}]->(parent)
    MERGE (maxim)-[:SUBSIDIARY_OF]->(parent)
    MERGE (amergis)-[:REBRANDED_FROM {year: 2022}]->(maxim)
    """,
    """
    MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
    WHERE v.normalized_name IN ['Amergis/Maxim', 'Soliant Health', 'Pioneer Healthcare']
    WITH v, fy, sum(p.amount) AS total, count(p) AS payment_count
    MERGE (v)-[s:SPENT_IN_YEAR]->(fy)
    SET s.total_amount = total, s.payment_count = payment_count
    """,
]


def main() -> None:
    if not SQLITE_DB.exists():
        raise FileNotFoundError(f"Missing SQLite DB: {SQLITE_DB}")

    conn = sqlite3.connect(SQLITE_DB)
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    total = 0
    batch: list[dict] = []

    with driver.session() as session:
        for row in stream_payments(conn):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                session.run(BATCH_CYPHER, batch=batch).consume()
                total += len(batch)
                if total % 5000 == 0:
                    print(f"INGESTED={total}")
                batch = []

        if batch:
            session.run(BATCH_CYPHER, batch=batch).consume()
            total += len(batch)

        for query in POST_CYPHER:
            session.run(query).consume()

        payment_count = session.run("MATCH (p:Payment) RETURN count(p) AS c").single()["c"]
        total_amount = session.run("MATCH (p:Payment) RETURN sum(p.amount) AS s").single()["s"]
        vendor_count = session.run("MATCH (v:Vendor) RETURN count(v) AS c").single()["c"]
        doc_count = session.run("MATCH (d:Document) RETURN count(d) AS c").single()["c"]
        print(
            f"PHASE4_OK PAYMENTS={payment_count} AMOUNT={total_amount:.2f} "
            f"VENDORS={vendor_count} DOCUMENTS={doc_count}"
        )

    conn.close()
    driver.close()


if __name__ == "__main__":
    main()
