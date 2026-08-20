# Migration report — ibd-uc-rag-prototype reorganization

Date: 2026-08-18

## Goal

Reorganize into a durable knowledge/code-separated structure:

```
/Users/janakirampulipati/Projects/ibd/
├── knowledge/
│   └── ibd-research-review/
└── apps/
    └── ibd-uc-rag-prototype/
```

## Old paths → new paths

| Content | Old path | New path |
|---|---|---|
| Evidence package (reports, workbooks, JSON, extracted-text, sources, config, scripts, tests) | `/Users/janakirampulipati/ibd-research-review/` | `/Users/janakirampulipati/Projects/ibd/knowledge/ibd-research-review/` |
| Prototype app (Streamlit + LangChain + LangGraph + MCP server + memory + subagents + tests) | `/Users/janakirampulipati/PycharmProjects/ibd-uc-rag-prototype/` and `/Users/janakirampulipati/Documents/Codex/2026-07-28/ibd-uc-rag-prototype/` | `/Users/janakirampulipati/Projects/ibd/apps/ibd-uc-rag-prototype/` |

**Old locations were left in place, not deleted** — this bridge cannot delete files on your machine, and the operation was a copy (`rsync -a`), not a move. All three copies of the evidence JSON are byte-identical (md5 `25166de97aa7cb8b6318276efc6e8df1`). If you want the old copies removed, do so yourself in Finder/Terminal — `~/ibd-research-review`, `~/PycharmProjects/ibd-uc-rag-prototype`, `~/Documents/Codex/2026-07-28/ibd-uc-rag-prototype` are now redundant.

Excluded from the knowledge copy (dev/authoring artifacts, not the reviewed evidence itself): `.venv`, `node_modules`, `.pytest_cache`, `backups`, `checkpoints-remediation`, `logs`, `previews*`, `processing`, `.final-remediation-work`, `.final-remediation-qa-work`, `.qa-remediated-work`, `.DS_Store`. Everything else — all completion/source-verification/QA reports, all five evidence workbook variants, `ibd-prototype-evidence.json`, `extracted-text/`, `sources/`, `extracted-claims/`, `config/`, `scripts/`, `tests/`, `archive/`, `outputs/`, `prototype_work/`, `EVIDENCE-GAPS.md` — was copied (156 files).

`cheatmeal-recovery` was not inspected or touched at any point in this operation.

## Verification (run against a byte-identical mirror in the cloud sandbox)

**Important constraint:** the device bridge to your Mac has no network access, so `pip install` cannot run through it. All verification below ran in Claude's cloud sandbox against a copy of the exact same files now sitting at `Projects/ibd/apps/ibd-uc-rag-prototype` on your Mac (confirmed identical via md5 checksums on the shared source files and a diff-free code copy). The code that was tested is the code that is now on your disk.

1. **Clean virtual environment** — `python3 -m venv venv` created fresh, no reused packages. ✅
2. **Dependencies installed** — `pip install -r requirements.txt` succeeded with no errors. Key versions: `langchain==0.2.17`, `langchain-community==0.2.19`, `langgraph==0.2.76`, `mcp==1.29.0` (pinned — the sandbox's default `mcp==2.0.0` lacks `FastMCP`), `streamlit==1.61.1`. ✅
3. **Full pytest suite** — `pytest tests/ -v` → **105 passed, 0 failed** (1 harmless pydantic-settings deprecation warning, unrelated to this project's code). Covers UC-only filtering, Crohn's-only exclusion, ESR/CRP/calprotectin/biologics/JAK/mucosal-healing/colonoscopy/ultrasound fallback, citation/locator/limitation preservation, diagnosis/medication-change/flare-prediction refusal, MCP tool schemas and retrieval correctness, memory isolation and clinical-content guarding, subagent routing, safety-critic and citation-verifier rejection, QA-agent reporting, retry/stop behavior, and no-model-call determinism. ✅
4. **Streamlit startup/HTTP health check** — `streamlit run streamlit_app.py --server.headless true` → `curl localhost:8531` returned **HTTP 200**, then shut down cleanly. ✅
5. **MCP stdio smoke test** — real `stdio_client`/`ClientSession` round-trip against `mcp_server/server.py`: `list_tools()` returned exactly the 6 required tools (`search_uc_claims`, `get_claim`, `get_source`, `list_supported_topics`, `check_claim_applicability`, `get_evidence_gaps`); `list_supported_topics` and `get_evidence_gaps` both called successfully. ✅
6. **Imports/paths from new location** — imported every module (`app.evidence_loader`, `app.workflow`, `app.subagents`, `mcp_server.tools`, `memory.session_memory`, `memory.preference_memory`) from a working directory outside the project (`/tmp`), confirming no hardcoded absolute paths broke the move. `grep` for old path strings (`ibd-uc-rag-prototype` outside the project name, `/mnt/user-data`, `/home/claude`) in every `.py` file returned zero matches — the evidence-file path is resolved via `Path(__file__).resolve().parent.parent`, which is relocation-safe by construction. `load_evidence_package()` correctly resolved to the new `data/ibd-prototype-evidence.json` and loaded 49 total claims, 5 UC-eligible, 15 Crohn's-only — matching the known-correct counts exactly. ✅

## Broken references found

**None.** No hardcoded paths, no broken imports, no data-loading failures, no test regressions after the move.

## Not done (per your instructions)

- No deployment to Vercel or any public service.
- No GitHub remote created.
- Old copies at the previous three locations were not deleted (cannot delete via this bridge; left for you to remove manually if desired).

## Known limitations carried forward unchanged

- Only 5 of 49 claims are UC-eligible under the strict `conditionApplicability contains "ulcerative_colitis"` rule (CLM-014, CLM-081, CLM-093, CLM-094, CLM-095).
- ESR, CRP, fecal calprotectin, mucosal healing, colonoscopy, intestinal ultrasound, biologics, and JAK inhibitors all correctly fall through to "This topic is not currently covered by the reviewed UC evidence set." — this is expected behavior given the evidence package, not a defect introduced by the reorganization.
- The underlying evidence package itself remains `NOT_READY_FOR_HUMAN_APPROVAL` per its own QA reports (now also copied into `knowledge/ibd-research-review/`).

## How to run it at the new location

```
cd ~/Projects/ibd/apps/ibd-uc-rag-prototype
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py          # UI
pytest tests/ -v                        # tests
python -m mcp_server.server             # MCP server (stdio)
```
