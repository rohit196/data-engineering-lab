# 0001 — Start with a local batch pipeline

Status: accepted for the scaffold; revisit after project discovery.

## Context

The real use case and source are undecided. The foundation must run without paid infrastructure and be straightforward to inspect and discuss.

## Decision

Use Python for ingestion/validation, SQL for transformations, DuckDB for local storage, and uv for a locked environment. Demonstrate a full-snapshot batch load with explicit contracts and failure recovery.

## Consequences

The pipeline is quick to reproduce and has a small operational footprint. It is limited to a small, in-memory, single-writer workflow. Cloud infrastructure, orchestration, incremental loading, and streaming will be selected only after source volume, freshness, and consumer requirements are known.

This record is not a claim that this stack suits every future project.
