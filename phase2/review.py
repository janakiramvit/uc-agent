"""Owner-review file: non-production records that are BOTH usable and UC-applicable.

Nothing here approves anything. Every entry carries an empty decision line for the owner.
"""

from __future__ import annotations

from phase2 import paths


def review_candidates(result: dict) -> tuple[list[dict], list[dict]]:
    """(uc_applicable_usable, ibd_general_usable) among non-production records - discovered, never assumed."""
    nonprod = [r for r in result["claims"] if r["originating_dataset"] != paths.DS_PRODUCTION and not r["in_production"]]
    usable = [r for r in nonprod if r["status"] == "usable"]
    return ([r for r in usable if r["applicability_class"] == "uc_specific"],
            [r for r in usable if r["applicability_class"] == "ibd_general"])


def _questions(result: dict, row: dict) -> list[str]:
    qs = result["coverage"]["questions"]
    return [f"{q} - {qs[q]['question']}" for q in row["mapped_question_ids"] if q in qs]


def _entry(result: dict, r: dict, n: int) -> list[str]:
    L = [f"### {n}. {r['claim_id']} - `{r['record_id']}`", "",
         f"- **Status:** {r['status']} (not approved; review status `{r['review_status'] or 'none recorded'}`, "
         f"evidence status `{r['evidence_status'] or 'none recorded'}`)",
         f"- **Claim:** {r['claim_text']}",
         f"- **Source:** {r['source_id']} - {r['source_title'] or 'title not recorded'}",
         f"- **Source URL:** {r['source_url']}",
         f"- **Publication date:** {r['publication_date'] or 'not recorded'}",
         f"- **Supporting excerpt:** \"{r['supporting_excerpt']}\"",
         f"- **Locator:** {r['locator']}",
         f"- **Applicability:** {', '.join(r['uc_applicability'])} ({r['applicability_class']}); "
         f"disease context: {', '.join(r['disease_context']) or 'not recorded'}",
         f"- **Limitations:** {r['limitations'] or 'none recorded'}"]
    qs = _questions(result, r)
    L.append(f"- **Related patient questions** ({r['mapping_basis']}): " + ("; ".join(qs) if qs else "none mapped"))
    for f in r.get("review_flags", []):
        L.append(f"- **Reviewer attention:** {f}")
    for v in r.get("variant_of", []):
        diff = ", ".join(v["differs_in"]) or "no field in the compared set"
        L.append(f"- **Variant note:** a record with the same claim ID exists as `{v['record_id']}`; differs in: {diff}.")
    L += ["- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)", ""]
    return L


def render(result: dict) -> str:
    uc, general = review_candidates(result)
    L = ["# Owner review - non-production evidence that is usable and UC-applicable", "",
         "Nothing below is approved, promoted or served. These records sit in dev staging only.", "",
         f"**{len(uc)} records** are usable and UC-applicable (`ulcerative_colitis` in the applicability, the same rule "
         "production uses); **" + str(len(general)) + "** more are usable but IBD-general only (listed after, not UC-eligible "
         "under the production rule). Counts are discovered from the manifest, not assumed.", "",
         "## A. Usable and UC-applicable", ""]
    for i, r in enumerate(uc, 1):
        L += _entry(result, r, i)
    L += ["## B. Usable, IBD-general only (not UC-eligible under the production rule)", ""]
    for i, r in enumerate(general, 1):
        L += _entry(result, r, i)
    return "\n".join(L) + "\n"
