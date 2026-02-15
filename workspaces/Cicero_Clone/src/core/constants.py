# Legal-specific Cypher patterns for GraphRAG
LEGAL_GRAPH_PATTERNS = {
    "authority_chain": """
        MATCH path = (c:Case)-[:CITES*1..3]->(authority:Case)
        WHERE c.name CONTAINS $search_term OR c.citation CONTAINS $search_term
        WITH authority, 
             min(length(path)) as depth,
             count(DISTINCT c) as citing_count
        RETURN authority.content as content,
               authority.citation_key as citation_key,
               authority.source_document_id as source_document_id,
               toFloat(citing_count) / (depth + 1) as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
    """,
    
    "issue_cluster": """
        MATCH (c:Case)-[:ADDRESSES]->(i:Issue)<-[:ADDRESSES]-(related:Case)
        WHERE i.name CONTAINS $search_term OR i.description CONTAINS $search_term
        WITH related, count(DISTINCT i) as shared_issues
        MATCH (related)-[:HAS_CHUNK]->(chunk:Chunk)
        RETURN chunk.content as content,
               related.citation_key as citation_key,
               related.source_document_id as source_document_id,
               toFloat(shared_issues) as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
    """,
    
    "statutory_application": """
        MATCH (c:Case)-[:APPLIES]->(s:Statute)<-[:APPLIES]-(related:Case)
        WHERE s.citation CONTAINS $search_term OR s.name CONTAINS $search_term
        WITH related, s, count(*) as application_count
        MATCH (related)-[:HAS_CHUNK]->(chunk:Chunk)
        WHERE chunk.content CONTAINS s.citation OR chunk.content CONTAINS $search_term
        RETURN chunk.content as content,
               related.citation_key as citation_key,
               related.source_document_id as source_document_id,
               toFloat(application_count) as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
    """,
    
    "factor_analysis": """
        MATCH (c:Case)-[:ANALYZES]->(f:Factor)<-[:ANALYZES]-(related:Case)
        WHERE f.name CONTAINS $search_term
        WITH related, collect(DISTINCT f.name) as shared_factors
        MATCH (related)-[:HAS_CHUNK]->(chunk:Chunk)
        RETURN chunk.content as content,
               related.citation_key as citation_key,
               related.source_document_id as source_document_id,
               toFloat(size(shared_factors)) as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
    """,
    
    "procedural_history": """
        MATCH path = (c:Case)-[:APPEALED_FROM|REVERSED_BY|AFFIRMED_BY*1..3]-(related:Case)
        WHERE c.name CONTAINS $search_term OR c.citation CONTAINS $search_term
        WITH related, length(path) as procedural_distance
        MATCH (related)-[:HAS_CHUNK]->(chunk:Chunk)
        RETURN chunk.content as content,
               related.citation_key as citation_key,
               related.source_document_id as source_document_id,
               1.0 / (procedural_distance + 1) as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
    """,
    
    "full_text_with_graph_boost": """
        CALL db.index.fulltext.queryNodes('document_content', $search_term) 
        YIELD node, score as text_score
        OPTIONAL MATCH (node)<-[:HAS_CHUNK]-(c:Case)-[:CITES]->(cited:Case)
        WITH node, text_score, count(DISTINCT cited) as citation_count
        RETURN node.content as content,
               node.citation_key as citation_key,
               node.source_document_id as source_document_id,
               text_score * (1 + 0.1 * citation_count) as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
    """
}
