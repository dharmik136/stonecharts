---
id: SC-ARCH-008
title: Matrix Substrate and Heatmap Architecture Specification
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: roadmap
requirements: [REQ-PROD-001, REQ-LAYOUT-001]
evidence: []
last_reviewed: "2026-08-11"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Family C: Matrix Substrate & Heatmap Architecture Specification

> **Location:** `docs/roadmap/matrix_substrate.md`  
> **Classification:** Informative architecture specification  
> **Authority:** Preceded by approved requirements, contracts, and ADRs per `SC-GOV-001`  
> **Status:** Proposed design opening Family C (Matrix / Grid) per `docs/roadmap/chart-families.md`

---

## 1. Executive Summary & Purpose

Family C (**Matrix / Grid**) addresses a fundamental visualization category distinct from Family A (Cartesian 1-D series on continuous/category axes) and Family B (Polar angle/radius coordinate systems). Instead of lines, bars, or arcs, Family C renders regular 2-D cell grids where values are encoded through color intensity on a continuous scale.

The canonical opener of Family C is the **Heatmap** (`"heatmap"`). In accordance with the StoneCharts governing rule (*"pay a family's foundation tax once, exhaust before opening another"* per `SC-ARCH-006` §1.4), the Heatmap introduces and pays the full foundation tax for the Matrix Substrate:

1. **Regular 2-D Cell Grid Layout Engine**: Categorical (row $\times$ column) and discrete binned coordinate mapping.
2. **Continuous Color Scale Engine**: Piecewise linear RGB interpolation supporting sequential, diverging, and custom stop ramps.
3. **Color-Axis (Gradient) Legend**: Continuous gradient bar with numerical ticks and labels, replacing discrete swatches.
4. **Accessible Matrix Representation**: WCAG 2.1 AA compliant semantic `<table>` with `<th scope="col">` and `<th scope="row">` headers.

Once the Matrix Substrate foundation tax is paid, subsequent Family C siblings (**Calendar heatmap**, **Tilemap**, **Hexbin / 2-D density**, **Allocation-over-time heatmap**, and **Latency heatmap**) reuse the coordinate space, color scale engine, gradient legend, and accessibility patterns with zero architectural duplication.

---

## 2. Taxonomy & Scope

Per `docs/roadmap/chart-families.md` §2 (Family C):

| Type | Class | Provenance | Description | Substrate Reuse |
|---|---|---|---|---|
| **Heatmap** | `new-family` | HC | 2-D categorical / discrete correlation and distribution grid | **Substrate opener** (pays foundation tax) |
| **Calendar heatmap** | `sibling` | PS | GitHub-style week $\times$ weekday activity grid | Matrix grid + date-to-cell projection |
| **Tilemap** | `sibling` | HC | Honeycomb, diamond, or square fleet/host grid | Matrix grid + alternative packings |
| **Hexbin / 2-D density** | `sibling` | PS | Aggregated 2-D scatter distributions | Numeric 2-D binning $\to$ Matrix color scale |
| **Allocation-over-time** | `sibling` | PS | Memory allocation buckets $\times$ wall-clock time | Time-binned Matrix grid |
| **Latency heatmap** | `sibling` | PS | Latency response buckets $\times$ wall-clock time (Gregg pulse) | Time-binned Matrix grid + multi-modal ramps |

---

## 3. Matrix Substrate Architecture

### 3.1 Bounding Box, Margins & Coordinate System

The Matrix frame occupies a fixed canvas (`width` $\times$ `height`). Plot boundaries (`plot_x`, `plot_y`, `plot_w`, `plot_h`) are calculated identically to Cartesian layout, reserving margins for title, subtitle, axis labels, and the color-axis legend:

```
+-------------------------------------------------------------+
|                                                             |
|                          Title                              |
|                         Subtitle                            |
|                                                             |
|          +---------------------------------------+          |
|          | (0, ny-1)                  (nx-1,ny-1)|          |
|  Y-Axis  |                                       |          |
|  Labels  |               Cell Grid               |          |
|  & Title |                                       |          |
|          | (0, 0)                     (nx-1, 0)  |          |
|          +---------------------------------------+          |
|                        X-Axis Labels                        |
|                         X-Axis Title                        |
|                                                             |
|              [=== Color-Axis Gradient Legend ===]           |
|                                                             |
+-------------------------------------------------------------+
```

#### Margin Computation Rules
* **Top Margin (`mTop`):** Default `20px` + `26px` (if title present) + `18px` (if subtitle present).
* **Left Margin (`mLeft`):** Calculated dynamically based on maximum category string length: `max(52px, max_y_label_len * 7.5 + 24px)`.
* **Right Margin (`mRight`):** Fixed at `24px` (or `60px` if vertical color-axis legend is positioned on the right).
* **Bottom Margin (`mBottom`):** Default `46px` + `18px` (if X-axis title present) + `36px` (if horizontal color-axis legend present).
* **Margin Overrides:** Supports manual `layout.margin.{top,left,right,bottom}` overrides per `REQ-LAYOUT-001`.

### 3.2 Discrete Grid Projection

Given $N_x = \text{len}(\text{xAxis.categories})$ columns and $N_y = \text{len}(\text{yAxis.categories})$ rows:

1. **Cell Dimensions:**
   $$\text{cellW} = \frac{\text{plotW}}{N_x}, \quad \text{cellH} = \frac{\text{plotH}}{N_y}$$

2. **Cell Position (Column $i \in [0, N_x-1]$, Row $j \in [0, N_y-1]$):**
   * Default matrix layout (top-down row index $j=0$ at top):
     $$\text{cellX}(i) = \text{plotX} + i \times \text{cellW}$$
     $$\text{cellY}(j) = \text{plotY} + j \times \text{cellH}$$
   * Cartesian mode (bottom-up row index $j=0$ at bottom):
     $$\text{cellY}(j) = \text{plotY} + (N_y - 1 - j) \times \text{cellH}$$

3. **Cell Border & Inset:**
   * Cells render as SVG `<rect>` elements.
   * `borderWidth`: default `1.0px`.
   * Cell rect geometry: `x = cellX + borderWidth/2`, `y = cellY + borderWidth/2`, `width = cellW - borderWidth`, `height = cellH - borderWidth`.
   * Border stroke color: `#ffffff` for light theme, `#1e1e2f` for dark theme.

---

## 4. Continuous Color Scale Engine

Unlike categorical palettes that assign distinct colors to series names, the Matrix substrate requires a continuous mapping from numeric values $v \in [\text{min}, \text{max}]$ to RGB hex colors.

### 4.1 ColorAxis Specification Contract

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

### 4.2 Interpolation Arithmetic

1. **Domain Resolution:**
   * If `colorAxis.min` or `colorAxis.max` are omitted, they are inferred from the minimum and maximum finite cell values in `series[].data`.
   * If $\text{max} \le \text{min}$, a degenerate normalized ratio $t = 0.5$ is assigned to all finite points.

2. **Normalized Scalar ($t$):**
   $$t = \text{clamp}\left(\frac{v - \text{min}}{\text{max} - \text{min}}, 0.0, 1.0\right)$$
   If `colorAxis.reversed` is true: $t \leftarrow 1.0 - t$.

3. **Piecewise Multi-Stop Interpolation:**
   Given sorted stops $(s_0, C_0), (s_1, C_1), \dots, (s_m, C_m)$ with $s_0 = 0.0$ and $s_m = 1.0$:
   * Find interval $k$ such that $s_k \le t \le s_{k+1}$.
   * Local ratio:
     $$u = \frac{t - s_k}{s_{k+1} - s_k} \quad (\text{if } s_{k+1} > s_k \text{ else } 0.0)$$
   * Interpolate RGB channels linearly (with deterministic integer rounding):
     $$R = \text{round}\left((1 - u) R_k + u R_{k+1}\right)$$
     $$G = \text{round}\left((1 - u) G_k + u G_{k+1}\right)$$
     $$B = \text{round}\left((1 - u) B_k + u B_{k+1}\right)$$
   * Format as `#rrggbb` 7-character lowercase hexadecimal string.

---

## 5. Color-Axis Gradient Legend

The color-axis legend provides visual calibration for the heatmap values.

### 5.1 SVG Construction

1. **`<defs>` LinearGradient:**
   * A unique `<linearGradient id="sc-color-axis-gradient-{id}" x1="0%" y1="0%" x2="100%" y2="0%">` is emitted in `<defs>`.
   * Each stop from `colorAxis.stops` is written as `<stop offset="{stop*100}%" stop-color="{color}"/>`.

2. **Gradient Bar:**
   * Emitted as `<rect class="sc-color-axis-bar" x="{lx}" y="{ly}" width="{lw}" height="12" fill="url(#...)" stroke="#cccccc" stroke-width="0.5"/>`.
   * Standard width: `lw = min(plotW * 0.6, 240px)`. Centered horizontally below X-axis labels.

3. **Tick Marks & Numerical Labels:**
   * Tick positions at $t \in [0.0, 0.25, 0.5, 0.75, 1.0]$ with corresponding data values:
     $$v_t = \text{min} + t \times (\text{max} - \text{min})$$
   * Value formatted via `fmt_num(v_t)`.
   * Labels rendered with `class="sc-color-axis-label"`, `font-size="10"`, `text-anchor="middle"`.

---

## 6. Document Object Model (DOM) & Class Contracts

To ensure DOM compatibility with the StoneCharts test harnesses, browser qualification suites, and WCAG auditors, the rendered SVG strictly adheres to:

```xml
<g class="sc-series sc-series-heatmap" data-name="Latency">
  <!-- Cell marks -->
  <rect class="sc-cell sc-point"
        x="120.0" y="80.0"
        width="45.0" height="25.0"
        fill="#4eb3d3"
        stroke="#ffffff"
        stroke-width="1"
        data-x="0"
        data-y="1"
        data-value="142.0"
        tabindex="0"
        aria-label="Auth, 04:00: 142.0 ms"/>
  ...
</g>

<!-- Color-axis legend -->
<g class="sc-legend sc-color-axis" role="region" aria-label="Color Scale Legend">
  <rect class="sc-color-axis-bar" .../>
  <text class="sc-color-axis-label" ...>10</text>
  <text class="sc-color-axis-label" ...>255</text>
  <text class="sc-color-axis-label" ...>500</text>
</g>
```

---

## 7. Accessibility Contract (WCAG 2.1 AA)

In adherence to `docs/contracts/accessibility.md` (`SC-CON-003`):

1. **Non-Visual Equivalent (`aria-hidden="false"` data table):**
   A visually hidden semantic HTML `<table>` is emitted within `<foreignObject>` or adjacent companion markup:
   ```html
   <table class="sc-a11y-table" aria-label="Service Latency Heatmap">
     <caption>Service Latency Heatmap: p95 response time (ms) by endpoint and hour of day</caption>
     <thead>
       <tr>
         <th scope="col">Service Endpoint</th>
         <th scope="col">00:00</th>
         <th scope="col">04:00</th>
         <th scope="col">08:00</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <th scope="row">Auth</th>
         <td>24.5</td>
         <td>142.0</td>
         <td>88.1</td>
       </tr>
     </tbody>
   </table>
   ```

2. **Color Blindness & Contrast Ratios:**
   * Palette presets MUST satisfy minimum 3:1 contrast against adjacent cell borders.
   * Diverging ramps (e.g., Blue-White-Orange or Purple-White-Green) provide deuteranopia/protanopia safety compared to Red-Green ramps.

---

## 8. Performance Budgets & Engineering Limits

* **Maximum Cells:** $10,000$ cells per chart instance (e.g., $100 \times 100$ or $365 \times 24$). Exceeding $10,000$ triggers `SpecError("maximum cell limit exceeded")`.
* **Renderer Execution Time:** $< 25\,\text{ms}$ (Python) and $< 5\,\text{ms}$ (Go) for a $50 \times 50$ (2,500 cells) grid.
* **Peak Memory Allocation:** $< 12\,\text{MB}$ during SVG string synthesis.
* **Deterministic Byte-Identity:** Float coordinates and RGB hex values use canonical precision (`fmt_num` formatting, 2 decimal places for pixels, uppercase/lowercase consistency) guaranteeing byte-exact parity between Python and Go.

---

## 9. Admission & Implementation Plan

Per `SC-ARCH-011` (Chart Admission Checklist):

1. **Phase 0 (Decision Gate):**
   * Register `DEC-061` in `docs/project/decisions.md` approving Family C Matrix Substrate and Heatmap admission.
   * Add `REQ-HEATMAP-001` to `docs/requirements/registry.yaml`.
   * Set target release (e.g., `0.0.0.35`).
2. **Phase 1 (Design):**
   * Completed by this document (`SC-ARCH-008`).
3. **Phase 2 (Contract & Schema):**
   * Add `"heatmap"` to `spec/chart-spec.schema.json` with `colorAxis` and 2-D categorical `xAxis`/`yAxis` validation.
   * Update `spec/svg-contract.md` to specify `.sc-cell` and `.sc-color-axis`.
4. **Phase 3 (Dual-Language Implementation & Goldens):**
   * Implement matrix substrate and heatmap renderer in `libs/python/stonecharts/charts/heatmap.py`.
   * Implement matrix substrate and heatmap renderer in `libs/go/heatmap.go`.
   * Generate 5 golden fixture SVGs verifying 100% byte-exact parity.
5. **Phase 4 & 5 (Verification, Fuzzing & Admission):**
   * Run full cross-language parity harness, property-based fuzzing, and StoneVerify qualification.
