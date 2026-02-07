# Phase 1 Task List — Document Acquisition

## Architect Tasks (Manual / Public Records)

- [ ] **File public records request** with VPS under RCW 42.56 for:
  - F-195 and F-195F reports (FY 2018-2023) — *2024-25 and 2025-26 obtained*
  - All contracts with Soliant Health, Maxim Healthcare, Amergis, Pioneer Healthcare (2018-present)
  - All consent agenda items approving vendor contracts (2020-present)
- [x] **Pull F-195 data from OSPI website** — Downloaded 4 reports to `documents/F195/`
- [ ] **Search WA Secretary of State** for Amergis, Maxim, Soliant, Pioneer corporate filings
- [ ] **Download VEA CBA** for salary schedule extraction

## Neo Tasks (Antigravity Workspaces)

### Workspace 1: VPS-F195-Analysis
- [ ] Extract Object 7 totals by fund (2018-2025)
- [ ] Extract Object 2 & 3 (salaries) for comparison
- [ ] Calculate Object 7 % of General Fund by year
- [ ] Generate trend chart with enrollment overlay

### Workspace 2: VPS-Vendor-Tracking
- [ ] Scrape VPS board meeting archives (2020-2025)
- [ ] Search for: Soliant, Maxim, Amergis, Pioneer
- [ ] Extract: date, agenda item, section, dollar amount, vote outcome
- [ ] Generate CSV of all vendor mentions

### Workspace 3: VPS-Peer-Comparison
- [ ] Extract Object 7 % of General Fund for:
  - Vancouver SD #37
  - Evergreen SD #114
  - Battle Ground SD #119
  - Camas SD #117
- [ ] Calculate Object 7 per-pupil by district
- [ ] Generate comparative chart

## Perplexity Tasks (OSINT)

- [x] Search: Amergis / Maxim Healthcare WA Secretary of State filings *(Tool: ccfs.sos.wa.gov)*
- [x] Search: Maxim Healthcare Medicaid fraud settlement 2011 *($150M settlement confirmed)*
- [ ] Search: OSPI Safety Net reimbursement data availability
- [x] Search: Vancouver Public Schools F-195 OSPI download links *(Found 2024-25 and 2025-26 on vansd.org)*

## NotebookLM Setup

- [ ] Create dedicated notebook for investigation
- [ ] Upload research documents (Contractor Spending, Budget Shortfall, Budget Deep Dive)
- [ ] Upload VEA CBA when obtained

---

## Chief Checkpoint (End of Phase 1)

Questions to answer before proceeding:

1. Do we have actual Object 7 dollar figures? If no, pause until obtained.
2. Have records requests been filed? What's the estimated response timeline?
3. Has Neo's OSPI extraction been verified against a known data point?
4. Have Antigravity agents produced verified artifacts?
