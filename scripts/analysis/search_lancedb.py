import lancedb
from lancedb.pydantic import pydantic_to_schema
from sentence_transformers import SentenceTransformer

def search_lancedb(query):
    print(f"Searching for: '{query}'")
    db = lancedb.connect('data/lancedb')
    tbl = db.open_table('woodward_contracts')
    
    # We need to embed the query first
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(query).tolist()
    
    # Now run vector search
    res = tbl.search(query_vector).limit(5).to_pandas()
    
    if len(res) == 0:
        print("No matches")
        return
        
    for i, row in res.iterrows():
        print(f"\n--- MATCH {i+1} ---")
        print(f"Source: {row['metadata']['source'] if 'metadata' in row and row['metadata'] and 'source' in row['metadata'] else 'Unknown'}")
        print(f"Text: {row['text'][:500]}...")

if __name__ == "__main__":
    search_lancedb("Washington State Auditor WA SAO audit procurement finding 2021 2024")
    print("\n============================================\n")
    search_lancedb("Amergis Maxim Healthcare Master Service Agreement MSA competitive bidding")
