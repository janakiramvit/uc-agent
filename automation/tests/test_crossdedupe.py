from __future__ import annotations

from uc_evidence_discovery import crossdedupe


def rec(provider, **kw):
    base = {"provider": provider, "title": "Vedolizumab versus adalimumab in ulcerative colitis: a trial",
            "doi": "", "pmid": "", "pmcid": "", "nctId": "", "canonicalUrl": "", "abstractText": "",
            "evidenceType": "published_study"}
    base.update(kw)
    return base


def test_same_paper_from_two_providers_merges_by_doi_and_remembers_both_finders():
    a = rec("europepmc", doi="10.1/ABC", pmid="1", abstractText="x" * 200)
    b = rec("pubmed", doi="10.1/abc", pmid="1", pmcid="PMC9")
    m = crossdedupe.merge([a, b])
    assert len(m.records) == 1
    assert m.records[0]["foundBy"] == ["europepmc", "pubmed"]
    assert m.records[0]["pmcid"] == "PMC9"                    # identifiers unioned
    assert m.absorbed_by_provider == {"pubmed": 1}


def test_merge_by_pmid_pmcid_url_and_normalised_title_alone():
    for key in ({"pmid": "42"}, {"pmcid": "PMC7"}, {"canonicalUrl": "https://Example.org/a/"}):
        a, b = rec("europepmc", **key), rec("pubmed", **{**key, "canonicalUrl": key.get("canonicalUrl", "").rstrip("/")})
        assert len(crossdedupe.merge([a, b]).records) == 1
    t1 = rec("europepmc", title="Fecal calprotectin in ulcerative colitis: a meta-analysis.")
    t2 = rec("pubmed", title="Fecal  Calprotectin in Ulcerative Colitis - A Meta-Analysis")
    assert len(crossdedupe.merge([t1, t2]).records) == 1


def test_richest_record_is_kept_and_a_guideline_tag_wins_over_study():
    a = rec("europepmc", doi="10.1/g", abstractText="")
    b = rec("pubmed", doi="10.1/g", abstractText="y" * 300, evidenceType="clinical_guideline", society="ACG")
    out = crossdedupe.merge([a, b]).records[0]
    assert out["abstractText"] and out["evidenceType"] == "clinical_guideline"


def test_a_trial_registry_record_never_merges_with_a_publication_even_with_same_nct_or_title():
    pub = rec("pubmed", nctId="NCT01234567", title="Same long title about ulcerative colitis treatment")
    trial = rec("clinicaltrials", nctId="NCT01234567", evidenceType="ongoing_trial",
                title="Same long title about ulcerative colitis treatment")
    out = crossdedupe.merge([pub, trial]).records
    assert len(out) == 2 and {r["evidenceType"] for r in out} == {"published_study", "ongoing_trial"}


def test_different_papers_are_not_merged_and_short_titles_do_not_merge():
    assert len(crossdedupe.merge([rec("a", title="Case report", doi="10.1/a"), rec("b", title="Case report", doi="10.1/b")]).records) == 2
    assert len(crossdedupe.merge([rec("a", title="Study one of ulcerative colitis outcomes", doi="10.1/a"),
                                  rec("b", title="Study two of ulcerative colitis outcomes", doi="10.1/b")]).records) == 2


def test_duplicate_within_one_provider_is_counted_against_that_provider():
    m = crossdedupe.merge([rec("pubmed", pmid="5"), rec("pubmed", pmid="5")])
    assert len(m.records) == 1 and m.absorbed_by_provider == {"pubmed": 1}


def test_two_versions_of_a_guideline_with_the_same_title_but_different_dois_are_not_merged():
    t = "ACG Clinical Guideline: Ulcerative Colitis in Adults"
    v1 = rec("acg", title=t, doi="10.14309/ajg.2019.1", pmid="1", evidenceType="clinical_guideline")
    v2 = rec("pubmed", title=t, doi="10.14309/ajg.2025.2", pmid="2", evidenceType="clinical_guideline")
    assert len(crossdedupe.merge([v1, v2]).records) == 2


def test_title_only_prior_duplicate_rule_does_not_swallow_a_new_version_with_its_own_doi():
    from uc_evidence_discovery.dedup import CandidateKey, ProcessedIndex
    idx = ProcessedIndex()
    idx.add(CandidateKey.from_record({"title": "ACG Clinical Guideline: Ulcerative Colitis in Adults", "doi": "10.1/old"}))
    new_version = CandidateKey.from_record({"title": "ACG Clinical Guideline: Ulcerative Colitis in Adults", "doi": "10.1/new"})
    assert idx.duplicate_reason(new_version) is None
    no_ids = CandidateKey.from_record({"title": "ACG Clinical Guideline: Ulcerative Colitis in Adults"})
    assert idx.duplicate_reason(no_ids) is not None
