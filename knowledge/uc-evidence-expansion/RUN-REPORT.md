# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-d2aed195360a` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/43309315361 · **Date:** 2026-11-12
**Run status:** `completed`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 57.3s |
| Discovery queries | 40 | 16 |
| Records screened | 200 | 98 |
| New sources accepted | 40 | 13 |
| Candidate excerpts | 100 | 5 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 13 |
| deferred | 18 |
| duplicate | 20 |
| rejected | 47 |

## QA

17 / 19 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Next run: search every configured provider (Europe PMC, PubMed, ClinicalTrials.gov, AGA, ACG, ECCO, NICE, BSG) for evidence published or updated since that provider's last successful cutoff (state/provider-state.json). Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-140/CLM-224 onward.",
  "topicId": "T-UCX-03",
  "searchId": null,
  "cursor": 0,
  "firstNewSourceId": "SRC-140",
  "firstNewClaimId": "CLM-224",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
