---
id: SC-ARCH-012
title: Flow Substrate and Sankey Architecture Specification
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

# Family E: Flow Substrate & Sankey Architecture Specification

> **Location:** `docs/roadmap/flow_substrate.md`  
> **Classification:** Informative architecture specification  
> **Authority:** Preceded by approved requirements, contracts, and ADRs per `SC-GOV-001`  
> **Status:** Proposed design opening Family E (Flow / Relational) per `docs/roadmap/chart-families.md`

---

## 1. Executive Summary & Purpose

Family E (**Flow / Relational**) visualizes networks of entities (nodes) connected by directional or non-directional relationships (links), where link weights encode throughput, byte volume, financial transfers, or dependency strengths. Unlike Cartesian grids (Family A), Polar arcs (Family B), or regular matrices (Family C), the Flow substrate operates on topological graph representations and continuous Bézier ribbon geometries.

The canonical opener of Family E is the **Sankey diagram** (`"sankey"`). In accordance with the StoneCharts governing rule (*"pay a family's foundation tax once, exhaust before opening another"* per `SC-ARCH-006` §1.4), Sankey introduces and pays the foundational investment for the entire Flow family:

1. **Topological Graph Model**: Node-link data parser, link weight validation, degree calculation, and flow conservation checks.
2. **Layering & Crossing-Minimization Engine**: Deterministic topological layering (longest-path ranking) and barycentric node reordering.
3. **Cubic Bézier Ribbon Geometry Engine**: Analytical calculation of parallel curved ribbon contours with variable source/target cross-sections.
4. **Accessible Network Representation**: WCAG 2.1 AA compliant tabular step-flow and adjacency representation for screen readers.

Once the Flow Substrate foundation tax is paid, subsequent Family E siblings (**Dependency wheel**, **Chord diagram**, **Network graph**, **Arc diagram**, **Packed bubble**, **Venn / Euler**, and **Word cloud**) reuse the graph data structures, link path generators, and accessibility models.

---

## 2. Taxonomy & Scope

Per `docs/roadmap/chart-families.md` §2 (Family E):

| Type | Class | Provenance | Description | Substrate Reuse |
|---|---|---|---|---|
| **Sankey** | `new-family` | HC | Multi-stage directional flow ribbons between ranked columns | **Substrate opener** (pays foundation tax) |
| **Dependency wheel** | `sibling` | HC | Circular Sankey (nodes arranged radially on a perimeter) | Flow graph + Polar node placement + internal ribbons |
| **Chord diagram** | `sibling` | PS | Symmetric service-to-service call matrix ribbons | Adjacency matrix $\to$ circular arcs + bi-directional ribbons |
| **Network graph** | `sibling` | HC | Force-directed service topology and dependency graph | Flow graph + iterative spring-electrical simulation |
| **Arc diagram** | `sibling` | HC | 1-D linear node alignment with semicircular link arcs | 1-D coordinate line + arc paths |
| **Packed bubble** | `sibling` | HC | Node-only circles sized by value with collision packing | Force simulation collision engine (no links) |
| **Venn / Euler** | `sibling` | HC | Proportional set-intersection areas | Set membership logic + circle-circle intersection geometry |
| **Word cloud** | `sibling` | HC | Hierarchical/frequency glyph packing | Archimedean spiral layout (own mini-foundation) |

---

## 3. Flow Data Model & Invariants

### 3.1 Input Schema Contract

A flow specification defines distinct `nodes` (entities) and directed `links` (connections):

```json
{
  "type": "sankey",
  "title": "API Gateway Request Routing",
  "subtitle": "Hourly request volume from Edge to Microservices",
  "series": [
    {
      "name": "Requests",
      "nodes": [
        { "id": "edge", "name": "Cloudflare Edge" },
        { "id": "gw", "name": "API Gateway" },
        { "id": "auth", "name": "Auth Service" },
        { "id": "billing", "name": "Billing Service" },
        { "id": "catalog", "name": "Catalog Service" }
      ],
      "data": [
        { "from": "edge", "to": "gw", "weight": 50000 },
        { "from": "gw", "to": "auth", "weight": 15000 },
        { "from": "gw", "to": "billing", "weight": 10000 },
        { "from": "gw", "to": "catalog", "weight": 25000 }
      ]
    }
  ]
}
```

### 3.2 Graph Normalization & Validation Invariants

1. **Node Identity**: Every node MUST possess a unique string `id`. Links reference existing `id`s in `from` (`source`) and `to` (`target`). Missing references trigger `SpecError("dangling link reference")`.
2. **Positive Finite Weights**: Link `weight` MUST be a finite number $> 0.0$. Negative or zero weights are strictly rejected.
3. **Self-Links**: A link where `from == to` is rejected in acyclic Sankey layouts.
4. **Node Flow Conservation**: For each intermediate node:
   $$\text{flow}_{\text{in}} = \sum_{e \in \text{in}(u)} \text{weight}(e), \quad \text{flow}_{\text{out}} = \sum_{e \in \text{out}(u)} \text{weight}(e)$$
   Effective node value: $V(u) = \max(\text{flow}_{\text{in}}, \text{flow}_{\text{out}})$.

---

## 4. Sankey Layout & Geometry Engine

### 4.1 Layer Assignment (Rank Allocation)

1. Compute topological depths using longest-path ranking:
   $$\text{layer}(u) = 0 \quad \text{if } \text{in}(u) = \emptyset; \quad \text{layer}(v) = \max_{(u, v) \in E} (\text{layer}(u) + 1)$$
2. Column horizontal coordinates:
   $$N_{\text{layers}} = \max(\text{layer}) + 1, \quad x(L) = \text{plotX} + L \times \frac{\text{plotW} - \text{nodeWidth}}{N_{\text{layers}} - 1}$$
   Standard node thickness: `nodeWidth = 16px`.

### 4.2 Vertical Positioning & Barycentric Crossing Minimization

1. Within each layer, nodes are ordered to minimize ribbon crossings using 4 iterations of the alternating **Barycenter heuristic**:
   $$\text{barycenter}(v) = \frac{\sum_{(u, v) \in E} y(u) \cdot \text{weight}(u, v)}{\sum_{(u, v) \in E} \text{weight}(u, v)}$$
2. Total layer height is calculated with uniform vertical padding (`nodePadding = 12px`):
   $$H(L) = \sum_{u \in L} h(u) + (|L| - 1) \times \text{nodePadding}$$
3. Nodes are centered vertically within `plotH`.

### 4.3 Cubic Bézier Ribbon Geometry

Each directed link between node $A$ at $(x_A, y_A)$ and node $B$ at $(x_B, y_B)$ with ribbon height $h$ is defined by a closed SVG `<path>` with two opposing cubic Bézier curves:

```
  (x0, y0_top) ------------ C(cp1, cp2) ------------> (x1, y1_top)
       |                                                    |
     [Node A]                                            [Node B]
       |                                                    |
  (x0, y0_bot) <----------- C(cp4, cp3) ------------ (x1, y1_bot)
```

1. Control point curvature parameter: $dx = (x_1 - x_0) \times 0.5$.
2. Top boundary curve:
   $$\mathbf{P}_{\text{top}}(t) = \text{CubicBezier}\left((x_0, y_{0,\text{top}}), (x_0 + dx, y_{0,\text{top}}), (x_1 - dx, y_{1,\text{top}}), (x_1, y_{1,\text{top}})\right)$$
3. Bottom boundary curve:
   $$\mathbf{P}_{\text{bot}}(t) = \text{CubicBezier}\left((x_1, y_{1,\text{bot}}), (x_1 - dx, y_{1,\text{bot}}), (x_0 + dx, y_{0,\text{bot}}), (x_0, y_{0,\text{bot}})\right)$$
4. Closed path command: `M x0 y0_top C ... L x1 y1_bot C ... Z`.

---

## 5. Document Object Model (DOM) & Class Contracts

```xml
<g class="sc-series sc-series-sankey" data-name="Requests">
  <!-- Directed links -->
  <g class="sc-links" role="group" aria-label="Flow links">
    <path class="sc-link"
          d="M 120.0 80.0 C 180.0 80.0 180.0 140.0 240.0 140.0 L 240.0 165.0 C 180.0 165.0 180.0 105.0 120.0 105.0 Z"
          fill="#3b82f6"
          fill-opacity="0.45"
          data-from="edge"
          data-to="gw"
          data-weight="50000"
          tabindex="0"
          aria-label="Cloudflare Edge to API Gateway: 50,000 requests"/>
  </g>

  <!-- Flow nodes -->
  <g class="sc-nodes" role="group" aria-label="Flow nodes">
    <rect class="sc-node sc-point"
          x="104.0" y="70.0"
          width="16.0" height="120.0"
          fill="#2563eb"
          stroke="#ffffff"
          stroke-width="1"
          data-id="edge"
          data-name="Cloudflare Edge"
          data-value="50000"
          tabindex="0"
          aria-label="Cloudflare Edge: 50,000 total volume"/>
    <text class="sc-node-label" x="98.0" y="130.0" text-anchor="end" font-size="11">Cloudflare Edge</text>
  </g>
</g>
```

---

## 6. Accessibility Contract (WCAG 2.1 AA)

In adherence to `docs/contracts/accessibility.md` (`SC-CON-007`):

1. **Step-by-Step Flow Table Companion:**
   An accessible HTML table describes transitions:
   ```html
   <table class="sc-a11y-table" aria-label="API Gateway Request Routing">
     <caption>Flow pathways and throughput values</caption>
     <thead>
       <tr>
         <th scope="col">Source</th>
         <th scope="col">Target</th>
         <th scope="col">Flow Volume</th>
         <th scope="col">% of Source</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <td>Cloudflare Edge</td>
         <td>API Gateway</td>
         <td>50,000</td>
         <td>100.0%</td>
       </tr>
       <tr>
         <td>API Gateway</td>
         <td>Catalog Service</td>
         <td>25,000</td>
         <td>50.0%</td>
       </tr>
     </tbody>
   </table>
   ```

2. **Keyboard Focus & Traversal:**
   * `Tab`: Advances focus sequentially through ranked nodes, then through links.
   * On link focus: Highlights connected source and target nodes with high-contrast outlines.

---

## 7. Performance Budgets & Limits

* **Graph Complexity Limits:** Up to 500 nodes and 2,000 links per chart instance. Exceeding either limit triggers `SpecError("maximum network complexity exceeded")`.
* **Renderer Execution Time:** $< 40\,\text{ms}$ (Python) and $< 10\,\text{ms}$ (Go) for a 100-node, 250-link Sankey diagram.
* **Deterministic Parity:** Float coordinates for Bézier control points use `fmt_num` with 2 decimal places, ensuring byte-identical SVG outputs across Python and Go.
