# Chart: Waterfall (`waterfall`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> sibling build detail: data model, marks, band layout, reused chrome, parity
> traps, and the a11y DOM contract.

- **Chart id:** `waterfall`
- **Spec `type`:** `"waterfall"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 12** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; waterfall rides the shared cartesian frame
  once its rank lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3
  Rank 12, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/waterfall.py` · `libs/go/waterfall.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5 (Rank 12)

## What it is

A waterfall chart: a **single ordered sequence of deltas** drawn as **floating
bars** that step up and down from a running total, so you can see how an initial
value is transformed — contribution by contribution — into a final value. Each
bar spans from the running total *before* the step to the running total *after*
it; **dashed connector lines** join the top of one bar to the foot of the next so
the eye follows the cumulative path. **Total** and **subtotal** bars break the
float and are drawn **zero-anchored** (from the baseline up to the running total),
so a reader can read the cumulative figure directly off the axis.

Bars are the hoverable, interactive elements (they replace the line chart's point
markers). Color encodes **direction**: increases, decreases, and totals each get
their own color (the up/down/total three-color config).

Waterfall is **build rank 12** — a late Cartesian sibling that reuses almost the
entire substrate the earlier ranks already built. It forces only two genuinely
new generalizations: the **running-total transform** (cumulative deltas → a
`[start, end]` span per bar, which also feeds the frame's y-domain) and the
**connector-lines primitive**. Its floating-`<rect>` mark is the same
**floating-bar primitive** first extracted for candlestick (Rank 8) and reused by
column-range (Rank 11); its geometry sits in the same **band layout** column
(Rank 1) pinned.

## Use it when

- Your x is an **ordered set of stages/drivers** and each contributes a signed
  **delta** to a running quantity you want to trace — a budget bridge, a P&L
  revenue-to-profit bridge, a latency budget across request stages, an inventory
  reconciliation.
- You want to show **how you got from a starting figure to an ending figure**,
  step by step, and (optionally) call out **subtotals** and a **grand total**
  along the way.
- Rows look like: `stage -> delta` (one series of signed numbers), with a few of
  those stages optionally flagged as a subtotal or total.

Do **not** use it for: comparing independent magnitudes across categories (use
[`column`](../column/design.md)), a **trend** over continuous/ordered x (use
[`line-basic`](../line-basic/design.md)), **composition** of a single total at one
instant (use pie/donut / a percent-stacked `column`), a floating `(low,high)`
range with no running total (use [`columnrange`](../columnrange/design.md)), or a
distribution of raw samples (use `histogram`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the stage labels, length `N` (absent → index `0..N-1`).
- `series[].data`: `N` numbers — the **signed deltas**, aligned to `categories`
  by index. Waterfall is normally **single-series** (one sequence of deltas); the
  band layout still supports `K = len(series)` if several delta sequences share
  the stage axis.
- A stage may be flagged a **subtotal** (`isIntermediateSum`) or a **grand total**
  (`isSum`); such a stage carries no delta of its own — its bar value is
  **computed** by the running-total transform (see *Data model*). In the flat form
  today's examples use, a flagged stage carries a `0` placeholder in `data` and
  the flag rides a chart-level companion array.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"waterfall"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle. Waterfall's legend is a **three-swatch key** (increase / decrease / total), not one swatch per series |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the stage labels, one band per stage) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the y range; the value axis always includes 0 (the baseline total/subtotal bars anchor to) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | tooltip name (legend uses the direction key, not the series name) |
| `series[].data` | number[] | — | the **signed deltas**, length `N` (negatives allowed → the bar steps *down*); a stage flagged sum/subtotal carries a `0` placeholder that the transform overrides |
| **`series[].isSum`** *(planned, per-point)* | bool per point | false | **NEW field.** Marks a stage a **grand total**: its bar is zero-anchored from the baseline to the running total of **all** preceding deltas; its own `y`/delta is ignored. Lands via the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) as part of the point-model generalization (§3.3 Rank 3 / §5.4b-DT) — the same `data`-element change scatter's `{x,y}` needs |
| **`series[].isIntermediateSum`** *(planned, per-point)* | bool per point | false | **NEW field.** Marks a stage a **subtotal**: zero-anchored bar showing the cumulative running total *so far*; does not itself consume a delta. Same lockstep as `isSum` |
| **`sumIndices`** *(chart-level, flat form)* | int[] | `[]` | **Forward-compatible companion.** Data indices that are grand totals — the flat-form equivalent of a per-point `isSum` while `data` is still `number[]`. Tolerated as an unknown key today (like column's pre-lockstep `stacking`); migrates onto the datum when the point model lands |
| **`intermediateSumIndices`** *(chart-level, flat form)* | int[] | `[]` | **Forward-compatible companion.** Data indices that are subtotals — the flat-form equivalent of a per-point `isIntermediateSum` |
| **`upColor`** | string \| gradient | theme up accent | **Three-color config.** Fill for **increase** bars (`delta > 0`). Hex, or a gradient object resolved through the `<defs>` pre-pass into `url(#grad)` |
| **`downColor`** | string \| gradient | theme down accent | Fill for **decrease** bars (`delta < 0`) |
| **`totalColor`** | string \| gradient | theme total accent | Fill for **total / subtotal** bars (zero-anchored) |
| `connector` | object | `{enabled:true, color:theme grid, dashStyle:dashed}` | styling for the dashed lines joining consecutive bars; `dashStyle` ∈ solid/dashed/dotted |

Fields carried over from the line spec but **inert** for waterfall (no line to
draw): `series[].color`, `fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`,
`marker` are accepted by the shared validator (forward-compatible) but not
consumed by the waterfall marks — direction color comes from the
`upColor`/`downColor`/`totalColor` config, not `series[].color`. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

> **Validated-today note.** `validate()` currently accepts `series[].data` as
> `number[]` only, so the per-point `isSum`/`isIntermediateSum` flags cannot yet
> live *inside* a datum (an object element fails `_num`). Today's examples
> therefore keep `data` a pure `number[]` and mark totals with the chart-level
> `sumIndices` / `intermediateSumIndices` arrays (unknown-but-tolerated keys). Every
> shipped example passes `validate() == []`. When the point-model lockstep lands,
> the flags move onto the datum and the **pure-delta goldens never move** — exactly
> the forward-compatible stance column takes with `stacking`, and candlestick /
> column-range take with their flat `number[]` examples.

## Data model

- **Value payload:** `series[].data` is `number[]` — one **signed delta** per
  stage, the same element shape line and column use. No `{x,y}` object model yet
  (that arrives with the Rank 3 point-model generalization; §3.3).
- **The running-total transform (net-new for this rank).** Accumulate the deltas
  **in stage index order** into a running total, and derive each bar's
  `[start, end]` span from it:

  ```
  running = 0.0
  for i in 0..N-1:
      if i is a sum/subtotal stage:
          start = 0.0                       # zero-anchored
          end   = running                   # display the cumulative total; delta ignored
          # running is UNCHANGED — a subtotal displays, it does not add
      else:
          start = running
          end   = running + delta[i]
          running = end                      # advance the cumulative
      bar[i] = (start, end)
  ```

  A **grand total** (`isSum`) and a **subtotal** (`isIntermediateSum`) are drawn
  identically (zero-anchored to the current `running`); they differ only in the
  legend/semantic label and, for `isSum`, the convention that it appears last and
  equals the sum of *all* deltas.
- **The frame owns the y-domain — and for waterfall it is the transform's
  cumulative extents, not the per-delta min/max.** The value axis spans
  `[min(0, all starts, all ends), max(0, all starts, all ends)]`, run through
  `nice_ticks` with `include_zero=True` (0 is always in — total/subtotal bars
  anchor there). This is the direct analogue of column's stacking-aware y-max:
  the marks **never** recompute a scale; the frame computes the domain over the
  cumulative running totals in the **pinned accumulation order** so the float and
  `%g` output match across languages.
- **Direction classification.** `delta > 0` → increase (up); `delta < 0` →
  decrease (down); a sum/subtotal stage → total — **regardless** of its placeholder
  value. Pin the comparator `delta >= 0 ? up : down` identically in both languages
  (the same discipline candlestick pins for `close >= open`).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2):

```python
# libs/python/stonecharts/charts/waterfall.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Waterfall", "band", _waterfall_marks)   # include_zero defaults True
```
```go
// libs/go/waterfall.go — package stonecharts
func renderWaterfallSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Waterfall", "band", waterfallMarks, true)
}
```

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series, containing the **dashed connector `<line>`s** (decorative) followed by
**one floating `<rect>` per stage** (the hoverable `.sc-point`):

```html
<g class="sc-series" data-series="0">
  <line class="sc-connector" x1="144.8" y1="150.0" x2="223.2" y2="150.0"
        stroke="#c9ccd6" stroke-width="1" stroke-dasharray="4 3"/>
  … one connector between each pair of consecutive bars …
  <rect class="sc-bar sc-point" data-series="0"
        data-series-name="Budget" data-x="Headcount" data-y="260"
        data-kind="increase" data-total="1060"
        data-color="#2e9e5b" data-r="3.5" data-r-hover="6"
        cx="184.0" cy="96.0" x="167.6" y="96.0" width="32.8" height="54.0"
        fill="#2e9e5b"/>
  … one .sc-bar.sc-point per stage …
</g>
```

- **Class:** `sc-bar sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `sc-bar` is a
  purely-cosmetic CSS hook, and `sc-connector` a cosmetic class on the connector
  lines (adding a class the runtime must *know about* is out of scope — NN#2). The
  bar **is** the hoverable point; there are no separate markers.
- **Bar geometry (the floating-bar primitive):** from the running-total transform,
  a stage's span is `(start, end)`. The rect is drawn between the two pixel
  y-values, never with a negative height:
  `y = min(ypix(start), ypix(end))`, `height = |ypix(start) - ypix(end)|`,
  `x = left(i, k)`, `width = barW` (band layout below). For a **delta** stage
  `start = running` and `end = running + delta`; for a **total/subtotal** stage
  `start = fr.ypix(0.0)`'s value `0.0` and `end = running` (**zero-anchored** — 
  always anchor to `fr.ypix(0.0)`, never recompute a baseline). Pin a **min-1px**
  height for a zero-magnitude bar (a `delta == 0` step or a subtotal that lands on
  0) in **both** languages — the doji rule candlestick pins.
- **Connector geometry (net-new primitive):** between consecutive bars, a
  horizontal dashed `<line>` at the shared cumulative level — from the **right edge
  of bar `i`** to the **left edge of bar `i+1`**, at `y = ypix(level)` where
  `level` is the running total that ends bar `i` (`end` of a delta stage, or the
  displayed cumulative of a total/subtotal). `x1 = left(i,k) + barW`,
  `x2 = left(i+1,k)`. Emitted **before** the rects so bars paint over the line
  ends. `connector.enabled:false` suppresses them. No connector after the last bar.
- **Fill (direction color):** `delta > 0` → resolve `upColor`; `delta < 0` →
  resolve `downColor`; sum/subtotal → resolve `totalColor`. Resolve each the same
  way column resolves a bar paint through `SeriesStyle.fill`: **pattern →
  `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never read
  `area_fill` (that is line's under-fill), and never leave a bar unfilled (an
  unfilled bar is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (bar center x) — the crosshair
  reads it — and by convention `cy` (bar top = `min(ypix(start), ypix(end))`).
  Without `cx` the crosshair breaks.
- **Legend:** waterfall's legend is the **increase / decrease / total** direction
  key (three swatches in those three colors), emitted by the shared tail. Do not
  emit a legend from the marks and do not renumber series indices.

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

- Waterfall is normally single-series ⇒ `K = 1` ⇒ one centered bar of width
  `groupW` per stage (one stage per band). The center `cx = xpix(i)`.
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author
  choices — identical to column so the two siblings share the substrate byte for
  byte.
- **The running-total accumulates in stage index order**, and the **frame's**
  y-domain uses that **same** order — pin both so cumulative floats and `%g` output
  match across languages.

## Reused chrome (obtained from the frame — never re-implemented)

Waterfall inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (incl. the running-total-aware y-domain
  the **frame** computes); y gridlines + labels.
- Categorical x-axis via the **band** `xpix`; the shared x-label loop lands the
  stage labels under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup for the default
  up/down/total accents.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a fill needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=True` (value axis /
baseline). It passes the bare noun **`"Waterfall"`** — the frame expands it to
`"Waterfall chart with N series…"` byte-for-byte. The **floating-bar primitive**
(rect between two arbitrary y-values) comes from candlestick / column-range and is
reused unchanged; only the **running-total transform** and the **connector-lines
primitive** are net-new here.

## Parity traps (verify before the byte-parity gate)

- **Accumulation ORDER** — accumulate the running total in stage index order; the
  frame's y-domain uses the **same** order. A reassociated sum diverges after `%g`
  / `f1` rounding.
- **Frame owns the y-domain** — the domain is the cumulative running-total extents
  (incl. 0), computed by the **frame**, not the per-delta min/max and not
  recomputed in the marks. Recomputing a scale (even to identical bytes) is a
  defect (NN, §7.1).
- **Band arithmetic ORDER** — evaluate the seven band-layout lines in that exact
  order; a reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1`.
- **Direction comparator** — pin `delta >= 0 ? up : down` identically; a total/
  subtotal stage is `total` regardless of its placeholder value. A flipped
  comparator silently mis-colors a zero-delta step.
- **Floating-rect flip** — draw with `y = min(ypix(start), ypix(end))`,
  `height = |ypix(start) - ypix(end)|`; never emit a negative `height`. Anchor
  total/subtotal bars to `fr.ypix(0.0)`, never a recomputed baseline.
- **Min-1px degenerate bar** — a `delta == 0` bar (or a subtotal landing on 0)
  would be zero-height; pin the **min-1px** rule identically in both languages
  (the doji rule) **before** formatting.
- **Connector endpoints** — from bar-right of step `i` (`left(i,k)+barW`) to
  bar-left of step `i+1` (`left(i+1,k)`) at the ending cumulative `level`; none
  after the last bar; coords via `f1`.
- **`data-y` semantics** — carries the **raw delta** the user supplied for a delta
  stage, and the **computed running total** for a sum/subtotal stage (the tooltip
  shows the meaningful figure). Emit `data-total` (the running total after the
  step) and `data-kind` (`increase`/`decrease`/`total`) as informational extras;
  the geometry uses the cumulative `[start,end]`.
- **Fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else solid
  hex, applied per direction (`upColor`/`downColor`/`totalColor`). Reading `solid`
  silently drops a gradient; reading `area_fill` is line's field. Never emit an
  unfilled bar.
- **Formatters** — `cx,cy,x,y,width,height`, connector `x1,y1,x2,y2` via
  `:.1f`/`f1`; `data-y`, `data-total`, radii via `fmt_num`/`fmtNum`; every user
  string via `esc`. A leaked raw `<` fails the XSS tests.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` (and the deltas) by index (never range-over-map); keep
  series/point/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes**.

- **Series group:** `.sc-series[data-series=N]` — one per series; `N` is the
  integer series index, **consistent** across the group, its points, its
  connectors, and the legend item (do not renumber). The connector lines sit
  inside the group so they hide with the series on legend-toggle.
- **Datum mark:** `.sc-point` (here also `.sc-bar`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover` — mandatory even though a `<rect>` ignores the hover `r`. Waterfall
  adds informational `data-kind` and `data-total`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (bar center x) and by
  convention `cy` (bar top).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(stage label)`; `data-y = esc(fmt_num(displayValue))` — the **raw
  delta** for a delta stage, the **computed total** for a sum/subtotal stage;
  `data-color = fr.styles[...].solid` for the resolved direction color;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks the
  bars. `a11y:false` restores the pre-a11y bytes. Waterfall keeps `data: number[]`,
  so the existing `number[]` data table renders the deltas faithfully with **no**
  generalization (the §5.4b-DT obligation only triggers when the data element type
  changes — that arrives with the per-point `isSum` object model). A richer table
  that also lists running totals is an optional enhancement, not a requirement.
- **Static-first:** the chart is fully readable with JS disabled — bars and
  connectors are server-rendered and filled; the crosshair ships `display:none`;
  the tooltip is JS-only.

## Example spec

See [`examples/intermediate-sums.json`](examples/intermediate-sums.json):

```json
{
  "type": "waterfall",
  "title": "Engineering Budget Bridge — FY25",
  "subtitle": "Planned deltas with a mid-year subtotal and year-end total",
  "intermediateSumIndices": [4],
  "sumIndices": [8],
  "upColor": "#2e9e5b",
  "downColor": "#d9534f",
  "totalColor": "#4b6cb7",
  "xAxis": {
    "title": "Line item",
    "categories": ["Base", "Headcount", "Tooling", "Cloud", "H1 subtotal", "Contractors", "Savings", "Travel", "FY total"]
  },
  "yAxis": { "title": "Budget (USD, thousands)" },
  "series": [
    { "name": "Budget", "data": [800, 260, 90, 140, 0, 180, -120, 40, 0] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, pure deltas, up/down color by sign, connectors, `K=1` centered bars |
| [`examples/intermediate-sums.json`](examples/intermediate-sums.json) | a subtotal (`intermediateSumIndices`) + a grand total (`sumIndices`), zero-anchored total bars, explicit up/down/total three-color config |
| [`examples/profit-bridge.json`](examples/profit-bridge.json) | classic revenue→profit bridge: float deltas via `fmt_num`, a mid-statement subtotal + final total, dashed `yAxis.gridLine`, default direction colors |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` observability latency budget: subtotal + total, custom up/down/total colors, a "saved-latency" negative delta |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, stage label, custom up/down/total color) so the XSS tests run against
the waterfall marks (§5.5d). `WATERFALL_CASES = ["basic","intermediate-sums","profit-bridge","themed-dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/waterfall/examples/intermediate-sums.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="waterfall",
    title="Monthly Cash Flow",
    x_axis=Axis(title="Driver", categories=["Opening", "Sales", "Refunds", "Payroll", "Marketing", "Interest"]),
    y_axis=Axis(title="Cash (thousands)"),
    series=[Series("Cash flow", [120, 85, -18, -46, -22, 9])],
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
- **Hover a bar** → tooltip (stage, delta, running total) + bar highlight + crosshair.
- **Click a legend swatch** → toggle the whole waterfall series on/off.
- **Keyboard** → arrows walk the bars; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — bars filled, connectors
  drawn, totals readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) and always includes 0 as the baseline
  total/subtotal bars anchor to, unless `yAxis.min/max` clamp it. The domain
  covers the full **cumulative** path, so a bar that overshoots the biggest single
  delta still fits.
- Bars use the **band** x-scale (`x_scale="band"`) — stages occupy equal bands;
  labels land under band centers.
- Direction colors come from `upColor`/`downColor`/`totalColor` (defaulting to the
  theme's up/down/total accents), **not** `series[].color`; a gradient/pattern
  direction color fills the bar via the `<defs>` pre-pass.
- Waterfall reuses the exemplar substrate (`_cartesian.py` / `cartesian.go`)
  column triggered — never forked. Its only net-new pieces are the running-total
  transform and the connector-lines primitive.

## Not yet supported (roadmap)

- Live renderers (`waterfall.py` / `waterfall.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **Per-point `isSum` / `isIntermediateSum` object model** — arrives with the Rank
  3 point-model generalization + the §5.4b five-place lockstep; until then the
  chart-level `sumIndices` / `intermediateSumIndices` companions carry the flags and
  the pure-delta goldens stay frozen.
- **Horizontal waterfall** — falls out of the orientation transpose (shared with
  bar / column-range), a later variant.
- Stacked / grouped multi-series waterfalls, per-stage color overrides, and
  negative-total color zones — variants layered on this base.
