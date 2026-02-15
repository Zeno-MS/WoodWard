# WoodWard Multi-Agent Investigation Plan

## 1. The Deployment Protocol: "The Dispatch"
To optimize token usage and leverage specialized AI capabilities, we will use a **"Task Bundle"** system. Rather than keeping all agents in one massive context window, we will generate discrete, self-contained bundles for you to hand off to specific AIs.

### **The Workflow**
1.  **I (The Coordinator)**: Identify a task (e.g., "Analyze Contract X for fraud").
2.  **Dispatch Generation**: I create a text file in `workspaces/dispatches/` containing *only* the relevant context and the specific prompt.
3.  **You (The Editor)**: Copy the content of that dispatch file into the specialized AI's interface (ChatGPT O1, Claude 3.5, Gemini 1.5).
4.  **Result Ingestion**: You paste the AI's output back into a result file, which I then read and integrate.

---

## 2. Specialized Agent Roles (The Roster)

### **Agent A: "Woodward" (The Narrative Architect)**
*   **Specialty**: Creative Writing, Synthesis, Storytelling.
*   **Best Model**: **Claude 4.6 Sonnet** (Anthropic) or **Gemini 3 Pro** (Google).
*   **Why**: Best-in-class for long-form narrative structure and low hallucination rates (crucial for journalism).
*   **Token Strategy**:
    *   **Input**: Receives *summarized* findings, not raw data. (e.g., "Fact: Expenses up $5M", not the CSV of 5,000 txns).
    *   **Output**: Drafts of news articles, blog posts, or timeline narratives.
*   **Context**: `investigative_journalist_briefing.md` + Current Findings Summary.

### **Agent B: "The General Counsel" (Contract Specialist)**
*   **Specialty**: Logic, Risk Analysis, Clause Parsing.
*   **Best Model**: **ChatGPT 5.3 Thinking** (Reasoning Heavy) or **Claude 4.6 Opus**.
*   **Why**: "ChatGPT 5.3 Thinking" excels at complex logical deduction, vital for finding contractual loop-holes and indemnification risks.
*   **Token Strategy**:
    *   **Input**: Receives *only* the specific text of the contract in question. Strict "Need to Know" basis.
    *   **Output**: Legal memos listing "High Risk" clauses (Indemnification, Termination).
    *   **Context**: WA State Procurement Law (Injected System Prompt) + Contract Text.

### **Agent C: "The Forensic Accountant" (Data Cruncher)**
*   **Specialty**: Pattern Recognition, Anomaly Detection, Python Coding.
*   **Best Model**: **Claude 4.6 Sonnet** (Coding) or **ChatGPT 5.2 (Code Interpreter)**.
*   **Why**: These models demonstrate superior Python code generation for data science (Pandas/NumPy) compared to older iterations.
*   **Token Strategy**:
    *   **Input**: Receives CSV headers and sample rows (first 10), never the full dataset unless executing code.
    *   **Output**: Python scripts to find anomalies, or tables of "Red Flag" transactions.
    *   **Context**: Database Schema (`woodward.db`) + Dataset Metadata.

---

## 3. Directory Structure for Delegation
We will organize these handoffs physically on your disk for easy access.

```text
WoodWard/
├── workspaces/
│   ├── dispatches/
│   │   ├── TO_LEGAL/         # Bundles for General Counsel
│   │   ├── TO_JOURNALIST/    # Bundles for Woodward
│   │   └── TO_ACCOUNTANT/    # Bundles for Data Analysis
│   └── results/              # Where you paste their answers
```

## 4. Immediate Execution Plan
1.  **Setup**: Create the `dispatches` directory structure.
2.  **Deployment**: I will generate the first **"Dispatch Bundle"** for the *Forensic Accountant* to analyze the Peer District Spending data gaps.

