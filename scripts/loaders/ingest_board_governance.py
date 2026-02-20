import json
import re
from datetime import datetime
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def extract_date(text):
    # Try finding explicit spelled out dates e.g. "Tuesday, August 16, 2022"
    # or "August 16, 2022"
    match = re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', text)
    if match:
        try:
            return datetime.strptime(match.group(0), "%B %d, %Y").strftime("%Y-%m-%d")
        except:
            pass
            
    # Try finding MM/DD/YY or MM/DD/YYYY
    match2 = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if match2:
        m, d, y = match2.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{int(m):02d}-{int(d):02d}"
        
    return None

def extract_vote(text):
    # Common formats: "Motion Carried 5-0", "unanimously approved", "Vote: 4-0"
    if re.search(r'unanimously|5[-\s]0|all members', text, re.IGNORECASE):
        return "5-0 (Unanimous)"
    if re.search(r'4[-\s]0', text):
        return "4-0"
    if re.search(r'4[-\s]1', text):
        return "4-1"
    match = re.search(r'vote was (\d)[-\s](\d)', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return "Unknown/Not Specified"

def find_vendor(text):
    # We only care about our specific targets mapped to their normalized names
    text_upper = text.upper()
    if 'AMERGIS' in text_upper or 'MAXIM' in text_upper:
        return "Amergis/Maxim"
    if 'SOLIANT' in text_upper:
        return "Soliant Health"
    if 'PIONEER HEALTHCARE' in text_upper:
        return "Pioneer Healthcare"
    # Secondary targets
    if 'PROCARE' in text_upper:
        return "ProCare Therapy"
    return None

def extract_items(text, meeting_date, source_id):
    items = []
    
    # Check if this entire chunk describes an action
    vendor = find_vendor(text)
    if vendor and ('APPROVE' in text.upper() or 'AUTHORIZE' in text.upper() or 'AGREEMENT' in text.upper()):
        
        # Determine if consent agenda
        is_consent = bool(re.search(r'consent agenda|action \(consent\)', text, re.IGNORECASE))
        
        # Grab the context sentence or line
        lines = text.split('\\n')
        item_desc = text[:200] # Safe fallback
        
        # Better extraction: look for the line with the vendor or "approve"
        for line in lines:
            if vendor.split('/')[0].upper() in line.upper() or 'APPROVE' in line.upper():
                item_desc = line.strip()
                break
                
        items.append({
            "date": meeting_date or f"Unknown_Meeting_{source_id}",
            "vendor": vendor,
            "description": item_desc[:255],
            "is_consent": is_consent,
            "vote": extract_vote(text),
            "source_id": source_id
        })
        
    return items

def ingest_governance():
    print("Parsing board chunks...")
    with open("documents/board_chunks_to_process.json") as f:
        chunks = json.load(f)
        
    all_extracted_items = []
    for chunk in chunks:
        date = extract_date(chunk["content"])
        items = extract_items(chunk["content"], date, chunk["lance_id"])
        all_extracted_items.extend(items)
        
    print(f"Extracted {len(all_extracted_items)} potential governance actions.")
    
    # De-duplicate heuristically by date and vendor
    unique_items = {}
    for item in all_extracted_items:
        key = f"{item['date']}_{item['vendor']}"
        if key not in unique_items:
            unique_items[key] = item
        else:
            # Upgrade vote info if we found a better one
            if item['vote'] != "Unknown/Not Specified" and unique_items[key]['vote'] == "Unknown/Not Specified":
                unique_items[key]['vote'] = item['vote']
            # Upgrade consent info
            if item['is_consent']:
                unique_items[key]['is_consent'] = True

    final_items = list(unique_items.values())
    print(f"Deduplicated to {len(final_items)} unique actions.")
    
    # Write to Neo4j
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        for idx, item in enumerate(final_items):
            # Create Board Meeting
            session.run("""
                MERGE (m:BoardMeeting {date: $date})
                ON CREATE SET m.type = 'Regular/Special', m.source_file = $source
            """, date=item['date'], source=item['source_id'])
            
            # Create Agenda Item
            agenda_id = f"AI_{idx}_{item['date']}"
            session.run("""
                MERGE (a:AgendaItem {agenda_id: $aid})
                SET a.description = $desc,
                    a.section = $section,
                    a.vote_result = $vote,
                    a.date = $date
            """, 
            aid=agenda_id, 
            desc=item['description'], 
            section="Consent Agenda" if item['is_consent'] else "Action Item",
            vote=item['vote'],
            date=item['date'])
            
            # Link Meeting -> AgendaItem
            session.run("""
                MATCH (m:BoardMeeting {date: $date})
                MATCH (a:AgendaItem {agenda_id: $aid})
                MERGE (m)-[:HAS_ITEM]->(a)
            """, date=item['date'], aid=agenda_id)
            
            # Create Contract
            contract_id = f"Contract_{item['vendor']}_{item['date']}"
            session.run("""
                MERGE (c:Contract {contract_id: $cid})
                SET c.description = $cdesc,
                    c.vendor_name = $vendor,
                    c.start_date = $date
            """, 
            cid=contract_id, 
            cdesc=f"Agreement with {item['vendor']} authorized on {item['date']}",
            vendor=item['vendor'],
            date=item['date'])
            
            # Link AgendaItem -> Contract
            session.run("""
                MATCH (a:AgendaItem {agenda_id: $aid})
                MATCH (c:Contract {contract_id: $cid})
                MERGE (a)-[:AUTHORIZES]->(c)
            """, aid=agenda_id, cid=contract_id)
            
            # Link Vendor -> Contract
            session.run("""
                MATCH (v:Vendor {normalized_name: $vendor})
                MATCH (c:Contract {contract_id: $cid})
                MERGE (v)-[:PARTY_TO]->(c)
                WITH c
                MATCH (vps:Organization {name: 'Vancouver Public Schools'})
                MERGE (vps)-[:PARTY_TO]->(c)
            """, vendor=item['vendor'], cid=contract_id)
            
            # Link Board Members -> Vote
            # Simple assumption for MVP: Treat all extracted votes as unanimous YES unless known otherwise.
            # In real data, you'd parse roll calls.
            if "5-0" in item['vote'] or "unanimous" in item['vote'].lower() or item['vote'] == "Unknown/Not Specified":
                session.run("""
                    MATCH (p:Person {role: 'Board Member'})
                    MATCH (a:AgendaItem {agenda_id: $aid})
                    MERGE (p)-[:VOTED {vote: 'YES'}]->(a)
                """, aid=agenda_id)
        
        # Verify
        metrics = session.run("""
            MATCH (m:BoardMeeting) RETURN count(m) as mtgs
        """).single()
        print(f"Total Board Meetings graphed: {metrics['mtgs']}")
        
        items = session.run("""
            MATCH (a:AgendaItem) RETURN count(a) as items
        """).single()
        print(f"Total Agenda Items graphed: {items['items']}")
        
        amergis = session.run("""
            MATCH (v:Vendor {normalized_name: 'Amergis/Maxim'})-[:PARTY_TO]->(c:Contract)<-[:AUTHORIZES]-(a:AgendaItem)
            RETURN count(c) as contracts
        """).single()
        print(f"Amergis/Maxim Contracts via Board Action: {amergis['contracts']}")

    driver.close()

if __name__ == "__main__":
    ingest_governance()
