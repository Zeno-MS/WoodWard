import pandas as pd
import glob
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def ingest_top40_salaries(session):
    print("Ingesting Top 40 Salaries...")
    total_employees = 0
    for csv_file in sorted(glob.glob("data/salaries/Top40_*.csv")):
        df = pd.read_csv(csv_file)
        year_code = csv_file.split("_")[-1].replace(".csv", "")
        
        fy_map = {"1920": "2019-20", "2021": "2020-21", "2122": "2021-22",
                  "2223": "2022-23", "2324": "2023-24"}
        fy_label = fy_map.get(year_code, year_code)

        batch = []
        for _, row in df.iterrows():
            batch.append({
                "name": row["FullName"],
                "salary": float(row["tfinsal"]),
                "position": row.get("Position", "Unknown"),
                "year": fy_label
            })
        
        total_employees += len(batch)

        session.run("""
            UNWIND $batch AS e
            MERGE (emp:Employee {name: e.name, year: e.year})
            SET emp.salary = e.salary,
                emp.position = e.position
            WITH emp, e
            MERGE (fy:FiscalYear {label: e.year})
            MERGE (emp)-[:EMPLOYED_IN]->(fy)
            WITH emp
            MATCH (vps:Organization {name: 'Vancouver Public Schools'})
            MERGE (emp)-[:WORKS_FOR]->(vps)
        """, batch=batch)
        print(f"Loaded {len(batch)} salaries for {fy_label}")
    return total_employees

def ingest_benchmarks(session):
    print("Ingesting Staffing Benchmarks...")
    df = pd.read_csv("data/ospi/Staffing_Benchmark_2324.csv")
    name_map = {
        "Evergreen": "Evergreen School District",
        "Spokane": "Spokane Public Schools",
        "Tacoma": "Tacoma Public Schools",
        "Vancouver": "Vancouver Public Schools"
    }
    for _, row in df.iterrows():
        dist_name = name_map.get(row["District"], row["District"])
        para = float(row["Paraeducators"]) if pd.notna(row.get("Paraeducators")) else 0.0
        prin = float(row["Principals"]) if pd.notna(row.get("Principals")) else 0.0
        supt = float(row["Superintendent"]) if pd.notna(row.get("Superintendent")) else 0.0
        teach = float(row["Teachers"]) if pd.notna(row.get("Teachers")) else 0.0

        session.run("""
            MERGE (o:Organization {name: $name})
            SET o.type = 'School District',
                o.benchmark_paraeducators = $para,
                o.benchmark_principals = $prin,
                o.benchmark_superintendent = $supt,
                o.benchmark_teachers = $teach
        """, name=dist_name, para=para, prin=prin, supt=supt, teach=teach)
    print(f"Loaded {len(df)} peer district staffing benchmarks.")
    return len(df)

def verify_ingestion(session):
    print("\\n--- VERIFICATION ---")
    emp_count = session.run("MATCH (e:Employee) RETURN count(e) as c").single()["c"]
    print(f"Total Employee records: {emp_count}")
    
    supt = session.run("MATCH (e:Employee) WHERE e.name CONTAINS 'SNELL' RETURN e.name as name, e.salary as salary, e.year as year ORDER BY e.year").data()
    print("Snell Salaries:")
    for record in supt:
        print(f"  {record['year']} ({record['name']}): ${record['salary']:,.2f}")
        
    org_count = session.run("MATCH (o:Organization {type: 'School District'}) RETURN count(o) as c").single()["c"]
    print(f"Total School District nodes (including VPS): {org_count}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        ingest_top40_salaries(session)
        try:
            ingest_benchmarks(session)
        except Exception as e:
            print(f"Could not load benchmarks: {e}")
        verify_ingestion(session)
    driver.close()

if __name__ == "__main__":
    main()
