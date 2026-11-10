# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-d27c0ed1114a` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/42737160838 · **Date:** 2026-11-10
**Run status:** `completed`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 27.1s |
| Discovery queries | 40 | 16 |
| Records screened | 200 | 0 |
| New sources accepted | 40 | 0 |
| Candidate excerpts | 100 | 0 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 0 |
| deferred | 0 |
| duplicate | 0 |
| rejected | 0 |

## QA

17 / 19 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Next run: search every configured provider (Europe PMC, PubMed, ClinicalTrials.gov, AGA, ACG, ECCO, NICE, BSG) for evidence published or updated since that provider's last successful cutoff (state/provider-state.json). Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-104/CLM-197 onward.",
  "topicId": "T-UCX-03",
  "searchId": null,
  "cursor": 0,
  "firstNewSourceId": "SRC-104",
  "firstNewClaimId": "CLM-197",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
