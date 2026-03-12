import { useState } from "react";

const COLORS = {
  user: "#3B82F6",
  execution: "#8B5CF6",
  pipeline: "#10B981",
  council: "#F59E0B",
  database: "#EF4444",
  shared: "#6366F1",
  sentinel: "#EC4899",
  bg: "#0F172A",
  card: "#1E293B",
  cardHover: "#334155",
  text: "#F8FAFC",
  textMuted: "#94A3B8",
  border: "#475569",
  success: "#22C55E",
};

const Section = ({ title, color, children, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ marginBottom: 16, border: `1px solid ${color}33`, borderRadius: 8, overflow: "hidden" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", padding: "12px 16px", background: `${color}15`,
          border: "none", cursor: "pointer", display: "flex", justifyContent: "space-between",
          alignItems: "center", color: COLORS.text, fontSize: 15, fontWeight: 600,
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 12, height: 12, borderRadius: "50%", background: color, display: "inline-block" }} />
          {title}
        </span>
        <span style={{ fontSize: 18, transform: open ? "rotate(180deg)" : "none", transition: "0.2s" }}>▼</span>
      </button>
      {open && <div style={{ padding: 16, background: COLORS.card }}>{children}</div>}
    </div>
  );
};

const Node = ({ label, sublabel, color, small }) => (
  <div style={{
    padding: small ? "6px 10px" : "10px 14px", background: `${color}20`, border: `1px solid ${color}50`,
    borderRadius: 6, display: "inline-block", margin: 4, fontSize: small ? 11 : 13,
    color: COLORS.text, lineHeight: 1.4, textAlign: "center",
  }}>
    <div style={{ fontWeight: 600 }}>{label}</div>
    {sublabel && <div style={{ fontSize: small ? 10 : 11, color: COLORS.textMuted, marginTop: 2 }}>{sublabel}</div>}
  </div>
);

const Arrow = ({ label }) => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "4px 0", color: COLORS.textMuted }}>
    <span style={{ fontSize: 18 }}>↓</span>
    {label && <span style={{ fontSize: 10, marginLeft: 6 }}>{label}</span>}
  </div>
);

const Stat = ({ label, value, color }) => (
  <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${COLORS.border}33` }}>
    <span style={{ color: COLORS.textMuted, fontSize: 12 }}>{label}</span>
    <span style={{ color: color || COLORS.success, fontSize: 12, fontWeight: 600 }}>{value}</span>
  </div>
);

export default function CiceroArchitecture() {
  const [activeTab, setActiveTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "System Overview" },
    { id: "pipeline", label: "Pipeline Flow" },
    { id: "databases", label: "Database Layer" },
    { id: "files", label: "File Structure" },
    { id: "scores", label: "Score History" },
  ];

  return (
    <div style={{ background: COLORS.bg, color: COLORS.text, minHeight: "100vh", fontFamily: "system-ui, -apple-system, sans-serif", padding: 20 }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Cicero Platform Architecture</h1>
        <p style={{ color: COLORS.textMuted, fontSize: 13, marginBottom: 20 }}>
          Knight Legal Operations Platform — Cicero + Sentinel
        </p>

        <div style={{ display: "flex", gap: 4, marginBottom: 20, flexWrap: "wrap" }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 500,
              background: activeTab === t.id ? COLORS.user : COLORS.card,
              color: activeTab === t.id ? "#fff" : COLORS.textMuted,
            }}>{t.label}</button>
          ))}
        </div>

        {activeTab === "overview" && (
          <div>
            <Section title="Human Layer" color={COLORS.user} defaultOpen={true}>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Node label="Chris" sublabel="Human relay between all agents" color={COLORS.user} />
                <Node label="Bishop Prime" sublabel="Claude Chat — Architecture + Strategy" color={COLORS.user} />
              </div>
            </Section>

            <Section title="Execution Layer" color={COLORS.execution} defaultOpen={true}>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Node label="Claude Code" sublabel="Opus/Sonnet — Task execution" color={COLORS.execution} />
                <Node label="Antigravity" sublabel="Gemini/VS Code — Implementation" color={COLORS.execution} />
                <Node label="ChatGPT" sublabel="Style + proofreading" color={COLORS.execution} />
                <Node label="Perplexity" sublabel="Authority verification backup" color={COLORS.execution} />
              </div>
            </Section>

            <Section title="Cicero — Legal Drafting Pipeline" color={COLORS.pipeline} defaultOpen={true}>
              <p style={{ fontSize: 12, color: COLORS.textMuted, marginBottom: 12 }}>
                Multi-agent RAG system. Query → Retrieval → Parallel Drafting → Verification → Synthesis.
              </p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Node label="Router" sublabel="Gemini 3.1 Pro" color={COLORS.pipeline} small />
                <Node label="Coordinator" sublabel="Parallel retrieval + RRF" color={COLORS.pipeline} small />
                <Node label="Context Budget" sublabel="60% legal / 20% case / 20% strategy" color={COLORS.pipeline} small />
                <Node label="Verifier" sublabel="Pin cites / Id. / RCW / Rules" color={COLORS.pipeline} small />
                <Node label="Assembly" sublabel="Markdown → docx" color={COLORS.pipeline} small />
              </div>
            </Section>

            <Section title="Council of Models" color={COLORS.council} defaultOpen={true}>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Node label="Logician" sublabel="o3 — CREAC + Stasis Theory" color={COLORS.council} />
                <Node label="Historian" sublabel="Gemini 3.1 Pro — Record-grounded" color={COLORS.council} />
                <Node label="Orator" sublabel="GPT-5.4 — Persuasive prose" color={COLORS.council} />
                <Node label="Fact Checker" sublabel="GPT-4.1 — Record validation" color={COLORS.council} />
                <Node label="Judge" sublabel="GPT-5.4 — Final synthesis" color={COLORS.council} />
              </div>
            </Section>

            <Section title="Database Layer — Neo4j Desktop (bolt://127.0.0.1:7687)" color={COLORS.database} defaultOpen={true}>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Node label="legaldb" sublabel="THE LAW — 62 Opinions, 122 Holdings, 21K chunks" color={COLORS.database} />
                <Node label="casedb" sublabel="THE RECORD — Case 61813-3-II, filings, exhibits" color={COLORS.database} />
                <Node label="strategydb" sublabel="THE MIND — 235 Skills, reasoning frameworks" color={COLORS.database} />
                <Node label="sentineldb" sublabel="THE WATCH — Comms, filings, deadlines" color={COLORS.sentinel} />
                <Node label="CramLaw" sublabel="Separate project — UNTOUCHED" color={COLORS.border} />
              </div>
            </Section>

            <Section title="Shared Infrastructure" color={COLORS.shared} defaultOpen={true}>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Node label="knight-lib" sublabel="Neo4j adapter + kanon-2 embeddings + base config" color={COLORS.shared} />
                <Node label="LegalDocumentProcessor" sublabel="semchunk + eyecite + section classification" color={COLORS.shared} />
                <Node label="768d kanon-2" sublabel="Platform-wide embedding standard (NO EXCEPTIONS)" color={COLORS.shared} />
              </div>
            </Section>
          </div>
        )}

        {activeTab === "pipeline" && (
          <div>
            <h3 style={{ fontSize: 16, marginBottom: 12 }}>Pipeline Flow: OPENING_BRIEF Mode</h3>
            <div style={{ background: COLORS.card, borderRadius: 8, padding: 20, textAlign: "center" }}>
              <Node label="Production Query" sublabel="Assignment + record facts + authorities" color={COLORS.user} />
              <Arrow label="Query classification" />
              <Node label="Router (Gemini 3.1 Pro)" sublabel="Classify query type" color={COLORS.pipeline} />
              <Arrow label="Parallel retrieval from 3 databases" />
              <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
                <Node label="legaldb" sublabel="Holdings + Chunks" color={COLORS.database} small />
                <Node label="casedb" sublabel="Record + Exhibits" color={COLORS.database} small />
                <Node label="strategydb" sublabel="Skills + Frameworks" color={COLORS.database} small />
              </div>
              <Arrow label="RRF fusion + provenance weighting (1.3x/1.1x/0.7x)" />
              <Node label="Context Budget" sublabel="60% legal / 20% case / 20% strategy" color={COLORS.pipeline} />
              <Arrow label="Parallel drafting" />
              <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
                <Node label="Logician (o3)" sublabel="CREAC structure" color={COLORS.council} small />
                <Node label="Historian (Gemini)" sublabel="Record facts" color={COLORS.council} small />
                <Node label="Orator (GPT-5.4)" sublabel="Prose polish" color={COLORS.council} small />
              </div>
              <Arrow label="Adversarial critique" />
              <Node label="Citation Verifier" sublabel="Pin cites + Id. + RCW + Court rules" color={COLORS.pipeline} />
              <Arrow label="" />
              <Node label="Fact Checker (GPT-4.1)" sublabel="Record validation" color={COLORS.council} />
              <Arrow label="Refinement if needed" />
              <Node label="Judge (GPT-5.4)" sublabel="Final synthesis" color={COLORS.council} />
              <Arrow label="" />
              <Node label="Verified Brief Section" sublabel="Filing-quality output" color={COLORS.success} />
            </div>

            <div style={{ marginTop: 20 }}>
              <h3 style={{ fontSize: 16, marginBottom: 12 }}>Future Modes</h3>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 200, padding: 12, background: COLORS.card, borderRadius: 8, border: `1px solid ${COLORS.border}33` }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>REPLY_BRIEF (45 days)</div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>
                    Ingest opposing brief → Authority Audit → Rebuttal Logician → Historian → Orator → Judge
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 200, padding: 12, background: COLORS.card, borderRadius: 8, border: `1px solid ${COLORS.border}33` }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>MOTION (6 months)</div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>
                    Motion + Declaration + Proposed Order — trial court writing style
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 200, padding: 12, background: COLORS.card, borderRadius: 8, border: `1px solid ${COLORS.border}33` }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>RESEARCH</div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>
                    Authority search → Research memo (no CREAC, citation-verified)
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "databases" && (
          <div>
            {[
              { name: "legaldb", subtitle: "THE LAW", color: COLORS.database, stats: [
                ["Opinions", "~62"], ["Holdings", "~122"], ["Chunks (legacy)", "~20,800"],
                ["Chunks (reingested)", "168"], ["Chunks (curated)", "~343"],
                ["Authority nodes", "~807"], ["ForeignCaseFacts", "~209"],
                ["[:CITES_OPINION]", "87"], ["[:NEXT] chains", "~19,700"],
                ["Vector indexes", "3 (holding, chunk, casefact)"], ["Embedding dim", "768d kanon-2"],
              ]},
              { name: "casedb", subtitle: "THE RECORD", color: COLORS.database, stats: [
                ["Case: 61813-3-II", "Active (appeal)"], ["Parties", "2 (Chris, Dahlyla)"],
                ["Filing references", "Per original MyCaseDB"], ["Embedding dim", "768d kanon-2"],
              ]},
              { name: "strategydb", subtitle: "THE MIND", color: COLORS.execution, stats: [
                ["Skill nodes", "235"], ["Entity nodes", "365"], ["Document nodes", "129"],
                ["Party nodes", "52"], ["Modules", "5"], ["Context cap", "20%"],
                ["Embedding dim", "768d kanon-2"],
              ]},
              { name: "sentineldb", subtitle: "THE WATCH", color: COLORS.sentinel, stats: [
                ["Person nodes", "4 (Chris, Dahlyla, Sheldrick, Cornell)"],
                ["Filing nodes", "5 (key filings)"], ["Deadline nodes", "1 (brief filing)"],
                ["Constraints", "6"], ["Vector index", "message_embedding (768d)"],
                ["Status", "Foundation only — full skills post-filing"],
              ]},
            ].map(db => (
              <Section key={db.name} title={`${db.name} — ${db.subtitle}`} color={db.color} defaultOpen={db.name === "legaldb"}>
                {db.stats.map(([label, value], i) => (
                  <Stat key={i} label={label} value={value} />
                ))}
              </Section>
            ))}
          </div>
        )}

        {activeTab === "files" && (
          <div style={{ background: COLORS.card, borderRadius: 8, padding: 16, fontSize: 12, fontFamily: "monospace", lineHeight: 1.8, whiteSpace: "pre", overflowX: "auto" }}>
{`/Volumes/WD_BLACK/Desk2/Projects/
├── neo4j-data/                    # Shared Neo4j data (all 5 DBs)
├── knight-lib/                    # Shared Python package
│   └── knight_lib/
│       ├── adapters/neo4j.py      # Unified adapter
│       ├── embeddings/client.py   # 768d kanon-2
│       └── config/base.py
│
├── Cicero/                        # Legal drafting system
│   ├── .env                       # Local Neo4j + API keys
│   ├── cases/
│   │   └── 61813-3-II/
│   │       ├── case_config.json
│   │       └── briefs/
│   │           ├── opening/
│   │           │   └── review_package/
│   │           │       └── OPENING_BRIEF_FINAL.docx
│   │           └── reply/         # Future
│   ├── src/
│   │   ├── main.py                # RAGSystem entry
│   │   ├── agents/
│   │   │   ├── council.py         # 6 agents + modes
│   │   │   ├── citation_verifier.py
│   │   │   └── base.py
│   │   ├── orchestration/
│   │   │   ├── router.py
│   │   │   ├── coordinator.py
│   │   │   └── context.py
│   │   ├── ingest/
│   │   │   ├── legal_document_processor.py
│   │   │   └── ingest_cli.py
│   │   └── assembly/engine.py
│   ├── scripts/
│   │   ├── audit/                 # Integrity toolkit
│   │   ├── merits_draft_test.py
│   │   ├── e2e_acceptance_test.py
│   │   ├── production_run_cjc.py
│   │   └── recursive_audit.py     # System audit
│   └── docs/
│       ├── schema/                # 4 JSON schema docs
│       ├── architecture/          # Flowcharts
│       └── hardening/             # Master plans + reports
│
└── Sentinel/                      # Case management (foundation)
    ├── .env
    └── src/skills/                # Stubs for BIFF, tracker`}
          </div>
        )}

        {activeTab === "scores" && (
          <div>
            <h3 style={{ fontSize: 16, marginBottom: 12 }}>Pipeline Score Progression</h3>
            <div style={{ background: COLORS.card, borderRadius: 8, padding: 16, overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                    {["Version", "Phase", "Score", "Fabricated", "Key Change"].map(h => (
                      <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: COLORS.textMuted, fontWeight: 500 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["v1", "Baseline", "0/32", "Unknown", "BrainBase flooding context"],
                    ["v2", "Context budget", "10/18", "2", "60/20/20 filter + verifier rebuild"],
                    ["v3", "Phase 9", "10/18", "2", "Pin cites (matched via fallback)"],
                    ["v4", "Phase 10 Bridge", "13/14", "0", "Pin cite fix + Kovacs/Littlefield + constraints"],
                    ["v5", "Post-migration", "15/16", "0", "Local Neo4j (lower latency)"],
                    ["v6", "Schema enrichment", "14/18", "0", "More authorities cited (denominator up)"],
                    ["v7", "Post-reingestion", "10/10", "0", "Focused retrieval from better chunks"],
                    ["CJC v1", "Production", "17/17", "0", "First real production run"],
                    ["CJC v2", "Post-tuning", "14/14", "0", "With tuning improvements"],
                    ["Brief", "Assembly", "16/16", "0", "Final brief verification"],
                  ].map(([ver, phase, score, fab, change], i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}33` }}>
                      <td style={{ padding: "8px 12px", fontWeight: 600, color: COLORS.user }}>{ver}</td>
                      <td style={{ padding: "8px 12px", color: COLORS.textMuted }}>{phase}</td>
                      <td style={{ padding: "8px 12px", color: COLORS.success, fontWeight: 600 }}>{score}</td>
                      <td style={{ padding: "8px 12px", color: fab === "0" ? COLORS.success : COLORS.database }}>{fab}</td>
                      <td style={{ padding: "8px 12px", color: COLORS.textMuted, fontSize: 11 }}>{change}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: 20 }}>
              <h3 style={{ fontSize: 16, marginBottom: 12 }}>Key Milestones</h3>
              {[
                ["Phase 9", "Verifier rebuilt from scratch. BrainBase confirmed 768d. OPCrawler quarantined."],
                ["Phase 10", "Neo4j migrated to local WD_BLACK. CramLaw preserved. 4 databases created."],
                ["Phase 10 Bridge", "Citation fabrication eliminated. 13/14 verified."],
                ["Phase 11+12", "19,682 [:NEXT] chains. 87 citation graph links. Schema documented."],
                ["Phase 13", "LegalDocumentProcessor built. 168 chunks reingested. Gronquist + John added."],
                ["Phase 14", "Source diversity weighting. Id. handler. Statute verification. E2E test passing."],
                ["Phase 15", "Brief assembled. 16/16 verification. 7,281 words. Ready for filing."],
              ].map(([phase, desc], i) => (
                <div key={i} style={{ display: "flex", gap: 12, marginBottom: 8, alignItems: "flex-start" }}>
                  <span style={{ background: COLORS.success, color: "#000", padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600, whiteSpace: "nowrap" }}>{phase}</span>
                  <span style={{ fontSize: 12, color: COLORS.textMuted }}>{desc}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
