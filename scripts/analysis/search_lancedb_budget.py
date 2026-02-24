import lancedb

def search_lancedb_budget():
    db_path = "data/lancedb"
    try:
        db = lancedb.connect(db_path)
        tbl = db.open_table("woodward_contracts")
        df = tbl.to_pandas()
        
        districts = ["Evergreen", "Camas", "Battle Ground", "Tacoma"]
        keywords = ["Object 7", "Purchased Services", "F-195", "budget"]
        
        print(f"--- Checking LanceDB for Budget Data ---")
        for dist in districts:
            # First filter by district
            dist_matches = df[df["content"].fillna("").astype(str).str.contains(dist, case=False)]
            
            if not dist_matches.empty:
                print(f"\nFound {len(dist_matches)} chunks mentioning '{dist}'. Filtering for budget keywords...")
                
                # Then check those chunks for budget keywords
                for kw in keywords:
                    kw_matches = dist_matches[dist_matches["content"].astype(str).str.contains(kw, case=False)]
                    if not kw_matches.empty:
                        print(f"  -> Matches for '{kw}': {len(kw_matches)}")
                        for _, row in kw_matches.head(3).iterrows():
                            text = row['content'].replace('\n', ' ')
                            print(f"     [EXCERPT]: {text[:300]}...\n")
                    else:
                        print(f"  -> No matches for '{kw}'")

    except Exception as e:
        print(f"Error checking LanceDB: {e}")

if __name__ == "__main__":
    search_lancedb_budget()
