# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-00f246ea42e7` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/33926438666 · **Date:** 2026-09-04
**Run status:** `partial`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 2.0s |
| Discovery queries | 10 | 2 |
| Records screened | 30 | 25 |
| New sources accepted | 5 | 0 |
| Candidate excerpts | 20 | 0 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 0 |
| deferred | 20 |
| duplicate | 0 |
| rejected | 5 |

## QA

13 / 15 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Continue topic T-UCX-03. Resume search S-UCX-03-a from cursor AoJwgO7cmI8DKDUwOTE2NzEz. Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-036/CLM-129 onward.",
  "topicId": "T-UCX-03",
  "searchId": "S-UCX-03-a",
  "cursor": "AoJwgO7cmI8DKDUwOTE2NzEz",
  "firstNewSourceId": "SRC-036",
  "firstNewClaimId": "CLM-129",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
