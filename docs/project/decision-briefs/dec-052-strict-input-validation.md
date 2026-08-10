---
id: SC-OPS-022
title: DEC-052 Strict Input Validation
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

# DEC-052 Strict Input Validation

## Decision question

Should StoneCharts replace silent fallbacks and lossy data handling with explicit
validation errors when input data is ambiguous or semantically invalid?

## Background

An external code review identified two places where StoneCharts silently degrades
input rather than rejecting it. For an ordinary chart library, silent degradation is
convenience. For a product selling visual integrity, it is the wrong philosophy.

### Finding 1: Histogram bin clamping

`libs/python/stonecharts/charts/histogram.py`, line 89:

```python
b = max(0, min(k - 1, b))
```

When explicit bin edges are configured and an observation falls outside the configured
range, it is silently clamped into the nearest edge bin. A claim of 9,500,000 in a
histogram with a 0–1,000,000 range silently becomes part of the 900k–1m bin.

**Why this matters:** The rendered histogram misrepresents the distribution. An
auditor looking at the chart cannot tell that extreme values were absorbed into edge
bins. The observation count in the rendered bins does not match the source data count.

### Finding 2: Arearange missing low values

`libs/python/stonecharts/charts/arearange.py`, line 53:

```python
lo_pts = [(fr.xpix(i), fr.ypix(low_arr[i] if i < len(low_arr) else s.data[i]))
          for i in range(n)]
```

When `low` data is absent or shorter than `data` (high values), the renderer silently
uses the high value as the low value. This collapses the range band to zero height —
the chart renders but shows no visible range, which could silently produce a
misleading visualization.

**Why this matters:** A caller who forgets to supply `low` data gets a chart that
looks like it rendered correctly but actually shows no confidence interval. The chart
does not tell the viewer that range data is missing.

### Principle

StoneCharts should prefer **loud failure over silent degradation**:

```
Expected 12 range points
Received:
  12 high values
  11 low values

E_RANGE_CARDINALITY: low and high arrays must have equal length.

RENDER REFUSED
```

This is more valuable than a chart that renders but lies.

## Recommendation

Accept strict input validation as a project-wide policy:

> **When input data is structurally incomplete, cardinally mismatched, or semantically
> invalid, the renderer must raise a `SpecError` rather than silently degrade.**

### Specific fixes

#### Histogram out-of-range observations

Replace silent clamping with an explicit policy:

```python
class OutOfRangePolicy(str, Enum):
    ERROR = "error"        # default: raise SpecError
    CLIP = "clip"          # current behavior, explicitly opted into
    OVERFLOW = "overflow"  # count in a dedicated overflow bin
```

Add `outOfRange` to the spec schema. Default is `"error"`. When `"clip"` is chosen,
the clamping behavior is retained but the evidence bundle records that clipping
occurred and how many observations were affected.

#### Arearange/columnrange/error-bar/dumbbell cardinality

When `low` is supplied, require `len(low) == len(data)`. When `low` is absent
entirely, raise `SpecError` — range chart types require both boundaries.

```python
if low_arr is None or len(low_arr) == 0:
    raise SpecError(
        f"Arearange requires 'low' data; got {len(low_arr or [])} values "
        f"for {len(s.data)} data points"
    )
if len(low_arr) != len(s.data):
    raise SpecError(
        f"Arearange 'low' length ({len(low_arr)}) does not match "
        f"'data' length ({len(s.data)})"
    )
```

#### Boxplot ordering

Validate `low <= q1 <= median <= q3 <= high` for each `BoxDatum`. Reject specs
where quartiles are out of order rather than rendering a visually nonsensical box.

#### Pie negative values

Reject specs where any pie data value is negative rather than rendering a
meaningless negative-angle slice.

#### Gauge bounds

Reject specs where `gaugeMin >= gaugeMax` or where the value falls outside the
gauge range without an explicit overflow policy.

### Go parity

Every Python validation must have an identical Go validation producing the same
error message format. Cross-language validation parity joins cross-language
rendering parity as a certification requirement.

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Strict by default, explicit opt-in for lenient | Bad input is rejected unless the caller explicitly requests degradation | Best for integrity; may break existing specs that rely on silent fallbacks |
| Strict as opt-in | Add validation but default to current lenient behavior | Backward compatible but doesn't improve the default experience |
| Defer | Keep current silent fallbacks | Misrepresentation risk remains; undermines visual integrity story |

## Migration risk

Existing specs that rely on silent fallbacks (e.g., arearange specs without `low`
data, histograms with out-of-range observations) will fail validation after this
change. This is intentional — those specs were producing misleading output.

A migration path:
1. Run `validate(spec)` against existing specs to identify affected ones.
2. Fix specs that have missing data.
3. For histogram specs that intentionally include out-of-range data, add explicit
   `outOfRange: "clip"` to the spec.

## Stakeholder impact

- **Product:** "StoneCharts refuses to render a misleading chart" becomes a concrete
  differentiator. Competing libraries silently render wrong charts.
- **Engineering:** Validation additions in `validate.py`/`validate.go`, plus schema
  changes for the `outOfRange` policy field. Fix ~4 renderer files.
- **QA:** Existing adversarial test fixtures may need updating if they rely on
  currently-silent fallback behavior.

## Dependencies

- DEC-050 (semantic invariants) defines the correctness properties that this decision
  enforces at the input boundary.
- Schema changes require a `spec/chart-spec.schema.json` update and a
  schema-compatibility check.

## Files requiring changes

- `libs/python/stonecharts/validate.py`
- `libs/go/validate.go`
- `libs/python/stonecharts/charts/histogram.py`
- `libs/go/histogram.go`
- `libs/python/stonecharts/charts/arearange.py`
- `libs/go/arearange.go`
- `libs/python/stonecharts/charts/columnrange.py` (if same pattern)
- `libs/go/columnrange.go`
- `spec/chart-spec.schema.json` (add `outOfRange` enum)
- `libs/python/tests/test_limits.py` (update edge-case expectations)
