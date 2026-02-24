import pandas as pd
import os

VPS_CODE = '06037'

def analyze_tosa_and_cuts():
    # Load 23-24 and 24-25 data
    try:
        df23 = pd.read_csv('data/salaries/S275_2324.csv', low_memory=False)
        df24 = pd.read_csv('data/salaries/S275_2425_Vancouver_Only.csv', low_memory=False)
    except Exception as e:
        print("Error loading S-275 data:", e)
        return

    # Clean columns
    df23.columns = [c.strip() for c in df23.columns]
    df24.columns = [c.strip() for c in df24.columns]

    # Filter for VPS
    df23['codist'] = df23['codist'].astype(str).str.strip().str.replace('"', '')
    df23 = df23[df23['codist'].isin([VPS_CODE, '6037', '06037 ', ' 06037'])]

    print("=== TOSA SEARCH 2023-2024 ===")
    tosa23 = df23[df23['AssnTitle'].str.contains('TOSA', case=False, na=False) | df23['Position'].str.contains('TOSA', case=False, na=False) if 'AssnTitle' in df23.columns or 'Position' in df23.columns else pd.Series(False, index=df23.index)]
    
    if tosa23.empty:
        # TOSA might just be duty root 33 'Other Teacher' or in a different title field. Let's look for any title containing 'Assign' or 'Special'
        for col in df23.columns:
            if df23[col].dtype == object:
                matches = df23[df23[col].str.contains('Special Assig', case=False, na=False) | df23[col].str.contains('TOSA', case=False, na=False)]
                if not matches.empty:
                    print(f"Found TOSA matches in column {col}")
                    print(matches[['LastName', 'FirstName', 'droot', 'bldgn', col]].head())

    print("\n=== CENTRAL OFFICE CODES ===")
    print("Checking duty roots for Central Office (e.g., 11, 12, 13, 21)...")
    # In S-275, Central Office usually has a specific bldgn (often '0000' or similar district-wide). Let's check unique bldgn values for duty roots 11-13.
    co_23 = df23[df23['droot'].isin(['11', '12', '13', '21', 11, 12, 13, 21])]
    
    # Build strings for reliable comparison
    df23['bldgn_str'] = df23['bldgn'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    df24['bldgn_str'] = df24['bldgn'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    
    admin_roots = ['11', '12', '13', '21']
    co_23 = df23[df23['droot'].astype(str).str.strip().isin(admin_roots)]
    
    admin_bldgn = co_23['bldgn_str'].value_counts().head(5)
    print("Top admin building codes:\n", admin_bldgn)
    central_bldgn = admin_bldgn.index[0]

    print(f"Assuming District Office bldgn is {central_bldgn}")
    
    # Filter for anything in District Office Building (all staff)
    dist_23 = df23[df23['bldgn_str'] == central_bldgn]
    dist_24 = df24[df24['bldgn_str'] == central_bldgn]
    
    # Calculate Central Office Reductions (ALL staff in bldgn 1014)
    dist_23_fte = pd.to_numeric(dist_23['assfte'], errors='coerce').sum()
    dist_24_fte = pd.to_numeric(dist_24['assfte'], errors='coerce').sum()
    print(f"2023-2024 Total Central Office FTE (bldgn {central_bldgn}): {dist_23_fte:.2f}")
    print(f"2024-2025 Total Central Office FTE (bldgn {central_bldgn}): {dist_24_fte:.2f}")
    print(f"Total Central Office Elimination: {dist_23_fte - dist_24_fte:.2f} FTE")

    # Find eliminated specific roles
    dist_23_agg = dist_23.groupby('droot')['assfte'].sum()
    dist_24_agg = dist_24.groupby('droot')['assfte'].sum()
    
    print("\n=== CENTRAL OFFICE REDUCTIONS BY DUTY ROOT ===")
    diff = (dist_23_agg.fillna(0) - dist_24_agg.reindex(dist_23_agg.index).fillna(0))
    diff = diff[diff > 0].sort_values(ascending=False)
    for root, reduction in diff.items():
        print(f"Duty Root {root}: Reduced by {reduction:.2f} FTE")

    print("\n=== TOSA SEARCH (Teachers assigned to Central Office) ===")
    tosa_roots = ['31', '32', '33', '34']
    tosa_23 = dist_23[dist_23['droot'].astype(str).str.strip().isin(tosa_roots)]
    tosa_24 = dist_24[dist_24['droot'].astype(str).str.strip().isin(tosa_roots)]
    
    print("2023-2024 TOSAs (Roots 31-34 at District Office) Count:", len(tosa_23['LastName'].unique()))
    print("2023-2024 TOSAs FTE (assfte):", pd.to_numeric(tosa_23['assfte'], errors='coerce').sum())
    
    print("\nUnique duty roots for these central office teachers (TOSAs):")
    print(tosa_23['droot'].value_counts())
if __name__ == '__main__':
    analyze_tosa_and_cuts()
