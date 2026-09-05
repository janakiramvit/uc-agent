# UC Evidence-Discovery — QA Report

**Run ID:** `uc-exp-aba49128a130` · **Generated:** 2026-09-05T16:37:29Z

> Automated QA only. Automated QA does NOT constitute clinical approval.

**Result: 13 / 15 PASS**

| # | Check | Result | Detail |
|---|---|---|---|
| QA-01 | Every candidate claim references a known source | **PASS** | 13 claims / 3 sources |
| QA-02 | Every claim has a non-empty exact excerpt and locator | **PASS** | checked |
| QA-03 | Every claim is marked mechanically extracted / abstract_only | **FAIL** | checked |
| QA-04 | DOI (when present) is well-formed; every source has an identifier | **PASS** | checked |
| QA-05 | No Crohn's-only record was labelled ulcerative_colitis | **PASS** | checked |
| QA-06 | Applicability labels are constrained to the allowed set (no ad-hoc upgrade) | **FAIL** | checked |
| QA-07 | No full-text file archived without an established licence | **PASS** | 0 archived |
| QA-08 | All human/clinical review fields blank; nothing approved | **PASS** | checked |
| QA-09 | No duplicate source or claim ids | **PASS** | checked |
| QA-10 | Counters agree with package contents | **PASS** | checked |
| QA-11 | Checkpoint validates against checkpoint.schema-v1.1.0.json | **PASS** | valid |
| QA-12 | Checkpoint records an exact next operation | **PASS** | present |
| QA-13 | No secret / token / connection-string pattern in outputs | **PASS** | regex scan |
| QA-14 | targetIndex is NONE (no promotion) | **PASS** | checked |
| QA-15 | No Reddit URL / handle in any output | **PASS** | regex scan |
