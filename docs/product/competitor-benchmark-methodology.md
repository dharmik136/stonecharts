---
id: SC-PROD-005
title: StoneCharts Competitor Benchmark Methodology
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# Competitor Benchmark Methodology

## Purpose

[`DEC-017`](../project/decisions.md)'s brief lists "create a reproducible competitor
benchmark methodology" as immediate work. [`SC-PROD-003`](visual-integrity-strategy.md)
requires that "any public competitor comparison must distinguish measured facts from
hypotheses" and that performance, security, and cost-savings claims "are not sales
claims until they are measured against reproducible competitor configurations."

This document defines **how** a comparison is run so it is reproducible and
falsifiable. It intentionally contains no comparison results, cost-savings
percentages, or performance numbers. Publishing an invented number here would violate
the constraint this document exists to enforce.

## Named comparison targets

Per the DEC-017 brief's competitive assumptions, the initial comparison set is:

- **Highcharts Export Server** — the official Node/Puppeteer headless-Chromium
  rendering path for PNG, JPG, PDF, and SVG.
- **QuickChart** — a hosted API that renders Chart.js configurations to images.
- **Vega / Vega-Lite** — server-side static rendering paths.

Adding a target requires the same rigor as adding a chart type: name it here first.

## Comparison axes

Each axis states what is measured and the method used to measure it. No axis may be
scored from vendor marketing copy alone.

| Axis | What is measured | Method |
|---|---|---|
| Operational footprint | Cold-start time, resident memory, and process/container requirements for an equivalent server-side render | Run each system's documented native or server rendering path against an equivalent chart-spec set (translated from StoneCharts' own benchmark variants), on the same host, with no concurrent load, per the discipline in [benchmark-spec.md](../quality/benchmark-spec.md) |
| Cross-invocation consistency | Whether the same logical chart definition produces identical output across two independent invocations of the target's own supported paths | Render the same spec twice through the target's documented paths and diff the output; report pass/fail, not an invented percentage |
| Data egress requirements | Whether the rendering path requires sending underlying data to a third-party or hosted endpoint | Static fact-check against the target's own published architecture documentation, cited with a source link and access date |
| Dependency and exposure surface | The runtime's direct dependency list and any CVEs published against the exact pinned versions used | Report the actual dependency list and linked CVE records; do not summarize as a security "grade" |
| Release provenance and evidence | Whether the target publishes reproducible SBOMs, build provenance, and conformance evidence comparable to StoneCharts' own release evidence packs | Check the target's public release artifacts against the checklist structure used in `docs/releases/0.0.0.N/evidence/` |

## Fair-comparison rules

- Compare like-for-like: StoneCharts' native server-side rendering against each
  target's native or server-side rendering path, never against a target's
  client-side interactive JavaScript as if it served the same job.
- Every reported number MUST cite the exact target version, the exact command or
  configuration used, the host specification, and the measurement date.
- Do not publish a number without publishing or linking the raw measurement
  artifact that produced it.
- Distinguish "documented capability" (found in the vendor's own documentation) from
  "measured behavior" (something run and captured directly) in every row of a
  comparison table.
- No comparison table may state a percentage or multiplier that this methodology's
  own measurement step did not produce.

## Output format

A completed benchmark run against one target produces:

- A stable evidence ID (`BENCH-COMPETITOR-<TARGET>-<YYYY-MM-DD>`) registered in
  [`docs/quality/evidence-registry.yaml`](../quality/evidence-registry.yaml), following
  the same pattern as `BENCH-SCATTER-BASELINE` and `BENCH-BUBBLE-BASELINE`.
- A results document under `docs/quality/` or the relevant release's evidence
  directory, linking the raw measurement artifacts and the exact reproduction
  command.

## Status

No competitor benchmark has been executed under this methodology yet. This document
defines the method only; it is not itself a benchmark result and MUST NOT be cited as
one.
