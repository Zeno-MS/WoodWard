import os
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def query_neo4j():
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            print("--- Sample Vendor and Payment ---")
            sample_query = """
            MATCH (v:Vendor)-[:RECEIVED_PAYMENT]-(p:Payment)
            RETURN v limit 1
            """
            result = session.run(sample_query)
            for rec in result:
                print("Vendor:", dict(rec['v']))
                
            sample_query2 = """
            MATCH (v:Vendor)-[:RECEIVED_PAYMENT]-(p:Payment)
            WHERE v.name CONTAINS 'MAXIM'
            RETURN p limit 1
            """
            result2 = session.run(sample_query2)
            for rec in result2:
                print("Payment:", dict(rec['p']))
                
            print("\n--- Yearly Spending by Vendor ---")
            query_yearly = """
            MATCH (v:Vendor)-[:RECEIVED_PAYMENT]-(p:Payment)-[:IN_FISCAL_YEAR]-(fy:FiscalYear)
            WHERE v.name CONTAINS 'MAXIM' OR v.name CONTAINS 'AMERGIS' OR v.name CONTAINS 'SOLIANT' OR v.name CONTAINS 'PIONEER' OR v.name CONTAINS 'AVEANNA' OR v.name CONTAINS 'SUNBELT'
            WITH p.amount AS amount, v.name AS vendor, fy.label AS fiscal_year
            RETURN fiscal_year, sum(amount) as total_spend, vendor
            ORDER BY fiscal_year, vendor
            """
            
            result_yearly = session.run(query_yearly)
            records = [dict(record) for record in result_yearly]
            for rec in records:
                print(f"{rec['fiscal_year']} | {rec['vendor']} : ${rec['total_spend']:,.2f}")
                
            print("\n--- Total Staffing Spending per Fiscal Year ---")
            query_summary = """
            MATCH (v:Vendor)-[:RECEIVED_PAYMENT]-(p:Payment)-[:IN_FISCAL_YEAR]-(fy:FiscalYear)
            WHERE v.name CONTAINS 'MAXIM' OR v.name CONTAINS 'AMERGIS' OR v.name CONTAINS 'SOLIANT' OR v.name CONTAINS 'PIONEER' OR v.name CONTAINS 'AVEANNA' OR v.name CONTAINS 'SUNBELT'
            WITH p.amount AS amount, fy.label AS fiscal_year
            RETURN fiscal_year, sum(amount) as total_spend
            ORDER BY fiscal_year
            """
            result_summary = session.run(query_summary)
            for rec in result_summary:
                print(f"{rec['fiscal_year']} : ${rec['total_spend']:,.2f}")

if __name__ == "__main__":
    query_neo4j()
