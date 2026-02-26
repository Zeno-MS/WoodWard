import json
from neo4j import GraphDatabase

def check_neo4j():
    uri = "bolt://localhost:7688"
    user = "neo4j"
    password = "woodward_secure_2024"

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # 1. Check node labels
            print("--- NEO4J NODE LABELS ---")
            labels_result = session.run("CALL db.labels()")
            labels = [record[0] for record in labels_result]
            print(labels)
            
            # 2. Look for specific labels that might be skills/personas
            target_labels = ['Persona', 'Skill', 'Prompt', 'Agent', 'AI', 'Brain']
            found_targets = [l for l in labels if l in target_labels]
            
            for label in found_targets:
                print(f"\n--- FINDING NODES FOR LABEL: {label} ---")
                query = f"MATCH (n:{label}) RETURN n LIMIT 5"
                nodes = session.run(query)
                for record in nodes:
                    node = record['n']
                    print(f"ID: {node.id}")
                    for key, value in node.items():
                         str_val = str(value)
                         if len(str_val) > 100:
                             str_val = str_val[:100] + "..."
                         print(f"  {key}: {str_val}")
                        
            # 3. Keyword search across all nodes
            print("\n--- KEYWORD SEARCH ACROSS ALL NODES ---")
            keywords = ['woodward', 'sentinel', 'neo', 'chief', 'skill', 'persona']
            
            for kw in keywords:
                query = f"""
                MATCH (n)
                WHERE any(k in keys(n) WHERE toString(n[k]) =~ '(?i).*{kw}.*')
                RETURN labels(n) as lbls, id(n) as node_id, n LIMIT 2
                """
                nodes = session.run(query)
                records = list(nodes)
                if records:
                     print(f"\nFound matches for '{kw}':")
                     for record in records:
                         print(f"  Labels: {record['lbls']}, Node ID: {record['node_id']}")
                         for key, value in record['n'].items():
                             str_val = str(value)
                             if kw.lower() in str_val.lower():
                                  print(f"    {key}: {str_val[:150]}...")
                                  
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    check_neo4j()
