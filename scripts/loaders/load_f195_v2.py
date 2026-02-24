#!/usr/bin/env python3
import sqlite3
import pypdf
import re
import os
from pathlib import Path
from neo4j import GraphDatabase

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "woodward.db"
DOCUMENTS_PATH = PROJECT_ROOT / "documents" / "F195"

# Neo4j Connection
NEO4J_URI = "neo4j://localhost:7688"
NEO4J_AUTH = ("neo4j", "woodward_secure_2024")

# Object Mapping
OBJECT_MAPPING = {
    "Certificated Salaries": 1,
    "Classified Salaries": 2,
    "Employee Benefits": 3,
    "Supplies": 4, # Matches "Supplies, Instructional Resources..." and "Supplies and Materials"
    "Purchased Services": 5,
    "Travel": 6,
    "Capital Outlay": 7,
}

def normalize_fy(fy):
    """Normalize fiscal year strings (e.g., 2024-25 -> 2024-2025)."""
    parts = fy.split('-')
    if len(parts) == 2:
        if len(parts[1]) == 2:
            return f"{parts[0]}-20{parts[1]}"
        return fy
    return fy

def get_or_create_fiscal_year_sql(conn, year_label):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM fiscal_years WHERE year_label = ?", (year_label,))
    row = cursor.fetchone()
    if row: return row[0]
    cursor.execute("INSERT INTO fiscal_years (year_label) VALUES (?)", (year_label,))
    conn.commit()
    return cursor.lastrowid

def extract_budget_data(pdf_path):
    """Robust extraction for both new and legacy F-195 layouts."""
    print(f"  Extracting from {pdf_path.name}...")
    reader = pypdf.PdfReader(pdf_path)
    
    # Infer year from filename if possible
    # VPS_2024-25_F-195.pdf -> 2024-2025
    fname = pdf_path.name
    fname_year_match = re.search(r'(\d{4}-\d{2,4})', fname)
    inferred_fy = normalize_fy(fname_year_match.group(1)) if fname_year_match else None
    
    results = []
    
    # We'll check the first 15 pages for the summary
    for page_num in range(min(15, len(reader.pages))):
        text = reader.pages[page_num].extract_text()
        if not text or "EXPENDITURE SUMMARY" not in text:
            continue
            
        print(f"    Found summary on page {page_num + 1}")
        
        # Step 1: Identify fiscal years in this doc
        # Usually found in headers like "FY 2024-2025" or column headers
        years_found = re.findall(r'(\d{4}-\d{2,4})', text)
        fy_cols = []
        for y in years_found:
            ny = normalize_fy(y)
            if ny not in fy_cols: fy_cols.append(ny)
        
        # Priority logic for years:
        # If we found years in the text, use them. 
        # But for 2018-2021 PDFs, the columns might not have years in text.
        if len(fy_cols) < 3 and inferred_fy:
             # If doc year is 2020-2021, columns are 2020-2021, 2019-2020, 2018-2019
             start_yr = int(inferred_fy.split('-')[0])
             fy_cols = [f"{start_yr}-{start_yr+1}", f"{start_yr-1}-{start_yr}", f"{start_yr-2}-{start_yr-1}"]
             # Re-normalize to 2024-2025 format
             fy_cols = [f"{y.split('-')[0]}-{int(y.split('-')[0])+1}" for y in fy_cols]
        
        fy_cols = fy_cols[:3]
        print(f"    Fiscal Years identified: {fy_cols}")
        
        # Step 2: Extract amounts
        # Regex for large currency numbers with commas
        amount_pattern = r'\b\d{1,3}(?:,\d{3})+\b'
        all_amounts = [float(a.replace(',', '')) for a in re.findall(amount_pattern, text) if float(a.replace(',', '')) > 100000]
        
        # Objects appear in order. Usually 3 amounts per object if 3 columns exist.
        # However, % columns might break this. 
        # In the dump, we see amounts like: 141,408,032 (Amount), 43.64 (Percent)
        # So we filter for amounts > 100,000 (standard school budget tier)
        
        # Check if objects are in text
        found_objects = []
        for obj_name in OBJECT_MAPPING.keys():
            if obj_name in text or (obj_name == "Supplies" and "Supplies" in text):
                found_objects.append(obj_name)
        
        print(f"    Found {len(all_amounts)} potential amounts and {len(found_objects)} object labels")
        
        # If text is jumbled (legacy), object labels might be at bottom, amounts at top.
        # In 2018-2021, Certificated Salaries is always the largest.
        # Let's use the sequence if it matches expectations.
        
        # NEWER PDFs (Success Case)
        # We'll just use the old positional logic but improved
        lines = text.split('\n')
        for obj_name, obj_code in OBJECT_MAPPING.items():
            for i, line in enumerate(lines):
                if obj_name in line:
                    # Look for numbers in this line and the next few
                    context = ' '.join(lines[i:i+3])
                    # Also check preceding lines if jumbled
                    context_pre = ' '.join(lines[max(0, i-10):i+1])
                    
                    row_amounts = [float(a.replace(',', '')) for a in re.findall(amount_pattern, context) if float(a.replace(',', '')) > 100000]
                    if not row_amounts:
                         # Fallback to the preceding context for jumbled legacy text
                         row_amounts = [float(a.replace(',', '')) for a in re.findall(amount_pattern, context_pre) if float(a.replace(',', '')) > 100000]
                         # For legacy PDFs, the percentages (e.g. 43.64) are mixed in.
                         # But since we filtered for > 100,000, we should only have the budget totals.
                         # The legacy PDFs usually list current budget, then prior budget, then actual.
                         # In the dump, they appear in order.
                    
                    if row_amounts:
                        # Limit to the number of columns we expect
                        for j, amount in enumerate(row_amounts[:len(fy_cols)]):
                            results.append({
                                'fy': fy_cols[j],
                                'obj_code': obj_code,
                                'obj_name': obj_name,
                                'amount': amount,
                                'source': pdf_path.name,
                                'page': page_num + 1
                            })
                    break
        
        if results: break # Found the summary page, stop searching
        
    return results

def load_to_sqlite(results):
    if not results: return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    loaded = 0
    for r in results:
        fy_id = get_or_create_fiscal_year_sql(conn, r['fy'])
        # Check existence
        cursor.execute("SELECT id FROM budget_items WHERE fiscal_year_id = ? AND object_id = ?", (fy_id, r['obj_code']))
        if cursor.fetchone(): continue
        
        cursor.execute("INSERT INTO budget_items (fiscal_year_id, object_id, amount, source_document) VALUES (?, ?, ?, ?)",
                       (fy_id, r['obj_code'], r['amount'], r['source']))
        loaded += 1
    conn.commit()
    conn.close()
    print(f"  Loaded {loaded} items to SQLite")

def load_to_neo4j(results):
    if not results: return
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    loaded = 0
    with driver.session() as session:
        for r in results:
            cypher = """
            MERGE (org:Organization {name: 'Vancouver Public Schools'})
            MERGE (bo:BudgetObject {name: $obj_name, code: $obj_code})
            MERGE (org)-[b:BUDGETED {fiscal_year: $fy}]->(bo)
            SET b.amount = $amount,
                b.source = $source
            """
            session.run(cypher, obj_name=r['obj_name'], obj_code=r['obj_code'], fy=r['fy'], amount=r['amount'], source=r['source'])
            loaded += 1
    driver.close()
    print(f"  Synced {loaded} items to Neo4j")

def main():
    print("Modernized F-195 Loader (v2)")
    for pdf_file in DOCUMENTS_PATH.glob("VPS_*.pdf"):
        if "F-195F" in pdf_file.name: continue # Skip the abbreviated versions
        data = extract_budget_data(pdf_file)
        if data:
            load_to_sqlite(data)
            load_to_neo4j(data)
        else:
            print(f"  [!] Failed to extract data from {pdf_file.name}")

if __name__ == "__main__":
    main()
