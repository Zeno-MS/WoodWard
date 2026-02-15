import sqlite3
import pandas as pd
import sys
import re
from pathlib import Path
from io import StringIO

# Configuration
DB_PATH = Path("data/woodward.db")
RESULTS_DIR = Path("workspaces/results")
TARGET_FILES = [
    "01_result_peer_data.md", 
    "01_peer_spending_gap_result.txt", 
    "peer_data.csv"
]

def find_result_file():
    for fname in TARGET_FILES:
        fpath = RESULTS_DIR / fname
        if fpath.exists():
            return fpath
    # Fallback: look for any .md or .txt file in results that contains "Evergreen"
    for fpath in RESULTS_DIR.glob("*"):
        if fpath.suffix in ['.md', '.txt', '.csv']:
            try:
                content = fpath.read_text()
                if "Evergreen" in content and "Tacoma" in content:
                    return fpath
            except:
                continue
    return None

def extract_csv_from_text(text):
    # Look for code blocks first
    code_blocks = re.findall(r'```csv\n(.*?)```', text, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    
    # If no code blocks, try to find lines that look like CSV (District,Year...)
    lines = text.split('\n')
    csv_lines = []
    started = False
    for line in lines:
        if "District,Year" in line:
            started = True
        if started and line.strip():
            csv_lines.append(line)
    
    if csv_lines:
        return "\n".join(csv_lines)
    
    return None

def ingest_data():
    print("🔍 Searching for Mission Alpha results...")
    result_file = find_result_file()
    
    if not result_file:
        print(f"❌ No result file found in {RESULTS_DIR}")
        print(f"   Please ensure you saved the AI output to 'workspaces/results/01_result_peer_data.md'")
        sys.exit(1)
        
    print(f"✅ Found file: {result_file.name}")
    content = result_file.read_text()
    
    csv_data = extract_csv_from_text(content)
    if not csv_data:
        print("❌ Could not extract CSV data from file.")
        print("   Ensure the AI output contains a ```csv block or standard CSV formatting.")
        sys.exit(1)
        
    try:
        df = pd.read_csv(StringIO(csv_data))
        print("📊 Data Parsed:")
        print(df)
        
        # Connect to DB
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("peer_spending", conn, if_exists="replace", index=False)
        conn.close()
        
        print(f"\n✅ SUCCESS: Data ingested into '{DB_PATH}' table 'peer_spending'.")
        print("   The Forensic Accountant is now ready to run comparisons.")
        
    except Exception as e:
        print(f"❌ Error parsing/ingesting CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ingest_data()
