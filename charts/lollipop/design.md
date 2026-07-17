# Chart: Lollipop (`lollipop`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file mirrors the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which copies
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> lollipop-specific build detail: the stem+head mark composition, the reused
> band layout, the reused marker symbols, the orientation subtype, the parity
> traps, and the a11y DOM contract.

- **Chart id:** `lollipop`
- **Spec `type`:** `"lollipop"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Composition sibling** (rides
  Column's band-layout + Line's marker — introduces **no** new generalization,
  only a new mark composition; not in the rank 1–13 core sweep) · **Src:** HC
  (highcharts-more)
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; lollipop rides the shared cartesian frame
  once extraction lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2
  Family A "Lollipop", §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/lollipop.py` · `libs/go/lollipop.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A lollipop chart: one or more series drawn as a **thin stem `<line>` rising from
the baseline** to each value, **capped with a marker `<circle>` (the "head")** at
the value. It is a column chart with the bar's ink stripped down to a stem and a
dot — the same categorical x-axis, the same numeric y-axis, the same
baseline-anchored geometry, but far less ink per datum. The **head** is the
hoverable, interactive element (it plays the role column gives to the bar and
line gives to the point marker).

Lollipop is a **composition sibling**: it is built once **Column** (band-layout,
the value-axis baseline `ypix(0)`) and **Line** (the four marker symbols) exist,
and it composes those two already-shipped primitives into a new mark. It forces
**no** new generalization — no new scale, no new transform, no new point model.
Its only new spec field is the **`orientation`** subtype selector (vertical /
horizontal), which reuses Bar's orientation-transpose concept.

## Use it when

- Your x is a set of **discrete categories** (endpoints, services, queries,
  hosts) and your y is a **count or magnitude** you want to compare *across*
  those categories, **and the story is the endpoints, not the volume of ink** —
  a lollipop reads cleaner than a column when there are many categories or the
  bars would be near-full-height and visually heavy.
- You want a **ranking** (sort categories by value and read top-to-bottom) — the
  `horizontal` subtype is the classic ranked-bar-lite.
- You want to **compare a few series** within each category (grouped side-by-side
  stems, each with its own marker symbol).
- Rows look like: `label -> value` (one stem) or `label -> value_a, value_b`
  (several series sharing one x).

Do **not** use it for: a **trend** over ordered/continuous x (use `line-basic`),
**part-to-whole of a single total** (use pie/donut), a **distribution** of raw
samples (use `histogram`), or **x/y correlation** with no shared category
ordering (use `scatter`). If the magnitude/area *is* the message, prefer
`column`. See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers, aligned to `categories` by index.
- **Identical value payload to `column` and `line`** (`data: number[]`) — one y
  per category. Grouped is a band-layout selection, not a different data shape. A
  bare `number` stays valid (x = index), so line/column/lollipop goldens never
  move when the point model lands (§3.2 point-model, §3.3 Rank 3).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"lollipop"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the shared tail's `<rect>`, tinted with the series color) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`orientation`** | string | `"vertical"` | **NEW field.** `"vertical"` = stems rise from the baseline up the y value-axis (categories on x); `"horizontal"` = stems run from the baseline along the x value-axis (categories on y) — the ranked-bar-lite subtype, which rides Bar's orientation-transpose (§3.2 orientation). Added in the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) |
| **`grouping`** | bool | true | **REUSED from `column`.** When a chart has multiple series: `true` → `K = len(series)` side-by-side sub-band stems per category (the pinned band layout); `false` → `K = 1`, all series' stems share one centered slot (overlaid, drawn in series order). Single-series ⇒ `K = 1` ⇒ one centered stem regardless |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories; on the y-axis when `orientation:"horizontal"`) |
| `yAxis.title` | string | — | axis label (the value-axis label) |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the value range; the value axis always includes 0 (the stem baseline) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | value-axis gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | stem/head values, length `N` (negatives allowed → the stem drops below the baseline and the head sits below it) |
| `series[].color` | string \| gradient | palette by index | the **stem + head color**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object. Stem stroke uses the gradient `url(#grad)`; the head fill + legend swatch + `data-color` use stop 0's solid (exactly line's stroke/marker split) |
| `series[].lineWidth` | number | 2 | **stem thickness** (px) — reused from line's line width; the stem `<line>` `stroke-width` |
| `series[].dashStyle` | string | solid | **stem dash**: solid/dashed/dotted — reused from line |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:3.5}` | **the lollipop head** — reused verbatim from line's marker: `symbol` ∈ circle/square/triangle/diamond, `radius` sizes the head. Authors typically bump `radius` (≈5–6) for a prominent head. `enabled:false` yields a bare stem (rare) |
| `series[].pattern` | object | — | hatch fill; accepted by the shared validator but inert for lollipop (there is no filled area/rect to hatch) |

Fields carried over from the line/column spec but **inert** for lollipop:
`fillOpacity`, `step`, `curve`, `stacking`, `pattern` are accepted by the shared
validator (forward-compatible) but not consumed by the lollipop marks — a stem is
baseline-anchored, not a cumulative offset, so `stacking` does not apply (see
Data model). Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — one y per category, the same
  shape column and line use. No `{x,y}` object model (that arrives with scatter,
  rank 3).
- **Single series (`K = 1`):** each category slot holds **one centered stem** at
  the band center `xpix(i)`, with its head at `ypix(value)`.
- **Grouped (`grouping:true`, default when multi-series):** each category slot is
  split into `K = len(series)` equal sub-bands; series `k`'s stem sits at the
  **center of sub-band `k`** — `stemX(i,k) = left(i,k) + barW/2` (band layout
  below). Each series head carries its own marker symbol so grouped stems are
  distinguishable.
- **Overlaid (`grouping:false`):** `K = 1`, all series' stems share the one
  centered slot, drawn in series index order (heads may coincide — later series
  on top).
- **No stacking.** A stem is anchored to the value-axis baseline `ypix(0)`, not to
  a cumulative offset, so there is no meaningful "stacked lollipop". The frame's
  `stacking` field is inert here; the value-axis y-domain is the ordinary
  `nice_ticks` over the data with 0 forced in (`include_zero=True`) — **the frame
  owns it**, the marks never recompute a scale.
- **The frame owns the value-axis domain.** `ypix` and `ypix(0.0)` (the baseline)
  come from the shared frame with `include_zero=True`; the marks call `fr.ypix`
  only.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2):

```python
# libs/python/stonecharts/charts/lollipop.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Lollipop", "band", _lollipop_marks)   # include_zero defaults True
```
```go
// libs/go/lollipop.go — package stonecharts
func renderLollipopSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Lollipop", "band", lollipopMarks, true)
}
```

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series. Inside it, to keep every head above every stem, it emits **all stems
first, then all heads** (mirroring line's path-then-markers order):

```html
<g class="sc-series" data-series="0">
  <!-- stems: one baseline-anchored <line> per category -->
  <line class="sc-stem" data-series="0"
        x1="128.4" y1="336.0" x2="128.4" y2="96.0"
        stroke="#2f7ed8" stroke-width="2"/>
  … one .sc-stem per category …
  <!-- heads: one .sc-point marker per category (the hoverable element) -->
  <circle class="sc-point sc-lollipop-head" data-series="0"
          data-series-name="p99" data-x="/checkout" data-y="42"
          data-color="#2f7ed8" data-r="5" data-r-hover="7.5"
          cx="128.4" cy="96.0" r="5" fill="#2f7ed8" stroke="#ffffff" stroke-width="1"/>
  … one .sc-point per category …
</g>
```

- **Two marks per datum, one hoverable.** The **head** carries `class="sc-point"`
  — it is the **contract** element the runtime keys on (tooltip / highlight /
  crosshair / legend-toggle). The **stem** carries `class="sc-stem"` (a
  purely-cosmetic CSS hook), and `sc-lollipop-head` on the head is likewise a
  cosmetic add — adding a class the runtime must *know about* is out of scope
  (NN#5, §5.3). Both marks sit inside the same `.sc-series[data-series=N]` group,
  so the legend toggle hides stem **and** head together.
- **Head geometry:** the head is line's marker, drawn by the reused
  `_marker`/`markerSVG` helper at `(stemX, ypix(value))` with radius
  `marker.radius`. All four symbols (circle/square/triangle/diamond) are
  supported verbatim; non-circle heads still carry `cx`/`cy` so the crosshair
  works (line's marker already does this).
- **Stem geometry (vertical):** `stemX = left(i,k) + barW/2` (band layout below);
  the stem runs `y1 = fr.ypix(0.0)` (baseline) to `y2 = fr.ypix(value)`. This is
  correct for **any sign** with **no flip** — a negative value simply gives
  `ypix(value) > ypix(0.0)` so the line points downward and the head lands below
  the baseline. (Unlike column, there is no rect whose `y`/`height` must be
  flipped around the baseline — a genuine simplification.)
- **Stem geometry (horizontal, `orientation:"horizontal"`):** the value axis is x
  and the band axis is y — `x1 = fr.xpix(0.0)` (value baseline) to
  `x2 = fr.xpix(value)`, both at `y = stemY(i,k)`; head at `(xpix(value), stemY)`.
  This rides Bar's orientation-transpose (a coordinate remap only — §3.2).
- **Color:** read `fr.styles[si].stroke` for the **stem** stroke (hex or
  `url(#grad)`) and `fr.styles[si].solid` for the **head** fill / `data-color` /
  legend swatch — **exactly line's stroke/marker split.** Never read
  `fr.styles[si].fill` (that is column's bar paint — a lollipop has no filled
  rect) and never read `area_fill` (line's under-fill). The head halo stroke is
  `theme.marker_halo`, as line's marker.
- **`cx` / `cy`:** every `.sc-point` head MUST carry `cx` (stem x) — the crosshair
  reads it — and by convention `cy` (head y). Without `cx` the crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (copied VERBATIM from the blueprint)

Lollipop reuses **Column's** band layout unchanged. Evaluate the arithmetic in
**exactly this operation order** in both languages so `f1` / `:.1f` rounding lands
ULP-for-ULP identically (blueprint §3.2 / §4; the frame's `xpix` implements the
band center, the marks build the sub-bands and place the stem at the sub-band
center):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
barW        = groupW / K
left(i,k)   = xpix(i) - groupW/2 + barW*k
stemX(i,k)  = left(i,k) + barW/2                      # stem sits at the sub-band CENTER
```

- Basic single-series ⇒ `K = 1` ⇒ `barW = groupW` ⇒ `stemX(i,0) = xpix(i)` (one
  centered stem at the band center).
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author
  choices. `grouping:false` forces `K = 1` (overlaid). Lollipop has no `stacking`
  slot collapse — it is always the grouped band layout (or `K=1`).
- For `orientation:"horizontal"` the identical arithmetic runs on the **y** band
  axis (`plot_h`, `n` categories down the side), producing `stemY(i,k)`; the value
  runs along x. Orientation is a coordinate remap only — same `f1` arithmetic.

## Reused chrome (obtained from the frame — never re-implemented)

Lollipop inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear value-axis via `nice_ticks` → `ypix` (with 0 forced in for the
  baseline); value-axis gridlines + labels.
- Categorical band axis via the **band** `xpix`; the shared x-label loop lands
  labels under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle`
  (`stroke`/`solid`), id-scoping via `cid` (defs emitted only when a series needs
  them — no empty `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- The reused **marker** helper (`_marker`/`markerSVG`) for the head, and the
  reused **band layout** for the stem x — both already parity-locked by column
  and line.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=True` (value axis /
baseline). It passes the bare noun **`"Lollipop"`** — the frame expands it to
`"Lollipop chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Band arithmetic ORDER** — evaluate the eight lines above in that exact order;
  a reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1` rounding.
  Reuse Column's helper — do **not** re-derive it.
- **Frame owns the value-domain** — the marks must call `fr.ypix`/`fr.xpix` only;
  recomputing a scale (even to identical bytes) is a defect (NN, §7.1).
- **Stem baseline** — anchor the stem to `fr.ypix(0.0)` (vertical) /
  `fr.xpix(0.0)` (horizontal); never recompute a baseline (the value axis already
  forced 0 into the domain).
- **Read the LINE fields, not the COLUMN field** — stem = `fr.styles[si].stroke`,
  head = `fr.styles[si].solid`. Reading `fill` (column's bar paint) or `area_fill`
  (line's under-fill) is the wrong field and drops the gradient/solid split.
- **Negatives need NO flip** — a value below 0 draws a downward stem and a head
  below the baseline naturally; do **not** copy column's `y`/`height` flip logic
  (there is no rect).
- **Emission order = stems then heads** — emit all `.sc-stem` lines, then all
  `.sc-point` heads, inside each series group, so heads render above stems
  identically in both languages.
- **`data-y` carries the raw value** — the head's `data-y = esc(fmt_num(value))`,
  the datum's own value (there is no cumulative total to confuse it with).
- **Formatters** — `x1,y1,x2,y2,cx,cy,x,y,width,height` and marker points via
  `:.1f`/`f1`; `data-y`, radii via `fmt_num`/`fmtNum`; every user string via
  `esc`. A leaked raw `<` fails the XSS tests.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep
  series/stem/head/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.sc-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its stems, its heads, and
  the legend item (do not renumber). The legend toggle hides the whole group —
  stem and head together.
- **Datum mark:** the **head** `.sc-point` (here also `.sc-lollipop-head`) carries
  **all** of `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`,
  `data-r`, `data-r-hover`. The stem `.sc-stem` is decorative and carries only
  `data-series` (so it hides with the series) — it is **not** a `.sc-point`.
- **Crosshair anchor:** every `.sc-point` head carries a `cx` (stem x) and by
  convention `cy` (head y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` (the raw datum value);
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`.
  Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks the
  heads. `a11y:false` restores the pre-a11y bytes. Lollipop keeps `data: number[]`,
  so the existing `number[]` data table renders faithfully with **no**
  generalization (that obligation applies only when the data element type
  changes — §5.4b-DT).
- **Static-first:** the chart is fully readable with JS disabled — stems and heads
  are server-rendered and colored; the crosshair ships `display:none`; the tooltip
  is JS-only.

## Example spec

See [`examples/grouped.json`](examples/grouped.json):

```json
{
  "type": "lollipop",
  "title": "Error Rate by Service",
  "subtitle": "This week vs last week, grouped lollipops",
  "grouping": true,
  "xAxis": { "title": "Service", "categories": ["auth", "cart", "search", "checkout", "billing"] },
  "yAxis": { "title": "Errors per 1k requests" },
  "series": [
    { "name": "Last week", "data": [4.2, 6.8, 3.1, 9.4, 2.7], "marker": { "symbol": "circle",  "radius": 5 } },
    { "name": "This week", "data": [3.6, 5.1, 3.4, 7.2, 2.2], "marker": { "symbol": "diamond", "radius": 5 } }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered stems, circle heads, baseline anchor |
| [`examples/grouped.json`](examples/grouped.json) | 2 series side-by-side, `grouping:true`, band sub-slots, distinct marker symbols per series head |
| [`examples/horizontal.json`](examples/horizontal.json) | `orientation:"horizontal"` ranked subtype, custom stem `lineWidth`, larger heads |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a gradient stem/head (`defs` pre-pass → stem `url(#grad)`, head solid = stop 0) + square heads + a negative value |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom head/stem color) so the XSS tests run against
the lollipop marks (§5.5d).
`LOLLIPOP_CASES = ["basic","grouped","horizontal","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/lollipop/examples/grouped.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Marker, Series, save_html
save_html(ChartSpec(
    type="lollipop",
    title="Error Rate by Service",
    x_axis=Axis(title="Service", categories=["auth", "cart", "search", "checkout", "billing"]),
    y_axis=Axis(title="Errors per 1k requests"),
    series=[
        Series("Last week", [4.2, 6.8, 3.1, 9.4, 2.7], marker=Marker(symbol="circle",  radius=5)),
        Series("This week", [3.6, 5.1, 3.4, 7.2, 2.2], marker=Marker(symbol="diamond", radius=5)),
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
- **Hover a head** → tooltip (x, series, y) + head highlight + crosshair.
- **Click a legend item** → toggle that series on/off (stem **and** head hide).
- **Keyboard** → arrows walk the heads; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — stems and heads colored
  and readable.

## Rendering notes

- The value axis uses "nice numbers" ticks (~6) and always includes 0 as the stem
  baseline unless `yAxis.min/max` clamp it.
- Stems use the **band** x-scale (`x_scale="band"`) — categories occupy equal
  bands; labels land under band centers. Grouped series split each band into `K`
  equal sub-slots.
- The head reuses line's four marker symbols; set `series[].marker.symbol` to
  distinguish grouped series, and `series[].marker.radius` to size the head.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient color paints the stem via the `<defs>` pre-pass while the head/legend
  use stop 0's solid.
- Lollipop adds **no** new generalization — it composes Column's band-layout and
  Line's marker, so it is one of the cheapest siblings once both exist.

## Not yet supported (roadmap)

- Live renderers (`lollipop.py` / `lollipop.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **Dumbbell** (two heads + connecting bar, `{low,high}` range model) — the
  adjacent sibling; lollipop is the single-head, baseline-anchored case.
- Segmented / "sparkline" lollipops, per-head data labels, connector-to-axis
  guides, and rotated x-labels — variants layered on this base.
