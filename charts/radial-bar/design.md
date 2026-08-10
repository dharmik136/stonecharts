# Radial bar (racetrack) chart — design & build recipe

> **Status:** certified (0.0.0.31, DEC-047)
> **Family:** B — Polar / radial (sibling)
> **Substrate:** Concentric track rings — one ring per category, angular
> extent encodes value.

## 1. What it shows

A radial bar (racetrack / progress ring) chart plots **categorical values**
as arcs on concentric circular tracks. Each category gets its own ring;
the arc length (angular sweep from the top) encodes the value. Multiple
series stack angularly within each track, like a stacked bar chart wrapped
into circles.

**Use when:** showing progress or completion across categories (KPI
dashboards, skill levels, SLO compliance), or comparing magnitudes on a
compact circular layout.

**Don't use when:** precise comparison is primary (use bar), data is
directional (use wind-rose).

## 2. Data model

| Field | Source | Meaning |
|-------|--------|---------|
| `xAxis.categories[N]` | spec | The N category labels (one per track) |
| `series[i].data[N]` | spec | One value per category for series i (angular fill) |

Minimum: 1 category, 1 series.

## 3. Geometry

### 3.1 Coordinate mapping

- **Center:** `(cx, cy)` = center of the plot area.
- **Max radius:** `r_max = min(plot_w, plot_h) / 2 - label_margin`.
  `label_margin = 40`.
- **Inner margin:** `r_inner = r_max × 0.3` (leave center hollow).
- **Track layout:** N categories, distributed from outermost to innermost.
  `band = (r_max - r_inner) / N`. Track i outer radius =
  `r_max - i × band`, inner radius = `r_max - (i + 1) × band + gap`
  where `gap = 2` px.
- **Track width:** `band - gap`.
- **Value → angle:** linear scale. `angle = -π/2 + (value / y_max) × 2π`.
  `y_max` = max cumulative stack across all categories. Arc starts at
  `-π/2` (12 o'clock), sweeps clockwise.

### 3.2 Grid

- **4 angular reference lines** from center at 0%, 25%, 50%, 75% of full
  sweep (angles `-π/2`, `0`, `π/2`, `π`).
- **Grid color:** `theme.grid_color`, stroke-width 1.

### 3.3 Track background

- Each track has a full-circle ring background:
  `<path>` annular ring, filled with grid color at low opacity (0.15).

### 3.4 Value bar (arc)

- Annular sector from start angle to end angle at track inner/outer radius.
- Fill = series color, stroke = theme background, stroke-width 1.
- Multiple series stack angularly per track (cumulative start angle).

### 3.5 Category labels

- Category label for track i placed at the left of the track (9 o'clock),
  offset outside the track outer edge.

### 3.6 Value tick labels

- Percentage labels at each angular reference line along the outermost track.

## 4. SVG class contract

| Element | Class | Data attributes |
|---------|-------|-----------------|
| Angular grid line | `sc-radialbar-grid` | `data-pct="0..75"` |
| Track background ring | `sc-radialbar-track` | `data-index="i"` |
| Category label | `sc-radialbar-label` | `data-index="i"` |
| Value tick label | `sc-radialbar-tick` | `data-value="v"` |
| Value arc bar | `sc-radialbar-bar sc-point` | `data-series="i"` `data-index="j"` `data-y` `data-color` |

## 5. Example spec (basic)

```json
{
  "type": "radial-bar",
  "title": "Skill Levels",
  "xAxis": {
    "categories": ["Python", "Go", "SQL", "JavaScript", "TypeScript"]
  },
  "series": [
    {"name": "Proficiency", "data": [90, 75, 80, 65, 70]}
  ],
  "yAxis": {"max": 100}
}
```
