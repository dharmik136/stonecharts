---
id: PC-ARCH-007
title: Cartesian Substrate and Layout Roadmap
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: roadmap
requirements: [REQ-LAYOUT-001]
evidence: []
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Cartesian Substrate & Layout Reference

> **Location:** `docs/roadmap/cartesian_substrate.md`
> **Status:** Roadmap reference. Approved requirements, contracts, and ADRs take
> precedence over this document.

This document defines the coordinate space, grid layouts, scale projections, and accumulator pipelines shared by all Cartesian/XY chart types in PeakCharts (Line, Area, Column, Bar, Scatter, etc.).

---

## 1. Bounding Box & Margins

The Cartesian frame occupies a fixed `width` × `height` canvas. The inner plotting area (`plot_x`, `plot_y`, `plot_w`, `plot_h`) is calculated dynamically by reserving margins on each side:

```
+-------------------------------------------------------------+
|                                                             |
|                          Title                              |
|                         Subtitle                            |
|                                                             |
|          +---------------------------------------+          |
|          |                                       |          |
|          |                                       |          |
|  Y-Axis  |              Plot Area                |          |
|  Title   |                                       |          |
|          |                                       |          |
|          +---------------------------------------+          |
|                        X-Axis Labels                        |
|                                                             |
|                         X-Axis Title                        |
|                            Legend                           |
|                                                             |
+-------------------------------------------------------------+
```

### Margin Calculation Rules
*   **Top Margin (`mTop`):** Start at `20px`. Add `26px` if `title` is present. Add `18px` if `subtitle` is present.
*   **Left Margin (`mLeft`):** Defaults to `52px`. If `yAxis.title` is present, increase to `62px`.
*   **Right Margin (`mRight`):** Fixed at `22px`.
*   **Bottom Margin (`mBottom`):** Start at `46px`. Add `18px` if `legend` is enabled. Add `18px` if `xAxis.title` is present.

---

## 2. Coordinate Scales & Projections

All geometry coordinate generation uses float64 projection functions mapped on the plot bounds:

### 2.1 Value Axis (Y-Axis)
*   **Domain Range:** `[yMin, yMax]` calculated using the Heckbert `nice_ticks` algorithm covering the range of all data points (always including `0.0` unless overridden by `yAxis.min` or `yAxis.max`).
*   **Projection (`ypix`):** Maps a numeric value $v$ to a vertical pixel coordinate:
    $$\text{ypix}(v) = \text{plotY} + \text{plotH} \times \left(1 - \frac{v - y_{\min}}{y_{\max} - y_{\min}}\right)$$

### 2.2 Category Axis (X-Axis)
*   **Point Scale:** Projects category index $i$ to a discrete coordinate centered on the tick line. Used by Line/Area.
    $$\text{xpix}(i) = \text{plotX} + \frac{\text{plotW} \times i}{N - 1} \quad (\text{if } N > 1; \text{ else } \text{plotX} + \frac{\text{plotW}}{2})$$
*   **Band Scale:** Divides the plot width into equal categorical slots. Used by Column/Bar.
    $$\text{bandWidth} = \frac{\text{plotW}}{N}$$
    $$\text{bandCenter}(i) = \text{plotX} + \text{bandWidth} \times i + \frac{\text{bandWidth}}{2}$$

---

## 3. Stacking & Grouping Arithmetic

For grouped and stacked siblings, sub-bands and vertical accumulations are calculated deterministically to maintain strict cross-language ULP-for-ULP float parity.

### 3.1 Grouped Column Padding
*   Group Margin Padding ratio: `PAD = 0.2` (reserves 20% of the category slot for outer spacing).
*   Group Width: $W_{group} = \text{bandWidth} \times (1 - \text{PAD})$.
*   Number of series: $K = \text{len(series)}$.
*   Individual Bar Width: $W_{bar} = W_{group} / K$.
*   Left edge of series $k$ in category $i$:
    $$\text{left}(i, k) = \text{bandCenter}(i) - \frac{W_{group}}{2} + W_{bar} \times k$$

### 3.2 Stacked Accumulation
*   Series are accumulated in index order ($0 \dots S-1$).
*   For each category, the running positive and negative sums are tracked separately.
*   The frame y-domain `yMax` represents the maximum cumulative sum of any category stack.

---

## 4. Accumulator Injection Strategy

To prevent visual drift and ensure byte-identity by construction, renderers write into a single string accumulator injected through the layout pipeline:

1.  **Head Chrome (`_chrome_head`):** Outputs SVG root wrapper, accessibility `<desc>` and attributes, chart background, title, subtitle, Y-axis gridlines and labels, axis baseline, X-axis labels, and axis titles.
2.  **Marks Callback (`marks_fn`):** The chart renderer receives the frame and the accumulator, and appends only its series groups `<g class="pk-series">` and point marks.
3.  **Tail Chrome (`_chrome_tail`):** Outputs the legend, closes the SVG, and closes wrappers.
