# Radar / Spider chart — design & build recipe

> **Status:** certified (0.0.0.27, DEC-043)
> **Family:** B — Polar / radial (sibling)
> **Substrate:** Polar category grid — N radial axes at equal angular spacing,
> concentric polygon gridlines (spiderweb), values mapped to radius.

## 1. What it shows

A radar (spider / web) chart plots **multi-dimensional categorical data** on
radial axes emanating from a shared center point. Each category gets its own
axis; the value along each axis determines the vertex position; connecting the
vertices forms a polygon. Multiple series overlay as distinct polygons for
comparison.

**Use when:** comparing entities across 3+ qualitative dimensions (service
scorecards, skill profiles, product feature coverage).

**Don't use when:** fewer than 3 dimensions (use bar), precise value reading
matters more than shape comparison (use grouped bar), trend over time (use
line).

## 2. Data model

| Field | Source | Meaning |
|-------|--------|---------|
| `xAxis.categories[N]` | spec | The N dimension labels (one per radial axis) |
| `series[i].data[N]` | spec | One value per dimension for series i |
| `series[i].fillOpacity` | spec | >0 fills the polygon interior (0 = line-only) |

Minimum: 3 categories, 1 series.

## 3. Geometry

### 3.1 Coordinate mapping

- **Center:** `(cx, cy)` = center of the plot area.
- **Max radius:** `r_max = min(plot_w, plot_h) / 2 - label_margin`.
  `label_margin = 40` reserves space for outer category labels.
- **Angle per axis:** `angle_i = -π/2 + i × 2π/N` (first axis points UP,
  clockwise).
- **Value → radius:** linear scale from `y_min` to `y_max`:
  `r = (value - y_min) / (y_max - y_min) × r_max`.
  Default: `y_min = 0`, `y_max = max(all series data)`.
  If `yAxis.min` / `yAxis.max` are set, use those.

### 3.2 Grid (spiderweb)

- **5 concentric polygon rings** at 20%, 40%, 60%, 80%, 100% of `r_max`.
  Each ring is a closed polygon with N vertices at the ring's radius on each
  axis.
- **N radial axis lines** from center to the outermost ring vertex.
- **Grid color:** `theme.grid_color`, stroke-width 1.

### 3.3 Axis labels

- Category labels placed outside the outermost ring, offset 12px from the
  ring vertex along the radial direction.
- `text-anchor`: `"middle"` for top/bottom axes, `"start"` for right half,
  `"end"` for left half.

### 3.4 Radial value labels

- Numeric tick labels along the first radial axis (index 0, pointing up)
  at each grid ring level.

### 3.5 Data polygon

- For each series, connect the N data vertices with straight line segments
  forming a closed polygon (`M ... L ... L ... Z`).
- `fill-opacity` from `series.fill_opacity` (default 0 = line-only).
- `stroke` = series color, `stroke-width` = 2.
- Data points rendered as circles (radius 4) at each vertex.

## 4. SVG class contract

| Element | Class | Data attributes |
|---------|-------|-----------------|
| Grid ring polygon | `sc-radar-ring` | `data-level="0..4"` |
| Radial axis line | `sc-radar-axis` | `data-index="i"` |
| Category label | `sc-radar-label` | `data-index="i"` |
| Value tick label | `sc-radar-tick` | `data-value="v"` |
| Series polygon | `sc-radar-poly sc-point` | `data-series="i"` `data-series-name` `data-color` |
| Series vertex dot | `sc-radar-dot sc-point` | `data-series="i"` `data-index="j"` `data-y` |

## 5. Example spec (basic)

```json
{
  "type": "radar",
  "title": "Service Scorecard",
  "xAxis": {
    "categories": ["Latency", "Throughput", "Availability", "Error Rate", "Saturation"]
  },
  "series": [
    {"name": "Service A", "data": [80, 95, 99, 15, 60], "fillOpacity": 0.15},
    {"name": "Service B", "data": [70, 80, 95, 25, 45], "fillOpacity": 0.15}
  ]
}
```
