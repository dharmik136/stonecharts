---
id: SC-ARCH-014
title: Geographic Substrate and Choropleth Architecture Specification
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

# Family G: Geographic Substrate & Choropleth Architecture Specification

> **Location:** `docs/roadmap/geo_substrate.md`  
> **Classification:** Informative architecture specification  
> **Authority:** Preceded by approved requirements, contracts, and ADRs per `SC-GOV-001`  
> **Status:** Proposed design opening Family G (Geo) per `docs/roadmap/chart-families.md`

---

## 1. Executive Summary & Purpose

Family G (**Geo**) renders spatial and cartographic data by projecting spherical coordinates (longitude $\lambda$, latitude $\phi$) onto a planar 2-D SVG canvas. While Cartesian plots (Family A) map abstract values to orthogonal axes, the Geo substrate operates on spherical trigonometry, map projections, and topological polygon enclosures.

The canonical opener of Family G is the **Choropleth map** (`"choropleth"`). In accordance with the StoneCharts governing rule (*"pay a family's foundation tax once, exhaust before opening another"* per `SC-ARCH-006` §1.4), Choropleth introduces and pays the full foundation tax for the Geographic Substrate:

1. **Planar Map Projections**: Deterministic implementations of Equirectangular, Mercator, and Albers Equal-Area projections.
2. **GeoJSON Polygon Ingestion**: MultiPolygon parsing, bounding box clipping, and coordinate-to-pixel projection.
3. **Region Fill & Color Quantization**: Reuses the Family C continuous and quantized color scale engine (`SC-ARCH-008`).
4. **Accessible Geographic Representation**: WCAG 2.1 AA compliant tabular listing with ISO 3166 codes, region names, and metric values.

Once this foundation tax is paid, subsequent Family G siblings (**Map bubble**, **Map point / marker map**, **Flow / connection map**, **Map line**, and **Tile-grid cartogram**) directly reuse the projection pipeline, coordinate transformations, and spatial bounds.

---

## 2. Taxonomy & Scope

Per `docs/roadmap/chart-families.md` §2 (Family G):

| Type | Class | Provenance | Description | Substrate Reuse |
|---|---|---|---|---|
| **Choropleth** | `new-family` | HC | Continuous / quantized color shading of geographic regions | **Substrate opener** (pays foundation tax) |
| **Map bubble** | `sibling` | HC | Sized circles anchored to geographic coordinates | Projection + Family A bubble mark |
| **Map point / marker** | `sibling` | HC | Point symbols and markers anchored to lat/lon | Projection + Family A scatter marker |
| **Flow / connection map** | `sibling` | HC | Great-circle curved routes between geographic endpoints | Projection + Family E Bézier ribbon |
| **Map line** | `sibling` | HC | Infrastructure routes, pipelines, and administrative borders | Projection + path polyline |
| **Geo heatmap** | `sibling` | HC | 2-D continuous density field over geographic coordinates | Projection + Family F 2-D contour |
| **Tile-grid map** | `sibling` | EXT | Abstract hex or square region cartograms | Abstract coordinates + Family C tilemap |

---

## 3. Geographic Data Model & Invariants

### 3.1 Input Schema Contract

A choropleth specification binds regional metric data to geographic feature keys:

```json
{
  "type": "choropleth",
  "title": "Regional Cloud Latency",
  "subtitle": "Average p95 egress latency by AWS region",
  "geo": {
    "projection": "albers",
    "map": "us-states-10m"
  },
  "colorAxis": {
    "min": 15.0,
    "max": 85.0,
    "minColor": "#e0f3f8",
    "maxColor": "#084081"
  },
  "series": [
    {
      "name": "Egress Latency (ms)",
      "data": [
        { "code": "US-VA", "name": "us-east-1 (Virginia)", "value": 18.2 },
        { "code": "US-OH", "name": "us-east-2 (Ohio)", "value": 24.5 },
        { "code": "US-OR", "name": "us-west-2 (Oregon)", "value": 78.4 }
      ]
    }
  ]
}
```

### 3.2 Invariants & Offline Static Boundary

1. **Static Self-Containment**: No runtime tile fetching or external network queries are permitted. Map topology geometry is embedded in the spec or bundled in certified prebuilt offline schemas.
2. **Valid Coordinate Bounds**: Longitude $\lambda \in [-180.0, 180.0]$, Latitude $\phi \in [-90.0, 90.0]$. Out-of-bounds coordinates trigger `SpecError("invalid geographic coordinate")`.
3. **Missing Region Handling**: Regions defined in the map topology with no corresponding value in `series[].data` render using the theme's neutral background fill (`colorAxis.nullColor`, default `#f1f5f9`), not 0.0.

---

## 4. Map Projections & Coordinate Geometry

### 4.1 Projection Formulae

1. **Equirectangular (Plate Carrée):**
   $$x = \text{plotX} + \text{plotW} \times \left(\frac{\lambda - \lambda_0 + 180}{360}\right)$$
   $$y = \text{plotY} + \text{plotH} \times \left(\frac{90 - \phi}{180}\right)$$

2. **Mercator Projection:**
   $$x = R \cdot (\lambda - \lambda_0)$$
   $$y = R \cdot \ln\left(\tan\left(\frac{\pi}{4} + \frac{\phi}{2}\right)\right)$$
   where latitude is clamped to $\phi \in [-85.0511^{\circ}, 85.0511^{\circ}]$ to prevent infinite canvas divergence.

3. **Albers Equal-Area Conic:**
   Conic projection preserving area proportionality for regional and national exhibits (e.g. US, Europe).

### 4.2 Polygon Coordinate Transformation & SVG Path Synthesis

* Geometry objects (Polygons and MultiPolygons) contain coordinate rings $[[\lambda_0, \phi_0], [\lambda_1, \phi_1], \dots, [\lambda_0, \phi_0]]$.
* Each coordinate pair is projected to canvas space $(x, y)$.
* Path string format:
  `M x0 y0 L x1 y1 L x2 y2 ... Z`
* Multiple exterior and interior (donut hole) rings within one polygon are concatenated into a single `<path>` element using the SVG `evenodd` fill rule.

---

## 5. Document Object Model (DOM) & Class Contracts

```xml
<g class="sc-series sc-series-choropleth" data-name="Egress Latency (ms)">
  <!-- Regional feature path -->
  <path class="sc-region sc-point"
        d="M 320.5 140.2 L 345.1 142.0 ... Z"
        fill="#4eb3d3"
        stroke="#ffffff"
        stroke-width="0.75"
        data-code="US-VA"
        data-name="us-east-1 (Virginia)"
        data-value="18.2"
        tabindex="0"
        aria-label="us-east-1 (Virginia): 18.2 ms"/>
</g>

<!-- Shared Family C Color-Axis Legend -->
<g class="sc-legend sc-color-axis" role="region" aria-label="Color Scale Legend">
  ...
</g>
```

---

## 6. Accessibility Contract (WCAG 2.1 AA)

In adherence to `docs/contracts/accessibility.md` (`SC-CON-007`):

1. **Semantic Geographic Data Table:**
   Renderers embed a structured tabular non-visual equivalent:
   ```html
   <table class="sc-a11y-table" aria-label="Regional Cloud Latency">
     <caption>Average p95 egress latency by AWS region</caption>
     <thead>
       <tr>
         <th scope="col">Region Code</th>
         <th scope="col">Region Name</th>
         <th scope="col">Egress Latency (ms)</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <td>US-VA</td>
         <td>us-east-1 (Virginia)</td>
         <td>18.2</td>
       </tr>
       <tr>
         <td>US-OR</td>
         <td>us-west-2 (Oregon)</td>
         <td>78.4</td>
       </tr>
     </tbody>
   </table>
   ```

2. **Keyboard Navigation:**
   * Focus advances through populated regions in alphabetical code order.
   * Active region receives high-contrast focus ring (`stroke="#000000" stroke-width="2"`).

---

## 7. Performance Budgets & Limits

* **Polygon Ring Limits:** Up to $1,500$ distinct coordinate rings per chart instance. Exceeding triggers `SpecError("maximum geographic polygon complexity exceeded")`.
* **Renderer Execution Time:** $< 45\,\text{ms}$ in Python and $< 10\,\text{ms}$ in Go for full national map geometries.
* **Deterministic Float Parity:** Standardized spherical trigonometric approximations producing identical float results formatted via `fmt_num` with 2 decimal places.
