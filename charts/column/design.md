---
id: SC-ARCH-005
title: StoneCharts Column Design
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-SCOPE-001, REQ-DET-001, REQ-STACK-001, REQ-STACK-002, REQ-RUNTIME-001, REQ-A11Y-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-STACK-SIGNED, TEST-PERCENT-DOMAIN, TEST-RUNTIME-BROWSER]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Chart: Column (`column`)

> **Phase 0 authority note:** this design predates the signed-stacking decision.
> [`ADR 0003`](../../docs/architecture/adr/0003-signed-stacking.md) overrides any
> single-accumulator or signed-percent language below until this design is reconciled.

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file is the **exemplar**
> every other Cartesian recipe is modeled on (it copies
> [`charts/line-basic/design.md`](../line-basic/design.md) and adds the sibling
> build detail: data model, marks, band layout, reused chrome, parity traps, and
> the a11y DOM contract).

- **Chart id:** `column`
- **Spec `type`:** `"column"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 1** · **Src:** HC
- **Status:** design-complete + examples validated · live Python/Go renderers
  (`column.py` / `column.go`) ride the shared Cartesian frame extracted for
  Rank 1 — see [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 1, §4, §5
- **Renderers:** `libs/python/stonecharts/charts/column.py` · `libs/go/column.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · implementation roadmap
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A column chart: one or more series drawn as **vertical, baseline-anchored bars**
over a shared categorical x-axis and a numeric y-axis. Each bar's height encodes
a value; bars are grouped side-by-side (multi-series), stacked, or
percent-stacked. Bars are the hoverable, interactive elements (they replace the
line chart's point markers).

Column is **build rank 1** — the first non-line Cartesian sibling. It is the
trigger for extracting the shared chrome out of `line.py`/`line.go` into the
shared cartesian module (§4), and it forces four reusable generalizations:
**band-layout**, the **stacking transform**, the **frame-owned stacking-aware
y-domain**, and the **rect-mark + `SeriesStyle.fill` bar-paint** primitive.

## Use it when

- Your x is a set of **discrete categories** (intervals, methods, services,
  stages) and your y is a **count or magnitude** you want to compare *across*
  those categories.
- You want to **compare a few series** within each category (grouped), or show
  **composition** within each category (stacked / percent-stacked).
- Rows look like: `label -> value` (one column) or `label -> value_a, value_b`
  (several series sharing one x).

Do **not** use it for: a **trend** over ordered/continuous x (use `line-basic`),
**x/y correlation** with no shared category ordering (use `scatter`),
**part-to-whole of a single total** (use pie/donut), or a **distribution** of raw
samples (use `histogram`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers, aligned to `categories` by index.
- Identical value payload to `line` (`data: number[]`) — grouped/stacked/percent
  are **transforms over these y-values**, selected by the chart-level `stacking`
  (+ `grouping`) fields, not a different data shape. A bare `number` stays valid
  (x = index), so line and column goldens never move when the point model lands.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"column"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the bar `<rect>`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`stacking`** | string | — (grouped) | **NEW field.** `null`/absent = grouped side-by-side; `"normal"` = bars stacked cumulatively; `"percent"` = stacked then normalized so each category totals 100%. The **frame** owns the resulting stacking-aware y-domain (max column **total**, not per-datum max). Added in the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) |
| **`grouping`** | bool | true | **NEW field.** Only meaningful when `stacking` is absent: `true` → `K = len(series)` side-by-side sub-bands per category (the pinned band layout); `false` → `K = 1`, all series share one centered slot (overlaid, drawn in series order). When `stacking` is set, grouping is ignored (a stack occupies one slot) |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the y range; the value axis always includes 0 (the bar baseline) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | bar values, length `N` (negatives allowed → bars drop below the baseline) |
| `series[].color` | string \| gradient | palette by index | the **bar fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole bar; legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the bar: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line spec but **inert** for column (no line to draw):
`fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`, `marker` are accepted
by the shared validator (forward-compatible) but not consumed by the column
marks. Full schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — one y per category, the same
  shape line uses. No `{x,y}` object model (that arrives with scatter, rank 3).
- **Grouped (default, `stacking` absent):** each category slot is split into
  `K = len(series)` equal sub-bands; series `k`'s bar sits in sub-band `k`. Basic
  single-series ⇒ `K = 1` ⇒ one centered bar of width `groupW`.
- **Stacked (`stacking: "normal"`):** one slot of width `groupW` per category;
  series segments accumulate on a cumulative baseline — segment `k`'s bottom is
  the running total through series `k-1`, its top the total through `k`.
- **Percent (`stacking: "percent"`):** stacked, then each segment is normalized
  by its category total so every category fills 0–100%.
- **The frame owns the y-domain.** For stacked/percent the y-max is the **max
  category total** (cumulative in the pinned summation order, §4), **not** the
  per-datum max — the marks never recompute a scale. For grouped it is the usual
  `nice_ticks` over the data with 0 forced in (`include_zero=True`).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2):

```python
# libs/python/stonecharts/charts/column.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Column", "band", _column_marks)   # include_zero defaults True
```
```go
// libs/go/column.go — package stonecharts
func renderColumnSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Column", "band", columnMarks, true)
}
```

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series, and inside it **one baseline-anchored `<rect>` per (category, series)**:

```html
<g class="sc-series" data-series="0">
  <rect class="sc-bar sc-point" data-series="0"
        data-series-name="GET" data-x="09:00" data-y="42"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="128.4" cy="96.0" x="112.0" y="96.0" width="32.8" height="240.0"
        fill="#2f7ed8"/>
  … one .sc-bar.sc-point per category …
</g>
```

- **Class:** `sc-bar sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `sc-bar` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The bar **is** the hoverable point; there are no separate markers.
- **Geometry (grouped):** `x = left(i,k)`, `width = barW`, from the band layout
  below. Baseline-anchored: `y = ypix(value)` and `height = ypix(0.0) - ypix(value)`
  for a positive value. **Negatives:** a value below 0 flips the rect —
  `y = min(ypix(0.0), ypix(value))`, `height = |ypix(0.0) - ypix(value)|` — so the
  bar drops from the baseline downward. Always anchor to `fr.ypix(0.0)`; never
  recompute a baseline (the value axis already forced 0 into the domain).
- **Geometry (stacked/percent):** the bar is a **floating** rect between two
  cumulative y-values — `y = ypix(cumTop)`, `height = ypix(cumBottom) - ypix(cumTop)`
  — where `cumBottom`/`cumTop` come from the cumulative sums in series order (percent
  divides each by the category total). One slot of width `groupW` per category.
- **Fill:** read `fr.styles[si].fill` — the resolved bar paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a bar unfilled
  (an unfilled column is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (bar center x) — the crosshair
  reads it — and by convention `cy` (bar top). Without `cx` the crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (copied VERBATIM from the blueprint)

Evaluate the arithmetic in **exactly this operation order** in both languages so
`f1` / `:.1f` rounding lands ULP-for-ULP identically (blueprint §3.2 / §4; the
frame's `xpix` implements the band center, the marks build the sub-bands):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
barW        = groupW / K
left(i,k)   = xpix(i) - groupW/2 + barW*k
```

- Basic single-series ⇒ `K = 1` ⇒ one centered bar of width `groupW`.
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author
  choices. `grouping:false` forces `K = 1` (overlaid); `stacking` forces one slot
  (`K = 1`) with cumulative segment heights.
- **Stacking cumulative sums accumulate in series index order**, and the
  **frame's** stacked y-max uses that **same** order — pin both so cumulative
  floats and `%g` output match across languages.
- Histogram (a later sibling) is the exception: bins are **contiguous — no
  inter-bar padding**. Column keeps the `PAD = 0.2` gap.

## Reused chrome (obtained from the frame — never re-implemented)

Column inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (incl. the stacking-aware y-max the
  **frame** computes); y gridlines + labels.
- Categorical x-axis via the **band** `xpix`; the shared x-label loop lands labels
  under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=True` (value axis /
baseline). It passes the bare noun **`"Column"`** — the frame expands it to
`"Column chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Band arithmetic ORDER** — evaluate the seven lines above in that exact order;
  a reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1` rounding.
- **Summation order** — accumulate stacked cumulative sums in series index order;
  the frame's stacked y-max uses the **same** order; percent divides each value by
  its category total in that order.
- **Frame owns the y-domain** — the marks must call `fr.ypix` only; recomputing a
  scale (even to identical bytes) is a defect (NN, §7.1).
- **Bar-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field. Never emit an unfilled bar.
- **Negative bars** — flip `y`/`height` around `ypix(0.0)`; do not emit a negative
  `height`.
- **`data-y` under stacking** — carries the **raw per-series segment value**, not
  the running cumulative total (the tooltip shows what the user supplied), while
  the geometry uses cumulative baselines.
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
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.sc-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its points, and the
  legend item (do not renumber).
- **Datum mark:** `.sc-point` (here also `.sc-bar`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover` — mandatory even though a `<rect>` ignores the hover `r`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (bar center x) and by
  convention `cy` (bar top).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` — the **raw** per-series
  value under stacking; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks bars.
  `a11y:false` restores the pre-a11y bytes. Column keeps `data: number[]`, so the
  existing `number[]` data table renders faithfully with **no** generalization
  (that obligation applies only when the data element type changes — scatter and
  later, §5.4b-DT).
- **Static-first:** the chart is fully readable with JS disabled — bars are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/grouped.json`](examples/grouped.json):

```json
{
  "type": "column",
  "title": "Requests by HTTP Method",
  "subtitle": "Grouped columns, per hour",
  "grouping": true,
  "xAxis": { "title": "Hour", "categories": ["09:00", "10:00", "11:00", "12:00", "13:00"] },
  "yAxis": { "title": "Requests (thousands)" },
  "series": [
    { "name": "GET",  "data": [42, 55, 61, 48, 39] },
    { "name": "POST", "data": [18, 24, 29, 22, 17] },
    { "name": "PUT",  "data": [6, 9, 11, 8, 5] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered bars, baseline anchor |
| [`examples/grouped.json`](examples/grouped.json) | 3 series side-by-side, `grouping:true`, band sub-slots |
| [`examples/stacked.json`](examples/stacked.json) | `stacking:"normal"`, cumulative segment baselines, frame-owned stacked y-max |
| [`examples/dark.json`](examples/dark.json) | `theme:"dark"`, single series — the minimal dark-theme case |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `stacking:"percent"` + a gradient bar fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom bar color) so the XSS tests run against the
column marks (§5.5d).
`COLUMN_CASES = ["basic","grouped","stacked","dark","themed-dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/column/examples/grouped.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="column",
    title="Requests by HTTP Method",
    x_axis=Axis(title="Hour", categories=["09:00", "10:00", "11:00", "12:00", "13:00"]),
    y_axis=Axis(title="Requests (thousands)"),
    series=[
        Series("GET",  [42, 55, 61, 48, 39]),
        Series("POST", [18, 24, 29, 22, 17]),
        Series("PUT",  [6, 9, 11, 8, 5]),
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
- **Hover a bar** → tooltip (x, series, y) + bar highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the bars; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — bars filled and readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) and always includes 0 as the bar baseline
  unless `yAxis.min/max` clamp it. For `stacking:"percent"` the axis is effectively
  0–100%.
- Bars use the **band** x-scale (`x_scale="band"`) — categories occupy equal
  bands; labels land under band centers.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole bar via the `<defs>` pre-pass.
- Column is the **exemplar**: the extraction it triggers (`_cartesian.py` /
  `cartesian.go`) is the substrate every later sibling reuses — never forked.

## Not yet supported (roadmap)

- **Bar** (horizontal columns) — the orientation transpose (rank 2).
- **Column range** (floating `(low,high)` bars) and **waterfall** (running-total
  columns) — later ranks reusing the band layout + floating-bar primitive.
- `drilldown`, rotated x-labels, negative-color zones, inverted axes — variants
  layered on this base.
