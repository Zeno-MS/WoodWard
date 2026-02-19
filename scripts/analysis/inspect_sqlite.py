import sqlite3
import os

DB_PATH = "data/woodward.db"

def inspect_sqlite():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Connecting to {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables:")
        for t in tables:
            table_name = t[0]
            cursor.execute(f"SELECT count(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} rows")
        
        # Sample vendors if any
        if any(t[0] == 'vendors' for t in tables):
            print("\nSample Vendors:")
            cursor.execute("SELECT name, wa_ubi FROM vendors LIMIT 5")
            for r in cursor.fetchall():
                print(f"  {r}")

        conn.close()

    except Exception as e:
        print(f"Error connecting to SQLite: {e}")

if __name__ == "__main__":
    inspect_sqlite()
