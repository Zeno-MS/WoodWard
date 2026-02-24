import os
import pypdf
import re
import pandas as pd

DOCS_DIR = "documents/F195"

# Define the files we downloaded and the years they cover (based on typical F195 naming)
files = {
    "Evergreen_2023-24_F195.pdf": "Evergreen",
    "Evergreen_2024-25_F195.pdf": "Evergreen",
    "BattleGround_F195.pdf": "Battle Ground",
    "Tacoma_F195_1.pdf": "Tacoma",
    "Tacoma_F195_2.pdf": "Tacoma",
    "Tacoma_F195_4.pdf": "Tacoma",
    "Tacoma_F195_6.pdf": "Tacoma"
}

def extract_budget_data():
    results = []
    
    for filename, district in files.items():
        pdf_path = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(pdf_path):
            continue
            
        print(f"Processing {filename}...")
        try:
            reader = pypdf.PdfReader(pdf_path)
            # F-195 General Fund summary is usually in the first 20 pages
            for i in range(min(20, len(reader.pages))):
                text = page_text = reader.pages[i].extract_text()
                if not text:
                    continue
                    
                # Look for the Expenditure Summary table
                if "EXPENDITURE SUMMARY" in text or "EXPENDITURES BY OBJECT" in text or "(7)" in text:
                    lines = text.split('\n')
                    
                    obj7 = None
                    total_exp = None
                    
                    for j, line in enumerate(lines):
                        if "Purchased Services" in line and not obj7:
                            # Typically the next line or same line has the numbers
                            context = ' '.join(lines[j:j+5])
                            amounts = [float(x.replace(',', '')) for x in re.findall(r'\b\d{1,3}(?:,\d{3})+\b', context)]
                            if amounts:
                                obj7 = amounts[0] # Grab the first column (usually Actual or Budget)
                                
                        if "TOTAL EXPENDITURES" in line and not total_exp:
                            context = ' '.join(lines[j:j+5])
                            amounts = [float(x.replace(',', '')) for x in re.findall(r'\b\d{1,3}(?:,\d{3})+\b', context)]
                            if amounts:
                                total_exp = amounts[0]
                    
                    if obj7 and total_exp:
                        perc = (obj7 / total_exp) * 100
                        results.append({
                            "District": district,
                            "File": filename,
                            "Object_7": obj7,
                            "Total_Expenditures": total_exp,
                            "Percentage": round(perc, 2)
                        })
                        break # Found what we need for this PDF
                        
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            
    df = pd.DataFrame(results)
    out_dir = "workspaces/VPS-Peer-Comparison"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "peer_object7_comparison.csv")
    df.to_csv(out_path, index=False)
    print("\nExtraction complete:")
    print(df.to_string())
    print(f"\nSaved to {out_path}")

if __name__ == "__main__":
    extract_budget_data()
