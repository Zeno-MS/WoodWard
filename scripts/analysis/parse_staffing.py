import pandas as pd
import os

# Setup paths
DATA_DIR = "data/ospi"
XLSX_PATH = os.path.join(DATA_DIR, "StaffingTables_2324.xlsx")

def parse_staffing():
    if not os.path.exists(XLSX_PATH):
        print(f"File not found: {XLSX_PATH}")
        return

    print(f"Reading {XLSX_PATH}...")
    # Table 17 is usually on a specific sheet or named sheet
    # Let's list sheets first
    xl = pd.ExcelFile(XLSX_PATH)
    print(f"Sheets: {xl.sheet_names}")
    
    # We are looking for "Table 17"
    target_sheet = None
    for sheet in xl.sheet_names:
        if "Table 17" in sheet:
            target_sheet = sheet
            break
    
    if not target_sheet:
        # Sometimes it's just index numbers
        print("Table 17 sheet not found by name. Checking all sheets...")
        target_sheet = xl.sheet_names[0] # Fallback to first sheet to inspect
        
    df = pd.read_excel(XLSX_PATH, sheet_name=target_sheet)
    
    # Show top rows to understand structure
    print("\nData Preview:")
    print(df.head(10))
    
    # We need to filter for Vancouver (District Code 06037 usually or search for name)
    # Peer Districts: Evergreen (06114), Tacoma (27010), Spokane (32081)
    
    districts = {
        "Vancouver": ["Vancouver", "06037"],
        "Evergreen": ["Evergreen", "06114"],
        "Tacoma": ["Tacoma", "27010"],
        "Spokane": ["Spokane", "32081"]
    }
    
    # Find columns that represent District Name or Code
    # (Usually first few columns)
    
    # Let's just grep for names in the whole dataframe for now to be safe
    for name, identifiers in districts.items():
        print(f"\nSearching for {name}...")
        match = df[df.apply(lambda row: row.astype(str).str.contains(identifiers[0], case=False).any(), axis=1)]
        if not match.empty:
            print(f"Found {len(match)} rows for {name}")
            print(match)
        else:
            print(f"No match found for {name} using '{identifiers[0]}'")

if __name__ == "__main__":
    parse_staffing()
