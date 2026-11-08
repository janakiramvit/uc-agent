"""Input locations for the Phase-2 inventory. Everything is read-only; nothing here is written to."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PRODUCTION_JSON = REPO / "apps" / "ibd-uc-rag-agent-web" / "api" / "data" / "ibd-prototype-evidence.json"
BASELINE_REGISTER_XLSX = REPO / "knowledge" / "ibd-research-review" / "ibd-evidence-review-final-remediation.xlsx"
EXPANSION_DIR = REPO / "knowledge" / "uc-evidence-expansion"
EXPANSION_CLAIMS = EXPANSION_DIR / "candidate-claims.json"
EXPANSION_SOURCES = EXPANSION_DIR / "sources.json"
DAILY_ARTIFACT_DIR = REPO / "automation" / "artifact"
QUESTION_TREE = REPO / "uc_39_question_tree.json"
TOPIC_QUESTION_MAP = Path(__file__).resolve().parent / "config" / "topic_question_map.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Dataset codes (the manifest's ``originating dataset`` values), in dedupe-retention priority.
DS_PRODUCTION = "prototype-v1"          # the 49 claims served by production
DS_BASELINE = "baseline-register"       # authoritative 61-claim register (not promoted)
DS_EXPANSION = "uc-evidence-expansion"  # Phase-2 candidate claims
DS_DAILY = "daily-discovery"            # claims saved by the daily discovery runs
DATASET_PRIORITY = [DS_PRODUCTION, DS_BASELINE, DS_EXPANSION, DS_DAILY]
