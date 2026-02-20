import lancedb
import pandas as pd
import json

LANCEDB_PATH = "data/lancedb"
TABLE_NAME = "woodward_contracts"

def get_board_chunks():
    db = lancedb.connect(LANCEDB_PATH)
    tbl = db.open_table(TABLE_NAME)
    df = tbl.to_pandas()
    
    board_kws = ['recommendation to approve', 'board action', 'consent agenda', 'yea', 'nay']
    vendor_kws = ['amergis', 'maxim', 'soliant', 'pioneer']
    
    # Filter 1: Must look like board minutes
    mask1 = df['content'].str.contains('|'.join(board_kws), case=False, na=False)
    
    # Filter 2: Must mention a target vendor (we only care about these contracts for the investigation)
    mask2 = df['content'].str.contains('|'.join(vendor_kws), case=False, na=False)
    
    board_chunks = df[mask1 & mask2].copy()
    
    # Export for Antigravity to read and process
    output = []
    for _, row in board_chunks.iterrows():
        output.append({
            "lance_id": row["source_document_id"],
            "citation_key": row.get("citation_key", ""),
            "content": row["content"]
        })
        
    with open("documents/board_chunks_to_process.json", "w") as f:
        json.dump(output, f, indent=2)
        
    print(f"Exported {len(output)} highly relevant board chunks for processing.")

if __name__ == "__main__":
    get_board_chunks()
