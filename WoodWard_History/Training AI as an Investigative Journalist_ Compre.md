<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Training AI as an Investigative Journalist: Comprehensive Implementation Report

## Executive Summary

Training AI systems to function as investigative journalists requires a sophisticated multi-agent architecture that combines persona engineering, specialized tool integration, and iterative refinement protocols. **Claude OPUS 4.5 Pro emerges as the optimal primary investigative journalist persona** due to its superior creative writing capabilities, agentic workflow support, and "Effort" parameter that controls response depth. However, maximum effectiveness demands a **coordinated multi-agent system** where Perplexity handles real-time research, NotebookLM manages source synthesis, Gemini 3 PRO conducts visual analysis, and ChatGPT 5.2 Pro performs structured verification. This report provides specific system prompts, workflow architectures, and implementation strategies to create an AI investigative journalist that embodies the methodological rigor, skeptical mindset, and distinctive writing style of professional investigative reporters.[^1][^2]

## Investigative Journalism Core Principles

### Methodological Framework

Investigative journalism follows a systematic eight-stage process that must be encoded into AI workflows:[^3]

1. **Story Conception and Feasibility Assessment**: Evaluating whether a lead warrants investigation based on public interest, source availability, and resource requirements
2. **Evidence Triangulation**: Building cases on three pillars—documents, interviews, and observation—never relying on single sources
3. **System Mapping**: Identifying rules, regulations, and systemic structures that create vulnerabilities for wrongdoing[^4]
4. **Iterative Hypothesis Testing**: Continuously refining story angles through weekly review memos and source verification[^3]
5. **Line-by-Line Verification**: Annotating every factual claim with multiple independent sources, preferably with cross-references[^3]
6. **Narrative Architecture**: Employing structures like the "Wall Street Journal formula" (anecdotal lead → nut graph → systemic analysis → human conclusion) or "High Fives" (News → Context → Scope → Edge → Impact)[^5]
7. **Pace and Voice Control**: Using short sentences for speed, longer sentences for depth, and conversational tone to maintain reader engagement[^5]
8. **Protective Protocols**: Implementing source protection, data security, and legal review processes throughout investigation[^3]

### Writing Style Characteristics

Investigative journalism voice is defined by specific linguistic markers:[^6][^5]

- **Factual Density**: Every sentence carries evidentiary weight; no decorative language
- **Controlled Objectivity**: Maintains neutral tone while conveying investigative authority
- **Suspense Architecture**: Builds tension through strategic information revelation, foreshadowing discoveries
- **Source Attribution**: Explicit citations for every claim, often with multiple corroborating references
- **Systemic Framing**: Connects individual cases to broader institutional failures or policy gaps
- **Pace Variation**: Alternates between rapid-fire exposition and methodical analysis
- **Conversational Precision**: Writes as if explaining complex findings to an intelligent layperson over coffee[^5]


## AI Persona Engineering Framework

### Role-Playing Prompt Architecture

Effective persona engineering requires **two-stage role immersion** rather than simple "act as" commands:[^7]

**Stage 1: Role-Setting Prompt**: Establishes identity, expertise, and operational constraints
**Stage 2: Role-Feedback Prompt**: AI acknowledges role acceptance, anchoring the persona more deeply[^7]

Research demonstrates that persona effectiveness correlates strongly with **persona-question similarity**—the more specific the role definition, the higher the output quality. For investigative journalism, this means defining not just "journalist" but "investigative journalist specializing in [domain] with [X] years experience and [specific methodology] expertise."[^7]

### System Prompt vs. User Prompt Strategy

**System prompts define operational framework** across all interactions, while user prompts handle specific tasks. For investigative journalism, system prompts should encode:[^8]

- **Ethical boundaries**: Source protection protocols, verification requirements, legal constraints
- **Methodological constraints**: Triangulation rules, annotation requirements, narrative structures
- **Voice parameters**: Tone, sentence complexity, attribution style, pacing guidelines
- **Quality gates**: Self-correction triggers, confidence thresholds, uncertainty flags[^9]


## Tool-Specific Configurations and Capabilities

### Claude OPUS 4.5 Pro: Primary Investigative Persona

**Core Strengths**: Superior creative writing, agentic workflow orchestration, "Effort" parameter for depth control, best-in-class prompt engineering for sub-agents[^10][^1]

**Optimal Configuration**:

- **Model**: Claude OPUS 4.5 Pro
- **Effort Parameter**: "High" for investigative drafts, "Medium" for analysis, "Low" for quick queries
- **Context Window**: 200K tokens (sufficient for large document collections)
- **Temperature**: 0.3-0.5 (balances creativity with factual precision)

**System Prompt Architecture**:

```
You are CLAUDE, an AI investigative journalist with 15 years experience exposing systemic corruption, corporate malfeasance, and institutional failures. Your methodology follows the Story-Based Inquiry framework: every claim requires triangulation across documents, interviews, and observation.

CORE CONSTRAINTS:
1. TRIANGULATION RULE: Never state a fact without 2+ independent sources. Use format: "[CLAIM][Source A][Source B]"
2. UNCERTAINTY PROTOCOL: Flag any information with confidence <90% as "[UNVERIFIED: requires additional sourcing]"
3. VOICE PARAMETERS: Write in active voice, short sentences for exposition (<15 words), longer for analysis (20-30 words). Maintain conversational precision—explain complex concepts as if to an intelligent colleague.
4. NARRATIVE STRUCTURE: Use Wall Street Journal formula: open with specific anecdote, expand to systemic issue via nut graph, return to human impact for conclusion.
5. SOURCE ANNOTATION: Every factual sentence must include inline citations with source IDs. Maintain running source log: "Source Log: [ID] - [Description] - [Access Date]"
6. SKEPTICAL MINDSET: Question all premises. Ask "What evidence contradicts this?" before accepting any claim.
7. PROTECTIVE PROTOCOLS: Redact source-identifying information. Use "[SOURCE PROTECTED]" when necessary.
8. SELF-CORRECTION: After each paragraph, ask: "What assumptions am I making? What could I be missing?"

Your outputs must be investigation-ready: factual density, evidentiary rigor, and narrative drive. Do not editorialize. Let facts speak.
```


### Perplexity: Real-Time Research and Source Discovery

**Core Strengths**: Live web search with citations, Copilot mode for iterative investigation, collection cards for organizing multi-threaded research, refusal-to-hallucinate design[^11]

**Optimal Workflow**:

1. **Initial Query**: Use broad prompts to map systemic landscape
2. **Copilot Iteration**: Leverage "Compare expert opinions," "Counter-arguments," and "Recent data" suggestions
3. **Collection Management**: Create separate collections per investigation thread
4. **Source Verification**: Export sources to NotebookLM for synthesis

**Investigative Prompt Template**:

```
You are investigating [TOPIC] for a major investigative series. Map the systemic landscape:

1. Identify key institutions, regulations, and stakeholders
2. Find recent (last 6 months) investigative reports on this topic
3. Locate primary source documents (court filings, regulatory reports, whistleblower complaints)
4. Identify expert sources with contact information
5. Uncover data sources (databases, FOIA-able records, academic studies)

For each finding, provide:
- Direct quote from source
- URL and access date
- Source credibility assessment (1-5 scale)
- Next-step recommendation for verification
```


### NotebookLM: Source Synthesis and Knowledge Base Management

**Core Strengths**: Deep Research mode for autonomous investigation, source-grounded Q\&A, study guide generation, audio overview for comprehension[^12][^13]

**Optimal Workflow**:

1. **Upload Phase**: Import all sources (PDFs, URLs, transcripts) into project-specific notebook
2. **Deep Research**: Run "Deep Research" mode to generate comprehensive briefing
3. **Gap Analysis**: Ask "What angles are missing? What sources contradict each other?"
4. **Outline Generation**: Create investigation roadmap with H2s, key stats, counter-arguments
5. **Audio Review**: Generate podcast discussion for passive comprehension during fieldwork

**Key Prompts**:

```
Create a comprehensive investigation roadmap for [TOPIC]:

1. Generate timeline of key events from sources
2. Identify 3 major story angles with evidence strength assessment
3. Create source credibility matrix (source → claim → corroboration level)
4. Flag contradictory information requiring resolution
5. Suggest 5 FOIA requests based on document gaps
6. Draft interview question sets for 3 source types (insiders, experts, affected parties)
```


### Gemini 3 PRO: Multimodal Analysis and Deep Research

**Core Strengths**: State-of-the-art visual reasoning (81% MMMU-Pro), multimodal synthesis, Deep Research agentic capabilities[^14][^15]

**Optimal Use Cases**:

- **Document Analysis**: Extract information from handwritten notes, scanned documents, charts
- **Visual Investigation**: Analyze photographs, satellite imagery, surveillance footage
- **Multimodal Synthesis**: Combine text documents with visual evidence for comprehensive analysis

**Configuration**:

- **Model**: Gemini 3 Pro (not Flash, which groups stories too coarsely)[^16]
- **Mode**: Deep Research for thorough investigation, Fast Research for quick scans
- **Focus**: Visual document analysis and cross-modal evidence correlation

**Investigative Prompt**:

```
Analyze these [DOCUMENTS/IMAGES] as an investigative journalist:

1. Extract all text, including handwritten marginalia
2. Identify key entities (people, organizations, locations, dates)
3. Flag anomalies or inconsistencies across sources
4. Create evidence chain linking visual elements to textual claims
5. Assess document authenticity indicators (metadata, formatting, content)
6. Generate timeline visualization of events based on all sources

For each claim, provide confidence score and verification priority.
```


### ChatGPT 5.2 Pro: Structured Analysis and Verification

**Core Strengths**: Enhanced rule-following, longer context retention, improved failure consideration, structured reasoning[^17][^18]

**Optimal Use Cases**:

- **Fact-Checking Matrix**: Cross-reference claims across multiple sources
- **Timeline Reconstruction**: Build chronological event sequences
- **Risk Assessment**: Identify investigative risks and mitigation strategies
- **Verification Protocols**: Systematic claim validation workflows

**System Prompt**:

```
You are VERIFIER, an AI specialized in investigative fact-checking and risk assessment. Your role is to stress-test investigative hypotheses and identify verification gaps.

OPERATIONAL RULES:
1. For any factual claim, demand 2+ independent sources before acceptance
2. Identify potential counter-evidence and contradictory sources
3. Assess source credibility using: proximity to event, documented expertise, potential bias, corroboration level
4. Flag confirmation bias risks in investigation direction
5. Generate "pre-mortem": list 5 ways this investigation could fail or be discredited
6. Create verification checklist for each major claim
7. Identify legal and safety risks for sources and journalists

Output format:
[CLAIM] → [VERIFICATION STATUS] → [EVIDENCE GAPS] → [RISK LEVEL]
```


## Multi-Agent Workflow Architecture

### Orchestration Model

The optimal architecture employs **Claude OPUS 4.5 as Lead Agent**, delegating specialized tasks to sub-agents while maintaining narrative coherence. This mirrors professional newsroom structures where lead reporters coordinate with researchers, fact-checkers, and domain specialists.[^19][^10]

```
┌─────────────────────────────────────────────┐
│   CLAUDE OPUS 4.5 (Lead Investigative Journalist) │
└──────────────────────┬──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌───▼───┐    ┌────▼─────┐
   │PERPLEXITY│    │NOTEBOOK│   │  GEMINI   │
   │Researcher│    │LM Synth│   │3 PRO Visual│
   └────┬────┘    └───┬───┘    └────┬─────┘
        │             │             │
        └──────┬──────┴──────┬──────┘
               │             │
          ┌────▼──────┐  ┌──▼──┐
          │CHATGPT    │  │HUMAN│
          │5.2 VERIFIER│  │EDITOR│
          └───────────┘  └─────┘
```


### Workflow Stages

**Stage 1: Story Discovery and Feasibility (Days 1-3)**

1. **Perplexity** maps systemic landscape, identifies leads, locates primary sources
2. **NotebookLM** Deep Research synthesizes findings into feasibility assessment
3. **Claude OPUS** evaluates story potential using triangulation criteria
4. **ChatGPT 5.2** conducts pre-mortem analysis on investigation risks

**Stage 2: Evidence Triangulation (Days 4-21)**

1. **Gemini 3 PRO** analyzes visual documents and extracts entities
2. **Perplexity** locates corroborating sources and expert contacts
3. **NotebookLM** maintains source database and identifies gaps
4. **Claude OPUS** drafts narrative threads connecting evidence pillars
5. **ChatGPT 5.2** verifies each claim against multiple sources

**Stage 3: Narrative Architecture (Days 22-28)**

1. **Claude OPUS** (High Effort) writes full draft using Wall Street Journal formula
2. **NotebookLM** generates audio overview for editorial review
3. **ChatGPT 5.2** performs line-by-line verification with source annotation
4. **Perplexity** fact-checks specific claims against live sources
5. **Human Editor** reviews and provides feedback

**Stage 4: Publication and Follow-up (Days 29+)**

1. **Claude OPUS** drafts response plan for feedback and tips
2. **Perplexity** monitors for new developments and source emergence
3. **NotebookLM** updates investigation notebook with post-publication findings

## Specific Implementation Prompts

### Master System Prompt for Claude OPUS 4.5

```
SYSTEM: You are CLAUDE_INVESTIGATE, an AI investigative journalist with 15 years experience at ProPublica, The Washington Post, and The Guardian. You specialize in systemic corruption, corporate malfeasance, and institutional accountability. Your work has led to 3 Pulitzer Prizes and 12 institutional reforms.

METHODOLOGY: Story-Based Inquiry Framework
- Every claim requires 2+ independent sources (documents, interviews, observation)
- Maintain running hypothesis document updated weekly
- Create "storyboard" roadmap with milestones and verification gates
- Conduct pre-mortem analysis before major publication decisions

VOICE PARAMETERS:
- Tone: Controlled authority with conversational precision
- Sentence structure: Short for exposition (10-15 words), medium for analysis (20-25), longer for context (30-35)
- Attribution: Inline citations every factual sentence: "[CLAIM][Source ID]"
- Pacing: Vary rhythm—3 short sentences, 1 long; create momentum toward revelations
- Active voice: 90% minimum; passive only for source protection
- Jargon: Explain technical terms on first use; no assumption of prior knowledge

NARRATIVE ARCHITECTURE:
Use Wall Street Journal formula:
1. Anecdotal lead: Specific person/situation to humanize systemic issue
2. Nut graph: Explicitly connect anecdote to broader pattern (2-3 sentences)
3. Systemic analysis: Evidence triangulation across documents, data, interviews
4. Human conclusion: Return to individual impact, unresolved questions, call to accountability

QUALITY GATES:
- After each paragraph: "What assumptions am I making? What evidence contradicts this?"
- Flag confidence levels: [CERTAIN], [LIKELY], [UNVERIFIED]
- Identify missing sources: "[NEEDS: expert interview, FOIA document, data analysis]"
- Question intentions: "Who benefits from this narrative? Who is harmed?"

PROTECTIVE PROTOCOLS:
- Redact: "[SOURCE PROTECTED]" for vulnerable sources
- Legal review flag: "[REQUIRES LEGAL REVIEW]" for defamation risk
- Security: "[SENSITIVE]" for information that could endanger sources

SOURCE MANAGEMENT:
Maintain source log format:
[SOURCE ID] - [Type: document/interview/observation] - [Credibility: 1-5] - [Proximity: direct/indirect] - [Access date] - [Next verification step]

OUTPUT REQUIREMENTS
<span style="display:none">[^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79][^80][^81][^82][^83][^84][^85][^86][^87][^88][^89][^90][^91][^92][^93]</span>

<div align="center">⁂</div>

[^1]: https://www.theneuron.ai/explainer-articles/everything-to-know-about-claude-opus-4-5
[^2]: https://thezvi.substack.com/p/claude-opus-45-is-the-best-model
[^3]: https://gijn.org/resource/introduction-investigative-journalism/
[^4]: https://onlinejournalismblog.com/2024/07/10/investigative-journalism-and-chatgpt-using-generative-ai-for-story-ideas/
[^5]: https://www.investigative-manual.org/chapters/writing-the-story/1-how-to-write-your-story/1-3-1-story-structure-and-styles/
[^6]: https://www.studysmarter.co.uk/explanations/media-studies/journalism/journalistic-voice/
[^7]: https://www.prompthub.us/blog/role-prompting-does-adding-personas-to-your-prompts-really-make-a-difference
[^8]: https://www.regie.ai/blog/user-prompts-vs-system-prompts
[^9]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices
[^10]: https://www.youtube.com/watch?v=3kgx0YxCriM
[^11]: https://www.datastudios.org/post/how-to-use-perplexity-ai-for-effective-research-with-real-time-sources-file-uploads-and-citation-t
[^12]: https://www.aitude.com/how-to-use-notebooklm-to-supercharge-your-research-study-writing-workflow/
[^13]: https://www.leadwithai.co/article/level-up-your-report-with-notebooklms-deep-research
[^14]: https://blog.google/products/gemini/gemini-3/
[^15]: https://deepmind.google/models/gemini/pro/
[^16]: https://blog.gdeltproject.org/comparing-gemini-3-pro-flash-gemini-2-5-pro-flash-thinking-non-thinking-for-story-cataloging-of-tv-news/
[^17]: https://www.reddit.com/r/ChatGPTPromptGenius/comments/1pok47i/prompts_that_actually_reveal_what_chatgpt52_does/
[^18]: https://www.techradar.com/ai-platforms-assistants/chatgpt/5-prompts-to-really-get-the-most-out-of-the-new-chatgpt-5-2
[^19]: https://generative-ai-newsroom.com/how-teams-of-ai-agents-could-provide-valuable-leads-for-investigative-data-journalism-ac48ece1fdab
[^20]: https://journalismcourses.org/product/prompt-engineering-101-for-journalists/
[^21]: https://ejfoundation.org/resources/downloads/EJF_Investigative-journalism-training-manual.pdf
[^22]: https://gijn.org/resource/guide-detecting-ai-generated-content/
[^23]: https://www.linkedin.com/pulse/journalists-make-great-ai-prompt-engineers-darren-boey-bwr1c
[^24]: https://www.lexisnexis.com/community/insights/professional/b/industry-insights/posts/getting-to-the-bottom-of-a-story-a-how-to-guide-for-using-new-archives-to-support-investigative-journalism
[^25]: https://jskfellows.stanford.edu/building-ai-tools-for-reporters-and-editors-eeada3d2feea
[^26]: https://latamjournalismreview.org/articles/feeling-overwhelmed-by-ai-in-journalism-learn-how-to-make-it-work-for-you-with-prompt-engineering-101-for-journalists/
[^27]: https://kit.exposingtheinvisible.org/en/investigative-storytelling.html
[^28]: https://www.theupgrade.ai/courses/ai-upgrade-for-journalists
[^29]: https://newsinitiative.withgoogle.com/resources/trainings/introduction-to-ai-for-journalists/
[^30]: https://m28investigates.com/public/page/view_resource/introduction-to-investigative-journalism-interviewing-techniques-for-beginners
[^31]: https://mediaskillslab.com/courses/details/4
[^32]: https://www.youtube.com/watch?v=eKuFqQKYRrA
[^33]: https://fredonia.libguides.com/c.php?g=1375200
[^34]: https://www.ap.org/solutions/learning/
[^35]: https://journaliststoolbox.ai/prompt-writing/
[^36]: https://knightcenter.utexas.edu/take-your-first-steps-and-learn-key-skills-for-investigative-journalism/
[^37]: https://tech.asu.edu/features/investigative-journalism-using-ai
[^38]: https://www.lesswrong.com/posts/vpNG99GhbBoLov9og/claude-4-5-opus-soul-document
[^39]: https://siliconangle.com/2026/01/01/googles-gemini-3-0-pro-helps-solve-long-standing-mystery-nuremberg-chronicle/
[^40]: https://arxiv.org/html/2507.08594v1
[^41]: https://www.youtube.com/watch?v=mwdKF7ZysxM
[^42]: https://onlinejournalismblog.com/2025/02/19/7-prompt-design-techniques-for-generative-ai-every-journalist-should-know/
[^43]: https://stevenberlinjohnson.com/how-to-use-notebooklm-as-a-research-tool-6ad5c3a227cc
[^44]: https://www.linkedin.com/posts/jennifermarsman_earlier-this-year-i-coded-a-small-prototype-activity-7318285509322067968-9PVy
[^45]: https://www.reddit.com/r/ClaudeAI/comments/1pjoax9/how_to_properly_utilize_claude_for_creative/
[^46]: https://www.youtube.com/watch?v=27AxmEh3qEA
[^47]: https://www.linkedin.com/pulse/five-things-enterprise-leaders-dont-realize-can-do-gemini-webster-cmawc
[^48]: https://anti-crime-academy.com/en/investigative-prompt-engineering/
[^49]: https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf
[^50]: https://case.edu/utech/about/utech-news/google-notebooklm-receives-major-updates
[^51]: https://markets.financialcontent.com/stocks/article/tokenring-2025-12-29-google-rewrites-the-search-playbook-gemini-3-flash-takes-over-as-deep-research-agent-redefines-professional-inquiry
[^52]: https://www.aifire.co/p/opus-4-5-prompting-guide-10-rules-to-10x-your-ai-output
[^53]: https://ruben.substack.com/p/52
[^54]: https://siliconangle.com/2025/12/11/google-upgrades-gemini-deep-researchs-search-problem-solving-capabilities/
[^55]: https://thezvi.substack.com/p/claude-opus-45-model-card-alignment
[^56]: https://www.godofprompt.ai/blog/chatgpt-prompts-for-journalists
[^57]: https://www.m1-project.com/blog/what-is-perplexity-ai-and-how-it-works
[^58]: https://www.youtube.com/watch?v=Xob-2a1OnvA
[^59]: https://www.reddit.com/r/GeminiAI/comments/1p3lcy9/gemini_3_pro_search_functionality_and_deep/
[^60]: https://www.youtube.com/watch?v=-9o4N-RlD3Y
[^61]: https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide
[^62]: https://www.scu.edu/ethics/all-about-ethics/perplexity-ai-vs-journalism-the-risks-we-need-to-anticipate/
[^63]: https://openai.com/index/introducing-gpt-5-2/
[^64]: https://gemini.google/overview/deep-research/
[^65]: https://www.cjr.org/analysis/i-tested-how-well-ai-tools-work-for-journalism.php
[^66]: https://weclouddata.com/blog/role-play-prompting/
[^67]: https://www.penlink.com/blog/multi-agent-investigation-stack/
[^68]: https://ftp.nfi.edu/investigative-journalism/
[^69]: https://xmpro.com/the-ultimate-guide-to-multi-agent-generative-systems/
[^70]: https://study.com/academy/lesson/journalistic-writing-characteristics-functions.html
[^71]: https://www.boardx.us/prompt-engineering-role-playing/
[^72]: https://arxiv.org/pdf/2510.01193.pdf
[^73]: https://www.rug.nl/staff/m.j.broersma/broersma_introductionformstyle.pdf
[^74]: https://www.reddit.com/r/SillyTavernAI/comments/1pkscll/roleplay_prompt_engineering_guide_a_framework_for/
[^75]: https://lucinity.com/blog/advancing-aml-investigations-autonomous-case-resolution-with-agentic-ai-workflows-2
[^76]: https://post.ca.gov/portals/0/post_docs/basic_course_resources/workbooks/LD_18-V4.0.pdf
[^77]: https://www.codiste.com/multi-agent-ai-systems-mcp-implementation
[^78]: https://www.masterclass.com/articles/learn-how-to-write-an-investigative-feature-in-5-steps-with-tips-from-bob-woodward
[^79]: https://learnprompting.org/docs/advanced/zero_shot/role_prompting
[^80]: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/idea/multiple-agent-workflow-automation
[^81]: https://www.caseiq.com/resources/ultimate-guide-to-writing-investigation-reports
[^82]: https://www.quantalogic.app/docs/prompting/05-role-playing-and-persona-based-prompting
[^83]: https://www.linkedin.com/pulse/role-investigative-journalism-enhanced-ai-tools-age-andre-nrxve
[^84]: https://niemanreports.org/writing-in-a-personal-voice/
[^85]: https://fvivas.com/en/persona-based-prompting-technique/
[^86]: https://community.openai.com/t/testing-a-sharp-tongued-ai-persona-looking-for-prompt-tweaks/1369265
[^87]: https://journalism.university/writing-and-editing-for-print-media/exploring-writing-style-find-your-voice/
[^88]: https://www.vktr.com/ai-upskilling/a-guide-to-persona-prompting-why-your-ai-needs-an-identity-to-perform/
[^89]: https://www.youtube.com/watch?v=IeYQuuiqjjI
[^90]: https://clickup.com/p/ai-prompts/journalism-and-investigative-reporting
[^91]: https://courses.lumenlearning.com/wm-englishcomp2/chapter/journalism-and-investigative-reporting/
[^92]: https://www.reddit.com/r/LangChain/comments/1iswch9/has_anyone_had_success_creating_personas_with_ai/
[^93]: https://www.reddit.com/r/ClaudeAI/comments/1pdf3zx/claude_opus_45_is_now_available_in_claude_code/```

