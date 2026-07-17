# PeakCharts — Chart Families & Roadmap

> Holistic map of every chart type we intend to support, organized so that
> **charts sharing a foundation are planned and built together**. This is the
> source doc other agents read to (a) pick what to build next and (b) know which
> shared components a chart type reuses vs. which new foundation it needs.

## The organizing principle: group by *substrate*, not by name

A chart type's cost and reuse are determined by its **substrate** = its
**coordinate system + data model + the marks it draws**. Charts on the same
substrate share ~80% of the code (coordinate mapping, axes/scales, legend,
tooltip, theme, a11y, escaping, number formatting, the JS runtime). A chart on a
*different* substrate needs a new foundational layer.

So "line graph family" is really the **Cartesian / XY family** — line, area,
column, bar, scatter all sit on the same x/y-axis substrate we already built.
Heatmap, pie, flame graph, sankey each live on a *different* substrate and are
**separate foundational investments**, correctly deferred.

## The tool that drives everything: variant vs. sibling vs. new-family

Every candidate chart is exactly one of these. This classification IS the plan.

| Class | Definition | Cost | Examples |
|---|---|---|---|
| **Variant** | Same renderer, toggled by a spec flag | ~nothing (already a flag or a small one) | spline, step, area (=`fillOpacity`), stacked |
| **Sibling** | New renderer, **same substrate** — reuses axes/scales/legend/theme/a11y | Medium (a renderer + goldens) | column, bar, scatter, combo |
| **New family** | New substrate (coord system / data model / marks) | High (new foundation first) | pie, heatmap, treemap, flame, sankey, map |

Rule: **exhaust variants and siblings within a family before opening a new
family.** Opening a family pays a foundation tax once; siblings then ride it cheaply.

---

## The full taxonomy

Legend: ✅ done · 🔸 variant (spec flag) · 🔹 sibling (new renderer, same substrate) · 🆕 new family (new substrate)

### A. Cartesian / XY family — *our current substrate*
Shared: x/y axes, linear + category scales, gridlines, plot area, series values,
legend, tooltip, crosshair, themes, a11y, gradients/patterns.
- **Line** ✅ — multi-series ✅, spline ✅, step ✅, area 🔸(`fillOpacity`), stacked area 🔸, percent (100%) area 🔸, range/band area 🔹
- **Column** (vertical bars) 🔹 — grouped 🔸, stacked 🔸, percent-stacked 🔸, range column 🔹, **waterfall** 🔹
- **Bar** (horizontal) 🔹 — column transposed; same variants
- **Scatter** 🔹 — bubble (3rd dim = size) 🔸, jitter/beeswarm 🔸
- **Combo** (line + column together) 🔹
- **Histogram** 🔹 (binning transform → column)
- **Financial** 🔹 — candlestick / OHLC (per-x open/high/low/close)
- **Error bars / range** 🔸 (whiskers on points)
- **Bullet** 🔹 (bar variant)

### B. Polar / radial family 🆕
New substrate: polar coordinates (angle + radius), arc geometry, no cartesian axes.
- Pie / donut — semi-circle, exploded, nested/multi-level
- Gauge / dial — solid, angular
- Radar / spider — filled, multi-series
- Polar / radial bar, wind rose

### C. Matrix / grid family 🆕
New substrate: 2-D cell grid + a **color-scale** legend.
- Heatmap — calendar heatmap, correlation matrix
- Hexbin / 2-D density

### D. Hierarchy family 🆕
New substrate: hierarchical (tree) data + a layout algorithm.
- Treemap (squarified/nested)
- Sunburst (hierarchical **polar** — bridges B + D)
- Icicle / partition → **flame graph / flame chart** (icicle for profiling: time on x, stack depth on y)
- Dendrogram / tree

### E. Flow / relational family 🆕
New substrate: nodes + links, graph layout.
- Sankey / alluvial, chord, network (force-directed), arc diagram

### F. Statistical distribution family 🆕/🔹
Some reuse the cartesian substrate + a stats computation.
- Boxplot 🔹 (cartesian + 5-number summary), violin 🆕 (box + density), density/KDE

### G. Geo family 🆕 (largest new investment)
New substrate: geographic projection + map data.
- Choropleth, bubble map, flow map, tile-grid map

### H. KPI / single-value 🔹
Minimal substrate.
- Number card, sparkline (tiny cartesian line), progress, bullet

---

## Scoped plan: the Cartesian / XY family

This is the family we execute next. Everything here reuses the hardened core.

### What we already have (the substrate — do not rebuild)
Coordinate mapping (`xpix`/`ypix`, plot area, margins) · linear y-scale
(`nice_ticks`) · category x-axis · title/subtitle · x/y axis + titles ·
gridlines · legend · crosshair · **themes** (light/dark/custom) · **a11y**
(role/aria/`<desc>`/data-table/keyboard nav) · **gradients/patterns/`<defs>`** ·
**escaping** · **`fmt_num` parity** · responsive · the JS runtime (tooltip,
highlight, legend toggle, keyboard, defs-scoping) · the golden parity harness.

### What must be GENERALIZED as the family grows (the real work)
1. **Richer series data model.** Today `data: number[]` (one y per x). Siblings need:
   scatter = (x, y) pairs; bubble = (x, y, z); candlestick = (o, h, l, c); range =
   (low, high). Decide a forward-compatible point model (keep `number[]` valid for line).
2. **Numeric x-axis.** Scatter needs a linear x-scale, not just categories —
   generalize the y-side `nice_ticks` machinery to x.
3. **Stacking transform.** grouped / stacked / percent is one shared transform used
   by column, bar, and area. Build it once.
4. **Orientation.** bar = column transposed — one orientation concept (or bar delegates
   to column with axes swapped).
5. **Shared cartesian chrome module.** Extract axes/gridlines/legend/title/crosshair/
   theme/a11y/defs out of `line.py`/`line.go` into `charts/_cartesian.*` that line,
   column, and scatter all call. **Do this while building column**, verified by line's
   goldens staying byte-identical.

### The category contract (what an agent needs to add a cartesian type)
1. `charts/<type>/design.md` — the self-contained recipe.
2. `render_<type>_svg(spec)` in **both** languages that:
   - reuses the shared cartesian chrome helpers (axes, gridlines, legend, title,
     crosshair, theme, a11y, `<defs>` pre-pass) — never re-implements them;
   - emits SVG following `spec/svg-contract.md` (`.pk-series`, `.pk-point`, `data-*`)
     so the runtime enhances it with **zero JS changes**;
   - routes through `_num`/`esc`/`fmt_num` so escaping + float parity are inherited.
3. Register in the `_RENDERERS` / `RenderSVG` dispatch.
4. Golden fixtures under `charts/<type>/{examples,golden}/` + parity test in both suites.
5. **Byte-identical Python↔Go** on every fixture; default output additive-only.

### Build order (each step reuses more of the substrate)
1. **Column / bar** — most common; forces stacking + orientation + the chrome
   extraction. Highest reuse. *(Next.)*
2. **Scatter / bubble** — forces numeric x-axis + richer point model.
3. **Area variants** (stacked / percent) — mostly the stacking transform on the
   existing line/area renderer.
4. **Combo** (line + column) — forces a composition layer (multiple marks, one plot).
5. **Histogram** — a binning transform → column.
6. **Financial / range / error-bar / waterfall** — richer point model + specialized marks.

When 1–6 are done, the Cartesian family is complete and we open the **next
family** (Polar/pie recommended — most-requested new substrate) with its own plan.

---

## Deferred families — the new foundation each one needs (so we know the tax)
- **Polar (B):** polar coordinate system + arc/sector path math + angular axis.
- **Matrix (C):** 2-D grid layout + a **continuous color scale** + color-scale legend.
- **Hierarchy (D, incl. flame graph):** tree data model + a layout algorithm (treemap
  squarify / partition) + zoom interaction.
- **Flow (E):** node-link data model + a layout (sankey flow / force).
- **Geo (G):** map projection + geo/topojson data ingestion.

Each is a **separate planning doc** when we get there — do not mix into the
cartesian plan.

## Non-goals for now
No new family until the Cartesian family's siblings (column, bar, scatter) exist
and prove the shared-chrome extraction holds byte-parity across ≥3 chart types.
Web-Component/Shadow-DOM embedding stays a separate track (see `docs/robustness.md`).
