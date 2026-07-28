---
id: SC-REL-023
title: StoneCharts 0.0.0.4 Bubble Performance Baseline Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4
requirements: [REQ-CHART-003, REQ-PERF-001]
evidence: [BENCH-BUBBLE-BASELINE, BENCH-RENDER-BASELINE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-28"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# Bubble Performance Baseline Review

## Scope

`GATE-S12`'s third acceptance criterion requires bubble's benchmark results to be
reviewed as a baseline, not just recorded. `bubble` was added as a sixth variant to
`libs/python/benchmark.py` and `libs/go/cmd/benchmark/main.go` during
`REQ-CHART-003`'s implementation, generating genuine point-model data - positional
`[x,y,z]` triples with `z` spanning `[1, 5000]` - so the recorded numbers exercise
the size-scale (global z-domain reduction + the pinned radius formula), not just the
already-qualified linear x-scale scatter proved.

## Commands run

- `python libs/python/benchmark.py`
- `go run ./cmd/benchmark`

Both cover the full approved workload matrix (Small 1x12, Business 8x100, Dense
20x1,000, Stress 20x5,000; SVG and HTML output modes; seed 42) for all six variants,
per `docs/quality/benchmark-spec.md` and `docs/contracts/performance-budgets.md`. Both
runs were executed cleanly (no concurrent background CPU load), matching the
discipline established in `SC-REL-015`/`SC-REL-019` after an earlier contaminated run
was discarded during scatter's review.

## Bubble results (this run)

Python (`p50` render time, ms):

| Profile | bubble SVG | bubble HTML | scatter SVG (reference) |
|---|---:|---:|---:|
| Small (1x12) | 0.142 | 0.359 | 0.126 |
| Business (8x100) | 5.177 | 7.461 | 3.697 |
| Dense (20x1,000) | 121.298 | 175.907 | 90.136 |
| Stress (20x5,000) | 608.367 | 894.227 | 477.463 |

Go (`p50` render time, ms):

| Profile | bubble SVG | bubble HTML | scatter SVG (reference) |
|---|---:|---:|---:|
| Small (1x12) | 0.000 | 0.538 | 0.000 |
| Business (8x100) | 7.990 | 13.396 | 5.573 |
| Dense (20x1,000) | 104.374 | 249.002 | 91.104 |
| Stress (20x5,000) | 602.797 | 970.451 | 393.079 |

Bubble runs measurably higher than scatter at Business/Dense/Stress in both
languages - expected and explained by two real, disclosed costs, not a regression:

1. **The global z-domain reduction** is an extra O(n) pass over every point of every
   series before any mark is drawn (scatter has no equivalent domain reduction beyond
   the frame's own x/y `nice_ticks`, which bubble also pays).
2. **The size-scale itself** (`clamp01` + `sqrt` + arithmetic) runs once per point, on
   top of scatter's plain `xpix`/`ypix` lookup.

Bubble's Go allocation is also visibly higher than scatter's at Dense/Stress (e.g.
Dense: 579MB vs scatter's 448MB) - the `[3]float64` per-point z-domain bookkeeping and
the extra `data-z` string formatting per mark account for this; it is proportional to
point count, not superlinear (no evidence of an accidental O(n²) path in either the
domain reduction or the size-scale).

Bubble's HTML mode carries the same disclosed long-format-table cost scatter's review
(`SC-REL-019`) already identified, now with a third `Z` column: at Stress, bubble's
HTML allocation (5.7GB in Go) is the highest of any variant measured to date, because
the accessible table emits one row per point (100,000 rows at 20 series x 5,000
points) with three data cells each, not one row per category.

## Reviewed result

Bubble's render time and memory scale proportionally with workload size in both
languages, with no unexplained outlier - the measured overhead versus scatter is
fully accounted for by the two new computations (global z-domain reduction and the
size-scale) plus the same long-format-table cost already disclosed for scatter. There
is no evidence of a performance defect specific to bubble.

As with `SC-REL-006`/`SC-REL-015`/`SC-REL-019`, these results establish a repeatable
comparative baseline; they do not themselves set an absolute release-blocking
threshold, which remains a separate governed decision under
`docs/contracts/performance-budgets.md`.

## Result

`BENCH-RENDER-BASELINE` is reaffirmed as covering bubble for 0.0.0.4. No unexplained
performance gap or regression was found; the real, higher cost bubble carries over
scatter is disclosed above with its concrete cause, not hidden.
