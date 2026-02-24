import requests
from bs4 import BeautifulSoup
import os

DOCS_DIR = "documents/F195"
os.makedirs(DOCS_DIR, exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_camas():
    print("\nFetching Camas F-195s...")
    url = "https://www.camas.wednet.edu/about-csd/budget-finance/"
    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.content, "html.parser")
        
        count = 1
        for a in soup.find_all("a", href=True):
            text = a.text.strip()
            href = a['href']
            if "195" in text or "195" in href.lower() or "budget" in text.lower():
                if href.endswith(".pdf") and "195" in href.lower():
                    full_url = href if href.startswith("http") else "https://www.camas.wednet.edu" + href
                    out_path = os.path.join(DOCS_DIR, f"Camas_F195_{count}.pdf")
                    print(f"Downloading {full_url} to {out_path}...")
                    try:
                        r = requests.get(full_url, headers=headers)
                        with open(out_path, 'wb') as f:
                            f.write(r.content)
                        print(f"Saved {out_path}")
                        count += 1
                    except Exception as e:
                        print(f"Failed to download {full_url}: {e}")
    except Exception as e:
        print(f"Error fetching Camas: {e}")

if __name__ == "__main__":
    fetch_camas()
