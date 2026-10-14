---
id: SC-ARCH-015
title: KPI and Single-Value Substrate Architecture Specification
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: roadmap
requirements: [REQ-PROD-001, REQ-LAYOUT-001]
evidence: []
last_reviewed: "2026-10-14"
review_due: "2027-01-14"
supersedes: null
superseded_by: null
---

# Family H: KPI & Single-Value Substrate Architecture Specification

> **Location:** `docs/roadmap/kpi_substrate.md`  
> **Classification:** Informative architecture specification  
> **Authority:** Preceded by approved requirements, contracts, and ADRs per `SC-GOV-001`  
> **Status:** Proposed design opening Family H (KPI / Single-Value) per `docs/roadmap/chart-families.md`

---

## 1. Executive Summary & Purpose

Family H (**KPI / Single-Value**) provides executive and operational dashboard indicators: headline numeric metrics, period-over-period deltas, inline micro-trends (sparklines, sparkbars), and linear progress gauges. Unlike coordinate-heavy charting families (Families A–G), Family H requires minimal coordinate projection and zero complex axis chrome.

In accordance with the StoneCharts taxonomy (`SC-ARCH-006` §2 Family H), the foundation tax for Family H is **near-zero**:
- **Sparkline** reuses the Family A Cartesian line renderer with all axis lines, labels, ticks, and legend disabled.
- **Sparkbar / Win-Loss** reuses the Family A Cartesian column renderer with chrome stripped.
- **Progress / Linear Gauge** reuses Cartesian floating-bar primitives.
- **Waffle / Unit Chart** reuses Family C categorical matrix cell packing.

The **Stat card** (`"stat-card"`) serves as the composite wrapper integrating typographic values, status badges, and inline sparkline trends.

---

## 2. Taxonomy & Scope

Per `docs/roadmap/chart-families.md` §2 (Family H):

| Type | Class | Provenance | Description | Substrate Reuse |
|---|---|---|---|---|
| **Number / Stat card** | `sibling` | EXT | Big numeric headline + delta badge + optional inline sparkline | Composite layout + Typography |
| **Sparkline** | `variant` | EXT | Tiny inline line chart without axes or labels | Family A Line (chrome disabled) |
| **Sparkbar / win-loss** | `variant` | EXT | Micro column/bar chart showing directional sign or counts | Family A Column (chrome disabled) |
| **Progress / linear gauge** | `sibling` | EXT | Single-bar progress track showing quota / capacity | Cartesian range bar |
| **Bullet graph** | `sibling` | HC | Actual value bar against target marker and qualitative bands | Already certified in Family A (`0.0.0.11`) |
| **Waffle / unit chart** | `sibling` | EXT | 10 $\times$ 10 or $N \times M$ grid of unit icons or squares | Family C Matrix cell layout |
| **KPI delta indicator** | `sibling` | EXT | Arrow glyph + percentage change badge | Typographic badge component |

---

## 3. Specification Schema & Data Formats

### 3.1 Stat Card Specification Contract

```json
{
  "type": "stat-card",
  "title": "API Error Budget Burn",
  "subtitle": "Current 30-day rolling window",
  "kpi": {
    "value": 14.2,
    "unit": "%",
    "precision": 1,
    "delta": {
      "value": -2.4,
      "unit": "pp",
      "direction": "down",
      "sentiment": "positive",
      "comparisonPeriod": "vs prior 30d"
    },
    "trend": {
      "type": "sparkline",
      "data": [18.5, 17.2, 16.8, 15.0, 14.8, 14.2],
      "stroke": "#10b981",
      "fill": "rgba(16, 185, 129, 0.15)"
    }
  }
}
```

### 3.2 Progress Gauge Specification Contract

```json
{
  "type": "progress-gauge",
  "title": "Storage Quota",
  "progress": {
    "current": 780.0,
    "max": 1000.0,
    "unit": "GB",
    "thresholds": [
      { "value": 750.0, "color": "#f59e0b" },
      { "value": 900.0, "color": "#ef4444" }
    ]
  }
}
```

---

## 4. Layout Architecture & Typography

The KPI frame occupies a compact bounding box (e.g., $240\text{px} \times 120\text{px}$ or $180\text{px} \times 80\text{px}$):

```
+-------------------------------------------------------+
|  Metric Title                                         |
|                                                       |
|  14.2%        [ v -2.4 pp vs prior 30d ]              |
|  (Headline)   (Delta Badge)                           |
|                                                       |
|  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   |
|  (Embedded Sparkline / Progress Bar)                  |
+-------------------------------------------------------+
```

### 4.1 Layout Dimensions
* **Headline Font Size:** `32px` (`font-weight="bold"`, tabular numbers).
* **Title Font Size:** `13px` (`font-weight="normal"`).
* **Delta Badge:** `12px` font with rounded rectangle background (`rx="4" ry="4"`).
  * Color coding: Green for positive sentiment, Red for negative sentiment, Gray for neutral.
* **Sparkline Height:** Fixed `24px` to `36px` along the bottom baseline.

---

## 5. Document Object Model (DOM) & Class Contracts

```xml
<g class="sc-kpi-card" role="group" aria-label="API Error Budget Burn: 14.2%, down 2.4 pp vs prior 30d">
  <!-- Title -->
  <text class="sc-kpi-title" x="16.0" y="24.0" font-size="13">API Error Budget Burn</text>
  
  <!-- Headline value -->
  <text class="sc-kpi-value" x="16.0" y="60.0" font-size="32" font-weight="bold">14.2%</text>
  
  <!-- Delta badge -->
  <g class="sc-kpi-delta sc-sentiment-positive" transform="translate(130.0, 42.0)">
    <rect class="sc-delta-bg" width="95.0" height="22.0" rx="4" fill="#ecfdf5"/>
    <text class="sc-delta-text" x="8.0" y="15.0" font-size="11" fill="#047857">▼ -2.4 pp</text>
  </g>
  
  <!-- Inline sparkline mark -->
  <path class="sc-sparkline-area" d="M 16.0 110.0 L ... Z" fill="rgba(16, 185, 129, 0.15)"/>
  <path class="sc-sparkline-line" d="M 16.0 95.0 L ... " fill="none" stroke="#10b981" stroke-width="2"/>
</g>
```

---

## 6. Accessibility Contract (WCAG 2.1 AA)

In adherence to `docs/contracts/accessibility.md` (`SC-CON-007`):

1. **Self-Descriptive Text Alternatives:**
   The entire KPI card is wrapped with an explicit `aria-label` synthesizing the full context:
   `aria-label="API Error Budget Burn: 14.2%, down 2.4 percentage points compared to prior 30 days. Trend is improving."`
2. **Accessible Numeric Summary:**
   Tabular numbers and direction arrows include non-symbol fallback text (e.g., `aria-hidden="true"` on the arrow glyph with screen-reader text `class="sr-only">Decreased by`).

---

## 7. Performance Budgets & Limits

* **Renderer Execution Time:** $< 5\,\text{ms}$ (Python) and $< 1\,\text{ms}$ (Go).
* **Peak Memory Footprint:** $< 1\,\text{MB}$.
* **Deterministic Byte Parity:** Strict identical string formatting for integer and floating-point numeric headlines.
