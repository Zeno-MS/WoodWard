import lancedb
import json

def search_lancedb():
    db = lancedb.connect("data/lancedb")
    table = db.open_table("woodward_contracts")
    df = table.to_pandas()
    
    keywords = ["rate", "fee", "bill", "invoice", "hourly", "auto-renew"]
    vendors = ["amergis", "maxim", "soliant", "procare"]
    
    count = 0
    for dict_index, row in df.iterrows():
        text = str(row['content']).lower()
        
        # safely parse metadata
        metadata = row['metadata']
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
                
        file_name = metadata.get('source_file', "").lower()
        
        has_vendor = any(v in file_name or v in text for v in vendors)
        if has_vendor:
            has_term = any(k in text for k in keywords)
            if has_term:
                count += 1
                if count <= 5:
                    print(f"\n--- MATCH {count} in {file_name} ---")
                    print(text[:500] + "..." if len(text) > 500 else text)
                    print("-" * 50)
                    
    print(f"\nTotal relevant chunks containing pricing/contract terms found: {count}")

if __name__ == "__main__":
    search_lancedb()
