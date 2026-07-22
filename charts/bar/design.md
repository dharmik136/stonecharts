# Chart: Bar (`bar`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this recipe copies the
> Cartesian exemplar [`charts/column/design.md`](../column/design.md) (itself
> modeled on [`charts/line-basic/design.md`](../line-basic/design.md)) and adds
> the one thing that makes `bar` its own chart: the **orientation transpose**.
> Bar is column with the value axis on **x** and the category (band) axis on
> **y** — the same data model, the same stacking/grouping, the same chrome, the
> same parity paths, only the axis roles swapped at draw time.

- **Chart id:** `bar`
- **Spec `type`:** `"bar"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 2** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; bar rides the shared cartesian frame — the
  same frame column uses — once its orientation parameter lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3
  Rank 2, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/bar.py` · `libs/go/bar.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A bar chart: one or more series drawn as **horizontal, baseline-anchored bars**.
The value runs **along x** (the numeric value axis) so each bar's **width**
encodes its magnitude; the categories run **down y** (the discrete band axis).
It is the [`column`](../column/design.md) chart rotated a quarter turn — bars are
still the hoverable, interactive elements (they replace the line chart's point
markers), and grouped / stacked / percent-stacked variants are identical to
column's, just laid on their side.

Bar is **build rank 2** — the second non-line Cartesian sibling. It forces
exactly **one** new generalization: **orientation**. Column already extracted the
shared chrome, the band-layout, the stacking transform, the frame-owned
stacking-aware value-domain, and the rect-mark + `SeriesStyle.fill` bar-paint
primitive (§4, §3.3 Rank 1). Bar reuses **all** of it and adds only a coordinate
remap: put the band axis on y and the value axis on x. Parity is therefore
**free** — a transpose changes no arithmetic, only which pixel each number maps
to (§3.3 Rank 2).

## The one idea: orientation (bar = column transposed)

**Author a bar spec exactly like a column spec.** The spec fields keep their
column meanings — `xAxis.categories` still holds the categories, `xAxis.title`
still titles the category axis, `yAxis` (`title`/`min`/`max`/`gridLine`) still
configures the **value** axis. The transpose is a **rendering** remap, not a spec
rewrite: change `type:"column"` → `type:"bar"` on the *same* spec and it renders
rotated. This is what "one renderer parameterized by orientation, not a fork"
means — bar delegates to the same shared frame column uses and flips a single
`orientation` flag.

Under `orientation="horizontal"` the frame swaps two things and nothing else:

| Role | Column (`vertical`) | Bar (`horizontal`) |
|------|---------------------|--------------------|
| **Band / category axis** | x — band centers via `xpix(i)`, category labels along the bottom | **y** — band centers via `ypix_band(i)`, category labels down the **left** |
| **Value axis** | y — `nice_ticks`→`ypix(v)`, value labels at left, **horizontal** gridlines | **x** — `nice_ticks`→`xpix_val(v)`, value labels along the **bottom**, **vertical** gridlines |
| **Bar grows** | up/down from the baseline `ypix(0)` (encodes **height**) | left/right from the baseline `xpix_val(0)` (encodes **width**) |

Everything else — titles, subtitle, legend, crosshair, themes, `<defs>` pre-pass,
a11y, the runtime — is **identical** and inherited unchanged. `nice_ticks`,
`fmt_num`, `esc`, `:.1f`/`f1` are the same parity-locked routines, applied to a
different axis. Legend/tooltip/a11y are unchanged (§3.3 Rank 2 parity note).

## Use it when

- Your independent variable is a set of **discrete categories** (services,
  endpoints, regions, teams) and you want to **compare a value across** them —
  especially when the category **labels are long** (endpoint paths, service
  names) and read better horizontally, or when you are showing a **ranking**
  (sort the categories by value).
- You want to **compare a few series** within each category (grouped), or show
  **composition** within each category (stacked / percent-stacked).
- Rows look like: `label -> value` (one bar) or `label -> value_a, value_b`
  (several series sharing one category).

Prefer `bar` over `column` when labels are long or you are ranking; prefer
`column` when x is naturally horizontal (time buckets, ordered stages).

Do **not** use it for: a **trend** over ordered/continuous x (use `line-basic`),
**x/y correlation** with no shared category ordering (use `scatter`),
**part-to-whole of a single total** (use pie/donut), or a **distribution** of raw
samples (use `histogram`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the category labels, length `N` (absent → index `0..N-1`).
  These render **down the y-axis** under `bar`, but they are still authored under
  `xAxis` — same field as column.
- each `series[].data`: `N` numbers, aligned to `categories` by index.
- Identical value payload to `column`/`line` (`data: number[]`) —
  grouped/stacked/percent are **transforms over these values**, selected by the
  chart-level `stacking` (+ `grouping`) fields, not a different data shape. A bare
  `number` stays valid (category = index), so line/column/bar goldens never move
  when the richer point model lands (§3.2 Point model, §3.3 Rank 3).

## Spec fields

Identical to [`column`](../column/design.md) — bar adds **no new spec field**
(orientation is a renderer parameter fixed by `type:"bar"`, not an author knob).

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"bar"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the bar `<rect>`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`stacking`** | string | — (grouped) | `null`/absent = grouped bars side-by-side; `"normal"` = bars stacked cumulatively **along x**; `"percent"` = stacked then normalized so each category totals 100%. The **frame** owns the resulting stacking-aware **value-domain** (max category **total**, not per-datum max). Same field, both validators, both spec models (§5.4b) — shared with column/area |
| **`grouping`** | bool | true | Only meaningful when `stacking` is absent: `true` → `K = len(series)` side-by-side sub-bands **stacked down y within each category**; `false` → `K = 1`, all series share one centered slot (overlaid, drawn in series order). When `stacking` is set, grouping is ignored (a stack occupies one slot) |
| `xAxis.title` | string | — | **category-axis** label (renders beside the left/y axis under bar) |
| `xAxis.categories` | string[] | index `0..N-1` | category labels (the band categories) — render **down y** |
| `yAxis.title` | string | — | **value-axis** label (renders under the bottom/x axis under bar) |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the value range; the value axis always includes 0 (the bar baseline) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | value gridline styling (renders as **vertical** lines under bar); `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | bar values, length `N` (negatives allowed → bars extend left of the baseline) |
| `series[].color` | string \| gradient | palette by index | the **bar fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole bar; legend swatch uses stop 0). For a horizontal bar a **left→right** gradient (`x1:0,y1:0,x2:1,y2:0`) reads most naturally |
| `series[].pattern` | object | — | hatch fill for the bar: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line spec but **inert** for bar (no line to draw):
`fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`, `marker` are accepted
by the shared validator (forward-compatible) but not consumed by the bar marks.
Full schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

Identical to column, with the **category axis on y** and the **value axis on x**:

- **Value payload:** `series[].data` is `number[]` — one value per category, the
  same shape line/column use. No `{x,y}` object model (that arrives with scatter,
  rank 3).
- **Grouped (default, `stacking` absent):** each category slot (a horizontal band)
  is split into `K = len(series)` equal sub-bands **stacked top-to-bottom**;
  series `k`'s bar sits in sub-band `k`. Basic single-series ⇒ `K = 1` ⇒ one
  centered bar of thickness `groupH`.
- **Stacked (`stacking: "normal"`):** one slot of thickness `groupH` per category;
  series segments accumulate on a cumulative baseline **along x** — segment `k`'s
  left edge is the running total through series `k-1`, its right edge the total
  through `k`.
- **Percent (`stacking: "percent"`):** stacked, then each segment is normalized by
  its category total so every category fills 0–100% of the x-axis.
- **The frame owns the value-domain.** For stacked/percent the value-max is the
  **max category total** (cumulative in the pinned summation order, §4), **not**
  the per-datum max — the marks never recompute a scale. For grouped it is the
  usual `nice_ticks` over the data with 0 forced in (`include_zero=True`). This is
  the *same* frame-owned domain column computes; orientation only changes that it
  drives `xpix_val` instead of `ypix`.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). The single difference from
column is the `orientation="horizontal"` argument threaded through the frame — the
rank-2 net-new. Column/line pass `orientation="vertical"` (the default) and stay
byte-identical:

```python
# libs/python/stonecharts/charts/bar.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    # noun="Bar", band scale, include_zero=True (value axis), orientation="horizontal"
    return render_cartesian(spec, "Bar", "band", _bar_marks, orientation="horizontal")
```
```go
// libs/go/bar.go — package stonecharts
func renderBarSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Bar", "band", barMarks, true, "horizontal")
}
```

> **Orientation is a frame parameter, added once (rank 2).** `render_cartesian` /
> `renderCartesian` and `build_frame` gain an `orientation ∈ {"vertical","horizontal"}`
> argument (default `"vertical"`). Under `"horizontal"` the frame routes the
> **band** scale to y (`band_width()` → `plot_h/n`, band center on y) and the
> **value** axis (`nice_ticks`/`include_zero`) to x, and the chrome head/tail draws
> category labels down the left and value ticks + **vertical** gridlines along the
> bottom. Because `"vertical"` reproduces the current column/line code path
> exactly, **all existing line and column goldens are byte-unchanged** after
> orientation lands (Gate A/C — the vertical path is the identity). Ideally
> column and bar share **one** parameterized marks routine; where they differ is
> only the final rect write (which pair of coordinates is band vs value).

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series, and inside it **one baseline-anchored `<rect>` per (category, series)**:

```html
<g class="sc-series" data-series="0">
  <rect class="sc-bar sc-point" data-series="0"
        data-series-name="Requests" data-x="/api/login" data-y="182"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="512.0" cy="96.0" x="72.0" y="80.0" width="440.0" height="32.0"
        fill="#2f7ed8"/>
  … one .sc-bar.sc-point per category …
</g>
```

- **Class:** `sc-bar sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `sc-bar` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The bar **is** the hoverable point; there are no separate markers.
- **Geometry (grouped).** Let `xval(v)` be the value-axis pixel on x
  (frame `xpix_val`, the value axis with `include_zero=True`) and the band layout
  below give the y-slot. The band (thickness) dimension is y; the value (length)
  dimension is x:
  - `y = top(i,k)`, `height = barH` (from the band layout).
  - Baseline-anchored along x: for a **positive** value `x = xval(0.0)` and
    `width = xval(value) - xval(0.0)`.
  - **Negatives:** a value below 0 flips the rect along x —
    `x = min(xval(0.0), xval(value))`, `width = |xval(value) - xval(0.0)|` — so the
    bar extends **left** of the baseline. Always anchor to `xval(0.0)`; never
    recompute a baseline (the value axis already forced 0 into the domain).
- **Geometry (stacked/percent):** the bar is a **floating** rect between two
  cumulative value-x's — `x = xval(cumLeft)`, `width = xval(cumRight) - xval(cumLeft)`
  — where `cumLeft`/`cumRight` come from the cumulative sums in series order
  (percent divides each by the category total). One slot of thickness `groupH`
  per category.
- **Fill:** read `fr.styles[si].fill` — the resolved bar paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a bar unfilled
  (an unfilled bar is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` and by convention `cy`. Under
  the transpose the value-end lands on x, so `cx = xval(value)` (the **bar tip**)
  and `cy` = the bar's band center on y (`top(i,k) + barH/2`). The unchanged
  runtime reads `cx` to position the (vertical) crosshair; putting it at the bar
  tip keeps the guide meaningful. Without `cx` the crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (column's, transposed to y)

The band scheme is column's §3.2 formula with the plot **height** substituted for
the width and `y` for `x`. Evaluate the arithmetic in **exactly this operation
order** in both languages so `f1` / `:.1f` rounding lands ULP-for-ULP identically
(blueprint §3.2 / §4; the frame's `ypix_band` implements the band center, the
marks build the sub-bands):

```
bandHeight   = plot_h / n
ypix_band(i) = plot_y + bandHeight*i + bandHeight/2     # band center on y
PAD          = 0.2                                       # single group-padding constant
groupH       = bandHeight * (1 - PAD)
K            = len(series)
barH         = groupH / K
top(i,k)     = ypix_band(i) - groupH/2 + barH*k
```

- Basic single-series ⇒ `K = 1` ⇒ one centered bar of thickness `groupH`.
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author
  choices — the *same* constants column uses. `grouping:false` forces `K = 1`
  (overlaid); `stacking` forces one slot (`K = 1`) with cumulative segment widths.
- **Stacking cumulative sums accumulate in series index order**, and the
  **frame's** stacked value-max uses that **same** order — pin both so cumulative
  floats and `%g` output match across languages.
- The value axis (x) is the exact transpose of column's y axis: same `nice_ticks`,
  same `include_zero=True` (0 forced in as the baseline), same `xval(v)` pixel map
  as column's `ypix(v)` but along x.

## Reused chrome (obtained from the frame — never re-implemented)

Bar inherits, with **zero** re-implementation, everything column inherits — the
frame just draws it transposed by orientation (§3.1, §4.2, §3.3 Rank 2):

- Plot area + margins; both axes + axis lines + axis titles.
- Linear **value** scale via `nice_ticks` → `xpix_val` (incl. the stacking-aware
  value-max the **frame** computes); **vertical** value gridlines + labels along
  the bottom.
- Categorical **band** axis via the band scale on **y**; the shared category-label
  loop lands labels beside band centers down the left with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"`, `include_zero=True` (value axis /
baseline), and `orientation="horizontal"`. It passes the bare noun **`"Bar"`** —
the frame expands it to `"Bar chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

Column's traps, all still in force, plus the transpose remap. Orientation adds
**no** new arithmetic — parity is free — but the remap must be applied
consistently in both languages.

- **Band arithmetic ORDER** — evaluate the seven lines above in that exact order
  (now over `plot_h`/`y`); a reassociated `plot_h/n` or `bandHeight*(1-PAD)`
  diverges after `f1` rounding.
- **Transpose consistency** — under `orientation="horizontal"` the band pixel is on
  y and the value pixel on x in **both** languages; never let one language leave
  the value on y. (`vertical` must remain the exact column code path so column
  goldens do not move.)
- **Summation order** — accumulate stacked cumulative sums in series index order;
  the frame's stacked value-max uses the **same** order; percent divides each
  value by its category total in that order.
- **Frame owns the value-domain** — the marks must call `fr.xpix_val` only;
  recomputing a scale (even to identical bytes) is a defect (NN, §7.1).
- **Bar-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field. Never emit an unfilled bar.
- **Negative bars** — flip `x`/`width` around `xval(0.0)`; do not emit a negative
  `width`.
- **`data-y` under stacking** — carries the **raw per-series segment value**, not
  the running cumulative total (the tooltip shows what the user supplied), while
  the geometry uses cumulative baselines along x.
- **`data-x`** — still the **category label** (`esc(category)`), even though
  categories render on the y axis; the tooltip and data table read the category
  from `data-x` unchanged.
- **Formatters** — `cx,cy,x,y,width,height` via `:.1f`/`f1`; `data-y`, radii,
  offsets via `fmt_num`/`fmtNum`; every user string via `esc`. A leaked raw `<`
  fails the XSS tests.
- **Degenerate percent** — a category total of 0 would divide-by-zero; pin the
  rule identically **before** the divide (Python raises, Go yields `NaN`→`"0"`).
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep series/point/legend
  `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Orientation changes **none**
of them — the runtime is unchanged (§3.3 Rank 2). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.sc-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its points, and the
  legend item (do not renumber).
- **Datum mark:** `.sc-point` (here also `.sc-bar`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover` — mandatory even though a `<rect>` ignores the hover `r`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (bar **tip** x =
  `xval(value)`) and by convention `cy` (bar band-center y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` — the **raw** per-series
  value under stacking; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks bars.
  `a11y:false` restores the pre-a11y bytes. Bar keeps `data: number[]`, so the
  existing `number[]` data table renders faithfully with **no** generalization
  (the §5.4b-DT obligation applies only when the data element type changes —
  scatter and later).
- **Static-first:** the chart is fully readable with JS disabled — bars are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/grouped.json`](examples/grouped.json):

```json
{
  "type": "bar",
  "title": "Response Latency by Service",
  "subtitle": "Grouped horizontal bars, p50 vs p95",
  "grouping": true,
  "xAxis": { "title": "Service", "categories": ["auth", "catalog", "cart", "payments", "shipping"] },
  "yAxis": { "title": "Latency (ms)" },
  "series": [
    { "name": "p50", "data": [24, 38, 31, 52, 45] },
    { "name": "p95", "data": [88, 142, 119, 210, 176] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered horizontal bars, ranked categories, baseline anchor on x |
| [`examples/grouped.json`](examples/grouped.json) | 2 series side-by-side, `grouping:true`, band sub-slots stacked down y |
| [`examples/stacked.json`](examples/stacked.json) | `stacking:"normal"`, cumulative segment baselines along x, frame-owned stacked value-max |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `stacking:"percent"` + a left→right gradient bar fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom bar color) so the XSS tests run against the
bar marks (§5.5d). `BAR_CASES = ["basic","grouped","stacked","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/bar/examples/grouped.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="bar",
    title="Response Latency by Service",
    x_axis=Axis(title="Service", categories=["auth", "catalog", "cart", "payments", "shipping"]),
    y_axis=Axis(title="Latency (ms)"),
    series=[
        Series("p50", [24, 38, 31, 52, 45]),
        Series("p95", [88, 142, 119, 210, 176]),
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
- **Hover a bar** → tooltip (category, series, value) + bar highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the bars; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — bars filled and readable.

## Rendering notes

- The **value** (x) axis uses "nice numbers" ticks (~6) and always includes 0 as
  the bar baseline unless `yAxis.min/max` clamp it. For `stacking:"percent"` the
  axis is effectively 0–100%.
- Bars use the **band** scale on **y** (`x_scale="band"`, `orientation="horizontal"`) —
  categories occupy equal horizontal bands; labels land beside band centers down
  the left.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole bar via the `<defs>` pre-pass. A
  **left→right** gradient tracks the bar's growth direction most naturally.
- Bar is column with the value/band axes swapped — it reuses the **same**
  extracted substrate (`_cartesian.py` / `cartesian.go`); the orientation flag is
  its only net-new, and it is **never** forked from column.

## Not yet supported (roadmap)

- Live renderers (`bar.py` / `bar.go`) — deferred; design + examples + validation
  are complete. Only `line` renders today. Bar lands after column (rank 1) and the
  orientation parameter it introduces.
- **Column range / bar range** (floating `(low,high)` bars) — the horizontal
  variant falls out of this orientation generalization + the floating-bar
  primitive (rank 11).
- **Bullet** (KPI bar + target + qualitative bands) — rides this bar substrate and
  the (usually horizontal) orientation transpose (rank 13).
- `drilldown`, rotated labels, negative-color zones, population-pyramid
  negative-stacks — variants layered on this base.
