"""Read every evidence dataset we already possess into one normalized record shape.

Read-only: no network, no DB, no research. A missing optional input is reported as
``available=False`` in the dataset summary rather than silently skipped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from phase2 import paths


@dataclass
class Record:
    dataset: str
    claim_id: str
    source_id: str | None
    source_title: str | None = None
    source_url: str | None = None
    claim_text: str | None = None
    excerpt: str | None = None
    locator: str | None = None
    publication_date: str | None = None
    publication_date_precision: str | None = None   # year | month | day | None
    uc_applicability: list[str] = field(default_factory=list)
    disease_context: list[str] = field(default_factory=list)
    evidence_status: str | None = None      # dataset-native evidence/eligibility status
    review_status: str | None = None
    verification_status: str | None = None
    declared_conflict_note: str | None = None
    limitations: str | None = None
    native_question_ids: list[str] = field(default_factory=list)
    topic: str | None = None
    source_resolved: bool = True
    in_production: bool = False
    # filled later
    mapped_question_ids: list[str] = field(default_factory=list)
    mapping_basis: str | None = None


@dataclass
class DatasetSummary:
    dataset: str
    available: bool
    files: list[str]
    claim_rows: int = 0
    source_rows: int = 0
    notes: list[str] = field(default_factory=list)


def _rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(paths.REPO))
    except ValueError:
        return str(path)


def split_multi(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        parts = value
    else:
        parts = str(value).replace(",", ";").split(";")
    return [p.strip() for p in parts if p and str(p).strip() and str(p).strip().lower() != "none"]


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s and s.lower() != "none" else None


def _date_precision(value: str | None) -> str | None:
    if not value:
        return None
    return {4: "year", 7: "month", 10: "day"}.get(len(value))


def load_production(path: Path = paths.PRODUCTION_JSON) -> tuple[list[Record], DatasetSummary]:
    if not path.exists():
        return [], DatasetSummary(paths.DS_PRODUCTION, False, [_rel(path)], notes=["file missing"])
    data = json.loads(path.read_text())
    sources = {s["sourceId"]: s for s in data["sources"]}
    recs = []
    for c in data["claims"]:
        s = sources.get(c.get("sourceId"))
        year = _clean(s.get("publicationYear")) if s else None
        recs.append(Record(
            dataset=paths.DS_PRODUCTION, claim_id=c["claimId"], source_id=c.get("sourceId"),
            source_title=c.get("sourceTitle"), source_url=_clean(c.get("sourceUrl")),
            claim_text=_clean(c.get("claimText")), excerpt=_clean(c.get("supportingExcerpt")),
            locator=_clean(c.get("exactLocator")), publication_date=year,
            publication_date_precision=_date_precision(year),
            uc_applicability=split_multi(c.get("conditionApplicability")),
            disease_context=split_multi(c.get("diseaseContext")),
            evidence_status=_clean(c.get("prototypeEligibilityStatus")),
            review_status=_clean(s.get("reviewStatus")) if s else None,
            topic=_clean(c.get("topic")), source_resolved=s is not None, in_production=True,
            limitations=_clean(c.get("limitations")),
        ))
    return recs, DatasetSummary(paths.DS_PRODUCTION, True, [_rel(path)], len(recs), len(sources))


def _read_xlsx_table(path: Path, sheet: str, header_row_idx: int = 3) -> list[dict[str, Any]]:
    import openpyxl  # optional dependency; absence is reported by the caller

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(wb[sheet].iter_rows(values_only=True))
    finally:
        wb.close()
    header = [str(c).strip() if c not in (None, "") else f"col{i}" for i, c in enumerate(rows[header_row_idx])]
    return [dict(zip(header, r)) for r in rows[header_row_idx + 1:] if any(v not in (None, "") for v in r)]


def load_baseline(path: Path = paths.BASELINE_REGISTER_XLSX) -> tuple[list[Record], DatasetSummary]:
    if not path.exists():
        return [], DatasetSummary(paths.DS_BASELINE, False, [_rel(path)], notes=["file missing"])
    try:
        claims = _read_xlsx_table(path, "Claims")
        sources = {r["Source ID"]: r for r in _read_xlsx_table(path, "Sources")}
    except ImportError:
        return [], DatasetSummary(paths.DS_BASELINE, False, [_rel(path)],
                                  notes=["openpyxl not installed; baseline register not read"])
    recs = []
    for c in claims:
        s = sources.get(c.get("Source ID"))
        year = _clean(s.get("Year")) if s else None
        recs.append(Record(
            dataset=paths.DS_BASELINE, claim_id=str(c["Claim ID"]).strip(), source_id=_clean(c.get("Source ID")),
            source_title=_clean(c.get("Source title")), source_url=_clean(c.get("Authoritative source URL")),
            claim_text=_clean(c.get("Final remediated claim")), excerpt=_clean(c.get("Preserved supporting excerpt")),
            locator=_clean(c.get("Precise locator")), publication_date=year,
            publication_date_precision=_date_precision(year),
            uc_applicability=split_multi(c.get("Condition applicability")),
            disease_context=split_multi(c.get("Disease context")),
            evidence_status=_clean(c.get("Evidence status")), review_status=_clean(c.get("Review status")),
            verification_status=_clean(c.get("Verification status")), topic=_clean(c.get("Topic")),
            limitations=_clean(c.get("Limitations")),
            source_resolved=s is not None,
        ))
    notes = []
    unresolved = [c for c in claims if _clean(c.get("Final-QA eligibility")) == "unresolved_not_approval_ready"]
    if unresolved:
        notes.append(f"{len(unresolved)} claim(s) flagged unresolved_not_approval_ready by the register")
    return recs, DatasetSummary(paths.DS_BASELINE, True, [_rel(path)], len(recs), len(sources), notes)


def load_expansion(claims_path: Path = paths.EXPANSION_CLAIMS,
                   sources_path: Path = paths.EXPANSION_SOURCES) -> tuple[list[Record], DatasetSummary]:
    if not claims_path.exists() or not sources_path.exists():
        return [], DatasetSummary(paths.DS_EXPANSION, False, [_rel(claims_path), _rel(sources_path)],
                                  notes=["file missing"])
    claims = json.loads(claims_path.read_text())["claims"]
    sources = {s["sourceId"]: s for s in json.loads(sources_path.read_text())["sources"]}
    recs = []
    for c in claims:
        s = sources.get(c.get("sourceId"))
        date = _clean(s.get("publicationDate")) if s else None
        recs.append(Record(
            dataset=paths.DS_EXPANSION, claim_id=c["claimId"], source_id=c.get("sourceId"),
            source_title=_clean(s.get("title")) if s else None,
            source_url=(_clean(s.get("canonicalUrl")) or _clean(s.get("alternateUrl"))) if s else None,
            claim_text=_clean(c.get("normalizedClaim")), excerpt=_clean(c.get("exactSupportingExcerpt")),
            locator=_clean(c.get("exactLocator")), publication_date=date,
            publication_date_precision=_date_precision(date),
            uc_applicability=split_multi(c.get("conditionApplicability")),
            disease_context=split_multi(c.get("diseaseContext")),
            evidence_status=_clean(c.get("lifecycleState")) or _clean(c.get("evidenceStrength")),
            review_status=_clean(c.get("reviewStatus")),
            declared_conflict_note=_clean(c.get("conflictsWithExistingEvidence")),
            limitations=_clean(c.get("limitations")),
            native_question_ids=list(c.get("mappedPatientQuestionIds") or []),
            source_resolved=s is not None,
        ))
    unused = sorted(set(sources) - {r.source_id for r in recs})
    notes = [f"{len(sources)} source(s) in sources.json; sources with no candidate claim: "
             + (", ".join(unused) or "none")]
    return recs, DatasetSummary(paths.DS_EXPANSION, True, [_rel(claims_path), _rel(sources_path)],
                                len(recs), len(sources), notes)


def load_daily(manifest_path: Path = paths.DAILY_MANIFEST) -> tuple[list[Record], DatasetSummary]:
    """Daily-discovery runs persist only *redacted* run reports (no claim text/excerpts), so they can
    contribute counts but never claim records. Read from the committed per-run manifest (counts + sha256),
    which phase2.inputs regenerates from automation/artifact. Runs reporting extracted claims whose text we
    do not hold are surfaced as a note, never invented."""
    if not manifest_path.exists():
        return [], DatasetSummary(paths.DS_DAILY, False, [_rel(manifest_path)], notes=["manifest missing"])
    m = json.loads(manifest_path.read_text())
    t = m["totals"]
    notes = [f"{m['run_count']} redacted run report(s); statuses={m['by_status']}",
             f"claimsExtracted reported across runs={t['claimsExtracted']}; sourcesAccepted={t['sourcesAccepted']}; "
             f"zero-claim runs={m['zero_claim_runs']}",
             "run artifacts are redacted by design (no claim text); they cannot yield claim records"]
    if t["claimsExtracted"]:
        notes.append("WARNING: runs report extracted claims but no claim text is stored locally")
    return [], DatasetSummary(paths.DS_DAILY, True, [_rel(manifest_path)], 0, t["sourcesAccepted"], notes)


def load_all() -> tuple[list[Record], list[DatasetSummary]]:
    records: list[Record] = []
    summaries: list[DatasetSummary] = []
    for loader in (load_production, load_baseline, load_expansion, load_daily):
        recs, summ = loader()
        records.extend(recs)
        summaries.append(summ)
    return records, summaries
