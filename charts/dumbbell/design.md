# Chart: Dumbbell (`dumbbell`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file mirrors the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which copies
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> dumbbell-specific build detail: the `{low,high}` range datum, the
> two-marker-plus-connector mark composition, the reused band layout, the reused
> marker symbols, the horizontal/vertical subtype, the parity traps, and the
> a11y DOM contract.

- **Chart id:** `dumbbell`
- **Spec `type`:** `"dumbbell"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Composition sibling** (rides
  **Column**'s band-layout, **Column range**'s `{low,high}` range point model +
  range-aware value-domain, and **Line**'s marker — introduces **no** new
  generalization, only a new mark composition; not in the rank 1–13 core sweep,
  adjacent to [`lollipop`](../lollipop/design.md)) · **Src:** HC (highcharts-more)
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; dumbbell rides the shared cartesian frame
  once extraction and the range point model land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2
  Family A "Dumbbell", §3.3 Rank 10/11, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/dumbbell.py` · `libs/go/dumbbell.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A dumbbell chart (a.k.a. DNA / connected-dot plot): one or more series drawn as a
**`{low,high}` range per category** — two marker `<circle>`s (a **low** head and a
**high** head) joined by a thin connecting `<line>` (the "bar"). It reads the
*gap* between two values per category — classically a **before / after** or
**start / end** comparison (last-quarter vs this-quarter latency, 2019 vs 2024
pay, min vs max temperature). It is a [`column range`](../columnrange/design.md)
with the floating rect stripped down to a connector and two dots, or equivalently
a [`lollipop`](../lollipop/design.md) whose single baseline-anchored stem becomes
a **floating** connector between two data values instead of rising from zero.

Dumbbell is a **composition sibling**: it is built once **Column** (band-layout),
**Column range / Area range** (the `{low,high}` point model + the range-aware
value-domain), and **Line** (the four marker symbols) exist, and it composes
those already-shipped primitives into a new mark. It forces **no** new
generalization — no new scale, no new transform, no new point model beyond the
`{low,high}` range one the range siblings already introduced. Its only new spec
field is the **`orientation`** subtype selector (vertical / horizontal), which
reuses Bar's orientation-transpose concept.

## Use it when

- Your x is a set of **discrete categories** (services, endpoints, regions,
  roles, teams) and each category carries **two comparable values** whose **gap**
  is the story — before vs after, this period vs last period, min vs max, target
  vs actual.
- You want a **ranking of change**: sort categories by the size (or direction) of
  the gap and read top-to-bottom — the `horizontal` subtype is the classic ranked
  dumbbell.
- You want to compare **a few `{low,high}` ranges** within each category (grouped
  dumbbells side-by-side, each with its own marker symbol).
- Rows look like: `label -> (low, high)` (one dumbbell) or
  `label -> (low_a, high_a), (low_b, high_b)` (several ranges sharing one x).

Do **not** use it for: a **single** value per category (use `column` / `bar`, or
`lollipop` for the low-ink version), a **trend** over ordered/continuous x (use
`line-basic`), a **filled band over time** (use `arearange`), a **floating
solid-bar range** where area matters (use `columnrange`), or a **center value
with a symmetric error interval** (use `error-bar`'s `{y,low,high}` — dumbbell has
no center y). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers — the **low** endpoint of each category's
  range, aligned to `categories` by index (the required, validated payload).
- each `series[].high`: `N` numbers — the **high** endpoint of each category's
  range (the second half of the `{low,high}` model, shared verbatim with
  [`columnrange`](../columnrange/design.md) and [`arearange`](../arearange/design.md)).
- **`{low,high}` range payload** — `data` holds the lows, `high` holds the highs,
  index-aligned. This is the **same** authoring shape column-range and area-range
  use, so their examples, spec model, and validator rules are reused unchanged. A
  bare `data: number[]` stays a valid `number[]` (the lows) so the shared
  validator accepts the spec on its known fields today, before the range point
  model lands in the renderers.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"dumbbell"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the shared tail's `<rect>`, tinted with the series color) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (with **both** low and high per row — see §a11y). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`orientation`** | string | `"vertical"` | **NEW field.** `"vertical"` = ranges run up the y value-axis (categories on x, connectors vertical); `"horizontal"` = ranges run along the x value-axis (categories on y, connectors horizontal) — the ranked subtype, which rides Bar's orientation-transpose (§3.2 orientation). Added in the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) |
| **`grouping`** | bool | true | **REUSED from `column`.** When a chart has multiple series: `true` → `K = len(series)` side-by-side sub-band dumbbells per category (the pinned band layout); `false` → `K = 1`, all series' dumbbells share one centered slot (overlaid, drawn in series order). Single-series ⇒ `K = 1` ⇒ one centered dumbbell regardless |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories; on the y-axis when `orientation:"horizontal"`) |
| `yAxis.title` | string | — | axis label (the value-axis label) |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks over lows∪highs) | clamp the value range; unlike column, the value axis is **not** forced through 0 — a range floats between its `low` and `high`, so the frame's range-aware domain spans `min(all lows)` to `max(all highs)` (§Data model) |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | value-axis gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the **low** endpoints, length `N` (the required, validated `number[]`) |
| `series[].high` | number[] | — | the **high** endpoints, length `N` (the `{low,high}` model; shared with column-range/area-range) |
| `series[].color` | string \| gradient | palette by index | the **connector + head color**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object. The connector stroke uses the gradient `url(#grad)`; the heads' fill + legend swatch + `data-color` use stop 0's solid (exactly line's stroke/marker split) |
| `series[].lineWidth` | number | 2 | **connector thickness** (px) — reused from line's line width; the connector `<line>` `stroke-width` |
| `series[].dashStyle` | string | solid | **connector dash**: solid/dashed/dotted — reused from line |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:4}` | **the two heads** — reused verbatim from line's marker: `symbol` ∈ circle/square/triangle/diamond, `radius` sizes both heads. Authors typically bump `radius` (≈5–6) for prominent dots. `enabled:false` yields a bare connector (rare) |
| `series[].lowName` / `series[].highName` | string | `Low` / `High` | forward-compatible labels for the two endpoints in the tooltip / data table (e.g. `"2019"` / `"2024"`, `"Before"` / `"After"`); accepted (ignored) by the shared validator until the range tooltip lands |
| `series[].pattern` | object | — | hatch fill; accepted by the shared validator but inert for dumbbell (there is no filled area/rect to hatch) |

Fields carried over from the line/column spec but **inert** for dumbbell:
`fillOpacity`, `step`, `curve`, `stacking` are accepted by the shared validator
(forward-compatible) but not consumed by the dumbbell marks — a range floats
between two absolute values, not on a cumulative baseline, so `stacking` does not
apply (see Data model). Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** the `{low,high}` **range point model** — `series[].data` is
  the `number[]` of lows and `series[].high` the `number[]` of highs, index-aligned
  to the categories. This is the **same** model column-range and area-range
  introduce (§3.3 Rank 10/11); dumbbell **reuses** it — no net-new point model.
- **Single series (`K = 1`):** each category slot holds **one centered dumbbell**
  at the band center `xpix(i)` — a connector from `ypix(low)` to `ypix(high)` with
  a head at each end.
- **Grouped (`grouping:true`, default when multi-series):** each category slot is
  split into `K = len(series)` equal sub-bands; series `k`'s dumbbell sits at the
  **center of sub-band `k`** — `dumbbellX(i,k) = left(i,k) + barW/2` (band layout
  below). Each series carries its own marker symbol so grouped dumbbells are
  distinguishable.
- **Overlaid (`grouping:false`):** `K = 1`, all series' dumbbells share the one
  centered slot, drawn in series index order (heads may coincide — later series on
  top).
- **No stacking, no baseline flip.** A dumbbell is **not** anchored to `ypix(0)` —
  both endpoints are absolute value positions, so there is no baseline and no
  negative-flip logic (unlike column's rect). `stacking` is inert. Negatives are
  handled naturally: a `low` below 0 simply maps to `ypix(low)` above the higher
  pixel row and the head sits below the axis zero line — no special case.
- **The frame owns the range-aware value-domain.** For the `{low,high}` model the
  frame computes the value axis over **`min(all lows)` … `max(all highs)`** via
  `nice_ticks` (the same range-aware domain column-range and area-range use),
  delegated with **`include_zero=False`** — a range floats, it is **not**
  zero-baselined. The marks call `fr.ypix` only; they **never** recompute a scale
  and never force 0.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). It passes
`include_zero=False` (a range has no baseline) so the frame builds the range-aware
domain over lows∪highs:

```python
# libs/python/peakcharts/charts/dumbbell.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    # noun="Dumbbell", band scale, include_zero=False (floating range, no baseline)
    return render_cartesian(spec, "Dumbbell", "band", _dumbbell_marks, include_zero=False)
```
```go
// libs/go/dumbbell.go — package peakcharts
func renderDumbbellSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Dumbbell", "band", dumbbellMarks, false)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series. Inside it, per category, it emits the **connector first, then the two
heads** (so the heads always render above the connector), and marks the **high
head** as the single hoverable `.pk-point` for the range datum:

```html
<g class="pk-series" data-series="0">
  <!-- connector: one floating <line> low->high per category -->
  <line class="pk-connector" data-series="0"
        x1="128.4" y1="336.0" x2="128.4" y2="120.0"
        stroke="#2f7ed8" stroke-width="2"/>
  <!-- low head: decorative endpoint marker -->
  <circle class="pk-dumbbell-low" data-series="0"
          cx="128.4" cy="336.0" r="4" fill="#2f7ed8" stroke="#ffffff" stroke-width="1"/>
  <!-- high head: THE hoverable range datum (.pk-point), carrying BOTH bounds -->
  <circle class="pk-point pk-dumbbell-high" data-series="0"
          data-series-name="Latency" data-x="/checkout"
          data-y="210" data-low="150" data-high="210"
          data-color="#2f7ed8" data-r="4" data-r-hover="6"
          cx="128.4" cy="120.0" r="4" fill="#2f7ed8" stroke="#ffffff" stroke-width="1"/>
  … one connector + two heads per category …
</g>
```

- **Three marks per datum, one hoverable.** A dumbbell datum is **one
  `{low,high}` range**, so — exactly like column-range's single floating rect and
  candlestick's single body — it exposes **one** `.pk-point`. The **high head**
  carries `class="pk-point"` (the **contract** element the runtime keys on:
  tooltip / highlight / crosshair / legend-toggle) and carries **both** bounds via
  `data-low` **and** `data-high`; its `data-y` = the high value (the canonical
  anchor the unchanged runtime reads). The **connector** (`pk-connector`) and the
  **low head** (`pk-dumbbell-low`) are decorative CSS hooks carrying only
  `data-series` (so they hide with the series); `pk-dumbbell-high` on the point is
  likewise a cosmetic add — adding a class the runtime must *know about* is out of
  scope (NN#2, §5.3). All three marks sit inside the same
  `.pk-series[data-series=N]` group, so the legend toggle hides connector **and**
  both heads together.
- **Head geometry:** each head is line's marker, drawn by the reused
  `_marker`/`markerSVG` helper — the **low** head at `(dumbbellX, ypix(low))`, the
  **high** head at `(dumbbellX, ypix(high))`, both with radius `marker.radius`. All
  four symbols (circle/square/triangle/diamond) are supported verbatim; non-circle
  heads still carry `cx`/`cy` so the crosshair works (line's marker already does
  this).
- **Connector geometry (vertical):** `dumbbellX = left(i,k) + barW/2` (band layout
  below); the connector runs `y1 = fr.ypix(low)` to `y2 = fr.ypix(high)`. This is
  correct for **any** low/high ordering with **no flip** — the connector `<line>`
  is symmetric, and the heads mark which end is which. There is **no** baseline and
  **no** `y`/`height` rect to flip (a genuine simplification over column).
- **Connector geometry (horizontal, `orientation:"horizontal"`):** the value axis
  is x and the band axis is y — the connector runs `x1 = fr.xpix(low)` to
  `x2 = fr.xpix(high)`, both at `y = dumbbellY(i,k)`; heads at `(xpix(low), y)` and
  `(xpix(high), y)`. This rides Bar's orientation-transpose (a coordinate remap
  only — §3.2).
- **Color:** read `fr.styles[si].stroke` for the **connector** stroke (hex or
  `url(#grad)`) and `fr.styles[si].solid` for the **heads'** fill / `data-color` /
  legend swatch — **exactly line's stroke/marker split.** Never read
  `fr.styles[si].fill` (that is column/column-range's bar paint — a dumbbell has no
  filled rect) and never read `area_fill` (line's under-fill). The head halo stroke
  is `theme.marker_halo`, as line's marker.
- **`cx` / `cy`:** the `.pk-point` high head MUST carry `cx` (the dumbbell x) — the
  crosshair reads it — and by convention `cy` (the high head y). Without `cx` the
  crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (copied VERBATIM from the blueprint)

Dumbbell reuses **Column's** band layout unchanged. Evaluate the arithmetic in
**exactly this operation order** in both languages so `f1` / `:.1f` rounding lands
ULP-for-ULP identically (blueprint §3.2 / §4; the frame's `xpix` implements the
band center, the marks build the sub-bands and place the dumbbell at the sub-band
center):

```
bandWidth      = plot_w / n
xpix(i)        = plot_x + bandWidth*i + bandWidth/2      # band center
PAD            = 0.2                                     # single group-padding constant
groupW         = bandWidth * (1 - PAD)
K              = len(series)
barW           = groupW / K
left(i,k)      = xpix(i) - groupW/2 + barW*k
dumbbellX(i,k) = left(i,k) + barW/2                      # dumbbell sits at the sub-band CENTER
```

- Basic single-series ⇒ `K = 1` ⇒ `barW = groupW` ⇒ `dumbbellX(i,0) = xpix(i)`
  (one centered dumbbell at the band center).
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author
  choices. `grouping:false` forces `K = 1` (overlaid). Dumbbell has no `stacking`
  slot collapse — it is always the grouped band layout (or `K=1`).
- For `orientation:"horizontal"` the identical arithmetic runs on the **y** band
  axis (`plot_h`, `n` categories down the side), producing `dumbbellY(i,k)`; the
  low/high values run along x. Orientation is a coordinate remap only — same `f1`
  arithmetic.

## Reused chrome (obtained from the frame — never re-implemented)

Dumbbell inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear value-axis via `nice_ticks` → `ypix` — here the **range-aware** domain
  over `min(lows) … max(highs)` (the same one column-range/area-range compute),
  delegated `include_zero=False`; value-axis gridlines + labels.
- Categorical band axis via the **band** `xpix`; the shared x-label loop lands
  labels under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle`
  (`stroke`/`solid`), id-scoping via `cid` (defs emitted only when a series needs
  them — no empty `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- The reused **marker** helper (`_marker`/`markerSVG`) for both heads, the reused
  **band layout** for the dumbbell x, and the reused **range-aware value-domain**
  for `{low,high}` — all already parity-locked by column, line, and the range
  siblings.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=False` (floating
range). It passes the bare noun **`"Dumbbell"`** — the frame expands it to
`"Dumbbell chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Band arithmetic ORDER** — evaluate the eight lines above in that exact order;
  a reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1` rounding.
  Reuse Column's helper — do **not** re-derive it.
- **Frame owns the range-domain** — the marks must call `fr.ypix`/`fr.xpix` only;
  recomputing a scale (even to identical bytes) is a defect (NN, §7.1). The domain
  spans lows∪highs and is delegated `include_zero=False` — **do not** force 0 into
  a dumbbell axis (that is column's zero-baseline, wrong for a floating range).
- **No baseline, no flip** — a dumbbell has no `ypix(0)` anchor and no rect; draw
  the connector `ypix(low)`→`ypix(high)` and the two heads at their absolute pixels.
  Do **not** copy column's `y`/`height` negative-flip logic (there is no rect), and
  do **not** anchor either head to zero.
- **Read the LINE fields, not the COLUMN field** — connector = `fr.styles[si].stroke`,
  heads = `fr.styles[si].solid`. Reading `fill` (column/column-range's bar paint) or
  `area_fill` (line's under-fill) is the wrong field and drops the gradient/solid
  split.
- **Emission order = connector, then low head, then high head** — emit the
  `.pk-connector` line, then the `.pk-dumbbell-low` head, then the
  `.pk-point`/`.pk-dumbbell-high` head, inside each series group, so heads render
  above the connector identically in both languages.
- **One `.pk-point` per range datum, on the HIGH head** — do not emit two
  `.pk-point`s per datum (a range is one datum, per the column-range precedent);
  the low head is decorative. `data-y` = the **high** value (canonical anchor);
  `data-low`/`data-high` carry the raw endpoints for the tooltip and the data
  table.
- **`data-low` / `data-high` carry the raw values** — `data-low = esc(fmt_num(low))`,
  `data-high = esc(fmt_num(high))` — the datum's own endpoints (there is no
  cumulative total to confuse them with).
- **Formatters** — `x1,y1,x2,y2,cx,cy` and marker points via `:.1f`/`f1`;
  `data-y`, `data-low`, `data-high`, radii via `fmt_num`/`fmtNum`; every user string
  via `esc`. A leaked raw `<` fails the XSS tests.
- **Degenerate `low == high`** — a zero-length connector is fine (a `<line>` with
  coincident ends draws nothing); both heads coincide. There is **no** divide, so
  no divide-by-zero rule to pin (unlike percent-stacked column) — a genuine
  simplification.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep
  series/connector/head/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its connector, its heads,
  and the legend item (do not renumber). The legend toggle hides the whole group —
  connector and both heads together.
- **Datum mark:** the **high head** `.pk-point` (here also `.pk-dumbbell-high`)
  carries **all** of `data-series`, `data-series-name`, `data-x`, `data-y`,
  `data-color`, `data-r`, `data-r-hover`, **plus** `data-low` and `data-high` (the
  full range). The connector `.pk-connector` and the low head `.pk-dumbbell-low`
  are decorative and carry only `data-series` (so they hide with the series) — they
  are **not** `.pk-point`s.
- **Crosshair anchor:** the `.pk-point` high head carries a `cx` (dumbbell x) and by
  convention `cy` (high head y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(high))`;
  `data-low = esc(fmt_num(low))`; `data-high = esc(fmt_num(high))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`.
  Pixel attrs use `:.1f`/`f1`.
- **A11y default-on + the range data-table obligation (§5.4b-DT / §6.4):** the SVG
  gets `role="img"` + concise `aria-label` + `<desc>`; the HTML adds a separate
  **visually-hidden data table**. Because dumbbell's datum is a `{low,high}` range —
  **not** a single `number` — the shared data table MUST be generalized (in
  lockstep, both languages, Py==Go table bytes) to render **both** low and high per
  row, exactly as column-range and area-range require. Dumbbell does **not**
  invent this generalization; it **shares** the range siblings' one. `a11y:false`
  restores the pre-a11y bytes. Keyboard nav walks the high heads.
- **Static-first:** the chart is fully readable with JS disabled — connectors and
  both heads are server-rendered and colored; the crosshair ships `display:none`;
  the tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "dumbbell",
  "title": "Median Latency: Before vs After Caching",
  "subtitle": "One dumbbell per endpoint — the gap is the improvement",
  "xAxis": { "title": "Endpoint", "categories": ["/login", "/search", "/cart", "/checkout", "/invoice"] },
  "yAxis": { "title": "p50 latency (ms)" },
  "series": [
    {
      "name": "p50 latency",
      "lowName": "After",
      "highName": "Before",
      "data": [42, 68, 55, 96, 71],
      "high": [88, 152, 119, 210, 164],
      "marker": { "symbol": "circle", "radius": 5 }
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered dumbbells, `{low,high}` range, circle heads, `lowName`/`highName` endpoint labels |
| [`examples/grouped.json`](examples/grouped.json) | 2 series side-by-side, `grouping:true`, band sub-slots, distinct marker symbols per series, ranges per category |
| [`examples/horizontal.json`](examples/horizontal.json) | `orientation:"horizontal"` ranked subtype, custom connector `lineWidth` + `dashStyle`, larger heads |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a gradient connector (`defs` pre-pass → connector `url(#grad)`, heads solid = stop 0) + square heads + a negative `low` value |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom head/connector color, `lowName`/`highName`) so
the XSS tests run against the dumbbell marks (§5.5d).
`DUMBBELL_CASES = ["basic","grouped","horizontal","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/dumbbell/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Marker, Series, save_html
save_html(ChartSpec(
    type="dumbbell",
    title="Median Latency: Before vs After Caching",
    x_axis=Axis(title="Endpoint", categories=["/login", "/search", "/cart", "/checkout", "/invoice"]),
    y_axis=Axis(title="p50 latency (ms)"),
    series=[
        Series("p50 latency", [42, 68, 55, 96, 71], high=[88, 152, 119, 210, 164],
               marker=Marker(symbol="circle", radius=5)),
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
- **Hover a dumbbell (its high head)** → tooltip (category, series, low + high) +
  head highlight + crosshair.
- **Click a legend item** → toggle that series on/off (connector **and** both heads
  hide).
- **Keyboard** → arrows walk the dumbbells; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — connectors and heads
  colored and readable.

## Rendering notes

- The value axis uses "nice numbers" ticks (~6) over the **range** (`min(lows)` …
  `max(highs)`) and is **not** forced through 0 — a dumbbell floats between its two
  endpoints (`include_zero=False`). Clamp with `yAxis.min/max` when you want a fixed
  window.
- Dumbbells use the **band** x-scale (`x_scale="band"`) — categories occupy equal
  bands; labels land under band centers. Grouped series split each band into `K`
  equal sub-slots.
- Both heads reuse line's four marker symbols; set `series[].marker.symbol` to
  distinguish grouped series and `series[].marker.radius` to size the dots. Give the
  two endpoints readable names with `lowName` / `highName`.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient color paints the connector via the `<defs>` pre-pass while the
  heads/legend use stop 0's solid.
- Dumbbell adds **no** new generalization — it composes Column's band-layout,
  Column range's `{low,high}` model + range-aware domain, and Line's marker, so it
  is one of the cheapest siblings once those exist.

## Not yet supported (roadmap)

- Live renderers (`dumbbell.py` / `dumbbell.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Dumbbell lands after the
  range point model (area-range / column-range, rank 10/11) and the band layout.
- **Per-endpoint independent styling** (different symbol/color for the low vs high
  head via `lowMarker` / `highMarker`) — a later variant on this base.
- **Arrow / directional connectors** (encode the sign of the change) and
  **connector color-by-direction** (gain vs loss) — layered on this base.
- `drilldown`, rotated x-labels, and a third connected point (a "barbell" of three
  markers) — variants layered on this base.
