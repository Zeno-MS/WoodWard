# BoardDocs Manual Download Guide
**Goal:** Securely download VPS Board Meeting Minutes to `documents/minutes/` without exposing scraper IP.

## 1. Access the Board Portal
1. **Ensure your VPN is connected** (for privacy).
2. Open your browser to:  
   [https://go.boarddocs.com/wa/vpswa/Board.nsf/Public](https://go.boarddocs.com/wa/vpswa/Board.nsf/Public)

## 2. Navigate to Meetings
1. Click the **"Meetings"** tab in the top-right corner.
2. In the left sidebar, you will see a year (e.g., "2024"). Click it to expand.
3. You will see a list of meetings. Focus on **"Regular Board Meeting"** entries.

## 3. Download Minutes
*Note: Agendas show what *might* happen. Minutes show what *did* happen (contracts approved).*

1. Select a meeting (e.g., "Jan 23, 2024").
2. Click **"View the Agenda"** button.
3. In the agenda view, look for a **"Minutes"** item (usually near the top, "Approval of Minutes").
   - *Wait, typically Minutes are approved in the NEXT meeting. So Jan Minutes are in Feb meeting.*
   - **Better Strategy:** Look for the **"Consent Agenda"** item. This is where contracts/warrants are typically listed.
4. Click on **"Consent Agenda"** or **"Business - Action Items"**.
5. Look for **attachment icons** (PDF symbol) next to items like "Voucher Warrants" or "Contract Approvals".
6. Click the attachment to open/download.

## 4. Save Files
1. Create a folder: `~/Projects/WoodWard/documents/minutes/`
2. Save files with this naming convention:
   `YYYY-MM-DD_Type_Description.pdf`
   
   Examples:
   - `2024-01-23_Consent_Warrants.pdf`
   - `2024-02-13_Minutes_Approved.pdf`

## 5. What to Look For
We need data on **Vendors** and **Contract Amounts**. Prioritize:
- **"Warrant Vouchers"** (Lists all checks/payments)
- **"Personnel Report"** (Hiring/Firing)
- **"resolution"** or **"contract"** attachments.

Once you have 3-5 PDFs, let me know, and I will extract the data!
