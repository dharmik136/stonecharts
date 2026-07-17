---
id: PC-CON-003
title: PeakCharts SVG DOM Contract
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-DET-001, REQ-RUNTIME-001, REQ-A11Y-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-RUNTIME-BROWSER]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# SVG DOM Contract

The shared interaction runtime (`runtime/chart-interactions.js`) enhances any SVG
that follows this contract. **Every language renderer must emit this structure**
so one runtime works everywhere. The SVG is fully valid and visible without JS;
the runtime only adds interactivity on top.

## Required structure

```html
<div class="pk-chart-wrap">           <!-- positioning context for the tooltip -->
  <svg class="pk-chart" ...>
    ...
    <line class="pk-crosshair" style="display:none" .../>   <!-- optional -->

    <g class="pk-series" data-series="0">                   <!-- one per series -->
      <path class="pk-series-line" data-series="0" d="..." stroke="COLOR" .../>
      <circle class="pk-point" data-series="0"
              data-series-name="Tokyo" data-x="Jan" data-y="7"
              data-color="COLOR" data-r="3.5" data-r-hover="6"
              cx=".." cy=".." r="3.5" .../>
      ...
    </g>

    <g class="pk-legend">
      <g class="pk-legend-item" data-series="0"> ...swatch + label... </g>
      ...
    </g>
  </svg>
  <div class="pk-tooltip" style="display:none"></div>       <!-- runtime fills this -->
</div>
```

## Contract elements

| Selector | Purpose | Runtime behavior |
|----------|---------|------------------|
| `.pk-chart-wrap` | Positioning context | Holds the absolutely-positioned `.pk-tooltip` |
| `svg.pk-chart` | The chart root | `PeakCharts.init()` scans for these |
| `.pk-series[data-series=N]` | Group for series N (line + points) | Legend toggle shows/hides the whole group |
| `.pk-point` | A data point | Hover → tooltip + enlarge to `data-r-hover`; leave → back to `data-r` |
| `.pk-legend-item[data-series=N]` | Legend entry for series N | Click → toggle every `[data-series=N]` (adds `.pk-hidden`) |
| `.pk-crosshair` | Vertical guide line (optional) | Shown at the hovered point's `cx`, hidden on leave |
| `.pk-tooltip` | Floating tooltip (optional; runtime creates if absent) | Filled from `data-x` / `data-series-name` / `data-y` / `data-color` |

## Required `data-*` on `.pk-point`

| Attr | Meaning |
|------|---------|
| `data-series` | Series index (string int) |
| `data-series-name` | Series display name (tooltip) |
| `data-x` | X label/value (tooltip title) |
| `data-y` | Y value (tooltip body) |
| `data-color` | Series color (tooltip dot) |
| `data-r` / `data-r-hover` | Base and hover radius |

## Rules

1. `data-series` values are consistent across the series group, its points, and
   its legend item — that string is the join key for show/hide.
2. Anything the runtime toggles must live under a `[data-series=N]` element.
3. Coordinates are plain SVG user units; no assumption about viewBox scaling.
4. The chart must be correct and readable with JavaScript disabled.
