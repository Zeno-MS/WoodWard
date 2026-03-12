# How The Key Numbers Were Built

This document shows how the main figures in this package were derived from public records.

You do not need to read code or run a database to use this guide. The goal is to show which numbers come straight from public documents, which are package calculations, and how to manually sanity-check the story's spine.

Bottom line: six headline figures matter most here. Three come straight from public records. Three are calculations built from public records. This guide shows, in plain language, how each one was derived.

## A Quick Rule Before You Start

There are two kinds of numbers in this package:

1. Numbers copied directly from public records.
2. Numbers calculated from public records.

This guide tells you which kind you are looking at each time.

## 1. The Board's Approximate $3 Million Amergis Figure

### What the claim is

The package says VPS board materials described the Amergis contract at approximately $3,000,000.

### What kind of number this is

Directly documented in a public board record.

### Where it comes from

- July 9, 2024 VPS board materials.
- See [SOURCE_VERIFICATION_LIST.md](SOURCE_VERIFICATION_LIST.md).

### What to look for

Look for the Amergis contract item in the consent agenda and the approximate cost language.

### What the package takes from that record

The package uses the board-facing figure of approximately $3,000,000.

### Why it matters

This is the public-facing estimate that frames the later comparison with what the district actually paid.

## 2. The $10,970,973 Amergis Figure for FY2024-25

### What the claim is

The package says VPS paid Amergis $10,970,973 in FY2024-25.

### What kind of number this is

Package calculation compiled from monthly district payment records.

### Where it comes from

- The monthly warrant-register record compiled in [vendor_summary_by_year.csv](../../01_Payment_Data/vendor_summary_by_year.csv).
- The package's summary in [FIGURES_SHEET.md](FIGURES_SHEET.md).
- Background on assembly in [DATA_DICTIONARY_AND_METHODOLOGY.md](../../DATA_DICTIONARY_AND_METHODOLOGY.md).

### What the package is doing

The package is not copying this number from one single board record. It is using a compiled year total built from monthly district payment records.

### A worked example of the logic

The district's monthly warrant registers are the payment paper trail. The package assembled those monthly records into fiscal-year totals and then isolated Amergis payments.

In plain English, the package is saying: when all FY2024-25 Amergis payments in the district's monthly payment records are pulled together, the total comes to $10,970,973.

### What you can manually verify without rebuilding everything

You can verify that:

1. The package consistently uses $10,970,973 as the FY2024-25 Amergis figure.
2. The package identifies monthly warrant registers as the underlying source.
3. The package includes the compiled yearly summary showing that total.

### Why it matters

This is the actual-payment side of the package's main contrast.

## 3. The $13,326,622 Total Staffing-Vendor Figure for FY2024-25

### What the claim is

The package says the core staffing-vendor total in FY2024-25 was $13,326,622.

### What kind of number this is

Package calculation compiled from public payment records.

### Where it comes from

- [vendor_summary_by_year.csv](../../01_Payment_Data/vendor_summary_by_year.csv)
- [FIGURES_SHEET.md](FIGURES_SHEET.md)

### What is included

For FY2024-25, the package's core vendor group includes these vendors:

- Maxim Healthcare: $15,716
- Amergis Healthcare: $10,970,973
- Soliant Health: $627,518
- ProCare Therapy: $1,712,415
- Pioneer Healthcare: $0

### The arithmetic

$15,716 + $10,970,973 + $627,518 + $1,712,415 + $0 = $13,326,622

### What is not included in the core figure

The package separately tracks vendors such as Aveanna Healthcare and Stepping Stones Group. Those amounts are shown in the payment summaries for transparency, but they are excluded from the core staffing-vendor total used in the articles and deliverables.

Pioneer is still part of the core vendor group even though it is $0 in FY2024-25 because it has non-zero payments in other years covered by the package.

### Why it matters

This is the broader outside-staffing figure against which the austerity narrative is measured.

## 4. The $10,970,973 Versus Approximate $3,000,000 Gap

### What the claim is

The package says the district's actual Amergis payments far exceeded the board-facing approximate figure.

### What kind of number this is

Simple comparison between one direct record figure and one package-compiled figure.

### The arithmetic

$10,970,973 - $3,000,000 = about $7,970,973

The package rounds that to about $7.97 million over the public-facing estimate.

### Why it matters

This is the easiest version of the story to understand: the board materials showed about $3 million, while the package says the district's own payment records add up to nearly $11 million for Amergis in that fiscal year.

## 5. The $10,592,850 Object 7 Overage

### What the claim is

The package says purchased-services spending ran about $10.59 million over budget in FY2024-25.

### What kind of number this is

Simple calculation from state budget-report figures.

### Where it comes from

- [FIGURES_SHEET.md](FIGURES_SHEET.md)
- The cited FY2024-25 F-195 state budget report.

### What the package takes from the record

- Budgeted purchased services: $36,738,206
- Actual purchased services: $47,331,056

### The arithmetic

$47,331,056 - $36,738,206 = $10,592,850

### What Object 7 means in plain English

Object 7 is Washington school-finance shorthand for purchased services, meaning money paid to outside entities rather than regular district payroll staff.

### Why it matters

This gives the Amergis story broader financial context: outside-services spending overall also ran above budget during the same crisis period.

## 6. The 87.2% Amergis/Maxim Concentration Figure

### What the claim is

The package says Amergis and Maxim together account for 87.2% of the core staffing-vendor total.

### What kind of number this is

Package calculation from the multi-year payment summary.

### Where it comes from

- [vendor_summary_by_year.csv](../../01_Payment_Data/vendor_summary_by_year.csv)
- [FIGURES_SHEET.md](FIGURES_SHEET.md)

### Important time-window note

This figure uses the all-years core total including FY2025-26 partial data.

### The numbers used

- Amergis all-years total including partial FY2025-26: $15,748,410
- Maxim all-years total: $12,326,099
- Combined Amergis/Maxim total: $28,074,509
- Core staffing-vendor total including partial FY2025-26: $32,189,236

### The arithmetic

$28,074,509 / $32,189,236 = about 87.2%

### Why the package treats Amergis and Maxim together

The package treats them as a continuity relationship because Amergis is presented as the renamed staffing division of Maxim. That framing is meant to describe vendor concentration over time, not to make a legal accusation.

### Why it matters

This supports the package's argument that one dominant vendor relationship came to control most of the district's staffing-vendor spend.

## 7. What Was Copied Directly From Records Versus Calculated

### Directly copied or directly quoted from records

- The approximate $3,000,000 board-facing Amergis figure.
- The F-195 budgeted and actual purchased-services figures.
- The DOJ settlement amount and date.

### Calculated from records

- The $10,970,973 FY2024-25 Amergis total.
- The $13,326,622 FY2024-25 core staffing-vendor total.
- The $10,592,850 purchased-services overage.
- The 87.2% Amergis/Maxim concentration figure.

## 8. Manual Cross-Checks You Can Do Yourself

If you want to test the package without rebuilding the dataset, do these checks:

1. Confirm the approximate $3,000,000 board figure.
2. Confirm that the package consistently uses $10,970,973 for FY2024-25 Amergis payments.
3. Confirm the purchased-services budget and actual figures in the F-195 reference.
4. Confirm the DOJ settlement source for Maxim.
5. Confirm that the package clearly tells you which numbers are direct-record figures and which are calculations.

If those five checks hold, the package's basic spine is solid.

## 9. Going Deeper

If you want to do a deeper audit, the package includes:

- The source list for the main public documents.
- The compiled payment summaries.
- A technical methodology note explaining how the package assembled the payment data.
- The underlying monthly payment records and related source files.

That deeper audit exists for transparency. It is not a prerequisite for evaluating whether the core reporting question is real.