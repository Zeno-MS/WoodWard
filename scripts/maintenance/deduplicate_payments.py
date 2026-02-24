#!/usr/bin/env python3
"""
Neo4j Vendor Payment Deduplicator

This script removes duplicate Payment nodes from the Neo4j database. 
Duplicates were caused by the same Board Warrant Register appearing in 
multiple vendor PRR response PDFs. 

It works by grouping Payments by their `raw_line` (which is unique per warrant/vendor/amount),
keeping the first node, and deleting the rest.
"""
from neo4j import GraphDatabase
import sys

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def run_deduplication():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    print("=== NEO4J PAYMENT DEDUPLICATION START ===")
    
    with driver.session() as session:
        # Pre-check
        pre_check = session.run("MATCH (p:Payment) RETURN count(p) as cnt").single()
        print(f"Total Payment nodes before cleanup: {pre_check['cnt']}")
        
        # Execute Deduplication
        # This Cypher query finds all Payment nodes with the same raw_line
        # Collects them into a list, ignores the first one, and deletes the rest.
        cypher = """
        MATCH (p:Payment)
        WITH p.raw_line AS raw_line, collect(p) AS nodes
        WHERE size(nodes) > 1
        UNWIND tail(nodes) AS duplicate
        DETACH DELETE duplicate
        RETURN size(nodes) - 1 AS deleted_count
        """
        
        result = session.run(cypher)
        total_deleted = sum(record["deleted_count"] for record in result)
        
        print(f"Successfully deleted {total_deleted} duplicate Payment nodes.")
        
        # Post-check
        post_check = session.run("MATCH (p:Payment) RETURN count(p) as cnt").single()
        print(f"Total Payment nodes after cleanup: {post_check['cnt']}")
        
        # Verify specific vendor drops
        vendors = ['AMERGIS HEALTHCARE STAFFING INC', 'SOLIANT HEALTH LLC', 'MAXIM HEALTHCARE SERVICES INC']
        for v in vendors:
            v_check = session.run("""
                MATCH (v:Vendor {name: $name})-[:RECEIVED_PAYMENT]->(p:Payment)
                RETURN count(p) as cnt, sum(p.amount) as total
            """, name=v).single()
            if v_check and v_check['cnt'] > 0:
                print(f"  {v}: {v_check['cnt']} records | ${v_check['total']:,.2f}")

    driver.close()
    print("=== NEO4J PAYMENT DEDUPLICATION COMPLETE ===")

if __name__ == "__main__":
    run_deduplication()
