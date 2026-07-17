# Chart: Boxplot (`boxplot`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this recipe is modeled on the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> sibling build detail: the 5-number-summary point model, the box/whisker/median/
> outlier marks, the band layout, the reused chrome, the parity traps, and the
> a11y DOM contract.

- **Chart id:** `boxplot`
- **Spec `type`:** `"boxplot"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 14** (lands after
  the primitives it reuses: point model from Scatter **rank 3**, whisker from
  Error bar **rank 9**, floating-bar from Candlestick **rank 8** / Column range
  **rank 11**, band-layout from Column **rank 1**) · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; boxplot rides the shared cartesian frame once
  extraction + the point model land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2
  (Family A row), §3.3 Rank 3/8/9/11, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/boxplot.py` · `libs/go/boxplot.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A boxplot: one or more series drawn as **box-and-whisker glyphs** over a shared
categorical x-axis and a numeric y-axis. Each category's glyph summarizes a
**distribution** with a **5-number summary** — `low` (min), `q1`, `median`, `q3`,
`high` (max) — plus optional **outlier** points beyond the whiskers. The box spans
`q1`→`q3` (the interquartile range), a line marks the `median`, whiskers reach out
to `low`/`high`, and outliers ride as separate circles. The box **is** the
hoverable, interactive element (it replaces the line chart's point marker).

Boxplot is a distribution sibling: it draws no baseline-anchored bar. It **reuses**
the band-layout (Column), the floating-bar/rect primitive (Candlestick / Column
range), and the **whisker primitive shared with Error bar**, and it forces one
reusable generalization: the frame's **value-axis extractor spans each datum's
`[low, high]` plus its outliers** (not a single per-category value) — the same
extractor generalization Candlestick, Area range, and Error bar need.

## Use it when

- Your x is a set of **discrete categories** (endpoints, days, regions, builds)
  and for each you have a **distribution** of a numeric quantity (latency, pause
  time, response size) that you want to **compare across categories**.
- You want to show **spread and skew** (IQR box + median position + whisker reach)
  and flag **outliers**, not just a single central number.
- You have either a **precomputed 5-number summary** per category, or **raw
  samples** you want summarized (`p25`/`median`/`p75` + Tukey whiskers) by the
  renderer.

Do **not** use it for: a single **count or magnitude** per category (use
`column`), a **trend** over ordered/continuous x (use `line-basic`), a **binned
frequency** of one sample list (use `histogram`), a **confidence interval on a
center value** (use `errorbar` — a center `y` **plus** `low/high`, not a full
quartile summary), or the **density shape** of a distribution (violin — the
Statistical-family density upgrade). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[]` carries **one 5-number summary per category**, aligned to
  `categories` by index, plus an optional per-category outlier list. Two input
  modes:
  - **summary mode:** `series[].boxData` — length `N` array of
    `{low, q1, median, q3, high, outliers?}` objects.
  - **samples mode:** `series[].samples` — length `N` array of `number[]` (raw
    samples per category); the renderer runs the **5-number-summary transform**
    (quartiles + Tukey whiskers + outliers).
- `series[].data` stays a `number[]` of **medians** — the point model's
  bare-number projection and the field the current strict validator requires (see
  **Data model** below). Line + column goldens never move when the summary point
  model lands.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"boxplot"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the box `<rect>`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (the **5-number summary + outliers** per category — see §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`orientation`** | string | `vertical` | **NEW field.** `vertical` = boxes rise on the value-y axis over categorical x (default); `horizontal` = the coordinate transpose (bands on y, value on x). The transpose is a coordinate remap only (Bar-vs-Column, blueprint §3.3 Rank 2) — legend/tooltip/a11y unchanged. Graduates via the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) |
| **`scatterOverlay`** | bool | false | **NEW field.** When `true` and `samples` are present, jittered raw sample points are drawn over each box as an overlay (`.pk-sample` circles). Purely additive marks — the box stays the `.pk-point` |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories) |
| `yAxis.title` | string | — | axis label (the value/distribution axis) |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks over box extremes + outliers) | clamp the value range; unlike column the value axis does **not** force 0 (a box is a floating glyph, not a baseline bar) |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the **median** per category, length `N` — the point model's bare-number projection and the field the strict validator checks; mirrors `boxData[i].median` |
| **`series[].boxData`** | object[] | — | **NEW field (summary mode).** length `N`; each `{low, q1, median, q3, high, outliers?}` (numbers; `outliers` is a `number[]`). Requires `low ≤ q1 ≤ median ≤ q3 ≤ high` |
| **`series[].samples`** | number[][] | — | **NEW field (samples mode).** length `N`; each a raw `number[]` the 5-number-summary transform reduces to a box + whiskers + outliers |
| `series[].color` | string \| gradient | palette by index | the **box fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the box; median/whiskers/outliers + legend swatch use stop 0) |
| `series[].pattern` | object | — | hatch fill for the box: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line spec but **inert** for boxplot (no line to draw):
`fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`, `marker` are accepted by
the shared validator (forward-compatible) but not consumed by the boxplot marks.
`boxData`, `samples`, `orientation`, and `scatterOverlay` are **forward-compatible**
today (the strict validator ignores unknown keys — additive, schema
`additionalProperties`-open); they graduate to fully-validated fields via the
§5.4b five-place drill when the boxplot renderer lands. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Point model (richer):** each category's datum is a **5-number summary**,
  canonically the object `{low, q1, median, q3, high, outliers?}`. It **reuses**
  the point model's `low`/`high` fields (shared with Candlestick / Area range /
  Column range) and **extends** it with `q1`, `median`, `q3` (the boxplot
  addition). Positional-array sugar (blueprint §4 point-model row):
  `[low, q1, median, q3, high]`. A bare `number` still maps to a datum whose
  `median` is that number (the fast path), so **line + column goldens never move**.
- **Summary mode (`boxData`):** the object is consumed directly. Enforce
  `low ≤ q1 ≤ median ≤ q3 ≤ high` in the (deferred) validator.
- **Samples mode (`samples` → transform):** for each category, sort the raw
  samples ascending, then compute quartiles by **linear interpolation** (the R-7 /
  NumPy-default method): for quantile `p`, rank `h = (n-1)·p`,
  `q = s[⌊h⌋] + (h-⌊h⌋)·(s[⌊h⌋+1] - s[⌊h⌋])` — `q1` at `p=0.25`, `median` at
  `p=0.5`, `q3` at `p=0.75`. `IQR = q3 - q1`; Tukey fences
  `lowerFence = q1 - 1.5·IQR`, `upperFence = q3 + 1.5·IQR`. **Whiskers** clamp to
  the most extreme sample *within* the fences (`low = min` in-fence,
  `high = max` in-fence); **outliers** are the samples strictly outside a fence
  (`v < lowerFence` or `v > upperFence`), kept in ascending order. Pin the sort,
  the interpolation, the fence arithmetic, and the strict `<`/`>` comparisons
  **identically** in both languages — a diverging quantile shifts every pixel and
  every `data-*` value before formatting.
- **`data` is the median projection.** `series[].data` (a `number[]`, one median
  per category) is what the **current** strict validator checks; it mirrors
  `boxData[i].median`. Examples carry both — `data` for today's gate, `boxData`/
  `samples` for the summary the frame reads once the point model lands.
- **The frame owns the value-domain.** The frame's value-axis extractor is
  generalized to span **each datum's `[low, high]` plus its outliers** (not the
  median in `data`), scanned in category-then-series order — so a whisker or an
  outlier never clips the plot. The value axis uses `nice_ticks` with
  **`include_zero=False`** (a floating glyph has no baseline). The marks never
  recompute a scale.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). It passes the bare noun
**`"Boxplot"`** (the frame expands it to `"Boxplot chart with N series…"`
byte-for-byte) and **`include_zero=False`**:

```python
# libs/python/peakcharts/charts/boxplot.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Boxplot", "band", _boxplot_marks, include_zero=False)
```
```go
// libs/go/boxplot.go — package peakcharts
func renderBoxplotSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Boxplot", "band", boxplotMarks, false)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one box glyph per (category, series)** — a floating box
`<rect>` (the `.pk-point`), a median `<line>`, upper + lower whisker stem/cap
`<line>`s, and one `<circle>` per outlier:

```html
<g class="pk-series" data-series="0">
  <rect class="pk-box pk-point" data-series="0"
        data-series-name="Response time (ms)" data-x="/search" data-y="88"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="240.5" cy="168.0" x="210.0" y="150.0" width="61.0" height="70.0"
        fill="#2f7ed8" fill-opacity="0.5" stroke="#2f7ed8"/>
  <line class="pk-median"      x1="210.0" y1="168.0" x2="271.0" y2="168.0" stroke="#2f7ed8"/>
  <line class="pk-whisker"     x1="240.5" y1="150.0" x2="240.5" y2="96.0"  stroke="#2f7ed8"/>
  <line class="pk-whisker-cap" x1="225.3" y1="96.0"  x2="255.8" y2="96.0"  stroke="#2f7ed8"/>
  <line class="pk-whisker"     x1="240.5" y1="220.0" x2="240.5" y2="260.0" stroke="#2f7ed8"/>
  <line class="pk-whisker-cap" x1="225.3" y1="260.0" x2="255.8" y2="260.0" stroke="#2f7ed8"/>
  <circle class="pk-outlier"   cx="240.5" cy="70.0" r="2.5" fill="#2f7ed8"/>
  … one box glyph per category …
</g>
```

- **Class:** the box rect is `pk-box pk-point`. `pk-point` is the **contract**
  class the runtime keys on (tooltip / highlight / crosshair / legend-toggle);
  `pk-box`, `pk-median`, `pk-whisker`, `pk-whisker-cap`, `pk-outlier`, `pk-sample`
  are purely-cosmetic CSS hooks (adding a class the runtime must *know about* is
  out of scope — NN#2). The box **is** the hoverable point; median/whiskers/
  outliers are decoration within the same series group.
- **Box geometry (floating):** `x = left(i,k)`, `width = barW` (band layout below);
  `y = ypix(q3)`, `height = ypix(q1) - ypix(q3)` — a floating rect between two
  y-values, **not** baseline-anchored. Never call `ypix(0.0)`; the value axis has
  no forced baseline. **Degenerate `q1 == q3`** (zero-height box): apply the shared
  **min-1px** rule (the Candlestick doji rule, §3.3 Rank 8), pinned identically in
  both languages, so the box never vanishes.
- **Median line:** horizontal `<line>` at `ypix(median)` from `x` to `x + barW`.
- **Whiskers (shared primitive with Error bar):** stem `<line>`s on the box center
  `cx = left(i,k) + barW/2` — upper from `ypix(q3)` to `ypix(high)`, lower from
  `ypix(q1)` to `ypix(low)` — each capped by a short horizontal `<line>` of
  half-width `capHalf` (below). Same stem+cap primitive Error bar draws.
- **Outliers:** one `<circle class="pk-outlier">` per outlier at `(cx, ypix(o))`,
  radius `outlierR`, in the datum's ascending outlier order.
- **Fill:** read `fr.styles[si].fill` — the resolved box paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** The box
  carries a `fill-opacity` (default `0.5`) so the median line reads through; the
  stroke + median + whiskers + outliers use `fr.styles[si].solid`. Never read
  `area_fill` (that is line's under-fill), and never leave the glyph invisible.
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (box center x) — the crosshair
  reads it — and by convention `cy = ypix(median)` (the summary's center).
- **Scatter overlay (`scatterOverlay:true`, samples mode):** additionally emit one
  `<circle class="pk-sample">` per raw sample at `(jitter(cx), ypix(v))`, drawn
  after the box glyph. The jitter offset is a **pinned deterministic** function of
  `(i, k, sampleIndex)` (never a PRNG — parity requires identical bytes), spanning
  `±barW·0.3`. Purely additive; the box stays the `.pk-point`.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (copied VERBATIM from the blueprint)

Evaluate the arithmetic in **exactly this operation order** in both languages so
`f1` / `:.1f` rounding lands ULP-for-ULP identically (blueprint §3.2 / §4; the
frame's `xpix` implements the band center, the marks build the sub-bands). This is
the **same** band layout Column pins — boxplot keeps the `PAD = 0.2` inter-glyph
gap:

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
barW        = groupW / K
left(i,k)   = xpix(i) - groupW/2 + barW*k
cx          = left(i,k) + barW/2                      # box center x
CAP         = 0.5                                     # whisker-cap fraction of barW (fixed)
capHalf     = barW * CAP / 2
```

- Basic single-series ⇒ `K = 1` ⇒ one centered box of width `groupW` per category.
- Multi-series ⇒ `K = len(series)` side-by-side boxes per category (grouped
  distributions), each in its band sub-slot — identical to Column's grouped mode.
- `PAD = 0.2`, `CAP = 0.5`, `outlierR`, and the box `fill-opacity` are **fixed
  constants**, not per-author choices.
- Boxplot has **no `stacking`** (stacking a distribution is meaningless) — one glyph
  per (category, series), never a cumulative segment.
- **Horizontal orientation** transposes the whole block (band on y, value on x) — a
  coordinate remap only, deferred with the renderer.

## Reused chrome (obtained from the frame — never re-implemented)

Boxplot inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear value-scale via `nice_ticks` → `ypix` (over the box extremes + outliers
  the **frame** computes, `include_zero=False`); y gridlines + labels.
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

Net-new to boxplot on top of the frame: the **whisker primitive** (shared with
Error bar), the **floating box rect** (shared with Candlestick / Column range),
the **median line**, the **outlier circles**, the **5-number-summary transform**
(samples mode), and the frame's **`[low,high]`+outlier value-domain extractor**.
The chart delegates with `x_scale="band"` and `include_zero=False`.

## Parity traps (verify before the byte-parity gate)

- **Band arithmetic ORDER** — evaluate the nine lines above in that exact order; a
  reassociated `plot_w/n`, `bandWidth*(1-PAD)`, or `barW*CAP/2` diverges after `f1`
  rounding.
- **Summary transform (samples mode)** — pin the ascending sort, the linear-
  interpolation quantile formula (`h = (n-1)·p`, then the two-point interpolation),
  the fence arithmetic (`q1 - 1.5·IQR` / `q3 + 1.5·IQR`), and the **strict** `<`/`>`
  outlier comparisons. Iterate categories, series, samples, and outliers in a fixed
  order (never range-over-map). A one-ULP quantile drift moves pixels **and**
  `data-*`.
- **Frame owns the value-domain** — the extractor spans `[low, high]` + outliers
  (not the `data` medians), scanned in a pinned order, `include_zero=False`; the
  marks call `fr.ypix` only. Recomputing a scale (even to identical bytes) is a
  defect (NN, §7.1).
- **Box-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field.
- **Zero-height box (`q1 == q3`)** — apply the shared min-1px rule identically
  (Candlestick doji, §3.3 Rank 8); never emit a `height="0.0"` box that vanishes,
  and never a negative `height`.
- **Glyph emission ORDER** — box rect (the `.pk-point`) first, then median, then
  upper stem, upper cap, lower stem, lower cap, then outliers in ascending order,
  then (if enabled) samples in index order — pinned identically so bytes match.
- **`data-y`** — carries the **median** (`fmt_num(boxData[i].median)`), the datum's
  representative value; the full 5-number summary + outliers surface in the a11y
  data table (§5.4b-DT), not by coercing a range into `data-y`.
- **Formatters** — `cx,cy,x,y,width,height`, whisker/median/cap coords via
  `:.1f`/`f1`; `data-y`, radii, jitter offsets via `fmt_num`/`fmtNum`; every user
  string via `esc`. A leaked raw `<` fails the XSS tests.
- **Degenerate samples** — an empty sample list (`n == 0`) has no quantiles; pin
  the rule identically **before** the divide/interpolation (Python raises, Go
  yields `NaN`→`"0"`). `n == 1` ⇒ all quartiles equal that value, `IQR = 0`, no
  outliers.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` / `boxData` / `samples` / outliers by index (never
  range-over-map); keep series/point/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its boxes, and the legend
  item (do not renumber).
- **Datum mark:** the box `.pk-point` (here also `.pk-box`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover` — mandatory even though a `<rect>` ignores the hover `r`. Median,
  whisker, cap, outlier, and sample marks carry **no** `data-*` (cosmetic).
- **Crosshair anchor:** every `.pk-point` carries a `cx` (box center x) and by
  convention `cy` (= `ypix(median)`).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(boxData[i].median))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`. Pixel
  attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG; a
  separate **visually-hidden data table** in the HTML; keyboard nav walks boxes.
  `a11y:false` restores the pre-a11y bytes.
- **§5.4b-DT (point-model data table).** Boxplot's datum is **not** a bare number,
  so the shared accessible data table MUST be generalized (in lockstep, both
  languages, Py==Go table bytes) to render the **full 5-number summary + outliers**
  per category (columns: category, low, q1, median, q3, high, outliers) — never a
  single coerced number per row. Shipping an a11y-broken/misrepresenting table
  while passing the golden gates is forbidden — this obligation is part of adding
  the new data shape, alongside the §5.4b field drill and the Rank-3 byte-identity
  gate.
- **Static-first:** the chart is fully readable with JS disabled — boxes,
  whiskers, medians, and outliers are server-rendered and filled; the crosshair
  ships `display:none`; the tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "boxplot",
  "title": "API Latency Distribution by Endpoint",
  "subtitle": "Response time (ms), 5-number summary per endpoint",
  "xAxis": { "title": "Endpoint", "categories": ["/login", "/search", "/cart", "/checkout", "/profile"] },
  "yAxis": { "title": "Response time (ms)" },
  "series": [
    {
      "name": "Response time (ms)",
      "data": [24, 88, 35, 130, 28],
      "boxData": [
        { "low": 12, "q1": 18, "median": 24,  "q3": 33,  "high": 48  },
        { "low": 40, "q1": 65, "median": 88,  "q3": 120, "high": 190 },
        { "low": 20, "q1": 28, "median": 35,  "q3": 44,  "high": 60  },
        { "low": 55, "q1": 90, "median": 130, "q3": 180, "high": 260 },
        { "low": 15, "q1": 22, "median": 28,  "q3": 36,  "high": 52  }
      ]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered boxes, summary mode (`boxData`), no outliers |
| [`examples/outliers.json`](examples/outliers.json) | single series, per-category `outliers` lists beyond the whiskers |
| [`examples/grouped.json`](examples/grouped.json) | 2 series side-by-side, `K=2` band sub-slots, grouped distributions + outliers |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `orientation:"horizontal"` + `scatterOverlay` (samples mode) + a gradient box fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom box color) so the XSS tests run against the
boxplot marks (§5.5d). `BOXPLOT_CASES = ["basic","outliers","grouped","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/boxplot/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="boxplot",
    title="API Latency Distribution by Endpoint",
    x_axis=Axis(title="Endpoint", categories=["/login", "/search", "/cart", "/checkout", "/profile"]),
    y_axis=Axis(title="Response time (ms)"),
    series=[Series("Response time (ms)", [24, 88, 35, 130, 28])],   # + boxData once the point model lands
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
- **Hover a box** → tooltip (category, series, median) + box highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the boxes; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — boxes, whiskers, medians,
  and outliers all server-rendered.

## Rendering notes

- The value axis uses "nice numbers" ticks (~6) over the **box extremes +
  outliers** and does **not** force 0 (a box is a floating glyph — `include_zero
  =False`), unless `yAxis.min/max` clamp it.
- Boxes use the **band** x-scale (`x_scale="band"`) — categories occupy equal
  bands; labels land under band centers; multi-series boxes split each band into
  `K` sub-slots (Column's grouped layout).
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the box via the `<defs>` pre-pass, while the
  stroke/median/whiskers/outliers use the resolved solid color.
- Boxplot reuses the **whisker primitive** with Error bar and the **floating-bar**
  with Candlestick / Column range — never fork them; extend the shared substrate.

## Not yet supported (roadmap)

- Live renderers (`boxplot.py` / `boxplot.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Boxplot lands after the
  point model (Rank 3), the whisker primitive (Rank 9), and the floating-bar
  (Ranks 8/11).
- **Horizontal orientation** — the coordinate transpose (bands on y, value on x);
  the `orientation` field is designed but the transpose is deferred.
- **Scatter/jitter overlay** — `scatterOverlay` raw-sample points; designed,
  deferred with the samples-mode transform.
- **Notched boxplot** (median confidence-interval notch) and **variable-width
  boxes** (width ∝ sample count) — later variants over this base.
- **Violin** — the density upgrade (Boxplot + mirrored KDE); a **Statistical
  family** new-family opener, not a boxplot variant. See
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2 (D5).
</content>
