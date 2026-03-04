# Evidence Package: What Changed and Why

*Updated March 2, 2026*

After assembling the initial evidence package, I went back and added the raw source materials so you can verify everything independently. This document tracks what was added, removed, or changed.

## Removed

- `object7_trend_data.csv` from Budget Data. Replaced by the finalized `object7_trend_FY2020_FY2025.csv`. The old version was an earlier draft with a different column layout.
- Two outdated cost model files (`cost_model.csv` and `cost_model_internal_vs_vendor.csv`). The only remaining cost model is `internal_vs_vendor_cost_model.csv`, which includes the updated BCBA/BT role additions.

## Added

**Raw data and source code (`00_Extraction_Scripts/` and `00_Data_Corpus/`)**

I included the Python scripts used to scrape and parse the BoardDocs warrant registers, and the SQLite database (`woodward.db`) containing all 25,578 deduplicated payment records. This way you can query the data directly rather than relying on my CSV summaries.

The scripts were sanitized before inclusion. API keys, IP addresses, and any identifying information were removed. The database had absolute file paths (which contained my local machine username) converted to relative paths.

**Warrant register PDFs (`05_Source_Documents/Warrant_Registers/`)**

153 warrant register PDFs are included. These provide 100% coverage of all 25,578 payment records, and you can verify the CSV totals against primary source documents directly.

**Collective bargaining agreements (`05_Source_Documents/CBAs/`)**

The VEA Collective Bargaining Agreement (2024-27) and the VAESP Salary Schedule. These are the source documents behind the internal fully-loaded cost calculations in the cost model.

**External source documents (`05_Source_Documents/`)**

Four key source documents that were previously listed as external links: the DOJ Maxim settlement press release, The Columbian's coverage of the $35M budget cuts, the OSPI SECC 21-32 complaint decision, and the OPB/InvestigateWest investigation. Retrieved and included as PDFs so you don't have to chase dead links.

## Updated

The Right of Reply index (`07_Right_of_Reply/INDEX.md`) was corrected to note that the sender email address (`tubthumping@tutamail.com`) is intentionally retained as a contact point, not redacted. Previous language incorrectly stated all identifiers had been removed.

## Querying the Database

The `woodward.db` file is a standard SQLite database. You can open it with:

- **DB Browser for SQLite** (free, all platforms, easiest option): download from sqlitebrowser.org, open the file, and browse or query.
- **Command line on Mac/Linux**: `sqlite3 woodward.db` in your terminal. Type `.tables` to see the schema, then run SQL against it.
- **Command line on Windows**: download sqlite3.exe from sqlite.org/download.html and point it at the file.

The database contains 10 tables covering all 25,578 payment records, board votes, and contract data.
