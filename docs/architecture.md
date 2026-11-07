# Architecture and guarantees

## Scope

This scaffold implements a single-process, complete-snapshot batch pipeline over a small local CSV. Python handles boundaries and validation. SQL handles the analytical model. DuckDB supplies a local warehouse without a server.

The full input is read into memory. There is no streaming, parallel ingestion, distributed processing, scheduler, cloud deployment, or incremental watermark yet. These are design decisions to revisit after choosing a real source and workload.

## Data flow

1. Read the source once into bytes; validate its UTF-8 CSV structure and contract.
2. Reject missing fields, duplicate IDs, invalid timestamps, negative/noninteger amounts, overflow, and empty snapshots. The existing warehouse remains unchanged.
3. Save the accepted bytes under their SHA-256 hash. An existing file is verified before reuse.
4. In one database transaction, rebuild bronze, cast timestamps and integers in silver, and aggregate gold by UTC date and normalized category.
5. Reconcile source, silver, and gold row counts. Insert successful-run metadata and commit.
6. On a database or reconciliation error, roll back all table replacements. The CLI exits nonzero and emits a JSON failure message.

The raw snapshot is the exact source. Bronze stores trimmed fields with normalized timestamp strings, so it is not a byte-preserving copy.

## Semantics

- **Idempotency:** rerunning an identical snapshot produces identical silver/gold data. Successful-run audit history grows intentionally.
- **Replacement:** each accepted file is a complete snapshot. Rows absent from a later input disappear. Never point this adapter at an incremental-only feed.
- **Time:** inputs must include a timezone. Silver uses TIMESTAMPTZ, and gold dates use a UTC database session.
- **Amounts:** sample values are nonnegative signed-64-bit integers in cents. Gold sums use DuckDB's wider aggregate type. Actual business currency semantics remain undecided.
- **Uniqueness:** duplicate event IDs fail the batch; no ambiguous winner is selected.
- **Recovery:** invalid inputs and database transaction failures preserve the last committed warehouse.

## Boundaries and limits

- Filesystem snapshots and the database do not share a transaction. A failed database run may leave an unused raw snapshot; retain it for diagnosis.
- An interrupted raw-file write can leave an incomplete snapshot. A rerun rejects it by hash; follow the runbook to move the damaged file aside.
- One writer at a time. Overlapping runs and cloud/object-store locking are outside this scaffold.
- Successful runs are persisted in `ops.pipeline_runs`; failed attempts are logged to stderr. Durable central logging and alerts are future work.
- The adapter supports contract version 1. It deliberately fails if contract semantics change without corresponding code and tests.
- The sample demonstrates technical behavior, not real-world scale, a service-level agreement, regulatory controls, or business impact.

## Why this stack

Python, SQL, DuckDB, and uv make the entire path reproducible on a laptop and in CI. Additional systems should solve a requirement we can explain in a project interview.

Revisit orchestration when dependencies, scheduling, and retries become meaningful. Revisit storage and compute when data size, concurrency, freshness, or deployment requirements exceed this local model. Record the evidence in a [decision record](decisions/0001-local-first.md).
