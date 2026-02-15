"""
Metadata extraction utilities for legal document processing.
Provides functions to extract case numbers, filing dates, parties, and classify filing types.
Ported from Legal GraphRAG v2.5.
"""

import re
from typing import Optional, Dict, Any

def extract_case_number(text: str) -> Optional[str]:
    """
    Extract case number from filing header.
    
    Supports formats:
    - XX-X-XXXXX-XX (standard court format)
    - XXXXXXABC (compact format like 618133KNI)
    
    Args:
        text: Text to search (usually first 1000 chars of filing)
        
    Returns:
        Extracted case number or None
    """
    patterns = [
        r"(?:CASE|NO\.|NUMBER)[\s:#]*(\d{2}-\d-\d{5}-\d{1,2})",  # Standard format
        r"(\d{6}[A-Z]{2,3})",  # Compact format
        r"NO\.\s*(\d{6})",  # Simple number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    
    return None


def extract_filing_date(title_or_text: str) -> Optional[str]:
    """
    Extract date from paper title or filing text.
    
    Looks for dates in format: MM/DD/YYYY
    Common in titles like "Motion for Contempt, 7/21/2025"
    
    Args:
        title_or_text: Paper title or filing text
        
    Returns:
        Date string in MM/DD/YYYY format or None
    """
    date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
    match = re.search(date_pattern, title_or_text)
    return match.group(1) if match else None


def extract_parties(text: str) -> Optional[Dict[str, str]]:
    """
    Extract party names from case caption.
    
    Looks for "[NAME] v. [NAME]" pattern in first 1000 chars.
    Note: This is simplified - could be enhanced with NER.
    
    Args:
        text: Text to search (usually beginning of filing)
        
    Returns:
        Dict with 'petitioner' and 'respondent' keys, or None
    """
    # Pattern: "Name v. Name" or "Name vs. Name"
    vs_pattern = r"([A-Z][A-Za-z\s\.]+)\s+v\.?\s+([A-Z][A-Za-z\s\.]+)"
    match = re.search(vs_pattern, text[:1000])
    
    if match:
        return {
            "petitioner": match.group(1).strip(),
            "respondent": match.group(2).strip()
        }
    
    return None


def classify_filing_type(title: str) -> str:
    """
    Classify filing type based on paper title.
    
    Uses regex patterns to match common legal filing types.
    
    Args:
        title: Paper title from index or document
        
    Returns:
        Filing type classification (Motion, Declaration, Order, etc.)
    """
    type_patterns = {
        "Motion": r"^motion\s+(for|to)",
        "Declaration": r"^declaration\s+of",
        "Order": r"^order(\s+on|\s+re:|\s+denying|\s+sealing)",
        "Notice": r"^notice\s+of",
        "Memorandum": r"^memorandum\s+of",
        "Parenting Plan": r"parenting\s+plan",
        "Certificate": r"^certificate",
        "Receipt": r"^receipt",
        "Designation": r"^designation",
        "Complaint": r"^complaint",
        "Answer": r"^answer",
        "Exhibit": r"^exhibit",
    }
    
    title_lower = title.lower().strip()
    
    for ftype, pattern in type_patterns.items():
        if re.search(pattern, title_lower):
            return ftype
    
    return "Other"


def is_new_filing(text: str) -> bool:
    """
    Detect if text represents start of a new filing.
    
    Uses pattern matching for common legal filing markers:
    - Case number headers
    - Court captions
    - Docket stamps
    - Filing type headers
    - Sub number markers
    
    Args:
        text: Text to check (typically first 500 chars of page)
        
    Returns:
        True if this appears to be a filing boundary
    """
    patterns = [
        r"CASE\s+NO\.\s+[\d\-]+",              # New case number header
        r"IN\s+THE\s+.*COURT",                  # Court caption
        r"FILED:\s+\d{1,2}/\d{1,2}/\d{4}",     # Docket stamp
        r"(DECLARATION|MOTION|ORDER|NOTICE|MEMORANDUM)\s+(OF|TO|RE:)",  # Filing headers
        r"SUB\s*#\s*\d+",                       # Sub number marker
        r"^\s*SUPERIOR\s+COURT",                # Court header at start
    ]
    
    return any(re.search(p, text, re.I) for p in patterns)


def detect_filing_boundaries(pdf_pages: list) -> list:
    """
    Detect filing boundaries in a multi-filing PDF.
    
    Args:
        pdf_pages: List of (page_num, page_text) tuples
        
    Returns:
        List of page numbers where new filings start
    """
    boundaries = [0]  # First page is always a boundary
    
    for i, (page_num, page_text) in enumerate(pdf_pages):
        if i == 0:
            continue
            
        # Check first 500 characters of page
        check_text = page_text[:500] if len(page_text) > 500 else page_text
        
        if is_new_filing(check_text):
            boundaries.append(i)
    
    return boundaries


def extract_all_metadata(text: str, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract all available metadata from filing text.
    
    Convenience function that runs all extractors.
    
    Args:
        text: Filing text (full or first page)
        title: Optional paper title
        
    Returns:
        Dict with all extracted metadata
    """
    metadata = {
        "case_number": extract_case_number(text),
        "parties": extract_parties(text),
    }
    
    if title:
        metadata["filing_type"] = classify_filing_type(title)
        metadata["filing_date"] = extract_filing_date(title)
    else:
        metadata["filing_date"] = extract_filing_date(text)
    
    return metadata
