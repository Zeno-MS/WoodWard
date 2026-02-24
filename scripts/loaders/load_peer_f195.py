import os
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

# Data gathered from OSPI F-195s / F-196s manually in the past or assumed from prior context
# We need to create the BudgetObject for Object 7 if it doesn't exist, and link it.
# We will use the same structure as the VPS load_budget.cypher

def load_peer_f195():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                
                # Make sure the organization nodes exist and have Has_Budget
                peers = [
                    "Evergreen School District", 
                    "Spokane Public Schools", 
                    "Tacoma Public Schools",
                    "Camas School District",
                    "Battle Ground School District"
                ]
                
                # We'll just load the Evergreen data first for Proof of Concept if we have it.
                # Since we don't have the explicit numbers right now in our files, we should 
                # check if there's a CSV or script that has them.

                print("Peer district nodes exist, but no budget data is loaded for them.")
                print("We need the raw OSPI F-195 data to load into the graph.")

    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    load_peer_f195()
