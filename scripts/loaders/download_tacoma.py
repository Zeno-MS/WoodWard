import requests
from bs4 import BeautifulSoup
import os

DOCS_DIR = "documents/F195"
os.makedirs(DOCS_DIR, exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def fetch_tacoma():
    print("\nFetching Tacoma F-195s...")
    url = "https://www.tacomaschools.org/fs/pages/7712"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")
    
    count = 1
    for a in soup.find_all("a", href=True):
        text = a.text.strip()
        href = a['href']
        if "195" in text or "195" in href.lower():
            full_url = href if href.startswith("http") else "https://www.tacomaschools.org" + href
            out_path = os.path.join(DOCS_DIR, f"Tacoma_F195_{count}.pdf")
            print(f"Downloading {full_url} to {out_path}...")
            
            try:
                r = requests.get(full_url, headers=headers)
                with open(out_path, 'wb') as f:
                    f.write(r.content)
                print(f"Saved {out_path}")
            except Exception as e:
                print(f"Failed to download {full_url}: {e}")
            count += 1

if __name__ == "__main__":
    fetch_tacoma()
