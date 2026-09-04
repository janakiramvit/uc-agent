# Checkpoint schema migration: v1.0.0 → v1.1.0

**Status:** additive, fully backward compatible. `checkpoint.schema.json` (v1.0.0) is left in
place unmodified. The new file `checkpoint.schema-v1.1.0.json` is a **superset**: every
document that validates against v1.0.0 also validates against v1.1.0, unchanged.

## Why

The daily automated runner (`automation/uc_evidence_discovery/`) needs to record a few fields
the v1.0.0 schema had no room for, and to dedupe on PMCID / ClinicalTrials.gov NCT identifiers
in addition to DOI / PMID / URL / title / content-hash. Rather than edit the existing schema in
place (which the operating rules for this package forbid — "do not silently modify the existing
schema"), this is a new, versioned file.

## What changed

- `processedSourceIdentifiers` gains two **optional** array properties: `pmcid`, `trialId`.
  Neither is in `required`; `additionalProperties: false` is retained, so a v1.0.0 document
  (which lacks both) still validates.
- The root object gains these **optional** properties (`additionalProperties: false` retained
  at the root — this is the only reason a new top-level key ever needs a schema bump):
  `duplicateRecords`, `promptVersion`, `workflowRunUrl`, `triggeringCommit`, `sourceDataCutoff`,
  `completedTopics`, `pendingTopics`, `limitConsumption`, `lockInfo`, `schemaMigratedFrom`,
  `accessAndLicensingStatus`, `promptVsCheckpointDifference`.
- `schemaVersion` remains an unconstrained string. The runner writes
  `"uc-evidence-expansion-1.1.0"` and, when migrating a v1.0.0 document, also sets
  `schemaMigratedFrom` to the prior value. This is purely informational — no old value is
  rejected.
- The **known-good filename is unchanged**: `state/checkpoint.json.known-good` (the real
  on-disk name). No second known-good filename is introduced by this migration.

## What did NOT change

- `required` at the root is identical to v1.0.0.
- No existing property's `type` narrowed.
- No existing enum value removed.
- `counters`, `completedSearches[].required`, `rejectedRecords[].required` unchanged.

## Backward-compatibility evidence

`automation/tests/test_checkpoint.py` loads the real, currently-committed
`knowledge/uc-evidence-expansion/state/checkpoint.json` and
`state/checkpoint.json.known-good` and asserts both validate against **both**
`checkpoint.schema.json` and `checkpoint.schema-v1.1.0.json` with zero errors.

## Runner behaviour

The runner always validates against v1.1.0. On a successful load of a v1.0.0-tagged document
it upgrades `schemaVersion` to `"uc-evidence-expansion-1.1.0"` on the next atomic write (with
`schemaMigratedFrom` recorded) — non-destructive, and reversible by simply reading the field
back out, since no v1.0.0 data is dropped or reshaped.
