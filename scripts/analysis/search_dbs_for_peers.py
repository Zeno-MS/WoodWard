import sqlite3
import pandas as pd
import lancedb
import os

def check_sqlite():
    db_path = "data/woodward.db"
    if not os.path.exists(db_path):
        print(f"SQLite DB not found at {db_path}")
        return
    
    print(f"--- Checking SQLite ({db_path}) ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    districts = ["Evergreen", "Camas", "Battle Ground", "Tacoma"]
    
    for table in tables:
        # Just grab the schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [c[1] for c in cursor.fetchall()]
        
        # Search text columns for the districts
        for col in columns:
            for dist in districts:
                try:
                    query = f"SELECT count(*) FROM {table} WHERE {col} LIKE ?"
                    cursor.execute(query, (f"%{dist}%",))
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"Found '{dist}' in {table}.{col} ({count} rows)")
                        
                        # Fetch a sample
                        sample_query = f"SELECT * FROM {table} WHERE {col} LIKE ? LIMIT 3"
                        df = pd.read_sql_query(sample_query, conn, params=(f"%{dist}%",))
                        print(df.to_string())
                        print("-" * 20)
                except Exception as e:
                    pass # ignore if col is not searchable like this

    conn.close()

def check_lancedb():
    db_path = "data/lancedb"
    if not os.path.exists(db_path):
        print(f"LanceDB not found at {db_path}")
        return
        
    print(f"\n--- Checking LanceDB ({db_path}) ---")
    try:
        db = lancedb.connect(db_path)
        tables = db.table_names()
        print(f"Tables: {tables}")
        
        for table_name in tables:
            tbl = db.open_table(table_name)
            df = tbl.to_pandas()
            
            districts = ["Evergreen", "Camas", "Battle Ground", "Tacoma"]
            for dist in districts:
                # Search all string columns
                for col in df.select_dtypes(include=['object', 'string']).columns:
                    # fillna to avoid errors
                    matches = df[df[col].fillna("").astype(str).str.contains(dist, case=False)]
                    if not matches.empty:
                        print(f"Found '{dist}' in {table_name}.{col} ({len(matches)} matches)")
                        print("Sample payload/text:")
                        # Assuming there is a text or payload column
                        text_col = 'text' if 'text' in df.columns else ('payload' if 'payload' in df.columns else col)
                        print(matches.head(1)[text_col].values[0][:200] + "...\n")
    except Exception as e:
        print(f"Error checking LanceDB: {e}")

if __name__ == "__main__":
    check_sqlite()
    check_lancedb()
