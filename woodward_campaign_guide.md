# WoodWard Campaign Guide: The VS Code Hand-Off

**Date**: Feb 14, 2026
**Role**: Mastermind (Antigravity) -> Task Master (VS Code / User)

## 1. The Strategy: "Divide and Conquer"
I (Antigravity) have designed the architecture and the "Dispatch System."
You (VS Code + Specialized AIs) are now the **Field Commander**. Your job is to execute the specific "Missions" below using your premium AI subscriptions via GitHub Copilot.

### The Tools
*   **VS Code**: Your Command Center. Use it to view files, run Python scripts, and manage the `workspaces/` directory.
*   **The Specialists (Copilot Supported)**:
    *   **GPT-5.3-Codex**: Use for **Legal Analysis** and **Complex Logic**. (Top Tier Reasoning).
    *   **Claude Opus 4.6**: Use for **Narrative/Writing**. (Best-in-class Prose).
    *   **Gemini 3 Pro**: Use for **Deep Research/Context**. (Large Context Window).
    *   **Claude Sonnet 4.5**: Use for **Fast Coding**.

---

## 2. Mission Protocol (How to Run a Dispatch)

**Step 1: Open the Dispatch File**
Navigate to `Projects/WoodWard/workspaces/dispatches/`. You will see subfolders like `TO_LEGAL`, `TO_JOURNALIST`.

**Step 2: Copy & Delegate**
Open a text file (e.g., `01_peer_spending_gap.txt`).
*   **COPY** the entire content.
*   **PASTE** it into the prompt window of the recommended AI (e.g., Copilot Chat -> Select Model).

**Step 3: Ingest the Result**
*   The AI will give you an answer (code, text, or table).
*   **CREATE** a new file in `workspaces/results/` named after the dispatch (e.g., `01_result_peer_data.md`).
*   **PASTE** the AI's answer there.

**Step 4: The Handoff Back**
Once you have collected the results, you summon me (Antigravity) back.
*   "Antigravity, I have the results in `workspaces/results`. Analyze them."

---

## 3. Active Missions (The Queue)

### [MISSION ALPHA] Financial Benchmarking
*   **Agent**: Forensic Accountant
*   **Dispatch File**: `workspaces/dispatches/TO_ACCOUNTANT/01_peer_spending_gap.txt`
*   **Goal**: Find the "Object 7" spending for Evergreen and Tacoma.
*   **Model**: **Claude Sonnet 4.5** or **GPT-5.2**.

### [MISSION BRAVO] Contract Risk Assessment
*   **Agent**: General Counsel (Cicero Clone)
*   **Dispatch File**: `workspaces/dispatches/TO_LEGAL/02_contract_risk_template.txt`
*   **Goal**: Analyze a specific PDF contract for "Indemnification" and "Termination" risks.
*   **Action**: You must **open a PDF contract**, copy its text, and paste it into the "INSERT CONTRACT TEXT HERE" section of the dispatch file *before* sending it to the AI.
*   **Model**: **GPT-5.3-Codex** (Critical for logic).

### [MISSION CHARLIE] Narrative Synthesis
*   **Agent**: Woodward (Journalist)
*   **Dispatch File**: `workspaces/dispatches/TO_JOURNALIST/03_narrative_brief.txt`
*   **Goal**: Turn the dry financial facts into a compelling story lede.
*   **Model**: **Claude Opus 4.6** (Best narrative style) or **Gemini 3 Pro**.

---

## 4. Maintenance Commands (VS Code Terminal)
If you need to check the status of the investigation system itself, run these in your VS Code terminal:

*   **Check Database Health**: `ls -lh data/woodward.db`
*   **Verify Python Env**: `source .venv/bin/activate && python --version`

## 5. Final Word
You are the Task Master. The AIs are your staff. I am your Strategist.
Good luck, Commander.
