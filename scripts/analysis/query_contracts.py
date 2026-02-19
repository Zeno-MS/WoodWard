"""
Query the WoodWard contracts LanceDB to find contract clause text for:
- Billing/hourly rates
- Termination clauses
- Auto-renewal provisions
- Service scope definitions

Output: A summary dispatch for the General Counsel agent.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../workspaces/Cicero_Clone/src'))

import lancedb

LANCEDB_PATH = "data/lancedb"
TABLE_NAME = "woodward_contracts"

def query_contracts(query: str, top_k: int = 8) -> list[dict]:
    db = lancedb.connect(LANCEDB_PATH)
    if TABLE_NAME not in db.table_names():
        print(f"Table '{TABLE_NAME}' not found. Tables: {db.table_names()}")
        return []
    tbl = db.open_table(TABLE_NAME)
    results = tbl.search(query).limit(top_k).to_list()
    return results

def print_results(label: str, results: list[dict]):
    print(f"\n{'='*60}")
    print(f"QUERY: {label}")
    print(f"{'='*60}")
    for i, r in enumerate(results, 1):
        source = r.get('source_file') or r.get('metadata', {}).get('source_file', 'unknown')
        text = r.get('text') or r.get('chunk_text', '')
        score = r.get('_distance', 'n/a')
        print(f"\n--- Result {i} [{source}] (score: {score}) ---")
        print(text[:800])
        print()

def main():
    queries = [
        ("Hourly Rate / Bill Rate", "hourly rate bill rate compensation schedule staffing fee"),
        ("Termination Clause", "termination without cause notice period contract cancellation"),
        ("Auto-Renewal", "automatic renewal evergreen renewal term extension"),
        ("Service Scope / IDEA Mandate", "special education services nurses paraeducators scope of work"),
        ("Amergis Rate Structure", "Amergis rate structure payment terms"),
    ]

    for label, query in queries:
        results = query_contracts(query)
        print_results(label, results)

    # Also write a dispatch file for the General Counsel
    print("\n\nGenerating Legal Dispatch Bundle...")
    dispatch_lines = [
        "[ROLE: General Counsel / Contract Specialist]",
        "",
        "**OBJECTIVE**:",
        "Analyze the following contract text excerpts from the Amergis/Maxim/Soliant/Pioneer contracts",
        "with Vancouver Public Schools. Identify: (1) Hourly/bill rates, (2) Termination clauses,",
        "(3) Auto-renewal provisions, (4) Liability/indemnification caps.",
        "",
        "**CONTEXT**:",
        "- VPS paid $27.9M to Amergis in 2024-25 alone.",
        "- Maxim (Amergis parent) settled $150M Medicaid fraud in 2011.",
        "- We need to find if the rate structure is defensible or exploitative.",
        "",
        "**CONTRACT TEXT EXCERPTS**:",
        "",
    ]

    for label, query in queries[:3]:  # Billing/termination only
        results = query_contracts(query, top_k=3)
        dispatch_lines.append(f"### {label}")
        for r in results:
            src = r.get('source_file') or 'unknown'
            txt = r.get('text') or r.get('chunk_text', '')
            dispatch_lines.append(f"**Source**: {src}")
            dispatch_lines.append(txt[:600])
            dispatch_lines.append("")

    dispatch_lines += [
        "**INSTRUCTIONS**:",
        "1. For each clause, identify if it is 'High Risk', 'Moderate Risk', or 'Standard'.",
        "2. Quote the specific language that creates risk.",
        "3. Note any clauses that appear to be missing (e.g., no rate cap, no termination for convenience).",
        "",
        "**OUTPUT**: Legal risk memo in markdown.",
    ]

    dispatch_path = "workspaces/dispatches/TO_LEGAL/03_amergis_clause_analysis.txt"
    os.makedirs(os.path.dirname(dispatch_path), exist_ok=True)
    with open(dispatch_path, "w") as f:
        f.write("\n".join(dispatch_lines))
    print(f"Legal dispatch written to: {dispatch_path}")

if __name__ == "__main__":
    main()
