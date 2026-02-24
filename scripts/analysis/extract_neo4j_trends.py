import os
import pandas as pd
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def extract_f195_trends():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                query = """
                MATCH (fy:FiscalYear)-[s:SPENT]->(bo:BudgetObject)
                WHERE bo.name IN ['Purchased Services', 'Certificated Salaries', 'Classified Salaries', 'Employee Benefits']
                RETURN fy.label AS fiscal_year, bo.name AS category, s.amount AS amount
                ORDER BY fy.label, bo.name
                """
                result = session.run(query)
                records = [dict(record) for record in result]
                
                if not records:
                    print("No F-195 spending found in Neo4j.")
                    return
                
                df = pd.DataFrame(records)
                pivot_df = df.pivot(index='fiscal_year', columns='category', values='amount').reset_index()
                
                out_dir = "workspaces/VPS-F195-Object7-Trends"
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, "f195_spending_trends.csv")
                pivot_df.to_csv(out_path, index=False)
                
                print(f"Extracted F-195 trends to {out_path}")
                print(pivot_df.to_string())
                
    except Exception as e:
        print(f"Error connecting to Neo4j to extract trends: {e}")

if __name__ == "__main__":
    extract_f195_trends()
