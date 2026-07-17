# Chart: Area (`area`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file mirrors the
> Cartesian **exemplar** [`charts/column/design.md`](../column/design.md) and the
> reference recipe [`charts/line-basic/design.md`](../line-basic/design.md), and
> adds the area build detail: the value payload, the cumulative-baseline fill
> geometry, the reused line renderer, the parity traps, and the a11y DOM
> contract.

- **Chart id:** `area`
- **Spec `type`:** `"area"`
- **Class:** `variant` (Family A — Cartesian/XY) · **Build rank 5** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; area rides the shared cartesian frame + the
  line renderer once column's stacking transform lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 5, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/area.py` · `libs/go/area.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

An area chart: one or more series drawn as **connected lines with the region
between the line and a baseline filled**, over a shared categorical x-axis and a
numeric y-axis. Each series is a line (the reference line chart) plus a fill; the
**point markers on the top edge** stay the hoverable, interactive elements (area
adds no new mark type — it reuses line's markers). Areas are **basic** (each fill
drops to the zero baseline, overlaid), **stacked** (each fill sits on the
previous series' cumulative top), or **percent-stacked** (stacked, then each
x-column normalized to 100%).

Area is **build rank 5** and the **cheapest** non-line sibling: it is effectively
a **variant** that rides the **entire line renderer** (the `_path_d` path builder,
the area fill, gradients/patterns, markers) and reuses **column's** stacking
transform + frame-owned stacked y-domain. Its only net-new is a thin wrapper that
fills **between two cumulative baselines** instead of always to zero.

## Use it when

- Your x is **ordered categories or time** (minutes, intervals, versions) and
  your y is a **continuous magnitude/volume** you want to read as a filled shape.
- You want to show a **trend with its volume under the line**, **composition over
  time** (stacked resource usage), or **share over time** (percent-stacked).
- Rows look like: `label -> value` (one series) or `label -> value_a, value_b`
  (several series sharing one x).

Do **not** use it for: comparing a value **across discrete categories** (use
`column`/`bar`), **x/y correlation** with no shared category ordering (use
`scatter`), **part-to-whole of a single total** (use pie/donut), or a
**distribution** of raw samples (use `histogram`). A basic overlaid area with
many series occludes itself — prefer `line-basic` or a stack. See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers, aligned to `categories` by index.
- **Identical value payload to `line` and `column`** (`data: number[]`) —
  basic/stacked/percent are **transforms over these y-values**, selected by the
  chart-level `stacking` (+ `grouping`) fields, not a different data shape. A bare
  `number` stays valid (x = index), so line/column/area goldens never move when
  the point model lands.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"area"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch uses the series solid color) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`stacking`** | string | — (basic) | **Shared field (with column).** `null`/absent = basic overlaid areas, each filled to the zero baseline; `"normal"` = areas stacked cumulatively (each fills from the previous series' cumulative top); `"percent"` = stacked then normalized so each x-column totals 100%. The **frame** owns the resulting stacking-aware y-domain (max column **total**, not per-datum max; for `"percent"` the axis is effectively 0–100). Routed through the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) |
| **`grouping`** | bool | true | **Shared field (with column), but INERT for area.** Areas cannot sit side-by-side — basic areas always **overlay** in series order, and `stacking` (not `grouping`) selects the cumulative transform. Accepted for cross-chart spec uniformity + forward-compatibility; it changes no area bytes |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (points land under category positions on the **point** x-scale) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the y range; the value axis always includes 0 (the fill baseline) unless clamped. For `"percent"` the axis is 0–100 |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | y-values, length `N` (negatives allowed for basic area → the fill drops below the baseline; stacking assumes non-negative contributions) |
| `series[].color` | string \| gradient | palette by index | applies to the **line stroke + the area fill** (and markers/legend via stop 0): hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object |
| `series[].fillOpacity` | number | area default `0.75` | fill translucency of the region. **Area fills by default** (unlike `line`, where an absent `fillOpacity` means `0`/no fill); the shared field, its type, and its validation are identical — only the area renderer's absent-value interpretation differs (both languages use `0.75` on absence, pinned for parity). Lower it (~0.3) for legible overlaid basic areas; keep it near-opaque for stacked segments |
| `series[].pattern` | object | — | hatch fill for the area: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |
| `series[].lineWidth` | number | 2 | thickness of the top-edge line (px) |
| `series[].dashStyle` | string | solid | top-edge line dash: solid/dashed/dotted |
| `series[].step` | string | — | stepped top edge: before/after/center (the fill follows the same stepped path) |
| `series[].curve` | string | — | `monotone` = smooth Fritsch–Carlson spline top edge (fill follows the same spline); default straight |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:3.5}` | top-edge point markers; `symbol` ∈ circle/square/triangle/diamond |

Unlike `column` (where `fillOpacity`/`lineWidth`/`dashStyle`/`step`/`curve`/`marker`
are inert because there is no line to draw), **area consumes them all** — the top
edge IS a line with markers. The only inert field is `grouping` (above). Full
schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — one y per category, the same
  shape line and column use. No `{x,y}` object model (that arrives with scatter,
  rank 3), so the accessible `number[]` data table needs **no** generalization
  (§5.4b-DT applies only when the data element type changes).
- **Basic (default, `stacking` absent):** each series is drawn independently — a
  line on `data`, filled down to the **zero baseline** `ypix(0.0)`. This is
  byte-identical to `line` with `fillOpacity>0` (the P5 area fill). Series overlay
  in index order; `grouping` has no effect.
- **Stacked (`stacking:"normal"`):** series segments accumulate on a cumulative
  baseline — series `k`'s **bottom** edge is the running total through series
  `k-1` (`cumBelow`), its **top** edge is the running total through `k` (`cumTop`).
  The fill is the band between those two polylines; the line + markers ride the
  **top** edge.
- **Percent (`stacking:"percent"`):** stacked, then each value is normalized by
  its **category total** so every x-column fills 0–100%. Cumulative baselines are
  computed on the normalized values.
- **The frame owns the y-domain.** For stacked/percent the y-max is the **max
  category total** (cumulative in the pinned summation order, §4), **not** the
  per-datum max — the marks never recompute a scale. For `"percent"` the frame's
  axis is effectively `nice_ticks(0, 100)`. For basic it is the usual `nice_ticks`
  over the data with 0 forced in (`include_zero=True`).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). Area passes the
**`"point"`** x-scale (like line — **not** column's `"band"`) and
`include_zero=True` (value axis / zero baseline):

```python
# libs/python/stonecharts/charts/area.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Area", "point", _area_marks)   # include_zero defaults True
```
```go
// libs/go/area.go — package stonecharts
func renderAreaSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Area", "point", areaMarks, true)
}
```

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series, and inside it, in this order: the filled area `<path>`, the top-edge
`<path>`, then one `<circle>`/marker `.sc-point` per category on the top edge:

```html
<g class="sc-series" data-series="0">
  <path class="sc-series-area" data-series="0"
        d="M64.0 300.0 L…  L720.0 96.0 L64.0 240.0 Z"
        fill="#2f7ed8" fill-opacity="0.75" stroke="none"/>
  <path class="sc-series-line" data-series="0"
        d="M64.0 96.0 L…" fill="none" stroke="#2f7ed8" stroke-width="2"
        stroke-linejoin="round" stroke-linecap="round"/>
  <circle class="sc-point" data-series="0"
          data-series-name="user" data-x="00:00" data-y="120"
          data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
          cx="64.0" cy="96.0" r="3.5" fill="#2f7ed8"/>
  … one .sc-point per category on the top edge …
</g>
```

- **Class:** the markers are `sc-point` — the **contract** class the runtime keys
  on (tooltip / highlight / crosshair / legend-toggle / keyboard nav). Area adds
  **no** new mark class; the point marker is the hoverable element, exactly as in
  line (adding a class the runtime must *know about* is out of scope — NN#2).
- **Area geometry (basic):** `topPts[i] = (fr.xpix(i), fr.ypix(value_i))`;
  `area_d = _path_d(topPts, step) + " L{topPts[-1].x:.1f} {base:.1f} L{topPts[0].x:.1f} {base:.1f} Z"`
  where `base = fr.ypix(0.0)`. This is line's existing area-fill code **verbatim**
  — never recompute a baseline.
- **Area geometry (stacked/percent):** the fill is the band between two cumulative
  polylines — `cumTop[i]` (running total **through** series `k`) and `cumBelow[i]`
  (running total through series `k-1`). Build the top run with `_path_d(topPts,
  step)` (or `_spline_d` when `curve=="monotone"`), then append the **bottom** run
  **reversed** (R→L along `cumBelow`) using the same builder, then `Z`. The
  line + markers ride `topPts`. For percent, `cumTop`/`cumBelow` are computed on
  the values normalized by each category total.
- **Fill:** read `fr.styles[si].area_fill` (the resolved **under-fill**) and
  `fr.styles[si].area_op` (the ` fill-opacity="…"` attribute) — resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** This is
  the **opposite** of column: area reads `area_fill`/`area_op` (line's under-fill),
  **never** column's `fill` bar-paint field. Never leave an area series unfilled
  under the light theme (an unfilled area chart is a broken static chart — NN#2).
- **Top-edge line + markers:** the `sc-series-line` and `sc-point` markers are
  emitted **exactly** as line does — same `_path_d`/`_spline_d`, same `stroke`,
  `stroke-width` via `fmt_num`, `dashStyle`, and marker symbols. Reuse line's code
  path; do not fork it.
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx = fr.xpix(i)` (the crosshair
  reads it) and `cy` (the top-edge y — `ypix(value)` for basic, `ypix(cumTop)` for
  stacked/percent).
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Cumulative-baseline layout — the pinned geometry (from the blueprint)

Area uses the **point** x-scale (§4.3) — categories map to evenly-spaced points,
**no** band padding (that is column's geometry). The only area-specific arithmetic
is the cumulative offset, and it MUST be evaluated in **exactly this order** in
both languages so `%g` totals and `f1` pixel coords land ULP-for-ULP identically
(blueprint §3.2 stacking transform / §3.3 Rank 5):

```
xpix(i)        = plot_x + plot_w*i/(n-1)      # point scale (plot_x + plot_w/2 when n<=1)
# basic:
base           = ypix(0.0)
topPts[i]      = (xpix(i), ypix(value_k[i]))
# stacked ("normal"):  accumulate in SERIES INDEX ORDER
cumBelow_k[i]  = Σ_{j<k}  value_j[i]           # running total through series k-1
cumTop_k[i]    = cumBelow_k[i] + value_k[i]    # running total through series k
# percent ("percent"): normalize per category BEFORE accumulating
total[i]       = Σ_j value_j[i]                # 0 → contribution 0 (guard BEFORE divide)
norm_k[i]      = 100 * value_k[i] / total[i]   # (total[i] == 0 ⇒ 0)
cumBelow_k[i]  = Σ_{j<k}  norm_j[i]
cumTop_k[i]    = cumBelow_k[i] + norm_k[i]
```

- **Summation ORDER is pinned:** accumulate cumulative sums in **series index
  order**, and the **frame's** stacked y-max uses that **same** order — pin both so
  cumulative floats and `%g` output match across languages.
- **Percent divide-by-zero is pinned BEFORE the divide:** a category total of 0
  would divide-by-zero (Python raises, Go yields `NaN`); guard `total[i]==0 ⇒
  contribution 0` identically in both languages before dividing.
- **Reuse `_path_d`/`_spline_d`** for both the top and bottom runs of the band so
  `f1` coords match for free — never hand-roll a second path builder.
- `grouping` never enters area geometry (it is inert); `stacking` is the only mode
  selector.

## Reused chrome (obtained from the frame — never re-implemented)

Area inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (incl. the stacking-aware y-max the
  **frame** computes; 0–100 for percent); y gridlines + labels.
- Categorical x-axis via the **point** `xpix`; the shared x-label loop lands labels
  under category points with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution into `SeriesStyle`
  (`stroke`, `solid`, `area_fill`, `area_op`), id-scoping via `cid` (defs emitted
  only when a series needs them — no empty `<defs>` under the light theme).
- **The entire line mark toolkit:** `_path_d` (linear + step), `_spline_d`
  (monotone), `_marker` (circle/square/triangle/diamond), the area-fill emit, and
  the `sc-series-line`/`sc-point` structure — reused, not forked.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="point"` and `include_zero=True`. It passes the
bare noun **`"Area"`** — the frame expands it to `"Area chart with N series…"`
byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Summation order** — accumulate stacked cumulative sums in series index order;
  the frame's stacked y-max uses the **same** order; percent divides each value by
  its category total in that order, computed **before** accumulating.
- **Frame owns the y-domain** — the marks must call `fr.ypix` only; recomputing a
  scale (even to identical bytes) is a defect (NN, §7.1). Percent's 0–100 axis is
  the frame's, not the marks'.
- **Fill field is `area_fill`, NOT `fill`** — area reads line's under-fill
  (`area_fill`/`area_op`); reading column's `fill` bar-paint is the wrong field.
  Resolution: pattern → `url(#pat)`; gradient → `url(#grad)`; else solid hex +
  `area_op`. Never emit an unfilled area under the light theme.
- **Reuse the path builders** — `_path_d`/`_spline_d` for **both** the top edge and
  the reversed bottom edge; a hand-rolled second builder diverges after `f1`
  rounding. Keep `step`/`curve` consistent across the two edges so the band stays
  watertight.
- **Baseline anchor** — basic uses `fr.ypix(0.0)`; stacked/percent uses the
  `cumBelow` polyline. Never recompute a baseline.
- **`data-y` under stacking/percent** — carries the **raw per-series value** the
  user supplied (not the running cumulative total, and **not** the normalized
  percent), while the geometry uses cumulative/normalized baselines.
- **Degenerate percent** — a category total of 0 would divide-by-zero; pin the
  rule identically **before** the divide (Python raises, Go yields `NaN`→`"0"`).
- **Formatters** — `cx,cy`, path `d` numbers via `:.1f`/`f1`; `data-y`, radii,
  `stroke-width`, `fill-opacity` via `fmt_num`/`fmtNum`; every user string via
  `esc`. A leaked raw `<` fails the XSS tests.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep series/point/legend
  `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes** — area's contract is line's contract plus the stacked fill.

- **Series group:** `.sc-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its points, and the
  legend item (do not renumber).
- **Datum mark:** `.sc-point` (a `<circle>`/marker) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (point x) and by
  convention `cy` (top-edge y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` — the **raw** per-series
  value under stacking/percent; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks the
  top-edge markers. `a11y:false` restores the pre-a11y bytes. Area keeps
  `data: number[]`, so the existing `number[]` data table renders faithfully with
  **no** generalization (that obligation applies only when the data element type
  changes — scatter and later, §5.4b-DT).
- **Static-first:** the chart is fully readable with JS disabled — areas are
  server-rendered and filled, lines and markers drawn; the crosshair ships
  `display:none`; the tooltip is JS-only.

## Example spec

See [`examples/stacked.json`](examples/stacked.json):

```json
{
  "type": "area",
  "title": "CPU Time by Subsystem",
  "subtitle": "Stacked area, cumulative over time",
  "stacking": "normal",
  "xAxis": { "title": "Time", "categories": ["00:00", "00:30", "01:00", "01:30", "02:00", "02:30"] },
  "yAxis": { "title": "CPU seconds" },
  "series": [
    { "name": "user",   "data": [120, 138, 155, 149, 162, 170], "fillOpacity": 0.85 },
    { "name": "system", "data": [60, 72, 80, 76, 88, 92],        "fillOpacity": 0.85 },
    { "name": "iowait", "data": [18, 24, 30, 27, 33, 36],        "fillOpacity": 0.85 }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | overlaid basic areas, zero baseline, `fillOpacity` translucency (the P5 line-fill path) |
| [`examples/stacked.json`](examples/stacked.json) | `stacking:"normal"`, cumulative fill baselines, frame-owned stacked y-max |
| [`examples/percent.json`](examples/percent.json) | `stacking:"percent"`, per-category normalization to 100%, 0–100 axis, degenerate-total guard |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `stacking:"normal"` + a gradient area fill (defs pre-pass + `SeriesStyle.area_fill` → `url(#grad)`) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom color) so the XSS tests run against the area
marks (§5.5d). `AREA_CASES = ["basic","stacked","percent","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/area/examples/stacked.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="area",
    title="CPU Time by Subsystem",
    stacking="normal",
    x_axis=Axis(title="Time", categories=["00:00", "00:30", "01:00", "01:30", "02:00", "02:30"]),
    y_axis=Axis(title="CPU seconds"),
    series=[
        Series("user",   [120, 138, 155, 149, 162, 170], fill_opacity=0.85),
        Series("system", [60, 72, 80, 76, 88, 92],        fill_opacity=0.85),
        Series("iowait", [18, 24, 30, 27, 33, 36],        fill_opacity=0.85),
    ],
), "out.html")
```

**Go —** same spec, byte-identical output:
```go
import "stonecharts"
spec, _ := stonecharts.FromJSON(specJSON)   // specJSON = the bytes above
stonecharts.SaveHTML(spec, "out.html", "")
```

## Output & interactivity

A self-contained interactive HTML file: inline SVG + CSS + the shared runtime.
- **Hover a point** → tooltip (x, series, y — the raw value) + point highlight +
  crosshair.
- **Click a legend item** → toggle that series (and its fill) on/off.
- **Keyboard** → arrows walk the top-edge markers; Esc clears without stealing
  focus.
- Renders fully (static) even with JavaScript disabled — areas filled, lines and
  markers readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) and always includes 0 as the fill baseline
  unless `yAxis.min/max` clamp it. For `stacking:"percent"` the axis is
  effectively 0–100%.
- Areas use the **point** x-scale (`x_scale="point"`, like line) — categories map
  to evenly-spaced points; labels land under them. There is **no** band padding
  (that is column's geometry).
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the area via the `<defs>` pre-pass.
- Area is a **variant** of the reference line renderer + column's stacking
  transform — it forks **neither**; the extraction they triggered
  (`_cartesian.py` / `cartesian.go`) is the substrate it reuses.

## Not yet supported (roadmap)

- Live renderers (`area.py` / `area.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **Streamgraph** (wiggle / silhouette baseline offset) — a variant layering a
  baseline-offset transform on this stacked-area renderer.
- **Area range (arearange)** — the pure `{low,high}` band (rank 10); a sibling
  with its own point model, distinct from the stacked cumulative baseline.
- **Area-spline / stepped area** — already available via `curve:"monotone"` /
  `step` on the top edge; called out here as named Highcharts subtypes.
- Negative-stack handling, area with `null`/gap points, inverted axes — variants
  layered on this base.
