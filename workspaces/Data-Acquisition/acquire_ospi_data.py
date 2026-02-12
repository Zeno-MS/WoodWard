import requests
import os
import zipfile
import io

# Setup paths
PROJECT_ROOT = "workspaces/Data-Acquisition"
DATA_DIR = "data/ospi"
os.makedirs(DATA_DIR, exist_ok=True)

# Verified OSPI S-275 direct links from browser inspection
S275_LINKS = {
    "2324": "https://ospi.k12.wa.us/sites/default/files/2024-12/2023-2024_final_s-275_personnel_database.zip",
    "2223": "https://ospi.k12.wa.us/sites/default/files/2023-10/2022-2023_final_s-275_personnel_database_1.zip",
    "2122": "https://ospi.k12.wa.us/sites/default/files/2023-11/2021-2022_final_s-275_personnel_database.zip",
    "2021": "https://ospi.k12.wa.us/sites/default/files/2023-08/2020-2021_final_s-275_personnel_database.zip",
    "1920": "https://ospi.k12.wa.us/sites/default/files/2023-08/2019-2020_final_s-275_personnel_database.zip"
}

# Verified XLSX links for Tables 15-40 (Staffing Summary)
STAFFING_XLSX_LINKS = {
    "2324": "https://ospi.k12.wa.us/sites/default/files/2024-12/table_15-40_school_district_personnel_summary_profiles_2023-24.xlsx"
}

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_data():
    print("Downloading OSPI Datasets...")
    
    # 1. Download S-275 Databases
    for year, url in S275_LINKS.items():
        filename = f"FinalS275_{year}.zip"
        print(f"  Requesting S-275 {year}: {url}")
        try:
            resp = requests.get(url, stream=True, verify=False)
            if resp.status_code == 200:
                zip_path = os.path.join(DATA_DIR, filename)
                with open(zip_path, "wb") as f:
                    f.write(resp.content)
                
                try:
                    extract_path = os.path.join(DATA_DIR, year)
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        z.extractall(extract_path)
                    print(f"    Success: Extracted to {extract_path}")
                except zipfile.BadZipFile:
                    print(f"    Error: Bad ZIP for {year}")
            else:
                print(f"    Failed: {resp.status_code}")
        except Exception as e:
            print(f"    Error: {e}")

    # 2. Download Staffing XLSX (Table 17)
    for year, url in STAFFING_XLSX_LINKS.items():
        filename = f"StaffingTables_{year}.xlsx"
        print(f"  Requesting Staffing XLSX {year}: {url}")
        try:
            resp = requests.get(url, verify=False)
            if resp.status_code == 200:
                xlsx_path = os.path.join(DATA_DIR, filename)
                with open(xlsx_path, "wb") as f:
                    f.write(resp.content)
                print(f"    Success: Saved to {xlsx_path}")
            else:
                print(f"    Failed: {resp.status_code}")
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    download_data()
