# Multi-source discovery (providers)

Every run attempts **all eight sources, independently**, and reports each one: Europe PMC, PubMed/MEDLINE,
ClinicalTrials.gov, and the guideline bodies AGA, ACG, ECCO, NICE and BSG. A failure, access limitation or empty result in one
source never stops or hides another.

## Root causes of the zero-result runs

| # | Cause | Evidence |
|---|---|---|
| 1 | The default Europe PMC query used PubMed syntax, `(2021:2026[pub_year])`. Europe PMC does not understand it and answers HTTP 200 with `hitCount: 0` - no error. | `tests/fixtures/europepmc_zero_pubmed_syntax.json` (live 2026-11-10: 0 hits; the same topic with `FIRST_IDATE:[...]` returned 190 hits in 8 days) |
| 2 | One query, one provider, no date window: nothing tied a run to "what is new since the last run". | `runner._do_research` (removed) |
| 3 | Silent failure modes in the providers themselves: PubMed ignores unknown fields/unbalanced syntax and returns the whole database (64,066 hits for garbage); ClinicalTrials.gov returns an empty 200 for a malformed date range; Europe PMC drops an unbalanced clause. None raise an error. | recorded in `tests/fixtures/pubmed_esearch_garbage_query.json`, `clinicaltrials_bad_range.json` |
| 4 | PubMed path returned titles only (no abstract) so every record was deferred; ClinicalTrials.gov summaries were treated like abstracts and could have produced "claims". | `screening`, `extract` (now guarded) |
| 5 | A run that did nothing still exited 0 and looked healthy; no alert, no per-source numbers. | scheduled runs 2026-11-02..09: 17-51 s, 0 screened |

## Architecture

```
window.py          per-provider search window: [last successful cutoff - 1 day, today], floored at 2026-11-10
providers/         one connector per source, each with ITS OWN query syntax + date filter (never shared)
  europepmc.py     FIRST_IDATE:[a TO b] ... NOT SRC:PPR          lint + canary
  pubmed.py        "..."[tiab] OR "..."[MeSH Terms], datetype=edat, mindate/maxdate (YYYY/MM/DD), translation check, efetch abstracts
  clinicaltrials.py  AREA[LastUpdatePostDate]RANGE[a,b]; all statuses; trial types only
  guidelines.py    AGA / ACG / ECCO / NICE / BSG: robots-gated site channel + PubMed-indexed society-journal channel
  robots.py        robots.txt policy (403 = not permitted, 5xx = unknown, Crawl-delay honoured)
crossdedupe.py     union-find over DOI / PMID / PMCID / NCT / canonical URL / normalised title; trials never merge with papers
discover.py        rotate providers, search, canary, cross-dedupe, round-robin screening, funnel, alerts, cutoffs
funnel.py          per-provider funnel (searches, hits, returned, screened, duplicates, rejected/deferred + reasons, accepted, claims)
alerts.py          ERROR / WARNING / INFO with codes; GitHub annotations; non-zero exit on ERROR
provider_state.py  state/provider-state.json: cutoffs, health counters, rejected-key memory (atomic + known-good)
reporting.py       DAILY-REPORT.md + provider-funnel.json (staging) and counts-only provider health in the redacted artifact
```

**Why a date window instead of rotating keyword topics.** "Everything new for ulcerative colitis since the last successful cutoff"
is complete by construction; a rotating topic list can never promise nothing was missed. A provider's cutoff advances only when
its whole window was retrieved *and* screened; otherwise the window is kept and the next run continues from it.

**Zero results are always explained.** After a zero (or any) window, a *canary* - a one-year window in the same provider syntax - runs:
canary > 0 -> "no new records" (with the reason); canary = 0 -> `INVALID_QUERY` error; window hits > canary -> the date filter is being
ignored (`INVALID_QUERY`). Providers that normally return results daily (Europe PMC, PubMed) escalate: 2 consecutive zero runs ->
WARNING, 3 -> ERROR.

## Evidence types (kept separate end to end)

`published_study` - `clinical_guideline` - `ongoing_trial` - `completed_trial_record`. Trial registry records are accepted only as
labelled trial sources with **no claims** (`extract_candidates` returns `[]` for them; QA-16 verifies). Every claim is abstract-only
and flagged `requiresFullTextVerification`.

## Access, copyright and robots

* Only public metadata, the public abstract (PubMed / Europe PMC / registry), the DOI and the legal source link are retained.
* The HTTP client refuses any `.pdf` URL and any `application/pdf` response; PDF/podcast links on listings are discarded.
* **AGA (gastro.org)**: robots.txt disallows all generic bots -> the site is never fetched (only `/robots.txt`); AGA guidelines are found through
  the PubMed index of *Gastroenterology* / *Clin Gastroenterol Hepatol*. **ECCO (ecco-ibd.eu)**: robots.txt answers 403 -> treated as not
  permitted; found through the *J Crohns Colitis* PubMed index. **ACG** (gi.org listing), **BSG** (sitemap) and **NICE** (seeded from NG130
  and the guidance it links) are read only where robots.txt allows. These access limits are reported every run as `ACCESS_LIMITED` warnings.
* Known limitations: NICE has no machine-readable feed (its listing page returns 403), so technology appraisals are only found when linked
  from a watched page; BSG titles come from the URL slug (no page fetch); a guideline listing without dates is change-detected by new URLs; a *revision* of an already-staged NICE/BSG page (same URL) is treated as a duplicate and not re-staged;
  deferred records (no public abstract yet) are retried only while they stay inside the 1-day overlap window.

## Running

```
python -m uc_evidence_discovery --state-root <worktree of automation/uc-evidence-staging> [--no-push]
UC_DISCOVERY_TODAY=2026-11-10 python -m ...        # controlled date
python -m pytest                                    # offline: unit tests + recorded fixtures
python -m pytest tests_live -m live -o addopts=     # one controlled live smoke test per provider
python tests/record_fixtures.py                     # re-record fixtures
```
