import lancedb
import json

def extract_pricing():
    db = lancedb.connect("data/lancedb")
    table = db.open_table("woodward_contracts")
    df = table.to_pandas()
    
    vendors = ["amergis", "maxim", "soliant", "procare"]
    
    print("--- EXTRACTED PRICING AND TERMS ---")
    
    for dict_index, row in df.iterrows():
        text = str(row['content']).lower()
        
        metadata = row['metadata']
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
                
        file_name = metadata.get('source_file', "").lower()
        
        # Must be a vendor file and contain actual pricing indicators
        is_vendor = any(v in file_name for v in vendors)
        if is_vendor:
            # Look for rates
            if "$" in text and ("rate" in text or "hourly" in text or "fee" in text):
                print(f"\n[RATES] File: {metadata.get('source_file')}")
                # Print the context around the dollar sign
                idx = text.find("$")
                start = max(0, idx - 100)
                end = min(len(text), idx + 200)
                print(text[start:end].replace('\n', ' '))
                
            # Look for auto-renewal
            if "renew" in text and ("auto" in text or "term" in text or "successive" in text):
                print(f"\n[RENEWAL] File: {metadata.get('source_file')}")
                idx = text.find("renew")
                start = max(0, idx - 100)
                end = min(len(text), idx + 200)
                print(text[start:end].replace('\n', ' '))

if __name__ == "__main__":
    extract_pricing()
