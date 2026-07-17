# Chart: X-Range / Gantt (`xrange`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this recipe copies the
> Cartesian **exemplar** [`charts/column/design.md`](../column/design.md) (itself
> modeled on [`charts/line-basic/design.md`](../line-basic/design.md)) and swaps
> in the span-sibling build detail: the `{x, x2, y}` span point model, the
> horizontal floating-bar mark on a **datetime** value axis, the **lane** (per-row
> category) band, the Gantt milestones + dependency connectors, the reused chrome,
> the parity traps, and the a11y DOM contract.

- **Chart id:** `xrange`
- **Spec `type`:** `"xrange"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank:** late sibling —
  reuses **band-layout** (Rank 1), **orientation transpose** (Rank 2),
  **numeric/datetime x-axis** (Rank 3), and the **floating-bar primitive**
  (Rank 8); forces no new *primitive*, only the span composition · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; xrange rides the shared cartesian frame once
  the floating-bar primitive + numeric/datetime x-axis + orientation land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2 Family A
  (X-range/Gantt row), §3.2, §3.3 Ranks 1/2/3/8, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/xrange.py` · `libs/go/xrange.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

An X-range chart: one or more series drawn as **horizontal bars that span a
`start → end` range** (`x1..x2`) along a **datetime (or numeric) value x-axis**,
each bar sitting in a **category lane** on the y-axis. Each bar encodes an
*interval* — when a thing began and ended — not a magnitude anchored at zero. It
is the substrate for **distributed-tracing span waterfalls** (Jaeger / Tempo),
**per-thread task bars**, and **project Gantt charts**. Its **Gantt** superset
adds two decorations: **milestones** (zero-duration diamond markers) and
**dependency connectors** (finish-to-start arrows between spans). The floating
span bar is the hoverable, interactive element (it replaces the line chart's
point markers).

X-range is a **late Cartesian sibling**: by the time it is built the family
already owns everything it needs and it forces **no net-new primitive**. It
composes four things earlier ranks extracted — the **band-layout** (Rank 1, here
one band per lane), the **orientation transpose** (Rank 2, the value axis on x
and the band axis on y), the **numeric/datetime x-axis** (Rank 3, `include_zero
= False`), and the **floating-bar primitive** (Rank 8, a `<rect>` between two
arbitrary values) — plus a **span `{x, x2, y}` point model** and two Gantt
decorations (milestone glyph + dependency connector) layered on top.

## Use it when

- Your data is a set of **intervals on a timeline** — each row has a **start and
  an end** (`x1..x2`) and belongs to a **lane** (a thread, service, operation,
  resource, task track). The classic cases:
  - **Trace / span waterfall** — distributed-tracing spans, one lane per
    service/operation, `start`/`end` in milliseconds from the trace root.
  - **Per-thread task bars** — wall-clock activity per worker/thread/CI stage.
  - **Project Gantt** — tasks with **dependencies** and **milestones** over
    calendar time.
- You want to see **when** each thing ran, **how long** it took (bar width), and
  **how the intervals overlap or chain** across lanes — not a single value per
  category.
- Rows look like: `lane -> (start, end)`, optionally with a **task label**, an
  **id**, **predecessor dependencies**, and a **milestone** flag.

Do **not** use it for: a single **magnitude** per category anchored at zero (use
[`column`](../column/design.md) / [`bar`](../bar/design.md)), a **`(low,high)`
value band** with no time semantics (use [`columnrange`](../columnrange/design.md)),
a **single event marker per point** with no duration (use `timeline`), an
**aggregated** call-stack profile where node width = self+children samples (that
is the Hierarchy flame graph, Family D — the *time-ordered* flame chart is an
xrange sibling), or a plain **trend** over time (use [`line-basic`](../line-basic/design.md)).
See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `yAxis.categories`: the **lane labels**, length `L` (threads, services,
  operations, resources, task tracks). Lanes render **down the y-axis**, one band
  each. Each span names its lane by an integer index into this array.
- `xAxis` is the **time value axis** (numeric or `datetime`), **not** a category
  axis — spans carry numeric `start`/`end` positions on it. `xAxis.type:"datetime"`
  formats the tick labels as dates (forward-compatible; see Spec fields).
- each `series[]` carries a set of **spans**, each a `{x, x2, y}` record — start,
  end, lane index — plus optional Gantt fields (`id`, `name`, `dependency`,
  `milestone`). A series groups spans that share a color / legend entry (a trace,
  a project phase, a thread); its spans may live in **many** lanes.
- **The value payload is richer than `number[]`.** A span needs at least three
  numbers (`start`, `end`, `lane`); a bare number cannot express it. See
  **Data model** for how the payload is carried today (validator-compatible) vs.
  after the point model lands.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"xrange"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the span `<rect>`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (generalized to render **start / end / lane** per span — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | **time-axis** label (e.g. "Elapsed (ms)", "Date") — renders under the bottom/x axis |
| **`xAxis.type`** | string | `linear` | **NEW field (forward-compatible).** `linear` (numeric ticks) or `datetime` (tick labels formatted as dates; `start`/`end` are epoch-based numbers). Still a **value** axis either way — spans carry numeric positions. Wire it through the §5.4b five-place lockstep when the renderer lands |
| `xAxis.min` / `xAxis.max` | number | auto (nice ticks over all spans; **0 NOT forced in**) | clamp the **time** window; the time axis is **not** zero-anchored (`include_zero=False`) — a trace running `1200..1850 ms` must not waste the axis down to 0 |
| `xAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | **vertical** time gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `yAxis.title` | string | — | **lane-axis** label (e.g. "Service", "Thread", "Task") |
| `yAxis.categories` | string[] | index `0..L-1` | the **lane labels**, length `L` — the band rows down the y-axis; `spans[].y` indexes into this array |
| `series[].name` | string | `Series i` | legend + tooltip name (a trace / phase / thread) |
| `series[].data` | number[] | — | the **span start** values, length = number of spans (interim encoding — see Data model; keeps the spec validator-clean and gives the a11y fallback a meaningful value) |
| **`series[].spans`** | object[] | — | **NEW field (forward-compatible companion).** the full span records the marks draw, aligned to `data` by index. Each span: `{ "x": <start>, "x2": <end>, "y": <lane index>, "id"?: string, "name"?: string, "dependency"?: string[], "milestone"?: bool }`. `x` mirrors `data[i]`; `x2` is the end; `y` selects the lane; `id`/`dependency` drive **dependency connectors**; `milestone:true` renders a **diamond** at `x` instead of a bar |
| `series[].color` | string \| gradient | palette by index | the **span fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole span bar; legend swatch uses stop 0). A **left→right** gradient (`x1:0,y1:0,x2:1,y2:0`) tracks the span's time direction most naturally |
| `series[].pattern` | object | — | hatch fill for the span: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line spec but **inert** for xrange (no line to draw,
spans don't stack): `fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`,
`marker`, and `stacking` are accepted by the shared validator (forward-compatible)
but not consumed by the xrange marks. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** each datum is a **span** `{x, x2, y}` — a start, an end, and
  a lane index — optionally with `id` / `name` / `dependency` / `milestone`. This
  is the **span point model**, a datum richer than the single-`y` `number[]` that
  line/column use, and richer than the `{low,high}` range model (it adds the lane
  dimension + the datetime x placement).
- **Carried today (validator-compatible):** the strict validator
  (`validate.py`/`validate.go`) still requires `series[].data` to be `number[]`
  (the point model lands with a later rank, not before). So each example carries
  the span records in the **forward-compatible `series[].spans` companion** (an
  array of `{x, x2, y, …}` objects the validator ignores) and keeps
  `series[].data` as the parallel `number[]` of **span starts** (`data[i] ==
  spans[i].x`), so the spec validates (`validate() == []`) and the a11y fallback /
  data table render a meaningful value. The example specs in this folder use
  exactly this encoding — the same pattern
  [`candlestick`](../candlestick/design.md) uses for its `ohlc` companion and
  [`columnrange`](../columnrange/design.md) for its parallel `high` array.
- **After the point model lands:** `series[].data` **becomes** the array of
  `{x, x2, y, …}` span datums (positional `[x, x2, y]` sugar); `spans` folds into
  `data`; the validator + both spec models gain the span datum shape in the §5.4b
  five-place lockstep; and the accessible data table generalizes off `number[]` in
  lockstep (§5.4b-DT). A bare number stays valid elsewhere (line/column goldens
  never move); a bare number in an xrange `data` is read as a start with an absent
  end → a degenerate zero-width (milestone-like) span, never coerced.
- **Lanes are the band axis (y).** The **rows** come from `yAxis.categories`
  (length `L`); `spans[].y` is an integer index into them. Multiple spans — from
  one series or several — may share a lane (a Gantt row / a thread with several
  sequential tasks). This is the **swimlane / per-thread lane** model.
- **The frame owns the time-domain, over BOTH ends.** The value (time) axis spans
  `nice_ticks(min(all starts), max(all ends))` with **`include_zero=False`** — the
  time axis is **not** forced to 0 (unlike column/bar). The marks never recompute a
  scale; they call `fr.xpix_val` / `fr.ypix_band` only.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). Two arguments differ from
column's delegation: **`include_zero=False`** (the time axis is not baseline-anchored)
and **`orientation="horizontal"`** (the band axis is the y lane axis, the value
axis is the x time axis — the Rank-2 transpose):

```python
# libs/python/peakcharts/charts/xrange.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    # noun="X-range", band scale on the LANE (y) axis, free time value axis on x
    return render_cartesian(spec, "X-range", "band", _xrange_marks,
                            include_zero=False, orientation="horizontal")
```
```go
// libs/go/xrange.go — package peakcharts
func renderXRangeSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "X-range", "band", xrangeMarks, false, "horizontal")
}
```

> **Where the lane categories come from.** Unlike [`bar`](../bar/design.md) — which
> transposes `column` keeping the band categories under `xAxis.categories` — xrange
> authors its lane categories under **`yAxis.categories`** (the axis they actually
> render on), because the x-axis is a genuine **datetime value** axis, not a
> transposed category axis. Under `orientation="horizontal"` the frame therefore
> sources the band labels from the **y** lane axis and drives `fr.xpix_val` for the
> time axis. `n = L` (lane count).

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one floating span `<rect>` per span** spanning
`xpix_val(start)` (left) to `xpix_val(end)` (right) inside its lane band:

```html
<g class="pk-series" data-series="0">
  <rect class="pk-span pk-point" data-series="0"
        data-series-name="checkout-trace" data-x="payment" data-y="1200"
        data-start="1200" data-end="1850" data-lane="payment" data-duration="650"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="512.0" cy="180.0" x="410.0" y="164.0" width="204.0" height="32.0"
        fill="#2f7ed8"/>
  … one .pk-span.pk-point per span …
</g>
```

- **Class:** `pk-span pk-point`. `pk-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `pk-span` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The span bar **is** the hoverable point; there are no separate
  markers.
- **Span geometry (the floating-bar primitive, transposed to x).** Let `xval(t)` be
  the value-axis pixel on x (frame `xpix_val`, the time axis with
  `include_zero=False`) and the lane band below give the y-slot. The rect **floats**
  along x between the two time values — it is **not** zero-anchored:
  - `x = xval(min(start, end))`, `width = |xval(end) - xval(start)|`.
  - Using `min` + `abs` (identical to candlestick's body / columnrange's floating
    bar) keeps `width` non-negative even if a spec supplies `end < start`, and is
    parity-safe. **Never** anchor to `xval(0.0)` — that is column/bar's baseline;
    a span floats.
  - `y = top(j)` and `height = barThickness` from the lane band layout below
    (`j = spans[i].y`).
- **Zero-duration span (`start == end`) / milestone:** the rect would have zero
  width. If the span is **not** a milestone, apply the **min-1px** rule (the same
  doji rule candlestick pins for `open == close`): `width = max(1.0, |xval(end) -
  xval(start)|)`, evaluated **identically** in both languages so a flat span stays a
  visible hairline. If `spans[i].milestone == true`, draw a **diamond** instead: a
  `<polygon class="pk-milestone pk-point">` centered at `(xval(start),
  ypix_band(j))` with half-extent `barThickness/2` — vertices at
  `(cx, cy-h)`,`(cx+h, cy)`,`(cx, cy+h)`,`(cx-h, cy)`. The milestone carries the
  **same** `data-*` as a span (`data-start == data-end`, `data-duration = 0`).
- **Dependency connectors (Gantt).** For each span carrying `dependency:[predId,…]`,
  draw a finish-to-start connector from **each predecessor's right edge**
  `(xval(pred.end), ypix_band(pred.y))` to **this span's left edge**
  `(xval(start), ypix_band(this.y))` as a `<path class="pk-dependency">` (an
  orthogonal elbow ending in a small arrowhead). The renderer builds a
  **span-id → (endX, laneY)** index in a pre-pass so a dependency can resolve a
  predecessor in **any** series. The connector is drawn **inside the dependent
  span's series group** (so it hides with that series on legend-toggle) but is
  **not** a `.pk-point` — it is decorative (no runtime behavior, no new JS; NN#2).
- **Fill:** read `fr.styles[si].fill` — the resolved span paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a span unfilled (an
  unfilled span bar is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (span center x = `xval((start
  + end)/2)`) — the crosshair reads it — and by convention `cy` (lane band center =
  `ypix_band(j)`). Without `cx` the crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Lane band layout — the pinned geometry (column's band, transposed to y)

xrange rides the **band** scale on the **y (lane) axis** under
`orientation="horizontal"`. The band scheme is column's §3.2 formula with the plot
**height** substituted for the width and `y` for `x`, and the band count `n = L`
(the number of lanes, from `yAxis.categories`). Evaluate the arithmetic in
**exactly this operation order** in both languages so `f1` / `:.1f` rounding lands
ULP-for-ULP identically (blueprint §3.2 / §4; the frame's `ypix_band` implements
the lane center, the marks build the slot):

```
laneHeight     = plot_h / L
ypix_band(j)   = plot_y + laneHeight*j + laneHeight/2     # lane band center on y
PAD            = 0.2                                       # single group-padding constant
barThickness   = laneHeight * (1 - PAD)                    # groupH with K = 1
top(j)         = ypix_band(j) - barThickness/2
```

- Every span in lane `j` uses the **same** lane band center `ypix_band(j)` and the
  same `barThickness` — a Gantt row / trace lane is one bar-height thick regardless
  of how many spans it holds (spans in a lane are normally sequential in time). One
  centered bar of thickness `barThickness = laneHeight*(1-PAD)` per lane
  (`K = 1`).
- **Rare multi-series-shares-a-lane sub-banding.** If several series place spans in
  the **same** lane and you want them vertically separated, split the lane into
  `K = len(series)` sub-bands exactly as [`bar`](../bar/design.md) does —
  `barH = groupH / K`, `top(j,k) = ypix_band(j) - groupH/2 + barH*k` — with
  `groupH = laneHeight*(1-PAD)`. Default is `K = 1` (all series share the lane
  thickness, drawn in series order).
- `PAD = 0.2` and the band formula are the **same constants** column/bar use — not
  per-author choices.
- The **value axis** (x, time), by contrast, is **not** shared verbatim with
  column: xrange passes `include_zero=False` so the time domain spans
  `min(start)..max(end)` without forcing 0.

## Reused chrome (obtained from the frame — never re-implemented)

xrange inherits, with **zero** re-implementation, everything column/bar inherit —
the frame just draws it transposed by orientation with a free time value axis
(§3.1, §4.2):

- Plot area + margins; both axes + axis lines + axis titles.
- Linear **time** value scale via `nice_ticks` → `xpix_val` — computed by the
  **frame** over both span ends with `include_zero=False`; **vertical** time
  gridlines + labels along the bottom.
- Categorical **lane** axis via the band scale on **y** (`n = L`); the shared
  category-label loop lands lane labels beside band centers down the left with no
  per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (generalized for the span model, §5.4b-DT) + keyboard nav. Responsive `<svg>`
  viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"`, **`include_zero=False`** (free time
value axis), and **`orientation="horizontal"`** (lane band on y). It passes the
bare noun **`"X-range"`** — the frame expands it to `"X-range chart with N
series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **`include_zero=False`, NOT True** — the time axis must span
  `min(start)..max(end)`, **not** force 0 in. Copying column's `include_zero=True`
  would anchor a `1200..1850 ms` trace to 0 in **both** languages (a silent,
  byte-parity-passing bug — the flag must be explicit; blueprint §3.2 caveat).
- **Orientation transpose** — under `orientation="horizontal"` the band (lane)
  pixel is on **y** and the time value pixel on **x** in **both** languages; never
  let one language leave the value on y. The lane categories come from
  **`yAxis.categories`** (`n = L`), not `xAxis.categories`.
- **Time-domain over BOTH ends** — the frame's value-range extractor must span
  `min(all starts)`..`max(all ends)`, considering **every** span's start and end,
  not just the `data` (starts) array. The marks call `fr.xpix_val` only;
  recomputing a scale (even to identical bytes) is a defect (NN, §7.1).
- **Lane band arithmetic ORDER** — evaluate the lane band lines above in that exact
  order (over `plot_h`/`y`, `n = L`); a reassociated `plot_h/L` or
  `laneHeight*(1-PAD)` diverges after `f1` rounding.
- **Floating-span geometry** — `x = xval(min(start,end))`,
  `width = |xval(end) - xval(start)|`; **min-1px** for a non-milestone zero-duration
  span (the shared doji rule with candlestick / columnrange). Never emit a negative
  `width`; never anchor to `xval(0.0)`.
- **Milestone vs bar branch** — `spans[i].milestone == true` (or `start == end` used
  as a milestone) draws the **diamond** `<polygon>`, else the span `<rect>`; the
  branch condition and the diamond half-extent (`barThickness/2`) must be identical
  in both languages so the two paths do not diverge.
- **Dependency resolution ORDER** — build the span-id index by iterating
  `spec.Series` **by index** then each series' spans by index (never range-over-map
  in Go); resolve `dependency` ids against that stable index so connector endpoints
  and emission order match across languages. An unresolved id is **skipped**
  identically (no connector), never a crash.
- **Bar-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill` is
  line's field. Never emit an unfilled span.
- **`data-y` vs `data-start`/`data-end`** — `data-y` carries a single representative
  value (`fmt_num(start)`) so the existing runtime tooltip has a body with **zero JS
  changes**; the full span rides the forward-compatible `data-start` / `data-end` /
  `data-lane` / `data-duration` attributes and the generalized a11y data table. All
  are `esc(fmt_num(...))` (numbers) / `esc(...)` (the lane label).
- **Formatters** — `cx,cy,x,y,width,height`, diamond/connector path numbers via
  `:.1f`/`f1`; `data-y`, `data-start`, `data-end`, `data-duration`, radii via
  `fmt_num`/`fmtNum`; every user string (`data-series-name`, `data-lane`, span
  `name`, custom color) via `esc`. A leaked raw `<` fails the XSS tests.
- **No stacking path** — do not route xrange through the stacking transform; spans
  never accumulate. Ignore `stacking` if present.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` and each series' spans by index; keep series/point/legend
  `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the selectors
+ `data-*` below (`spec/svg-contract.md`). Emit them correctly and tooltip,
highlight, crosshair, legend-toggle, and keyboard nav all work with **zero JS
changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series; `N` is the integer
  series index, **consistent** across the group, its spans, and the legend item (do
  not renumber). A series' dependency connectors live inside its group so they hide
  with it.
- **Datum mark:** `.pk-span.pk-point` (a `<rect>`; a milestone is
  `.pk-milestone.pk-point`, a `<polygon>`) carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`
  (mandatory even though a `<rect>`/`<polygon>` ignores the hover `r`), **plus** the
  span extension `data-start`, `data-end`, `data-lane`, `data-duration`.
- **Crosshair anchor:** every `.pk-point` carries a `cx` (span center x =
  `xval((start+end)/2)`) and by convention `cy` (lane band center = `ypix_band(j)`).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(lane label)`; `data-y = esc(fmt_num(start))`;
  `data-start = esc(fmt_num(start))`; `data-end = esc(fmt_num(end))`;
  `data-lane = esc(lane label)`; `data-duration = esc(fmt_num(end - start))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`. Pixel
  attrs use `:.1f`/`f1`.
- **A11y default-on + the point-model data-table obligation (§5.4b-DT):**
  `role="img"` + concise `aria-label` + `<desc>` in the SVG; a separate
  **visually-hidden data table** in the HTML; keyboard nav walks spans. Because
  xrange's datum is a span (not a single `number`), the data table MUST be
  generalized **in lockstep in both languages** to render **start / end / lane** per
  span (not a coerced single number per row), proven by a Py==Go table-bytes test.
  `a11y:false` restores the pre-a11y bytes.
- **Static-first:** the chart is fully readable with JS disabled — spans,
  milestones, and connectors are server-rendered and filled; the crosshair ships
  `display:none`; the tooltip is JS-only.

## Example spec

See [`examples/trace-waterfall.json`](examples/trace-waterfall.json):

```json
{
  "type": "xrange",
  "title": "Checkout Request — Distributed Trace",
  "subtitle": "Span waterfall, one lane per service (elapsed ms from root)",
  "xAxis": { "title": "Elapsed (ms)", "type": "datetime" },
  "yAxis": { "title": "Service", "categories": ["gateway", "auth", "cart", "payment", "ledger"] },
  "series": [
    {
      "name": "checkout-trace",
      "data": [0, 40, 120, 210, 520],
      "spans": [
        { "x": 0,   "x2": 900, "y": 0, "id": "root",  "name": "POST /checkout" },
        { "x": 40,  "x2": 190, "y": 1, "id": "authz", "name": "verify token",   "dependency": ["root"] },
        { "x": 120, "x2": 500, "y": 2, "id": "cart",  "name": "load cart",      "dependency": ["root"] },
        { "x": 210, "x2": 760, "y": 3, "id": "pay",   "name": "charge card",    "dependency": ["cart"] },
        { "x": 520, "x2": 700, "y": 4, "id": "post",  "name": "post ledger",    "dependency": ["pay"] }
      ]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/trace-waterfall.json`](examples/trace-waterfall.json) | single series, distributed-tracing span waterfall, `datetime` x-axis (ms), one lane per service, dependency chain across lanes |
| [`examples/gantt.json`](examples/gantt.json) | project Gantt — multiple task spans across lanes with finish-to-start **dependencies** and a **milestone** span, `datetime` (epoch-day) x-axis |
| [`examples/swimlanes.json`](examples/swimlanes.json) | **per-thread lanes** — two series (worker threads) sharing lane rows, CI-pipeline stage bars, showing the swimlane model + legend toggle |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a **gradient** span fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) + a custom-colored series, deployment-window spans |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, lane label, span `name`, custom span color) so the XSS tests run
against the xrange marks (§5.5d).
`XRANGE_CASES = ["trace-waterfall","gantt","swimlanes","themed-dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/xrange/examples/trace-waterfall.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="xrange",
    title="Checkout Request — Distributed Trace",
    x_axis=Axis(title="Elapsed (ms)"),
    y_axis=Axis(title="Service", categories=["gateway", "auth", "cart", "payment", "ledger"]),
    series=[
        # spans travel in the forward-compatible `spans` companion until the point
        # model lands; `data` carries the span starts so the spec validates.
        Series("checkout-trace", [0, 40, 120, 210, 520]),
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
- **Hover a span** → tooltip (lane, series, start / end / duration) + span
  highlight + crosshair.
- **Click a legend item** → toggle that series on/off (its spans **and** its
  dependency connectors hide together).
- **Keyboard** → arrows walk the spans; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — spans, milestones, and
  connectors are server-rendered and filled.

## Rendering notes

- The **time** (x) value axis uses "nice numbers" ticks (~6) over
  `min(start)..max(end)` and is **not** zero-anchored (`include_zero=False`) unless
  `xAxis.min/max` clamp it — a timeline frames the data window, not 0. With
  `xAxis.type:"datetime"` the tick labels are formatted as dates; the underlying
  positions stay numeric.
- Spans use the **band** scale on **y** (`x_scale="band"`,
  `orientation="horizontal"`) — lanes occupy equal horizontal bands; lane labels
  land beside band centers down the left. `n = L` (lane count from
  `yAxis.categories`).
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole span via the `<defs>` pre-pass.
- Milestones render as **diamonds** (zero-duration markers); dependency connectors
  render as **finish-to-start elbow arrows** between spans, resolved through a
  span-id index so a predecessor may live in any series.
- xrange adds **no net-new primitive**: it composes column's **band layout** (one
  band per lane), bar's **orientation transpose** (value on x / band on y),
  scatter's **numeric/datetime x-axis** (`include_zero=False`), and candlestick's
  **floating-bar primitive** — plus the span point model + Gantt milestone/
  dependency decorations. It reuses the **same** extracted substrate
  (`_cartesian.py` / `cartesian.go`); it is **never** forked.

## Not yet supported (roadmap)

- Live renderers (`xrange.py` / `xrange.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Landing them depends on the
  span point model (§5.4b five-place lockstep) + the numeric/datetime x-axis +
  orientation + floating-bar primitive being extracted into the shared frame first,
  plus the §5.4b-DT data-table generalization.
- Canonical `{x, x2, y}` span datum + positional `[x, x2, y]` sugar — today the span
  is the interim `data` (starts) + parallel `spans` companion encoding.
- A true **continuous datetime x-scale** with calendar-aware tick placement
  (months/quarters, weekend shading) — today `datetime` labels ride a numeric value
  axis with `nice_ticks`.
- **Partial-fill / progress bars** (a `completed` fraction shading part of a Gantt
  bar), **resource-utilization coloring**, **collapsible task groups**, and
  **critical-path highlighting** — Gantt variants layered on this base.
- **Drag-to-reschedule** and other editing interactions — out of scope (static-first;
  the runtime only *enhances*, never edited for a chart add — NN#2).
