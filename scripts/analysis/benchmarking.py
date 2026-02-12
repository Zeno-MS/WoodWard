import pandas as pd
import os

# Setup paths
DATA_DIR = "data/ospi"
XLSX_PATH = os.path.join(DATA_DIR, "StaffingTables_2324.xlsx")

# Vancouver District Code: 06037
# Evergreen: 06114
# Tacoma: 27010
# Spokane: 32081

PEER_IDS = ["06037", "06114", "27010", "32081"]
PEER_NAMES = {
    "06037": "Vancouver",
    "06114": "Evergreen",
    "27010": "Tacoma",
    "32081": "Spokane"
}

def analyze_benchmarks():
    xl = pd.ExcelFile(XLSX_PATH)
    summary_data = []

    # Mapping of labels to flexible sheet names
    tables = {
        "Superintendent": "Table 15",
        "Principals": "Table 17",
        "Teachers": "Table 19",
        "Paraeducators": "Table 20"
    }

    for label, sheet_pattern in tables.items():
        # Find the actual sheet name (flexible space)
        target_sheet = None
        for s in xl.sheet_names:
            if s.replace(" ", "").lower() == sheet_pattern.replace(" ", "").lower():
                target_sheet = s
                break
        
        if not target_sheet:
            print(f"Sheet {sheet_pattern} not found.")
            continue
        
        print(f"Processing {label} ({target_sheet})...")
        df_raw = pd.read_excel(XLSX_PATH, sheet_name=target_sheet)
        
        header_row = 0
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains("District", case=False).any():
                header_row = i
                break
        
        df = pd.read_excel(XLSX_PATH, sheet_name=target_sheet, skiprows=header_row+1)
        
        dist_col = df.columns[0]
        fte_col = None
        for col in df.columns:
            if "total" in str(col).lower() and "fte" in str(col).lower():
                fte_col = col
                break
        if not fte_col:
            # Fallback for Table 15 which just has 'FTE'
             for col in df.columns:
                if "fte" in str(col).lower():
                    fte_col = col
                    break
        
        if not fte_col:
            print(f"  Could not find FTE column in {target_sheet}. Columns: {list(df.columns)}")
            continue

        for dist_id in PEER_IDS:
            # Match by code
            match = df[df[dist_col].astype(str).str.contains(dist_id, na=False)]
            if not match.empty:
                fte_val = match[fte_col].values[0]
                summary_data.append({
                    "District": PEER_NAMES[dist_id],
                    "Category": label,
                    "FTE": fte_val
                })
            else:
                # Try matching by name
                dist_name_col = df.columns[1]
                match_name = df[df[dist_name_col].astype(str).str.contains(PEER_NAMES[dist_id], case=False, na=False)]
                if not match_name.empty:
                     fte_val = match_name[fte_col].values[0]
                     summary_data.append({
                        "District": PEER_NAMES[dist_id],
                        "Category": label,
                        "FTE": fte_val
                    })

    bench_df = pd.DataFrame(summary_data)
    if bench_df.empty:
        print("No benchmark data extracted.")
        return

    print("\nStaffing Benchmarks (FTE):")
    # Clean up FTE strings/numbers
    bench_df['FTE'] = pd.to_numeric(bench_df['FTE'], errors='coerce')
    pivot_df = bench_df.pivot(index="District", columns="Category", values="FTE")
    print(pivot_df)
    
    pivot_df.to_csv("data/ospi/Staffing_Benchmark_2324.csv")
    print("\nBenchmark saved to data/ospi/Staffing_Benchmark_2324.csv")

if __name__ == "__main__":
    analyze_benchmarks()
