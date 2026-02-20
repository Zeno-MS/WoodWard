import pandas as pd
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def ingest_cost_benchmark(session):
    print("Ingesting Cost Comparison Benchmarks...")
    df = pd.read_csv("documents/cost_comparison.csv")
    
    batch = []
    for _, row in df.iterrows():
        batch.append({
            "role": row["Role"],
            "contractor_hourly": float(row["Contractor_Hourly_Mid"]),
            "contractor_annual": float(row["Contractor_Annual"]),
            "inhouse_annual": float(row["InHouse_Annual"]),
            "premium_dollars": float(row["Premium_Dollars"]),
            "premium_pct": float(row["Premium_Percent"])
        })
        
    session.run("""
        UNWIND $roles AS r
        MERGE (cb:CostBenchmark {role: r.role})
        SET cb.contractor_hourly_mid = r.contractor_hourly,
            cb.contractor_annual = r.contractor_annual,
            cb.inhouse_annual = r.inhouse_annual,
            cb.premium_dollars = r.premium_dollars,
            cb.premium_percent = r.premium_pct
    """, roles=batch)
    print(f"Loaded {len(batch)} CostBenchmark nodes.")

def regenerate_analysis_csvs(session):
    print("\\nRegenerating Vendor Spending Annual CSV...")
    query_vendor = """
        MATCH (v:Vendor)-[s:SPENT_IN_YEAR]->(fy:FiscalYear)
        WHERE v.normalized_name IN ["Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"]
        RETURN v.normalized_name as vendor, fy.label as year, s.total_amount as amount
        ORDER BY fy.label, vendor
    """
    res = session.run(query_vendor).data()
    df_vendor = pd.DataFrame(res)
    df_vendor.to_csv("documents/visualizations/vendor_spending_annual.csv", index=False)
    print(f"Saved documents/visualizations/vendor_spending_annual.csv ({len(df_vendor)} rows)")
    
    print("\\nRegenerating SPED Contractor Annual CSV...")
    query_sped = """
        MATCH (v:Vendor)-[:RECEIVED_PAYMENT]->(p:Payment)-[:IN_FISCAL_YEAR]->(fy:FiscalYear)
        WHERE v.vendor_type = "Staffing Agency"
        RETURN fy.label as year, sum(p.amount) as total_sped_contractor
        ORDER BY fy.label
    """
    res = session.run(query_sped).data()
    df_sped = pd.DataFrame(res)
    df_sped.to_csv("documents/visualizations/sped_contractor_annual.csv", index=False)
    print(f"Saved documents/visualizations/sped_contractor_annual.csv ({len(df_sped)} rows)")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        ingest_cost_benchmark(session)
        regenerate_analysis_csvs(session)
    driver.close()

if __name__ == "__main__":
    main()
