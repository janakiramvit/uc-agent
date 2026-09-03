"""The gate must not assume the inputs share a schema. Prove they don't."""

from __future__ import annotations

from pipeline import schema_infer


def _fields(doc, *sheet_or_container):
    if doc["kind"] == "json":
        shape = doc["shape"]
        if shape.get("container") == "array":
            return shape["record_fields"]
        return shape.get("claims[]", {}).get("record_fields", {})
    for s in sheet_or_container:
        if s in doc["sheets"]:
            return doc["sheets"][s]["fields"]
    return {}


def test_inference_runs_and_covers_all_inputs(tmp_path):
    docs = schema_infer.run(out_dir=tmp_path)
    assert {"register_workbook", "qa_workbook", "prototype_workbook", "prototype_json",
            "candidate_claims_json"} <= set(docs)
    assert (tmp_path / "_comparison.md").is_file()


def test_schemas_are_not_identical(tmp_path):
    docs = schema_infer.run(out_dir=tmp_path)
    reg = _fields(docs["register_workbook"], "Claims")
    proto = _fields(docs["prototype_workbook"], "Included Claims")
    cand = _fields(docs["candidate_claims_json"])

    # 1. claim-text column name differs across the three
    assert "Final remediated claim" in reg
    assert "claimText" in proto
    assert "claim" in cand and "claimText" not in cand

    # 2. the register carries a workflow "Evidence status" but NO evidence-STRENGTH
    #    column; the prototype workbook and candidate JSON both carry evidenceLevel.
    assert "Evidence status" in reg
    assert not any(k.lower().replace(" ", "").replace("_", "") in
                   ("evidencelevel", "evidencegrade", "levelofevidence") for k in reg)
    assert "evidenceLevel" in proto and "evidenceLevel" in cand

    # 3. condition applicability: string in workbooks/prototype-json, list in candidate json
    assert "list" in cand["conditionApplicability"]["types"]
    assert "str" in proto["conditionApplicability"]["types"]

    # 4. evidence-level vocabularies diverge
    proto_el = set(proto["evidenceLevel"]["enum_domain"] or [])
    cand_el = set(cand["evidenceLevel"]["enum_domain"] or [])
    assert "meta-analysis" in proto_el and "meta_analysis" in cand_el
    assert proto_el != cand_el
