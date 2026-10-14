# Chart: Heatmap (`heatmap`)

> A single-file, self-describing specification for this chart type.
> Defines the canonical contract for Family C (Matrix / Grid) Heatmap visualization in StoneCharts.
> Implemented with 100% byte-parity in Python and Go.

- **Chart id:** `heatmap`
- **Spec `type`:** `"heatmap"`
- **Class:** `new-family` (Family C — Matrix / Grid)
- **Status:** certified · release `0.0.0.35`
- **Renderers:** `libs/python/stonecharts/charts/heatmap.py` · `libs/go/heatmap.go`
- **Substrate:** [`docs/roadmap/matrix_substrate.md`](../../docs/roadmap/matrix_substrate.md) (`SC-ARCH-008`)
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) (`SC-CON-003`)
- **Requirement:** [`docs/requirements/registry.yaml`](../../docs/requirements/registry.yaml) (`REQ-HEATMAP-001`)
- **Decision:** [`docs/project/decisions.md`](../../docs/project/decisions.md) (`DEC-061`)

---

## 1. Overview & Purpose

The Heatmap renders a 2-D matrix where data values are mapped to cell background colors on a continuous numerical color scale. It serves as the **foundational opener of Family C (Matrix / Grid)**, paying the complete foundation tax for:
1. **2-D Discrete Categorical Grid Layout**: Fixed canvas with dynamic margin calculation, category label placement, and cell border insets.
2. **Continuous Color Scale Engine**: Piecewise linear RGB interpolation across arbitrary user-defined or default stops.
3. **Color-Axis (Gradient) Legend**: Continuous gradient bar with numerical ticks and labels.
4. **Accessible Matrix Representation**: WCAG 2.1 AA compliant semantic `<table>` with column and row headers.

---

## 2. Data Shape & Specification

### 2.1 Coordinate Axes
- `xAxis.categories`: Array of strings defining the column labels ($N_x \ge 1$).
- `yAxis.categories`: Array of strings defining the row labels ($N_y \ge 1$).
- Total cell count $N_x \times N_y$ must not exceed $10,000$.

### 2.2 Data Points
Each point in `series[].data` represents a matrix cell observation and may be supplied in either format:
1. Positional triplet: `[x, y, value]`
2. Object format: `{"x": x, "y": y, "value": value}`

Where:
- `x`: Integer column index in range $[0, N_x - 1]$.
- `y`: Integer row index in range $[0, N_y - 1]$.
- `value`: Finite numerical value.

### 2.3 ColorAxis Configuration
```json
"colorAxis": {
  "min": 0.0,
  "max": 100.0,
  "minColor": "#e0f3f8",
  "maxColor": "#084081",
  "stops": [
    [0.0, "#e0f3f8"],
    [0.5, "#4eb3d3"],
    [1.0, "#084081"]
  ],
  "nullColor": "#f0f0f0",
  "reversed": false
}
```

- When `min` or `max` are omitted, they are inferred from the minimum and maximum finite values present in `series[].data`.
- If `stops` are omitted, a default 3-stop sequential blue gradient is used.
- Colors are interpolated in RGB space with deterministic rounding:
  $$C = \text{int}(C_0 + u \cdot (C_1 - C_0) + 0.5)$$

---

## 3. Layout & Geometry

- **Canvas Dimensions:** Default `820` $\times$ `460` px (customizable via `width` and `height`).
- **Margins:**
  - `m_top`: $20.0\,\text{px} + (26.0\text{ if title}) + (18.0\text{ if subtitle})$.
  - `m_left`: $\max(52.0, \text{max\_y\_label\_len} \times 7.5 + 24.0) + (18.0\text{ if yAxis.title})$.
  - `m_right`: $24.0\,\text{px}$.
  - `m_bottom`: $46.0\,\text{px} + (18.0\text{ if xAxis.title}) + (36.0\text{ if color-axis legend})$.
  - Supports manual override via `layout.margin.{top,left,right,bottom}`.
- **Plot Dimensions:**
  - `plot_w = width - m_left - m_right`
  - `plot_h = height - m_top - m_bottom`
  - `cell_w = plot_w / N_x`
  - `cell_h = plot_h / N_y`
- **Cell Geometry:**
  - Border width: $1.0\,\text{px}$.
  - Inset rect: $x = \text{cellX} + 0.5$, $y = \text{cellY} + 0.5$, $w = \text{cell\_w} - 1.0$, $h = \text{cell\_h} - 1.0$.
  - Stroke: `#ffffff` for light theme, `#1e1e2f` for dark theme.

---

## 4. DOM Elements & CSS Classes

```xml
<g class="sc-series sc-series-heatmap" data-series="0" data-name="Sales">
  <rect class="sc-cell sc-point"
        data-series="0"
        data-series-name="Sales"
        data-x="Mon"
        data-y="142"
        data-cell-x="0"
        data-cell-y="1"
        data-value="142"
        data-color="#4eb3d3"
        x="120.5" y="80.5"
        width="44.0" height="24.0"
        fill="#4eb3d3"
        stroke="#ffffff"
        stroke-width="1"
        tabindex="0"
        aria-label="Auth, Mon: 142"/>
</g>
```

---

## 5. Semantic Invariants

1. **Parity:** Python and Go renderers produce byte-identical SVG across all valid specs and themes.
2. **Bounds Enforcement:** Non-integer coordinates, coordinates outside $[0, N-1]$, and non-finite values are rejected at validation time.
3. **Determinism:** Linear RGB stop interpolation and numeric string formatting (`fmt_num`) use exact rounding without floating-point drift.
4. **Accessibility:** Semantic HTML table generated in both languages faithfully represents the 2-D grid without value truncation.
