import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime
import os

# URLs and Vendors
BASE_URL = "https://go.boarddocs.com/wa/vpswa/Board.nsf/Public"
VENDORS = ["Soliant", "Maxim", "Amergis", "Pioneer"]
OUTPUT_FILE = "data/vendor_mentions.csv"

async def run():
    print("Starting Smart Board Scraper (Robust Mode)...")
    results = []
    
    # Ensure directories exist
    os.makedirs("documents/screenshots", exist_ok=True)
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
                    "a[title='Search']",
                    "button[aria-label='Search']",
                    ".featured-search-toggler",
                    "#searchTerm" # valid ID sometimes
                ]
                
                search_input = None
                
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
                    
                    # Look again
                    search_box = page.locator("input[placeholder='Search']").first
                    if await search_box.is_visible():
                        print("  Found search box after toggle.")
                        search_input = search_box
                
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
                    print(f"  Found {match_count} occurrences of '{vendor}' in page text.")
                    
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
