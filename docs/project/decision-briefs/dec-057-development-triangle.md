---
id: SC-OPS-027
title: DEC-057 Development Triangle Chart Type
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

# DEC-057 Development Triangle Chart Type

## Decision question

Should StoneCharts build a first-class `development-triangle` (or `actuarial-matrix`)
chart type as a high-priority addition for the insurance reporting segment?

## Background

The development triangle is one of the most fundamental actuarial representations.
It shows how insurance claims develop over time, typically with accident years as
rows and development periods as columns:

```
          DEVELOPMENT PERIOD
AY        12      24      36      48      60

2021     120     184     213     228     235
2022     137     199     229     241
2023     154     216     247
2024     171     238
2025     193
```

The triangular shape (fewer values in recent years) is inherent to the data — recent
accident years have had less time to develop.

### Why this matters for StoneCharts

This chart type maps directly to the insurance reporting segment that DEC-017
identified as StoneCharts' primary validation market. Every actuary works with
development triangles. Every reserve review includes them. Every regulatory
submission shows them.

A single well-executed development-triangle chart type could be more valuable to an
actuarial buyer than many of the niche chart types currently in the experimental tier.

### What actuaries need beyond a basic heatmap

A general-purpose heatmap shows colored cells in a matrix. An actuarial development
triangle needs domain-specific features:

| Feature | Description |
|---------|-------------|
| **Incremental vs. cumulative** | Toggle between incremental and cumulative views |
| **Paid vs. incurred** | Support both paid and incurred triangles |
| **Loss ratios** | Divide by earned premium to show loss ratio triangle |
| **Development factors** | Show link ratios (column-to-column factors) |
| **Diagonal highlighting** | Highlight the latest diagonal (most recent valuation) |
| **Selected values** | Mark actuarially selected factors vs. raw data |
| **Annotations** | Cell-level notes (e.g., "large loss adjusted") |
| **Prior comparison** | Side-by-side with previous valuation's triangle |
| **Color scales** | Heat-map coloring by value magnitude or deviation |
| **Row/column aggregates** | Weighted averages, medians, selected factors in summary rows |

### Market context

**The insurance analytics market is $15.4B (2026) growing 15.6% CAGR.** Actuarial
modeling software is a key growth area. Tools like Moody's, SAS, and Oracle provide
actuarial modeling but their visualization is typically embedded in proprietary
dashboards. A standalone, deterministic, auditable triangle renderer would fill a
gap.

**IFRS 17 requires granular reserve disclosure.** Development triangles are a
standard component of reserve disclosures under IFRS 17 and Solvency II. Actuaries
need to produce these for regulatory submissions, board presentations, and audit
reviews. Currently they use Excel, R, or Python scripts — none with visual integrity
guarantees.

**No charting library offers a first-class development triangle.** Highcharts has
heatmaps but not actuarial-specific features. Vega can render a matrix but requires
significant custom configuration. D3 requires building from primitives. A
purpose-built, governed development triangle would be unique in the market.

## Recommendation

Add `development-triangle` as a new chart type, targeting the **certified** tier
from the start (it should be built to the SC-CERT standard from day one).

### Spec design

```json
{
  "type": "development-triangle",
  "title": "Incurred Loss Development Triangle",
  "triangle": {
    "origins": ["2021", "2022", "2023", "2024", "2025"],
    "periods": [12, 24, 36, 48, 60],
    "values": [
      [120, 184, 213, 228, 235],
      [137, 199, 229, 241],
      [154, 216, 247],
      [171, 238],
      [193]
    ],
    "view": "cumulative",
    "valueType": "incurred",
    "unit": "millions"
  },
  "diagonal": {"highlight": true, "label": "Latest diagonal"},
  "factors": {"show": true, "position": "below"},
  "colorScale": {"type": "sequential", "domain": "auto"},
  "annotations": [
    {"origin": "2023", "period": 36, "text": "Large loss adjusted"}
  ]
}
```

### Semantic invariants (SC-SEM for this chart type)

- `values[i]` has at most `len(periods) - i` entries (triangular shape)
- Cumulative values are non-decreasing within each row (for paid claims)
- Development factors are `values[i][j+1] / values[i][j]` — renderer can compute
  and display but must not modify the input triangle (DEC-049)
- Color scale maps to actual value range, not arbitrary normalization

### Implementation scope

| Component | Description |
|-----------|-------------|
| `charts/development-triangle/design.md` | Chart design document |
| `charts/development-triangle/examples/` | Basic, factors, diagonal, annotated, comparison |
| `libs/python/stonecharts/charts/development_triangle.py` | Python renderer |
| `libs/go/development_triangle.go` | Go renderer |
| `spec/chart-spec.schema.json` | Add `development-triangle` type and `triangle` schema |
| Golden tests | Byte-identical fixtures across all examples |
| Property tests | Randomized triangle generation with invariant checks |
| Semantic tests | Triangular shape, factor correctness, color mapping |

### Build order

This chart type does NOT use the Cartesian substrate. It is a matrix/table layout
with its own SVG shell (similar to funnel's substrate exception in DEC-031). The
rendering approach is:

1. Grid of cells at fixed row/column positions
2. Cell text (value) with optional color fill
3. Diagonal highlight overlay
4. Factor row/column (computed display, not spec mutation)
5. Annotation markers
6. Row/column header labels

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Build as first-class certified chart type | Purpose-built for the insurance segment; certified from start | New chart type effort (~2–3 days); highest market impact |
| Build as a heatmap variant | Extend a general heatmap with actuarial features | Shares substrate but may compromise domain-specific features |
| Defer | Focus on certifying existing candidate charts first | Misses a high-value market opportunity |

## Dependencies

- DEC-049 (renderer purity) — must be built pure from day one.
- DEC-050 (semantic invariants) — triangle-specific invariants should be defined
  at design time.
- DEC-053 (tiered certification) — should enter directly as certified, not
  experimental.
