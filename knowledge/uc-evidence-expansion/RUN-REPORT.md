# UC Evidence-Expansion — Run Report

**Run ID:** `uc-exp-e648136e30e7`
**Run type:** one bounded, manually initiated UC evidence-research increment
**Date:** 2026-09-02
**Run status:** `partially_completed` (planned 2-topic scope finished inside every limit; a third topic was deliberately not started)

> Nothing in this run is clinically approved. All new evidence is `pending_clinical_review`. No application code,
> deployment, Vercel configuration, scheduler, or production RAG/vector index was touched.

---

## 1. Limits vs actuals

| Limit | Ceiling | Actual this run |
|---|---|---|
| Research runtime | 10 min | **~4 min 9 s** (13:08:34Z → 13:12:43Z) |
| Search queries | 10 | **5** (2 WebSearch discovery + 1 Europe PMC keyword + Europe PMC/NCBI identifier retrieval) |
| Records screened | 75 | **30** |
| New sources accepted | 5 | **3** (SRC-028, SRC-033, SRC-034) |
| PDFs downloaded | 3 | **0** |
| Candidate claims extracted | 15 | **13** (CLM-115 … CLM-127) |
| Retries per service | 2 | max 1 used (PubMed HTML, Europe PMC full-text XML) |
| Reference-following depth | 1 | 0 levels used |
| Consecutive empty searches → stop | 2 | triggered for T-UCX-01 discovery (calprotectin meta-analysis search) |

**Stop reason:** planned scope completed well inside all limits; starting topic T-UCX-03 (acute severe UC)
would have required full-text guideline sections that could not be retrieved cleanly in the remaining budget.

## 2. Topics

**Selected**

| Topic | Question nodes | Why |
|---|---|---|
| **T-UCX-01** — UC disease-activity monitoring biomarkers (fecal calprotectin, CRP, ESR) | L2-1.2, L3-1.2.1, L3-1.2.2 | Densest cluster of `none`-coverage nodes in the Reddit demand tree; top demand branch L1-1 (priority 10); guideline-dense so high-quality evidence is fast to find. |
| **T-UCX-02** — Treat-to-target & remission definitions (clinical vs endoscopic vs histologic; mucosal healing) | L3-1.2.3, L2-1.2 | L3-1.2.3 has `none` coverage and one authoritative consensus (STRIDE-II) answers it directly. |

**Deferred:** T-UCX-03 acute severe UC red flags (L3-1.1.2); T-UCX-04 starting a medicine / infection monitoring / loss-of-response & TDM (L2-2.1); T-UCX-05 biologic/JAK positioning & colectomy (L2-2.3); T-UCX-06 pregnancy / EIM / CRC surveillance (L2-3.3); T-UCX-07 UC-specific diet (L2-2.2).

**Next recommended topic:** **T-UCX-03 — acute severe ulcerative colitis: red-flag symptoms and urgent/emergency assessment thresholds** (primary node L3-1.1.2; only remaining `none`-coverage node with *High* clinical risk in branch L1-1).

## 3. Sources

| ID | Citation | Year | Type | Region | Full text | Archival |
|---|---|---|---|---|---|---|
| **SRC-028** | Singh S, et al. AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis. *Gastroenterology* 2023;164(3):344-372. PMID 36822736. DOI 10.1053/j.gastro.2022.12.007 | 2023 | Guideline (UC-specific) | US (AGA); Canada applicable w/ qualification | structured abstract only | `link_only` |
| **SRC-033** | Turner D, et al. STRIDE-II … Determining Therapeutic Goals for Treat-to-Target strategies in IBD. *Gastroenterology* 2021;160(5):1570-1583. PMID 33359090. DOI 10.1053/j.gastro.2020.12.031 | 2021 | Consensus (IBD-general: UC + Crohn's) | International (IOIBD); Canada + US applicable | structured abstract only | `link_only` |
| **SRC-034** | Feuerstein JD, et al. AGA Clinical Practice Guidelines on the Management of Moderate to Severe Ulcerative Colitis. *Gastroenterology* 2020;158(5):1450-1461. PMID 31945371. DOI 10.1053/j.gastro.2020.01.006 | 2020 | Guideline (UC-specific) | US (AGA); Canada applicable w/ qualification | citation only — **eligible, not extracted, deferred** | `link_only` |

- **Full-text vs abstract-only:** 0 full-text; 2 structured-abstract-only (SRC-028, SRC-033); 1 citation-only/deferred (SRC-034).
- **Excluded / deferred at screening:** ACG *Ulcerative Colitis in Adults* 2019 (PMID 30840605) — deferred: a 2025 ACG UC update is pre-staged as planned `SRC-027` in `knowledge/ibd-research-review/scripts/extend_uc_evidence.py`; adding the 2019 full guideline now risks a version conflict. Reserved for T-UCX-03. • ECCO *Therapeutics in UC: Medical Treatment* 2022 (PMID 34635919) — no abstract in retrieved metadata, full text not accessed within limits; deferred for a European-guideline / regional-qualification pass. • PMID 32044313 — identifier mis-resolved to an unrelated article; discarded.

## 4. Candidate claims

13 claims, all verbatim-supported by a retrieved structured abstract and substring-verified against the cached API response.

- **SRC-028 → CLM-115 … CLM-121** (7): biomarker + symptom monitoring in symptomatic remission; fecal calprotectin <150 µg/g to rule out inflammation; FC >150 µg/g with moderate/severe symptoms to inform treatment; endoscopy when biomarkers and symptoms are discordant; endoscopy when symptoms are mild; "7 conditional recommendations" + biomarker-vs-endoscopy knowledge gap; overall conclusion that FC / lactoferrin / CRP can inform UC monitoring. **conditionApplicability = `ulcerative_colitis`.**
- **SRC-033 → CLM-122 … CLM-127** (6): systematic-review size (11,278 screened / 435 included); most-important targets include CRP/ESR + calprotectin normalisation; long-term targets (clinical remission + endoscopic healing + disability/QoL/growth); short-term targets (symptom relief + marker normalisation); histological healing in UC is a *measure of remission depth*, not a formal target; framework must be adapted to the individual patient and local resources. **conditionApplicability = `ibd_general` (not relabelled UC-specific).**

## 5. Conflicts (kept visible, none resolved automatically)

| ID | Tension |
|---|---|
| CONF-01 | Fecal calprotectin **threshold granularity**: AGA operationalises 150 µg/g for UC; STRIDE-II names marker "normalization" without a numeric cut-off in its abstract. |
| CONF-02 | **Evolving target**: STRIDE-II (2021) says histologic healing in UC is *not* a formal target; later literature increasingly argues it should be. |
| CONF-03 | **Population scope**: STRIDE-II is IBD-general; CLM-122–127 must stay labelled `ibd_general`, never presented as UC-specific. |
| CONF-04 | **Certainty**: all 7 AGA recommendations are conditional; the guideline itself flags biomarker-vs-endoscopy monitoring as a knowledge gap. |
| CONF-05 | **Version / prior-run**: planned `SRC-027…032` / `CLM-101…114` in `extend_uc_evidence.py` were never materialized; reconcile before any promotion. |

## 6. Regional applicability

- **SRC-028 / SRC-034:** US professional-society guidance (AGA). Concepts transfer to Canada; fecal calprotectin assays are **not interchangeable**, so cut-offs need local assay validation; drug sequencing / formulary access differ in Canada.
- **SRC-033:** international consensus (IOIBD), Canadian and US authors; explicitly "adapt to local resources". Applies to both Canada and the US at the concept level; monitoring intervals not specified.
- Not clinician-confirmed — see GAP-09.

## 7. Licensing restrictions

- Every source is `link_only`: **no stated redistribution or local-archival licence** (Europe PMC `isOpenAccess = N`, `license = null` for all three).
- Unpaywall listed a "free" publisher PDF for SRC-028 — **not downloaded**; a reachable PDF was not assumed licensed.
- Retained (permitted): citation metadata, DOI, PubMed ID, canonical URL, access status, and the structured abstract text for SRC-028 and SRC-033.
- Not stored: any full text or publisher PDF.
- No paywall, authentication, robots rule, or rate limit was bypassed. PubMed's HTML was cookie-walled; retrieval switched to the Europe PMC REST and NCBI E-utilities public APIs.

## 8. Unresolved evidence gaps

See `EVIDENCE-GAPS.md` and the **Evidence Gaps** sheet. Headlines: UC-specific ESR value (GAP-01), colonoscopy/biopsy rationale (GAP-02), intestinal ultrasound (GAP-03), mucosal-healing prognosis (GAP-04), **acute severe UC red flags (GAP-05, high clinical risk)**, medicines / loss of response / TDM (GAP-06), biologic-JAK positioning & colectomy (GAP-07), pregnancy / EIM / CRC surveillance (GAP-08), Canada/US confirmation (GAP-09).

## 9. Checkpoint & resumption

- **Checkpoint:** `knowledge/uc-evidence-expansion/state/checkpoint.json` (validates against `state/checkpoint.schema.json`, draft-07). Known-good copy: `state/checkpoint.json.known-good`. Advisory lock: `state/run.lock` (released).
- **Run journal (append-only):** `knowledge/uc-evidence-expansion/journal/run-journal.ndjson` (12 events appended this run).
- **Exact next operation (from checkpoint):** start topic **T-UCX-03**, execute pending search **S-UCX-03-a** on Europe PMC from cursor `0`, then **S-UCX-03-b** (NCBI efetch of ACG 2019 PMID 30840605 ASUC section + AGA hospitalized-UC guidance). Skip identifiers already in `processedSourceIdentifiers`. Assign new IDs from **SRC-035** and **CLM-128**.

## 10. QA

Automated QA: **21 / 21 checks PASS** (`qa-results.json`, `QA-REPORT.md`, **QA Results** sheet). Automated QA does **not** constitute clinical approval; every check is itself pending human/clinical review.

## 11. Storage recommendation

See `STORAGE-RECOMMENDATION.md`. Compared Supabase Storage + Postgres/pgvector, Vercel Blob + compatible DB/vector store, and Cloudflare R2 + compatible DB. **Recommendation: Supabase Storage + Postgres/pgvector.** No service was provisioned, no account created, no credential added, no production change made.

## 12. Created / updated output paths

```
knowledge/uc-evidence-expansion/
  sources.json                         (new)
  candidate-claims.json                (new)
  question-coverage-map.json           (new)
  ingestion-manifest.json              (new)
  licensing-access-register.json       (new)
  qa-results.json                      (new)
  reviewer-workbook.xlsx               (new)
  reviewer-workbook.xlsx.inspect.ndjson(new)
  EVIDENCE-GAPS.md                     (new)
  QA-REPORT.md                         (new)
  RUN-REPORT.md                        (new)
  STORAGE-RECOMMENDATION.md            (new)
  README.md                            (new)
  state/checkpoint.json                (new)
  state/checkpoint.json.known-good     (new)
  state/checkpoint.schema.json         (new)
  state/run.lock                       (new, released)
  journal/run-journal.ndjson           (new, append-only)
  retrieval-cache/*.json               (new — API retrieval provenance, git-ignored)
  source-files/                        (empty — no archivable file this run)
```
