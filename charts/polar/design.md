# Polar chart — design & build recipe

> **Status:** certified (0.0.0.28, DEC-044)
> **Family:** B — Polar / radial (sibling)
> **Substrate:** Polar coordinate grid — angular x-axis (categories at equal
> spacing), radial y-axis (value mapped to radius), circular gridlines.

## 1. What it shows

A polar chart maps **categorical data onto a circular coordinate system**.
Categories are distributed at equal angular intervals around the circle's
circumference; values are mapped to the radial distance from center. Unlike
radar (which uses polygon gridlines), polar uses **circular gridlines** and
renders data as either a closed polygon line, filled area, or radial column
sectors.

**Use when:** data is cyclical or directional (months, compass bearings,
hours of day), comparing magnitude across angular categories.

**Don't use when:** data has no cyclical nature (use bar/column), precise
value reading matters more than pattern (use grouped bar), trend over time
without cyclical wrap (use line).

## 2. Data model

| Field | Source | Meaning |
|-------|--------|---------|
| `xAxis.categories[N]` | spec | The N angular labels (one per radial position) |
| `series[i].data[N]` | spec | One value per category for series i |
| `series[i].fillOpacity` | spec | >0 fills the area under the line to center |

Minimum: 3 categories, 1 series.

## 3. Geometry

### 3.1 Coordinate mapping

- **Center:** `(cx, cy)` = center of the plot area.
- **Max radius:** `r_max = min(plot_w, plot_h) / 2 - label_margin`.
  `label_margin = 40` reserves space for outer category labels.
- **Angle per category:** `angle_i = -π/2 + i × 2π/N` (first category
  points UP, clockwise).
- **Value → radius:** linear scale from `y_min` to `y_max`:
  `r = (value - y_min) / (y_max - y_min) × r_max`.
  Default: `y_min = 0`, `y_max = max(all series data)`.
  If `yAxis.min` / `yAxis.max` are set, use those.

### 3.2 Grid (circular)

- **5 concentric circular rings** at 20%, 40%, 60%, 80%, 100% of `r_max`.
  Each ring is a `<circle>` element (unlike radar's polygon rings).
- **N radial axis lines** from center to the outermost ring at each
  category angle.
- **Grid color:** `theme.grid_color`, stroke-width 1.

### 3.3 Axis labels

- Category labels placed outside the outermost ring, offset 12px from the
  ring edge along the radial direction.
- `text-anchor`: `"middle"` for top/bottom, `"start"` for right half,
  `"end"` for left half.

### 3.4 Radial value labels

- Numeric tick labels along the first radial axis (index 0, pointing up)
  at each grid ring level.

### 3.5 Data marks

- For each series, connect data vertices with straight line segments
  forming a closed polygon (`M ... L ... L ... Z`).
- `fill-opacity` from `series.fill_opacity` (default 0 = line-only).
- `stroke` = series color, `stroke-width` = 2.
- Data points rendered as circles (radius 4) at each vertex.

## 4. SVG class contract

| Element | Class | Data attributes |
|---------|-------|-----------------|
| Grid circle | `sc-polar-ring` | `data-level="0..4"` |
| Radial axis line | `sc-polar-axis` | `data-index="i"` |
| Category label | `sc-polar-label` | `data-index="i"` |
| Value tick label | `sc-polar-tick` | `data-value="v"` |
| Series polygon | `sc-polar-poly sc-point` | `data-series="i"` `data-series-name` `data-color` |
| Series vertex dot | `sc-polar-dot sc-point` | `data-series="i"` `data-index="j"` `data-y` |

## 5. Example spec (basic)

```json
{
  "type": "polar",
  "title": "Monthly Rainfall",
  "xAxis": {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  },
  "series": [
    {"name": "Tokyo", "data": [50,60,110,130,200,180,250,220,180,120,80,40], "fillOpacity": 0.15}
  ]
}
```
