---
description: Protocol for logging and analyzing OSPI right-of-reply responses
---

# OSPI Response Logging Workflow

When the USER provides a new response from OSPI (Office of Superintendent of Public Instruction) or other entities regarding the Right-of-Reply requests, follow this protocol to ingest and document the response:

## 1. Analyze the Response
- Identify the **Sender** (Name, Title, Department, Email, Phone).
- Identify the **Date and Time** received.
- Determine exactly which of the **Outstanding Questions** were answered.
- Extract the **Key content** and evaluate the **Evidence value** (e.g., does it confirm data, point to systemic gaps, or provide legal frameworks?).
- Identify any **Action items** (like follow-ups, saving files, or updating indexes).

## 2. Update the OSPI Response Log
File: `/Users/chrisknight/Projects/WoodWard/workspaces/OSPI_Response_Log_for_Antigravity.md`
- Add a new section for the response following the existing format (e.g., `## Response #3: [Name]`).
- Include subheaders for `Key content`, `Evidence value`, and `Action items`.
- Update the **Outstanding Questions** section by noting which questions were answered and adjusting the "unanswered" count.
- Add a new row to the **Summary for INDEX.md update** table at the bottom of the log.

## 3. Update the Right of Reply Index
File: `/Users/chrisknight/Projects/WoodWard/VPS_Investigation_Evidence/07_Right_of_Reply/INDEX.md`
- Update the canonical index of right-of-reply correspondence to reflect the new OSPI response, ensuring it matches the data added to the log table.

## 4. Save the Source Material
- Ensure the raw email or response document is saved in the `/Users/chrisknight/Projects/WoodWard/VPS_Investigation_Evidence/07_Right_of_Reply/` directory (inform the USER if they need to save an email as a markdown file with a specific filename, e.g., `OSPI_[Name]_[Topic]_Response_[Date].md`).
- Convert any `.eml` or raw text to a consistently formatted markdown file containing the full headers and body text.
