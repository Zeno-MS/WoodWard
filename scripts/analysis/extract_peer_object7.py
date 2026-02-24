import os
import pandas as pd
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def extract_peer_object7():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                query = """
                MATCH (o:Organization)-[r:BUDGETED]->(bo:BudgetObject {name: 'Purchased Services'})
                WHERE o.name IN ['Vancouver Public Schools', 'Evergreen School District (Clark)', 'Battle Ground School District', 'Tacoma School District']
                RETURN o.name AS district, r.fiscal_year AS fiscal_year, r.amount AS object7_amount
                ORDER BY district, fiscal_year
                """
                result = session.run(query)
                records = [dict(record) for record in result]
                
                if not records:
                    print("No peer district Object 7 data found in Neo4j.")
                    return
                
                df = pd.DataFrame(records)
                pivot_df = df.pivot(index='fiscal_year', columns='district', values='object7_amount').reset_index()
                
                out_dir = "workspaces/VPS-Peer-Comparison"
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, "peer_object7_comparison.csv")
                pivot_df.to_csv(out_path, index=False)
                
                print(f"Extracted Peer Object 7 data to {out_path}")
                print(pivot_df.to_string())
                
    except Exception as e:
        print(f"Error connecting to Neo4j to extract peer data: {e}")

if __name__ == "__main__":
    extract_peer_object7()
