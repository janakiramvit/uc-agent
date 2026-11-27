# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-bf2271e21c38` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/46077188451 · **Date:** 2026-11-27
**Run status:** `partial`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 163.5s |
| Discovery queries | 40 | 16 |
| Records screened | 200 | 410 |
| New sources accepted | 40 | 15 |
| Candidate excerpts | 100 | 6 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 15 |
| deferred | 68 |
| duplicate | 214 |
| rejected | 113 |

## QA

17 / 19 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Next run: search every configured provider (Europe PMC, PubMed, ClinicalTrials.gov, AGA, ACG, ECCO, NICE, BSG) for evidence published or updated since that provider's last successful cutoff (state/provider-state.json). Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-337/CLM-368 onward.",
  "topicId": "T-UCX-03",
  "searchId": null,
  "cursor": 0,
  "firstNewSourceId": "SRC-337",
  "firstNewClaimId": "CLM-368",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
