import os
from neo4j import GraphDatabase
import pandas as pd

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def explore_peer_nodes():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                result = session.run("""
                MATCH (o:Organization)
                WHERE o.name IN ['Evergreen School District', 'Spokane Public Schools', 'Tacoma Public Schools', 'Camas School District', 'Battle Ground School District']
                RETURN o
                """)
                for record in result:
                    node = record['o']
                    print(f"Node: {node['name']}")
                    for key, value in node.items():
                        print(f"  {key}: {value}")
                    print("-" * 20)
                
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    explore_peer_nodes()
