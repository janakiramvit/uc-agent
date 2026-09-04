# UC Evidence-Expansion — Unresolved Evidence Gaps

**Run ID:** `uc-exp-e648136e30e7` · **Date:** 2026-09-02 · Status after this increment.

Reddit demand tree (`uc_39_question_tree.json`) is used only to prioritise these gaps. Reddit posts and personal
experiences are **not** medical evidence. Nothing below is clinically approved.

## Scope covered this run

Two topics only — **T-UCX-01** (UC disease-activity monitoring biomarkers) and **T-UCX-02** (treat-to-target &
remission definitions) — mapping to Reddit question nodes **L2-1.2, L3-1.2.1, L3-1.2.2, L3-1.2.3** and touching
**L2-1.1** and **L3-1.3.3**. All other nodes remain as before this run.

## Gap register

| Gap | Node(s) | Status | Why still open | Next action |
|---|---|---|---|---|
| **GAP-01** — UC-specific value of ESR for monitoring | L3-1.2.1 | open | No UC-specific source ingested for ESR. STRIDE-II (SRC-033) mentions ESR only as a general IBD marker (CLM-123); no IBD-general or Crohn's evidence was relabelled to UC. | Targeted search for UC-specific ESR performance vs fecal calprotectin / CRP. |
| **GAP-02** — Colonoscopy / biopsy rationale when labs & symptoms look reassuring | L3-1.2.2 | partially_open | Only the biomarker–symptom **discordance** scenario (CLM-118) and the **mild-symptom** scenario (CLM-119) are covered. No dedicated histology / biopsy / dysplasia-surveillance source. | Ingest a UC endoscopy + histology guideline section. |
| **GAP-03** — Intestinal ultrasound for UC monitoring | L3-1.2.2 | open | Not addressed. A prospective UC IUS cohort (TRUST&UC) is pre-staged as planned `SRC-029` in `extend_uc_evidence.py` but was never materialized. | Reconcile the planned `SRC-029` or ingest a current IUS source. |
| **GAP-04** — Prognostic value of mucosal / histologic healing in UC | L3-1.2.3 | partially_open | Target **definitions** are covered (CLM-124, CLM-126). Outcome evidence (relapse, hospitalisation, colectomy, cancer risk) is not ingested. | Ingest a mucosal-healing outcomes systematic review / meta-analysis. |
| **GAP-05** — Acute severe UC: red-flag symptoms & urgent/emergency assessment | L3-1.1.2 | open | **Deferred this run.** Needs full-text guideline sections (e.g. Truelove & Witts criteria) that could not be retrieved cleanly within the time/query budget. **High clinical risk.** | Run **T-UCX-03** next (see checkpoint `nextRecommendedOperation`). |
| **GAP-06** — Starting a UC medicine; infection monitoring; loss-of-response assessment & therapeutic drug monitoring | L2-2.1, L3-2.1.1, L3-2.1.2, L3-2.1.3 | open | Out of scope for a 2-topic increment. `SRC-034` (AGA moderate-to-severe UC 2020) was accepted as *eligible* but not extracted; its full-text recommendation statements are deferred. | Run **T-UCX-04**; begin with SRC-034 full-text extraction. |
| **GAP-07** — Biologic / small-molecule / JAK inhibitor comparative positioning; colectomy decision | L2-2.3, L3-2.3.1, L3-2.3.3 | open | Partly pre-staged (planned `SRC-031`/`SRC-032`, upadacitinib & tofacitinib trials) but never materialized; needs reconciliation with the prior planned run. | Run **T-UCX-05** after reconciling the planned set. |
| **GAP-08** — Pregnancy & reproductive health; extraintestinal manifestations; colorectal-cancer surveillance & vaccines | L3-3.3.1, L3-3.3.2, L3-3.3.3 | open | Distinct evidence bodies; deferred. | Run **T-UCX-06**. |
| **GAP-09** — Canada vs US applicability confirmation | cross-cutting | open | Assessed per source (US-origin AGA guidance; Canadian transfer and assay/formulary caveats noted) but **not clinician-confirmed**. | Human reviewer to confirm regional transfer, fecal calprotectin assay calibration, and drug-access notes. |
| **GAP-10** — Symptom vs objective inflammation discordance (dedicated UC cohort evidence) | L3-1.1.3, L3-1.2.3 | partially_open | STRIDE-II frames histologic healing as remission depth (CLM-126); AGA covers biomarker–symptom discordance (CLM-118). No dedicated UC cohort quantifying how often symptoms and endoscopy/histology disagree. | A pre-staged secondary-cohort analysis (planned `SRC-030`) exists in `extend_uc_evidence.py`; reconcile or ingest current evidence. |

## Prior-run reconciliation note

`knowledge/ibd-research-review/scripts/extend_uc_evidence.py` stages **planned** sources `SRC-027`–`SRC-032`
and **planned** claims `CLM-101`–`CLM-114` (ACG UC 2025 update, AGA UC biomarkers, TRUST&UC intestinal ultrasound,
a UC symptom/endoscopy-histology cohort, and upadacitinib/tofacitinib maintenance evidence). **None of these were
ever persisted** — no output files exist. This run:

- reserved `SRC-001…032` and `CLM-001…114` so no ID collides;
- adopted the planned canonical id **`SRC-028`** for the AGA UC biomarkers guideline (same PMID/DOI), documented in
  `sources.json → SRC-028.idProvenance` and `deduplication`;
- issued new IDs **`SRC-033`, `SRC-034`, `CLM-115…127`**.

A human reviewer should decide whether to formally fold the planned `SRC-027/029/030/031/032` set into this package
before any promotion.
