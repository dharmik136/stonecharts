---
id: SC-REL-019
title: StoneCharts 0.0.0.3 Scatter Performance Baseline Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.3
requirements: [REQ-CHART-002, REQ-PERF-001]
evidence: [BENCH-SCATTER-BASELINE, BENCH-RENDER-BASELINE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-27"
review_due: "2026-08-27"
supersedes: null
superseded_by: null
---

# Scatter Performance Baseline Review

## Scope

`GATE-S9`'s third acceptance criterion requires scatter's benchmark results to be
reviewed as a baseline, not just recorded. `scatter` was added as a fifth variant to
`libs/python/benchmark.py` and `libs/go/cmd/benchmark/main.go` during `REQ-CHART-002`'s
implementation, alongside `line`, `grouped-column`, `stacked-column`, and `bar`.
Unlike bar's benchmark data (a plain `number[]` reused unchanged), scatter's benchmark
spec generates genuine point-model data - positional `[x,y]` pairs - so the recorded
numbers exercise the new linear x-scale and point-model normalization path, not just
the bare-number fast path.

## Commands run

- `python libs/python/benchmark.py`
- `go run ./cmd/benchmark`

Both cover the full approved workload matrix (Small 1x12, Business 8x100, Dense
20x1,000, Stress 20x5,000; SVG and HTML output modes; seed 42) for all five variants,
per `docs/quality/benchmark-spec.md` and `docs/contracts/performance-budgets.md`. Both
runs were re-executed a second time after an initial run was contaminated by
concurrent background CPU load (other qualification tasks running in parallel); the
numbers below are from the clean, uncontended re-run.

## Scatter results (this run)

Python (`p50` render time, ms):

| Profile | scatter SVG | scatter HTML | line SVG (reference) |
|---|---:|---:|---:|
| Small (1x12) | 0.172 | 0.610 | 0.196 |
| Business (8x100) | 6.118 | 10.789 | 7.322 |
| Dense (20x1,000) | 160.012 | 239.647 | 175.142 |
| Stress (20x5,000) | 767.107 | 1121.039 | 930.159 |

Go (`p50` render time, ms):

| Profile | scatter SVG | scatter HTML | line SVG (reference) |
|---|---:|---:|---:|
| Small (1x12) | 0.000 | 0.505 | 0.000 |
| Business (8x100) | 9.074 | 18.416 | 10.034 |
| Dense (20x1,000) | 161.810 | 257.142 | 194.673 |
| Stress (20x5,000) | 678.564 | 1146.213 | 782.564 |

(Small-profile Go timings round to 0.000ms below the sampler's resolution at that
workload size; this matches line/column/bar's existing behavior at the same profile
in `SC-REL-006`/`SC-REL-015`, not a scatter-specific measurement artifact.)

Scatter's DOM element count and output byte size run consistently *lower* than the
other variants at every profile (e.g. Dense: scatter 20,106 elements / 4,574,586B vs.
line 21,120 elements / 4,882,788B in Python) - expected, since scatter emits one mark
per point with no connecting `<path>` and no per-point category label loop, unlike
line's path-plus-markers or column/bar's rect-plus-band-chrome.

Scatter's HTML mode allocation is visibly higher than SVG-only variants at Dense/Stress
in Go (e.g. Stress: 4.35GB vs. line's 3.04GB) because the accessible data table is
long-format (one row per point, §5.4b-DT) rather than one row per category - at
20 series x 5,000 points, that is 100,000 table rows instead of 5,000. This is a real,
disclosed cost of the lossless point-model table shape, not a bug: coercing scatter's
`(x, y)` pairs into a category-shaped table would violate the accessibility contract
(`SC-REL-018`) to save memory. It is within the same order of magnitude as the other
variants' HTML overhead and does not represent a regression against any existing
guarantee - no release gate imposes an absolute memory budget, only a repeatable
comparative baseline (`docs/contracts/performance-budgets.md`).

## Reviewed result

Scatter's SVG render time, memory, and output-size profile is at or below
line/column/bar's at every workload size, in both languages - consistent with scatter
being the cheapest mark type in the family (no path, no band layout, no stacking).
Its HTML mode carries a real, understood, and disclosed extra cost from the
long-format accessible table, proportional to point count rather than category count.
There is no unexplained outlier and no evidence of an accidental O(n²) path in the
point-model normalization or the linear x-scale.

As with `SC-REL-006`/`SC-REL-015`, these results establish a repeatable comparative
baseline; they do not themselves set an absolute release-blocking threshold, which
remains a separate governed decision under `docs/contracts/performance-budgets.md`.

## Result

`BENCH-RENDER-BASELINE` is reaffirmed as covering scatter for 0.0.0.3. No unexplained
performance gap or regression was found for scatter relative to the already-qualified
0.0.0.1/0.0.0.2 chart types; its one real cost (long-format HTML table memory at high
point counts) is disclosed above, not hidden.
