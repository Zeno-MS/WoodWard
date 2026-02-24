import sqlite3
import pandas as pd
from neo4j import GraphDatabase

NEO4J_URI = "neo4j://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "woodward_secure_2024"

STAFFING_VENDORS = [
    "AMERGIS HEALTHCARE STAFFING INC", 
    "MAXIM HEALTHCARE SERVICES INC", 
    "SOLIANT HEALTH LLC", 
    "SUNBELT STAFFING LLC",
    "PIONEER HEALTHCARE SERVICES LLC",
    "ACCOUNTABLE HEALTHCARE STAFFING INC",
    "AVEANNA HEALTHCARE"
]

def analyze_object7_disaggregation():
    # Get Budget Data from SQLite
    db_path = 'data/woodward.db'
    conn = sqlite3.connect(db_path)
    
    print("=== TOTAL OBJECT 7 BUDGET (VPS) FROM SQLITE ===")
    budget_query = """
    SELECT fy.year_label as fiscal_year, SUM(bi.amount) as total_budget
    FROM budget_items bi
    JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id
    JOIN budget_objects bo ON bi.object_id = bo.id
    WHERE bo.name = 'Purchased Services'
    GROUP BY fy.year_label
    ORDER BY fy.year_label;
    """
    try:
        budget_df = pd.read_sql_query(budget_query, conn)
        budgets = dict(zip(budget_df['fiscal_year'], budget_df['total_budget']))
        for fy, amount in budgets.items():
            print(f"FY {fy}: ${amount:,.2f}")
    except Exception as e:
        print(f"SQLite Error: {e}")
        budgets = {}
    
    conn.close()

    # Get Vendor Spend from Neo4j (direct unique lines)
    print("\n=== CORRECTED TOTAL STAFFING VENDOR SPEND (VPS) FROM NEO4J ===")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        spend_query = """
        MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)
        WHERE v.name IN $vendors
        WITH p.amount AS amt, p.entry_date AS edate
        WITH amt,
             CASE
               WHEN edate.month >= 9 THEN toString(edate.year) + '-' + toString(edate.year + 1)
               ELSE toString(edate.year - 1) + '-' + toString(edate.year)
             END AS fy
        RETURN fy, SUM(amt) AS vendor_total
        ORDER BY fy
        """
        
        vendor_spends = {}
        for record in session.run(spend_query, vendors=STAFFING_VENDORS):
            fy = record["fy"]
            # Normalize to match SQLite format: 2024-25 -> 2024-2025
            fy_parts = fy.split('-')
            if len(fy_parts) == 2 and len(fy_parts[1]) == 2:
                fy = f"{fy_parts[0]}-20{fy_parts[1]}"
                
            amount = record["vendor_total"]
            vendor_spends[fy] = amount
            print(f"FY {fy}: ${amount:,.2f}")
            
    driver.close()
            
    print("\n=== CORRECTED OBJECT 7 DISAGGREGATION (STAFFING SHARE) ===")
    if not budgets and not vendor_spends:
        print("No data found in either database.")
        return

    all_fys = sorted(set(list(budgets.keys()) + list(vendor_spends.keys())))
    
    for fy in all_fys:
        budget = budgets.get(fy, 0)
        spend = vendor_spends.get(fy, 0)
        
        if budget > 0 and spend > 0:
            percentage = (spend / budget) * 100
            print(f"FY {fy}:")
            print(f"  Total Object 7 Budget: ${budget:,.2f}")
            print(f"  Total Staffing Vendor Spend (paid warrants): ${spend:,.2f}")
            print(f"  Staffing Share of Object 7: {percentage:.2f}%\n")
        elif spend > 0:
            print(f"FY {fy}: No Object 7 budget data available in DB, but vendor spend is ${spend:,.2f}\n")

if __name__ == "__main__":
    analyze_object7_disaggregation()
