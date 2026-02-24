import sqlite3
import pandas as pd

def check_sqlite_schema():
    db_path = "data/woodward.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    for table in tables:
        print(f"\n--- {table} ---")
        df = pd.read_sql_query(f"PRAGMA table_info({table})", conn)
        print(df)
        
        # Count rows
        count = pd.read_sql_query(f"SELECT count(*) as c FROM {table}", conn).iloc[0]['c']
        print(f"Total Rows: {count}")
        
        if count > 0:
            sample = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 2", conn)
            print("Sample Rows:")
            print(sample.to_string())

    conn.close()

if __name__ == "__main__":
    check_sqlite_schema()
