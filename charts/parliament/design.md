# Parliament / hemicycle chart — design & build recipe

> **Status:** certified (0.0.0.32, DEC-048)
> **Family:** B — Polar / radial (sibling)
> **Substrate:** Semicircular hemicycle — concentric arcs of unit dots,
> one dot per item, colored by category.

## 1. What it shows

A parliament (hemicycle) chart plots **part-to-whole categorical counts** as
unit dots arranged in concentric semicircular rows. Each dot represents one
unit (seat, vote, item); color encodes the category. The total count determines
the number of dots; their arrangement fills a 180° hemicycle from bottom-left
to bottom-right.

Classic uses: parliamentary seat distribution, voting breakdowns, survey
response counts, resource allocation by department.

## 2. Geometry contract

### 2.1 Inputs

| Field | Source | Notes |
|---|---|---|
| categories | `xAxis.categories[j]` | Category labels (party names) |
| values | `series[0].data[j]` | Count per category (integer-like) |

Single-series only. Each `data[j]` is the count of dots for category `j`.
Total dots = sum of all values.

### 2.2 Layout

- **Hemicycle center:** `(cx, cy)` at bottom-center of the plot area.
- **Radii:** concentric arcs from `r_min` (innermost) to `r_max` (outermost).
- **Angular span:** π (180°), from π (left) to 0 (right).
- **Rows:** computed to fit all dots with approximately equal spacing.
  Row count `n_rows` chosen so total capacity ≥ total dots.
  Each row `k` at radius `r_k = r_min + k * (r_max - r_min) / (n_rows - 1)`.
  Capacity of row `k` = `floor(π * r_k / dot_spacing)`.
- **Dot radius:** derived from row spacing and angular spacing to avoid overlap.

### 2.3 Rendering

1. Compute total dots and row layout.
2. Distribute dots across rows (inner to outer, left to right within each row).
3. Assign colors by category order: first `data[0]` dots get category 0 color,
   next `data[1]` dots get category 1 color, etc.
4. Each dot is a `<circle>` with `data-category`, `data-index`, and `data-color`.

### 2.4 Multi-series

Not supported — parliament is inherently single-series (one seat map).
If multiple series provided, only `series[0]` is used.

## 3. SVG structure

```
<svg viewBox="0 0 W H" class="sc-chart" role="img" aria-label="…">
  <desc>…</desc>
  <defs>…</defs>
  <rect class="sc-bg" …/>
  <text class="sc-title">…</text>
  <text class="sc-subtitle">…</text>
  <!-- dots -->
  <circle class="sc-parliament-dot" data-category="j" …/>
  …
  <!-- legend -->
  <g class="sc-legend">…</g>
</svg>
```

## 4. Themes

- Light: white background, standard palette.
- Dark: `#1e1e2f` background, dark palette.

## 5. Accessibility

- `role="img"` + `aria-label` + `<desc>` on `<svg>`.
- Visually-hidden data table with category, count, percentage.

## 6. Adversarial

- XSS payloads in title, subtitle, category names, series name.
- Zero-value categories (no dots, still in legend).
- Single category (all dots one color).

## 7. Test matrix

| Fixture | What it exercises |
|---|---|
| basic | 5 parties, standard parliament |
| single-series | 3 categories, small count |
| multi-series | Ignored — uses series[0] only |
| themed-dark | Dark theme |
| adversarial | XSS payloads, zero values |
