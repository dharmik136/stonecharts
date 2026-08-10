# Pie chart — design

| Field | Value |
|-------|-------|
| Type  | `"pie"` |
| Class | new-family (Family B opener — pays the polar foundation tax) |
| Src   | HC |

## What it shows

Part-to-whole composition: each slice represents one category's share of a
total. A single series of N non-negative values maps to N arc sectors whose
angles are proportional to value / total.

## Data model

```jsonc
{
  "type": "pie",
  "title": "Market Share",
  "xAxis": { "categories": ["Chrome", "Safari", "Firefox", "Edge"] },
  "series": [{ "name": "Browsers", "data": [65, 18, 10, 7] }]
}
```

- `xAxis.categories[i]` → slice label for `series[0].data[i]`.
- Single series only; multi-series pie is out of scope for v1.
- All values must be non-negative. Zero-valued slices are skipped (no arc).

## Rendering

### Layout

No Cartesian axes or gridlines. Own SVG shell (like funnel).

- Title and subtitle at top (same positioning as Cartesian charts).
- Pie centered in the remaining plot area.
- Legend at bottom using the shared legend renderer.

### Geometry

Start angle: −π/2 (12 o'clock). Clockwise rotation.

For each slice with value > 0:
- `sweep = (value / total) * 2π`
- `x1 = cx + r·cos(startAngle)`, `y1 = cy + r·sin(startAngle)`
- `x2 = cx + r·cos(endAngle)`, `y2 = cy + r·sin(endAngle)`
- SVG path: `M cx cy L x1 y1 A r r 0 <largeArc> 1 x2 y2 Z`
- `largeArc = 1` if `sweep > π`, else `0`
- Special case: single slice at 100% → draw a `<circle>` instead of an arc.

Slice stroke: 2px white (`#ffffff`) for light theme, 2px `#1e1e2f` for dark.

### Data attributes

Each `<path>` (or `<circle>`) carries:
`class="sc-slice sc-point"`, `data-series="0"`, `data-series-name`,
`data-x` (category label), `data-y` (formatted value),
`data-index` (slice index), `data-percentage` (formatted %),
`data-color`, `data-r`, `data-r-hover`, `cx`, `cy`.

### Donut variant

When `innerSize` > 0 (float 0–1, proportion of outer radius), the chart renders
as a donut (annular ring). Slices become annular sectors:

- Path: outer arc (clockwise) → line to inner arc → inner arc (counter-clockwise) → close.
- Single-slice 100%: two concentric circle arcs with `fill-rule="evenodd"`.
- `subtype: "donut"` is conventional but not required; `innerSize > 0` is
  the actual trigger.

### Accessibility

`role="img"`, `aria-label`, `<desc>` summary.
Data table: Category | Value | Percentage columns.
