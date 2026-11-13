# UC Evidence-Discovery — QA Report

**Run ID:** `uc-exp-bad40544162e` · **Generated:** 2026-11-13T20:48:31Z

> Automated QA only. Automated QA does NOT constitute clinical approval.

**Result: 17 / 19 PASS**

| # | Check | Result | Detail |
|---|---|---|---|
| QA-01 | Every candidate claim references a known source | **PASS** | 41 claims / 45 sources |
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
| QA-16 | No candidate claim is attached to a trial registry source (trials are never treatment-effect claims) | **PASS** | 15 trial source(s) |
| QA-17 | Every source's evidenceType (when present) is one of the four separate evidence types | **PASS** | checked |
| QA-18 | No PDF link or downloaded-file field is stored on any source | **PASS** | checked |
| QA-19 | Every extracted claim is flagged as requiring full-text verification | **PASS** | checked |
