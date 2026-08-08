# Chart: Bullet (`bullet`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** [`charts/column/design.md`](../column/design.md) and adds the
> sibling build detail: data model, marks, band layout, reused chrome, parity
> traps, and the a11y DOM contract.

- **Chart id:** `bullet`
- **Spec `type`:** `"bullet"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 13** · **Src:** SF
- **Status:** design-complete + renderers certified
- **Renderers:** `libs/python/stonecharts/charts/bullet.py` · `libs/go/bullet.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5 (Rank 13)

## What it is

A bullet chart: a **compact KPI visualization** that shows a primary measure
(the "performance" bar), a comparative marker (the "target" tick), and
qualitative range bands (graded background rectangles indicating poor,
satisfactory, and good performance zones). Each row represents one KPI,
rendered as a horizontal bar.

Stephen Few's original bullet graph design replaces gauges and meters with a
space-efficient, information-dense display that works in dashboards.

## Data model

```jsonc
{
  "type": "bullet",
  "xAxis": { "categories": ["Revenue"] },
  "series": [{ "name": "2024 Actual", "data": [275] }],
  "bulletTarget": 250,        // comparative target value
  "bulletRanges": [150, 225, 300]  // qualitative range bounds
}
```

| Field | Type | Description |
|---|---|---|
| `series[].data[]` | `number[]` | Measure values — one per category (the KPI bar length) |
| `bulletTarget` | `number` | Target value — drawn as a tick mark across the measure bar |
| `bulletRanges` | `number[]` | Qualitative range bounds (sorted ascending). Defines graded background bands from 0 to each bound |

## Marks

1. **Qualitative range bands** — full-height background `<rect>` elements within
   each band, graded from darkest (lowest/worst) to lightest (highest/best).
   Light theme: `#cccccc`, `#dddddd`, `#eeeeee`. Dark theme: `#3d3d55`,
   `#2d2d42`, `#1e1e30`.

2. **Measure bar** — a thinner `<rect>` (40% of band height), baseline-anchored,
   showing the actual value. Colored with the series palette color.

3. **Target tick** — a vertical `<line>` at the target value, 60% of band
   height, stroke-width 2. Light theme: `#333333`. Dark theme: `#cccccc`.

## Reused infrastructure

- Horizontal orientation (same as bar — `render_cartesian(…, orientation="horizontal")`)
- Value axis with `nice_ticks` and `include_zero=True`
- Band layout (one row per category)
- Shared chrome (title, subtitle, axes, gridlines, legend, crosshair)
- Theme + palette
- A11y (role="img", desc, visually-hidden data table)

## Parity traps

- Range band x-coords computed from `value_pix(prev)` to `value_pix(range[k])` —
  must use `f1` / `:.1f` formatting for byte identity.
- Target tick uses `stroke-width="2"` (integer), not `"2.0"`.
- Measure bar height is `bar_h * 0.4`; target height is `bar_h * 0.6` — both
  use exact float multiplication, no rounding before `f1`.
