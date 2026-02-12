import os
import subprocess
import pandas as pd

# Setup paths
DATA_DIR = "data/ospi"
OUTPUT_DIR = "data/salaries"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# District Code for Vancouver
VPS_CODE = "06037"

YEAR_MAP = {
    "2324": "2023-2024_Final_S-275_Personnel_Database.accdb",
    "2223": "2022-2023_Final_S-275_Personnel_Database.accdb",
    "2122": "2021-2022_Final_S-275_Personnel_Database.accdb",
    "2021": "2020-2021_Final_S-275_Personnel_Database.accdb",
    "1920": "2019-2020_Final_S-275_Personnel_Database.accdb"
}

def get_table_name(db_path):
    # mdb-tables returns a space-separated list of tables
    try:
        result = subprocess.run(["mdb-tables", db_path], capture_output=True, text=True)
        tables = result.stdout.strip().split()
        # Usually there's only one big public table
        for t in tables:
            if "Public" in t or "S-275" in t:
                return t
        return tables[0] if tables else None
    except:
        return None

# Duty Root Mapping (Common Executive/Admin roots)
DUTY_ROOTS = {
    "11": "Superintendent",
    "12": "Deputy/Asst Superintendent",
    "13": "Other District Administrator",
    "21": "Elementary Principal",
    "22": "Middle/Junior High Principal",
    "23": "Secondary Principal",
    "24": "Elementary Vice Principal",
    "25": "Middle/Junior High Vice Principal",
    "26": "Secondary Vice Principal",
    "31": "Elementary Teacher",
    "32": "Secondary Teacher",
    "33": "Other Teacher",
    "40": "Other Support Personnel"
}

def extract_top_40():
    all_summary = []
    
    for year, db_file in YEAR_MAP.items():
        db_path = os.path.join(DATA_DIR, year, db_file)
        if not os.path.exists(db_path): continue
            
        table_name = get_table_name(db_path)
        if not table_name: continue
            
        print(f"Exporting {year} Table '{table_name}'...")
        csv_path = os.path.join(OUTPUT_DIR, f"S275_{year}.csv")
        
        # Only export if doesn't exist to save time
        if not os.path.exists(csv_path):
            with open(csv_path, "w") as f:
                subprocess.run(["mdb-export", db_path, table_name], stdout=f)
            
        print(f"  Parsing {csv_path}...")
        try:
            # S-275 can have multiple rows per person (assignments). 
            # We need to sum salaries or take the Max if assignments are split but tfinsal is per-assignment total.
            # Actually, tfinsal is usually the total final salary for that individual.
            df = pd.read_csv(csv_path, low_memory=False)
            
            # Clean column names (strip quotes/spaces)
            df.columns = [c.strip() for c in df.columns]
            
            # Vancouver Code: 06037 (string "06037" or in some years "6037")
            # The column is 'codist'
            df['codist'] = df['codist'].astype(str).str.strip().str.replace('"', '')
            
            # Try both 06037 and 6037
            vps_df = df[df['codist'].isin(['06037', '6037', '06037 ', ' 06037'])]
            
            if vps_df.empty:
                print(f"  No records found for VPS in {year}. Checking first few codist values: {df['codist'].head().tolist()}")
                continue
                
            # Salary column: tfinsal (Total Final Salary)
            # Position column: droot (Duty Root)
            
            # Individuals might have multiple rows (one per duty). 
            # We group by Name (LastName + FirstName) to get their total compensation.
            vps_df['FullName'] = vps_df['FirstName'].str.strip() + " " + vps_df['LastName'].str.strip()
            vps_df['tfinsal'] = pd.to_numeric(vps_df['tfinsal'], errors='coerce')
            
            # Get the primary duty (the one with the highest fte?) or just the first one.
            # We'll take the max tfinsal per person (assuming it's a per-person total reported on each row)
            # OR sum it if it's split. In S-275, tfinsal IS usually the individual total.
            
            grouped = vps_df.groupby('FullName').agg({
                'tfinsal': 'max',
                'droot': lambda x: str(x.iloc[0]).strip() # Take first duty root
            }).reset_index()
            
            # Map Duty Root
            grouped['Position'] = grouped['droot'].map(lambda x: DUTY_ROOTS.get(str(x), f"Other ({x})"))
            
            top_40 = grouped.sort_values(by='tfinsal', ascending=False).head(40)
            top_40['Year'] = year
            
            summary_file = os.path.join(OUTPUT_DIR, f"Top40_{year}.csv")
            top_40.to_csv(summary_file, index=False)
            print(f"  Saved {len(top_40)} records to {summary_file}")
            
            all_summary.append(top_40)
            
        except Exception as e:
            print(f"  Error parsing {year}: {e}")

    if all_summary:
        master_df = pd.concat(all_summary)
        master_output = os.path.join(OUTPUT_DIR, "VPS_Top_Salaries_5yr.csv")
        master_df.to_csv(master_output, index=False)
        print(f"\nMaster report saved to {master_output}")

if __name__ == "__main__":
    extract_top_40()
