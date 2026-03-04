import asyncio
from playwright.async_api import async_playwright
import sqlite3
import os
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://go.boarddocs.com/wa/vpswa/Board.nsf/Public"
START_DATE = 20200801
END_DATE = 20250831
# Set this to True to test on a single month/meeting. If False, runs the whole 5-year scraper.
TEST_MODE = False

def setup_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("documents/packets", exist_ok=True)
    os.makedirs("documents/screenshots", exist_ok=True)
    
    conn = sqlite3.connect("data/board_meetings.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            date TEXT,
            datenumber INTEGER,
            type TEXT,
            url TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agenda_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            item_unique_id TEXT,
            item_title TEXT,
            item_text TEXT,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agenda_item_id INTEGER,
            filename TEXT,
            url TEXT,
            saved_path TEXT,
            FOREIGN KEY(agenda_item_id) REFERENCES agenda_items(id)
        )
    ''')
    conn.commit()
    return conn

async def phase_1_enumeration(page, conn):
    print(f"--- Phase 1: Meeting Enumeration ---")
    print(f"Navigating to {BASE_URL}")
    await page.goto(BASE_URL)
    await page.wait_for_load_state("networkidle")
    
    # Click Meetings tab
    try:
        meetings_tab = page.locator("text='Meetings'").first
        if await meetings_tab.is_visible():
            print("Clicking Meetings tab...")
            await meetings_tab.click()
            await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Error finding Meetings tab: {e}")
        return

    print("Parsing full HTML for meetings...")
    full_html = await page.content()
    soup = BeautifulSoup(full_html, "html.parser")
    
    meetings = soup.find_all("a", class_="meeting")
    print(f"Found {len(meetings)} total meetings in DOM.")
    
    cursor = conn.cursor()
    target_count = 0
    
    for m in meetings:
        try:
            date_num = int(m.get("datenumber", 0))
            if START_DATE <= date_num <= END_DATE:
                m_id = m.get("unique")
                date_text = m.find("strong").text.strip() if m.find("strong") else ""
                type_text = m.find_all("div")[-1].text.strip() if m.find_all("div") else "Meeting"
                
                # Filter out Cancelled
                if "CANCELLED" in type_text.upper():
                    continue
                    
                # We want Regular, Special, Work Session
                meeting_types = ["regular", "special", "work session", "committee"]
                if not any(t in type_text.lower() for t in meeting_types):
                     continue

                url = f"{BASE_URL}?open&id={m_id}"
                
                cursor.execute("INSERT OR IGNORE INTO meetings (id, date, datenumber, type, url, status) VALUES (?, ?, ?, ?, ?, ?)",
                               (m_id, date_text, date_num, type_text, url, 'pending'))
                target_count += 1
        except Exception as e:
            pass
            
    conn.commit()
    print(f"Finished Phase 1. Inserted/Verified {target_count} target meetings in DB.")

async def phase_2_extraction(page, conn):
    print(f"\n--- Phase 2: Packet Extraction ---")
    cursor = conn.cursor()
    
    if TEST_MODE:
        cursor.execute("SELECT id, url, date FROM meetings WHERE status = 'pending' ORDER BY datenumber DESC LIMIT 2")
    else:
        cursor.execute("SELECT id, url, date FROM meetings WHERE status = 'pending' ORDER BY datenumber ASC")
        
    pending_meetings = cursor.fetchall()
    print(f"Found {len(pending_meetings)} pending meetings to scrape.")
    
    for meeting_id, url, meeting_date in pending_meetings:
        print(f"Scraping Meeting: {meeting_date} ({meeting_id})")
        print(f"URL: {url}")
        
        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2) # Respectful delay
            
            # Click view agenda
            btn = page.locator("#btn-view-agenda").first
            if await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(3000)
            else:
                print("  No 'View the Agenda' button found. Trying to proceed anyway...")
            
            # Wait for items to populate
            try:
                await page.wait_for_selector("li.item", timeout=5000)
                items = await page.locator("li.item").all()
            except:
                print("  No agenda items found after 5s timeout. Skipping.")
                cursor.execute("UPDATE meetings SET status = 'failed' WHERE id = ?", (meeting_id,))
                conn.commit()
                continue
                
            print(f"  Found {len(items)} agenda items.")
            
            for i in range(len(items)):
                try:
                    # Need to query locator again to prevent staleness
                    item_elems = await page.locator("li.item").all()
                    if i >= len(item_elems): break
                    item = item_elems[i]
                    
                    # Ensure element is visible/scroll into view (boarddocs menus are long)
                    await item.scroll_into_view_if_needed()
                    
                    item_unique_id = await item.get_attribute("unique")
                    item_title = await item.get_attribute("xtitle")
                    
                    print(f"    -> Item {i+1}: {item_title[:50]}...")
                    await item.click()
                    
                    # Wait for right pane to load this specific item's details
                    try:
                        await page.wait_for_selector(f"#agendaitemlastModified-{item_unique_id}", timeout=2000)
                    except:
                        # Sometimes there is no lastModified span, just wait a bit
                        await asyncio.sleep(1)
                    
                    # Extract item text
                    right_pane = page.locator("#view-agenda-item")
                    item_text = await right_pane.inner_text()
                    
                    # Save to DB
                    cursor.execute("INSERT INTO agenda_items (meeting_id, item_unique_id, item_title, item_text) VALUES (?, ?, ?, ?)",
                                   (meeting_id, item_unique_id, item_title, item_text))
                    agenda_item_id = cursor.lastrowid
                    
                    # Extract attachments
                    file_links = await page.locator("#view-agenda-item a.public-file").all()
                    for f in file_links:
                        href = await f.get_attribute("href")
                        fname = await f.inner_text()
                        
                        full_url = href if href.startswith("http") else f"https://go.boarddocs.com{href}"
                        clean_fname = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', fname.strip())
                        
                        # Fix date format for file path
                        clean_date = re.sub(r'[^0-9A-Za-z]', '', meeting_date.split(',')[1] if ',' in meeting_date else meeting_date)[:10]
                        saved_path = f"documents/packets/{clean_date}_{item_unique_id}_{clean_fname}"
                        if not saved_path.endswith(".pdf"): saved_path += ".pdf"
                        
                        print(f"      Downloading: {clean_fname}")
                        
                        # Download PDF synchronously (could be async, but keeping simple and polite here)
                        try:
                            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/121.0.0.0"}
                            resp = requests.get(full_url, headers=headers, timeout=15)
                            if resp.status_code == 200:
                                with open(saved_path, "wb") as pdf_file:
                                    pdf_file.write(resp.content)
                                    
                                cursor.execute("INSERT INTO attachments (agenda_item_id, filename, url, saved_path) VALUES (?, ?, ?, ?)",
                                               (agenda_item_id, fname.strip(), full_url, saved_path))
                        except Exception as dl_e:
                            print(f"      Failed to download PDF: {dl_e}")
                            
                except Exception as e:
                    print(f"    Error processing item {i+1}: {e}")
            
            # Mark meeting complete
            cursor.execute("UPDATE meetings SET status = 'complete' WHERE id = ?", (meeting_id,))
            conn.commit()
            
        except Exception as e:
            print(f"  Error processing meeting {meeting_id}: {e}")
            cursor.execute("UPDATE meetings SET status = 'error' WHERE id = ?", (meeting_id,))
            conn.commit()

async def run_scraper():
    conn = setup_db()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await phase_1_enumeration(page, conn)
        await phase_2_extraction(page, conn)
        
        await browser.close()
        conn.close()
        
    print("\nScraping Run Finished!")

if __name__ == "__main__":
    asyncio.run(run_scraper())
