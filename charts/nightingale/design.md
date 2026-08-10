# Nightingale / rose / coxcomb chart — design & build recipe

> **Status:** certified (0.0.0.30, DEC-046)
> **Family:** B — Polar / radial (variant)
> **Substrate:** Polar category grid — N radial directions at equal angular
> spacing, radius-proportional sector wedges per direction.

## 1. What it shows

A nightingale (coxcomb / rose) chart plots **categorical data** as sector
wedges on a polar grid where the **radius** of each sector encodes the
value. Every category gets an equal angular slice; the visual area grows
quadratically with value, emphasizing differences. Multiple series are
overlaid (drawn back-to-front) with fill opacity for layering.

**Use when:** comparing magnitude across cyclical or categorical groups
where the quadratic area emphasis is desired (monthly totals, categorical
scores, Florence Nightingale's original mortality causes).

**Don't use when:** precise comparison is primary (use bar/column), data
is directional with stacked bands (use wind-rose).

## 2. Data model

| Field | Source | Meaning |
|-------|--------|---------|
| `xAxis.categories[N]` | spec | The N category labels (one per angular sector) |
| `series[i].data[N]` | spec | One value per category for series i (radius from center) |

Minimum: 3 categories, 1 series.

## 3. Geometry

### 3.1 Coordinate mapping

- **Center:** `(cx, cy)` = center of the plot area.
- **Max radius:** `r_max = min(plot_w, plot_h) / 2 - label_margin`.
  `label_margin = 40`.
- **Angle per category:** `angle_i = -π/2 + i × 2π/N` (first category
  points UP, clockwise). Each sector spans `2π/N` radians centered on the
  category angle.
- **Value → radius:** linear scale. `r = (value / y_max) × r_max`.
  `y_max` = max value across all series and all categories.

### 3.2 Grid (circular)

- **5 concentric circular rings** at 20%, 40%, 60%, 80%, 100% of `r_max`.
- **N radial axis lines** from center through each category.
- **Grid color:** `theme.grid_color`, stroke-width 1.

### 3.3 Sector wedge

- Each sector is a wedge from center to `r = value/y_max × r_max`,
  spanning from `angle - half_span` to `angle + half_span`.
- `half_span = π/N - gap` where `gap = 0.02` radians (thin separator).
- Fill = series color with fillOpacity (default 0.7 for multi-series layering).
- Stroke = theme background or white, stroke-width 1.
- Multiple series: drawn in series order (back-to-front). Later series
  overlay earlier ones. Use fillOpacity for visual layering.

### 3.4 Axis labels

- Category labels placed outside the outermost ring, offset 12px.

### 3.5 Radial value labels

- Numeric tick labels along the first radial axis at each ring level.

## 4. SVG class contract

| Element | Class | Data attributes |
|---------|-------|-----------------|
| Grid circle | `sc-nightingale-ring` | `data-level="0..4"` |
| Radial axis line | `sc-nightingale-axis` | `data-index="i"` |
| Category label | `sc-nightingale-label` | `data-index="i"` |
| Value tick label | `sc-nightingale-tick` | `data-value="v"` |
| Sector wedge | `sc-nightingale-sector sc-point` | `data-series="i"` `data-index="j"` `data-y` `data-color` |

## 5. Example spec (basic)

```json
{
  "type": "nightingale",
  "title": "Monthly Sales",
  "xAxis": {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  },
  "series": [
    {"name": "Revenue", "data": [40, 30, 35, 50, 45, 60, 70, 65, 55, 50, 45, 55]}
  ]
}
```
