#!/usr/bin/env python3
"""
Load F-195 budget data into WoodWard SQLite database.
Segregated from all other project databases.
"""

import sqlite3
import pypdf
import re
import sys
from pathlib import Path

# Project root is two levels up from scripts/loaders/
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "woodward.db"
DOCUMENTS_PATH = PROJECT_ROOT / "documents" / "F195"

# F-195 Object code mapping (from schema)
OBJECT_MAPPING = {
    "Certificated Salaries": 1,
    "Classified Salaries": 2,
    "Employee Benefits": 3,
    "Supplies": 4,
    "Purchased Services": 5,
    "Travel": 6,
    "Capital Outlay": 7,
}

def get_or_create_fiscal_year(conn, year_label):
    """Get fiscal year ID, creating if necessary."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM fiscal_years WHERE year_label = ?", (year_label,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO fiscal_years (year_label) VALUES (?)", (year_label,))
    conn.commit()
    return cursor.lastrowid

def extract_budget_summary(pdf_path):
    """Extract budget summary from F-195 PDF."""
    results = []
    reader = pypdf.PdfReader(pdf_path)
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        
        # Look for the budget summary page - must have BOTH the header AND object names
        if "EXPENDITURE SUMMARY" not in text or "Certificated Salaries" not in text:
            continue
        
        lines = text.split('\n')
        
        # Extract fiscal years from the text
        # Format: "Actual\n2022-2023" or "Budget\n2023-2024"
        all_text = ' '.join(lines)
        year_pattern = r'(\d{4}-\d{2,4})'
        years_found = re.findall(year_pattern, all_text)
        # Get unique years in order
        fiscal_years = []
        for y in years_found:
            if y not in fiscal_years:
                fiscal_years.append(y)
        fiscal_years = fiscal_years[:3]  # Maximum 3 columns
        
        print(f"  Found fiscal years: {fiscal_years}")
        
        # Extract amounts for each object
        for obj_name, obj_code in OBJECT_MAPPING.items():
            for i, line in enumerate(lines):
                if obj_name in line:
                    # Match numbers with commas (budget amounts are typically large)
                    amount_pattern = r'\b[\d]{1,3}(?:,\d{3})+\b'
                    # Look at current and next few lines for amounts
                    context = ' '.join(lines[i:i+4])
                    amounts = re.findall(amount_pattern, context)
                    
                    # Convert to floats
                    amounts = [float(a.replace(',', '')) for a in amounts if a]
                    # Filter to reasonable budget amounts (> $100,000)
                    amounts = [a for a in amounts if a > 100000]
                    
                    print(f"  {obj_name}: {amounts[:len(fiscal_years)]}")
                    
                    for j, amount in enumerate(amounts[:len(fiscal_years)]):
                        if j < len(fiscal_years):
                            results.append({
                                'fiscal_year': fiscal_years[j],
                                'object_code': obj_code,
                                'object_name': obj_name,
                                'amount': amount,
                                'source': pdf_path.name,
                                'page': page_num + 1
                            })
                    break
        
        # Only process the first matching page
        break
    
    return results



def load_f195_to_db(pdf_path, conn):
    """Load F-195 data into database."""
    print(f"Processing: {pdf_path.name}")
    
    data = extract_budget_summary(pdf_path)
    if not data:
        print(f"  No budget summary found in {pdf_path.name}")
        return 0
    
    cursor = conn.cursor()
    loaded = 0
    
    for item in data:
        fy_id = get_or_create_fiscal_year(conn, item['fiscal_year'])
        
        # Check if already exists
        cursor.execute("""
            SELECT id FROM budget_items 
            WHERE fiscal_year_id = ? AND object_id = ?
        """, (fy_id, item['object_code']))
        
        if cursor.fetchone():
            print(f"  Skipping duplicate: {item['fiscal_year']} {item['object_name']}")
            continue
        
        cursor.execute("""
            INSERT INTO budget_items (fiscal_year_id, object_id, amount, source_document)
            VALUES (?, ?, ?, ?)
        """, (fy_id, item['object_code'], item['amount'], item['source']))
        loaded += 1
    
    conn.commit()
    print(f"  Loaded {loaded} budget items")
    return loaded

def main():
    print(f"WoodWard F-195 Loader")
    print(f"Database: {DB_PATH}")
    print(f"Documents: {DOCUMENTS_PATH}")
    print("-" * 50)
    
    conn = sqlite3.connect(DB_PATH)
    
    total = 0
    for pdf_file in DOCUMENTS_PATH.glob("*.pdf"):
        total += load_f195_to_db(pdf_file, conn)
    
    conn.close()
    print("-" * 50)
    print(f"Total loaded: {total} budget items")

if __name__ == "__main__":
    main()
