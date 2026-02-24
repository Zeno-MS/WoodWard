import pandas as pd
import glob
import os

target_names = ["FISH", "BLECHSCHMIDT"]
all_dfs = []

files = glob.glob("data/salaries/S275_*.csv")

columns_to_keep = [
    "SchoolYear", "LastName", "FirstName", "MiddleName", "cert", "codist",
    "certfte", "clasfte", "certbase", "clasbase", "othersal", "tfinsal", 
    "droot", "prog", "act", "asspct", "assfte", "asssal", "asshpy"
]

results = []

for f in files:
    try:
        df = pd.read_csv(f, low_memory=False)
        
        # Filter for Vancouver
        if "codist" in df.columns:
            # Handle possible float/int parsing
            codist = df["codist"].fillna(0).astype(int).astype(str).str.zfill(5)
            vps_df = df[codist == "06037"]
        else:
            vps_df = df 
            
        print(f"File {f} -> {len(vps_df)} records for VPS")
        if vps_df.empty: continue
            
        # Filter for names
        if "LastName" in vps_df.columns:
            targets = vps_df[vps_df["LastName"].fillna("").str.strip().str.upper().isin(target_names)]
            
            if not targets.empty:
                available_cols = [c for c in columns_to_keep if c in targets.columns]
                results.append(targets[available_cols])
                
    except Exception as e:
        print(f"Error processing {f}: {str(e)}")

if results:
    final_df = pd.concat(results, ignore_index=True)
    if "SchoolYear" not in final_df.columns and "yr" in final_df.columns:
        final_df["SchoolYear"] = final_df["yr"]
        
    final_df = final_df.sort_values(by=["LastName", "FirstName", "SchoolYear"])
    
    out_dir = "workspaces/VPS-S275-Admin-Salaries"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "fish_blechschmidt_compensation.csv")
    final_df.to_csv(out_path, index=False)
    print(f"Extracted {len(final_df)} records to {out_path}")
    print(final_df[["LastName", "FirstName", "SchoolYear", "tfinsal", "droot", "prog", "act"]].to_string())
else:
    print("No records found in VPS.")
