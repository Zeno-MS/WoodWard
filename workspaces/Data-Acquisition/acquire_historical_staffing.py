import requests
import os

# Setup paths
DATA_DIR = "data/ospi/historical"
os.makedirs(DATA_DIR, exist_ok=True)

# URL Templates based on observed patterns
# https://ospi.k12.wa.us/sites/default/files/2023-10/table_17_certificated_principal-duty_roots_21_22_2022-23.xlsx
# https://ospi.k12.wa.us/sites/default/files/2024-02/table_17_certificated_principal-duty_roots_21_22_2021-22.xlsx
# 2020-21: https://ospi.k12.wa.us/sites/default/files/2024-02/table_17_certificated_principal-duty_roots_21_22_2020-21.xlsx

TABLE_LINKS = {
    "2223": {
        "17": "https://ospi.k12.wa.us/sites/default/files/2023-10/table_17_certificated_principal-duty_roots_21_22_2022-23.xlsx",
        "19": "https://ospi.k12.wa.us/sites/default/files/2023-10/table_19_certificated_teacher-duty_roots_31_32_33_2022-23.xlsx",
        "20": "https://ospi.k12.wa.us/sites/default/files/2023-10/table_20_classified_paraeducator-duty_root_91_2022-23.xlsx"
    },
    "2122": {
        "17": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_17_certificated_principal-duty_roots_21_22_2021-22.xlsx",
        "19": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_19_certificated_teacher-duty_roots_31_32_33_2021-22.xlsx",
        "20": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_20_classified_paraeducator-duty_root_91_2021-22.xlsx"
    },
    "2021": {
        "17": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_17_certificated_principal-duty_roots_21_22_2020-21.xlsx",
        "19": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_19_certificated_teacher-duty_roots_31_32_33_2020-21.xlsx",
        "20": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_20_classified_paraeducator-duty_root_91_2020-21.xlsx"
    },
    "1920": {
        "17": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_17_certificated_principal-duty_roots_21_22_2019-20.xlsx",
        "19": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_19_certificated_teacher-duty_roots_31_32_33_2019-20.xlsx",
        "20": "https://ospi.k12.wa.us/sites/default/files/2024-02/table_20_classified_paraeducator-duty_root_91_2019-20.xlsx"
    }
}

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_historical():
    for year, tables in TABLE_LINKS.items():
        year_dir = os.path.join(DATA_DIR, year)
        os.makedirs(year_dir, exist_ok=True)
        for t_id, url in tables.items():
            filename = f"Table_{t_id}_{year}.xlsx"
            dest = os.path.join(year_dir, filename)
            print(f"Downloading {year} Table {t_id}...")
            try:
                resp = requests.get(url, verify=False)
                if resp.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(resp.content)
                    print(f"  Saved to {dest}")
                else:
                    print(f"  Failed: {resp.status_code}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    download_historical()
