# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-f96662ebf3d4` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/43100207814 · **Date:** 2026-11-11
**Run status:** `completed`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 36.0s |
| Discovery queries | 40 | 16 |
| Records screened | 200 | 29 |
| New sources accepted | 40 | 7 |
| Candidate excerpts | 100 | 6 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 7 |
| deferred | 2 |
| duplicate | 17 |
| rejected | 3 |

## QA

17 / 19 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Next run: search every configured provider (Europe PMC, PubMed, ClinicalTrials.gov, AGA, ACG, ECCO, NICE, BSG) for evidence published or updated since that provider's last successful cutoff (state/provider-state.json). Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-126/CLM-218 onward.",
  "topicId": "T-UCX-03",
  "searchId": null,
  "cursor": 0,
  "firstNewSourceId": "SRC-126",
  "firstNewClaimId": "CLM-218",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
