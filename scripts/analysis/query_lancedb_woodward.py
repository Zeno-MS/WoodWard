import lancedb
import sys

def search_lancedb():
    db = lancedb.connect('data/lancedb')
    tables = db.table_names()
    print(f"Available tables: {tables}")
    
    if 'woodward_contracts' in tables:
        tbl = db.open_table('woodward_contracts')
        # We can do FTS or vector search. For now, FTS might be easier if enabled, 
        # but let's just do a vector search if we have a model, or fetch all and regex.
        # Let's inspect the schema first
        print(f"Contracts table schema: {tbl.schema}")
        # Fetch a few rows to see content
        df = tbl.to_pandas()
        print(f"Total rows in contracts: {len(df)}")
        for i, row in df.head(3).iterrows():
            print(f"Row {i}: {row.get('title', 'No Title')} - {row.get('text', '')[:100]}")
    
    if 'board_minutes' in tables:
        tbl = db.open_table('board_minutes')
        print(f"Minutes table schema: {tbl.schema}")
        df = tbl.to_pandas()
        print(f"Total rows in minutes: {len(df)}")

if __name__ == "__main__":
    search_lancedb()
