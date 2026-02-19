import os
from neo4j import GraphDatabase

# Configuration from docker-compose.yml
# Trying neo4j protocol instead of bolt, as bolt might be stricter or misconfigured
URIs = ["neo4j://localhost:7688", "bolt://localhost:7688"]
AUTH = ("neo4j", "woodward_secure_2024")

def inspect_database():
    for uri in URIs:
        print(f"Attempting to connect to {uri}...")
        try:
            with GraphDatabase.driver(uri, auth=AUTH) as driver:
                driver.verify_connectivity()
                print(f"SUCCESS: Connected to {uri}")
                
                with driver.session() as session:
                    # Count total nodes
                    result = session.run("MATCH (n) RETURN count(n) as count")
                    total_nodes = result.single()["count"]
                    print(f"\nTotal Nodes: {total_nodes}")
                    
                    if total_nodes == 0:
                        print("Database is empty.")
                    else:
                        # Count nodes by label
                        print("\nNodes by Label:")
                        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
                        for record in result:
                            labels = record["labels"]
                            count = record["count"]
                            print(f"  {labels}: {count}")
                        
                        # Count relationships
                        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                        total_rels = result.single()["count"]
                        print(f"\nTotal Relationships: {total_rels}")
                        
                        # Count relationships by type
                        print("\nRelationships by Type:")
                        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC")
                        for record in result:
                            rel_type = record["type"]
                            count = record["count"]
                            print(f"  {rel_type}: {count}")
                            
                        # Sample some nodes
                        print("\nSample Node Properties (Limit 5):")
                        result = session.run("MATCH (n) RETURN labels(n) as labels, keys(n) as keys LIMIT 5")
                        for record in result:
                            print(f"  {record['labels']}: {record['keys']}")

                return # Exit on success of one URI

        except Exception as e:
            print(f"Failed to connect to {uri}: {e}")

if __name__ == "__main__":
    inspect_database()
