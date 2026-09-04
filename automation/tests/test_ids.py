from __future__ import annotations

import json

from uc_evidence_discovery import config
from uc_evidence_discovery.ids import Allocator, scan_existing


def test_floor_when_nothing_recorded_yet(state_paths):
    src, clm = scan_existing(state_paths, {})
    alloc = Allocator(src, clm)
    assert alloc.peek_source_id == "SRC-033"   # floor 32 + 1
    assert alloc.peek_claim_id == "CLM-115"    # floor 114 + 1


def test_registry_ahead_of_prompt_hardcoded_ids_wins(state_paths):
    state_paths.sources_path.write_text(json.dumps({
        "sources": [{"sourceId": "SRC-040"}, {"sourceId": "SRC-041"}]
    }), encoding="utf-8")
    state_paths.claims_path.write_text(json.dumps({
        "claims": [{"claimId": "CLM-150"}]
    }), encoding="utf-8")
    alloc = Allocator.from_state(state_paths, {})
    # NOT SRC-035/CLM-128 (the prompt's hard-coded values) -- registries are ahead
    assert alloc.source_id() == "SRC-042"
    assert alloc.claim_id() == "CLM-151"
    assert config.PROMPT_EXPECTATIONS["firstNewSourceId"] == "SRC-035"
    assert config.PROMPT_EXPECTATIONS["firstNewClaimId"] == "CLM-128"


def test_ids_never_collide_within_a_run():
    alloc = Allocator(used_src=set(), used_clm=set())
    seen_src = {alloc.source_id() for _ in range(20)}
    seen_clm = {alloc.claim_id() for _ in range(20)}
    assert len(seen_src) == 20
    assert len(seen_clm) == 20


def test_checkpoint_accepted_records_also_count_toward_next_id(state_paths):
    checkpoint = {"acceptedRecords": [{"sourceId": "SRC-060"}]}
    src, clm = scan_existing(state_paths, checkpoint)
    assert 60 in src
    assert Allocator(src, clm).source_id() == "SRC-061"
