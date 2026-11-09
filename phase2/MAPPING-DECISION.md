# Which question mapping is used for Phase-2 evaluation

**Decision.** Coverage of the 39 patient questions is evaluated **only** from the evidence-derived mapping:

1. candidate claims keep their own source-provided `mappedPatientQuestionIds`;
2. production (`prototype-v1`) and baseline-register claims are mapped by the explicit claim-topic table
   `config/topic_question_map.json` (plus one documented override, CLM-081 -> L2-2.2), tagged
   `mapping_basis=topic_rule` / `claim_override`;
3. `core_condition_knowledge` and null-topic claims stay **unmapped** (a known limitation, not repaired).

**The question tree's `current_evidence_package_coverage` field (`partial` / `none`) is informational
only.** It is carried through as `prior_tree_coverage` and is never an input to the computation. The file
does not record how those labels were derived, so it cannot be audited claim by claim.

**Disagreement.** `output/tree-disagreement.json` lists every node where the tree label and the evaluation
disagree (11 of 39 in the production-servable scope, all of the form tree=`partial`, evaluated=`not_covered`).
They are documented, not adjusted: no claim, mapping or status was changed to make the numbers agree, and no
evidence was added.

**Why the evaluation is the stricter reading.** A question counts as `covered` only when a *usable*,
*UC-applicable* claim is mapped to it; IBD-general-only claims give `partial`; Crohn's-only claims never count.
That mirrors the production retrieval rule (`"ulcerative_colitis" in conditionApplicability`).

**Scopes reported.** `production_servable` (claims in the live package) and `all_possessed` (adds the baseline
register and the Phase-2 candidates, none of which is approved or served).
