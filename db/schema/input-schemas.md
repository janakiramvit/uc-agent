# Inferred input schemas + comparison

Machine inference: `python -m pipeline.ingest --step infer` writes
`db/schema/inferred/*.json` + `*.md` + `_comparison.md` (all **gitignored** — they can
echo workbook values). This file is the committed hand summary.

## The inputs are NOT one schema

| concept | `register_workbook` (Claims) | `prototype_workbook` (Included Claims) | `candidate-claims.json` |
|---|---|---|---|
| claim id | `Claim ID` | `claimId` | `claimId` |
| claim text | `Final remediated claim` (+ `Original claim`, `QA proposed claim`) | `claimText` | `claim` |
| supporting excerpt | `Preserved supporting excerpt` | `supportingExcerpt` | `supportingExcerpt` |
| locator | `Precise locator` | `exactLocator` | `pageNumber` (mostly empty) |
| condition applicability | `"a; b; c"` string | `"a; b; c"` string | **`["a","b"]` list** |
| disease context | `"a; b"` string | `"a; b"` string | **list** |
| evidence level | **absent** (per-claim) | `evidenceLevel` free-text (`meta-analysis`, `clinical guideline`, `EL5`, `guideline/consensus`, `review`, …) | `evidenceLevel` snake vocab (`meta_analysis`, `formal_guideline`, …) |
| outcome type | **absent** | `outcomeType` (+ `obstruction_risk`, `perioperative_nutrition_management`, `evidence_uncertainty`) | `outcomeType` (+ `adverse_effects`, `remission_maintenance`) |
| confidence | **absent** | `confidence` (high/moderate/low) | `confidence` (high/moderate) |
| review status | `Review status` | absent | `reviewStatus` |
| workflow status | `Evidence status`, `Final-QA eligibility`, `Verification status`, `Future approved-export eligibility` | `prototypeEligibilityStatus` | `reviewStatus` only |

Other schema families:
- **`qa_workbook`** — 8 QA sheets. `Source and Locator QA` (61 rows) and `Corrected Claim
  QA` (10) carry QA-*observed* `Outcome type` / `Study type` / `Confidence`; these are kept
  in `claim_qa.findings` and **never** merged into `claim`.
- **`prototype_json`** — same shape as `prototype_workbook` (string enums, `claimText`);
  it is the shadow-test oracle, not a load source. Note token **order** in
  `conditionApplicability` differs between the workbook and the JSON for some rows
  (`ulcerative_colitis; crohns_disease; ibd_general` vs
  `ibd_general; crohns_disease; ulcerative_colitis`) — set-equal, reconciled as `match`.

## Adapter decisions from this

1. Two load adapters (`register_workbook`, `prototype_workbook`) + one overlay
   (`qa_workbook`) + one read-only reference (`json_reconcile`).
2. `"a; b; c"` → `text[]` via `enums.split_multi`; list inputs pass through.
3. Register claims get `evidence_level` / `outcome_type` / `confidence` / `study_type` /
   `plain_language_explanation` / `applicability_limitations` = `NULL` (no source column).
4. Enum vocab reconciled through `enum_crosswalk` (see `enumerations.md`); unmapped →
   quarantine (`condition`) or pending-NULL (`evidence_level`, …), raw always kept.

## Counts

| input | sources | claims | excluded | other |
|---|--:|--:|--:|---|
| register_workbook | 26 (SRC-001..026) | 61 (CLM-005..100) | 40 removed/replaced + CLM-092 | 4 audit sheets → `reconcile_raw` |
| prototype_workbook | 20 | 49 | 12 | matches `ibd-prototype-evidence.json` exactly |
| qa_workbook | — | — | — | 133 `claim_qa_raw` (10 + 61 + 61 + 1) |
| candidate-claims.json | — | 95 | — | pre-remediation superset |
