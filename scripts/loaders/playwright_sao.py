import os
import time
from playwright.sync_api import sync_playwright

DOCS_DIR = os.path.abspath("documents/SAO_Audits")
os.makedirs(DOCS_DIR, exist_ok=True)

def download_sao_reports():
    print(f"Downloading SAO reports to {DOCS_DIR}...")
    
    with sync_playwright() as p:
        # Launch browser with downloads enabled to our specific directory
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        # Navigate to the SAO reports page
        page.goto("https://sao.wa.gov/reports-data/audit-reports")
        page.wait_for_load_state('networkidle')
        
        # We need to wait for the Angular app to load
        time.sleep(5)
        
        # Fill in the government name
        page.fill("input[placeholder='Search by Government Name']", "Vancouver School District No. 37")
        time.sleep(1)
        
        # Set start date to Jan 1, 2020
        page.fill("input[name='startDate']", "01/01/2020")
        
        # Set end date to today
        page.fill("input[name='endDate']", "12/31/2025")
        
        # Click search button
        page.click("button.search-button") # Adjust selector if needed based on actual DOM
        # Try a more generic button click if specific class fails
        try:
            page.click("button:has-text('Search')")
        except:
            pass
            
        time.sleep(5)
        
        # Handle pagination if necessary
        while True:
            # Find all download links on the current page
            # SAO usually has a table with "Download" or "View" links that are PDFs
            rows = page.query_selector_all("tr")
            for row in rows:
                if "Vancouver School District" in row.inner_text():
                    try:
                        # Find the link in this row
                        link = row.query_selector("a[href$='.pdf']")
                        if link:
                            href = link.get_attribute("href")
                            # Trigger download
                            with page.expect_download() as download_info:
                                link.click()
                            download = download_info.value
                            filepath = os.path.join(DOCS_DIR, download.suggested_filename)
                            download.save_as(filepath)
                            print(f"Downloaded: {filepath}")
                    except Exception as e:
                        print(f"Error downloading a row: {e}")
            
            # Check for next page
            try:
                next_btn = page.query_selector("button.next-page:not([disabled])")
                if next_btn:
                    next_btn.click()
                    time.sleep(3)
                else:
                    break
            except:
                break
                
        browser.close()

if __name__ == "__main__":
    download_sao_reports()
