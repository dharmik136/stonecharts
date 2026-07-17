---
id: PC-ARCH-006
title: PeakCharts Chart Families Roadmap
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: roadmap
requirements: [REQ-PROD-001]
evidence: []
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# PeakCharts — Chart Families Blueprint & Cartesian Build Roadmap

> **Status:** Long-range engineering roadmap. Approved requirements, contracts, and
> ADRs take precedence. Chart and language expansion is paused for Phase 0 and Alpha 1.
> **Location:** `docs/roadmap/chart-families.md`
> **Audience:** Anyone planning chart-catalog expansion. Sections 4–5 preserve the
> detailed implementation procedure that produced Column. Future work must first
> reconcile it with approved requirements, contracts, ADRs, and the active release.

> **Governance migration:** historical uses of "binding", "locked", and uppercase
> requirement language in this file describe the previous planning regime. This file
> is informative under `PC-GOV-001`; those words become normative only when adopted by
> an approved requirement, contract, or ADR.

## Historical planning decisions

Two planning calls are settled and frozen. Everything below is downstream of them.

- **Call #1 — Build the WHOLE Cartesian family, extraction-first.** We do not add one-off cartesian charts. We commit to the entire Cartesian/XY family (column, bar, scatter, bubble, area-variants, combo, histogram, financial, ranges, waterfall, bullet, …) as a planned sweep. The **first** non-line sibling (Column) **triggers extracting the shared chrome** out of `line.py`/`line.go` into a shared cartesian module in **both** languages, *before or with* that sibling — never after. The line goldens are the frozen witness that the extraction changed nothing.
- **Call #2 — Highcharts baseline + profiling superset.** The catalog floor is the **Highcharts chart catalog** (every Highcharts chart type is in scope as a baseline target). On top of that floor we add a **profiling/observability superset** — chart types Highcharts does **not** ship that a profiler/observability product needs (flame graphs, flame charts, latency-over-time heatmaps, allocation-over-time heatmaps, icicle/partition, violin/ridgeline, ECDF/SLO curves, chord service-call matrices, span/Gantt trace waterfalls, force-directed topology). In the taxonomy every type is flagged **HC** (Highcharts baseline), **PS** (profiling superset — not in Highcharts, added for profiling), or **EXT** (beyond-baseline extra — not in Highcharts, not profiling-specific but useful).

---

## 1. Purpose & organizing principle

### 1.1 Why this document exists

PeakCharts renders charts as **static-first, byte-identical SVG from two independent implementations** (Python and Go), verified by a shared golden corpus. Adding chart types naively — one renderer at a time, each re-deriving axes/scales/legend/theme/a11y — would (a) duplicate the ~95%-shared "chrome" that already exists twice in `line.py`/`line.go`, and (b) let the two languages drift apart byte-for-byte. This document prevents both by organizing the entire catalog around **shared substrates** and defining the exact contract for riding each substrate without duplication or drift.

### 1.2 The organizing principle: group by SUBSTRATE

A **substrate** is the coordinate system + geometry engine + scale machinery a chart needs. Charts are grouped into **8 families by substrate**, not by visual resemblance. Two charts that look different but share a substrate (line and column both live on the Cartesian x/y plane) belong to the **same** family; two charts that look similar but need different substrates (a pie and a radial bar are polar; a treemap is hierarchy) do **not**.

Grouping by substrate is what makes the build economical: **you pay a family's foundation tax once** (build the substrate), then every subsequent type in that family is cheap because it reuses the substrate and adds only its marks.

### 1.3 The classification tool: variant / sibling / new-family

Every prospective chart type is classified against the substrates we already have:

| Tag | Meaning | Cost | Example |
|---|---|---|---|
| **done** | Already shipped. | — | Line |
| **variant** | Same renderer as an existing type + a flag/transform. No new mark, no new substrate. | Hours. | Area (fill flag), Streamgraph (baseline-offset flag), Donut (inner radius), Sparkline (chrome off) |
| **sibling** | Same **substrate** as an existing family, but a **new mark and/or a new generalization** of the shared machinery (a new point model, a new scale, a new layout). | Days. | Column, Bar, Scatter, Candlestick |
| **new-family** | Needs a **new substrate** — a new coordinate system / geometry / layout engine not yet built. Pays a **foundation tax**. | Weeks. | Pie (polar), Heatmap (matrix), Treemap (hierarchy), Sankey (flow), Violin (statistical KDE), Choropleth (geo) |

**Classification is a build-order tool, not a taxonomy label.** It answers "how expensive is this, and what does it force us to generalize?" — which drives sequencing.

### 1.4 The governing rule: exhaust a family before opening a new one

> **Finish (or deliberately scope-cut) an entire family's siblings and variants before paying another family's foundation tax.**

Rationale: the foundation tax is the expensive, risky part. Once paid, siblings are cheap. Opening a second family before the first is exhausted means paying a second foundation tax while the first family's cheap wins are still unrealized — the worst ordering. Concretely, per Call #1: **complete the Cartesian family** (it already owns the current substrate — foundation tax = $0) before opening Polar (Pie) or any other new-family. Within a family, build in the order that unlocks the most reuse for the fewest generalizations (see §3.3).

---

## 2. The audited taxonomy — 8 families

**Legend.**
**Class:** `done` · `variant` · `sibling` · `new-family` (per §1.3).
**Src (Call #2 provenance):** **HC** = Highcharts baseline · **PS** = profiling superset (not in Highcharts; added for observability/profiling) · **EXT** = beyond-baseline extra (not in Highcharts, not profiling-specific).
Every family lists its **foundation tax** — the one-time substrate cost paid by its `new-family` opener.

### Family A — Cartesian / XY  *(CURRENT SUBSTRATE)*

**Substrate:** Cartesian x/y plane — linear + category scales (+ log, datetime to add), rectangular plot area; marks = polyline/path, rect/bar, point/symbol, whisker.
**Foundation tax:** **ALREADY PAID.** `charts/line-basic` is done through P1–P5. Every cartesian sibling rides the existing axes/scales/legend/tooltip/crosshair/themes/a11y/defs/runtime/golden harness. This is the family we exhaust first (Call #1).

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Line** | done | HC | multi-series, spline, step (before/after/middle), datetime axis, log axis, zoom/pan, annotations, plot bands/lines, negative-color zones, inverted axes, null/gap handling, marker symbols, dashed | Metric time-series (CPU/mem/latency over time). Reference implementation; spline+step already shipped as variants. |
| **Area** | variant | HC | area (fillOpacity, done), area-spline, stepped area, stacked area, percent (100%) stacked area, negative area, area w/ nulls, inverted | Stacked resource usage over time. Fill done in P5; stacked/percent need the shared **stacking transform** — same renderer + flags. |
| **Streamgraph** | variant | HC | wiggle baseline, silhouette / inside-out | Theme-river of event/log volume over time. Stacked area + a wiggle/silhouette baseline-offset transform; same area renderer + offset flag. |
| **Range area (arearange)** | sibling | HC | arearange, areasplinerange, area-range + line | p50–p95 latency band over time. First driver of the **pure `{low,high}` point model** (no center y — distinct from the error-bar `{y,low,high}` center+range model; see §3.3). |
| **Column** | sibling | HC | basic, grouped, stacked, percent-stacked, negative, rotated labels, drilldown, inverted, column pyramid | Per-interval counts (throughput, GC pauses). **FIRST sibling to build** — forces the shared-chrome extraction + stacking + band-layout + orientation concept. |
| **Bar (horizontal)** | sibling | HC | basic, stacked, percent, negative-stack population pyramid | Column transposed → the single **orientation** concept (axes swapped); bar ideally delegates to column. |
| **Column range (columnrange)** | sibling | HC | vertical, horizontal | Min–max range per time bucket. (low,high) rect mark; rides the range point model + floating-bar primitive. |
| **Waterfall** | sibling | HC | vertical, horizontal, with intermediate sums | Budget/latency deltas across stages. Running-total column + connector lines. |
| **Histogram** | sibling | HC | frequency, density-normalized, pareto (histogram + cumulative line), bell-curve fit overlay | Latency / alloc-size distribution. Binning transform → column renderer on a numeric x-axis. Pareto & bellcurve are derived-series overlays. |
| **Scatter** | sibling | HC | basic, regression/trend line, categorized, polygon/hull overlay, 3D scatter | Latency vs payload-size correlation. Forces the **numeric x-scale** (generalize nice_ticks to x) + (x,y) point model. |
| **Bubble** | variant | HC | bubble, 3D bubble | Variant of the scatter sibling: z → marker radius (size-scale). |
| **Combo** | sibling | HC | line+column, dual axis, multiple axes, meteogram (spline+column+windbarb+errorbar) | Throughput bars + latency line on a shared time axis. Composition layer: multiple mark types on one plot / multiple y-axes. |
| **Financial (candlestick / OHLC)** | sibling | HC | candlestick, OHLC bar, HLC, hollow candlestick, Heikin-Ashi, flags/events | Min/max/first/last per window. (o,h,l,c) point model + wick/body floating-bar mark + datetime x-axis. |
| **Error bar** | sibling | HC | vertical whiskers, horizontal, on column/line | Confidence interval on aggregated latency. `{y,low,high}` center+range mark (a center y **plus** low/high — distinct from area/column range's pure `{low,high}`), usually overlaid on column/scatter. |
| **Boxplot** | sibling | HC | vertical, horizontal, with outliers, with scatter overlay | **Latency distribution per endpoint** (p25/median/p75 + whiskers + outliers). Cartesian axes + 5-number-summary transform + box/whisker mark. (Violin is the density upgrade — Statistical family.) |
| **Lollipop** | sibling | HC | vertical, horizontal | Stem line + marker; column-family mark (highcharts-more). |
| **Dumbbell** | sibling | HC | horizontal, vertical | Before/after latency per service. Two markers + connecting bar; (low,high) range model. |
| **Timeline** | sibling | HC | horizontal, vertical, with labels/leaders | Deploy / incident / release event timeline. Datetime axis + event markers along a single line. |
| **X-range / Gantt** | sibling | HC | xrange, Gantt (dependencies, milestones), swimlanes / per-thread lanes | **Span/Gantt trace waterfall** — distributed-tracing spans (Jaeger/Tempo), per-thread task bars. Horizontal bars spanning x1..x2 per category row on a datetime axis — core observability span-timeline substrate. |
| **Flame chart (time-ordered)** | sibling | PS | per-thread lanes, wall-clock x-axis | **Per-thread stack over wall-clock time** (Chrome DevTools / Perfetto style). Plots actual call intervals as floating bars at [start,end] against a datetime x-axis with a depth y — a depth-lane span timeline. Reuses the X-range/Gantt datetime-axis + floating-bar primitive; does **NOT** use the Hierarchy squarify/partition layout (it is time-ordered, not aggregated by self+children width). The aggregated flame graph + icicle/partition live in Hierarchy (Family D). |
| **Variwide** | sibling | HC | variable-width column | Column where bar WIDTH also encodes a value; needs a cumulative-width x-layout. |
| **Vector plot** | sibling | HC | vector field | Per-(x,y): direction + length → arrow glyph. |
| **Windbarb** | sibling | HC | meteorological barbs | Datetime axis + wind-barb glyph (speed + direction). |
| **Funnel / pyramid** | sibling (does NOT inherit axis chrome) | HC | funnel, inverted pyramid, area/neck funnel, funnel3d, pyramid3d | Conversion / drop-off across pipeline stages. Centered stacked trapezoids; value→width linear scale (cartesian-lite). **Exception to the Family A substrate contract:** it uses none of the x/y axis chrome, no gridlines, and neither the point nor band x-scale — it brings its **own** centered-trapezoid mark + value→width centering layout. Highcharts derives it from the pie/part-to-whole module. Alt home: part-to-whole with pie (Polar). |
| **Technical indicators & overlays** | sibling | HC | SMA/EMA, Bollinger bands, MACD, RSI, VWAP, plot bands/lines, flags | Moving-average / anomaly overlays on metric series. Derived-series transforms producing extra cartesian series/panes; **NOT a new substrate**. |
| **3D isometric (column / scatter / cylinder)** | new-family | HC | 3D column, 3D scatter, cylinder, 3D area | Isometric z-projection over cartesian — a genuine new foundation (depth sorting, projection). **Conflicts with static-first byte-parity — out of scope for v1.** (3D pie rides polar+projection.) |

> **Family A substrate contract:** every cartesian sibling rides the existing axes/scales/legend/tooltip/crosshair/themes/a11y/defs/runtime/golden harness — **with one declared exception: funnel/pyramid** (see its row), which brings its own centered-trapezoid mark + value→width layout and inherits none of the x/y axis chrome.

### Family B — Polar / radial

**Substrate:** Polar coordinates (angle θ + radius r); arc/sector path geometry (SVG `A` commands); angular + radial axes instead of x/y.
**Foundation tax:** Polar coordinate system (θ,r ↔ x,y) + arc/sector path builder + angular & radial axes/gridlines + start-angle/end-angle & inner-radius handling.

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Pie** | new-family | HC | basic, with legend, exploded/sliced, gradient/monochrome, drilldown, small-multiple pies | **Opens the family** (pays the polar foundation tax once). Part-to-whole. |
| **Donut / doughnut** | variant | HC | donut (innerSize), semi-circle donut, nested / multi-level | Pie with an inner radius. |
| **Variable-radius pie** | variant | HC | radius-encoded 2nd metric | Slice angle = share, slice radius = a second metric. |
| **Gauge / dial** | sibling | HC | angular gauge, VU meter, clock, dual / multi-pointer | Single live metric vs thresholds. Value→angle pointer + colored bands. |
| **Solid gauge** | sibling | HC | radial fill, activity gauge (multi-ring), radial progress | **Utilization / SLO gauges** (CPU%, error-budget burn, saturation). Filled arc from start-angle to value-angle. |
| **Radar / spider** | sibling | HC | line radar, filled radar, multi-series, spiderweb vs circular grid | Multi-dimension service scorecard (RED/USE per service). Cartesian line/area on a polar category grid. |
| **Polar / radial (generic)** | sibling | HC | polar line, polar column, polar scatter, polar range | The general polar wrapper — any cartesian series re-projected onto the polar grid. |
| **Wind rose** | variant | HC | stacked polar column by direction | Polar stacked column; direction = angle, frequency = radius. |
| **Nightingale / rose / coxcomb** | variant | HC | area rose, radius-value polar column | Polar column where radius encodes value at equal angles. |
| **Radial bar (racetrack)** | sibling | HC | concentric progress rings, radial stacked bar | Bars along the angular axis / concentric progress rings. |
| **Funnel / pyramid (part-to-whole)** | sibling | HC | funnel, inverted pyramid, area/neck funnel | Conversion / drop-off across pipeline stages. Grouped here as **part-to-whole** (Highcharts derives it from the pie module). Brings its own centered-trapezoid mark + value→width centering layout — it does **not** use the polar arc geometry either; it is filed here for the part-to-whole intent, not for substrate reuse. Primary listing is its Family A row. |
| **Item / parliament (hemicycle)** | sibling | HC | rectangular item grid, circular parliament | Unit/pictorial: one symbol per item packed into a wedge/grid; part-to-whole by count. **Only the circular hemicycle is polar**; the **rectangular item-grid** subtype uses no polar coordinates — it is a unit/pictorial grid that belongs with Waffle / unit chart in **Family H (KPI)**. |

### Family C — Matrix / grid

**Substrate:** Regular 2-D cell grid (row × column categories, or binned numeric) with value→fill via a continuous color scale; no data lines.
**Foundation tax:** 2-D grid layout + continuous color scale (sequential/diverging interpolation) + color-axis (gradient) legend + cell/tile renderer; for binned variants, numeric 2-D binning.

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Heatmap** | new-family | HC | basic, large / boosted, correlation matrix, categorical, clustered / reordered | **Opens the family** — introduces the continuous color scale + color-axis (gradient) legend every matrix/hierarchy/geo type reuses. Correlation / co-occurrence matrices. |
| **Calendar heatmap** | sibling | PS | GitHub-style year grid, month grid | Event / incident / commit density per day. Date → (week, weekday) cell layout. |
| **Tilemap** | sibling | HC | honeycomb / hexagon, circle, diamond, square | Fleet / host status grid. Non-square cell packings. |
| **Hexbin / 2-D density** | sibling | PS | hex binning, square binning | Dense (latency,size) scatter collapsed to counts. Numeric 2-D binning + count→color. |
| **Allocation-over-time heatmap** | sibling | PS | alloc-size buckets × time | **Memory allocations over time** (y = size bucket, x = time, color = count/bytes). Time-binned grid. |
| **Latency heatmap (pulse / Gregg)** | sibling | PS | latency buckets × time, weighted | **Latency distribution over time** (x = time, y = latency bucket, color = frequency). The "rainbow" latency heatmap; reveals multi-modality invisible in a p99 line. |

### Family D — Hierarchy

**Substrate:** Hierarchical (parent/child, valued) tree data + a space-filling or node-link layout; region / arc / node marks.
**Foundation tax:** Tree data model + layout engines (treemap squarify, rectangular partition/icicle, radial partition/sunburst, tidy-tree, circle-packing) + breadcrumb & drill-zoom interaction; reuses the Matrix continuous color scale.

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Treemap** | new-family | HC | squarified, nested / levels, color-axis, drilldown, treemap↔sunburst transition | **Opens the family** — tree data model + squarify layout. Disk / heap usage by module. |
| **Sunburst** | sibling | HC | radial partition, drill / zoom, multi-level | Aggregated call-tree by proportion. Bridges Polar (arc geometry) + Hierarchy (tree). |
| **Icicle / partition** | sibling | PS | top-down, left-right | Call-tree partition — the **flame-graph base layout**. Rectangular partition. |
| **Flame graph (aggregated)** | sibling | PS | flame (bottom-up), icicle (top-down), differential / diff, off-CPU, alphabetical vs time-weighted | **THE CPU/alloc profiler view** — **aggregated** stacks, width = self+children samples, click-to-zoom, search-to-highlight. Icicle where node width = aggregated cost. (The **time-ordered** flame chart is NOT here — it is a Cartesian xrange sibling, Family A, because it plots wall-clock intervals, not aggregated widths.) |
| **Dendrogram / cluster tree** | sibling | HC | tidy tree, cluster, radial tree | Node-link hierarchical layout (Reingold–Tilford). Highcharts ships this as the `treegraph` series (node-link tidy/cluster tree, since v10.1). |
| **Circle packing** | sibling | EXT | hierarchical enclosure | Enclosure layout; contrast with force-based packed bubble (Flow). |
| **Organization chart** | sibling | HC | top-down, horizontal | Tidy hierarchical tree (Highcharts implements as sankey-derived layout). |

### Family E — Flow / relational

**Substrate:** Node + link (graph) data model; a layout engine (flow ranking, force simulation, or fixed arc/chord placement); link marks = bezier ribbons / edges.
**Foundation tax:** Node/link data model + layout engines (sankey rank + flow allocation, force-directed simulation, arc/chord circular placement) + ribbon/edge path geometry; set-overlap geometry for venn; **Archimedean-spiral glyph-packing layout for word cloud** (a node-only outlier that reuses none of the sankey/force/chord/ribbon machinery — see its row).

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Sankey** | new-family | HC | basic, vertical / inverted, multi-level, alluvial | **Opens the family** — rank + flow-allocation layout + ribbon paths. Request flow across services/queues; byte flow. |
| **Dependency wheel** | sibling | HC | circular sankey | Sankey wrapped to a circle (polar node placement + ribbons). |
| **Chord diagram** | sibling | PS | directed, symmetric | Service-to-service call-volume matrix. Adjacency matrix → arcs + ribbons on a circle. |
| **Network graph (force-directed)** | sibling | HC | force-directed, clustered, weighted edges | **Service dependency / call graph topology** — the observability topology map. Force-simulation layout. |
| **Arc diagram** | sibling | HC | 1-D nodes + arcs | Nodes on a line, links as arcs above/below. |
| **Packed bubble** | sibling | HC | packed bubble, split packed bubble | Force layout of node-only circles (no links); size = value. Legitimately reuses the family's **force-sim**. |
| **Venn / Euler** | sibling | HC | 2-set, 3-set, Euler (proportional) | Set-overlap geometry (circle intersection); grouped here as relational/set. |
| **Word cloud** | sibling (own mini-foundation) | HC | spiral packing, rotation | Archimedean-spiral text packing; size = frequency; **no links**. **Substrate outlier:** it has no node/link data model and no graph layout, and reuses **none** of sankey/force/chord/ribbon machinery — it needs its own **Archimedean-spiral glyph-packing** engine (added to Family E's foundation tax above). It is filed under Flow only for the "node-only, no real link substrate" convenience grouping. |

### Family F — Statistical / distribution

**Substrate:** Cartesian axes + a statistical transform that **synthesizes a shape** (density / quantiles / contours) rather than plotting raw points.
**Foundation tax:** Kernel density estimation (1-D KDE) + quantile/summary computation + mirrored (violin) / stacked-ridge layout, **plus** marching-squares contour extraction over a 2-D KDE grid (for 2-D density/contour, which rides this single tax and additionally consumes the Matrix color scale). One opener (Violin) pays the whole tax.
**NB:** Boxplot, histogram, and error-bar reuse only cartesian axes and therefore live in **Family A (Cartesian)**, not here.

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Violin** | new-family | PS | violin, violin + box, half-violin, split violin | **Latency distribution shape per endpoint** (multi-modality visible). Boxplot + mirrored KDE density; **introduces the KDE transform** the family is named for (and, via the shared tax, the 2-D contour machinery). |
| **Ridgeline (joyplot)** | sibling | PS | stacked KDE ridges | Latency distributions across many services / time buckets. Vertically offset KDE areas; reuses KDE + the area renderer. |
| **Density / KDE curve** | sibling | HC | 1-D KDE, normal-fit (bell curve) | Smoothed latency PDF. Rides the cartesian area/line renderer; adds only the KDE/normal transform (Highcharts bellcurve). |
| **2-D density / contour** | sibling | PS | contour lines, filled contour, density heatmap | Marching-squares contour extraction over a 2-D KDE grid; also consumes the Matrix color scale. **Sibling, not a second opener** — the marching-squares + 2-D-grid KDE geometry is folded into Family F's single foundation tax (paid by Violin), preserving the one-opener-per-family invariant. |
| **Q-Q plot** | sibling | PS | quantile-quantile, P-P plot | Compare a latency distribution vs normal/reference. Cartesian scatter of quantile pairs + reference line; no new substrate. |
| **ECDF / cumulative** | sibling | PS | ECDF step, CDF | **SLO attainment curve** (x = latency, y = fraction ≤ x). Cartesian step-line of the empirical CDF. |

### Family G — Geo

**Substrate:** Geographic projection (lat/lon → x/y) over map polygon geometry (geo/topojson); region + point + link marks.
**Foundation tax:** Map projection library (Mercator/Albers/Robinson/…) + geo/topojson polygon ingestion + region hit-testing + pan/zoom navigation; reuses Matrix color scale + Scatter bubble marks + Flow ribbons. **Largest new investment.**

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Choropleth** | new-family | HC | continuous, data-classes / quantized, categorized areas | **Opens the family** — projection + region fills. |
| **Map bubble (proportional symbol)** | sibling | HC | bubble, sized markers | Scatter bubbles anchored at lat/lon. |
| **Map point / marker map** | sibling | HC | markers, clustered points | Point series on the projection. |
| **Flow / connection map** | sibling | HC | great-circle links, flowmap | Cross-region traffic / replication flows. Curved links between geo points (reuses Flow ribbon geometry). |
| **Map line (mapline)** | sibling | HC | borders, routes | Line/path geometry on the map. |
| **Geo heatmap / density map** | sibling | HC | geoheatmap, kernel density | Continuous field over the projection. |
| **Tile-grid map (cartogram)** | sibling | EXT | hex / square tile per region | Equal-area tile per region (reuses Matrix tilemap); abstract geography. |
| **Tiled web map (raster)** | sibling | HC | OSM / XYZ raster tiles | Raster basemap under vector series. **Needs external tile fetch — breaks static-first; likely out of scope.** |

### Family H — KPI / single-value

**Substrate:** Minimal — one value (or a few) rendered as text + a mini-mark; usually no axes/chrome.
**Foundation tax:** **NEAR-ZERO.** Sparkline reuses the cartesian line renderer with chrome off; gauge-style KPIs reuse the polar solid gauge; bullet rides the cartesian bar substrate. This family is mostly "existing renderers with chrome stripped."

| Type | Class | Src | Subtypes | Profiling superset use / notes |
|---|---|---|---|---|
| **Number / stat card** | sibling | EXT | big number, with delta / trend, with embedded sparkline | Single SLI headline (current p99, error rate). Text + delta; minimal layout. |
| **Sparkline** | variant | EXT | line, area, with band | Inline metric trend in tables/rows. Tiny cartesian line with axes/legend/margins off → **a variant of the line renderer.** |
| **Sparkbar / win-loss** | variant | EXT | bar spark, win-loss | Tiny column renderer, chrome off. |
| **Progress / linear gauge** | sibling | EXT | progress bar, segmented, stacked progress | Error-budget / quota consumed. Single 0–100% bar. |
| **Bullet graph** | sibling | HC | horizontal, vertical, with qualitative bands | **SLI vs target + good/warn/bad bands.** Cartesian bar + target marker + qualitative range bands. Rides the cartesian bar substrate (see §3.3 rank 13). |
| **Waffle / unit chart** | sibling | EXT | 10×10 grid, icon waffle | Grid of unit cells, part-to-whole by count/color (categorical). |
| **Pictorial / icon array** | sibling | HC | repeated glyph, clipped fill | Value encoded by repeated/clipped SVG icons. |
| **KPI delta / trend indicator** | sibling | EXT | arrow + percent, sparkline + value | Composite headline metric tile. |

---

## 3. The Cartesian family — scoped plan

Per Call #1 this is the family we build to exhaustion first. Its foundation tax is $0 (the substrate exists). What follows is the shared substrate we already have, the generalizations the siblings force, and the exact build order.

### 3.1 Shared substrate we already own (reused by every cartesian sibling)

From `charts/line-basic` (done P1–P5), every sibling inherits, with **zero** re-implementation:

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix`; category x-axis via `xpix`.
- Y gridlines + labels; titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution, id-scoping via `cid`.
- Accessibility: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table + keyboard nav.
- Responsive `<svg>` viewBox; the shared JS runtime (`runtime/chart-interactions.js`: tooltip, highlight, legend-toggle, keyboard, crosshair).
- `esc` (string escaping), `fmt_num`/`fmtNum` (`%g` 6-sig values), `f1`/`:.1f` (pixel coords) — all parity-locked in `util.py`/`util.go`.
- The golden Python==Go parity harness pinning both renderers to the **same** committed `charts/*/golden/*.svg`.

### 3.2 The generalizations the siblings force

Building the family requires generalizing the line-only machinery in exactly these ways. Each is built **once**, then reused. The five headline generalizations (per the plan) are point-model, numeric-x-axis, stacking, orientation, and band-layout; three more (size-scale, composition-layer, secondary-y-axis) complete the set.

| Generalization | What it does | Parity discipline (the trap) | Forced by |
|---|---|---|---|
| **Point model** (richer, forward-compatible datum) | Normalize `series[].data` (today `number[]`, one y per index) into a canonical datum with OPTIONAL float fields `{x,y,z,open,high,low,close,name}`. A bare number stays valid (x = index) so **line + column goldens never move**; positional arrays (`[x,y]`, `[o,h,l,c]`, `[low,high]`) are sugar; absent/null field → **gap, never coerced to 0**. | Both languages parse to the **same** struct field-for-field; the bare-number fast path is **pinned** in both (Python: numeric element → `Datum(x=index, y=float(v))`; Go: a custom `UnmarshalJSON` that still decodes a bare-number array `[1,2,3]` to the same `[]float64`-equivalent bytes). When the element type changes, `_line_marks`, `_column_marks`, and `build_frame`'s y-range extractor **all** move from `v` to `datum.y` in lockstep; every new field formats through `fmt_num`/`esc`. Gated by a byte-identity check at the changing rank (§3.3 Rank 3). | scatter, bubble, candlestick, error-bar, area-range, column-range, waterfall |
| **Numeric x-axis** | Generalize the value-axis machinery (`nice_ticks` + tick labels + gridlines + pixel map) from y-only to x: `xpix` from a **value**, x tick labels, vertical gridlines. | Reuse the already-parity-locked `nice_ticks` + `fmt_num` verbatim → x ticks are byte-identical for free. `data-x` becomes a numeric value via `fmt_num`, not a category string. **Caveat — do NOT carry the y-baseline zero-anchor into x:** the shared value axis bakes in "force 0 into the domain" for the column/bar/area value axis; a free numeric x (and free numeric y) axis must reuse the axis routine with **include-zero OFF** (see §4.2), or a scatter with x∈[100,200] is wrongly anchored at 0. Both languages would be wrong identically and pass byte-parity — so the include-zero flag must be explicit. | scatter, bubble, histogram, candlestick |
| **Stacking transform** (grouped / stacked / percent) | One shared transform computing per-datum cumulative baselines and percent shares, consumed by column, bar, area. Selected by a **new `stacking` spec field** (+ grouped/overlaid selector) routed through the §5.4b five-place lockstep. The **frame** (not the marks) owns the stacking-aware y-domain: for stacked/percent the y-max is the max column **total**, not the per-datum max. | Pin the **summation ORDER** (accumulate series in index order) and the percent division so cumulative floats and `%g` output match across languages. The frame's cumulative y-domain uses the **same** summation order. | column, bar, area |
| **Orientation transpose** (bar = column transposed) | One orientation concept swapping the category-axis and value-axis, so bar delegates to column with axes swapped instead of forking a renderer. Also yields horizontal range bars + horizontal bullet. | Parity is free — orientation is a coordinate remap only; same `fmt_num`/`f1` and band arithmetic. | bar, column-range, bullet |
| **Band layout** (per-category slot with padding) | Split each category slot into K sub-bands (grouped) — the geometry every rect-based sibling needs. Pinned scheme: `bandWidth = plot_w / n`; band center `xpix(i) = plot_x + bandWidth*i + bandWidth/2`; single group-padding constant `PAD = 0.2`; `groupW = bandWidth*(1 - PAD)`; `K = len(series)`; `barW = groupW / K`; `left(i,k) = xpix(i) - groupW/2 + barW*k`. (Basic single-series ⇒ K=1 ⇒ one centered bar of width `groupW`.) | Evaluate the arithmetic in **exactly** this operation order so `f1` rounding lands ULP-for-ULP identically in Py and Go. `PAD` and `K = len(series)` are fixed constants, not per-author choices. | column, bar, histogram, candlestick, column-range, waterfall, bullet, combo |
| **Size scale** (z → area-proportional radius) | Map a third dimension z to marker radius: `r = rmin + (rmax-rmin)*sqrt(clamp01((z-zmin)/(zmax-zmin)))`. | **Degenerate rule pinned identically in BOTH languages, evaluated BEFORE any division:** if `zmax <= zmin` (all-equal z, or a single point) use a fixed radius `(rmin+rmax)/2` — never divide `0/0` (Python raises `ZeroDivisionError`; Go yields `NaN`→`fmtNum`→`"0"`). Otherwise `clamp01` the ratio to `[0,1]` **before** `sqrt` so the domain is never negative (Python `math.sqrt(neg)` raises; Go `math.Sqrt(neg)=NaN`→`"0"`). Pin `rmin`/`rmax`; radius via `fmt_num`; `sqrt` is IEEE754-identical (`math.sqrt`/`math.Sqrt`) **only once the domain is guaranteed ≥ 0**. Covered by a bubble edge-case parity test (all-equal z, single point, z at/below/above domain — asserts finite output and Py==Go). | bubble |
| **Composition layer** (multiple mark kinds on one plot) | Compute plot-area + scales ONCE, then dispatch each series to its own mark renderer against shared scales. Generalizes the single top-level `type` into a per-series `series[].type`. | The new per-series `type` field is validated identically in both languages (deterministic error order). | combo |
| **Secondary y-axis** (dual value axis) | A second, independent y-scale + axis (its own `nice_ticks`) for co-plotted series with different units. Lower priority, but the substrate must leave room for it. | The second axis reuses the same `nice_ticks`/`fmt_num` path → byte-identical by construction. | combo, candlestick |

### 3.3 Build order (rank → what it unlocks)

Ordered so each sibling forces the fewest **new** generalizations and unlocks the most reuse for the next. Each entry lists: data model, marks, key reuse, net-new components, and the parity trap.

**Rank 1 — Column (vertical bars).** *THE trigger for the shared-chrome extraction (§4).*
- **Data model:** value payload reuses `data:number[]` — one y per category, identical shape to line. Grouped/stacked/percent are transforms over these y-values, **selected by a new `stacking` (+ grouping) spec field** (§5.4b five-place lockstep — you physically cannot render a `stacked` golden differently from `grouped`/`basic` without a mode selector, and an unvalidated `stacking` key would break NN#3).
- **Marks:** one baseline-anchored `<rect class="pk-bar pk-point">` per (category,series): x/width from the band slot; `y = ypix(value)`; `height = ypix(0) - ypix(value)`. Bars replace circle markers as the hoverable element. Legend swatch is the existing `<rect>`. Bar fill reads `fr.styles[si].fill` (the resolved bar paint — solid/gradient/pattern — see §5.3 / §4.3), **not** `area_fill`.
- **Reuses:** plot-area+margins, y-scale (`nice_ticks`/`ypix`), y-gridlines+labels, axis lines, categorical x-axis, titles+subtitle, axis titles, legend, crosshair, a11y, defs pre-pass (gradient/pattern fill on bars), theme+palette, responsive svg, svg-contract, `fmt_num`/`f1`/`esc` parity.
- **Net-new:** the **chrome extraction** into `charts/_cartesian.*` (Call #1 trigger, §4); **band-layout**; **stacking-transform** + the new `stacking`/`grouping` spec field (§5.4b); **frame-owned stacking-aware y-domain** (§4/§5.2); **rect-mark primitive**; **`fill` field on SeriesStyle** for bar paint (§4.3/§5.3).
- **Parity trap:** fix band arithmetic ORDER so `f1` rounding matches ULP-for-ULP. Pinned scheme (identical in both languages, evaluated in this order): `bandWidth = plot_w/n`; band center `xpix(i) = plot_x + bandWidth*i + bandWidth/2`; group-padding constant `PAD = 0.2`; `groupW = bandWidth*(1-PAD)`; `K = len(series)`; `barW = groupW/K`; `left = xpix(i) - groupW/2 + barW*k`. Stacking cumulative sums must accumulate in the same series order in both languages, and the **frame's** stacked y-max uses that same order. Bars carry the same `data-series`/`data-x`/`data-y`/`data-color` (+ `cx`) as `.pk-point`, so the runtime enhances with **zero JS change**.

**Rank 2 — Bar (horizontal columns).** Forces the **orientation** generalization.
- **Data model:** `number[]` value payload + the shared `stacking`/`grouping` field (same as column); only axis roles swap.
- **Marks:** horizontal `<rect>` bars — value → WIDTH along x (the value axis); categories run down y (the band axis). Same grouped/stacked/percent variants.
- **Reuses:** column's band-layout + stacking (incl. the frame-owned stacked value-domain); y-scale machinery (now applied to x); all chrome; parity paths.
- **Net-new:** **orientation-transpose** (bar = column with the value axis on x and the band axis on y; ideally one renderer parameterized by orientation, not a fork).
- **Parity:** free — transpose is a coordinate remap only; `nice_ticks`/value labels move to x, category labels to the left (y); legend/tooltip/a11y unchanged.

**Rank 3 — Scatter (XY points).** Forces **numeric-x-axis** + **point-model**.
- **Data model:** **richer** — `{x,y}` numeric pairs (positional `[x,y]` sugar). The bare-number fast path stays valid for line/column (x=index) and is **pinned in both languages** (Python: numeric element → `Datum(x=index, y=float(v))`; Go: custom `UnmarshalJSON` keeping `[]float64`-equivalent decoding for numeric arrays), so old goldens don't move.
- **Marks:** unconnected `<circle|rect|polygon class="pk-point">` at `(xpix(x), ypix(y))` — reuse the four existing marker symbols; no series line. Fill-opacity for overlap density.
- **Reuses:** plot-area, y-scale, gridlines, axis lines, chrome, marker symbols, defs pre-pass, theme, parity paths.
- **Net-new:** **numeric-x-axis** (with include-zero **OFF** for the free x-domain — §3.2 caveat, §4.2); **point-model normalization** (x,y datum) — which also moves `_line_marks`, `_column_marks`, and `build_frame`'s y-range extractor from a float element to `datum.y` in lockstep; optional vertical x-gridlines.
- **Parity:** the x-scale reuses the already-parity-locked `nice_ticks`+`fmt_num` verbatim → x ticks byte-identical for free. `data-x` becomes numeric via `fmt_num`. Crosshair may become two-axis; tooltip shows (x,y).
- **Byte-identity gate (mandatory, because the data element type changes):** after the point-model lands, `git diff` MUST be empty on **ALL** existing goldens (every line fixture **and** every prior sibling — column) — the bare-number fast path must reproduce the exact pre-refactor bytes, proven by golden-diff, **not** asserted. Plus a Py==Go cross-render on every one of those fixtures. This gate applies to **any** rank that changes the `data` element type. Also generalize the accessible data table for the new point model per §5.4b (data table stops assuming `number[]`).

**Rank 4 — Bubble (XY + size).** Forces the **size-scale**. *(A `sibling`, not a variant — it introduces a new scale and a new `{x,y,z}` point model; see §1.3 and the §2 Family A row.)*
- **Data model:** richer — `{x,y,z}`; z drives marker size.
- **Marks:** `<circle class="pk-point">` at `(xpix(x),ypix(y))`, r from a size-scale of z; fill-opacity for overlap; add `data-z`.
- **Reuses:** scatter's numeric-x-axis + point-model; y-scale; chrome; parity.
- **Net-new:** **size-scale** (`r = rmin + (rmax-rmin)*sqrt(clamp01((z-zmin)/(zmax-zmin)))`); optional size legend (z buckets).
- **Parity:** pin the radius formula + `rmin`/`rmax` constants. **Handle the degenerate domain identically in BOTH languages, before any division:** if `zmax <= zmin` use a fixed radius `(rmin+rmax)/2`; otherwise `clamp01` the ratio to `[0,1]` before `sqrt`. Never perform a raw float divide Python would reject (`0/0` → `ZeroDivisionError`) or feed a negative into `sqrt`. Radius via `fmt_num`; `sqrt` is IEEE754-identical only once the domain is guaranteed ≥ 0. Add a bubble edge-case parity test (all-equal z e.g. `z=[5,5,5]`, single point, z at/below/above domain) analogous to `test_spline_edge_cases`, asserting finite output and Py==Go.

**Rank 5 — Area (stacked + percent).** The cheapest sibling once column exists — effectively a **variant** riding column's stacking.
- **Data model:** `number[]` value payload + the shared `stacking`/`grouping` field — stacked/percent are cumulative-offset transforms.
- **Marks:** filled `<path class="pk-series-area">` (already exists via fillOpacity) but the baseline becomes the **previous series' cumulative top** instead of zero; percent mode normalizes each x-column to 100%. Series line drawn on the cumulative top edge.
- **Reuses:** the **entire line renderer** (path builder, area fill, gradients/patterns, markers); column's stacking-transform + frame-owned stacked y-domain; y-scale; chrome; parity.
- **Net-new:** **band-fill-between-cumulative-baselines** (area top of series k = cumulative through k; bottom = cumulative through k−1) — a thin wrapper over the existing path builder.
- **Parity:** pin the column-total summation ORDER and the division so `%g` output matches; reuse `_path_d` so `f1` coords match for free. Percent mode: y-axis becomes `nice_ticks(0,100)`; each value divided by its column total.

**Rank 6 — Combo (line + column).** Forces the **composition-layer**.
- **Data model:** `number[]` per series PLUS a per-series render kind: `series[].type ∈ {line,column}`. Generalizes the top-level `type` into a per-series concept.
- **Marks:** columns (rects) + line paths + points co-drawn on ONE shared plot area against shared (or dual) y-scales.
- **Reuses:** column's rect-mark + band-layout; line's path + markers; the shared `_cartesian` chrome; y-scale; theme; defs; parity.
- **Net-new:** **composition-layer** (compute plot-area + scales ONCE, then dispatch each series to its mark renderer); **secondary-y-axis** (optional, dual units); legend swatch variants (bar rect vs line dash) by mark kind.
- **Parity:** the new per-series `type` field is validated in both languages with deterministic error order.

**Rank 7 — Histogram (binned distribution).** Introduces the **binning-transform**.
- **Data model:** semantically different — input is a **raw sample list** `number[]` (unaggregated), binned by the renderer; OR pre-binned points `{binStart,binEnd,count}`. Not y-per-category.
- **Marks:** contiguous (zero-gap) `<rect>` bars, one per bin, on a **numeric** x-axis (bin edges), height = count/frequency.
- **Reuses:** column's rect-mark; scatter's numeric-x-axis (for bin edges); y-scale for counts; chrome; parity.
- **Net-new:** **binning-transform** (min/max → bin count/width → assign samples → counts).
- **Parity (biggest trap in the family):** the bin-edge computation AND the value→bin rule (`bin = floor((v-min)/width)`, last bin inclusive of max) MUST be byte-identical or counts diverge **before** any formatting. Bars are contiguous — NO inter-bar padding, unlike column's categorical bands.

**Rank 8 — Candlestick / OHLC (financial).** Introduces the **(o,h,l,c) point model** + **floating-bar primitive**.
- **Data model:** richer — `{open,high,low,close}` per x (+ optional numeric/time x). `number[]` cannot express it.
- **Marks:** candlestick = wick `<line>` high→low + floating body `<rect>` open↔close (**not** baseline-anchored); OHLC bar = vertical high→low tick + left(open)/right(close) ticks. Up/down color by `close>=open`.
- **Reuses:** band-layout (slot/width per x); y-scale; y-gridlines+labels; axis lines; category or numeric x-axis; chrome; theme; parity.
- **Net-new:** **point-model (o,h,l,c)**; **floating-bar primitive** (rect between two arbitrary y-values); **wick line primitive**; up/down two-color legend.
- **Parity:** the `close>=open` comparator and body geometry (`y=ypix(max(open,close))`, `height=|ypix(open)-ypix(close)|`) must be identical; pin a **min-1px** rule for the doji (open==close) zero-height body in BOTH languages. `data-*` carries all four values. Shares the floating-bar with column-range.

**Rank 9 — Error bars (whiskers on points).** Extends the point-model with **low/high alongside a center y**.
- **Data model:** richer — center `y` PLUS `(low,high)`: `{y,low,high}`. Typically an **overlay** on line/column/scatter, not a standalone plot.
- **Marks:** `<line>` stem low→high centered on the point x + short cap `<line>`s at each end, drawn on top of the base mark.
- **Reuses:** existing point/line/column marks as base; y-scale; chrome; band-layout (to center on a bar); parity.
- **Net-new:** **whisker-mark primitive** (stem + two caps); point-model extension: low/high alongside a center y (distinct from area-range, which has no center y).
- **Parity:** cap half-width constant + stem/cap coords via `f1` identical both languages.

**Rank 10 — Area range (band between two lines).** Introduces the **(low,high) point model** + **band-fill between two data paths**.
- **Data model:** richer — `(low,high)` per x, NO center line. `{low,high}` (positional `[low,high]` sugar).
- **Marks:** one filled `<path>` = high boundary L→R + low boundary R→L + Z (a band from a single datum's two values); optional bounding strokes.
- **Reuses:** line's `_path_d` builder run twice (top on highs L→R, bottom on lows R→L); area fill / gradient / pattern / defs; y-scale; chrome; category x-axis; legend; a11y; parity.
- **Net-new:** **point-model (low,high)**; **band-fill between two DATA paths** (vs stacked-area's fill between a series and a cumulative baseline).
- **Parity:** two passes of the already-parity-locked `_path_d`, concatenated → `f1` coords match for free. Horizontal variant falls out of the orientation generalization.

**Rank 11 — Column range (floating bars).** Reuses the floating-bar + (low,high) model — near-zero net-new once candlestick lands.
- **Data model:** richer — `(low,high)` per category; floating bars.
- **Marks:** floating `<rect>` from `ypix(low)` to `ypix(high)`, one per category/series, inside band slots — not zero-anchored.
- **Reuses:** column's band-layout; **floating-bar primitive** (shared with candlestick); y-scale; chrome; category x-axis; parity.
- **Net-new:** point-model (low,high) — shared with area-range; **no net-new mark** once candlestick lands. Orientation generalization yields a horizontal bar-range for free.

**Rank 12 — Waterfall (running-total columns).** Introduces the **running-total transform** + **connector lines**.
- **Data model:** `number[]` of DELTAS, plus an optional per-point flag `isSum`/`isIntermediateSum` (`{y,isIntermediateSum}`). Running total computed by a transform; total bars anchor to the baseline.
- **Marks:** floating `<rect>` per step (running-total → running-total+delta) + dashed connector `<line>`s between consecutive bar tops; up/down color by delta sign; total/subtotal bars zero-anchored.
- **Reuses:** column's band-layout; floating-bar (from candlestick/column-range); y-scale; chrome; parity.
- **Net-new:** **running-total transform** (cumulative deltas → per-bar [start,end]); **connector-lines primitive**; up/down/total three-color legend + the optional `isSum` flag (new spec field, validated both languages).
- **Parity:** cumulative-sum accumulation ORDER identical; connector goes from bar-right of step i to bar-left of step i+1; coords via `f1`.

**Rank 13 — Bullet (KPI bar + target + qualitative bands).** Rides the bar substrate; also belongs to Family H (KPI).
- **Data model:** richer-ish — per row: a measure `value`, a comparative `target`, and qualitative range bounds: `{value, target, ranges:[..]}`.
- **Marks:** background qualitative-range `<rect>`s (graded shades) + a thinner measure `<rect>` (the bar) + a `<line>` target tick crossing it.
- **Reuses:** orientation-transpose (usually horizontal); value axis (`nice_ticks`); band-layout (one row per KPI); chrome (often minimal, KPI-card mode); theme+palette; a11y; parity.
- **Net-new:** **qual-range-bands** (graded background rects from theme shades); **target-marker** (tick line); **compact/KPI layout mode** (minimal chrome).
- **Parity:** band thresholds + target coords via `f1`; shade selection deterministic from the theme palette.

---

## 4. The Cartesian EXTRACTION CONTRACT  *(one-time, gated — performed with Rank 1 / Column)*

**Grounding.** `libs/python/peakcharts/charts/line.py` (`render_svg`, lines 158–386) and `libs/go/line.go` (`renderLineSVG`, lines 189–492) are today ~95% the same program written twice. This contract separates that program into **shared cartesian chrome** (a new `_cartesian.py` / `cartesian.go`) and **line-specific marks** (what stays in `line.py`/`line.go`), and defines the byte-identity gate that proves the extraction changed nothing. Per Call #1, building Column **triggers** this extraction in **both** languages first (commit it on its own so the byte-preserving refactor is auditable). If `_cartesian.py`/`cartesian.go` already exist (a prior sibling created them), you **reuse and extend** them — never fork.

### 4.1 The single hard constraint that dictates the design: emission order

`render_svg` / `renderLineSVG` write one buffer in exactly this order (Python appends to list `p`; Go writes to one `strings.Builder`):

```
<svg …>                     ┐
  <desc>                    │
  <defs>…</defs>            │  CHROME — "head"
  <rect pk-bg>              │  (line.py 230–325 / line.go 312–407)
  <text pk-title/subtitle>  │
  <g pk-axis-y> gridlines+labels
  <line pk-axis-line>       │
  <g pk-axis-x> x labels    │
  axis titles (x, rot-y)    │
  <line pk-crosshair>       ┘
  <g pk-series>…</g> × N    ← MARKS (line.py 327–362 / line.go 410–456)
  <g pk-legend>…</g>        ┐  CHROME — "tail"
</svg>                      ┘  (line.py 364–385 / line.go 458–491)
```

Chrome is **not** one contiguous block — the series marks are sandwiched between a **head** and a **tail**. Byte-identity therefore forbids any "emit all chrome, then all marks" reshuffle. The abstraction must emit **head → (chart's marks) → tail** in place. **This is the load-bearing design fact.**

### 4.2 Inventory: SHARED CARTESIAN CHROME vs LINE-SPECIFIC MARKS

**SHARED CARTESIAN CHROME → moves to `_cartesian.py` / `cartesian.go`:**

| Concern | Python (line.py) | Go (line.go) | Phase |
|---|---|---|---|
| W/H, theme, palette pickup | 159–160 | 190–196 | frame build |
| a11y summary + `role`/`aria-label`/`<desc>` | `_a11y_summary` 145–155; 162–167 | `a11ySummary` 170–185; 197–202 | frame build (parameterize noun) |
| Margin math (`m_top/left/right/bottom`) | 170–177 | 204–223 | frame build |
| Plot rect (`plot_x/y/w/h`) | 179–180 | 225–228 | frame build |
| `n`, `cats` (categories or index fallback) | 183–184 | 230–242 | frame build |
| Value-axis range + `nice_ticks` → `y_min/y_max/y_ticks` — **include-zero is an explicit parameter:** ON for the column/bar/area value axis and the y baseline (`min(values+[0.0])`, `max(values+[0.0])`); OFF for a free numeric x (and free numeric y) scatter/bubble axis (§3.2 caveat). For **stacked/percent** the frame computes the y-max from the max column **total** (cumulative in the pinned summation order), NOT the per-datum max — the frame owns this, the marks never recompute a scale. | 187–190 | 244–262 | frame build |
| `xpix` / `ypix` | 192–198 | 264–272 | frame methods |
| `<defs>` pre-pass → `SeriesStyle(stroke, solid, area_fill, area_op, fill)`, `cid`, `defs_parts` | 202–228 (`_gradient_def`, `_pattern_def`) | 274–310 (`gradientDef`, `patternDef`, `seriesStyle`) | frame build |
| `<svg>` open (responsive + fixed) + font-family | 230–242 | 312–321 | head |
| `<desc>` emit | 244–246 | 323–326 | head |
| `<defs>` emit | 248–250 | 328–333 | head |
| background rect | 252–256 | 335–340 | head |
| title + subtitle | 258–270 | 342–353 | head |
| Y gridlines + labels (`_dash_array`) | 272–290 | 355–374 (`dashArray`) | head |
| axis line | 292–296 | 376–379 | head |
| X labels | 298–306 | 381–389 | head |
| axis titles (x + rotated y) | 308–319 | 391–402 | head |
| crosshair | 321–325 | 404–407 | head |
| legend (bottom-center) | 364–383 | 458–488 | tail |
| `</svg>` | 385 | 490 | tail |
| dash map `_DASH`/`dashArray` (used by **both** gridline chrome and line mark) | 23–27 | 11–20 | shared helper |

**LINE-SPECIFIC MARKS → stay in `line.py` / `line.go`:**

| Concern | Python | Go |
|---|---|---|
| Linear + step path builder | `_path_d` 30–53 | `pathD` 24–54 |
| Monotone spline (Fritsch–Carlson) | `_spline_d` 56–94 | `splineD` 58–109 |
| Point-marker shapes (circle/square/triangle/diamond) | `_marker` 97–113 | `markerSVG` 113–128 |
| Series loop body: build `pts`, choose spline vs step/linear `d`, area-fill path, `pk-series-line` path, `pk-point` markers w/ `data-*` | 327–362 | 410–456 |

`esc` / `fmt_num`/`fmtNum` / `nice_ticks`/`niceTicks` stay in `util.py`/`util.go` unchanged (already shared). Note `PALETTE` (line.py 17–20) is **dead** — the renderer uses `theme.palette` (line 160), never the module constant; **delete it** (it does not affect output). **Warning — delete ONLY line.py's module-level `PALETTE`.** The identical 8-hex literal in `spec.py` `Theme.palette` (and Go `lightTheme()`) is the **LIVE canonical default** every default-palette chart resolves through — do **NOT** delete or "consolidate" that copy, or every default-palette chart changes.

### 4.3 The abstraction: `CartesianFrame` + a marks callback (accumulator injection)

A chart renderer supplies **only** a marks function; the frame owns everything else. Because of the §4.1 sandwich, the orchestrator injects a **shared accumulator** (Python `list`, Go `*strings.Builder`) through **head → marks → tail**. Injecting **one** accumulator (rather than concatenating three returned strings) makes byte-identity true *by construction*: same writes, same order, same buffer as today's single-buffer renderer.

The **one generalization allowed during extraction** is a first-class **x-scale strategy** on the frame:
- **point scale** — `xpix(i) = plot_x + plot_w*i/(n-1)`, and `plot_x + plot_w/2` when `n<=1`. Used by line/area/scatter-with-categories. **Line MUST keep this exact formula so its bytes do not move.**
- **band scale** — categories occupy equal bands. Pinned formula (identical in both languages, this operation order): `band_width() = plot_w / n`; `xpix(i) = plot_x + band_width()*i + band_width()/2` (band center). Used by column/bar. The mark drawer builds sub-bands from `band_width()` with the §3.2 constants (`PAD=0.2`, `K=len(series)`).

The shared x-label loop calls `frame.xpix(i)`, so labels land under points (line) or band centers (column) with no per-chart label code. Line passes `x_scale="point"` (the default) and is byte-identical to today; **line keeps `x_scale="point"` unchanged** — only column/bar pass `"band"`.

**Python — `libs/python/peakcharts/charts/_cartesian.py`**

```python
from dataclasses import dataclass
from typing import Callable, List, Optional
from ..spec import ChartSpec, Theme

@dataclass
class SeriesStyle:                 # replaces the ad-hoc tuple in line.py 228
    stroke: str                    # hex or url(#grad)
    solid: str                     # representative solid — markers/legend/data-color
    area_fill: Optional[str]       # None = no area; else hex / url(#grad) / url(#pat)
    area_op: str                   # ' fill-opacity="…"' or ''
    fill: str                      # resolved BAR paint: url(#grad) / url(#pat) / solid hex
                                   #   (populated by the defs pre-pass; line ignores it → line bytes unchanged)

@dataclass
class CartesianFrame:
    spec: ChartSpec
    W: int; H: int
    theme: Theme
    plot_x: float; plot_y: float; plot_w: float; plot_h: float
    n: int; cats: List[str]
    y_min: float; y_max: float; y_ticks: List[float]
    cid: str
    styles: List[SeriesStyle]
    defs_parts: List[str]
    a11y_attr: str; a11y_desc: str
    scale: str                                 # "point" | "band"
    include_zero: bool                         # value-axis zero-anchor: True for value axis / y baseline, False for free numeric x/y
    stacking: Optional[str]                    # None | "normal" | "percent" — frame owns the stacked y-domain
    def xpix(self, i: int) -> float: ...        # line.py 192–195 verbatim for "point"; band center for "band"
    def ypix(self, v: float) -> float: ...      # line.py 197–198 verbatim
    def band_width(self) -> float: ...          # band scale only: plot_w / n

# Chart supplies ONLY this: append its marks for one plot into p.
MarksFn = Callable[[CartesianFrame, List[str]], None]

def build_frame(spec: ChartSpec, chart_noun: str, x_scale: str = "point",
                include_zero: bool = True) -> CartesianFrame: ...  # §4.2 "frame build"
#   include_zero=True  → value axis / y baseline (column/bar/area): force 0 into the domain
#   include_zero=False → free numeric x/y (scatter/bubble): domain from the data only
#   reads spec stacking mode → computes the stacking-aware y-domain on the FRAME (max column total)
def _chrome_head(fr: CartesianFrame, p: List[str]) -> None: ...   # §4.1 head, writes into p
def _chrome_tail(fr: CartesianFrame, p: List[str]) -> None: ...   # §4.1 tail, writes into p

def render_cartesian(spec: ChartSpec, chart_noun: str, x_scale: str, marks: MarksFn,
                     include_zero: bool = True) -> str:
    fr = build_frame(spec, chart_noun, x_scale, include_zero)
    p: List[str] = []
    _chrome_head(fr, p)
    marks(fr, p)          # chart appends its <g class="pk-series">…</g> blocks here
    _chrome_tail(fr, p)
    return "".join(p)     # single "".join, NO trailing newline

# moved chrome helpers (verbatim bodies):
def a11y_summary(spec: ChartSpec, chart_noun: str) -> str: ...   # was _a11y_summary; "Line"→noun
def gradient_def(gid, g) -> str: ...                              # was _gradient_def
def pattern_def(pid, pat) -> str: ...                             # was _pattern_def
_DASH = {"dashed": "5 5", "dotted": "2 3"}
def dash_array(style: str) -> str: return _DASH.get(style, "")   # was _dash_array
```

`a11y_summary` generalizes line.py 151 `f"Line chart with …"` to `f"{chart_noun} chart with …"`. **The noun is the bare word** — `"Line"`, `"Column"` — **not** `"Line chart"`. Called with `"Line"` it reproduces `"Line chart with N series…"` byte-for-byte.

**Go — `libs/go/cartesian.go` (same flat `package peakcharts`)**

```go
type seriesStyle struct { stroke, solid, areaFill, areaOp, fill string }  // moved from line.go 161–167; +fill = resolved bar paint

type cartesianFrame struct {
    spec                       *ChartSpec
    W, H                       int
    theme                      *Theme
    plotX, plotY, plotW, plotH float64
    n                          int
    cats                       []string
    yMin, yMax                 float64
    yTicks                     []float64
    cid                        string
    styles                     []seriesStyle
    defs                       string
    a11yAttr, a11yDesc         string
    scale                      string          // "point" | "band"
    includeZero                bool            // value-axis zero-anchor
    stacking                   string          // "" | "normal" | "percent" — frame owns the stacked y-domain
}
func (f *cartesianFrame) xpix(i int) float64     { … }   // line.go 264–269 verbatim for "point"; band center plotX + bandWidth()*i + bandWidth()/2 for "band"
func (f *cartesianFrame) ypix(v float64) float64 { … }   // line.go 270–272 verbatim
func (f *cartesianFrame) bandWidth() float64     { … }   // band scale only: plotW / float64(n)

type marksFn func(f *cartesianFrame, p *strings.Builder)

func buildFrame(spec *ChartSpec, noun, xScale string, includeZero bool) *cartesianFrame { … }  // §4.2 frame build; reads spec stacking → stacked y-domain
func chromeHead(f *cartesianFrame, p *strings.Builder)               { … }  // §4.1 head
func chromeTail(f *cartesianFrame, p *strings.Builder)               { … }  // §4.1 tail

func renderCartesian(spec *ChartSpec, noun, xScale string, marks marksFn, includeZero bool) string {
    f := buildFrame(spec, noun, xScale, includeZero)
    var p strings.Builder
    chromeHead(f, &p)
    marks(f, &p)
    chromeTail(f, &p)
    return p.String()
}
// moved chrome helpers (verbatim bodies): a11ySummary(spec, noun), gradientDef, patternDef, dashArray.
```

> **Line stays byte-identical:** line calls `renderCartesian(spec, "Line", "point", lineMarks, true)` — `include_zero=True` reproduces the existing `min(values+[0.0])`/`max(values+[0.0])` domain exactly, `stacking` is `None`/`""`, and the new `fill` field is populated but unread by line marks.

> **Caution — the no-area sentinel is per-language.** `SeriesStyle.area_fill` is Python `Optional[str]` (`None` = no area) but Go `areaFill string` (`""` = no area). This split is safe **ONLY** while a real fill value is never `""` and never a meaningful `None`. A future sibling that treats an empty-string fill as "transparent/inherit" would **diverge** — Python `area_fill is not None` would draw it while Go `areaFill != ""` would skip it. New fields must **not** overload these sentinels.

### 4.4 What `line.py` / `line.go` look like AFTER extraction

The series-loop body is **moved verbatim** — the only edits are rebindings: `sstyle[si]`→`fr.styles[si]`, bare `xpix`/`ypix`→`fr.xpix`/`fr.ypix`, `cats`→`fr.cats`, `theme`→`fr.theme`. Verbatim move is precisely what guarantees identical bytes. **When Rank 3 lands the point model** (the `data` element becomes a datum), the `for i, v in enumerate(s.data)` here changes to read `datum.y` (bare-number fast path → `y = float(v)`), in lockstep with `_column_marks` and `build_frame`'s y-range extractor, under the Rank 3 byte-identity gate — but at extraction time (Rank 1) `data` is still `number[]` and the loop is verbatim.

```python
# libs/python/peakcharts/charts/line.py
from ._cartesian import CartesianFrame, dash_array, render_cartesian
from ..spec import Marker
from ..util import fmt_num
# keep: _path_d, _spline_d, _marker (unchanged)

def render_svg(spec) -> str:
    return render_cartesian(spec, "Line", "point", _line_marks)   # include_zero defaults True

def _line_marks(fr: CartesianFrame, p: list) -> None:
    theme = fr.theme
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        pts = [(fr.xpix(i), fr.ypix(v)) for i, v in enumerate(s.data)]
        d = _spline_d(pts) if s.curve == "monotone" else _path_d(pts, s.step)
        lw = s.line_width if s.line_width is not None else 2
        line_dash = dash_array(s.dash_style)
        line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
        p.append(f'<g class="pk-series" data-series="{si}">')
        if st.area_fill is not None and pts:
            base = fr.ypix(0.0)                       # NOT recomputed — call fr.ypix(0.0)
            area_d = f"{d} L{pts[-1][0]:.1f} {base:.1f} L{pts[0][0]:.1f} {base:.1f} Z"
            p.append(f'<path class="pk-series-area" data-series="{si}" d="{area_d}" '
                     f'fill="{st.area_fill}"{st.area_op} stroke="none"/>')
        p.append(f'<path class="pk-series-line" data-series="{si}" d="{d}" fill="none" '
                 f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}" stroke-linejoin="round" '
                 f'stroke-linecap="round"{line_dash_attr}/>')
        mk = s.marker or Marker()
        if mk.enabled:
            ...   # line.py 350–361 verbatim, using fr.cats, st.solid, theme.marker_halo
        p.append("</g>")
```

```go
// libs/go/line.go — keep pathD, splineD, markerSVG (unchanged)
func renderLineSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Line", "point", lineMarks, true)
}
func lineMarks(f *cartesianFrame, p *strings.Builder) {
    theme := f.theme
    for si, s := range f.spec.Series {
        st := f.styles[si]
        pts := make([][2]float64, len(s.Data))
        for i, v := range s.Data { pts[i] = [2]float64{f.xpix(i), f.ypix(v)} }
        var d string
        if s.Curve == "monotone" { d = splineD(pts) } else { d = pathD(pts, s.Step) }
        ...   // line.go 423–455 verbatim, using f.cats, st.*, theme.MarkerHalo
    }
}
```

`render.py` (`_RENDERERS = {"line": _line.render_svg}`, line 23) and `render.go` (`RenderSVG` switch, line 69) are **untouched** — both still resolve to the same renderers.

### 4.5 Migration map (symbol → destination)

> **Caution — line numbers are APPROXIMATE.** Every source line number quoted in this extraction contract (§4.1–§4.5) has already **drifted by 1–3 lines** against the current files and will keep drifting. **Locate code by SYMBOL NAME** (function / variable), then **re-verify the current line range** before moving anything — never slice purely by the numbers quoted here.

| Symbol | From | To |
|---|---|---|
| `_a11y_summary`→`a11y_summary(spec,noun)`, `a11ySummary` | line | `_cartesian.py` / `cartesian.go` |
| `_gradient_def`/`gradientDef`, `_pattern_def`/`patternDef` | line | cartesian |
| `_DASH`+`_dash_array`, `dashArray` | line | cartesian |
| `seriesStyle` struct (+ new `fill` field) | line.go | cartesian.go |
| margins/plot/`n`/`cats`/y-range/`xpix`/`ypix`/defs-prepass | inline in renderer | `build_frame`/`buildFrame` + frame methods |
| head chrome writes | inline | `_chrome_head`/`chromeHead` |
| legend + close | inline | `_chrome_tail`/`chromeTail` |
| `_path_d`,`_spline_d`,`_marker` / `pathD`,`splineD`,`markerSVG` | line | **stay** |
| series loop body | inline | `_line_marks`/`lineMarks` |
| `PALETTE` (dead — the line.py module constant ONLY, **not** `spec.py` `Theme.palette`) | line.py 17–20 | **delete** (see §4.2 warning) |

**No change to:** `util.*`, `spec.*`, `validate.*`, `render.*`, `runtime/chart-interactions.js`, `spec/svg-contract.md`, `spec/themes/*.json`, every `charts/line-basic/golden/*.svg`, every `examples/*.json`.

### 4.6 Byte-identity VERIFICATION GATE

The invariant: after extraction the line goldens are **100% byte-identical** (`git diff` empty) and Python==Go still holds. Both existing suites (`test_golden.py::_check`, `render_test.go::TestGolden`) already pin each renderer to the **same** committed `charts/line-basic/golden/*.svg`. That shared pin is what turns "both green" into "Python==Go==baseline."

**Before extraction — widen the corpus so the moved label/fallback chrome is actually witnessed.** All 8 existing line fixtures have `len(categories) == max(len(data))` AND supply `categories` explicitly, so two pieces of chrome that move into `_chrome_head` are **never exercised**: (a) the x-label loop bound (Python `cats[:n]` vs Go `i<n && i<len(cats)`) is never stressed with `len(categories) != n`, and (b) the absent-`categories` index fallback (`cats = [str(i) for i in range(n)]`) is never hit at all. A regression in either would pass Gates 2–4 and give false confidence. **So, before touching code, add to the line golden set (or the first column set) at least: one fixture with `len(categories) > max(len(data))`, one with `len(categories) < max(len(data))`, and one with `categories` entirely absent (exercises the index fallback). Regenerate their goldens from the CURRENT renderer so they pin the pre-refactor bytes, THEN extract.** This makes Gates 2–4 actually cover the moved label/fallback paths.

- **Gate 0 — Freeze the baseline (before touching code).** `git status --porcelain charts/line-basic/golden/` → empty. Green on current code: `python libs/python/tests/test_golden.py`; `pytest libs/python/tests/`; `cd libs/go && go test ./...`. Record the target hashes (`Get-FileHash charts/line-basic/golden/*.svg`), **including the newly-added category-edge fixtures above** — none may move.
- **Gate 1 — Refactor touches renderers only.** Extraction edits `line.py`, `line.go` and adds `_cartesian.py`, `cartesian.go`. It **must never** write under `charts/line-basic/golden/**` or `examples/**`. If a golden shows modified, the extraction changed output — **stop and fix the extraction; never regenerate goldens to make tests pass.**
- **Gate 2 — Golden pin (primary proof).** `python libs/python/tests/test_golden.py` GREEN ⇒ Python == committed golden byte-for-byte (all fixtures incl. the category-edge ones). `cd libs/go && go test -run TestGolden ./...` GREEN ⇒ Go == committed golden. Both green ⇒ Python == Go == pre-refactor baseline for `basic, styled, markers, spline, gradient, dark, adversarial, gradient-partial` **plus the added `cats>n`, `cats<n`, and `cats-absent` fixtures**.
- **Gate 3 — `git diff` empty on goldens (headline gate).** `git diff --stat charts/line-basic/golden/` → empty. Overall `git diff --stat` should show only `line.py`, `line.go` (shrunk) + new `_cartesian.py`, `cartesian.go`. That diff shape **is** the evidence the change is a pure refactor.
- **Gate 4 — Direct Python==Go cross-render (independent of goldens).** For each `charts/line-basic/examples/*.json` (incl. the category-edge fixtures), render with the Go CLI and with Python's `render_svg`, and `diff` — empty for all. Catches drift even if a golden were stale.
- **Gate 5 — Chrome+marks wiring regressions.** These exercise the seam and must stay green in both suites: `test_xss_escaping`/`TestXSSEscaping`, `test_a11y_toggle`/`TestA11yToggle` (confirms the a11y-noun parameterization preserves `role=img`/`<desc>` on-off bytes), `test_theme_json_parity`/`TestThemeJSONParity`, `test_invalid_fixtures_parity`/`TestInvalidFixturesParity`, `test_spline_edge_cases`/`TestSplineEdgeCases`.

**Pass condition:** Gates 2, 3, 4, 5 all green with **zero bytes changed** in `charts/line-basic/golden/` (including the newly-pinned category-edge fixtures).

### 4.7 Byte-identity gotchas to enforce during the port

1. **One accumulator, not three concatenations.** Inject `p`/`*strings.Builder` through head→marks→tail. Do not have head/tail return strings a caller re-joins — accumulator injection removes any doubt and mirrors today's single buffer.
2. **`fr.ypix(0.0)` for the area baseline.** line.py 338 / line.go 430 call `ypix(0.0)`; the moved marks must call `fr.ypix(0.0)`, never recompute a baseline.
3. **`a11y_summary` noun default.** Passing `"Line"` must reproduce `"Line chart with N series…"` exactly (line.py 151 / line.go 179). The noun is the bare word.
4. **Dash helper is shared, not duplicated.** `dash_array`/`dashArray` lives once in cartesian and is imported by line — gridline (chrome) and series line (mark) must call the **same** function so `"5 5"`/`"2 3"` can't drift.
5. **`.1f` vs `fmt_num` placement is load-bearing.** The moved marks keep `f"{x:.1f}"`/`f1(...)` for coordinates and `fmt_num`/`fmtNum` for radii/line-width exactly where the originals use them. Do **not** "normalize" these during the move.
6. **Frame is per-render, not cached.** `xpix`/`ypix` close over `n`, `plot_*`, `y_min/max` — store them on the frame and read them in the methods; do not memoize across specs.
7. **`include_zero` reproduces line exactly.** Line passes `include_zero=True`; the frame's value-axis math must stay `min(values+[0.0])`/`max(values+[0.0])` for that case so line bytes do not move. The `False` path (free numeric x/y) is exercised only by scatter/bubble.

This contract lets Column be added as a second marks callback + `render_cartesian(spec, "Column", "band", _column_marks)` with **zero** duplication of axes/scales/legend/theme/a11y/defs, while the line goldens remain the frozen witness that the shared chrome still renders identical bytes.

---

## 5. The per-chart-type coordination procedure

**Authority.** This section is a detailed engineering procedure, not current release
authority. Before adding a Cartesian/XY type, the procedure must be reviewed against
the active requirements, contracts, ADRs, and renderer constitution. Any adopted step
is then linked from the governing requirement and verified through release evidence.

**The six non-negotiables you are protecting (do not break any):**
1. Python and Go emit **byte-identical SVG** for the same spec (golden-tested).
2. **Static-first:** the SVG is complete and readable with JS disabled; `runtime/chart-interactions.js` only *enhances*.
3. **Strict shared validation:** `validate.py` and `validate.go` produce **identical** `$.path: expected X, received Y` errors; defaults apply only on *absence*, never to coerce malformed input.
4. **Accessibility default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG; a separate visually-hidden data table in the HTML; keyboard nav.
5. **Themes** resolved server-side into concrete SVG attributes (`spec/themes/*.json`, baked + JSON-parity-tested).
6. All user strings via `esc`; all numbers via `fmt_num`/`fmtNum` (data values) or `:.1f`/`f1` (pixel coordinates).

**Golden rule of this contract:** the chart renderer draws **only the series marks** (the inner content of `<g class="pk-series">…</g>`). Every piece of chrome — margins, scales, ticks, gridlines, axis lines, axis titles, legend, crosshair, background, `<defs>`, theme resolution, a11y summary, `<svg>` open/close — is obtained from the **shared cartesian module** (§4). You may **never** re-implement any of it in a chart renderer. (The frame also owns the value-axis domain, including the stacking-aware y-max — the marks never compute a scale.)

### 5.0 Vocabulary & source-of-truth map

| Concern | Python | Go |
|---|---|---|
| Per-chart renderer | `libs/python/peakcharts/charts/<id>.py` → `render_svg(spec)` | `libs/go/<id>.go` (`package peakcharts`) → `render<Id>SVG(spec)` |
| Dispatch registry | `render.py` `_RENDERERS: Dict[str, Callable]` | `render.go` `RenderSVG` `switch spec.Type` |
| Shared spec model | `peakcharts/spec.py` (dataclasses + `ChartSpec.from_dict`) | `libs/go/spec.go` (structs + `FromJSON` + `applyDefaults`) |
| Strict validator | `peakcharts/validate.py` `validate(d) -> List[str]` | `libs/go/validate.go` `validate(raw) -> []string` |
| Shared utils | `peakcharts/util.py` `esc`, `fmt_num`, `nice_ticks` | `libs/go/util.go` `esc`, `fmtNum`, `f1`, `niceTicks` |
| Shared cartesian module (§4) | `peakcharts/charts/_cartesian.py` | `libs/go/cartesian.go` |
| Schema (doc SoT) | `spec/chart-spec.schema.json` | same file |
| Themes (canonical) | `spec/themes/{light,dark}.json` | same files (baked + parity-tested) |
| DOM contract | `spec/svg-contract.md` | same file |
| Runtime (never edit for a new chart) | `runtime/chart-interactions.js` | same file |
| Golden harness | `libs/python/tests/test_golden.py` | `libs/go/render_test.go` |

Two facts you rely on:
- **The validator does NOT currently gate `type`** — it only checks `type` is a string, **not** that it names a known chart. Because of that gap an unknown/bogus `type` slips past validation and is caught only at **dispatch — where the two languages DIVERGE:** `render.py` raises a **catchable `ValueError`**, while `render.go` **`panic`s** in `default` (an uncatchable crash). This is a **real behavioral divergence, not a symmetric rejection.** **Contract obligation:** when a sibling adds a new chart type it MUST add that type to a **validated known-type set in BOTH `validate.py` and `validate.go`**, so an unknown/bogus `type` is rejected **identically as a `SpecError` before dispatch** (same `$.type` error text in both languages) instead of Python-raises / Go-panics. So "registering a chart type" = adding it to the two dispatchers, the schema `enum` (docs), **and** the shared known-type validation set.
- **Goldens carry no trailing newline** and are UTF-8 (no BOM). `render_svg` returns a single `"".join(...)` with no terminal newline; a stray trailing `\n` fails the byte compare.

### 5.1 Exact files to create / modify

Let `<id>` be the new chart id (kebab-case, matches `spec.type`, e.g. `column`); `<Id>` its Go-exported camel form (e.g. `Column`).

**Create (new chart):**
```
charts/<id>/design.md                     # self-contained recipe (copy line-basic/design.md structure)
charts/<id>/examples/<case>.json          # one spec per golden case
charts/<id>/golden/<case>.svg             # byte-reference SVG per case (UTF-8, no trailing newline)
charts/<id>/invalid-fixtures.json         # ONLY if the chart adds any new validated spec field (§5.5b)
libs/python/peakcharts/charts/<id>.py     # renderer: render_svg(spec)
libs/go/<id>.go                           # renderer: render<Id>SVG(spec) (package peakcharts)
```

**Create once, on the FIRST sibling (the §4 extraction):**
```
libs/python/peakcharts/charts/_cartesian.py
libs/go/cartesian.go
```
If these exist (a prior sibling created them), **reuse and extend** — do not fork.

**Modify (registration + wiring):**
```
libs/python/peakcharts/render.py          # _RENDERERS["<id>"] = _<id>.render_svg  (+ import)
libs/go/render.go                         # add `case "<id>": return render<Id>SVG(spec)` to RenderSVG
spec/chart-spec.schema.json               # add "<id>" to properties.type.enum (+ any new field defs)
libs/python/tests/test_golden.py          # add the new chart's cases + invalid-fixtures wiring (§5.6)
libs/go/render_test.go                    # add the new chart's cases + invalid-fixtures wiring (§5.6)
CHARTS.md                                 # add a catalog row + decision-guide entry
docs/roadmap/chart-families.md            # tick the built item
```
Only touch `runtime/chart-interactions.js`, `spec/themes/*.json`, `util.py`/`util.go` with a specific sanctioned reason (§5.4 forbids the first for a chart add; the others are shared-core changes with their own parity tests).

### 5.2 Renderer signature — how it obtains geometry and chrome

The chart renderer is a **one-line delegation** to the shared orchestrator (§4.3), supplying only a marks callback. It obtains everything but the marks from the shared module. It must **never** call `nice_ticks`, resolve a theme, format an axis, build a legend, open the `<svg>`, emit `<defs>`, or compute any y-domain (including the stacked/percent y-max — the **frame** owns that) itself.

**Python (`charts/<id>.py`)**
```python
from ..spec import ChartSpec
from ..util import esc, fmt_num                      # marks may need these directly
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec: ChartSpec) -> str:
    return render_cartesian(spec, "Column", "band", _column_marks)   # noun="Column", band scale, include_zero defaults True (value axis)

def _column_marks(fr: CartesianFrame, p: list) -> None:
    for si, s in enumerate(fr.spec.series):
        # emit exactly ONE <g class="pk-series" data-series="{si}">…</g> per series into p
        ...
```

**Go (`<id>.go`)**
```go
func renderColumnSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Column", "band", columnMarks, true)
}
func columnMarks(f *cartesianFrame, p *strings.Builder) {
    for si := range f.spec.Series {
        // emit exactly ONE <g class="pk-series" data-series="si">…</g> per series into p
        ...
    }
}
```

**Registration (mandatory, both languages):**
- Python `render.py`: `from .charts import column as _column` then `_RENDERERS["column"] = _column.render_svg`.
- Go `render.go`: add `case "column": return renderColumnSVG(spec)` to the `RenderSVG` switch (before `default`).

**Hard rules for the marks function:**
- Emits exactly one `<g class="pk-series" data-series="{si}">…</g>` per series, nothing outside it.
- Uses `fr.xpix`/`fr.ypix`/`fr.band_width` for **all** geometry — computes **no** scale of its own (the frame owns the value-axis domain, incl. the stacking-aware y-max).
- Baseline for bars/area is `fr.ypix(0.0)` — the shared value-axis (with `include_zero=True`) already forces 0 into the domain; do **not** special-case it.
- Every number it prints is formatted per §5.3 — never raw `str(float)` / `strconv.FormatFloat` with other precision.

### 5.3 DOM-contract compliance (`spec/svg-contract.md`) — emit these so the runtime enhances with ZERO JS changes

The runtime keys **only** on the selectors + `data-*` below. Emit them correctly and tooltip, highlight, crosshair, legend-toggle, keyboard nav, and `<defs>` id-scoping all work with no runtime edit. The shared head/tail already emit `svg.pk-chart`, `.pk-crosshair`, `.pk-legend`/`.pk-legend-item`, and `<defs>`. **Your marks emit the series group and the points.**

**Required structure your marks produce:**
```html
<g class="pk-series" data-series="0">
  <!-- optional visible mark(s): bar rect / area path / connecting line -->
  <rect class="pk-point" data-series="0"
        data-series-name="Tokyo" data-x="Jan" data-y="7"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="123.4" cy="88.0"  x="…" y="…" width="…" height="…" fill="#2f7ed8"/>
  … one .pk-point per datum …
</g>
```

**The non-negotiable emission rules:**
1. **The whole series group is `.pk-series[data-series=N]`.** The legend toggle does `querySelectorAll('[data-series="N"]')` and flips `display` on every match except the legend item. Anything that must hide with the series carries `data-series="N"` — the group already does, so nested marks inherit. Keep `N` an integer string equal to the series index, **consistent** across the group, its points, and the legend item (emitted by the shared tail with the same index — do not renumber).
2. **The datum mark is `.pk-point`** and MUST carry all of: `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`. Mandatory even for non-circular marks (a bar `<rect>`): the runtime calls `pt.setAttribute("r", …)` on hover — a `<rect>` ignores `r` (harmless), but the attributes must be present for contract conformance and the tooltip body.
3. **Every `.pk-point` MUST carry a `cx`** (and by convention `cy`). The crosshair reads `pt.getAttribute("cx")` to position the vertical guide. For a bar, `cx` = bar center x; `cy` = bar top (or center). Without `cx` the crosshair breaks.
4. **Escaping / formatting inside `data-*`:** `data-series-name` = `esc(s.name)`; `data-x` = `esc(<category label>)` (or a numeric value via `fmt_num` on a numeric-x chart); `data-y` = `esc(fmt_num(value))`; `data-color` = the resolved solid (`fr.styles[si].solid`, already escaped); `data-r`/`data-r-hover` = `fmt_num(...)`. Pixel attributes (`cx,cy,x,y,width,height`) use `:.1f`/`f1`. **Under stacking:** for stacked / percent bars the geometry uses cumulative baselines, but `data-y` MUST carry the **raw per-series segment value** (the datum's own value), **not** the running cumulative total — the tooltip shows the value the user supplied, not the stack sum.
5. **Do not invent new classes the runtime must know about.** You may add purely-cosmetic classes (e.g. `pk-bar`) for CSS, but runtime behaviors are driven only by the contract selectors above. Adding a behavior that needs new JS is **out of scope** for a chart add (it breaks non-negotiable #2's "zero JS changes").
6. **Static correctness:** the chart must be fully readable with JS disabled. The crosshair ships `style="display:none"` (from the shared head); the tooltip is JS-only. Everything else is server-rendered.

**Bar-fill resolution (a real byte-parity + NN#2 trap).** A bar has ONE fill that may be solid / gradient / pattern — the line-shaped `SeriesStyle` (`stroke, solid, area_fill, area_op`) does not carry it directly (`area_fill` is `None` unless `fillOpacity>0`/pattern, and line relies on `stroke==fill_color`). The extraction therefore adds a **`fill` field to `SeriesStyle`** (populated by the defs pre-pass, §4.3; unread by line so line bytes do not move). Your bar mark reads `fr.styles[si].fill`, resolved as: **pattern → the pattern `url(#pat)` ref; gradient → the gradient `url(#grad)` ref; else the solid hex.** Never leave a basic column unfilled (an unfilled bar is a broken static chart — NN#2), and never silently drop gradient/pattern by reading `solid`.

**Number/string formatting parity table (a real byte-parity trap):**

| What you emit | Python | Go |
|---|---|---|
| Pixel coordinate (`cx,cy,x,y,width,height`, path `d` numbers) | `f"{v:.1f}"` | `f1(v)` |
| Data value, radius, opacity, offset, tile size, angle, stroke width, tick label | `fmt_num(v)` | `fmtNum(v)` |
| Integer literals (`W`, `H`, series index, `font-size="11"`) | `str(int)` / literal | `%d` / literal |
| Any user string (name, label, color, category) | `esc(s)` | `esc(s)` |

Never format a float any other way. `fmt_num`/`fmtNum` are parity-locked (`%g` 6-sig, `.0` dropped, NaN/Inf→`"0"`); `f1`/`:.1f` are parity-locked to one decimal. Mixing formatters between languages is the #1 cause of a byte diff.

### 5.4 Mandatory reuse of the strict validator, `esc`, and number formatting

**5.4a — If your chart adds NO new spec field.** You inherit all validation for free — the existing validators cover `type/id/theme/title/subtitle/width/height/legend/a11y/xAxis/yAxis/series[...]`. Do nothing to the validators; confirm every `examples/*.json` passes `validate() == []`. **Column is NOT such a case** — its `stacked`/`grouped`/`percent` mode is selected by a **new `stacking` (+ grouping) spec field** with no existing selector anywhere (`spec.*`, `validate.*`, schema), so you physically cannot render a `stacked` golden differently from `grouped`/`basic` without it, and an unvalidated `stacking` key would be silently ignored by both parsers (breaking NN#3). Column therefore follows **§5.4b** for that field. (A genuinely field-free sibling is one whose spec shape is exactly the line spec's — e.g. a mark-only restyle.)

**5.4b — If your chart adds ANY new spec field.** Every new field MUST be added in **five places, in lockstep**, or you break non-negotiable #3 and/or #1. Worked example: `series[].borderRadius` (number, default `0`). (Column's `stacking`/`grouping` selector and waterfall's `isSum` are real instances of the same five-place drill.)
1. **Schema** (`spec/chart-spec.schema.json`): add the property under the right `definitions` node with `type` + `default` + `description`. Keep the `additionalProperties`-open, forward-compatible stance.
2. **`validate.py`:** add a rule in the matching helper using existing primitives so error text is identical. For a series-level number, inside `_series`: `if "borderRadius" in v: _num(v["borderRadius"], f"{path}.borderRadius", errs)`. Use `_num`/`_intnum`/`_str`/`_bool`/`_str_array` — never bespoke error strings. Defaults are **not** applied here.
3. **`validate.go`:** the exact mirror — same path, byte-identical wording: `if hasKey(m, "borderRadius") { vnum(m["borderRadius"], path+".borderRadius", &errs) }`.
4. **Spec model — Python** (`spec.py`): add the dataclass field + default (`border_radius: float = 0.0`), parsed in `from_dict` with **default-on-absence only** (mirror `_opt_float`/`s.get(..., default)`; never coerce).
5. **Spec model — Go** (`spec.go`): add the struct field with the right `json:` tag and `omitempty`/pointer semantics reproducing the Python default exactly (use `*float64` + accessor when "absent" must differ from a real `0`, as `Gradient`/`Marker`/`GridLine` already do). Wire the default into `applyDefaults`/an accessor. Decode-then-default must yield the same value Python yields for both "absent" and "present".
6. **Invalid fixtures** (`charts/<id>/invalid-fixtures.json`): add ≥1 hostile case per new field (`{"borderRadius":"x"} → "$.series[0].borderRadius: expected number, received string"`), and wire the file into both parity tests (§5.6c). This proves the two validators reject identically.

**5.4b-DT — Point-model / accessible-data-table obligation.** The shared HTML **accessible data table** (`_data_table`/`dataTable`, a hard a11y non-negotiable, NN#4) assumes `series.data` is `number[]`. **When a chart's `data` stops being `number[]`** (scatter `{x,y}`, bubble `{x,y,z}`, candlestick `{o,h,l,c}`, area-range `{low,high}`, …), the data table MUST be generalized in **lockstep in both languages** to render the point model faithfully (not a coerced single number per row), with a test proving Py==Go table bytes. A future sibling may NOT ship an a11y-broken/misrepresenting table while passing the golden gates — this obligation is part of "adding a new data shape," alongside the §5.4b field drill and the Rank-3 byte-identity gate (§3.3).

**5.4c — `esc` and number formatting are mandatory everywhere.** Any user-controlled string reaching the SVG/HTML (series name, category, custom color, title, chart `id`, theme colors) goes through `esc`; the shared module escapes chrome/theme values, your marks must `esc` the strings they emit (`data-series-name`, `data-x`, custom mark colors). XSS tests fail if you leak a raw `<`. Numbers use `fmt_num`/`fmtNum` (values) or `:.1f`/`f1` (coordinates) per §5.3 — no exceptions.

### 5.5 Golden + cross-language parity test wiring

Both suites pin **both** renderers to the **same** golden files in `charts/<id>/golden/`. If both pass, each language equals the shared bytes, therefore they equal each other. Wire the new chart into **both CASES lists**.

**5.5a — Python (`test_golden.py`).** Generalize the line-hardcoded `_check` to be chart-aware, keeping line working, then add cases:
```python
def _check(chart_id: str, name: str):
    spec_path   = ROOT / "charts" / chart_id / "examples" / f"{name}.json"
    golden_path = ROOT / "charts" / chart_id / "golden"   / f"{name}.svg"
    spec = ChartSpec.from_dict(json.loads(spec_path.read_text(encoding="utf-8")))
    assert render_svg(spec) == golden_path.read_text(encoding="utf-8"), name

LINE_CASES   = ["basic","styled","markers","spline","gradient","dark","adversarial","gradient-partial"]
COLUMN_CASES = ["basic","grouped","stacked","dark","adversarial"]

def test_line_golden():   [_check("line-basic", n) for n in LINE_CASES]
def test_column_golden(): [_check("column", n)     for n in COLUMN_CASES]
```
**Migrate the existing call sites — the `_check` signature changed from one arg to two, so the eight current callers WILL break if left alone.** Rewrite every existing single-arg caller (`test_line_basic_golden` … and any `_check("basic")`-style call) to the two-arg form `_check("line-basic", name)` — or collapse them into the single `test_line_golden` above — and update the `__main__` runner from `for _n in CASES: _check(_n)` to iterate `(chart_id, cases)` pairs (`for cid, cases in [("line-basic", LINE_CASES), ("column", COLUMN_CASES)]: for n in cases: _check(cid, n)`). **Keep `test_spline_edge_cases()` intact.** Do not change what bytes the existing line tests compare against. (Leaving a stale 1-arg caller against the 2-arg `_check` = `TypeError`, whole Python suite red before Column is even exercised.)

> **pytest coverage rule (a real gap — fixed for `gradient-partial`, keep it fixed).** Plain `pytest libs/python/tests/` runs **only** the explicit per-case `test_line_<name>_golden` functions; a fixture that exists **only** in the `CASES` list / `__main__` loop (run by `python … test_golden.py`) is **NOT** covered by pytest. So every golden fixture MUST have **both** a per-case pytest function **AND** a `CASES` entry — otherwise pytest silently skips it while `python … test_golden.py` still checks it.

**5.5b — Go (`render_test.go`).** Make `TestGolden` iterate a `chartID → cases` table:
```go
func TestGolden(t *testing.T) {
    suites := map[string][]string{
        "line-basic": {"basic","styled","markers","spline","gradient","dark","adversarial","gradient-partial"},
        "column":     {"basic","grouped","stacked","dark","adversarial"},
    }
    for chartID, cases := range suites {
        for _, name := range cases {
            specBytes, err := os.ReadFile("../../charts/"+chartID+"/examples/"+name+".json")
            if err != nil { t.Fatal(err) }
            spec, err := FromJSON(specBytes); if err != nil { t.Fatal(err) }
            want, err := os.ReadFile("../../charts/"+chartID+"/golden/"+name+".svg")
            if err != nil { t.Fatal(err) }
            if got := RenderSVG(spec); got != string(want) {
                t.Errorf("%s/%s: SVG != golden (got %d, want %d bytes)", chartID, name, len(got), len(want))
            }
        }
    }
}
```
(Map iteration order is irrelevant — each case is an independent assertion.)

**5.5c — Invalid-fixtures parity (only if §5.4b applied).** Generalize `test_invalid_fixtures_parity`/`TestInvalidFixturesParity` to read **both** `charts/line-basic/invalid-fixtures.json` and `charts/<id>/invalid-fixtures.json`, asserting `validate(spec) == errors` for every case. Same file, both languages → both validators reject identically.

**5.5d — Reuse the cross-cutting tests.** Do not duplicate them, but ensure your chart passes: XSS escaping, a11y toggle (`role="img"`+`<desc>` on / absent off), theme JSON parity, malformed-no-panic/valid-edges-render.
- **XSS is NOT vacuously covered.** `test_xss_escaping`/`TestXSSEscaping` hardcode `type:"line"`, so as-is they assert **nothing** about Column's own marks (`data-x`, `data-series-name`, custom bar color). **Requirement:** the Column `adversarial` example MUST carry hostile strings (`<script>`, `"`, `<`, `&`) in **every** field the marks emit (series name, category label, custom color), AND either (a) parameterize `test_xss_escaping`/`TestXSSEscaping` over the chart id so they run against Column too, or (b) assert in a test that the Column adversarial golden contains the **escaped** bytes and **no** raw `<script>`. A Column renderer that leaks a raw `<` must fail a test.
- If your chart adds a numeric transform (e.g. stacking, or the bubble **size-scale**), add an edge-case test analogous to `test_spline_edge_cases` (flat/negative/single/mixed data stays finite — no `NaN`/`Inf`). For **bubble** specifically this means the all-equal-`z`/single-point/out-of-domain cases (§3.3 Rank 4) assert finite radius output and Py==Go.

**5.5e — Generating the golden files.** Goldens are generated **once** from the shared logic, then both suites verify them:
1. Write each `charts/<id>/examples/<case>.json`.
2. Generate the reference SVG with the **Python** renderer (canonical), writing **UTF-8, no BOM, no trailing newline**:
   ```python
   import json, pathlib
   from peakcharts import ChartSpec
   from peakcharts.render import render_svg
   for case in COLUMN_CASES:
       spec = ChartSpec.from_dict(json.load(open(f"charts/column/examples/{case}.json", encoding="utf-8")))
       pathlib.Path(f"charts/column/golden/{case}.svg").write_text(render_svg(spec), encoding="utf-8")
   ```
3. Run **both** suites. If Go fails, that is a **Python↔Go divergence to fix in code**, never a golden to regenerate to match a broken language. Only regenerate a golden when you intentionally changed the spec fixture.

### 5.6 The byte-identity GATES (all must be green to land)

- **Gate A — extraction is byte-preserving (only when you performed §4):** `git diff --stat -- charts/line-basic/golden/` empty; `python libs/python/tests/test_golden.py` all PASS; `cd libs/go && go test ./...` green. Unchanged goldens + green tests = line SVG did not move a byte. (Applies to the widened corpus too — the added `cats>n`/`cats<n`/`cats-absent` fixtures must be pinned and unchanged, §4.6.)
- **Gate A′ — data-element-type change is byte-preserving (any rank that changes the `data` element, e.g. Rank 3 point-model):** `git diff` empty on **ALL** existing goldens — every line fixture **and** every prior sibling (column) — proving the bare-number fast path reproduces the exact pre-change bytes; plus a Py==Go cross-render on all of them. This is a golden-diff **proof**, not an assertion (§3.3 Rank 3).
- **Gate B — new chart is Python == Go on every fixture:** both suites' new-chart cases pass against the **same** `charts/<id>/golden/*.svg`. Belt-and-suspenders: render one fixture in each language to files and `diff` — empty.
- **Gate C — default output stays additive-only:** no existing golden (line's or any prior sibling's) changes — `git status charts/*/golden/` shows only **new** files. The shared head/tail must not emit new empty elements (no stray `<defs>`, no background `<rect>` under the light theme) — defs are emitted only when a series needs them (as `line` gates `<defs>` on `defs_parts`). Any deliberate baseline change is out of scope for a chart add and follows the separate "regenerate all goldens in lockstep" policy in `docs/customization/plan.md`.

**Byte-parity traps checklist (verify before Gate B):**
- Trailing newline in a golden → fails compare. Goldens have none.
- A float printed with `str()`/`FormatFloat(...,-1,64)` instead of `fmt_num`/`f1`.
- Go `range`-over-map producing output in nondeterministic order (never build ordered SVG from a map; iterate `spec.Series` by index).
- A `data-*` string not run through `esc`.
- Series/point/legend `data-series` indices drifting apart.
- A default resolved differently across languages for an "absent" field (Go zero-value vs Python `None`) — use pointers/accessors in Go to distinguish absent from `0`/`""`.
- A degenerate numeric op (e.g. bubble `0/0` size-scale, or a stacked/percent divide-by-zero total) diverging: Python raises, Go yields `NaN`→`"0"`. Pin the degenerate rule identically **before** the divide (§3.2 size-scale, §3.3 Rank 4).
- Emitting a `<defs>` or background `<rect>` unconditionally (breaks Gate C).

### 5.7 Step-by-step checklist (follow in order)

1. **Read** `spec/svg-contract.md`, `charts/line-basic/design.md`, this document (§3–§5), and `docs/customization/plan.md` (golden policy).
2. **Classify** the chart (variant / sibling / new-family per §1.3, §2). This contract covers **siblings on the existing Cartesian substrate**. If it needs a new substrate (polar, matrix, hierarchy…), **stop** — that is a separate planning doc, not this procedure.
3. **If this is the first sibling:** perform the §4 extraction into `_cartesian.py` + `cartesian.go` (incl. widening the corpus with the category-edge fixtures, §4.6); pass **Gate A**. Commit the extraction on its own so the byte-preserving refactor is auditable.
4. **Write** `charts/<id>/design.md` (copy `line-basic/design.md` structure: id, spec `type`, renderer paths, contract link, data shape, spec-field table, example spec, generate snippets, rendering notes, roadmap). It must be self-contained.
5. **If new spec fields:** add them in all five places + invalid fixtures (§5.4b). Confirm `validate()` parity mentally against the error-text format. **If the `data` element type changes**, also generalize the accessible data table in lockstep (§5.4b-DT) and plan for Gate A′.
6. **Implement the Python renderer** `charts/<id>.py`: `render_svg` = one-line `render_cartesian(spec, noun, x_scale, _marks)` (pass `include_zero=False` for a free numeric x/y chart); `_marks` emits the §5.3 DOM contract exactly. Use `esc` + `fmt_num`/`:.1f`.
7. **Implement the Go renderer** `<id>.go` (`package peakcharts`): `render<Id>SVG` mirroring the Python composition line-for-line. Use `esc` + `fmtNum`/`f1`. Distinguish absent vs zero with pointers/accessors.
8. **Register** in `render.py` `_RENDERERS` and `render.go` `RenderSVG` switch; add `<id>` to the schema `type` enum.
9. **Author** `charts/<id>/examples/*.json` (cover: basic, a styled/grouped/stacked variant, `dark` theme, an `adversarial`/XSS spec with hostile strings in **every** marks-emitted field per §5.5d, and any edge case the chart's math needs). Confirm each passes `validate()==[]`.
10. **Generate** goldens from the Python renderer (UTF-8, no BOM, no trailing newline) per §5.5e.
11. **Wire tests:** add the chart's CASES to `test_golden.py` and `render_test.go` (§5.5a/b) — migrating the existing `_check` call sites (§5.5a); add invalid-fixtures wiring if §5.4b (§5.5c); add the XSS-over-chart-id assertion (§5.5d) and any numeric edge-case test.
12. **Run both suites:** `python libs/python/tests/test_golden.py` and `cd libs/go && go test ./...`. Fix **code** (never fudge goldens) until both are green.
13. **Pass Gate B and Gate C** (§5.6), and **Gate A′** if the data element type changed. Confirm `git status` shows only additive golden files and no modified existing golden.
14. **Static check:** open one generated HTML (`save_html`/`SaveHTML`) with JS disabled — chart complete and readable (bars filled, data table faithful to the point model). Then with JS: hover→tooltip+crosshair, legend click→series toggles, keyboard arrows walk points, Esc clears without stealing focus. All with **zero** edits to `runtime/chart-interactions.js`.
15. **Docs:** add the CHARTS.md catalog row + decision-guide entry; tick this file's roadmap item.

### 5.8 Definition of Done

A Cartesian chart type is **done** only when ALL hold:
- [ ] `charts/<id>/design.md`, `examples/*.json`, and `golden/*.svg` exist; design.md is self-contained (an agent can build the chart from it alone).
- [ ] The renderer exists in **both** languages, is a one-line delegation to `render_cartesian`/`renderCartesian` supplying only a marks callback, and re-implements **no** chrome/scale/legend/theme/a11y/defs — all obtained from the shared cartesian module (incl. the value-axis domain and any stacking-aware y-max, which the **frame** owns).
- [ ] The renderer is registered in `render.py` `_RENDERERS` and `render.go` `RenderSVG`; `spec.type` enum updated in the schema.
- [ ] Marks emit the `spec/svg-contract.md` structure exactly: `.pk-series[data-series=N]` groups, `.pk-point` with all required `data-*` **and** a `cx`, bar fill resolved from `SeriesStyle.fill` (never unfilled), legend/crosshair inherited from the shared tail. The shared runtime enhances with **zero JS changes** (tooltip, highlight, crosshair, legend toggle, keyboard nav, defs-scoping — all verified live).
- [ ] Every new spec field (if any — incl. Column's `stacking`/`grouping`) is present and consistent across schema + `validate.py` + `validate.go` + `spec.py` + `spec.go`, defaults applied **only on absence**; both validators reject the shared `invalid-fixtures.json` with **identical** `$.path: expected X, received Y` text.
- [ ] If the `data` element type changed, the accessible data table is generalized in lockstep in both languages (§5.4b-DT) with a Py==Go test, and **Gate A′** passes (all existing goldens byte-unchanged).
- [ ] All user strings via `esc`; all numbers via `fmt_num`/`fmtNum` (values) or `:.1f`/`f1` (coordinates). XSS tests pass **against this chart's marks** (adversarial example carries hostile strings in every emitted field; §5.5d) and a11y-toggle tests pass. Any new numeric transform (stacking, size-scale) has a finite-output edge-case test.
- [ ] **Gate A** (if extraction happened): line goldens byte-unchanged (`git diff` empty, incl. the category-edge fixtures), both suites green.
- [ ] **Gate B**: both suites pass the new chart's cases against the same goldens → Python == Go byte-identical on **every** fixture.
- [ ] **Gate C**: no existing golden modified; output additive-only; no empty `<defs>`/background emitted under the default light theme.
- [ ] `python libs/python/tests/test_golden.py` and `go test ./...` fully green; CHARTS.md and this roadmap updated.

If any box is unchecked, the chart is **not done** — regardless of visual appearance.

---

## 6. Deferred families & their foundation tax

These families are **out of scope until the Cartesian family is exhausted** (§1.4). Each entry states the one-time foundation tax that its `new-family` opener pays and what unlocks afterward. They are listed in the recommended order of eventual investment (cheapest / highest-leverage first). None of them may be started while cartesian siblings remain unbuilt.

| Order | Family | Opener (new-family) | Foundation tax paid once | Then cheap |
|---|---|---|---|---|
| D1 | **Polar / radial** | Pie | Polar coordinate system (θ,r ↔ x,y) + arc/sector path builder + angular & radial axes/gridlines + start/end-angle & inner-radius handling. | Donut/variablepie (variants), gauge, solid gauge (SLO/utilization), radar, wind rose, nightingale, radial bar, parliament. |
| D2 | **Matrix / grid** | Heatmap | 2-D grid layout + **continuous color scale** (sequential/diverging) + color-axis (gradient) legend + cell/tile renderer; numeric 2-D binning for binned variants. | Calendar heatmap, tilemap, hexbin, **allocation-over-time** + **latency-over-time (pulse)** heatmaps (profiling superset). The color scale here is reused by Hierarchy and Geo. |
| D3 | **Hierarchy** | Treemap | Tree data model + layout engines (squarify, rectangular partition/icicle, radial partition/sunburst, tidy-tree, circle-packing) + breadcrumb & drill-zoom; reuses the Matrix color scale. | Sunburst, **icicle/partition**, **aggregated flame graph** (THE profiler view), dendrogram, circle packing, org chart. (The **time-ordered** flame chart is NOT here — it is a Cartesian xrange sibling in Family A, reusing the datetime-axis + floating-bar primitive, not squarify/partition.) |
| D4 | **Flow / relational** | Sankey | Node/link data model + layout engines (sankey rank+flow allocation, force-directed simulation, arc/chord circular placement) + ribbon/edge path geometry; set-overlap geometry for venn; **Archimedean-spiral glyph-packing for word cloud** (a node-only outlier that reuses none of sankey/force/chord/ribbon). | Dependency wheel, **chord** (service-call matrix), **network graph** (service topology), arc diagram, packed bubble (reuses the force-sim), venn/Euler, word cloud (own spiral packer). |
| D5 | **Statistical / distribution** | Violin | Kernel density estimation (1-D KDE) + quantile/summary computation + mirrored (violin)/stacked-ridge layout, **plus marching-squares contour extraction over a 2-D KDE grid** (folded into this single tax so 2-D density/contour is a sibling, not a second opener). (Boxplot, histogram, error-bar live in Cartesian — they need only cartesian axes.) | Ridgeline, KDE/bell curve, **2-D density/contour** (sibling; also consumes Matrix color), Q-Q, **ECDF/SLO attainment curve**. Reuses Cartesian axes + Matrix color scale (2-D density). |
| D6 | **Geo** | Choropleth | Map projection library (Mercator/Albers/Robinson/…) + geo/topojson polygon ingestion + region hit-testing + pan/zoom. **Largest new investment.** Reuses Matrix color scale + Scatter bubble marks + Flow ribbons. | Map bubble, marker map, flow/connection map, mapline, geo heatmap, tile-grid cartogram. (Tiled raster web map breaks static-first — likely out of scope.) |
| — | **KPI / single-value** | (no opener) | **Near-zero.** Sparkline is a **variant** of the line renderer (chrome off); sparkbar a variant of column; gauge-style KPIs reuse the polar solid gauge; bullet rides the cartesian bar substrate (§3.3 rank 13). | Stat card, sparkline/sparkbar, progress/linear gauge, bullet, waffle, pictorial, delta indicator. Fold in opportunistically as the underlying substrates land — this family has **no** foundation tax of its own. |

**Cross-family reuse chain (why the D-order is what it is).** Matrix's continuous color scale is a prerequisite of Hierarchy (treemap color-axis) and of Geo (choropleth fills + geoheatmap). Polar's arc geometry is reused by Hierarchy's Sunburst and by Flow's dependency wheel. Statistical reuses Cartesian axes (already built) + Matrix color (2-D density). Geo reuses Matrix color + Scatter bubbles + Flow ribbons — hence it is last (it consumes the most prior foundations). Building in the D1→D6 order pays each foundation tax once and maximizes downstream reuse.

---

## 7. Non-goals & sequencing

### 7.1 Non-goals (explicitly out of scope for v1)

- **3D / isometric charts** (3D column/scatter/cylinder/area, funnel3d/pyramid3d, 3D pie). They require a depth-sorting + projection layer that **conflicts with static-first byte-parity** and adds a genuine new foundation. Deferred indefinitely.
- **Tiled raster web maps** (OSM/XYZ basemaps). They require **external tile fetch**, which breaks the static-first, self-contained-SVG guarantee. Out of scope while static-first holds.
- **Any behavior that needs new runtime JS.** Adding a chart may **never** edit `runtime/chart-interactions.js`. A datum interaction the shared runtime does not already support (via the `.pk-series`/`.pk-point`/`data-*` contract) is out of scope for a chart add.
- **Hand-editing generated goldens to make a test pass.** A Go/Python divergence is a **code** bug to fix, never a golden to regenerate. Goldens are regenerated only on an intentional spec-fixture change, or via the separate lockstep "regenerate all" policy in `docs/customization/plan.md`.
- **Per-chart re-implementation of chrome.** Axes, scales (including the value-axis domain / stacked y-max), legend, crosshair, theme, a11y, `<defs>` are owned exclusively by the shared cartesian module (§4/§5). A renderer that re-derives any of them is a defect even if byte-correct.
- **Coercing malformed input.** Defaults apply **only on absence**; a present-but-malformed value is a validation error, never a silently-corrected default.
- **Expanding the top-level `type` semantics ad hoc.** New per-series render kinds (e.g. `series[].type` for combo) or new fields (e.g. Column's `stacking`/`grouping`, waterfall `isSum`) go through the full five-place lockstep of §5.4b — schema + both validators + both spec models + invalid fixtures.

### 7.2 Sequencing (the single ordered plan)

1. **Extraction first (Call #1).** With Column (Rank 1), extract the shared chrome into `_cartesian.py` + `cartesian.go` (widening the corpus with the category-edge fixtures first, §4.6); pass **Gate A**; commit the extraction on its own.
2. **Exhaust the Cartesian family (Call #1)** in the §3.3 build order: Column → Bar → Scatter → Bubble → Area → Combo → Histogram → Candlestick → Error bar → Area range → Column range → Waterfall → Bullet. Each rides §5's coordination contract and must satisfy Gates B and C (and Gate A′ for any rank that changes the `data` element type, e.g. Scatter) before landing. Order is fixed so each sibling forces the fewest **new** generalizations (§3.2) and unlocks the most reuse for the next.
3. **Only after the Cartesian family is exhausted** (§1.4), open the deferred families in the §6 D1→D6 order — Polar → Matrix → Hierarchy → Flow → Statistical → Geo — each paying its foundation tax once and reusing prior foundations per the cross-family reuse chain. KPI types fold in opportunistically as their underlying substrates land (no dedicated foundation).
4. **Throughout, the roadmap assumptions remain:** every type targets the **Highcharts baseline** floor plus the **profiling superset** (Call #2), and every non-line addition rides the extracted shared substrate rather than duplicating it (Call #1). Approved release scope and contracts can supersede these assumptions. Byte-identical Python==Go output, verified against a shared golden corpus, remains the intended gate for certified renderers.
