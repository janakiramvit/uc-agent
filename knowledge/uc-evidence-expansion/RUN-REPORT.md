# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-c58600b5bdd9` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/34884740724 · **Date:** 2026-09-14
**Run status:** `completed`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 0.9s |
| Discovery queries | 10 | 1 |
| Records screened | 30 | 0 |
| New sources accepted | 5 | 0 |
| Candidate excerpts | 20 | 0 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 0 |
| deferred | 0 |
| duplicate | 0 |
| rejected | 0 |

## QA

13 / 15 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Continue topic T-UCX-03. Resume a fresh discovery query from cursor 0. Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-046/CLM-139 onward.",
  "topicId": "T-UCX-03",
  "searchId": null,
  "cursor": 0,
  "firstNewSourceId": "SRC-046",
  "firstNewClaimId": "CLM-139",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
