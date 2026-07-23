---
id: SC-CON-017
title: StoneCharts Performance and Artifact-Size Budget Policy
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PERF-001, REQ-REL-001]
evidence: [BENCH-RENDER-BASELINE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Performance and Artifact-Size Budget Policy

## Policy

StoneCharts 0.0.0.1 does not promise fixed absolute latency or memory thresholds yet.
Release qualification is instead based on a reproducible benchmark baseline across the
approved workloads and a documented regression budget derived from observed variance.

## Required workload set

- Small: 1 series x 12 categories
- Business: 8 series x 100 categories
- Dense: 20 series x 1,000 categories
- Stress: 20 series x 5,000 categories

## Required measurements

- Cold and warm render time
- Peak memory where supported
- Output byte size
- DOM element count where applicable
- Artifact-size evidence for shipped packages and release materials

## Release rule

Release can be blocked by a regression only when the measured result departs from the
approved baseline beyond the recorded variance policy for that workload and environment.
The approved release manifest must name the affected workload, measured change, reason,
and approval.

## Non-claim

This policy does not invent a static percentage budget before the baseline exists. It
also does not turn benchmark numbers into a universal promise outside the recorded
environment and workload set.

