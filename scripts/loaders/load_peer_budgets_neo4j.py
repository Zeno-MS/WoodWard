import pandas as pd
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def format_currency(amount):
    """Format amount as currency string."""
    try:
        return "${:,.0f}".format(float(amount))
    except (ValueError, TypeError):
        return str(amount)

def ingest_peer_budgets(session):
    print("Ingesting Peer District F-195 Object 7 Data...")
    df = pd.read_csv("workspaces/VPS-Peer-Comparison/peer_object7_comparison.csv")
    
    # We only have Object 7 data for these, and maybe Total Expenditures
    for _, row in df.iterrows():
        district = row["District"]
        
        # Clean up district name for Org node
        if district == "Evergreen":
            org_name = "Evergreen School District (Clark)"
        elif district == "Battle Ground":
            org_name = "Battle Ground School District"
        elif district == "Tacoma":
            org_name = "Tacoma School District"
        else:
            continue
            
        year = row["Year"].replace(" Budget", "")
        obj7_amount = row["Object_7_Raw_Total"]
        source = row["Note"]
        
        if pd.isna(obj7_amount) or str(obj7_amount) == "N/A":
            continue
            
        print(f"Loading {org_name} - {year} - Obj7: {obj7_amount}")
        
        # We need to link the org to the budget object. The existing vps cypher linked 
        # (Organization)-[:HAS_BUDGET]->(FiscalYear)-[:SPENT]->(BudgetObject).
        # This overwrote the SPENT amounts for multiple orgs sharing a FiscalYear.
        # To fix this pattern cleanly for peers without breaking existing queries, 
        # we can attach the Organization to the SPENT relationship directly or create Org-specific FY nodes.
        # But a better graph pattern is (Org)-[:SPENT {amount, year}]->(BudgetObject).
        # Let's use the property-rich :SPENT relationship from Org to BudgetObject.
        
        cypher = """
            MERGE (org:Organization {name: $org_name})
            SET org.type = 'School District'
            
            MERGE (bo:BudgetObject {name: 'Purchased Services'})
            
            // Create a specific Budget relationship
            MERGE (org)-[r:BUDGETED {fiscal_year: $year}]->(bo)
            SET r.amount = toFloat($obj7_amount),
                r.formatted_amount = $formatted_amt,
                r.source = $source
        """
        session.run(cypher, 
                    org_name=org_name, 
                    year=year, 
                    obj7_amount=obj7_amount,
                    formatted_amt=format_currency(obj7_amount),
                    source=source)
        
    print("Done loading peer budgets to Neo4j.")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        ingest_peer_budgets(session)
    driver.close()

if __name__ == "__main__":
    main()
