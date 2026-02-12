import sqlite3
from pathlib import Path

# Connect to SQLite
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "woodward.db"

def generate_cypher():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("// Auto-generated Budget Load Script")
    print("// Source: woodward.db")
    
    # 1. Create Fiscal Years
    cursor.execute("SELECT year_label FROM fiscal_years")
    for (year,) in cursor.fetchall():
        print(f"MERGE (fy:FiscalYear {{label: '{year}'}});")
        # Link to VPS
        print(f"MATCH (vps:Organization {{name: 'Vancouver Public Schools'}})")
        print(f"MERGE (vps)-[:HAS_BUDGET]->(fy);")
    
    # 2. Create Budget Objects
    cursor.execute("SELECT name, description FROM budget_objects")
    for name, desc in cursor.fetchall():
        # clean desc for cypher string
        desc = desc.replace("'", "\\'")
        print(f"MERGE (bo:BudgetObject {{name: '{name}'}}) SET bo.description = '{desc}';")
    
    # 3. Create Budget Items (Relationships)
    cursor.execute("""
        SELECT fy.year_label, bo.name, bi.amount, bi.source_document
        FROM budget_items bi
        JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id
        JOIN budget_objects bo ON bi.object_id = bo.id
    """)
    
    for year, obj_name, amount, source in cursor.fetchall():
        print(f"""
MATCH (fy:FiscalYear {{label: '{year}'}})
MATCH (bo:BudgetObject {{name: '{obj_name}'}})
MERGE (fy)-[r:SPENT]->(bo)
SET r.amount = {amount}, 
    r.formatted = '${amount:,.0f}',
    r.source = '{source}';
""")

    conn.close()

if __name__ == "__main__":
    generate_cypher()
