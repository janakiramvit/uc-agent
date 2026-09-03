"""Schema-compatibility gate & Supabase migration pipeline (Prompt v1.0.0).

Package layout:
    config      - versions, paths, the input-file registry
    enums       - canonical enum vocabulary + per-input crosswalk (single source of truth)
    db          - psycopg3 connection + reversible-migration runner (DB I/O only)
    schema_infer- independent per-input schema inference -> schema/inferred/*.json
    adapters/   - one validated adapter per input format -> in-memory staging records
    validate    - pure validation over staging records (+ thin DB writer)
    reconcile   - field-by-field workbook<->JSON reconciliation (+ redacted report)
    promote     - staging -> canonical (gated; DB I/O); NOT run without --confirm-promote
    gate        - the full pre-production checklist
    ingest      - CLI orchestrator

Hard rules enforced here (see db/PLAN-v1.0.0.md):
    * missing clinical / applicability / evidence-strength / licensing / review values
      stay None - never inferred, never defaulted;
    * material reconciliation mismatch -> quarantine + report, never silent normalization;
    * nothing writes to canonical evidence tables without an approved promotion.
"""

__version__ = "1.0.0"
