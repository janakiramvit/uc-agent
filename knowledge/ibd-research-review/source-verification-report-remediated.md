# IBD evidence source verification report — remediated

Generated: 2026-07-30  
Status: pending second independent QA and human approval  
Approval state: no source or claim is approved

## Scope and controls

This was a bounded evidence-remediation pass performed only in `/Users/janakirampulipati/ibd-research-review`. It did not inspect or modify the excluded application repository and did not implement application architecture, retrieval, embeddings, RAG, APIs, UI, or production infrastructure.

Research used legal public sources only. No paywall was bypassed and no paid model call was made. Public access does not imply permission for downstream republication; licensing remains a separate human review item.

## Source disposition

- Original selected sources: 25
- Active sources after remediation: 25
- Superseded sources retained for audit only: 1
- New replacement source: SRC-026, the 2023 ESPEN guideline update
- Effective abstract-only sources: SRC-002, SRC-013, SRC-015, and SRC-017
- Unresolved legal full-text access issues: 4
- Incorrect full-text mappings rejected and archived: 11

Allowed source-status vocabulary was enforced:

- `verified_full_text`
- `verified_abstract_only`
- `verified_guideline`
- `superseded_replaced`
- `insufficient_access`
- `reject_recommended`

All sources remain `pending_human_review`; user decision and note fields are blank.

## Incorrect mapping corrections

| Source | Incorrect DOI / PMCID | Corrected DOI / PMCID | Outcome |
|---|---|---|---|
| SRC-004 | `10.3390/microorganisms8111638` / `PMC7690730` | `10.1016/j.advnut.2024.100219` / `PMC11063602` | Correct public XML verified |
| SRC-006 | `10.1097/JS9.0000000000003019` / `PMC5250567` | `10.1097/JS9.0000000000003019` / `PMC12626460` | Correct public XML verified |
| SRC-007 | `10.2174/1389450116666150202161500` / `PMC4366573` | `10.1186/s12937-016-0183-8` / `PMC4942986` | Correct public XML verified |
| SRC-008 | `10.1007/s10350-007-9003-8` / `PMC6314770` | `10.3390/nu15173824` / `PMC10489664` | Correct public XML verified |
| SRC-009 | `10.1002/jgh3.12817` / `PMC8719151` | `10.1002/jgh3.12817` / `PMC9667405` | Correct public XML verified |
| SRC-010 | `10.1186/s13643-020-01426-2` / `PMC1513293` | `10.1186/s13643-020-01426-2` / `PMC7395978` | Correct public XML verified |
| SRC-011 | `10.1093/advances/nmaa145` / `PMC3649719` | `10.1093/advances/nmaa145` / `PMC8166559` | Correct public XML verified |
| SRC-013 | `10.1128/microbiolspec.BAD-0010-2016` / `5941818` | `10.1038/s41575-024-00893-5` / blank | Mismatch removed; abstract only |
| SRC-016 | `10.1053/j.gastro.2021.05.047` / `PMC6718954` | `10.1053/j.gastro.2021.05.047` / `PMC8396394` | Correct public XML verified |
| SRC-018 | `10.1097/MPG.0b013e3181c92c53` / `PMC5434712` | `10.1053/j.gastro.2019.03.015` / `PMC6726378` | Correct public XML verified |
| SRC-020 | `10.1080/16546628.2017.1305193` / `PMC5404419` | `10.1136/bmj.n1554` / `PMC8279036` | Correct public XML verified |

For each corrected full-text mapping, the PubMed title, DOI, PMCID, first author, and publication year were compared with the correct PMC JATS record. The erroneous files were moved to `archive/incorrect-source-mappings`; they were not deleted.

## Superseded source remediation

SRC-003, the 2017 ESPEN IBD nutrition guideline, is classified `superseded_replaced`. It is mapped to:

- New source ID: SRC-026
- Title: *ESPEN guideline on Clinical Nutrition in inflammatory bowel disease*
- PMID: `36739756`
- DOI: `10.1016/j.clnu.2022.12.004`
- Publication: *Clinical Nutrition* 42 (2023), 352–379
- Official public PDF: `https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf`

Old-claim disposition:

- CLM-009: removed
- CLM-010: replaced by CLM-096
- CLM-011: replaced by CLM-097
- CLM-012: removed

The old record and its disposition are preserved in `archive/superseded-sources/SRC-003.json`.

## Claim reconciliation

The 95 original claims reconcile exactly and mutually exclusively:

| Category | Count |
|---|---:|
| Retained unchanged | 2 |
| Retained revised | 53 |
| Removed | 37 |
| Replaced by new | 2 |
| Still needs evidence | 1 |
| **Total** | **95** |

The active Claims sheet contains 58 rows: 55 retained claims ready for human review, one claim still needing evidence, and two new replacement claims. Removed and replaced original claims are absent from the active sheet and preserved in the audit archive.

Every active claim has a supporting excerpt and an exact locator using one of the required locator forms: abstract sentence, PDF journal page plus recommendation/section, or official webpage heading plus paragraph/bullet.

## Bounded evidence-gap decisions

| Gap | Status | Required answer limit |
|---|---|---|
| Post-surgical context | `partially_resolved_with_answer_limit` | Clinician/surgical-team management only; no individualized regimen |
| Stricture or obstruction risk | `partially_resolved_with_answer_limit` | Flag risk and defer texture/enteral decisions to the IBD team |
| Biomarkers | `unresolved_feature_must_be_excluded` | Exclude claims that a diet will improve CRP, calprotectin, or other biomarkers |
| Adverse effects | `partially_resolved_with_answer_limit` | Safety warning about restrictive diets; no quantified adverse-event claim |
| Alcohol | `partially_resolved_with_answer_limit` | State uncertainty only; do not recommend alcohol |
| Physical activity | `resolved_for_mvp` | General, appropriately bounded activity encouragement only |

Search limits were enforced in separate logs:

- More-evidence claims: maximum 2 searches per claim
- MVP gaps: maximum 3 searches, 4 candidates, and 2 selected sources per gap

## Canada/US applicability

Each source was assigned a regional assessment:

- Direct US sources were identified as such.
- UK, European, and international guidance was marked portable only with qualification.
- Canada/US differences in healthcare pathways, dietitian access, formula and food availability, cultural fit, terminology, fibre/alcohol guidance, and local clinical practice were retained as limitations.
- High-risk contexts—perioperative care, obstruction/stricture, malnutrition, and restrictive diets—remain clinician-led.

## Access, licensing, evidence, and reliability limitations

- Four sources remain abstract-only after all legal public-access checks.
- SRC-013 became abstract-only after its mismatched full text was rejected.
- Guideline statements include evidence extrapolation and good-practice consensus.
- Observational associations are not represented as intervention effects.
- Symptom effects are not represented as control of inflammation.
- Publicly available source content was used for verification only; downstream copyright and licensing were not cleared.
- This evidence set is prepared for review, not clinical deployment.

## Verification result

All 53 automated tests passed. The workbook was rendered sheet-by-sheet and visually inspected. The formula scan returned zero matches for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A`.

Hard stop: second independent QA and human approval are required before any source or claim is treated as approved.
