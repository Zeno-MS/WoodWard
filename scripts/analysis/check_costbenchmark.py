import os
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def check_costbenchmarks():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                result = session.run("MATCH (n:CostBenchmark) RETURN keys(n) as keys LIMIT 1")
                for record in result:
                    print(f"CostBenchmark keys: {record['keys']}")
                    
                print("\nAll CostBenchmarks:")
                result = session.run("MATCH (n:CostBenchmark) RETURN n")
                for record in result:
                    node = record['n']
                    props = ", ".join([f"{k}: {v}" for k, v in node.items()])
                    print(f"  {props}")
                
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    check_costbenchmarks()
