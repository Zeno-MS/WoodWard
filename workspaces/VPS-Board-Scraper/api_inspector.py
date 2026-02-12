import requests
import json

# BoardDocs "Public" API endpoints reversed from typical sites
BASE_URL = "https://go.boarddocs.com/wa/vpswa/Board.nsf"
MEETING_LIST_URL = f"{BASE_URL}/BD-GetMeetingList?OpenAgent"

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Origin": "https://go.boarddocs.com",
    "Referer": "https://go.boarddocs.com/wa/vpswa/Board.nsf/Public"
}

def probe_api():
    print(f"Probing: {MEETING_LIST_URL}")
    
    # Try creating a session to handle cookies
    session = requests.Session()
    
    # 1. Hit the main page first to get cookies
    try:
        print("1. Visiting main page for cookies...")
        main_resp = session.get(f"{BASE_URL}/Public", headers=HEADERS)
        print(f"   Status: {main_resp.status_code}")
        print(f"   Cookies: {session.cookies.get_dict()}")
    except Exception as e:
        print(f"   Failed: {e}")

    # 2. Try the Meeting List endpoint
    try:
        print("\n2. Requesting Meeting List (POST)...")
        # BoardDocs often expects a POST for this, sometimes with payload
        payload = {
            "current_committee_id": "" 
        }
        resp = session.post(MEETING_LIST_URL, headers=HEADERS, data=payload)
        
        print(f"   Status: {resp.status_code}")
        print(f"   Content-Type: {resp.headers.get('Content-Type')}")
        print("   Response Preview:")
        print(resp.text[:500])
        
        if resp.status_code == 200:
            with open("data/api_meeting_list_probe.txt", "w") as f:
                f.write(resp.text)
            print("   Saved response to data/api_meeting_list_probe.txt")
            
    except Exception as e:
        print(f"   Failed: {e}")

if __name__ == "__main__":
    probe_api()
