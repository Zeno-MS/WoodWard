# Project WoodWard VS Code Handoff

**Last Updated:** March 1, 2026

## Open Workspaces / Key Files
- `workspaces/FINAL_ARTICLES/` -> Contains the locked `ARTICLE_1` through `ARTICLE_4` markdown files.
- `VPS_Investigation_Evidence_Package.zip` -> The final journalist handoff package.
- `VPS_Investigation_Evidence/` -> The uncompressed directory containing the clean deduplicated CSVs, the EML-to-Markdown right of reply files, and the Neo4j Person Dossiers.
- `/tmp/generate_dossiers.py` & `/tmp/eml_to_markdown.py` -> The Python scripts used to build the handoff package.

## Terminal State & Background Processes
- Docker Desktop is currently running.
- `woodward-neo4j` Docker container is actively running on ports `7474` and `7687`.
- The SQLite database `woodward.db` is locked and located in `data/`.

## Immediate Next Steps for Next Session
1. Unpack `CONTEXT_HANDOFF.md` to review the initialization prompt.
2. The primary objective is to finalize the journalist outreach and deliver the evidence package.
3. Await User command to either begin drafting pitches or pivoting to the Cicero Legal operations.
