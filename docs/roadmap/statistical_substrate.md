---
id: SC-ARCH-013
title: Statistical Substrate and Violin Architecture Specification
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

# Family F: Statistical Substrate & Violin Architecture Specification

> **Location:** `docs/roadmap/statistical_substrate.md`  
> **Classification:** Informative architecture specification  
> **Authority:** Preceded by approved requirements, contracts, and ADRs per `SC-GOV-001`  
> **Status:** Proposed design opening Family F (Statistical / Distribution) per `docs/roadmap/chart-families.md`

---

## 1. Executive Summary & Purpose

Family F (**Statistical / Distribution**) visualizes probability densities, multi-modal spreads, and cumulative distributions synthesized from raw observations. While Boxplots and Histograms in Family A (Cartesian) plot pre-binned or 5-number summaries, Family F introduces statistical kernel synthesis that transforms raw sample arrays into continuous probability density functions (PDFs), mirrored violin profiles, ridgeline stacks, and 2-D contours.

The canonical opener of Family F is the **Violin plot** (`"violin"`). In accordance with the StoneCharts governing rule (*"pay a family's foundation tax once, exhaust before opening another"* per `SC-ARCH-006` §1.4), Violin introduces and pays the full foundation tax for the Statistical Substrate:

1. **Kernel Density Estimation (KDE) Engine**: Deterministic 1-D Gaussian kernel convolution with Silverman's rule-of-thumb bandwidth optimization.
2. **Mirrored Envelope Geometry**: Bi-lateral symmetrical SVG path construction with smooth cubic Bezier or Catmull-Rom splines.
3. **Integrated Quartile & Outlier Marks**: Mini-boxplot and median dot markers embedded within the density envelope.
4. **Accessible Distribution Contract**: WCAG 2.1 AA accessible summary table reporting min, quartiles, median, max, and primary density modes.

Once this foundation tax is paid, subsequent Family F siblings (**Ridgeline / joyplot**, **Density / KDE curve**, **2-D density / contour**, **Q-Q plot**, and **ECDF / cumulative**) reuse the KDE engine, bandwidth selectors, and statistical transforms with zero architectural duplication.

---

## 2. Taxonomy & Scope

Per `docs/roadmap/chart-families.md` §2 (Family F):

| Type | Class | Provenance | Description | Substrate Reuse |
|---|---|---|---|---|
| **Violin** | `new-family` | PS | Mirrored density envelope + embedded boxplot per category | **Substrate opener** (pays foundation tax) |
| **Ridgeline (joyplot)** | `sibling` | PS | Vertically staggered, partially overlapping KDE curves | 1-D KDE engine + area fill with vertical baseline offsets |
| **Density / KDE curve** | `sibling` | HC | Continuous probability density curve over Cartesian plane | 1-D KDE engine + single-line / filled area renderer |
| **2-D density / contour** | `sibling` | PS | Iso-density contours extracted via marching-squares | 2-D KDE grid + marching-squares isocontour extraction |
| **Q-Q plot** | `sibling` | PS | Empirical quantiles plotted against theoretical normal | Quantile transformation + Cartesian scatter & diagonal |
| **ECDF / cumulative** | `sibling` | PS | Empirical cumulative distribution step-function | Empirical sort + Cartesian step-after line |

---

## 3. Statistical Data Model & Invariants

### 3.1 Input Schema Contract

A violin chart consumes either raw numeric sample arrays or precomputed KDE density points:

```json
{
  "type": "violin",
  "title": "Service Latency Distribution",
  "subtitle": "Response time (ms) by endpoint with multi-modal spread",
  "xAxis": {
    "categories": ["Checkout", "Search", "Auth"]
  },
  "yAxis": {
    "title": "Response Time (ms)",
    "min": 0.0
  },
  "series": [
    {
      "name": "p95 Latency",
      "data": [
        {
          "category": "Checkout",
          "samples": [12.4, 14.1, 15.2, 18.0, 19.5, 42.1, 44.0, 45.2, 48.0]
        },
        {
          "category": "Search",
          "samples": [5.1, 6.2, 6.5, 7.0, 8.1, 9.2, 10.4]
        }
      ]
    }
  ],
  "violin": {
    "bandwidth": "silverman",
    "showBoxplot": true,
    "points": 50
  }
}
```

### 3.2 Statistical Invariants

1. **Finite Sample Arrays**: Every value in `samples` MUST be a finite number. Non-finite values (`null`, `NaN`, `Infinity`) are rejected before computation.
2. **Minimum Sample Size**: Each sample set MUST contain at least 4 observations to perform valid KDE estimation; fewer than 4 triggers `SpecError("insufficient sample size for KDE")`.
3. **Normalized Area Integration**: The estimated density integrates to 1.0 over the real domain:
   $$\int_{-\infty}^{\infty} \hat{f}(y)\,dy = 1.0$$

---

## 4. Kernel Density Estimation (KDE) Engine

### 4.1 Gaussian Kernel

Given $n$ observations $y_1, y_2, \dots, y_n$ with sample standard deviation $\sigma$ and interquartile range $\text{IQR}$:

1. **Bandwidth Selection (Silverman's Rule of Thumb):**
   $$A = \min\left(\sigma, \frac{\text{IQR}}{1.34}\right)$$
   $$h = 0.9 \times A \times n^{-1/5}$$
   If $A == 0.0$ (degenerate zero variance), $h = 1.0$.

2. **Density Estimator at evaluation point $y$:**
   $$\hat{f}(y) = \frac{1}{n \cdot h \cdot \sqrt{2\pi}} \sum_{i=1}^n \exp\left(-\frac{1}{2}\left(\frac{y - y_i}{h}\right)^2\right)$$

3. **Evaluation Grid:**
   The density is evaluated at $K = 50$ uniformly spaced intervals spanning $[y_{\min} - 3h, y_{\max} + 3h]$.

### 4.2 Mirrored Envelope Geometry

For category slot centered at $x_c$ with maximum allocated half-width $W_{\max} = \text{bandWidth} \times 0.4$:

1. Maximum density observed: $f_{\max} = \max_k \hat{f}(y_k)$.
2. Horizontal displacement for point $k$:
   $$w(k) = W_{\max} \times \frac{\hat{f}(y_k)}{f_{\max}}$$
3. Left and right coordinates:
   $$x_{\text{left}}(k) = x_c - w(k), \quad x_{\text{right}}(k) = x_c + w(k)$$
4. The violin path is assembled as a continuous closed SVG polygon or smooth spline:
   `M x_c y_min L ... (right path ascending) ... L x_c y_max L ... (left path descending) ... Z`.

---

## 5. Document Object Model (DOM) & Class Contracts

```xml
<g class="sc-series sc-series-violin" data-name="p95 Latency">
  <!-- Violin mark for category -->
  <g class="sc-violin-group" data-category="Checkout">
    <!-- Density envelope -->
    <path class="sc-violin-envelope sc-point"
          d="M 150.0 320.0 C 175.0 280.0 ... Z"
          fill="#3b82f6"
          fill-opacity="0.35"
          stroke="#2563eb"
          stroke-width="1.5"
          tabindex="0"
          aria-label="Checkout: median 19.5 ms, bimodal density"/>

    <!-- Embedded boxplot marker -->
    <line class="sc-violin-whisker" x1="150.0" y1="310.0" x2="150.0" y2="90.0" stroke="#1e293b" stroke-width="1.5"/>
    <rect class="sc-violin-box" x="146.0" y="180.0" width="8.0" height="90.0" fill="#1e293b"/>
    <circle class="sc-violin-median" cx="150.0" cy="225.0" r="3.0" fill="#ffffff"/>
  </g>
</g>
```

---

## 6. Accessibility Contract (WCAG 2.1 AA)

In adherence to `docs/contracts/accessibility.md` (`SC-CON-007`):

1. **Parametric & Non-Parametric Summary Table:**
   Renderers embed a descriptive table presenting the distribution characteristics:
   ```html
   <table class="sc-a11y-table" aria-label="Service Latency Distribution">
     <caption>Summary statistics and density modes for latency observations</caption>
     <thead>
       <tr>
         <th scope="col">Endpoint</th>
         <th scope="col">Samples</th>
         <th scope="col">Min</th>
         <th scope="col">p25</th>
         <th scope="col">Median</th>
         <th scope="col">p75</th>
         <th scope="col">Max</th>
         <th scope="col">Modal Peak</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <th scope="row">Checkout</th>
         <td>9</td>
         <td>12.4</td>
         <td>15.2</td>
         <td>19.5</td>
         <td>44.0</td>
         <td>48.0</td>
         <td>18.0 ms (Primary), 44.5 ms (Secondary)</td>
       </tr>
     </tbody>
   </table>
   ```

---

## 7. Performance Budgets & Limits

* **Sample Complexity:** Up to $50,000$ raw samples across all categories. Beyond $50,000$ triggers `SpecError("maximum sample count exceeded")`.
* **Renderer Execution Time:** $< 30\,\text{ms}$ (Python) and $< 6\,\text{ms}$ (Go) for 10 categories $\times$ 500 samples (5,000 total points).
* **Deterministic ULP Parity:** Gaussian evaluation $\exp(-0.5 \cdot z^2)$ uses standard IEEE-754 float64 math; outputs formatted via `fmt_num` with 2 decimal places ensuring bit-identical SVG paths across Python and Go.
