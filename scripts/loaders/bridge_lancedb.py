import lancedb
from neo4j import GraphDatabase

URI = "neo4j://localhost:7688"
AUTH = ("neo4j", "woodward_secure_2024")

def bridge_lancedb():
    print("Connecting to LanceDB...")
    db = lancedb.connect("data/lancedb")
    tbl = db.open_table("woodward_contracts")
    df = tbl.to_pandas()

    sources = df.groupby("source_document_id").agg(
        chunk_count=("id", "count"),
        first_citation=("citation_key", "first"),
    ).reset_index()

    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        print(f"Bridging {len(sources)} documents to Neo4j...")
        for _, row in sources.iterrows():
            session.run("""
                MERGE (d:Document {filename: $filename})
                ON CREATE SET d.document_type = 'Contract/Minutes',
                              d.lance_id = $lance_id,
                              d.lance_chunk_count = $chunk_count
                ON MATCH SET  d.lance_id = $lance_id,
                              d.lance_chunk_count = $chunk_count
            """,
            filename=row["source_document_id"],
            lance_id=row["source_document_id"],
            chunk_count=int(row["chunk_count"]))
        
        print("Classifying board minutes mentioning 'Amergis Education'...")
        amergis_education_chunks = df[df['content'].str.contains("Amergis Education", case=False, na=False)]
        for _, row in amergis_education_chunks.iterrows():
            session.run("""
                MATCH (d:Document {lance_id: $lance_id})
                SET d.document_type = 'Board Meeting Minutes',
                    d.mentions_amergis_education = true
            """, lance_id=row["source_document_id"])

        count = session.run("MATCH (d:Document) WHERE d.lance_id IS NOT NULL RETURN count(d) as c").single()["c"]
        types = session.run("MATCH (d:Document) WHERE d.lance_id IS NOT NULL RETURN d.document_type as type, count(d) as c").data()
        
        print(f"\\nLANCEDB BRIDGE COMPLETE.")
        print(f"Bridged count: {count} (Expected: 55)")
        print("Document types:")
        for t in types:
            print(f"  {t['type']}: {t['c']}")

    driver.close()

if __name__ == "__main__":
    bridge_lancedb()
