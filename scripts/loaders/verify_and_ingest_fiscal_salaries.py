import pandas as pd
import glob
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def reformat_name(last_first):
    # e.g., 'Snell, Jeffrey' -> 'JEFFREY SNELL'
    if pd.isna(last_first):
        return "UNKNOWN"
    parts = last_first.split(',', 1)
    if len(parts) == 2:
        return f"{parts[1].strip()} {parts[0].strip()}".upper()
    return last_first.strip().upper()

def verify_and_update():
    print("Reading fiscal.wa.gov dataset...")
    df_all = pd.read_excel("data/ospi/K12AllStaffSalaryData.xlsx")
    
    # Filter for Vancouver
    df_vps = df_all[df_all['DistrictName'] == 'Vancouver'].copy()
    
    # Track verification outcomes
    discrepancies = []
    matches = 0

    # Let's verify SY2023-24 against Top40_2324.csv
    print("\\n--- VERIFYING SY 2023-24 ---")
    df_old_2324 = pd.read_csv("data/salaries/Top40_2324.csv")
    
    # Create a quick lookup from new data format (formatted name) -> SY2023-24
    df_vps['FormattedName'] = df_vps['Name'].apply(reformat_name)
    vps_2324_lookup = dict(zip(df_vps['FormattedName'], df_vps['SY2023-24']))
    
    for _, row in df_old_2324.iterrows():
        name = str(row['FullName']).upper()
        old_salary = float(row['tfinsal'])
        
        # Exact or fuzzy match logic could be added, here exact upper
        if name in vps_2324_lookup:
            new_salary = vps_2324_lookup[name]
            # new_salary might be NaN
            if pd.isna(new_salary):
                discrepancies.append((name, old_salary, "MISSING_IN_NEW"))
            elif abs(old_salary - new_salary) <= 1.0:
                matches += 1
            else:
                discrepancies.append((name, old_salary, new_salary))
        else:
            # Maybe slight name diffs? E.g. middle initial
            # Try partial
            found = False
            for new_name, sal in vps_2324_lookup.items():
                if name in new_name or new_name in name:
                    if not pd.isna(sal) and abs(old_salary - sal) <= 1.0:
                        matches += 1
                        found = True
                        break
                    else:
                        discrepancies.append((name, old_salary, sal))
                        found = True
                        break
            if not found:
                discrepancies.append((name, old_salary, "NOT_FOUND"))

    print(f"Verified {matches} out of {len(df_old_2324)} records successfully matching within $1.")
    if discrepancies:
        print(f"Found {len(discrepancies)} discrepancies:")
        for disc in list(discrepancies)[:10]:
            print(f"  {disc[0]}: old={disc[1]}, new={disc[2]}")
        if len(discrepancies) > 10:
            print(f"  ... and {len(discrepancies) - 10} more.")
            
    # Now let's ingest SY2024-25 Top 40
    print("\\n--- INGESTING SY 2024-25 TOP 40 ---")
    
    df_2425 = df_vps.copy()
    # convert down to numeric where possible, coercing errors
    df_2425['SY2024-25'] = pd.to_numeric(df_2425['SY2024-25'], errors='coerce')
    df_2425 = df_2425.dropna(subset=['SY2024-25'])
    top40_2425 = df_2425.sort_values(by='SY2024-25', ascending=False).head(40)
    
    batch = []
    for _, row in top40_2425.iterrows():
        batch.append({
            "name": row['FormattedName'],
            "salary": float(row['SY2024-25']),
            "position": str(row['Duty']) if pd.notna(row['Duty']) else "Unknown",
            "year": "2024-25"
        })
        
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
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
        print(f"Updated Neo4j with {len(batch)} salaries for 2024-25.")

        supt_2425 = session.run("MATCH (e:Employee) WHERE e.name CONTAINS 'SNELL' AND e.year = '2024-25' RETURN e.salary as salary").single()
        if supt_2425:
            print(f"Jeff Snell's 2024-25 salary loaded as: ${supt_2425['salary']:,.2f}")
            
    driver.close()
    
    # Save the top 40 for 24-25 to keep the directory consistent
    top40_output_df = pd.DataFrame(batch)
    top40_output_df.to_csv("data/salaries/Top40_2425.csv", index=False)
    print("Saved data/salaries/Top40_2425.csv")

if __name__ == "__main__":
    verify_and_update()
