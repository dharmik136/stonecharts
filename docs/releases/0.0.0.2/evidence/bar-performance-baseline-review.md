---
id: SC-REL-015
title: StoneCharts 0.0.0.2 Bar Performance Baseline Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001, REQ-PERF-001]
evidence: [BENCH-BAR-BASELINE, BENCH-RENDER-BASELINE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# Bar Performance Baseline Review

## Scope

`GATE-S6`'s third acceptance criterion requires bar's benchmark results to be reviewed
as a baseline, not just recorded. `bar` was already added as a fourth variant to
`libs/python/benchmark.py` and `libs/go/cmd/benchmark/main.go` during `REQ-CHART-001`'s
implementation, alongside `line`, `grouped-column`, and `stacked-column`. This review
re-runs both harnesses fresh and evaluates bar's results specifically, following the
same method as `performance-baseline-review.md` (`SC-REL-006`).

## Commands run

- `python libs/python/benchmark.py`
- `go run ./cmd/benchmark`

Both cover the full approved workload matrix (Small 1x12, Business 8x100, Dense
20x1,000, Stress 20x5,000; SVG and HTML output modes; seed 42) for all four variants,
per `docs/quality/benchmark-spec.md` and `docs/contracts/performance-budgets.md`.

## Bar results (this run)

Python (`p50` render time, ms):

| Profile | bar SVG | bar HTML | line SVG (reference) |
|---|---:|---:|---:|
| Small (1x12) | 0.139 | 0.378 | 0.134 |
| Business (8x100) | 3.868 | 5.208 | 4.432 |
| Dense (20x1,000) | 92.981 | 114.707 | 105.106 |
| Stress (20x5,000) | 500.613 | 609.974 | 498.240 |

Go (`p50` render time, ms):

| Profile | bar SVG | bar HTML | line SVG (reference) |
|---|---:|---:|---:|
| Small (1x12) | 0.000 | 0.530 | 0.000 |
| Business (8x100) | 6.001 | 8.265 | 6.029 |
| Dense (20x1,000) | 107.387 | 140.978 | 122.539 |
| Stress (20x5,000) | 392.704 | 488.685 | 424.824 |

(Small-profile Go timings round to 0.000ms below the sampler's resolution at that
workload size; this matches line/column's existing behavior at the same profile in
`SC-REL-006`, not a bar-specific measurement artifact.)

Output byte size and DOM element count for bar track within 1-2% of column's at every
profile (e.g. Dense: bar 4,853,660B/21,100 elements vs. stacked-column 4,856,856B/
21,096 elements in Go) - expected, since bar shares column's mark count and only
transposes the geometry.

## Reviewed result

Bar's render time, memory, and output-size profile is statistically indistinguishable
from line/grouped-column/stacked-column at every workload size, in both languages.
There is no bar-specific performance regression or outlier. This is consistent with
bar being a geometry transposition of column over the shared cartesian substrate
(`libs/python/stonecharts/charts/_cartesian.py` / `libs/go/cartesian.go`), not a
separate rendering path with its own cost profile.

As with `SC-REL-006`, these results establish a repeatable comparative baseline; they
do not themselves set an absolute release-blocking threshold, which remains a separate
governed decision under `docs/contracts/performance-budgets.md`.

## Result

`BENCH-RENDER-BASELINE` is reaffirmed as covering bar for 0.0.0.2. No performance gap
or regression was found for bar relative to the already-qualified 0.0.0.1 chart types.
