import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime
import os
import requests
import re

# URLs and Vendors
BASE_URL = "https://go.boarddocs.com/wa/vpswa/Board.nsf/Public"
VENDORS = ["Soliant", "Maxim", "Amergis", "Pioneer"]
OUTPUT_FILE = "data/vendor_mentions.csv"

async def run():
    print("Starting Smart Board Scraper (Robust Mode)...")
    results = []
    
    # Ensure directories exist
    os.makedirs("documents/screenshots", exist_ok=True)
    os.makedirs("documents/contracts", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Navigating to {BASE_URL}")
        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="documents/screenshots/page_loaded.png")

        # Debug: Print all visible inputs
        inputs = await page.locator("input:visible").all()
        print(f"Found {len(inputs)} visible inputs.")
        for i, inp in enumerate(inputs):
            try:
                placeholder = await inp.get_attribute("placeholder")
                print(f"  Input {i}: placeholder='{placeholder}'")
            except:
                pass

        for vendor in VENDORS:
            print(f"Searching for: {vendor}")
            match_count = 0
            
            try:
                # STRATEGY 1: Click the magnifying glass icon if it exists (common in BoardDocs)
                # Usually top right
                # Try generic search toggles
                potential_toggles = [
                    "#btn-search", # Confirmed correct ID
                    "a[title='Search']",
                    "button[aria-label='Search']",
                    ".featured-search-toggler",
                    "#searchTerm"
                ]
                
                search_input = None
                
                # Check for explicit overlay input first
                overlay_input = page.locator("#searchstring").first
                if await overlay_input.is_visible():
                     print("  Found overlay search input directly.")
                     search_input = overlay_input
                else: 
                    # Check directly for visible search box first
                    search_box = page.locator("input[placeholder='Search']").first
                    if await search_box.is_visible():
                        print("  Found search box directly.")
                        search_input = search_box
                    else:
                        # Try to click a toggle
                        print("  Search box hidden. Looking for toggles...")
                        for selector in potential_toggles:
                            try:
                                elem = page.locator(selector).first
                                if await elem.is_visible():
                                    print(f"  Clicking toggle: {selector}")
                                    await elem.click()
                                    await page.wait_for_timeout(500)
                                    break
                            except:
                                pass
                    
                    # Look again for search box
                        if await search_box.is_visible():
                            print("  Found search box after toggle.")
                            search_input = search_box
                    
                    # If still not found, check for overlay input again
                    if not search_input:
                        overlay_input = page.locator("#searchstring").first
                        if await overlay_input.is_visible():
                            print("  Found overlay search input after toggle.")
                            search_input = overlay_input
                
                if search_input:
                    await search_input.click()
                    await search_input.fill(vendor)
                    await search_input.press("Enter")
                    
                    # Wait for results
                    await page.wait_for_timeout(3000)
                    await page.screenshot(path=f"documents/screenshots/results_{vendor}.png")
                    
                    # Count results
                    # Look for "Meethings" or "Agenda Items"
                    content_text = await page.inner_text("body")
                    
                    # Simple substring count in body text
                    # This is a proxy for actual verification
                    match_count = content_text.lower().count(vendor.lower())
                    # Wait for results
                    try:
                        await page.wait_for_selector(".result", timeout=5000)
                        results_loc = page.locator(".result")
                        count = await results_loc.count()
                        print(f"  Found {count} result items.")
                        
                        # Verify text content of results to be sure
                        match_count = 0
                        for i in range(count):
                            item = results_loc.nth(i)
                            text = await item.inner_text()
                            if vendor.lower() in text.lower():
                                match_count += 1
                                
                            # CHECK FOR DOWNLOADABLE FILES
                            # Check if item itself is a file
                            class_attr = await item.get_attribute("class")
                            is_file = "filepublic" in (class_attr or "")
                            
                            if is_file:
                                # The span is inside it.
                                # Let's look for the span with href specifically
                                
                                # Re-query inside the item
                                link_span = item.locator("span.file").first
                                if await link_span.count() > 0:
                                    href = await link_span.get_attribute("href")
                                    if href:
                                        full_url = f"https://go.boarddocs.com{href}"
                                        print(f"    Found file: {full_url}")
                                        
                                        # Clean filename from text
                                        # Use regex to make it safe
                                        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', text.strip())[:50]
                                        if not safe_name.endswith(".pdf"):
                                            safe_name += ".pdf"
                                            
                                        download_path = f"documents/contracts/{vendor}_{i}_{safe_name}"
                                        
                                        # Download
                                        try:
                                            print(f"      Downloading to {download_path}...")
                                            resp = requests.get(full_url, headers={
                                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                                            })
                                            with open(download_path, "wb") as f_out:
                                                f_out.write(resp.content)
                                            print("      Download complete.")
                                        except Exception as dl_err:
                                            print(f"      Download failed: {dl_err}")

                        print(f"  Verified {match_count} items containing '{vendor}'.")
                        
                    except Exception as e:
                        print(f"  No results found (timeout waiting for .result): {e}")
                        match_count = 0
                    
                else:
                    print(f"  Could not find search input for {vendor}")
                    await page.screenshot(path=f"documents/screenshots/error_{vendor}_no_input.png")

                results.append({
                    "Vendor": vendor,
                    "Mentions": match_count,
                    "Status": "Success" if match_count > 0 else "No Results/Hidden",
                    "Timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                print(f"  Error searching for {vendor}: {e}")
                results.append({
                    "Vendor": vendor,
                    "Mentions": 0,
                    "Error": str(e),
                    "Status": "Error",
                    "Timestamp": datetime.now().isoformat()
                })

            # Refresh for next iteration to clear state
            await page.reload()
            await page.wait_for_load_state("networkidle")

        await browser.close()

    # Save summary results
    with open(OUTPUT_FILE, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["Vendor", "Mentions", "Status", "Timestamp", "Error"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
