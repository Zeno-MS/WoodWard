# WoodWard Investigation: Manual Action Plan

This guide outlines high-value actions you can take manually to advance the investigation. These tasks require human intuition/access or are blocked by anti-bot measures.

## 1. High-Priority Document Retrieval (BoardDocs)
**Goal**: Get the actual contracts to see the "Hourly Rate" markup.
**Action**:
1.  Log in to [VPS BoardDocs](https://go.boarddocs.com/wa/vpswa/Board.nsf/Public).
2.  Use the "Search" feature (magnifying glass) for these exact terms:
    *   `"Soliant"` (Expect ~58 hits)
    *   `"Amergis"` AND `"Maxim"` (Look for the name change/contract novation)
    *   `"ProCare Therapy"`
    *   `"Consolidated Healthcare"`
3.  **Download PDFs**: For every "Contract Approval" or "Consent Agenda" item found:
    *   Open the agenda item.
    *   Scroll to "Attachments".
    *   Download the PDF contract.
    *   **Save to**: `~/Projects/WoodWard/documents/contracts/` (Create this folder if needed).
    *   **Filename Convention**: `YYYY-MM-DD_VendorName_Contract.pdf`

## 2. The "Staffing Paradox" Verification
**Goal**: Confirm if the district is replacing $60/hr employees with $120/hr contractors.
**Action**:
1.  **LinkedIn Recon**: Search for "Vancouver Public Schools" + "Soliant" or "Amergis".
    *   Are people listing themselves as "Contractor at VPS"?
    *   Do any former VPS HR/Admin staff now work for these agencies?
2.  **Job Postings**: Look at current VPS job boards (`vps.k12.wa.us/careers`).
    *   Are there "Paraeducator" or "Nurse" openings that look like they are *purposely* unfilled (e.g., posted for months)?
    *   Agencies often pitch their services as a solution to "hard to fill" roles.

## 3. Executive Network Mapping
**Goal**: Detect potential conflicts of interest.
**Action**:
1.  **Jeff Snell & The Board**:
    *   Check Jeff Snell's past district (Camas). Did solitary/Amergis spending spike there during his tenure (2011-2021)?
    *   Search: `"Camas School District" Soliant contract`
2.  **Vendor Lobbying**:
    *   Check the [WA PDC (Public Disclosure Commission)](https://www.pdc.wa.gov/) for any donations from "Maxim", "Amergis", or "Soliant" to school board members.

## 4. The "Smoking Gun" Calculation
**Goal**: Calculate the "Vendor Premium".
**Instructions**:
If you find a contract PDF (from Step 1), look for the "Rate Sheet" (usually an exhibit at the end).
*   **Agency Rate**: e.g., $95/hr for an RN.
*   **District Rate**: Look at the S-275 data I pulled (`data/salaries/Top40_2324.csv` or similar). A typical district RN might be ~$55/hr + benefits.
*   **The Math**: If (Agency Rate) > (District Rate + 35% Benefits Load), the district is losing money on every hour.

## 5. Artifact Checklist
When you return, please dump any files you found into `~/Projects/WoodWard/documents/contracts/` and I will index them immediately.

**Key Leads to Follow:**
*   [ ] **The "Novation" Agreement**: Find the document where VPS formally acknowledged Maxim becoming Amergis. This often hides liability clauses.
*   [ ] **The 2022 Budget Meeting Minutes**: Read the minutes from when the 24% Superintendent raise was voted on. Was there public comment? Was it on the "Consent Agenda" (hidden) or a main item?
