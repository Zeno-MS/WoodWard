#!/usr/bin/env python3
"""Audit all raw data sources for the WoodWard Neo4j re-ingestion."""
import sqlite3
import os
import glob

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def audit_lancedb():
    print("=" * 60)
    print("LANCEDB AUDIT")
    print("=" * 60)
    try:
        import lancedb
        db = lancedb.connect(os.path.join(PROJECT, "data", "lancedb"))
        print(f"Tables: {db.table_names()}")
        tbl = db.open_table("woodward_contracts")
        df = tbl.to_pandas()
        print(f"Total chunks: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print(f"Unique source_document_id: {df['source_document_id'].nunique()}")

        # Amergis variants
        for term in ["Amergis Education", "Amergis Healthcare", "Amergis Staffing", "Amergis"]:
            hits = df[df["content"].str.contains(term, case=False, na=False)]
            print(f"  Content matching '{term}': {len(hits)} chunks")
            if len(hits) > 0 and term == "Amergis Education":
                for _, row in hits.head(3).iterrows():
                    src = row.get("source_document_id", "?")
                    print(f"    [{src}] {row['content'][:200]}...")

        # Source doc samples
        print("\nSource document IDs (first 25):")
        for sid in sorted(df["source_document_id"].unique())[:25]:
            print(f"  {sid}")
        print(f"  ... ({df['source_document_id'].nunique()} total)")
    except Exception as e:
        print(f"LanceDB error: {e}")

def audit_pdfs():
    print("\n" + "=" * 60)
    print("PDF SOURCE AUDIT")
    print("=" * 60)
    pdf_dir = os.path.join(PROJECT, "workspaces", "VPS-Board-Scraper", "documents", "contracts")
    pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    print(f"Total PDFs: {len(pdfs)}")

    # Categorize by vendor prefix
    prefixes = {}
    for p in pdfs:
        name = os.path.basename(p)
        prefix = name.split("_")[0]
        prefixes.setdefault(prefix, []).append(name)

    for prefix, files in sorted(prefixes.items()):
        print(f"  {prefix}: {len(files)} files")

    # Search for Amergis Education in filenames
    amergis_ed = [p for p in pdfs if "education" in os.path.basename(p).lower()]
    if amergis_ed:
        print(f"\n  PDFs with 'education' in name: {len(amergis_ed)}")
        for p in amergis_ed:
            print(f"    {os.path.basename(p)}")

def audit_csvs():
    print("\n" + "=" * 60)
    print("CSV/XLSX DATA AUDIT")
    print("=" * 60)

    paths = [
        ("data/salaries/Top40_*.csv", "Top40 Salary CSVs"),
        ("data/salaries/VPS_*.csv", "VPS Salary Summaries"),
        ("data/salaries/S275_*.csv", "S-275 Full Exports"),
        ("data/ospi/*.csv", "OSPI CSVs"),
        ("data/ospi/*.xlsx", "OSPI XLSX"),
        ("documents/visualizations/*.csv", "Visualization CSVs"),
        ("documents/cost_comparison.csv", "Cost Comparison"),
    ]

    for pattern, label in paths:
        full_pattern = os.path.join(PROJECT, pattern)
        files = sorted(glob.glob(full_pattern))
        if files:
            print(f"\n{label}:")
            for f in files:
                size = os.path.getsize(f)
                size_str = f"{size / 1024 / 1024:.1f}MB" if size > 1024*1024 else f"{size / 1024:.0f}KB"
                print(f"  {os.path.basename(f):50s} {size_str}")

def audit_neo4j_container():
    print("\n" + "=" * 60)
    print("NEO4J CONTAINER STATUS")
    print("=" * 60)
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=woodward-neo4j", "--format", "{{.Status}}"],
        capture_output=True, text=True
    )
    status = result.stdout.strip()
    print(f"  Container status: {status if status else 'NOT RUNNING'}")

def audit_f195():
    print("\n" + "=" * 60)
    print("F-195 BUDGET PDFs")
    print("=" * 60)
    f195_dir = os.path.join(PROJECT, "documents", "F195")
    if os.path.exists(f195_dir):
        for f in sorted(os.listdir(f195_dir)):
            size = os.path.getsize(os.path.join(f195_dir, f))
            print(f"  {f:40s} {size / 1024:.0f}KB")
    else:
        print("  F195 directory not found")

if __name__ == "__main__":
    audit_lancedb()
    audit_pdfs()
    audit_csvs()
    audit_f195()
    audit_neo4j_container()
