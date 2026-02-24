import os
from neo4j import GraphDatabase
import pandas as pd

URIs = ["neo4j://localhost:7688", "bolt://localhost:7688"]
AUTH = ("neo4j", "woodward_secure_2024")

def query_graph():
    for uri in URIs:
        try:
            with GraphDatabase.driver(uri, auth=AUTH) as driver:
                driver.verify_connectivity()
                print(f"Connected to {uri}")
                
                with driver.session() as session:
                    # Look at all employee nodes to see what properties they have
                    print("\n--- Employee Node Properties Sample ---")
                    result = session.run("MATCH (e:Employee) RETURN e LIMIT 3")
                    for record in result:
                        print(dict(record['e']))

                    # Query for Deputy Superintendent and Executive Directors from 2023 to 2025
                    query = """
                    MATCH (e:Employee)
                    WHERE e.position CONTAINS 'Deputy Superintendent' OR e.position CONTAINS 'Executive Director' OR e.position CONTAINS 'Other District Administrator' OR e.position CONTAINS 'Director'
                    RETURN e.name as Name, e.position as Title, e.salary as Salary, e.year as Year
                    ORDER BY e.year, Title, Name
                    """
                    print("\n--- Cabinet Restructuring Data ---")
                    result = session.run(query)
                    records = []
                    for record in result:
                        records.append({
                            "Year": record["Year"],
                            "Name": record["Name"],
                            "Title": record["Title"],
                            "Salary": record["Salary"]
                        })
                        print(f"{record['Year']}: {record['Name']} - {record['Title']} (${record['Salary']})")

                    df = pd.DataFrame(records)
                    print("\n", df.to_string())

                return
        except Exception as e:
            print(f"Failed {uri}: {e}")

if __name__ == "__main__":
    query_graph()
