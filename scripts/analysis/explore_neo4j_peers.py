import os
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def explore_peer_data():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                print("1. Looking for Peer Organizations:")
                result = session.run("MATCH (o:Organization) RETURN o.name, o.type LIMIT 20")
                for record in result:
                    print(f"  {record['o.name']} ({record['o.type']})")

                print("\n2. Looking for 'Evergreen' specifically:")
                result = session.run("MATCH (n) WHERE n.name CONTAINS 'Evergreen' RETURN labels(n), n.name")
                for record in result:
                    print(f"  {record['labels(n)']} - {record['n.name']}")
                    
                print("\n3. Looking for SPENT relationships from any District:")
                result = session.run("""
                MATCH (o:Organization)-[:HAS_BUDGET]->(fy:FiscalYear)-[s:SPENT]->(bo:BudgetObject)
                RETURN o.name, fy.label, count(s) as num_spending_records
                """)
                for record in result:
                    print(f"  {record['o.name']} - {record['fy.label']}: {record['num_spending_records']} records")
                
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    explore_peer_data()
