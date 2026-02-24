import lancedb
from openai import OpenAI
import os

def search_lancedb(query):
    print(f"Searching for: '{query}'")
    db = lancedb.connect('data/lancedb')
    tbl = db.open_table('woodward_contracts')
    
    # We need to embed the query first using OpenAI ADA-002
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    
    try:
        response = client.embeddings.create(input=[query], model="text-embedding-ada-002")
        query_vector = response.data[0].embedding
        
        # Now run vector search
        res = tbl.search(query_vector).limit(5).to_pandas()
        
        if len(res) == 0:
            print("No matches")
            return
            
        for i, row in res.iterrows():
            print(f"\n--- MATCH {i+1} ---")
            print(f"Source: {row['metadata']['source'] if 'metadata' in row and row['metadata'] and 'source' in row['metadata'] else 'Unknown'}")
            print(f"Text: {row['text'][:800]}...")
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")

if __name__ == "__main__":
    search_lancedb("Washington State Auditor SAO audit finding procurement competitive bidding")
    print("\n============================================\n")
    search_lancedb("Master Service Agreement MSA bill rates Amergis Maxim Healthcare Soliant")
