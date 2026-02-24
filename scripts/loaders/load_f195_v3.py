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

# Object Mapping (Standard OSPI Codes)
OBJECT_MAP = {
    1: "Certificated Salaries",
    2: "Classified Salaries",
    3: "Employee Benefits",
    4: "Supplies",
    5: "Purchased Services",
    7: "Travel",
    8: "Capital Outlay"
}
# Also support reversed or bracketed codes found in older PDFs
LEGACY_LABELS = {
    "Certificated Salaries": 1,
    "Classified Salaries": 2,
    "Employee Benefits": 3,
    "Supplies": 4,
    "Purchased Services": 5,
    "Travel": 6,
    "Capital Outlay": 7
}

def normalize_fy(fy):
    fy = fy.replace('FY ', '').replace('FY', '').strip()
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

def extract_gf10_data(pdf_path):
    """Extract budget data from the GF10 detailed summary page."""
    print(f"  Analysing {pdf_path.name}...")
    reader = pypdf.PdfReader(pdf_path)
    
    results = []
    
    # Target page search
    target_page = None
    for i, page in enumerate(reader.pages):
        # We only really need the first 40 pages for summary, or the last pages for GF10
        if i > 40 and i < len(reader.pages) - 40: continue 
        
        text = page.extract_text()
        if not text: continue
        
        # Look for the GF10 header or equivalent
        if "SUMMARY OF GENERAL FUND EXPENDITURES BY OBJECT OF EXPENDITURE" in text or \
           ("EXPENDITURE SUMMARY BY OBJECTS" in text and "Certificated Salaries" in text):
            target_page = page
            print(f"    Found object summary page at index {i}")
            break
    
    if not target_page:
        return []

    text = target_page.extract_text()
    
    # 1. Identify Years (Order: Budget, Budget Prior, Actual Prior Prior)
    years_found = re.findall(r'(\d{4}-\d{2,4})', text)
    fy_cols = []
    for y in years_found:
        ny = normalize_fy(y)
        if ny not in fy_cols: fy_cols.append(ny)
    
    # Filename fallback if text is jumbled
    fname_match = re.search(r'(\d{4}-\d{2,4})', pdf_path.name)
    if fname_match and (not fy_cols or len(fy_cols) < 3):
        doc_fy = normalize_fy(fname_match.group(1))
        start_yr = int(doc_fy.split('-')[0])
        # In F-195s, columns are Year, Year-1, Year-2
        fy_cols = [f"{start_yr}-{start_yr+1}", f"{start_yr-1}-{start_yr}", f"{start_yr-2}-{start_yr-1}"]
    
    fy_cols = fy_cols[:3]
    print(f"    Fiscal Years: {fy_cols}")

    # 2. Extract Numbers (> 100k, with commas)
    amount_pattern = r'\b\d{1,3}(?:,\d{3})+\b'
    all_numbers = [float(n.replace(',', '')) for n in re.findall(amount_pattern, text) if float(n.replace(',', '')) > 100000]
    
    # 3. Pair numbers with objects
    # In jumbled text, the amounts are often listed in reverse order or bulk.
    # We expect 7 objects * 3 columns = 21 numbers.
    # Total might be there too (8th object).
    
    # Let's see if we can find the labels
    detected_labels = []
    for label in LEGACY_LABELS.keys():
        if label in text:
            detected_labels.append(label)
    
    # Match logic: if we have 21+ numbers, we take them in blocks of 3
    # The order in the PDF is usually (9) to (0) or (0) to (9).
    # In legacy jumbled text, Certificated (2) and Classified (3) are at the END of labels.
    # But for the numbers, they are at the START of the numerical list.
    
    # Let's use a simpler heuristic: match the largest numbers to Salaries.
    # Certificated Salaries is always the #1 largest line item (~$150M+).
    # Employee Benefits is #2 (~$80M+).
    # Classified Salaries is #3 (~$60M+).
    # Purchased Services is #4 (~$30-40M).
    
    # We'll map them by identifying the 3-value group that fits the scale.
    # Scaling factors (rough): Cert: 150M, Class: 60M, Ben: 90M, Supp: 20M, Purch: 40M
    
    extracted_data = {}
    
    # Group numbers into triplets
    triplets = []
    for i in range(0, len(all_numbers) - 2, 1):
        triplets.append(all_numbers[i:i+3])
        
    for trip in triplets:
        avg = sum(trip) / 3
        if avg > 100000000: # > 100M
            extracted_data["Certificated Salaries"] = trip
        elif 70000000 < avg <= 100000000: # 70M - 100M
            extracted_data["Employee Benefits"] = trip
        elif 50000000 < avg <= 75000000: # 50M - 75M
            extracted_data["Classified Salaries"] = trip
        elif 25000000 < avg <= 55000000: # 25M - 55M
            # Purchased Services is usually higher than Supplies
            if "Purchased Services" not in extracted_data:
                extracted_data["Purchased Services"] = trip
        elif 10000000 < avg <= 30000000:
             if "Supplies" not in extracted_data:
                 extracted_data["Supplies"] = trip
    
    for label, amounts in extracted_data.items():
        for j, amt in enumerate(amounts):
            if j < len(fy_cols):
                results.append({
                    'fy': fy_cols[j],
                    'obj_code': LEGACY_LABELS[label],
                    'obj_name': label,
                    'amount': amt,
                    'source': pdf_path.name,
                    'page': i + 1
                })
    
    return results

def load_to_sqlite(results):
    if not results: return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    loaded = 0
    for r in results:
        fy_id = get_or_create_fiscal_year_sql(conn, r['fy'])
        cursor.execute("SELECT id FROM budget_items WHERE fiscal_year_id = ? AND object_id = ?", (fy_id, r['obj_code']))
        if cursor.fetchone(): continue
        cursor.execute("INSERT INTO budget_items (fiscal_year_id, object_id, amount, source_document) VALUES (?, ?, ?, ?)",
                       (fy_id, r['obj_code'], r['amount'], r['source']))
        loaded += 1
    conn.commit()
    conn.close()
    print(f"    Loaded {loaded} items to SQLite")

def load_to_neo4j(results):
    if not results: return
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        for r in results:
            cypher = """
            MERGE (org:Organization {name: 'Vancouver Public Schools'})
            MERGE (bo:BudgetObject {name: $obj_name, code: $obj_code})
            MERGE (org)-[b:BUDGETED {fiscal_year: $fy}]->(bo)
            SET b.amount = $amount, b.source = $source
            """
            session.run(cypher, obj_name=r['obj_name'], obj_code=r['obj_code'], fy=r['fy'], amount=r['amount'], source=r['source'])
    driver.close()
    print(f"    Synced {len(results)} items to Neo4j")

def main():
    print("F-195 Detail Parser (v3)")
    files = sorted(list(DOCUMENTS_PATH.glob("VPS_*.pdf")), reverse=True)
    for pdf_file in files:
        if "F-195F" in pdf_file.name: continue
        data = extract_gf10_data(pdf_file)
        if data:
            load_to_sqlite(data)
            load_to_neo4j(data)
        else:
            print(f"    [!] Failed to extract details from {pdf_file.name}")

if __name__ == "__main__":
    main()
