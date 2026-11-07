# Project brief — decide together

Status: open. The synthetic events are only a technical demo.

## Problem and audience

- Who will use the output?
- What recurring decision or workflow should it improve?
- What can the user do after this project that they cannot do today?
- Which employer roles should this demonstrate readiness for?

## Source and permission

- Dataset/API name, owner, and access URL:
- Public terms, redistribution permission, rate limits, and attribution:
- Fields, keys, historical coverage, update cadence, and estimated size:
- Personal/sensitive data handling and retention:
- Known gaps, bias, missing values, duplicates, and late-arriving records:

## Smallest useful result

- One question the first version will answer:
- Exact metric definitions and grain:
- Consumer interface: query, dashboard, API, or export:
- Example acceptance scenario with an independently checkable result:

## Engineering targets

- Batch or streaming, with a reason:
- Freshness target and completion deadline:
- Historical backfill and incremental/replay strategy:
- Quality checks and expected response to failures:
- Runtime, budget, and deployment constraints:
- What will be measured, and against which baseline?

## Candidate directions

| Direction | Potential consumer | Engineering challenge to investigate |
| --- | --- | --- |
| Toronto mobility or service operations | Operations analyst | Time-series ingestion, geographic dimensions, freshness |
| Risk and anomaly monitoring | Risk analyst | Late records, explainable flags, quality controls |
| Reading and text analytics | Personal analytics user | API/file ingestion, text normalization, reusable data models |

These are prompts for discussion, not selected datasets or promised outcomes. Verify source availability and terms before choosing one.

## Definition of done

- [ ] A documented, accessible source and justified use case.
- [ ] A reproducible ingestion-to-output path with sample data.
- [ ] Tested contracts, reruns, and failure recovery.
- [ ] Measured correctness, freshness, runtime, and cost.
- [ ] An architecture diagram and documented tradeoffs.
- [ ] A demo and case study with verifiable results.
