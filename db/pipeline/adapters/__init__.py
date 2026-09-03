"""One validated adapter per input format.

Each adapter turns a single input file into a list of
:class:`~pipeline.adapters.base.StagingRecord` objects. Adapters do **no** DB I/O and
**no** cleaning of clinical values - they parse, split multi-value strings, attach
provenance, and stop. Validation, enum crosswalking, and quarantine happen later in
``pipeline.validate``.
"""

from pipeline.adapters.base import (  # noqa: F401
    AdapterResult,
    ClinicalFieldDefaultError,
    StagingRecord,
    apply_safe_default,
)
