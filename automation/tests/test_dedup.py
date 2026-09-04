from __future__ import annotations

from uc_evidence_discovery.dedup import CandidateKey, ProcessedIndex, content_hash, norm_doi, norm_nct, norm_url


def test_normalisers():
    assert norm_doi("https://doi.org/10.1053/J.Gastro.2022.12.007") == "10.1053/j.gastro.2022.12.007"
    assert norm_doi("DOI: 10.1/x") == "10.1/x"
    assert norm_nct("nct01234567 ") == "NCT01234567"
    assert norm_url("HTTPS://Example.com/a/") == "example.com/a"


def test_doi_duplicate_detected():
    idx = ProcessedIndex(doi={"10.1/x"})
    assert idx.duplicate_reason(CandidateKey(doi="10.1/x")) == "duplicate_doi:10.1/x"


def test_pmid_pmcid_trial_url_hash_title_each_detected():
    idx = ProcessedIndex(
        pmid={"111"}, pmcid={"PMC222"}, trial_id={"NCT01234567"},
        canonical_url={"example.com/a"}, checksum={content_hash("t", "a")},
        normalized_title={"a title"},
    )
    assert "duplicate_pmid" in idx.duplicate_reason(CandidateKey(pmid="111"))
    assert "duplicate_pmcid" in idx.duplicate_reason(CandidateKey(pmcid="PMC222"))
    assert "duplicate_trial_id" in idx.duplicate_reason(CandidateKey(trial_id="NCT01234567"))
    assert "duplicate_canonical_url" in idx.duplicate_reason(CandidateKey(canonical_url="example.com/a"))
    assert "duplicate_content_hash" in idx.duplicate_reason(CandidateKey(checksum=content_hash("t", "a")))
    assert "duplicate_normalized_title" in idx.duplicate_reason(CandidateKey(normalized_title="a title"))


def test_non_duplicate_returns_none():
    idx = ProcessedIndex(doi={"10.1/x"})
    assert idx.duplicate_reason(CandidateKey(doi="10.1/y", pmid="999")) is None


def test_add_then_detected_within_same_run():
    idx = ProcessedIndex()
    key = CandidateKey.from_record({"title": "Some Study", "doi": "10.9/z"})
    assert idx.duplicate_reason(key) is None
    idx.add(key)
    assert idx.duplicate_reason(key) is not None


def test_from_checkpoint_and_merge_sources_json(state_paths):
    from uc_evidence_discovery.dedup import ProcessedIndex

    idx = ProcessedIndex.from_checkpoint({"processedSourceIdentifiers": {
        "doi": ["10.1/a"], "pubmedId": ["123"], "canonicalUrl": [], "checksum": [], "normalizedTitle": [],
    }})
    assert "10.1/a" in idx.doi
    assert "123" in idx.pmid

    idx2 = idx.merge_sources_json({"sources": [{"doi": "10.2/b", "title": "T2"}]})
    assert "10.2/b" in idx2.doi
