# Roadmap

## Foundation — implemented

- [x] Runnable packaged Python CLI and separate SQL models.
- [x] Synthetic fixture, explicit contract, and ignored local artifacts.
- [x] Raw snapshots, three warehouse layers, reconciliation, and run history.
- [x] Rerun, invalid-input, rollback, and integrity tests.
- [x] Local instructions and automated lint/test/sample-run workflow.

## Discovery — next

- [ ] Choose the audience and one valuable question.
- [ ] Compare accessible datasets and verify terms.
- [ ] Complete the project brief and decide the deployment budget.
- [ ] Define output grain, metric definitions, and acceptance criteria.

## First real vertical slice

- [ ] Ingest one real source with provenance and bounded retries if remote.
- [ ] Replace the demo contract and add source-specific fixtures.
- [ ] Build one useful output and validate it independently.
- [ ] Document and test backfill/replay behavior.

## Operations — driven by actual requirements

- [ ] Choose incremental loading, scheduling, and late-data handling.
- [ ] Measure and test freshness, failures, runtime, and operating cost.
- [ ] Add deployment infrastructure and external secret management if needed.
- [ ] Publish a reproducible demo and portfolio case study.
