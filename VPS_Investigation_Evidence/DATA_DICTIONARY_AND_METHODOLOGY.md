# DATA DICTIONARY & EXTRACTION METHODOLOGY
*Technical companion guide for data journalists and researchers verifying the Vancouver Public Schools evidence package.*

## 1. Overview
This investigation relies on a 25,578-record dataset of vendor payments covering Fiscal Years 2020-21 through 2025-26 (partial). 25,578 deduplicated payment records extracted from 125 distinct warrant register PDFs. 153 source PDFs are included in this package, providing 100% coverage of the underlying payment data. 

To ensure the integrity of the `$32.1M` primary-vendor headline figure, the extraction process utilized strict deduplication and normalization protocols.

## 2. Extraction & Deduplication Methodology
Warrant registers in Washington State school districts frequently contain duplicate line items when payments are split across multiple internal accounting codes, or when original warrants are voided and re-issued. Simply summing the raw PDF lines will result in inflated figures.

**The Deduplication Protocol:**
1. **Raw OCR/Text Extraction:** All 153 primary F-195/Warrant Register PDFs were parsed row-by-row.
2. **Key Generation:** A unique composite key was generated for every payment record consisting of: `[Date] + [Payee Name String] + [Exact Dollar Amount]`.
3. **Collision Handling:** If multiple lines in the same PDF shared the exact same Date, Payee, and Amount, they were treated as a single warrant payment to prevent double-counting split-accounting lines.
4. **Warrant Number Matching:** Where OCR successfully extracted the 6-digit or 9-digit warrant number, it was cross-referenced to ensure voided warrants (which appear as negative amounts or zeroed lines) did not corrupt the total net cash outlay.

*Note: The resulting dataset (25,578 records) represents the most conservative, mathematically sound floor of district spending. The actual spending may be slightly higher if identical payments to the same vendor were legitimately processed on the exact same day, but deduplication ensures zero risk of overstating the totals.*

## 3. Data Dictionary (`01_Payment_Data/vendor_payments_all_records.csv`)

| Column Name | Data Type | Description |
|---|---|---|
| `Date` | String | The execution date of the warrant (MM/DD/YYYY). |
| `Payee` | String | The exact entity name as it appeared on the warrant register (e.g., "AMERGIS HEALTHCARE STAFFING INC"). |
| `Amount` | Float | The USD dollar amount of the warrant. |
| `Warrant Number` | String | The 6- or 9-digit district warrant tracker. May be blank if OCR could not isolate it from the accounting strings. |
| `Fiscal Year` | String | Bucketed strictly as September 1 through August 31, aligning with Washington State OSPI reporting standards. e.g., A warrant dated 01/02/2024 is classified as FY2023-24. |

## 4. Normalization Notes
- **Amergis/Maxim:** In 2022, Maxim Healthcare Services rebranded its educational staffing division to Amergis. Both entities operate from the same Columbia, Maryland headquarters. For the purpose of the investigation's market concentration thesis (87.2%), payments to "Maxim" and "Amergis" are combined.
- **Aveanna & Stepping Stones:** These vendors appear in the raw 25,578-record database but are excluded from the canonical "5 primary vendor" $32.1M total cited in the articles, as their services frequently involve 1-on-1 specialized medical care rather than classroom staffing substitution. They are retained in the master export for full transparency. 

## 5. Verification
A journalist can verify the dataset's accuracy by randomly selecting any record in `vendor_payments_all_records.csv`, locating the corresponding board meeting date on the VPS BoardDocs portal, opening the Warrant Register PDF for that month, and confirming the line item.
