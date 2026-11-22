# UC Evidence-Discovery — Daily Run Report

**Run ID:** `uc-exp-18c85e919ea3` · **Run:** https://github.com/janakiramvit/uc-agent/actions/runs/45067410780 · **Date:** 2026-11-22
**Run status:** `partial`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | 450s soft / 540s finalize | 66.4s |
| Discovery queries | 40 | 16 |
| Records screened | 200 | 262 |
| New sources accepted | 40 | 9 |
| Candidate excerpts | 100 | 12 |
| PDFs archived | 0 (policy) | 0 |

## Dispositions

| Disposition | Count |
|---|---|
| accepted | 9 |
| deferred | 45 |
| duplicate | 197 |
| rejected | 11 |

## QA

17 / 19 automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{
  "description": "Next run: search every configured provider (Europe PMC, PubMed, ClinicalTrials.gov, AGA, ACG, ECCO, NICE, BSG) for evidence published or updated since that provider's last successful cutoff (state/provider-state.json). Skip every identifier in processedSourceIdentifiers. Allocate new ids from SRC-251/CLM-319 onward.",
  "topicId": "T-UCX-03",
  "searchId": null,
  "cursor": 0,
  "firstNewSourceId": "SRC-251",
  "firstNewClaimId": "CLM-319",
  "doNot": [
    "approve any source or claim",
    "download a PDF whose redistribution licence is not established",
    "promote anything to the production RAG/vector index or Supabase",
    "convert Crohn's-only or IBD-general findings to UC-specific claims",
    "make any paid model or API call"
  ]
}
```
