#!/usr/bin/env python3
"""
Task 3: Board Vote / Consent Agenda Analysis
Uses OpenAI API to extract structured data from board minute chunks in LanceDB.
Identifies vendor contract approvals, consent agenda items, and vote records.
"""
import os
import sys
import json
import csv
import lancedb
import pandas as pd
import re
from datetime import datetime

# --- Configuration ---
LANCEDB_PATH = "data/lancedb"
TABLE_NAME = "woodward_contracts"
OUTPUT_CSV = "documents/board_approvals.csv"
OUTPUT_JSON = "documents/board_approvals.json"

# Check for API key
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip()
                    if key and key != "#" and not key.startswith("#"):
                        API_KEY = key

if not API_KEY:
    print("=" * 60)
    print("OPENAI_API_KEY not found.")
    print("Set it with: export OPENAI_API_KEY='sk-...'")
    print("Or add it to WoodWard/.env as OPENAI_API_KEY=sk-...")
    print("=" * 60)
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=API_KEY)

def load_board_chunks():
    """Load chunks from LanceDB that likely contain board meeting content."""
    db = lancedb.connect(LANCEDB_PATH)
    tbl = db.open_table(TABLE_NAME)
    df = tbl.to_pandas().drop(columns=['embedding'], errors='ignore')
    
    # Filter for chunks containing board action language
    board_kws = ['approve', 'authorization', 'consent agenda', 'resolution', 
                 'agreement', 'contract', 'vote', 'yea', 'nay', 'motion',
                 'recommendation to approve', 'board action']
    pattern = '|'.join(re.escape(k) for k in board_kws)
    mask = df['content'].str.contains(pattern, case=False, na=False)
    board_chunks = df[mask].copy()
    
    # Also score by relevance to vendor contracts
    vendor_kws = ['Amergis', 'Maxim', 'Soliant', 'ProCare', 'Pioneer Healthcare',
                  'staffing', 'therapy', 'healthcare', 'nursing']
    board_chunks['vendor_score'] = board_chunks['content'].str.lower().apply(
        lambda t: sum(t.count(k.lower()) for k in vendor_kws)
    )
    
    # Sort by vendor relevance (process vendor-related ones first)
    board_chunks = board_chunks.sort_values('vendor_score', ascending=False)
    
    print(f"Found {len(board_chunks)} board action chunks ({board_chunks['vendor_score'].gt(0).sum()} vendor-related)")
    return board_chunks


EXTRACTION_PROMPT = """You are a legal document analyst. Extract ALL board actions from this text.

For EACH board action found, extract:
- meeting_date: The date of the board meeting (MM/DD/YYYY format, or "unknown")
- agenda_item_number: The number/label of the agenda item (e.g., "12", "C-7", "unknown")
- description: Brief description of what was approved
- vendor_name: Name of vendor/company if this involves a contract (or "N/A")
- contract_type: Type of contract if applicable (e.g., "staffing", "services", "interlocal", "N/A")
- was_consent_agenda: true if this was part of a consent agenda, false if discussed separately, null if unknown
- vote_result: The vote outcome (e.g., "5-0", "unanimous", "approved", "unknown")
- dollar_amount: Dollar amount if mentioned (or "unknown")

Return ONLY valid JSON array. If no board actions found, return [].

Example output:
[
  {
    "meeting_date": "09/20/2016",
    "agenda_item_number": "12",
    "description": "Approval of client services agreement with Soliant Health Inc.",
    "vendor_name": "Soliant Health Inc.",
    "contract_type": "staffing",
    "was_consent_agenda": false,
    "vote_result": "5-0",
    "dollar_amount": "unknown"
  }
]

TEXT TO ANALYZE:
"""


def analyze_chunk(chunk_text: str, source: str) -> list[dict]:
    """Send a chunk to GPT-4o for structured extraction."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You extract board meeting actions into structured JSON. Return only valid JSON arrays."},
                {"role": "user", "content": EXTRACTION_PROMPT + chunk_text[:3000]}
            ],
            temperature=0,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        
        # Handle both {"actions": [...]} and [...] formats
        if isinstance(parsed, dict):
            actions = parsed.get("actions", parsed.get("board_actions", parsed.get("items", [])))
        elif isinstance(parsed, list):
            actions = parsed
        else:
            actions = []
        
        # Add source metadata
        for action in actions:
            action["source_chunk"] = source
        
        return actions
    
    except Exception as e:
        print(f"  Error processing {source}: {e}")
        return []


def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    chunks = load_board_chunks()
    
    # Process vendor-related chunks first, then a sample of others
    vendor_chunks = chunks[chunks['vendor_score'] > 0]
    other_chunks = chunks[chunks['vendor_score'] == 0].head(30)  # Sample of 30 non-vendor
    process_chunks = pd.concat([vendor_chunks, other_chunks])
    
    print(f"\nProcessing {len(process_chunks)} chunks ({len(vendor_chunks)} vendor-related + {len(other_chunks)} general)...")
    
    all_actions = []
    for i, (_, row) in enumerate(process_chunks.iterrows()):
        src = row.get('citation_key') or row.get('source_document_id', 'unknown')
        chunk_idx = row.get('chunk_index', '?')
        label = f"{src}#chunk-{chunk_idx}"
        
        if (i + 1) % 10 == 0:
            print(f"  Processing {i+1}/{len(process_chunks)}...")
        
        actions = analyze_chunk(row['content'], label)
        all_actions.extend(actions)
    
    print(f"\nExtracted {len(all_actions)} board actions total.")
    
    # Deduplicate by (meeting_date, agenda_item_number, vendor_name)
    seen = set()
    unique_actions = []
    for action in all_actions:
        key = (
            action.get('meeting_date', ''),
            action.get('agenda_item_number', ''),
            action.get('vendor_name', ''),
            action.get('description', '')[:50]
        )
        if key not in seen:
            seen.add(key)
            unique_actions.append(action)
    
    print(f"After deduplication: {len(unique_actions)} unique actions.")
    
    # Save JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(unique_actions, f, indent=2)
    print(f"Saved JSON to {OUTPUT_JSON}")
    
    # Save CSV
    if unique_actions:
        fieldnames = ['meeting_date', 'agenda_item_number', 'description', 'vendor_name',
                      'contract_type', 'was_consent_agenda', 'vote_result', 'dollar_amount',
                      'source_chunk']
        with open(OUTPUT_CSV, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(unique_actions)
        print(f"Saved CSV to {OUTPUT_CSV}")
    
    # Print vendor-related highlights
    vendor_actions = [a for a in unique_actions 
                      if any(v in (a.get('vendor_name','') or '').upper() 
                             for v in ['AMERGIS','MAXIM','SOLIANT','PROCARE','PIONEER'])]
    
    if vendor_actions:
        print(f"\n{'='*60}")
        print(f"VENDOR CONTRACT APPROVALS FOUND: {len(vendor_actions)}")
        print(f"{'='*60}")
        for a in vendor_actions:
            consent = "CONSENT AGENDA" if a.get('was_consent_agenda') else "SEPARATE VOTE" if a.get('was_consent_agenda') == False else "UNKNOWN"
            print(f"  [{a.get('meeting_date','?')}] {a.get('vendor_name','?')} — {a.get('description','?')[:80]}")
            print(f"    Vote: {a.get('vote_result','?')} | {consent} | Amount: {a.get('dollar_amount','?')}")
    else:
        print("\nNo vendor-specific contract approvals extracted (may need broader search).")


if __name__ == "__main__":
    main()
