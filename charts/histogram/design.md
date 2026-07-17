# Chart: Histogram (`histogram`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file mirrors the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> sibling build detail: data model, marks, bin geometry, reused chrome, parity
> traps, and the a11y DOM contract.

- **Chart id:** `histogram`
- **Spec `type`:** `"histogram"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 7** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; histogram rides the shared cartesian frame
  once the extraction, the numeric x-axis, and binning land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 7, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/histogram.py` · `libs/go/histogram.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A histogram: a **distribution** of a single continuous variable drawn as
**contiguous, baseline-anchored `<rect>` bars** over a **numeric x-axis** of bin
edges. Each bar covers one bin `[binStart, binEnd)`; its height encodes the
**count** (frequency) or **density** of samples that fall in that bin. Unlike a
column chart the bars **touch with no gap** — the x is a continuous number line
sliced into intervals, not a set of discrete categories.

Histogram is **build rank 7**. It reuses column's rect-mark and scatter's numeric
x-axis, and its one genuinely new component is the **binning transform**
(min/max → bin count/width → assign samples → counts). It also hosts two
**derived-series overlays** — the **pareto** cumulative-percent line and the
**bell-curve** normal fit — selected by a chart-level `overlay` field.

## Use it when

- You have **many raw samples of one continuous quantity** (latencies, allocation
  sizes, GC pauses, payload sizes) and want to see the **shape of their
  distribution** — where the mass sits, skew, modality, tails.
- Your rows look like a **flat list of numbers** (`[42, 55, 61, …]`), not a
  `label -> value` table.
- You already have **pre-binned counts** (`binStart, binEnd, count` per bucket)
  and want them drawn as a distribution.

Do **not** use it for: a **count/magnitude across discrete categories** you chose
yourself (use `column` — its bars have a `PAD=0.2` gap and a categorical x), a
**trend** over ordered/continuous x (use `line-basic`), **x/y correlation** of
two variables (use `scatter`), or a **five-number statistical summary** per group
(use `boxplot`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

Histogram's data is **semantically different** from every y-per-category sibling —
the input is the raw material of a distribution, and the renderer (not the author)
decides the bars:

- **Raw mode (default):** each `series[].data` is an **unaggregated list of
  samples** (`number[]`) — the renderer computes bin edges from the data range and
  the `binning` config, then counts samples per bin.
- **Pre-binned mode (`preBinned: true`):** each `series[].data` is a list of
  **per-bin counts** (`number[]`, one per bin), and `xAxis.binEdges` supplies the
  `N+1` numeric edges. The canonical richer form of a pre-binned bucket is the
  point object `{binStart, binEnd, count}`; until the shared **point model**
  lands (§3.3 Rank 3), pre-binned is expressed as counts + `binEdges` so today's
  `number[]` validator accepts it unchanged (see **Data model**).

There is **no** `xAxis.categories` axis of author-chosen labels — the x labels are
**bin edges**, numeric values produced by the binning transform and formatted
through `fmt_num`.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"histogram"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the bar `<rect>`); with an `overlay`, the derived series gets its own legend entry |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`binning`** | object | auto | **NEW field.** Raw-mode bin selection: `{count?: int, width?: number, start?: number}`. `count` → that many equal-width bins across `[min,max]`; `width` → fixed-width bins (`start` overrides the first left edge, default = data min); neither → the pinned default `count = max(1, ceil(sqrt(n)))`. `count` and `width` are mutually exclusive (`count` wins if both present). Ignored in pre-binned mode. Added via the §5.4b five-place lockstep |
| **`preBinned`** | bool | false | **NEW field.** `true` → `series[].data` is per-bin **counts** (not raw samples) and `xAxis.binEdges` supplies the edges; `binning` is ignored |
| **`normalization`** | string | `"frequency"` | **NEW field.** `"frequency"` → bar height = raw count; `"density"` → height = `count / (n * binWidth)` so the total bar **area** integrates to 1 (comparable across differing bin widths / sample sizes) |
| **`overlay`** | string | — (none) | **NEW field.** Derived-series overlay drawn on top of the bars: `"pareto"` → a cumulative-percent line + points on a **secondary y-axis** (0–100%); `"bellcurve"` → a smooth normal-fit `<path>` scaled to the histogram. The overlay is a **renderer-computed series**, not one the author supplies |
| `xAxis.title` | string | — | axis label |
| `xAxis.binEdges` | number[] | — | **NEW field.** Pre-binned mode only: the `N+1` numeric bin edges, ascending; bar `b` spans `[binEdges[b], binEdges[b+1])`. `len(binEdges) == len(data)+1` |
| `xAxis.min` / `xAxis.max` | number | auto (from bin edges) | clamp the numeric x range; default spans the outer bin edges |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the count/density range; the value axis always includes 0 (the bar baseline) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | **raw samples** (raw mode) OR **per-bin counts** (`preBinned`), length arbitrary (raw) or `= N bins` (pre-binned) |
| `series[].color` | string \| gradient | palette by index | the **bar fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole bar; legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the bar: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line/column spec but **inert** for histogram (no line
to draw, no author categories, no group/stack of author series): `fillOpacity`,
`lineWidth`, `dashStyle`, `step`, `curve`, `marker`, `grouping`, `stacking` are
accepted by the shared validator (forward-compatible) but not consumed by the
histogram bar marks. (The pareto/bellcurve overlay draws its own derived line with
fixed styling — it does not read the user series' `lineWidth`/`dashStyle`.) Full
schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` in **both** modes — raw samples
  (raw mode) or per-bin counts (`preBinned`). No object element is used **today**,
  so histogram rides the existing `number[]` validator and the existing
  `number[]` accessible data table with **no** generalization (the obligation in
  §5.4b-DT applies only when the `data` element type actually changes).
- **The pre-binned point object `{binStart, binEnd, count}`** is the canonical
  richer form named in the blueprint (§3.3 Rank 7). It arrives with the shared
  **point model** (§3.3 Rank 3): a bare number stays valid, and a bucket object is
  sugar for `{x:binStart, y:count}` + `binEnd`. Until then, `preBinned` specs carry
  `data:[counts]` + `xAxis.binEdges:[edges]`, which is byte-for-byte the same
  information and passes `validate()` unchanged. When the point model lands, the
  accessible data table is generalized in lockstep (§5.4b-DT) to render the bucket
  faithfully.
- **The frame owns the y-domain.** Counts/density feed the usual `nice_ticks` with
  0 forced in (`include_zero=True`) — the bar baseline. The marks never recompute a
  scale. With `overlay:"pareto"` the cumulative-percent line rides a **secondary
  y-axis** (0–100%) owned by the frame (the combo secondary-y-axis generalization,
  §3.2), not a scale the marks derive.
- **The frame owns the x-domain too.** The numeric x-scale spans the **outer bin
  edges** `[edge_0, edge_K]` — a free numeric axis (include-zero **OFF** for x;
  do **not** anchor bin edges at 0). This is scatter's numeric x-axis (§3.3 Rank 3),
  reused verbatim: `nice_ticks` + `fmt_num` give byte-identical x ticks for free.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). Histogram rides the **numeric
x-scale** (scatter's, for bin edges) with the **count value-axis zero-anchored**
(`include_zero=True` — the y baseline):

```python
# libs/python/peakcharts/charts/histogram.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Histogram", "linear", _histogram_marks)  # include_zero defaults True (count baseline)
```
```go
// libs/go/histogram.go — package peakcharts
func renderHistogramSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Histogram", "linear", histogramMarks, true)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one baseline-anchored `<rect>` per bin** (plus, when an
`overlay` is set, one derived `.pk-series` for the pareto/bellcurve line):

```html
<g class="pk-series" data-series="0">
  <rect class="pk-bar pk-point" data-series="0"
        data-series-name="Latency" data-x="39–60" data-y="9"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="112.0" cy="180.0" x="80.0" y="180.0" width="64.0" height="156.0"
        fill="#2f7ed8"/>
  … one .pk-bar.pk-point per bin …
</g>
```

- **Class:** `pk-bar pk-point`. `pk-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `pk-bar` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The bar **is** the hoverable point; there are no separate markers.
- **Geometry (contiguous — the load-bearing divergence from column):** a bar for
  bin `b` spans **adjacent bin edges** with **no inter-bar padding**:
  `x = fr.xpix(edge(b))`, `width = fr.xpix(edge(b+1)) - fr.xpix(edge(b))`. Because
  consecutive bars share an edge pixel, they touch — there is **no** `PAD`, no
  `groupW`, no `barW`, none of column's band arithmetic. Baseline-anchored on the
  count axis: `y = fr.ypix(h(b))`, `height = fr.ypix(0.0) - fr.ypix(h(b))`, where
  `h(b)` is the bin count (or density). Always anchor to `fr.ypix(0.0)`; never
  recompute a baseline (the count axis already forced 0 into the domain).
- **Bin heights:** `h_frequency(b) = count[b]`; `h_density(b) = count[b] / (n * w)`
  where `n` = total samples and `w` = bin width. Guard `n*w == 0` **before** the
  divide (pin the rule identically — see parity traps).
- **Fill:** read `fr.styles[si].fill` — the resolved bar paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a bar unfilled
  (an unfilled histogram is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (bar center x — here the bin
  **midpoint** `fr.xpix((edge(b)+edge(b+1))/2)`) — the crosshair reads it — and by
  convention `cy` (bar top). Without `cx` the crosshair breaks.
- **Overlay (derived series):** when `overlay` is set the marks append **one more**
  `<g class="pk-series" data-series="{K}">` after the bars — a `pk-series-line`
  `<path>` plus `.pk-point`s — for the cumulative-percent (pareto) or normal-fit
  (bellcurve) curve. Its `data-series` index is `len(series)` (it does not renumber
  the bar series), and the shared tail emits its legend swatch.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Bin layout — the pinned geometry (the binning transform)

The **binning transform** is histogram's one net-new component and, per the
blueprint, **the biggest parity trap in the family** (§3.3 Rank 7): bin edges and
the value→bin assignment must be **byte-identical** across languages or counts
diverge *before* any formatting. Evaluate the arithmetic in **exactly this
operation order** in both Python and Go:

```
# RAW MODE — bin selection, edges, assignment (identical order both languages)
lo = min(samples);  hi = max(samples)            # data range
K  = binning.count                     if count given
     else ceil((hi - lo) / binning.width)        if width given
     else max(1, ceil(sqrt(n)))                   # default: sqrt choice, PINNED
w  = binning.width                     if width given
     else (hi - lo) / K                           # count / default mode
lo = binning.start                     if start given (width mode)  # first left edge
edge(i) = lo + w*i                     for i = 0 … K                 # N+1 edges

# assign each sample v to a bin — last bin is INCLUSIVE of hi:
bin(v) = K-1                           if v == hi
         else clamp(floor((v - lo) / w), 0, K-1)
count[bin(v)] += 1

# PRE-BINNED MODE:
edge(i) = xAxis.binEdges[i]            # given directly, K = len(binEdges) - 1
count[b] = data[b]                     # counts given directly

# HEIGHT:
h_frequency(b) = count[b]
h_density(b)   = count[b] / (n * w)    # guard n*w == 0 BEFORE the divide

# PIXELS (contiguous — NO padding, unlike column):
x(b)      = fr.xpix(edge(b))
width(b)  = fr.xpix(edge(b+1)) - fr.xpix(edge(b))
cx(b)     = fr.xpix((edge(b) + edge(b+1)) / 2)
y(b)      = fr.ypix(h(b))
height(b) = fr.ypix(0.0) - fr.ypix(h(b))
```

- **`sqrt` for the default bin count is IEEE754-identical** (`math.sqrt` /
  `math.Sqrt`); `ceil` and `floor` are exact; so `K` is pinned across languages.
- **The last bin is inclusive of `hi`** — without the explicit `v == hi ⇒ K-1`
  guard, the maximum sample would land in bin `K` (out of range). Pin this rule
  identically **before** the `floor`.
- **Bars are contiguous — zero inter-bar padding.** This is the deliberate
  exception the blueprint calls out (column keeps `PAD = 0.2`; histogram does not).
  Do **not** import column's `groupW`/`barW`/`left(i,k)` band arithmetic.
- **Pareto cumulative:** `cum(b) = sum(count[0..b])`; percent `pct(b) = 100 * cum(b) / n`
  — accumulate in bin order, divide once, both languages the same order.
- **Bell-curve fit:** mean `μ = Σv / n`; variance `σ² = Σ(v-μ)² / n`; `σ = sqrt(σ²)`
  — accumulate in sample order; guard `σ == 0` before scaling; `sqrt` is
  IEEE754-identical.

## Reused chrome (obtained from the frame — never re-implemented)

Histogram inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (the count/density value axis, 0 forced
  in); y gridlines + labels.
- **Numeric x-axis** via scatter's `linear` `xpix` (bin edges), `nice_ticks` +
  `fmt_num` x ticks + optional vertical gridlines — include-zero **OFF** for x.
- **Secondary y-axis** (0–100%) for the pareto overlay — combo's dual value axis
  (§3.2), owned by the frame.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="linear"` (numeric bin edges) and
`include_zero=True` (the count/density value axis / baseline). It passes the bare
noun **`"Histogram"`** — the frame expands it to `"Histogram chart with N
series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Binning is THE trap.** The bin-edge computation *and* the value→bin rule
  (`bin = floor((v-lo)/w)`, last bin inclusive of `hi`, `clamp` to `[0,K-1]`) must
  be byte-identical, evaluated in the exact order above — a reassociated `(hi-lo)/K`
  or a missing `v==hi` guard changes **counts**, which diverges *before* any
  formatting and no `fmt_num` can rescue.
- **Default bin count** — `K = max(1, ceil(sqrt(n)))` only when neither `count` nor
  `width` is given; `sqrt` is IEEE754-identical, `ceil` exact. Pin it; do not let
  one language fall back to a different heuristic.
- **Contiguous bars — no padding** — `width = xpix(edge(b+1)) - xpix(edge(b))`;
  never borrow column's `PAD`/`groupW`/`barW`. A stray gap is a visible defect and
  a byte diff.
- **Numeric x-domain from bin edges, include-zero OFF** — the x-scale spans
  `[edge_0, edge_K]`, never anchored at 0; the **count** (y) axis is the one with
  `include_zero=True`. Mixing these up wrongly anchors the x at 0 (both languages
  identically → passes byte-parity but is wrong), so the flag must be explicit.
- **Density divide-by-zero** — `count[b] / (n*w)` with `n*w == 0` must be guarded
  **before** the divide, pinned identically (Python raises without the guard; Go
  yields `NaN`→`"0"`) so the two never diverge.
- **Bar-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field. Never emit an unfilled bar.
- **Pareto / bell-curve accumulation order** — cumulative sums accumulate in bin
  order; mean/variance in sample order; both languages identical; `σ = sqrt(var)`
  is IEEE754-identical; guard `σ == 0` before scaling the curve.
- **`data-y` is the raw bin height** — the count (frequency mode) or the density
  value (density mode) the tooltip shows, via `esc(fmt_num(...))`; never the
  cumulative pareto total.
- **Formatters** — `cx,cy,x,y,width,height` and path `d` numbers via `:.1f`/`f1`;
  `data-y`, edges, radii, density, percent via `fmt_num`/`fmtNum`; every user
  string via `esc`. A leaked raw `<` fails the XSS tests.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep series/point/legend
  `data-series` indices in lockstep (the overlay series is index `len(series)`).

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series (plus one for the
  overlay at index `len(series)`); `N` is the integer series index, **consistent**
  across the group, its points, and the legend item (do not renumber).
- **Datum mark:** `.pk-point` (here also `.pk-bar`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover` — mandatory even though a `<rect>` ignores the hover `r`.
- **Crosshair anchor:** every `.pk-point` carries a `cx` (bin midpoint x) and by
  convention `cy` (bar top).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(<bin range label>)` (e.g. `"39–60"` — the bin edges via `fmt_num`,
  joined, then `esc`); `data-y = esc(fmt_num(height))` — the raw count or density,
  **not** the cumulative pareto total; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks bins.
  `a11y:false` restores the pre-a11y bytes. Histogram keeps `data: number[]` (raw
  samples or counts), so the existing `number[]` data table renders faithfully with
  **no** generalization — that obligation applies only when the data element type
  changes to the `{binStart,binEnd,count}` object model (which lands with the point
  model, §5.4b-DT).
- **Static-first:** the chart is fully readable with JS disabled — bars are
  server-rendered and filled, overlays drawn; the crosshair ships `display:none`;
  the tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "histogram",
  "title": "Response Latency Distribution",
  "subtitle": "Raw request timings, binned into 10 equal-width buckets",
  "binning": { "count": 10 },
  "xAxis": { "title": "Latency (ms)" },
  "yAxis": { "title": "Requests" },
  "series": [
    { "name": "Latency", "data": [42, 55, 61, 48, 39, 72, 88, 95, 110, 63, 57, 44, 51, 66, 78] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | raw samples, `binning.count`, frequency histogram, contiguous bars, numeric x |
| [`examples/prebinned.json`](examples/prebinned.json) | `preBinned:true`, per-bin counts + `xAxis.binEdges`, `normalization:"density"` (area integrates to 1) |
| [`examples/pareto.json`](examples/pareto.json) | raw samples, `binning.width`+`start`, `overlay:"pareto"` (cumulative-% line on a secondary y-axis) |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `overlay:"bellcurve"` (normal fit) + a gradient bar fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, custom bar color, and the bin-range `data-x` label) so the XSS tests
run against the histogram marks (§5.5d).
`HISTOGRAM_CASES = ["basic","prebinned","pareto","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/histogram/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="histogram",
    title="Response Latency Distribution",
    x_axis=Axis(title="Latency (ms)"),
    y_axis=Axis(title="Requests"),
    series=[Series("Latency", [42, 55, 61, 48, 39, 72, 88, 95, 110, 63])],
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
- **Hover a bar** → tooltip (bin range, series, count/density) + bar highlight + crosshair.
- **Click a legend item** → toggle that series (or the overlay) on/off.
- **Keyboard** → arrows walk the bins; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — bars filled, overlay drawn.

## Rendering notes

- The x-axis is **numeric** (bin edges), using scatter's `nice_ticks`-driven
  numeric scale with include-zero **OFF** — the domain spans the outer bin edges,
  never anchored at 0. The y-axis (counts/density) uses "nice numbers" ticks (~6)
  and always includes 0 as the bar baseline unless `yAxis.min/max` clamp it.
- Bars use the **contiguous** edge mapping (`x_scale="linear"`) — one `<rect>` per
  bin, touching neighbours with no gap (the histogram exception to column's band
  padding).
- The default bin count when neither `binning.count` nor `binning.width` is given
  is `max(1, ceil(sqrt(n)))`, pinned identically in both languages.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole bar via the `<defs>` pre-pass.
- `overlay` draws a renderer-computed derived series (pareto cumulative-% line on a
  secondary 0–100% axis, or a bell-curve normal fit) — it reuses combo's
  secondary-y-axis and line's `_path_d`, adding no new runtime behavior.

## Not yet supported (roadmap)

- Live renderers (`histogram.py` / `histogram.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Histogram is sequenced after
  the extraction (§4), scatter's **numeric x-axis** (Rank 3), and combo's
  **secondary y-axis** (Rank 6), which it reuses.
- The **`{binStart, binEnd, count}`** pre-binned point object as a `data` element —
  arrives with the shared point model (§3.3 Rank 3); until then pre-binned is
  expressed as counts + `xAxis.binEdges`.
- Adaptive bin-width rules (Freedman–Diaconis, Sturges, Scott) as named `binning`
  strategies; log-spaced bins; multi-series overlaid distributions with per-series
  opacity.
- Rotated x-labels, 2-D histogram (→ heatmap/hexbin, Family C), and the KDE/violin
  density upgrade (Family F) — layered on other substrates, not this base.
