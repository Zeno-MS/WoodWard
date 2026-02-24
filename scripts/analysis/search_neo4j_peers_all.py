import os
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def search_all_nodes():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                districts = ["Evergreen", "Camas", "Battle Ground"]
                for district in districts:
                    print(f"\nSearching for '{district}' in any node property:")
                    query = f"""
                    MATCH (n)
                    WHERE any(k in keys(n) WHERE toString(n[k]) CONTAINS '{district}')
                    RETURN labels(n) as lbls, properties(n) as props
                    LIMIT 5
                    """
                    result = session.run(query)
                    found = False
                    for record in result:
                        found = True
                        print(f"  {record['lbls']}: {record['props']}")
                    if not found:
                        print(f"  No nodes found containing '{district}'")
                
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    search_all_nodes()
