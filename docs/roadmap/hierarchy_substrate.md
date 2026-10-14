---
id: SC-ARCH-009
title: Hierarchy Substrate and Treemap Architecture Specification
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

# Family D: Hierarchy Substrate & Treemap Architecture Specification

> **Location:** `docs/roadmap/hierarchy_substrate.md`  
> **Classification:** Informative architecture specification  
> **Authority:** Preceded by approved requirements, contracts, and ADRs per `SC-GOV-001`  
> **Status:** Proposed design opening Family D (Hierarchy) per `docs/roadmap/chart-families.md`

---

## 1. Executive Summary & Purpose

Family D (**Hierarchy**) models nested parent-child data structures where quantitative values aggregate from leaf nodes to branch ancestors. Unlike Cartesian plots (Family A), Polar arcs (Family B), or regular 2-D categorical grids (Family C), the Hierarchy substrate operates on space-filling tessellations and recursive coordinate subdivisions.

The opening chart type of Family D is the **Treemap** (`"treemap"`). In accordance with the StoneCharts governing rule (*"pay a family's foundation tax once, exhaust before opening another"* per `SC-ARCH-006` §1.4), Treemap introduces and pays the full foundation tax for the Hierarchy Substrate:

1. **Tree Data Structure & Value Aggregation**: Strict acyclic node-link tree parser, ID-to-parent indexer, and self+children value rollups.
2. **Squarified Tessellation Engine**: Deterministic implementation of the Bruls–Huizing–van Wijk squarified layout minimizing aspect ratio distortion.
3. **Multi-Level Container Geometry**: Inner padding, header bands for non-leaf branches, and depth-based hierarchical clipping.
4. **Hierarchical Navigation & Breadcrumb Contract**: State-model for zoom-into-subtree transitions and ancestor trail presentation.
5. **Screen-Reader Nested Outline Contract**: WCAG 2.1 AA accessible representation using nested hierarchical HTML lists (`<ol class="sc-hierarchy-tree">`).

Once this foundation tax is paid, subsequent Family D siblings (**Sunburst**, **Icicle / partition**, **Aggregated Flame Graph**, **Dendrogram / cluster tree**, and **Circle packing**) directly reuse the tree aggregation engine, color inheritance models, and accessibility structures.

---

## 2. Audited Taxonomy & Family Roadmap

Per `docs/roadmap/chart-families.md` §2 (Family D):

| Type | Class | Provenance | Description | Substrate Reuse |
|---|---|---|---|---|
| **Treemap** | `new-family` | HC | Squarified recursive rectangular enclosure | **Substrate opener** (pays foundation tax) |
| **Sunburst** | `sibling` | HC | Radial multi-level partition | Hierarchy tree + Polar arc geometry |
| **Icicle / partition** | `sibling` | PS | Rectangular partition with depth-axis alignment | Hierarchy tree + depth-lane linear layout |
| **Flame graph (aggregated)** | `sibling` | PS | CPU/allocation call-stack profile (width = total samples) | Icicle partition + profiler search/diff |
| **Dendrogram / cluster tree** | `sibling` | HC | Node-link tidy tree (Reingold–Tilford) | Hierarchy tree + tree-graph edge routing |
| **Circle packing** | `sibling` | EXT | Nested circular enclosure | Hierarchy tree + circle-tangency packing |
| **Organization chart** | `sibling` | HC | Card-based management hierarchy | Node-link layout + card mark |

---

## 3. Hierarchy Data Model & Aggregation Pipeline

### 3.1 Input Schema Contract

Hierarchy data is specified either as an explicit node array with parent pointers or as a recursive nested object.

```json
{
  "type": "treemap",
  "title": "Disk Space Utilization",
  "subtitle": "Storage by top-level package and module",
  "series": [
    {
      "name": "Storage",
      "data": [
        { "id": "root", "name": "root" },
        { "id": "kernel", "name": "kernel", "parent": "root" },
        { "id": "fs", "name": "fs", "parent": "kernel", "value": 14200000 },
        { "id": "net", "name": "net", "parent": "kernel", "value": 8500000 },
        { "id": "drivers", "name": "drivers", "parent": "kernel", "value": 31200000 },
        { "id": "user", "name": "usr", "parent": "root" },
        { "id": "bin", "name": "bin", "parent": "user", "value": 18400000 },
        { "id": "lib", "name": "lib", "parent": "user", "value": 52100000 }
      ]
    }
  ]
}
```

### 3.2 Tree Normalization & Validation Invariants

1. **Uniqueness**: Every node MUST possess a unique string `id`. Duplicate IDs trigger `SpecError("duplicate node id")`.
2. **Root Singularity**: Exactly one root node exists (a node with no `parent` or `parent: null`). Multiple disconnected trees are rejected unless an implicit root is declared.
3. **Acyclic Guarantee**: Cycle detection via depth-first traversal ensures no node is an ancestor of itself.
4. **Value Rollup**:
   * For leaf nodes, `value` MUST be a finite number $\ge 0.0$.
   * For non-leaf nodes, if `value` is omitted, it is computed as the exact sum of all direct child values:
     $$V_{\text{node}} = \sum_{c \in \text{children}(\text{node})} V_c$$
   * If a non-leaf node specifies an explicit `value` greater than its children's sum, the difference represents "self" cost ($V_{\text{self}} = V_{\text{node}} - \sum V_c$).

---

## 4. Squarified Treemap Layout Engine

StoneCharts adopts the **Squarified Treemap algorithm** (Bruls, Huizing, van Wijk, 2000) because it optimizes for low aspect ratios (approaching 1:1 squares), eliminating thin, unreadable slivers and ensuring consistent label legibility.

### 4.1 Bounding Box & Padding

The inner plotting rectangle `(plot_x, plot_y, plot_w, plot_h)` is computed using standard margins. Within each non-leaf node rectangle $(X, Y, W, H)$:

* **Header Height (`hHeader`):** `18px` if node title is displayed, reserving the top strip.
* **Inner Padding (`pad`):** `2px` around child container.
* **Effective Child Area:**
  $$X' = X + \text{pad}, \quad Y' = Y + \text{hHeader} + \text{pad}$$
  $$W' = W - 2 \times \text{pad}, \quad H' = H - \text{hHeader} - 2 \times \text{pad}$$

### 4.2 Row-by-Row Squarification Algorithm

For a list of child nodes sorted in descending order of value:

1. Let the remaining rectangle have dimensions $(w, h)$ with $s = \min(w, h)$.
2. Add items to the current row layout incrementally.
3. For a candidate row with items of sum $S_R$ and minimum/maximum item values $v_{\min}, v_{\max}$:
   $$\text{aspect\_ratio} = \max\left(\frac{s^2 \cdot v_{\max}}{S_R^2}, \frac{S_R^2}{s^2 \cdot v_{\min}}\right)$$
4. Continue adding items to the current row as long as the worst aspect ratio improves. When adding a new item worsens the ratio, fix the current row, subtract its occupied area from the available rectangle, and start a new row along the new shortest edge.
5. Recursively subdivide each child node that has subordinate children.

### 4.3 Determinism and Float Parity

To prevent ULP drift between Python and Go:
* Node sorting uses a stable composite key: `(-node.value, node.id)`.
* Geometry coordinates are truncated or rounded via `fmt_num` with 2 decimal places.
* Total canvas energy conservation: $\sum \text{area}(\text{leaves}) \equiv \text{effective\_plot\_area}$.

---

## 5. Color Mapping & Visual Hierarchy

Family D supports two distinct color distribution modes:

1. **Branch Ancestor Inheritance (Categorical):**
   * Top-level children of root receive distinct categorical palette colors from the active theme (`theme.colors`).
   * Subordinate descendants inherit their top-level branch color with depth-based luminance decay:
     $$L_{\text{child}} = L_{\text{parent}} \times (1.0 - 0.12 \times \text{depth})$$
2. **Continuous Metric Mapping (ColorAxis):**
   * Reuses the Family C continuous color-scale engine (`SC-ARCH-008`).
   * Leaf cells are shaded according to a secondary metric (e.g., cell color encodes percentage growth while area encodes total volume).

---

## 6. Document Object Model (DOM) & Class Contracts

The rendered SVG conforms to the StoneCharts semantic class hierarchy:

```xml
<g class="sc-series sc-series-treemap" data-name="Storage">
  <!-- Parent branch container -->
  <g class="sc-treemap-group" data-id="kernel" data-depth="1">
    <rect class="sc-treemap-header-bg" x="100.0" y="50.0" width="300.0" height="18.0" fill="#e2e8f0"/>
    <text class="sc-treemap-header-text" x="104.0" y="63.0" font-size="11">kernel</text>
    
    <!-- Leaf node marks -->
    <rect class="sc-treemap-node sc-point"
          x="102.0" y="70.0"
          width="118.0" height="140.0"
          fill="#3b82f6"
          stroke="#ffffff"
          stroke-width="1"
          data-id="fs"
          data-name="fs"
          data-value="14200000"
          data-depth="2"
          tabindex="0"
          aria-label="kernel / fs: 14.2 MB (26.3%)"/>
    <text class="sc-treemap-label" x="161.0" y="145.0" font-size="10" text-anchor="middle">fs</text>
  </g>
</g>
```

---

## 7. Accessibility Contract (WCAG 2.1 AA)

In adherence to `docs/contracts/accessibility.md` (`SC-CON-007`):

1. **Semantic Tree Companion:**
   Renderers embed a hidden hierarchical ordered list inside the accessibility tree container:
   ```html
   <ol class="sc-a11y-tree" aria-label="Disk Space Utilization">
     <li>
       <span>root</span>
       <ol>
         <li>
           <span>kernel (53.9 MB)</span>
           <ol>
             <li>fs: 14.2 MB (26.3% of kernel)</li>
             <li>net: 8.5 MB (15.8% of kernel)</li>
             <li>drivers: 31.2 MB (57.9% of kernel)</li>
           </ol>
         </li>
         <li>
           <span>usr (70.5 MB)</span>
           <ol>
             <li>bin: 18.4 MB (26.1% of usr)</li>
             <li>lib: 52.1 MB (73.9% of usr)</li>
           </ol>
         </li>
       </ol>
     </li>
   </ol>
   ```

2. **Keyboard Navigation & Hierarchy Traversal:**
   * `Tab` / `Shift+Tab`: Move sequentially between leaf cell marks.
   * `Alt + Down`: Drill into current branch container.
   * `Alt + Up`: Drill out to parent container.
   * `Escape`: Reset drilldown state to root level.

---

## 8. Performance Budgets & Admission Checklist

* **Node Budget:** Up to $5,000$ active nodes per spec. Beyond $5,000$ nodes triggers `SpecError("maximum node count exceeded")`.
* **Renderer Execution Time:** $< 35\,\text{ms}$ in Python and $< 8\,\text{ms}$ in Go for a 1,000-node hierarchy.
* **Memory Ceiling:** $< 16\,\text{MB}$ peak memory allocation during recursive squarification.
* **Admission Path (Phase 0 to 5 per SC-ARCH-011):**
  1. Record `DEC-062` in `docs/project/decisions.md` targeting Family D.
  2. Implement Treemap in `libs/python/stonecharts/charts/treemap.py` and `libs/go/treemap.go`.
  3. Validate 100% byte-exact parity across 5 golden SVG fixtures.
