from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bullet(items):
    return "\n".join(f"- {item}" for item in items) or "- None recorded"


def main():
    data = json.loads((ROOT / "processing/checkpoints/research-data.json").read_text())
    summary = json.loads((ROOT / "run-summary.json").read_text())
    sources = data["sources"]
    claims = data["claims"]
    topics = Counter(c["topic"] for c in claims)
    outcomes = Counter(c["outcomeType"] for c in claims)
    conditions = Counter(v for c in claims for v in c["conditionApplicability"])
    contexts = Counter(v for c in claims for v in c["diseaseContext"])
    selected_lines = [
        f"**{s['sourceId']} — {s['sourceTitle']}** ({s['publicationYear']}; {s['studyType']}; "
        f"{s['fullTextAvailability']}). Coverage: {', '.join(s['relevantTopics'])}. "
        f"[Source]({s['canonicalUrl']})"
        for s in sources
    ]
    rejected_lines = [
        f"{r['source']} — {r['reason']}" for r in data["rejectedCandidates"][:30]
    ]
    strongest = [f"{name}: {count} retained candidate claims" for name, count in topics.most_common(6)]
    weakest = [f"{name}: {count} retained candidate claim(s)" for name, count in sorted(topics.items(), key=lambda x: x[1])[:8]]
    report = f"""# IBD Source Verification Report

**Status:** Pending human review. No source or claim is approved.

**Scope:** Standalone evidence review for adult users in Canada and the United States. This package is informational research support only; it does not diagnose disease, predict flares, establish that foods caused symptoms or inflammation, prescribe diets, or recommend treatment changes.

## Run overview

- Searches performed: {summary['searchesPerformed']}
- Candidates discovered: {summary['candidatesFound']}
- Sources selected: {summary['sourcesSelected']}
- Claims retained: {summary['claimsRetained']}
- Public full-text acquisitions: {summary['fullTextAcquisitions']}
- Abstract-only acquisitions: {summary['abstractOnlyAcquisitions']}
- Paid model calls: 0

## Selected sources

{bullet(selected_lines)}

## Rejected or deferred candidates

{bullet(rejected_lines)}

Rejection generally reflects source caps, insufficient incremental coverage, absent usable passages, or lower priority in this bounded first pass. It is not a universal judgment that a source is scientifically invalid.

## Condition and disease-context coverage

- Ulcerative-colitis applicability: {conditions.get('ulcerative_colitis', 0)} candidate claims
- Crohn’s-disease applicability: {conditions.get('crohns_disease', 0)} candidate claims
- Shared IBD applicability: {conditions.get('ibd_general', 0)} candidate claims
- Active disease: {contexts.get('active_disease', 0)} candidate claims
- Remission: {contexts.get('remission', 0)} candidate claims
- Post-surgical context: {contexts.get('post_surgery', 0)} candidate claims
- Stricture/obstruction-risk context: {contexts.get('stricture_or_obstruction_risk', 0)} candidate claims

These are candidate-claim counts, not evidence grades and not approval counts. A single claim may carry more than one applicability value.

## Strongest evidence areas

{bullet(strongest)}

The strongest areas in this initial set are those supported by current consensus/guideline material, systematic reviews or meta-analyses, and controlled studies. Evidence remains heterogeneous by disease, disease state, outcome definition, and intervention fidelity.

## Weakest evidence areas and gaps

{bullet(weakest)}

Additional under-covered dimensions from the coverage matrix:

{bullet(summary['coverageGaps'])}

Particularly cautious future expansion is warranted for meal timing, hydration and sodium, fermented foods, dairy/lactose, coffee/caffeine, alcohol, artificial sweeteners, and direct human evidence on individual additives. General-population incidence evidence should remain clearly labelled as indirect and must not be converted into individual disease-course advice.

## Conflicts and non-comparability

The run preserved {summary['conflicts']} potential conflict/non-comparability flags and {summary['duplicates']} near-duplicate flags. Many flags arise because findings concern different diseases, active disease versus remission, symptoms versus objective inflammation, different populations, or different evidence levels. They must not be silently merged. The workbook identifies the paired claims for human review.

## Canada and United States applicability

Scientific applicability was assessed separately from practical applicability. For each source and claim the package records population/region and notes possible differences in:

- food availability, cost, fortification, labelling, and formula access
- cultural fit and adaptable food equivalents
- healthcare pathways and access to IBD-specialist dietitians
- disease phenotype, activity, surgery, and stricture risk
- whether a named dietary pattern’s defining characteristics can transfer without prescribing one cuisine

International evidence was retained when scientifically relevant. Non-North-American origin was treated as a limitation to assess, not an automatic exclusion. US official patient information is directly useful to US users but still may not map perfectly to Canadian services or terminology.

## Reliability and acquisition limitations

- Publicly accessible sources only; no paywalls were bypassed.
- Abstract-only records are explicitly labelled and normally limited to moderate confidence.
- Metadata, abstracts, and deterministic sentence extraction cannot replace full-text appraisal of methods, tables, risk of bias, or subgroup definitions.
- Supporting excerpts are preserved, but sentence-level extraction can omit surrounding qualifications.
- Search ranking and source availability can change over time.
- Sample size, population, and region are marked as not reported when unavailable in the acquired passage.
- Confidence describes source quality and applicability, not approval and not certainty for an individual.

## Risks of product misuse

The most important risks are treating association as causation; treating symptom response as proof of inflammatory change; using a population result as individualized advice; ignoring disease activity, strictures, surgery, malnutrition, medication, or clinician context; and presenting a named diet as universally appropriate. Any future product must retain the boundaries and uncertainty language represented here.

## Recommended next research expansion

1. Human-review the selected passages against full text, especially abstract-only records.
2. Add targeted controlled evidence for ulcerative-colitis-specific dietary interventions and objective inflammatory outcomes.
3. Strengthen post-surgical, stricture, hydration, sodium, meal-timing, alcohol, caffeine, dairy/lactose, fermented-food, and food-reintroduction coverage.
4. Add Canadian clinical and dietetic guidance where available and compare US/Canadian food labelling, fortification, formula access, and referral pathways.
5. Reconcile superseded guidelines and document recommendation strength and evidence grades directly from the current full text.

## Approval boundary

All review fields are blank. The package must remain outside any application or retrieval system until a human explicitly approves individual sources and claims.
"""
    (ROOT / "source-verification-report.md").write_text(report)


if __name__ == "__main__":
    main()

