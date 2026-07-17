# Chart: Range area (`arearange`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** ([`charts/column/design.md`](../column/design.md)) and the
> reference recipe ([`charts/line-basic/design.md`](../line-basic/design.md)),
> and adds the sibling build detail: the pure `{low,high}` point model, the
> single-path band mark, the reused chrome, the parity traps, and the a11y DOM
> contract.

- **Chart id:** `arearange`
- **Spec `type`:** `"arearange"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 10** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; range-area rides the shared cartesian frame
  once the point model lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3
  Rank 10, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/arearange.py` · `libs/go/arearange.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A range-area chart: one or more series drawn as a **filled band between two
data boundaries** — a **high** line and a **low** line — over a shared
categorical x-axis and a numeric y-axis. Each datum contributes **two** y-values
(`low` and `high`) at the same x; the fill is the region between them. There is
**no center line** and **no baseline anchor** — the band floats between its own
two boundaries. It is the canonical way to show an interval over ordered x: a
p50–p95 latency band, a min–max temperature envelope, a forecast confidence
range.

Range-area is **build rank 10** — the first driver of the **pure `{low,high}`
point model** (a datum with two positional y-values and *no* center y, distinct
from the error-bar `{y,low,high}` center+range model, Rank 9). Its net-new work
is exactly two things: that point model, and **band-fill between two DATA paths**
(as opposed to stacked-area's fill between a series and a cumulative baseline).
Everything else is reuse — it runs line's already-parity-locked path builder
**twice** and concatenates the two passes.

## Use it when

- Your x is **ordered categories or time** (hours, days, versions) and each x
  carries an **interval** — a `(low, high)` pair you want to shade.
- You want to show a **band / envelope / confidence range** rather than a single
  trend line: percentile spreads (p50–p95), min–max, forecast ±.
- Rows look like: `label -> (low, high)` (one band) or several such bands sharing
  one x (nested percentile bands).

Do **not** use it for: a single **trend** with one y per x (use `line-basic`);
an interval with a **meaningful center estimate plus** whiskers (use `errorbar`
— its `{y,low,high}` keeps the center y this chart drops); **floating bars** per
discrete category rather than a continuous shaded band (use `columnrange`);
**part-to-whole composition** (use stacked `area`). See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each series carries **two** aligned numeric arrays of length `N`: the **high**
  boundary and the **low** boundary, `low[i] <= high[i]` per index.
- **Landed model (target):** a single `data` array of `[low, high]` pairs —
  `data: [[low,high], …]` (positional sugar) or `[{ "low":…, "high":… }, …]`
  (object form). This is the pure `{low,high}` point model (§3.3 Rank 10, point
  model §3.2). It arrives with the Rank-3 point-model landing in the shared
  validator + spec models.
- **Today's model (what the examples use, so `validate()==[]`):** the point
  model is **not yet** in the shared validator, which still requires
  `series[].data` to be `number[]` (each element a bare number). So an example
  spec carries the band as the currently-validated `data: number[]` = the
  **high** boundary, **plus a forward-compatible `low: number[]` companion** for
  the low boundary. Both validators ignore the unknown `low` key
  (forward-compatible), so `validate()` returns `[]` today; when the point model
  lands, `data` (highs) + `low` fold into `data: [[low,high]]` with no change of
  meaning. (This mirrors how the column exemplar carries `stacking`/`grouping`
  as forward-compatible keys until they land in the validator.)

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"arearange"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the band fill) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (generalized to show **low–high per cell**, §5.4b-DT below). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`subtype`** | string | `"arearange"` | **NEW field (areaspline-range subtype selector).** `"arearange"` = straight boundary segments; `"areasplinerange"` = both boundaries drawn as smooth Fritsch–Carlson splines (reuses line's `_spline_d`). Equivalent to setting `series[].curve:"monotone"` on every series (the chart-level sugar). Forward-compatible until landed via the §5.4b five-place lockstep |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (aligned to each datum by index) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks) | clamp the y range; auto range spans **min(all lows) → max(all highs)** with 0 forced in (`include_zero=True`) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | **high** boundary values, length `N` (the currently-validated `number[]`; folds into `data:[[low,high]]` when the point model lands) |
| **`series[].low`** | number[] | — | **NEW field.** the **low** boundary values, length `N`, aligned to `data` (`low[i] <= data[i]`). Forward-compatible companion to `data` (the highs) until the `{low,high}` point model lands |
| `series[].color` | string \| gradient | palette by index | the **band fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole band; legend swatch + boundary stroke use stop 0) |
| `series[].fillOpacity` | number | 0.5 | band fill opacity (a range area is a *filled* mark — unlike line, the fill is the whole point, so it defaults visible) |
| `series[].pattern` | object | — | hatch fill for the band: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |
| `series[].lineWidth` | number | 0 | **optional bounding stroke** on the two boundaries: `0` = fill only (no outline); `>0` = stroke the high+low edges at this width in the series color |
| `series[].curve` | string | — | `monotone` = smooth (Fritsch–Carlson) boundaries for **this** series (per-series form of `subtype:"areasplinerange"`); default straight |
| `series[].dashStyle` | string | solid | dash for the optional bounding stroke: solid/dashed/dotted |

Fields carried over from the line spec but **inert** for range-area (there is no
single line, only a filled band): `step`, `marker` are accepted by the shared
validator (forward-compatible) but not consumed by the range-area marks.
Full schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** the **pure `{low,high}` point model** — two positional
  y-values per x, **no center y**. This is the net-new data shape of Rank 10 and
  is deliberately *distinct* from error-bar's `{y,low,high}` (which keeps a
  center estimate): a range area draws only the two envelope boundaries.
- **Bare-number bridge (today):** `series[].data` is the currently-validated
  `number[]` = the **high** boundary; `series[].low` is the forward-compatible
  `number[]` = the **low** boundary. When the Rank-3 point model lands, `data`
  becomes `[[low,high]]`/`[{low,high}]` and the two arrays coalesce — the meaning
  is unchanged, so no example rewrites its numbers, only its shape.
- **The frame owns the y-domain — and it must see BOTH boundaries.** For a range
  area the auto y-range is `nice_ticks` over **min(all lows) → max(all highs)**
  with 0 forced in (`include_zero=True`). This is the one place range-area *must*
  extend the frame's y-range extractor beyond line's `s.data`: line reads only
  `v` (the single y), but range-area's domain would clip every low value below
  the axis if the extractor saw only `data` (the highs). When the point model
  lands, `build_frame`'s y-range extractor moves from `v` to
  `min(datum.low, datum.high)` / `max(datum.low, datum.high)` in lockstep with
  the marks (§4.2 y-range-extractor note; §5.4b). The marks themselves **never**
  recompute a scale — they call `fr.ypix` only.
- **No baseline anchor.** Unlike column/area, the band does **not** anchor to
  `ypix(0.0)`; both edges are data-driven (`ypix(low)` and `ypix(high)`). 0 is
  forced into the *domain* for a stable axis, but it is not a mark baseline.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). It uses the
**point** x-scale (boundaries are drawn at point positions, like line/area — not
band slots) and `include_zero=True`:

```python
# libs/python/peakcharts/charts/arearange.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Range area", "point", _arearange_marks)   # include_zero defaults True
```
```go
// libs/go/arearange.go — package peakcharts
func renderAreaRangeSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Range area", "point", areaRangeMarks, true)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one filled band `<path>`** plus **one `.pk-point`
per datum** (the hoverable elements — the band replaces line's point markers as
the interactive target, but each datum still gets a `.pk-point` at its high edge
for tooltip/crosshair/keyboard nav):

```html
<g class="pk-series" data-series="0">
  <path class="pk-series-range pk-band" data-series="0"
        d="M64.0 300.0 L214.0 260.0 L364.0 180.0 … L364.0 240.0 L214.0 300.0 L64.0 340.0 Z"
        fill="#2f7ed8" fill-opacity="0.5" stroke="none"/>
  <!-- one .pk-point per datum (at the high edge; carries low+high in data-*) -->
  <circle class="pk-point" data-series="0"
          data-series-name="p50–p95" data-x="00:00" data-low="60" data-high="120" data-y="60–120"
          data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
          cx="64.0" cy="300.0" r="3.5"/>
  … one .pk-point per datum …
</g>
```

- **One band path per series.** Its `d` is the concatenation of **two** passes of
  line's parity-locked path builder: the **high** boundary L→R, then the **low**
  boundary R→L, then `Z`. Because both passes reuse the exact `_path_d`/`pathD`
  (or `_spline_d`/`splineD` when `subtype:"areasplinerange"`/`curve:"monotone"`)
  that line already golden-tested, the `:.1f` coordinate bytes match across
  languages **for free** — no new geometry to parity-verify. See the band-fill
  layout below.
- **Fill:** read `fr.styles[si].fill` — the resolved band paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex** — the
  same rule column's bar uses. Never leave a band unfilled (an unfilled range
  area shows nothing — NN#2). `fill-opacity` comes from `series[].fillOpacity`
  (default `0.5`).
- **Optional bounding strokes:** when `series[].lineWidth > 0`, additionally
  stroke the two boundaries in the series `stroke` color (dash from
  `series[].dashStyle`). With `lineWidth:0` (default) the band is fill-only.
- **`.pk-point` per datum:** class `pk-point` is the runtime contract class
  (tooltip / highlight / crosshair / legend-toggle / keyboard nav). Each datum
  emits one at its **high** edge (`cx = xpix(i)`, `cy = ypix(high)`); it carries
  `data-low`, `data-high`, and a combined `data-y="low–high"` so the tooltip
  shows the interval, not a single number.
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (datum x) — the crosshair
  reads it — and `cy` (the high edge) by convention.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band-fill layout — the pinned geometry

The band is **two passes of the already-parity-locked line path builder,
concatenated**. Evaluate in **exactly this order** in both languages so the
`:.1f` coordinates land ULP-for-ULP identically:

```
n           = len(data)                                   # = len(low)
hi_pts      = [(xpix(i), ypix(high[i])) for i in 0..n-1]  # high boundary, natural x order
lo_pts      = [(xpix(i), ypix(low[i]))  for i in 0..n-1]  # low boundary,  natural x order

# straight (subtype "arearange"):        top = _path_d(hi_pts)
# smooth   (subtype "areasplinerange"):  top = _spline_d(hi_pts)
top_d       = path_or_spline(hi_pts)                      # "M… L…"  (high, L→R)
bottom_rev  = reversed(lo_pts)                            # low boundary, R→L
bottom_tail = "".join(f" L{x:.1f} {y:.1f}" for (x,y) in bottom_rev)
band_d      = f"{top_d}{bottom_tail} Z"                   # high L→R, then low R→L, then close
```

- **High boundary is drawn L→R with the SAME builder line uses** — so its
  segment bytes are identical to a line drawn over the highs. **Low boundary is
  appended R→L** as plain `L` segments (a reversed traversal), then `Z` closes
  the ring. The result is one closed path whose interior is the band.
- For **areasplinerange** both boundaries use `_spline_d`/`splineD`. The low
  boundary's reversed spline is built by splining `lo_pts` L→R and reversing the
  emitted point sequence's `L` tail identically in both languages (pin the
  reversal to operate on the **evaluated** spline sample points, not on the
  control points, so the two languages traverse the exact same coordinates).
- **`xpix` is the POINT scale** (`plot_x + plot_w*i/(n-1)`, and `plot_x+plot_w/2`
  when `n<=1`) — the same scale line/area use. Range-area does **not** use band
  slots; there is no `PAD`/`K` sub-band arithmetic.
- Single datum (`n==1`) ⇒ a degenerate zero-width band; pin the `n<=1` xpix
  branch identically (frame already does).

## Reused chrome (obtained from the frame — never re-implemented)

Range-area inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (over the low→high domain the **frame**
  computes); y gridlines + labels.
- Categorical x-axis via the **point** `xpix`; the shared x-label loop lands
  labels under point positions with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- **line's `_path_d` / `_spline_d` builders** — run **twice** (highs L→R, lows
  R→L). This is the load-bearing reuse: no new coordinate math, so no new parity
  surface.
- **Area fill / gradient / pattern / defs** machinery — the same paint path
  column and area use, reading `SeriesStyle.fill`.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (generalized to low–high, below) + keyboard nav. Responsive `<svg>` viewBox;
  the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="point"` and `include_zero=True`. It passes the
bare noun **`"Range area"`** — the frame expands it to `"Range area chart with N
series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Two-pass path ORDER** — build the high boundary L→R with `_path_d`/`_spline_d`
  first, then append the low boundary **R→L** as `L` segments, then `Z`. Reversing
  the wrong boundary, or appending L→R, produces a self-crossing bow-tie that
  still "renders" but is wrong and diverges from the intended fill.
- **Reversed-spline traversal** — for areasplinerange, reverse the **evaluated
  sample points** of the low spline, not the control points; both languages must
  sample then reverse in the same order or the `:.1f` bytes diverge.
- **Frame owns the y-domain over BOTH boundaries** — the auto y-range must be
  `min(all lows) → max(all highs)` (with 0 forced in); an extractor that reads
  only `data` (highs) clips the lows below the axis. This is the point-model
  lockstep move (`v` → `datum.low`/`datum.high`) that must land with the marks.
  The marks still call `fr.ypix` only — recomputing a scale is a defect (NN, §7.1).
- **Band-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  (line's under-fill sentinel) is the wrong field. Never emit an unfilled band.
- **`data-y` carries the interval** — the tooltip shows `low–high` (both values
  via `fmt_num`), not a single coerced number. Keep `data-low`/`data-high`
  separately for the runtime + data table.
- **`fillOpacity` default is 0.5, not 0** — a range area is a filled mark; a `0`
  default (line's) would render an invisible band. This default lives in the
  spec model (both languages), applied **only on absence** (§5.4b).
- **Formatters** — path `d` numbers, `cx`, `cy` via `:.1f`/`f1`; `data-low`,
  `data-high`, radii via `fmt_num`/`fmtNum`; every user string via `esc`. A
  leaked raw `<` fails the XSS tests.
- **No baseline confusion** — do **not** anchor either edge to `ypix(0.0)`; both
  are data-driven. 0 is in the domain for a stable axis only.
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
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`
  — plus range-area's `data-low` and `data-high`. `data-y` is the human interval
  `"low–high"` (both via `fmt_num`) so the tooltip shows the band, not one number.
- **Crosshair anchor:** every `.pk-point` carries `cx` (datum x) and by
  convention `cy` (the high edge).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-low = esc(fmt_num(low))`,
  `data-high = esc(fmt_num(high))`, `data-y = esc(fmt_num(low)+"–"+fmt_num(high))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`.
  Pixel attrs (`cx,cy`, path `d`) use `:.1f`/`f1`.
- **A11y data table is GENERALIZED (§5.4b-DT — mandatory).** Range-area is the
  first chart whose `data` stops being a single `number[]`, so the shared
  visually-hidden data table (`_data_table`/`dataTable`, NN#4) **must** be
  generalized in lockstep in both languages to render the point model faithfully:
  each `(series, category)` cell shows the **band** `low–high` (e.g. `60–120`),
  **not** a coerced single number — replacing the line-era `fmt_num(s.data[i])`
  cell with `fmt_num(low)+"–"+fmt_num(high)`. A test must prove Py==Go table
  bytes. Shipping the un-generalized (single-number) table while passing the
  golden gates is **forbidden** — it is part of "adding a new data shape,"
  alongside the §5.4b field drill and the Rank-3 byte-identity gate.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  the generalized visually-hidden data table in the HTML; keyboard nav walks the
  per-datum `.pk-point`s. `a11y:false` restores the pre-a11y bytes.
- **Static-first:** the chart is fully readable with JS disabled — the band is
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "arearange",
  "title": "Request Latency Band",
  "subtitle": "p50–p95 over the day",
  "xAxis": { "title": "Hour", "categories": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"] },
  "yAxis": { "title": "Latency (ms)" },
  "series": [
    { "name": "p50–p95", "data": [120, 135, 180, 240, 210, 150], "low": [60, 68, 95, 140, 120, 80] }
  ]
}
```

`data` holds the **high** boundary (p95); `low` holds the **low** boundary (p50).
When the `{low,high}` point model lands they fold into `data: [[60,120], …]`.

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single band, straight boundaries, default fill, `data`(high)+`low` companion |
| [`examples/spline-range.json`](examples/spline-range.json) | `subtype:"areasplinerange"` (smooth boundaries via `_spline_d`), `fillOpacity`, custom color, `lineWidth` bounding stroke |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + **two nested bands** (multi-series legend + palette) + a gradient band fill (defs pre-pass → `url(#grad)`) |
| [`examples/adversarial.json`](examples/adversarial.json) | hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field — series name, category labels, custom color — so the XSS tests run against the range-area marks (§5.5d) |

`AREARANGE_CASES = ["basic","spline-range","dark","adversarial"]` (golden case
`dark` = `themed-dark.json`). The `adversarial` case is the pinned XSS witness:
its golden must contain the **escaped** bytes and **no** raw `<script>`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/arearange/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="arearange",
    title="Request Latency Band",
    x_axis=Axis(title="Hour", categories=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]),
    y_axis=Axis(title="Latency (ms)"),
    series=[
        Series("p50–p95", [120, 135, 180, 240, 210, 150]),   # highs; low=[60,68,95,140,120,80] once the point model lands
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
- **Hover a datum** → tooltip (x, series, `low–high`) + highlight + crosshair.
- **Click a legend item** → toggle that band on/off.
- **Keyboard** → arrows walk the per-datum points; Esc clears without stealing
  focus.
- Renders fully (static) even with JavaScript disabled — the band is filled and
  the low–high data table is readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) over **min(all lows) → max(all highs)**
  and forces 0 into the domain unless `yAxis.min/max` clamp it.
- Boundaries use the **point** x-scale (`x_scale="point"`) — the same as
  line/area; labels land under point positions.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is
  unset; a gradient/pattern color fills the whole band via the `<defs>` pre-pass.
- `subtype:"areasplinerange"` (or `series[].curve:"monotone"`) swaps both
  boundary builders from `_path_d` to `_spline_d` — the *only* change from the
  straight variant; the two-pass concatenation is identical.
- Range-area is a **sibling** of the exemplar (`column`): it re-uses the extracted
  `_cartesian.py` / `cartesian.go` substrate and never forks it.

## Not yet supported (roadmap)

- Live renderers (`arearange.py` / `arearange.go`) — deferred; design + examples
  + validation are complete. Only `line` renders today. Landing requires the
  Rank-3 `{low,high}` point model in the shared validator + spec models + the
  §5.4b-DT data-table generalization (all in lockstep, both languages).
- **Column range** (`columnrange`) — the discrete floating-bar sibling sharing
  this exact `{low,high}` point model (rank 11).
- **Horizontal** range area — falls out of the orientation generalization.
- `null`/missing boundary (gap) handling, and a third **center** series overlaid
  on the band (a line through the middle) — variants layered on this base.
