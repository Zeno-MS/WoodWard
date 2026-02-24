import requests
import os

DOCS_DIR = "documents/SAO_Audits"
os.makedirs(DOCS_DIR, exist_ok=True)

# The browser subagent extracted these exact report IDs for Vancouver SD #37:
# 2020: 1025838, 1025839
# 2021: 1028172, 1028177
# 2022: 1030364, 1030366
# 2023: 1032666, 1032716
# 2024: 1034665, 1034746
# 2025: 1036882, 1036926

report_ids = [
    1025838, 1025839,
    1028172, 1028177,
    1030364, 1030366,
    1032666, 1032716,
    1034665, 1034746,
    1036882, 1036926
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def download_reports():
    for rid in report_ids:
        # SAO URL pattern for direct document downloads:
        url = f"https://sao.wa.gov/api/v1/auditreports/download?id={rid}"
        # Some endpoints use the raw AR number, some use an internal GUID. 
        # The new portal uses a different structure, let's try the public document route
        url2 = f"https://portal.sao.wa.gov/ReportSearch/Home/ViewReportFile?arn={rid}&isFinding=false"
        url3 = f"https://portal.sao.wa.gov/ReportSearch/Home/ViewReportFile?spFileId={rid}"
        
        filepath = os.path.join(DOCS_DIR, f"AuditReport_{rid}.pdf")
        if os.path.exists(filepath):
            print(f"Skipping {rid}, already downloaded.")
            continue
            
        print(f"Downloading {rid}...")
        try:
            # We try the most common known URL pattern for WA SAO
            r = requests.get(url2, headers=headers)
            if r.status_code == 200 and len(r.content) > 10000: # Ensure it's not a generic HTML error page
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"  Success (url2) -> {filepath}")
                continue
                
            print(f"  Failed url2, status: {r.status_code}. Trying url3...")
            r = requests.get(url3, headers=headers)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"  Success (url3) -> {filepath}")
                continue
                
            print(f"  Failed. Could not download {rid}")
        except Exception as e:
            print(f"  Error on {rid}: {e}")

if __name__ == "__main__":
    download_reports()
