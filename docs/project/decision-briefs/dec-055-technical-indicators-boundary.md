---
id: SC-OPS-025
title: DEC-055 Technical Indicators Architectural Boundary
status: approved
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

# DEC-055 Technical Indicators Architectural Boundary

## Decision question

Should the technical-indicators chart type's computational transforms (SMA, EMA,
Bollinger, VWAP, RSI, MACD) remain inside the certified rendering kernel, or be
separated into an extension outside the certification boundary?

## Background

The technical-indicators renderer (`technical_indicators.py` / `technical_indicators.go`)
implements six mathematical transforms inside the render function:

- **SMA** — Simple Moving Average
- **EMA** — Exponential Moving Average
- **Bollinger Bands** — Mean ± k standard deviations
- **VWAP** — Volume-Weighted Average Price
- **RSI** — Relative Strength Index
- **MACD** — Moving Average Convergence Divergence

These transforms take raw series data and compute derived values that are then
rendered as line overlays and oscillator panes. The computation happens inside the
renderer, not in a separate transform layer.

### The architectural concern

StoneCharts' value proposition is:

> Render authoritative facts with provable visual integrity.

Technical indicators blur this boundary:

```
Customer calculates authoritative values
    ↓
StoneCharts renders + verifies those values
```

vs. the current approach:

```
Customer provides raw data
    ↓
StoneCharts recalculates derived values internally
    ↓
StoneCharts renders the result
```

When something is wrong in the second model, the fault could be in:
- The input data
- The transform calculation
- The rendering

For the first model, the fault is either in the input or in the rendering — never
in the chart library's business calculations. This is a cleaner liability boundary
for regulated reporting.

### Code-level findings

The renderer also mutates `spec.y_axis.min` and `spec.y_axis.max` (confirmed in
DEC-049 audit), and the transforms run parity-critical floating-point math that
must produce identical results in Python and Go. This adds a verification burden
that is qualitatively different from pure rendering.

### Market context

**Actuarial reporting does not need in-renderer transforms.** Insurance platforms
compute their own SMA/EMA equivalents (loss development factors, moving average
loss ratios) in their actuarial models. They need a chart library that renders
those computed values faithfully, not one that recomputes them.

**Transform separation reduces certification surface.** Every line of code inside
the certified rendering kernel is a line that must be verified for cross-language
parity, purity, and semantic correctness. Moving transforms out reduces the
certification burden and makes the core guarantee stronger.

## Recommendation

Move technical-indicators to the **experimental** tier (DEC-053) and flag the
transforms as a non-certified extension.

### Implementation options

| Approach | Description | Effort |
|----------|-------------|--------|
| **Tier only** | Keep TI code where it is but mark it `experimental` in the capability API | Minimal — metadata change only |
| **Separate package** | Move transforms to `libs/python/stonecharts/transforms/` and `libs/go/transforms/` outside the certified rendering kernel | Moderate — file moves + import changes |
| **Pre-render transform** | Expose transforms as a separate `compute_indicators(spec)` function that returns a new spec with pre-computed series; rendering then works on pure data | Moderate — cleanest boundary |

### Recommended approach

**Tier only** (option 1) for now. The code works, produces byte-identical output,
and is golden-tested. Moving files is unnecessary churn unless a customer needs
TI in the certified tier. If that happens, the pre-render transform approach
(option 3) is the right architecture.

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Mark experimental, defer separation | TI stays functional but outside certification scope | No code changes; clearest path |
| Separate into transform package | Clean architectural boundary; transforms testable independently | File moves; import changes; moderate effort |
| Keep in certified kernel | TI is certified alongside all other charts | Certification burden includes business calculations |

## Dependencies

- DEC-053 (tiered certification) provides the tier metadata to mark TI as
  experimental.
- DEC-049 (renderer purity) fixes the y-axis mutation in TI regardless of tier
  decision.
