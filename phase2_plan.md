# WoodWard Phase 2: Forensic Data Analysis & Acquisition

## Goal
Gather deep forensic data to build a case regarding budget mismanagement, specifically focusing on the "Staffing Paradox" (increasing headcount + increasing purchased services) and benchmarking against peer districts.

## User Review Required
> [!IMPORTANT]
> **Data Sources**: I will be accessing public state databases (OSPI, Fiscal Information) which may require downloading large files or parsing complex reports.

## Proposed Changes

### 1. BoardDocs API Reverse Engineering
#### [MODIFY] `workspaces/VPS-Board-Scraper/api_scraper.py`
*   Create a new script that bypasses the browser and directly queries the `BD-GetMeetingList` and related endpoints.
*   Use `requests` with proper headers to simulate a valid session.
*   Goal: Download all meeting agendas and attachments (PDFs) for 2020-2025.

### 2. Salary & Staffing Data Acquisition
#### [NEW] `workspaces/Data-Acquisition/acquire_ospi_data.py`
*   Script to download or scrape:
    *   **S-275 Personnel Reporting**: For salary data (Top 40 analysis).
    *   **Apportionment Reports**: For FTE staffing numbers.
*   Target Years: 2019-2020 through 2024-2025.

### 3. Comparable District Analysis
#### [NEW] `workspaces/Analysis/benchmarking.py`
*   Select Peer Districts: Evergreen, Tacoma, Spokane, Battle Ground.
*   Extract F-195 "Object 7" (Purchased Services) data for these districts.
*   Generate a comparison chart: `documents/visualizations/peer_comparison.png`.

## Verification Plan
### Automated Tests
*   Run `api_scraper.py` and verify it can list meetings without browser interaction.
*   Run `benchmarking.py` and verify the generation of the comparison chart.

### Manual Verification
*   Inspect the "Top 40 Salaries" list for accuracy and trends.
*   Review the "Staffing vs. Spending" correlation.
