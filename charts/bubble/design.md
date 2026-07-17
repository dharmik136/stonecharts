# Chart: Bubble (`bubble`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> sibling build detail: data model, marks, the size-scale, reused chrome, parity
> traps, and the a11y DOM contract.

- **Chart id:** `bubble`
- **Spec `type`:** `"bubble"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 4** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; bubble rides the shared cartesian frame once
  scatter's numeric-x-axis + point-model land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 4, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/bubble.py` · `libs/go/bubble.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A bubble chart: one or more series drawn as **unconnected circles** on a plane
with a **numeric x-axis** and a **numeric y-axis**. Each point carries **three**
numbers — `x`, `y`, and `z`. `(x, y)` place the circle's center; **`z` drives its
radius** through a shared **size-scale**. The circles are semi-transparent so
overlapping bubbles read through one another (density). The bubble **is** the
hoverable, interactive element (it replaces the line chart's point markers and
the column chart's bar).

Bubble is **build rank 4** — the fourth Cartesian sibling. It rides directly on
**scatter** (rank 3, which landed the **numeric-x-axis** and the **`{x,y}` point
model**) and adds exactly **one** new reusable generalization: the **size-scale**
(`z → area-proportional radius`) plus an optional **size legend** (z buckets). It
introduces no new chrome and no new mark primitive beyond parameterizing the
existing point/circle mark's radius.

## Use it when

- You have a **third magnitude** to encode on top of an x/y correlation — e.g.
  latency (`y`) vs payload size (`x`) with **request volume** (`z`) as the bubble
  area; revenue vs margin sized by headcount; risk vs reward sized by exposure.
- The x and y are both **continuous numbers** (no shared category ordering) and
  the extra `z` variable is a **non-negative magnitude** you want compared by
  **area** at a glance.
- Rows look like: `x, y, z` per point (payload=30, latency=120, requests=5600).

Do **not** use it for: an x/y correlation with **no** third variable (use
`scatter`), a **trend** over ordered/continuous x (use `line-basic`), a
**magnitude across discrete categories** (use `column`), or **part-to-whole**
(use pie/donut). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- Each point is a `{x, y, z}` triple: `x`/`y` are numeric coordinates, `z` is a
  **non-negative magnitude** mapped to the circle radius by the size-scale.
- The **z-domain is global** — `zmin`/`zmax` are reduced over **every** point of
  **every** series (see [Size scale](#size-scale--the-pinned-geometry)) so a given
  `z` maps to the **same** radius everywhere and bubbles are comparable across
  series.
- **Transitional representation (what the examples carry today).** The canonical
  `{x,y,z}` datum (and its positional `[x,y,z]` sugar) is the **point model** that
  scatter/bubble introduce (§3.2, §3.3 Rank 3–4); it is **not yet accepted by the
  current validator**, which still requires `series[].data` to be `number[]`
  (the "bare number stays valid" fast path — a bare number is `y`, `x = index`).
  So until the point model lands, an example bubble carries:
  - `series[].data` — the **`y`** values, `number[]` (validated today);
  - `series[].x` — the **`x`** values, `number[]` (forward-compatible, ignored by
    the validator);
  - `series[].z` — the **`z`** magnitudes, `number[]` (forward-compatible).

  These three parallel arrays are the transitional bridge to the future datum
  `{x: x[i], y: data[i], z: z[i]}`; when the point-model normalization lands, they
  fold into `data: [{x,y,z}, …]` (or `[[x,y,z], …]`) with **no change to the
  rendered bytes**, and the bare-number path keeps line/column goldens frozen
  (§3.3 Rank 3 byte-identity gate).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"bubble"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is a filled circle) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (generalized to render `x, y, z` per row — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | axis label |
| `xAxis.min` / `xAxis.max` | number | auto (nice ticks, **no** forced 0) | clamp the **numeric** x range; unlike a value axis the x-domain is **not** zero-anchored (`include_zero=False`) — a bubble with x∈[100,200] must not be dragged to 0 |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, **no** forced 0) | clamp the numeric y range; the free numeric y-axis is likewise **not** zero-anchored |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| **`sizeLegend`** | bool \| object | `false` | **NEW field.** `true` renders a **size legend** — a small stack of sample bubbles at bucketed z values (`zmin`, `zmid`, `zmax`) with numeric labels, so a reader can decode area→magnitude. An object form (`{buckets:int, title:string}`) is accepted forward-compatibly. Ignored by today's validator (unknown key) |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the **`y`** values, length `N` (see [Data shape](#data-shape)) |
| **`series[].x`** | number[] | index `0..N-1` | **the `x` values**, length `N`, aligned to `data` by index. Forward-compatible parallel array (folds into the `{x,y,z}` datum). Absent → `x = index` |
| **`series[].z`** | number[] | — | **the `z` magnitudes**, length `N`, aligned to `data` by index. Non-negative; drives the radius via the size-scale. Forward-compatible parallel array |
| `series[].color` | string \| gradient | palette by index | the **bubble fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills every circle; legend swatch + `data-color` use stop 0) |
| `series[].fillOpacity` | number | `0.65` (bubble default) | **overlap opacity** of the circle fill. Line's default is `0` (no area fill); bubble **reinterprets** this field as the circle fill-opacity and defaults it to a pinned `0.65` so overlapping bubbles read through one another. Set `1` for opaque bubbles |
| `series[].pattern` | object | — | hatch fill for the circle: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line spec but **inert** for bubble (no line to draw):
`lineWidth`, `dashStyle`, `step`, `curve` are accepted by the shared validator
(forward-compatible) but not consumed by the bubble marks. `marker.radius` is
**ignored** — the radius comes from the size-scale, not a fixed marker size (a
bubble whose radius did not encode `z` would be a broken bubble chart, NN#2).
Full schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** three aligned `number[]` arrays per series — `data` (`y`),
  `x`, and `z` — one triple `{x[i], y[i], z[i]}` per index `i`. This is the
  transitional form of the canonical `{x,y,z}` datum (see [Data shape](#data-shape)).
  A missing `x` array defaults to `x = index`; `z` is required for a genuine
  bubble (absent `z` degenerates every radius to the fixed `(RMIN+RMAX)/2`, i.e.
  a plain scatter).
- **Numeric x, numeric y — no zero-anchor.** Both axes are **free numeric** axes
  built by the shared value-axis routine with **`include_zero=False`**: the domain
  comes from the data only (`nice_ticks` over `min/max`), never forced through 0.
  This is scatter's rank-3 caveat (§3.2, §4.2) — carrying the column/bar/area
  y-baseline zero-anchor into a free x (or free y) would wrongly drag a bubble
  cluster at x∈[100,200] down to the origin. `xAxis.min/max` and `yAxis.min/max`
  clamp the respective domain when set.
- **z → radius (the size-scale).** The **only** net-new generalization. `z` maps
  to a circle radius `r ∈ [RMIN, RMAX]` by an **area-proportional** rule
  (`r ∝ sqrt(z)` so *area* ∝ z, the perceptually honest encoding). The reduction
  and formula are pinned below.
- **The frame owns the domains.** The marks call `fr.xpix`/`fr.ypix` only and read
  the size-scale from the frame; they **never** recompute an axis scale (NN, §7.1).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). It delegates with the
**numeric** x-scale (`x_scale="linear"`, landed by scatter) and
**`include_zero=False`** (free numeric x/y):

```python
# libs/python/peakcharts/charts/bubble.py
from ._cartesian import render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Bubble", "linear", _bubble_marks, include_zero=False)
```
```go
// libs/go/bubble.go — package peakcharts
func renderBubbleSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Bubble", "linear", bubbleMarks, false)
}
```

The marks callback first reduces the **global** z-domain (§ Size scale), then emits
**exactly one** `<g class="pk-series" data-series="{si}">` per series, and inside
it **one `<circle>` per point**:

```html
<g class="pk-series" data-series="0">
  <circle class="pk-bubble pk-point" data-series="0"
          data-series-name="Checkout API" data-x="30" data-y="120" data-z="5600"
          data-color="#2f7ed8" data-r="24.7" data-r-hover="24.7"
          cx="512.0" cy="188.0" r="24.7"
          fill="#2f7ed8" fill-opacity="0.65"/>
  … one .pk-bubble.pk-point per point …
</g>
```

- **Class:** `pk-bubble pk-point`. `pk-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `pk-bubble` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The circle **is** the hoverable point; there are no separate
  markers.
- **Geometry:** `cx = xpix(x)`, `cy = ypix(y)`, `r = size_scale(z)`. For a
  `<circle>` these are the native SVG attributes — `cx`/`cy`/`r` **are** the
  geometry, no separate `x`/`y`/`width`/`height`. Emit `cx`/`cy` via `:.1f`/`f1`;
  emit `r` via `fmt_num` (it is a scale output, like a radius, not a raw pixel
  coordinate).
- **Fill:** read `fr.styles[si].fill` — the resolved bubble paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a bubble unfilled.
- **Overlap opacity:** every circle carries `fill-opacity` = `series[].fillOpacity`
  when present, else the pinned default **`0.65`** — so overlapping bubbles read
  through one another. This is bubble's reinterpretation of `fillOpacity` (line's
  default `0` would make an *invisible* bubble field).
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (circle center x) — the
  crosshair reads it — and `cy` (center y). For a circle these coincide with the
  drawn center.
- **`data-z`:** the **new** datum attribute — the raw `z` magnitude via `fmt_num`.
  Alongside the inherited `data-x`/`data-y`, it lets the tooltip and data table
  show the full `(x, y, z)` triple.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — a filled circle swatch; do not renumber and do not emit a legend from
  the marks.

## Size scale — the pinned geometry

Evaluate the size-scale in **exactly this operation order** in both languages so
`%g`/`fmt_num` rounding of `r` lands identically. This is the **one** net-new
numeric transform bubble introduces (§3.2 "Size scale"; §3.3 Rank 4):

```
RMIN        = 4.0                                    # pinned constant (px radius)
RMAX        = 32.0                                   # pinned constant (px radius)

# 1. Global z-domain — reduce over EVERY point of EVERY series, in series-index
#    order then point order. One domain for the whole chart (bubbles comparable).
zmin        = min(z over all points, all series)
zmax        = max(z over all points, all series)

# 2. Degenerate rule — pinned identically, evaluated BEFORE any division.
def size_scale(z):
    if zmax <= zmin:                                 # all-equal z, or a single point
        return (RMIN + RMAX) / 2                     # fixed radius — NEVER divide 0/0
    t = clamp01((z - zmin) / (zmax - zmin))          # clamp to [0,1] BEFORE sqrt
    return RMIN + (RMAX - RMIN) * sqrt(t)            # area-proportional (r ∝ sqrt(z))

clamp01(v)  = max(0.0, min(1.0, v))
```

- **`RMIN = 4.0` / `RMAX = 32.0` are fixed constants**, not per-author choices
  (analogous to column's `PAD = 0.2`). Pinning them makes every radius reproducible
  across languages.
- **`r ∝ sqrt(z)` gives area ∝ z** — the honest magnitude encoding (a bubble with
  twice the `z` has twice the *area*, not twice the radius). This is why the `sqrt`
  is inside the formula and the domain must be `≥ 0` before it runs.
- **Degenerate domain (`zmax <= zmin`)** — all-equal `z`, a single point, or an
  absent `z` array — returns the **fixed** `(RMIN+RMAX)/2 = 18.0`. This is the
  pinned rule that must fire **before** the divide: a raw `0/0` is a
  `ZeroDivisionError` in Python and `NaN` in Go — the two languages would diverge.
- **`clamp01` before `sqrt`** — clamp the ratio into `[0,1]` **first**, so `sqrt`
  never receives a negative (Python `math.sqrt(neg)` raises; Go `math.Sqrt(neg)`
  yields `NaN`). Clamping also keeps a `z` outside the data domain (if a future
  spec supplies an explicit `zMin`/`zMax`) pinned to the endpoint radius.
- **`sqrt` is IEEE-754 identical** (`math.sqrt` / `math.Sqrt`) **only once the
  domain is guaranteed `≥ 0`** — hence the clamp precedes it.

This is covered by a **bubble edge-case parity test** (analogous to
`test_spline_edge_cases`): all-equal `z` (e.g. `z=[5,5,5]`), a single point, and
`z` at/below/above the domain — each asserts a **finite** radius and **Py == Go**
(§3.3 Rank 4; §7 gauntlet).

## Size legend — the optional z-decoder

When `sizeLegend` is truthy the shared tail (or a bubble-supplied legend hook)
renders a small stack of **sample bubbles** at bucketed z values so a reader can
decode area→magnitude:

- **Buckets:** by default three — `zmin`, `zmid = (zmin+zmax)/2`, `zmax` — each
  drawn as a circle of radius `size_scale(bucket)` with a `fmt_num(bucket)` label.
  `sizeLegend.buckets` overrides the count forward-compatibly.
- **Placement:** inside the plot area (top-left or bottom-right corner), nested or
  stacked, using the theme's legend text color. It is chrome — parity-locked
  formatting (`fmt_num` for labels, `:.1f`/`f1` for circle coords) applies.
- The size legend is **independent** of the series legend (`legend`): the series
  legend maps color→series; the size legend maps area→z.

## Reused chrome (obtained from the frame — never re-implemented)

Bubble inherits, with **zero** re-implementation (§3.1, §4.2), everything scatter
already reuses plus scatter's own net-new axis:

- Plot area + margins; x/y axes + axis lines + axis titles.
- **Numeric x-axis** (scatter's rank-3 net-new) — `nice_ticks` + x tick labels +
  vertical gridlines + `xpix` from a **value** (`x_scale="linear"`); reused verbatim.
- Linear **numeric** y-scale via `nice_ticks` → `ypix`, **both** built with
  `include_zero=False`; y gridlines + labels.
- Titles + subtitle; legend (bottom-center); crosshair (two-axis for the free x/y).
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (generalized for the `{x,y,z}` point model — §5.4b-DT) + keyboard nav.
  Responsive `<svg>` viewBox; the shared JS runtime.
- The **point model** (`{x,y}` normalization) from scatter — bubble extends it with
  `z` only.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="linear"` and `include_zero=False`. It passes the
bare noun **`"Bubble"`** — the frame expands it to `"Bubble chart with N series…"`
byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Size-scale ORDER** — evaluate the size-scale exactly as pinned: reduce the
  **global** `zmin`/`zmax` first (series-index order then point order), check
  `zmax <= zmin` **before** any divide, `clamp01` **before** `sqrt`. A reassociated
  ratio or an early `sqrt` diverges after `fmt_num`.
- **Degenerate z-domain** — all-equal `z` / single point / absent `z` must return
  the fixed `(RMIN+RMAX)/2`; a raw `0/0` is a `ZeroDivisionError` (Python) vs `NaN`
  (Go). Pin the rule identically **before** the divide (§3.2, §3.3 Rank 4).
- **`include_zero=False` on BOTH axes** — bubble passes `False`; carrying line's /
  column's zero-anchor into the free x **or** y domain wrongly re-anchors the
  cluster at 0. Both languages would be wrong identically and still pass byte-parity
  — so the flag must be explicit (§3.2 caveat, §4.2, §7 gauntlet #7).
- **z-domain scope** — reduce `zmin`/`zmax` **globally** across all series (not
  per-series), so a given `z` maps to the same radius everywhere; a per-series
  reduction would make bubbles non-comparable and is a defect.
- **Bubble-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field. Never emit an unfilled bubble.
- **`fillOpacity` default** — bubble's default is **`0.65`**, not line's `0`; emit
  the `fill-opacity` attribute identically in both languages (absent field → the
  pinned `0.65`).
- **Formatters** — `cx,cy` via `:.1f`/`f1`; `r`, `data-z`, `data-y`, `data-x`
  (numeric) via `fmt_num`/`fmtNum`; every user string via `esc`. A leaked raw `<`
  fails the XSS tests.
- **Radius format** — `r` and `data-r`/`data-r-hover` go through `fmt_num` (scale
  outputs, like a radius), **not** `:.1f`; keep both `data-r` and `data-r-hover`
  present even though a bubble does not grow on hover (`data-r-hover == data-r`).
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep series/point/legend
  `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the selectors
+ `data-*` below (`spec/svg-contract.md`). Emit them correctly and tooltip,
highlight, crosshair, legend-toggle, and keyboard nav all work with **zero JS
changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its points, and the legend
  item (do not renumber).
- **Datum mark:** `.pk-point` (here also `.pk-bubble`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, **`data-z`**, `data-color`,
  `data-r`, `data-r-hover` — `data-z` is the new bubble attribute; the tooltip shows
  the full `(x, y, z)` triple.
- **Crosshair anchor:** every `.pk-point` carries `cx` and `cy` (the circle center).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(fmt_num(x))`; `data-y = esc(fmt_num(y))`;
  `data-z = esc(fmt_num(z))`; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(r)`. Center coords use `:.1f`/`f1`.
- **A11y default-on + data-table generalization (§5.4b-DT):** bubble's `data` stops
  being a plain `number[]` (each row is an `{x,y,z}` triple), so the shared
  **visually-hidden data table** MUST be generalized — in lockstep in both
  languages — to render `x`, `y`, and `z` per row (not a single coerced number),
  with a Py==Go table-bytes test. Shipping the old `number[]` table would
  misrepresent the data and is an a11y non-negotiable failure (NN#4). `a11y:false`
  restores the pre-a11y bytes. Keyboard nav walks the bubbles.
- **Static-first:** the chart is fully readable with JS disabled — bubbles are
  server-rendered, filled, and sized; the crosshair ships `display:none`; the
  tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "bubble",
  "title": "Endpoint Latency vs Payload",
  "subtitle": "Bubble area = requests per minute",
  "xAxis": { "title": "Payload size (KB)" },
  "yAxis": { "title": "p95 latency (ms)" },
  "sizeLegend": true,
  "series": [
    {
      "name": "Checkout API",
      "x":    [2, 8, 15, 30, 55, 90],
      "data": [45, 62, 78, 120, 180, 260],
      "z":    [1200, 3400, 800, 5600, 2100, 900]
    }
  ]
}
```

`data` is the `y` array; `x` and `z` are the forward-compatible parallel arrays
(see [Data shape](#data-shape)). The spec passes `validate() == []` today and folds
into the `{x,y,z}` datum with no byte change when the point model lands.

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, numeric x/y, `z → radius`, `sizeLegend`, default overlap opacity |
| [`examples/multi-series.json`](examples/multi-series.json) | 3 series, **global** z-domain comparability, `fillOpacity` overlap density |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a gradient bubble fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) + `sizeLegend` |
| [`examples/uniform-z.json`](examples/uniform-z.json) | all-equal `z` → the **degenerate size-domain** fixed radius `(RMIN+RMAX)/2`; also clamps `xAxis`/`yAxis` |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted string field
(series name, custom bubble color) so the XSS tests run against the bubble marks
(§5.5d). `BUBBLE_CASES = ["basic","multi-series","themed-dark","uniform-z","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/bubble/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="bubble",
    title="Endpoint Latency vs Payload",
    x_axis=Axis(title="Payload size (KB)"),
    y_axis=Axis(title="p95 latency (ms)"),
    series=[
        Series("Checkout API", [45, 62, 78, 120, 180, 260],
               x=[2, 8, 15, 30, 55, 90], z=[1200, 3400, 800, 5600, 2100, 900]),
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
- **Hover a bubble** → tooltip (x, y, z, series) + bubble highlight (halo) + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the bubbles; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — bubbles filled and sized.

## Rendering notes

- **Both** axes use "nice numbers" ticks (~6) over the **data** domain with
  `include_zero=False` — the free numeric x/y is **not** zero-anchored (a bubble
  cluster at x∈[100,200] stays there). `xAxis.min/max` and `yAxis.min/max` clamp
  the respective domain.
- Radius comes from the **size-scale** of `z` (area-proportional, `r ∝ sqrt(z)`),
  never from `marker.radius` (ignored). The z-domain is **global** across all series.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole bubble via the `<defs>` pre-pass.
- Bubbles are semi-transparent (`fill-opacity` default `0.65`) so overlaps read as
  density; set `fillOpacity:1` for opaque bubbles.
- Bubble reuses the **exact** substrate scatter extended — it forks **nothing**;
  its only net-new is the size-scale + optional size legend.

## Not yet supported (roadmap)

- Live renderers (`bubble.py` / `bubble.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Bubble lands **after**
  scatter (rank 3) supplies the numeric-x-axis + point model it reuses.
- The `{x,y,z}` datum in `data` (objects / positional `[x,y,z]`) — accepted once the
  point-model normalization + validator update land (§3.3 Rank 3); until then the
  parallel-array transitional form is used.
- **3D bubble**, explicit `zMin`/`zMax` domain override, per-series size-scale, and
  a categorical x variant — variants layered on this base.
</content>
</invoke>
