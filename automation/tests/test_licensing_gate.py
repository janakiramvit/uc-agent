from __future__ import annotations

from uc_evidence_discovery.licensing import licence_permits_archival, plan_archival


def test_unestablished_licence_prevents_archival():
    d = plan_archival({"license": "", "isOpenAccess": "N"})
    assert d.archival_status == "link_only"
    assert d.redistribution_status == "not_established"
    assert d.stored is False


def test_subscription_required_prevents_archival():
    d = plan_archival({"license": "All rights reserved", "isOpenAccess": "N"})
    assert d.redistribution_status == "not_established"
    assert d.stored is False


def test_open_licence_detected_but_runner_still_never_stores_a_file():
    d = plan_archival({"license": "CC BY 4.0", "isOpenAccess": "Y"})
    assert d.redistribution_status == "permitted_open_licence"
    assert d.archival_status == "link_only"   # this version never fetches a file
    assert d.stored is False


def test_licence_predicate_requires_both_open_access_flag_and_open_licence_text():
    assert licence_permits_archival("CC BY 4.0", "Y") is True
    assert licence_permits_archival("CC BY 4.0", "N") is False
    assert licence_permits_archival(None, "Y") is False
    assert licence_permits_archival("All rights reserved", "Y") is False
