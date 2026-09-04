# Reconciliation SUMMARY (redacted - safe to commit)

_Generated 2026-09-04T20:53:30.323050+00:00 by `pipeline.reconcile`. Counts only; no evidence text, no connection strings._

## Comparison A
- prototype-v1 workbook  vs  ibd-prototype-evidence.json (same origin - full parity)
- rows: 826; match=752, null_preserved=74
- **material mismatches: 0**
- claim ID sets: both=49
- source ID sets: both=20

## Comparison B
- baseline-register workbook  vs  candidate-claims.json (pre-remediation reference)
- rows: 884; json_only=263, match=394, mismatch=54, null_preserved=56, workbook_only=117
- **material mismatches: 0**
- claim ID sets: both=56, {'register_workbook_only': 5, 'candidate_claims_json_only': 39}

## Comparison C
- baseline-register  vs  prototype-v1  (shared IDs - both current)
- rows: 510; json_only=60, match=422, mismatch=9, null_preserved=1, workbook_only=18
- **material mismatches: 4**
- claim ID sets: both=49, {'baseline-register_only': 12}
- source ID sets: both=20, {'baseline-register_only': 6}

## Per-field status tally (all comparisons)

| field | match | mismatch | material-mismatch | workbook_only | json_only | null_preserved |
|---|--:|--:|--:|--:|--:|--:|
| __id_set__ | 0 | 0 | 0 | 23 | 39 | 0 |
| applicability_limitations | 49 | 0 | 0 | 0 | 105 | 0 |
| authoritative_url | 188 | 5 | 0 | 0 | 1 | 0 |
| claim_text | 100 | 54 | 0 | 0 | 0 | 0 |
| condition_applicability | 188 | 1 | 1 | 0 | 5 | 0 |
| confidence | 49 | 0 | 0 | 0 | 56 | 0 |
| disease_context | 188 | 0 | 0 | 0 | 5 | 1 |
| evidence_level | 49 | 0 | 0 | 0 | 56 | 0 |
| evidence_status | 0 | 0 | 0 | 56 | 0 | 0 |
| limitations | 154 | 0 | 0 | 0 | 0 | 0 |
| outcome_type | 49 | 0 | 0 | 0 | 56 | 0 |
| precise_locator | 98 | 0 | 0 | 56 | 0 | 0 |
| prototype_eligibility_status | 49 | 0 | 0 | 0 | 0 | 56 |
| pub_year | 40 | 0 | 0 | 0 | 0 | 0 |
| review_status | 56 | 0 | 0 | 0 | 0 | 69 |
| source_type | 20 | 0 | 0 | 0 | 0 | 0 |
| supporting_excerpt | 151 | 3 | 3 | 0 | 0 | 0 |
| title | 40 | 0 | 0 | 0 | 0 | 0 |
| topic | 100 | 0 | 0 | 0 | 0 | 5 |

## Quarantine recommendations
- total: 6 across 6 entities
- `baseline-register`: 3
- `prototype-v1`: 3

Entity refs with a material mismatch (IDs only, no values):
- baseline-register:claim:CLM-081
- baseline-register:claim:CLM-083
- baseline-register:claim:CLM-085
- prototype-v1:claim:CLM-081
- prototype-v1:claim:CLM-083
- prototype-v1:claim:CLM-085

## Classifications (IDs + category only, no values)
- **expected_versioned_difference** (5): claim:CLM-097.authoritative_url, claim:CLM-098.authoritative_url, claim:CLM-099.authoritative_url, claim:CLM-100.authoritative_url, source:SRC-026.authoritative_url
- **requires_clinical_applicability_review** (1): claim:CLM-083.condition_applicability
