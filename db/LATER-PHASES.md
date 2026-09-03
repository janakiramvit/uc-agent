# Later phases (NOT built in v1.0.0)

## Phase 2 — incremental evidence import
`knowledge/uc-evidence-expansion/` — see `PHASE-2-INPUT.md`.

## Phase 3+ — object storage & embeddings

Out of scope for the schema-compatibility gate. Recorded here so they are not
accidentally pulled into v1.0.0.

### Supabase Storage for source documents
- `knowledge/ibd-research-review/sources/**` (PubMed/PMC XML, ECCO/ESPEN HTML, ESPEN PDF)
  and `extracted-text/**` would move to a Storage bucket, referenced by
  `canonical.source` (a `storage_path` column, added by a future migration).
- Access via signed URLs from the server only; the bucket is private; `anon` has no read.

### pgvector embeddings for retrieval
- A `canonical.claim_embedding(claim_id, model, dim, embedding vector)` table + an
  `ivfflat`/`hnsw` index, populated after promotion.
- The app's `agent_core/vector_retrieval.py` already computes OpenAI
  `text-embedding-3-small` vectors in-process and is **left untouched** in v1.0.0. A future
  phase would let it read/write the pgvector table instead of re-embedding per process.

Neither is implemented. No migration, table, bucket, or dependency for these exists yet.
