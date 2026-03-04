import requests
import re
import json
import time
from bs4 import BeautifulSoup
from pathlib import Path

# URL from user navigation: https://go.boarddocs.com/wa/vpswa/Board.nsf/goto?open&id=ATBLRG573489
BASE_URL = "https://go.boarddocs.com/wa/vpswa/Board.nsf"
MEETING_LIST_URL = f"{BASE_URL}/BD-GetMeetingList?OpenAgent"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://go.boarddocs.com/wa/vpswa/Board.nsf/Public",
    "Origin": "https://go.boarddocs.com"
}

# New endpoint attempt: XML feed
XML_FEED_URL = f"{BASE_URL}/XML-ActiveMeetings"

def get_meetings(year="2024"):
    print(f"Fetching meetings from XML feed...")
    response = requests.get(XML_FEED_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to fetch XML feed: {response.status_code}")
        return []
    
    print("Response received.")
    print(response.text[:500])  # print start of XML
    return []

def main():
    print("WoodWard BoardDocs Scraper")
    
    meetings_2024 = get_meetings("2024")
    meetings_2025 = get_meetings("2025")
    
    all_meetings = meetings_2024 + meetings_2025
    
    print(f"\nTotal meetings found: {len(all_meetings)}")
    for m in all_meetings:
        print(f"{m.get('date')} - {m.get('name')}")

if __name__ == "__main__":
    main()
