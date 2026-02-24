import os
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def explore_peer_rels():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                result = session.run("""
                MATCH (o:Organization {name: 'Evergreen School District'})-[r]-(m)
                RETURN type(r), labels(m), m.name
                """)
                records = list(result)
                print(f"Found {len(records)} relationships for Evergreen.")
                for record in records:
                    print(f"  -[{record['type(r)']}]-> {record['labels(m)']} {record['m.name']}")
                    
                print("\nLet's also check all nodes to see if there is another node type for Budget/F195")
                result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
                for record in result:
                    print(f"  {record['labels']}: {record['count']}")
                    
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    explore_peer_rels()
