import pypdf
import sys
import re

def extract_object_7(pdf_path):
    print(f"Extracting Object 7 data from: {pdf_path}")
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        number_of_pages = len(reader.pages)
        print(f"Total pages: {number_of_pages}")
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Search for Object 7 or Purchased Services
            if "Object 7" in text or "Purchased Services" in text:
                print(f"\n--- Page {i+1} ---")
                lines = text.split('\n')
                for j, line in enumerate(lines):
                    # Look for lines with Object 7 or Purchased Services
                    if "Object 7" in line or "Purchased Services" in line:
                        print(f"Match found on line {j}: {line.strip()}")
                        # Print context (5 lines before and after)
                        start = max(0, j - 5)
                        end = min(len(lines), j + 6)
                        for k in range(start, end):
                            print(f"  {k}: {lines[k].strip()}")
                        print("-" * 40)
                    
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_f195.py <pdf_file>")
        sys.exit(1)
        
    extract_object_7(sys.argv[1])
