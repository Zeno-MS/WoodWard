# Handoff: Building the BoardDocs Scraper

## 1. The Objective
We need a robust web scraper to extract all board meeting agendas, minutes, and attached PDF packets from the Vancouver Public Schools (VPS) BoardDocs portal from **August 2020 through August 2025**.

The ultimate goal is to ingest this text into our local `LanceDB` instance so the AI investigation team (Sentinel, WoodWard) can perform semantic searches on board discussions regarding specific staffing agencies (Amergis, Maxim, Soliant) and budget deficits.

## 2. The Target System
- **Portal:** [VPS BoardDocs Public Portal](https://go.boarddocs.com/wa/vpswa/Board.nsf/Public)
- **Architecture:** BoardDocs is a heavily JavaScript-driven SPA (Single Page Application). Standard HTTP requests (`requests`/`BeautifulSoup`) will not work out of the box because the meeting IDs and document links are generated dynamically by the browser.

## 3. Existing Code & Context
You are working in the `workspaces/VPS-Board-Scraper` directory. 

There is an existing script here called `smart_scraper.py`. 
- **What it does:** It uses `playwright` to open the BoardDocs URL, attempts to find the search bar, and types in vendor names ("Amergis", "Soliant") to get a raw count of how many search results appear.
- **What it lacks:** It does *not* systematically iterate through the calendar. It does *not* download the actual HTML agendas or the attached PDF packets. It was a blunt force tool just to see if the vendors were mentioned at all.

## 4. Your Requirements for the New Scraper

Please build a new Python script (e.g., `systematic_scraper.py`) using **Playwright** (since it's already installed and working in `smart_scraper.py`) that executes the following logic:

### Phase 1: Meeting Enumeration
1. Navigate to the main BoardDocs meetings tab (usually accessed by clicking the "Meetings" button in the top right of the BoardDocs UI).
2. Iterate through the years/months in the navigation tree for the target window (Aug 2020 - Aug 2025).
3. For every "Regular", "Special", or "Work Session" meeting, extract the meeting Date and the internal BoardDocs Meeting ID/URL.

### Phase 2: Packet Extraction
1. For each meeting identified in Phase 1, navigate to the detailed agenda view.
2. Iterate through every agenda item (e.g., "1.01 Call to Order", "4.05 Consent Agenda: Personnel").
3. Extract the text of the agenda item.
4. **Crucial Step:** Check if there are any attached files (PDFs, DOCXs). If there are, extract the direct download URL for the file or trigger the download directly via Playwright.

### Phase 3: Storage
1. Save the metadata for all meetings and agenda items into a structured CSV or SQLite table in the `data/` directory.
2. Save all downloaded PDF attachments into `documents/packets/` using a clear naming convention (e.g., `YYYY-MM-DD_ItemNumber_Filename.pdf`).

## 5. Defensive Scraping Rules
- **Respect load:** Add `asyncio.sleep(2)` or similar waits between page navigations and clicks to avoid overwhelming the district's server and getting IP banned.
- **Fail gracefully:** BoardDocs layouts occasionally change for special meetings. Use `try/except` blocks around specific selector clicks so the scraper logs the error and moves to the next meeting rather than crashing entirely.
- **Headless mode:** Run Playwright in `headless=False` for the first few test runs so you can visually confirm the selectors are clicking the right elements in the BoardDocs tree. Once verified, switch to `headless=True`.

## 6. Next Steps
Review `smart_scraper.py` to see which Playwright selectors successfully worked in the past, then begin architecting the new `systematic_scraper.py`.
