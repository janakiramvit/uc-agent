from __future__ import annotations

from uc_evidence_discovery.apis import clinicaltrials, europepmc


def test_europepmc_norm_maps_core_fields():
    rec = europepmc._norm({
        "id": "36822736", "source": "MED", "pmid": "36822736",
        "doi": "10.1053/j.gastro.2022.12.007",
        "title": "AGA Clinical Practice Guideline on the Role of Biomarkers.",
        "authorString": "Singh S, et al.", "journalTitle": "Gastroenterology",
        "pubYear": "2023", "firstPublicationDate": "2023-03-01",
        "abstractText": "In patients with UC in symptomatic remission...",
        "isOpenAccess": "N", "license": "", "pubType": "guideline",
    })
    assert rec["pmid"] == "36822736"
    assert rec["doi"] == "10.1053/j.gastro.2022.12.007"
    assert rec["canonicalUrl"] == "https://doi.org/10.1053/j.gastro.2022.12.007"
    assert rec["alternateUrl"].endswith("/36822736/")
    assert "In patients with UC" in rec["abstractText"]
    assert rec["title"].endswith("Biomarkers")  # trailing period stripped


def test_europepmc_norm_falls_back_to_europepmc_url_without_doi():
    rec = europepmc._norm({"id": "999", "source": "MED", "title": "No DOI study"})
    assert rec["canonicalUrl"] == "https://europepmc.org/abstract/MED/999"


def test_clinicaltrials_norm_maps_registry_fields():
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT01234567", "officialTitle": "A UC Trial"},
            "statusModule": {"overallStatus": "COMPLETED", "completionDateStruct": {"date": "2024-06-01"}},
            "descriptionModule": {"briefSummary": "A trial of a UC biologic."},
            "designModule": {"studyType": "INTERVENTIONAL"},
            "conditionsModule": {"conditions": ["Ulcerative Colitis"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Example Sponsor"}},
        }
    }
    rec = clinicaltrials._norm(study)
    assert rec["nctId"] == "NCT01234567"
    assert rec["canonicalUrl"] == "https://clinicaltrials.gov/study/NCT01234567"
    assert rec["conditions"] == ["Ulcerative Colitis"]
    assert rec["isOpenAccess"] == "Y"
    assert "UC biologic" in rec["abstractText"]
