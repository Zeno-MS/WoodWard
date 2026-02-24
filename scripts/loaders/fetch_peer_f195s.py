import requests
from bs4 import BeautifulSoup
import os
import subprocess

DOCS_DIR = "documents/F195"
os.makedirs(DOCS_DIR, exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def fetch_evergreen():
    print("Fetching Evergreen F-195s (via known GDrive links)...")
    # Known links from RESEARCH_FINDINGS
    links = {
        "Evergreen_2023-24_F195.pdf": "13wsXOwx0fuDOr1y1BNEKvw8vS9B5tXE-",
        "Evergreen_2024-25_F195.pdf": "1f6bAravjTz98jhGcy_96ELDi4B1oCWlk"
    }
    for name, gid in links.items():
        out_path = os.path.join(DOCS_DIR, name)
        if not os.path.exists(out_path):
            print(f"Downloading {name}...")
            subprocess.run(["gdown", gid, "-O", out_path], capture_output=True)
            print(f"Saved {name}")
        else:
            print(f"Already have {name}")

def fetch_tacoma():
    print("\nFetching Tacoma F-195s...")
    url = "https://www.tacomaschools.org/fs/pages/7712"
    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.content, "html.parser")
        
        for a in soup.find_all("a", href=True):
            text = a.text.strip()
            href = a['href']
            if "195" in text or "195" in href.lower():
                print(f"Found F-195 link: {text} - {href}")
                # We can download these later if they are direct PDFs
    except Exception as e:
        print(f"Error fetching Tacoma: {e}")

if __name__ == "__main__":
    fetch_evergreen()
    fetch_tacoma()
