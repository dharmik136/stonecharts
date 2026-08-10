# Wind Rose chart — design & build recipe

> **Status:** certified (0.0.0.29, DEC-045)
> **Family:** B — Polar / radial (variant)
> **Substrate:** Polar category grid — N radial directions at equal angular
> spacing, stacked radial column sectors per direction.

## 1. What it shows

A wind rose plots **directional frequency/magnitude data** as stacked radial
columns on a polar grid. Each angular category represents a direction (compass
bearing, month, hour); each series stacks outward from center as a sector
wedge. The radial extent of each wedge encodes the value for that series at
that direction.

**Use when:** data is directional or cyclical with multiple magnitude bands
(wind speed by direction, event counts by hour of day, seasonal distributions).

**Don't use when:** data has no angular/directional nature (use stacked bar),
precise value comparison is primary (use grouped column).

## 2. Data model

| Field | Source | Meaning |
|-------|--------|---------|
| `xAxis.categories[N]` | spec | The N direction labels (one per angular sector) |
| `series[i].data[N]` | spec | One value per direction for series i (stacks outward) |

Minimum: 3 categories, 1 series.

## 3. Geometry

### 3.1 Coordinate mapping

- **Center:** `(cx, cy)` = center of the plot area.
- **Max radius:** `r_max = min(plot_w, plot_h) / 2 - label_margin`.
  `label_margin = 40`.
- **Angle per direction:** `angle_i = -π/2 + i × 2π/N` (first direction
  points UP, clockwise). Each sector spans `2π/N` radians centered on the
  direction angle.
- **Value → radius:** linear scale. Each series stacks: `r_start` =
  cumulative sum of preceding series values at this direction, `r_end` =
  `r_start + value`. Scaled to `r_max` using `y_max` = max cumulative
  stack across all directions.

### 3.2 Grid (circular)

- **5 concentric circular rings** at 20%, 40%, 60%, 80%, 100% of `r_max`.
- **N radial axis lines** from center through each direction.
- **Grid color:** `theme.grid_color`, stroke-width 1.

### 3.3 Sector wedge

- Each sector is an annular wedge (arc path) spanning from `angle - half_span`
  to `angle + half_span`, with inner radius `r_start` and outer radius `r_end`.
- `half_span = π/N - gap` where `gap = 0.02` radians (thin separator).
- Fill = series color, stroke = theme background or white, stroke-width 1.

### 3.4 Axis labels

- Direction labels placed outside the outermost ring, offset 12px.

### 3.5 Radial value labels

- Numeric tick labels along the first radial axis at each ring level.

## 4. SVG class contract

| Element | Class | Data attributes |
|---------|-------|-----------------|
| Grid circle | `sc-windrose-ring` | `data-level="0..4"` |
| Radial axis line | `sc-windrose-axis` | `data-index="i"` |
| Direction label | `sc-windrose-label` | `data-index="i"` |
| Value tick label | `sc-windrose-tick` | `data-value="v"` |
| Sector wedge | `sc-windrose-sector sc-point` | `data-series="i"` `data-index="j"` `data-y` `data-color` |

## 5. Example spec (basic)

```json
{
  "type": "wind-rose",
  "title": "Wind Distribution",
  "xAxis": {
    "categories": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
  },
  "series": [
    {"name": "0-5 kt", "data": [5, 3, 4, 2, 6, 8, 7, 4]},
    {"name": "5-10 kt", "data": [8, 5, 6, 4, 9, 12, 10, 6]},
    {"name": "10-15 kt", "data": [3, 2, 3, 1, 4, 5, 4, 2]}
  ]
}
```
