import lancedb
import os

def check_lancedb():
    db_path = "data/lancedb"
    if not os.path.exists(db_path):
        print(f"LanceDB directory not found at {os.path.abspath(db_path)}")
        return

    print(f"Connecting to LanceDB at: {os.path.abspath(db_path)}")
    db = lancedb.connect(db_path)
    
    table_names = db.table_names()
    print(f"\n--- LANCEDB TABLES ({len(table_names)}) ---")
    for name in table_names:
        print(f"\nTABLE: {name}")
        try:
            table = db.open_table(name)
            
            # Print schema
            print("  SCHEMA:")
            for field in table.schema:
                print(f"    - {field.name}: {field.type}")
                
            # Print row count
            count = len(table)
            print(f"  TOTAL ROWS: {count}")
            
            # Print a sample row if not empty
            if count > 0:
                print("  SAMPLE ROW METADATA:")
                # We'll fetch the first row, convert to pandas to easily ignore the giant embedding vector
                df = table.head(1).to_pandas()
                for _, row in df.iterrows():
                    for col in df.columns:
                        if col != 'embedding' and col != 'vector':
                            val = str(row[col])
                            if len(val) > 200:
                                val = val[:200] + "..."
                            print(f"    [{col}]: {val}")
                            
        except Exception as e:
            print(f"  Error reading table {name}: {e}")

if __name__ == "__main__":
    check_lancedb()
