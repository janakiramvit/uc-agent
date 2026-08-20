"""BM25 keyword retrieval correctness (agent_core.retrieval.UCEvidenceRetriever)."""

UC_ELIGIBLE_IDS = {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}


def test_bm25_retrieves_only_uc_eligible_claims(retriever):
    results = retriever.retrieve(query="fibre")
    assert results
    for r in results:
        assert r.claim_id in UC_ELIGIBLE_IDS


def test_bm25_topic_filter_restricts_candidates_before_ranking(retriever):
    results = retriever.retrieve(query="fibre", topic_filter="fibre")
    ids = {r.claim_id for r in results}
    assert ids == {"CLM-014", "CLM-094"}


def test_bm25_alcohol_query_surfaces_alcohol_claim(retriever):
    results = retriever.retrieve(query="alcohol", topic_filter="alcohol")
    ids = {r.claim_id for r in results}
    assert ids == {"CLM-095"}


def test_bm25_non_uc_disease_filter_returns_nothing(retriever):
    results = retriever.retrieve(query="fibre", disease_filter="crohns_disease")
    assert results == []


def test_bm25_never_returns_crohns_only_or_excluded_claims(retriever, package):
    results = retriever.retrieve(query="the")  # broad query, all documents rank
    ids = {r.claim_id for r in results}
    assert ids.isdisjoint(package.excluded_claim_ids)
    for claim_id in ids:
        original = next(c for c in package.all_claims if c["claimId"] == claim_id)
        assert original.get("conditionApplicability") != "crohns_disease"
