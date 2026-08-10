---
id: SC-OPS-021
title: DEC-051 Property and Fuzz Test Expansion
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.32 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-10"
review_due: "2026-09-10"
supersedes: null
superseded_by: null
---

# DEC-051 Property and Fuzz Test Expansion

## Decision question

Should StoneCharts extend randomized property tests and fuzz seeds from the current
7 chart types to all 35?

## Background

### Current coverage

The Python property test suite (`test_property_rendering.py`) generates randomized
specs for exactly 7 chart types:

```
line, column, area, bar, combo, scatter, bubble
```

Each type gets 8 randomized cases from a fixed seed, testing that:
- `render_svg` does not raise exceptions
- `render_svg` produces well-formed SVG (valid XML, `<svg>` root)
- The output is deterministic (rendering twice produces identical bytes)

The Go fuzz test (`FuzzFromJSON`) has 10 seed files covering the same 7 chart types
(with combo dual-axis as an additional seed).

The Go randomized test (`TestRandomizedSpecsRenderValidSVG`) mirrors the Python suite
with the same 7 types.

### The gap

The remaining 28 chart types have golden fixture tests (deterministic, specific
examples) but no randomized or fuzz coverage. This means:

- **Golden tests** prove: "These specific examples produce expected bytes."
- **Property tests** prove: "A broader range of inputs does not expose NaN/Inf, parser
  problems, or nondeterminism."
- **Fuzz tests** prove: "Malformed or extreme inputs do not crash the renderer."

For the 28 chart types without property/fuzz coverage, the only assurance is that
hand-crafted examples work. Edge cases in data shapes, empty series, extreme values,
and unusual combinations are untested by randomized generation.

### Chart families and data models

Not all 35 chart types can share one randomized generator. They fall into several
data model families:

| Family | Data model | Chart types |
|--------|-----------|-------------|
| Category-value | `categories[] + data[]` | line, column, area, bar, lollipop, variwide, windbarb, streamgraph, nightingale, radial-bar |
| Point (x,y) | `data: [{x,y}]` or `x[] + data[]` | scatter, bubble, vector-plot, timeline |
| Range | `data[] + low[]` or `data[] + high[]` | arearange, columnrange, error-bar, dumbbell |
| OHLC | `ohlc: [{o,h,l,c}]` | candlestick |
| Summary | `boxData: [{low,q1,median,q3,high}]` | boxplot |
| Binning | `data[]` (raw observations) | histogram |
| Span | `spans: [{x,x2,y}]` | xrange, flame-chart |
| Composition | `categories[] + data[]` (single series) | pie, gauge, solid-gauge, parliament |
| Polar category | `categories[] + data[]` (multi-series) | radar, polar, wind-rose |
| KPI | `data[] + bulletTarget + bulletRanges` | bullet |
| Transform | `data[] + indicators[]` | technical-indicators |
| Stack-only | `categories[] + data[]` (multi-series stacked) | waterfall, funnel, combo |

### Implementation approach

Build one randomized spec generator per data model family, then instantiate it for
each chart type in that family. This avoids 35 independent generators while respecting
the structural differences between chart types.

## Recommendation

Extend property and fuzz coverage to all 35 chart types, organized by data model
family.

### Phase 1 — Category-value family (10 types)

Extend the existing `_specs()` generator to cover: lollipop, variwide, windbarb,
streamgraph, nightingale, radial-bar (in addition to the existing line, column, area,
bar).

These all share `categories[] + data[]` and differ only in mark rendering.

### Phase 2 — Range family (4 types)

New generator producing `{data[], low[], high[]}` specs for: arearange, columnrange,
error-bar, dumbbell.

Invariant: `len(low) == len(data)` and `low[i] <= data[i]` where applicable.

### Phase 3 — Structured data models (7 types)

Individual generators for: boxplot (summary model), candlestick (OHLC), histogram
(raw observations), xrange/flame-chart (spans), bullet (KPI), technical-indicators
(transforms).

### Phase 4 — Polar/composition family (6 types)

Generator for: pie, gauge, solid-gauge, parliament, radar, polar, wind-rose.

### Go parity

Each Python generator gets a corresponding Go randomized test and fuzz seed corpus
entry.

### Coverage target

Every chart type should have:
- 8 randomized property test cases (matching the existing pattern)
- At least 2 fuzz seed corpus entries in Go
- Determinism assertion (render twice, compare bytes)
- No-crash assertion (no panic/exception on valid randomized input)

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Expand to all 35 in 4 phases | Full randomized coverage; phased delivery | Moderate engineering effort (~2 days); best assurance |
| Expand to top 13 only | Cover the charts closest to commercial use | Partial coverage; leaves 22 types with golden-only testing |
| Defer | Keep current 7-type coverage | The gap between "certified" and "deeply tested" persists |

## Stakeholder impact

- **Product:** "Every certified chart type is randomized-tested" becomes a true
  statement. Currently it is not.
- **Engineering:** ~4 new generator functions (one per family), instantiated across
  types. The existing test infrastructure handles the rest.
- **QA:** Randomized tests catch edge cases that hand-crafted goldens miss — NaN
  propagation, empty series, extreme value ranges, single-point datasets.

## Dependencies

- DEC-049 (renderer purity) should be resolved first, since randomized tests will
  expose mutation-related nondeterminism.
