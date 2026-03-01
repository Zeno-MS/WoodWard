import lancedb
import sys
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)

db = lancedb.connect("/Users/chrisknight/Projects/WoodWard/data/lancedb")

# print available tables
print("Tables:", db.table_names())

try:
    table = db.open_table("woodward_contracts")
    
    # Run the queries Che suggested
    queries = [
        # 1. Vendor MSAs
        '("Amergis" OR "Maxim" OR "Soliant" OR "ProCare") AND ("contract" OR "agreement" OR "master service" OR "MSA" OR "amendment")',
        # 2. Budget briefings
        '("Purchased Services" OR "Object 7" OR "Object-7" OR "Object7") AND ("budget" OR "hearing" OR "presentation")',
        # 3. SPED Staffing context
        '("special education" OR "Special Services") AND ("staffing" OR "contract" OR "agency" OR "hard to fill")',
        # 4. Consent agenda wrapping
        '("consent agenda" OR "Consent") AND ("staffing" OR "agency" OR "contract")',
        # 5. Procurement pathways
        '("sole source" OR "single source" OR "emergency") AND ("staffing" OR "agency" OR "contract")',
        # 6. Cash flow events
        '("registered warrant" OR "registered warrants" OR "interfund loan" OR "cash flow" OR "apportionment advance")',
        # 7. Training/Onboarding
        '("onboarding" OR "training" OR "de-escalation" OR "restraint") AND ("contractor" OR "agency" OR "paraeducator" OR "special education teacher")',
        # 8. HR metrics
        '("exit interview" OR "retention" OR "resignation") AND ("paraeducator" OR "special education")'
    ]
    
    # "Absence as evidence" queries
    absence_queries = [
        'Blechschmidt AND ("Purchasing" OR "Purchased Services" OR "Object 7") AND ("staffing" OR "special education")',
        '("Amergis" OR "Soliant") AND ("onboarding" OR "training" OR "de-escalation")',
        '"exit interview" AND ("special education" OR "paraeducator")'
    ]
    
    for i, q in enumerate(queries):
        print(f"\n--- QUERY {i+1}: {q} ---")
        try:
            # Using basic FTS (assuming FTS index is created)
            # If FTS isn't set up perfectly, we can fallback to vector search if needed, but FTS is preferred here
            res = table.search(q, query_type="fts").limit(3).to_pandas()
            if not res.empty:
                print(f"FOUND {len(res)} matching segments")
                # print snippet of text and source
                for idx, row in res.iterrows():
                    print(f"  Snippet: {str(row.get('text', ''))[:300]}...")
            else:
                print("NO MATCHES")
        except Exception as e:
            print(f"Search failed for query {i+1}: {e}")
            
    print("\n\n=== ABSENCE AS EVIDENCE QUERIES ===\n")
    for i, q in enumerate(absence_queries):
        print(f"\n--- ABSENCE QUERY {i+1}: {q} ---")
        try:
            res = table.search(q, query_type="fts").limit(1).to_pandas()
            if not res.empty:
                print(f"WARNING: FOUND MATCHES for what should be an absence query.")
            else:
                print("CONFIRMED ABSENT: 0 hits")
        except Exception as e:
            print(f"Search failed: {e}")

except Exception as e:
    print(f"Error accessing LanceDB: {e}")
