# Chart: Scatter (`scatter`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** ([`charts/column/design.md`](../column/design.md), which copies
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the sibling
> build detail: data model, marks, point placement, reused chrome, parity traps,
> and the a11y DOM contract.

- **Chart id:** `scatter`
- **Spec `type`:** `"scatter"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 3** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; scatter rides the shared cartesian frame once
  the point model lands — see [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 3, §3.2, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/scatter.py` · `libs/go/scatter.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A scatter plot: one or more series drawn as **unconnected point marks** at
`(x, y)` positions on a **numeric x-axis** and a **numeric y-axis**. Each point
is an independent `(x, y)` observation — there is no series line joining them.
Overlap density is conveyed by a marker **fill-opacity** so dense clouds read as
shaded regions. Points are the hoverable, interactive elements (the same
`.pk-point` marks line draws on top of its line, here standing alone).

Scatter is **build rank 3** — the first sibling on a **free numeric x-axis**. It
is the trigger for two of the family's headline generalizations:
the **point model** (`series[].data` normalizes to `{x,y}` datums, a bare number
staying valid with `x = index`) and the **numeric x-axis** (generalize the
value-axis `nice_ticks`/tick/gridline/pixel machinery from y-only to x, with the
zero-anchor turned **OFF** so a free x-domain is not wrongly pinned at 0).

## Use it when

- You have **two continuous numeric variables** and want to see their
  **correlation, spread, or clustering** — latency vs payload size, GC pause vs
  heap occupancy, CPU vs request rate.
- Your points have **no shared category ordering** and **should not be
  connected** — each `(x, y)` stands alone.
- Rows look like: `x, y` (one point series) or several such series overlaid to
  compare clusters. A single-variable sample stream (`y` per sample index) is the
  degenerate case — the **bare-number fast path** (`x = index`).

Do **not** use it for: a **trend** over ordered/continuous x where the points
*should* be joined (use `line-basic`), **comparison across discrete categories**
(use `column`/`bar`), **part-to-whole** (pie/donut), or a **distribution** of one
variable (use `histogram`). Add a third value as marker size → use `bubble`
(rank 4, scatter + a size-scale). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- each `series[].data`: a list of `(x, y)` points — the **point model** (below).
- `xAxis` is a **numeric value axis** derived from the point x-values (not a
  category list); `xAxis.categories` is accepted but ignored for the x-domain
  (the free numeric x-domain comes from the data).
- The y-domain is likewise **free** (`include_zero = False`) — a scatter with
  `y ∈ [420, 900]` is framed on that band, **not** anchored at 0.

## Data model

Scatter is the rank-3 sibling that lands the **point model** (§3.2 / §3.3
Rank 3). `series[].data` normalizes to a canonical datum with optional float
fields; scatter reads `{x, y}`:

- **Object form (primary):** `{"x": 128, "y": 47}` — an explicit `(x, y)`
  observation.
- **Positional sugar:** `[128, 47]` — a two-element array is `[x, y]`.
- **Bare-number fast path (pinned):** a plain number `47` stays valid with
  `x = index` (the datum is `Datum(x=i, y=47)`). This is the **same fast path**
  line and column ride, and it is **pinned byte-for-byte in both languages**
  (Python: numeric element → `Datum(x=index, y=float(v))`; Go: a custom
  `UnmarshalJSON` that still decodes a bare-number array `[1,2,3]` to the same
  `[]float64`-equivalent bytes) so **line and column goldens never move** when
  the point model arrives.
- **Absent / null field → gap, never coerced to 0** — a missing `y` drops the
  point; it is not plotted at the baseline.

The frame owns **both** domains. Because the x-axis is free, scatter delegates
with `include_zero = False` (§3.2 caveat, §4.2): the value-axis routine is
reused for x **with the zero-anchor OFF**, or a scatter with `x ∈ [100, 200]`
would be wrongly anchored at 0. The marks never recompute a scale — they call
`fr.xpix(x)` / `fr.ypix(y)` only.

> **Shipped examples note.** The current shared validator (`validate.py` /
> `validate.go`) still types `series[].data` as `number[]` — the point-model
> element type (object `{x,y}` / positional `[x,y]`) lands with the Rank-3
> five-place lockstep (§5.4b) and its byte-identity gate (§3.3 Rank 3, Gate A′).
> Until then the **shipped `examples/*.json` ride the bare-number fast path**
> (`x = index`) so each passes `validate() == []` today, exactly as `column`'s
> examples ride `number[]`. The object/positional forms above are shown
> throughout this recipe as the **target** input the point model accepts; they
> begin validating (and are added to the golden set) the moment the point-model
> element type is registered in the two validators.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"scatter"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is a point marker in the series symbol) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (here rendering `(x, y)` pairs — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | axis label |
| `xAxis.min` / `xAxis.max` | number | auto (nice ticks over the x-values, **0 NOT forced**) | clamp the numeric x range; the free x-axis does **not** auto-include 0 |
| `xAxis.gridLine` | object | `{enabled:false}` | **vertical** x-gridline styling (now meaningful — the x-axis is numeric): `{enabled, color, dashStyle}`, `dashStyle` ∈ solid/dashed/dotted. Reuses the existing gridLine object, applied to the x ticks |
| `xAxis.categories` | string[] | — | accepted for compatibility but **ignored** for the x-domain (scatter x comes from the point data, not a category list) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks over the y-values, **0 NOT forced**) | clamp the y range; the free y-axis does **not** auto-include 0 (a scatter is framed on its data, not the origin) |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | point[] | — | the `(x, y)` points — object `{x,y}` / positional `[x,y]` / bare-number fast path (`x = index`). See **Data model** |
| `series[].color` | string \| gradient | palette by index | the **point fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[…]}` object (legend swatch uses stop 0) |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:4}` | the point mark (now the **primary** mark, not a decoration on a line): `symbol` ∈ circle/square/triangle/diamond; `radius` px |
| `series[].fillOpacity` | number | 1 | **point** fill-opacity — set `< 1` (e.g. `0.6`) so overlapping points shade denser regions (overlap density). For scatter this styles the marker fill, **not** an under-line area |
| `series[].regression` | bool | false | **planned field.** `true` → draw an ordinary-least-squares **trend line** for that series as an extra `<path class="pk-series-line pk-trend">` on top of the points. Adds via the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) when the renderer lands |

Fields carried over from the line/column spec but **inert** for scatter (no line,
no bands): `lineWidth`, `dashStyle`, `step`, `curve`, `pattern`, `stacking`,
`grouping` are accepted by the shared validator (forward-compatible) but not
consumed by the scatter marks. Unlike column, scatter **does** consume `marker`
(the point *is* the marker) and **does** consume `fillOpacity` (as point
fill-opacity). Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). It passes the
numeric x-scale and `include_zero=False` so **both** the x- and y-domains are
free:

```python
# libs/python/peakcharts/charts/scatter.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Scatter", "linear", _scatter_marks, include_zero=False)
```
```go
// libs/go/scatter.go — package peakcharts
func renderScatterSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Scatter", "linear", scatterMarks, false)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one point mark per datum** — the reused marker symbol
(`circle`/`square`/`triangle`/`diamond`), carrying the full `.pk-point` contract.
**No `pk-series-line` path is emitted** (the points are unconnected):

```html
<g class="pk-series" data-series="0">
  <circle class="pk-point" data-series="0"
          data-series-name="checkout-api" data-x="128" data-y="47"
          data-color="#2f7ed8" data-r="4" data-r-hover="6.5"
          cx="286.4" cy="181.0" r="4"
          fill="#2f7ed8" fill-opacity="0.6"/>
  … one .pk-point per datum …
</g>
```

- **Class:** `pk-point` — the **contract** class the runtime keys on (tooltip /
  highlight / crosshair / legend-toggle / keyboard nav). The point **is** the
  hoverable mark; there is no separate line or area.
- **Geometry:** each point sits at `cx = fr.xpix(datum.x)`, `cy = fr.ypix(datum.y)`.
  `fr.xpix` maps a **value** (not an index) for scatter's `"linear"` x-scale
  (below). The visible shape is the reused marker builder for the series
  `symbol` at `(cx, cy)` with radius `r` — **reuse the four existing marker
  symbols** (`_marker` / `markerSVG`; §4.2 line-marks, promoted so scatter can
  reuse them without a fork). No baseline, no width/height — an `(x, y)` mark has
  none.
- **Fill:** read the resolved point paint (`fr.styles[si]` — pattern →
  `url(#pat)`; gradient → `url(#grad)`; else the solid hex). Apply
  `fill-opacity` from `series[].fillOpacity` (default 1). Never leave a point
  unfilled (an unfilled scatter is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (point x) — the crosshair
  reads it — and `cy` (point y). For circle/square/triangle/diamond the shape is
  centered on `(cx, cy)`.
- **No connecting line.** Unlike line, scatter emits **no** `<path
  class="pk-series-line">`. `curve`, `step`, `dashStyle`, `lineWidth` are inert.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Numeric x-scale — the pinned geometry (the rank-3 net-new machinery)

Scatter introduces the **linear (numeric value) x-scale** — the third x-scale
strategy on the frame, parallel to the two extraction landed (`point`, `band`;
§4.3). It mirrors the y-scale exactly: reuse the already-parity-locked
`nice_ticks` + `fmt_num` **verbatim** over the x-values so x ticks, labels, and
vertical gridlines are byte-identical for free. Evaluate in **exactly this order**
in both languages so `:.1f`/`f1` rounding lands ULP-for-ULP identically:

```
x_lo, x_hi, x_ticks = nice_ticks(min(xs), max(xs), include_zero=False)   # 0 NOT forced
xpix(v) = plot_x + plot_w * (v - x_lo) / (x_hi - x_lo)                    # value → pixel, mirrors ypix
# degenerate (single distinct x / one point) — pin BEFORE the divide, identically:
#   if x_hi == x_lo:  xpix(v) = plot_x + plot_w / 2      (center; never divide by 0)
```

- **`include_zero = False` is load-bearing.** The shared value-axis bakes in
  "force 0 into the domain" for the column/bar/area value axis and the y
  baseline; scatter's free x (**and** free y) reuse that routine with the flag
  **OFF** (§3.2 caveat). Both languages would be wrong identically and still pass
  byte-parity — so the flag must be explicit, not implicit.
- **Vertical x-gridlines** are drawn by the frame at `x_ticks` when
  `xAxis.gridLine.enabled` (reusing the `dash_array`/`dashArray` helper — the
  same one the y-gridlines and any line dash use, so styles can't drift).
- **`data-x` is numeric.** It becomes `esc(fmt_num(x))` — a formatted number via
  `fmt_num`, **not** a category string (line/column emit `esc(category)`). This
  is the single biggest `data-*` difference from the categorical siblings.
- The shared x-label loop calls `frame.xpix(tick)` so tick labels land under the
  numeric ticks with no per-chart label code.

## Reused chrome (obtained from the frame — never re-implemented)

Scatter inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (**`include_zero=False`** — free
  y-domain); y gridlines + labels.
- The **numeric** x-axis via the `"linear"` `xpix` (the rank-3 net-new scale
  above); vertical x-gridlines; the shared x-label loop lands labels under the
  numeric ticks with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + id-scoping via `cid`
  (defs emitted only when a series needs them — no empty `<defs>` under the light
  theme).
- The four **marker symbols** (`circle`/`square`/`triangle`/`diamond`) via the
  reused `_marker`/`markerSVG` builders.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (rendering `(x, y)` pairs — §5.4b-DT) + keyboard nav. Responsive `<svg>`
  viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values, incl. numeric `data-x`),
  `:.1f`/`f1` (pixel coords) — all parity-locked.

The chart delegates with `x_scale="linear"` and `include_zero=False` (free x/y).
It passes the bare noun **`"Scatter"`** — the frame expands it to
`"Scatter chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **`include_zero = False` on BOTH axes** — the free x **and** free y domains
  reuse the value-axis routine with the zero-anchor OFF. Leaving it ON (the
  column default) silently anchors a `x ∈ [100,200]` scatter at 0 — and both
  languages would be wrong *identically*, passing byte-parity. Pass the flag
  explicitly.
- **Numeric-x-scale ORDER** — evaluate `nice_ticks(min,max,include_zero=False)`
  then `xpix(v) = plot_x + plot_w*(v - x_lo)/(x_hi - x_lo)` in that exact order;
  a reassociated numerator/denominator diverges after `:.1f` rounding.
- **Degenerate x-domain** — a single distinct x (or one point) makes
  `x_hi == x_lo`; pin the `xpix = plot_x + plot_w/2` center rule **before** the
  divide, identically in both languages (Python `ZeroDivisionError` vs Go
  `+Inf`/`NaN` would otherwise diverge). Mirror the y-scale's existing
  single-value handling.
- **`data-x` is numeric** — emit `esc(fmt_num(x))`, never a category string; a
  raw `str(float)` / `FormatFloat(...,-1,64)` instead of `fmt_num` is the #1
  byte diff.
- **Point model bare-number fast path** — a plain number must normalize to
  `Datum(x=index, y=v)` byte-for-byte in both languages, so line/column goldens
  do not move (Gate A′, §3.3 Rank 3). Positional `[x,y]` and object `{x,y}` are
  sugar over the same datum.
- **Gap, not zero** — an absent/null `y` **drops** the point; it is never plotted
  at `ypix(0)`.
- **No connecting line** — emit no `pk-series-line` path; `curve`/`step`/
  `dashStyle`/`lineWidth` are inert (reading them would draw a line scatter must
  not have).
- **Point fill** — pattern → `url(#pat)`; gradient → `url(#grad)`; else solid
  hex; apply `fill-opacity` from `fillOpacity`. Never emit an unfilled point.
- **Formatters** — `cx,cy` (and any shape path numbers) via `:.1f`/`f1`;
  `data-x`, `data-y`, radii via `fmt_num`/`fmtNum`; every user string via `esc`.
  A leaked raw `<` fails the XSS tests.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep series/point/legend
  `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its points, and the
  legend item (do not renumber).
- **Datum mark:** `.pk-point` carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`.
- **Crosshair anchor:** every `.pk-point` carries `cx` (point x) and `cy`
  (point y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  **`data-x = esc(fmt_num(x))`** (the numeric x — the key difference from the
  categorical siblings); `data-y = esc(fmt_num(y))`; `data-color =
  fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs
  (`cx,cy`) use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks
  points. `a11y:false` restores the pre-a11y bytes. **Data-table obligation
  (§5.4b-DT):** scatter's `data` is **no longer `number[]`** — it is `(x, y)`
  pairs — so the shared data table MUST be generalized **in lockstep in both
  languages** to render each point as an `(x, y)` row (not a coerced single
  number), with a test proving Py==Go table bytes. This is part of "adding a new
  data shape," alongside the §5.4b field drill and the Rank-3 byte-identity gate.
- **Static-first:** the chart is fully readable with JS disabled — points are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/correlation.json`](examples/correlation.json) — two point clouds
with distinct marker symbols and overlap-density fill (shipped on the bare-number
fast path so it validates today):

```json
{
  "type": "scatter",
  "title": "Request Latency Samples",
  "subtitle": "Two endpoints, unconnected points, overlap shaded",
  "xAxis": { "title": "Sample #" },
  "yAxis": { "title": "Latency (ms)" },
  "series": [
    { "name": "checkout-api", "data": [42, 55, 38, 61, 47, 90, 52, 44, 73, 58, 49, 66],
      "marker": { "symbol": "circle", "radius": 4 }, "fillOpacity": 0.6 },
    { "name": "search-api",   "data": [61, 58, 72, 55, 80, 63, 69, 77, 84, 66, 59, 71],
      "marker": { "symbol": "triangle", "radius": 4 }, "fillOpacity": 0.6 }
  ]
}
```

The **target** point-model form the same renderer accepts (validating once the
Rank-3 element type is registered) uses explicit `(x, y)` — object or positional:

```jsonc
// point-model form (target): free numeric x from the data, include_zero OFF
"series": [
  { "name": "latency vs payload",
    "data": [[128, 47], [256, 52], [512, 66], [1024, 91], [2048, 140]],
    "marker": { "symbol": "circle", "radius": 4 }, "fillOpacity": 0.6 }
]
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, bare-number fast path (`x=index`), default circle markers, free y-domain |
| [`examples/correlation.json`](examples/correlation.json) | two series (overlaid clouds), distinct marker symbols (`circle`/`triangle`), `fillOpacity` overlap density |
| [`examples/regression.json`](examples/regression.json) | `series[].regression` trend-line (planned field, forward-compatible), vertical x-gridlines via `xAxis.gridLine`, clamped free axes |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a gradient point fill (defs pre-pass) + a second series with a custom hex + `diamond`/`square` symbols |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, custom point color, and — once numeric-x lands — any label) so the
XSS tests run against the scatter marks (§5.5d). `SCATTER_CASES =
["basic","correlation","regression","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/scatter/examples/correlation.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="scatter",
    title="Request Latency Samples",
    x_axis=Axis(title="Sample #"),
    y_axis=Axis(title="Latency (ms)"),
    series=[
        Series("checkout-api", [42, 55, 38, 61, 47, 90, 52, 44, 73, 58, 49, 66]),
        Series("search-api",   [61, 58, 72, 55, 80, 63, 69, 77, 84, 66, 59, 71]),
    ],
), "out.html")
```

**Go —** same spec, byte-identical output:
```go
import "peakcharts"
spec, _ := peakcharts.FromJSON(specJSON)   // specJSON = the bytes above
peakcharts.SaveHTML(spec, "out.html", "")
```

## Output & interactivity

A self-contained interactive HTML file: inline SVG + CSS + the shared runtime.
- **Hover a point** → tooltip (x, series, y) + point highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the points; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — points filled and
  readable.

## Rendering notes

- Both axes use "nice numbers" ticks (~6). Unlike the value-axis siblings,
  **neither axis auto-includes 0** (`include_zero=False`) — a scatter is framed
  on its data, not the origin. `xAxis.min/max` and `yAxis.min/max` clamp when set.
- The x-axis is **numeric** (`x_scale="linear"`), reusing the y-scale's
  `nice_ticks`/`fmt_num` verbatim so x ticks are byte-identical for free.
  `xAxis.categories` is ignored for the x-domain.
- Points are **unconnected** — no series line. Overlap density is conveyed by
  `series[].fillOpacity < 1`.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is
  unset; a gradient/pattern fills the point via the `<defs>` pre-pass.
- Marker symbols reuse the four shared builders (circle/square/triangle/diamond);
  the point *is* the marker.

## Not yet supported (roadmap)

- Live renderers (`scatter.py` / `scatter.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **Point-model validator support** — the object `{x,y}` / positional `[x,y]`
  `data` element type (§5.4b five-place lockstep + Gate A′ byte-identity proof);
  shipped examples ride the bare-number fast path until then.
- **Regression / trend line** (`series[].regression`) — OLS fit line overlay.
- **Bubble** (rank 4) — scatter `{x,y,z}` + the size-scale (`z → marker radius`).
- Categorized scatter, polygon/convex-hull overlay, jitter for tied x, and a
  two-axis crosshair — variants layered on this base.
