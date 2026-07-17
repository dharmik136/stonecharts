# Chart: Error bar (`error-bar`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file copies the
> [`charts/line-basic/design.md`](../line-basic/design.md) template and follows
> the sibling exemplar [`charts/column/design.md`](../column/design.md), adding the
> sibling build detail: data model, marks, the pinned whisker geometry, reused
> chrome, parity traps, and the a11y DOM contract.

- **Chart id:** `error-bar`
- **Spec `type`:** `"error-bar"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 9** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; error-bar rides the shared cartesian frame once
  the point-model extraction lands — see [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 9, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/error_bar.py` · `libs/go/errorbar.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

An error-bar chart: each datum is drawn as a **vertical whisker** — a `<line>`
**stem** spanning `low → high`, centered on the point's x, capped by a **short
horizontal `<line>`** at each end — with the **center value `y`** marked by a
point on top. It encodes a magnitude **plus its uncertainty** (a confidence
interval, standard error, or percentile spread) around that magnitude.

Error bars are **typically an overlay** on a base line, column, or scatter mark,
not a standalone plot: the base mark shows the aggregate (`y`), the whisker shows
its `(low, high)` band. Rendered on its own, this chart draws the center marker
**and** the whisker itself.

Error bar is **build rank 9**. It forces one reusable generalization — the
**whisker-mark primitive** (one stem + two caps) — and extends the shared **point
model** with **`low`/`high` alongside a center `y`** (distinct from area-range /
column-range, which carry a *pure* `{low,high}` with no center value). It reuses
the band layout to center the whisker on a bar when overlaid on grouped columns.

## Use it when

- You have a **magnitude and its uncertainty** per category — a mean with a
  95% CI, an aggregate with a standard error, a p50 with a p05–p95 spread — and
  you want to show both the **point estimate** and the **interval** around it.
- You want to **overlay** interval bars on an existing line / column / scatter to
  qualify each aggregate with its confidence band.
- Rows look like: `label -> y, low, high` (a center value with a lower and upper
  bound; the bounds may be **asymmetric** about `y`).

Do **not** use it for: a **pure range with no center** (a p50–p95 latency band —
use `arearange`; a floating min–max column — use `columnrange`), a **trend** over
ordered x (use `line-basic`), **compare-across-categories** magnitudes with no
interval (use `column`), or a **full distribution** with quartiles + outliers
(use `boxplot`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers — the **center `y`** per category, aligned to
  `categories` by index (the same shape line/column use; the bare-number fast path).
- each `series[].low` / `series[].high`: `N` numbers — the lower and upper bound
  per category, aligned by index. These are the forward-compatible carrier for the
  `{y,low,high}` point model (see **Data model**); with them absent the chart
  degenerates to bare center markers.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"error-bar"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the series color) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (generalized to render `y / low / high` per point — see §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks over `min(low)…max(high)`) | clamp the y range; the value axis spans the **whisker extents** (`low..high`), not just the center `y` |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the **center `y`** per category, length `N` |
| **`series[].low`** | number[] | — (bare center markers) | **NEW field.** the **lower** bound per category, length `N`. The forward-compatible carrier for the `{y,low,high}` point model; added in the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) when Rank 9 lands |
| **`series[].high`** | number[] | — (bare center markers) | **NEW field.** the **upper** bound per category, length `N`. Same lockstep as `low`; `low[i] <= data[i] <= high[i]` is the intended shape (see parity traps for degenerate ordering) |
| `series[].color` | string \| gradient | palette by index | the whisker **stroke** + center-marker fill: hex `#2f7ed8`, or a `{type:linearGradient,…}` object (a 1px whisker takes the gradient's **stop-0 solid**; the legend swatch uses stop 0) |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:3.5}` | the center-value marker drawn on top of the whisker; `symbol` ∈ circle/square/triangle/diamond |

Fields carried over from the line spec but **inert** for error-bar (no filled area
or connecting line to draw): `fillOpacity`, `lineWidth`, `dashStyle`, `step`,
`curve`, `pattern` are accepted by the shared validator (forward-compatible) but
not consumed by the whisker marks — the stem/caps use a **fixed** whisker
stroke-width constant, not `lineWidth`. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — the **center `y`** per
  category, the same shape line/column use (the bare-number fast path). The
  `(low, high)` bounds ride two **parallel forward-compatible arrays**
  `series[].low` / `series[].high` (each length `N`).
- **Point model (`{y,low,high}`):** when Rank 9 lands the shared point-model
  extension (§4 / §3.3 Rank 9), each datum coalesces to a canonical
  `{y, low, high}` — a center value **plus** a low/high band. This is **distinct**
  from:
  - **area-range** / **column-range** — a *pure* `{low,high}` with **no center**
    (the band *is* the datum), and
  - **candlestick** — `{open,high,low,close}` (four values, up/down colored).
  A bare `number` stays valid (`y = number`, no whisker), so line/column goldens
  never move when the point model lands. The bare-number fast path is pinned in
  both languages (Python: numeric element → center-only datum; Go: a
  `UnmarshalJSON` that still decodes `[1,2,3]` to the same `[]float64`-equivalent
  bytes). Until then, examples use the parallel-array carrier and pass
  `validate() == []` (the bounds ride as forward-compatible keys).
- **Overlay semantics:** an error bar is typically **drawn on top of** a base
  line/column/scatter mark; the composition layer (rank 6, combo) co-plots the
  base series and the whisker on one plot. **Standalone** (these examples), the
  renderer draws the center marker **and** the whisker.
- **The frame owns the y-domain.** For the `{y,low,high}` range model the value
  axis spans **`min(low) … max(high)`** across all points (the range extractor,
  not the per-datum center), so a whisker never clips — the marks never recompute
  a scale. `nice_ticks` runs over that span; `yAxis.min/max` clamp it.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2):

```python
# libs/python/peakcharts/charts/error_bar.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Error bar", "band", _error_bar_marks)   # include_zero defaults True
```
```go
// libs/go/errorbar.go — package peakcharts
func renderErrorBarSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Error bar", "band", errorBarMarks, true)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it, **per (category, series)**: three whisker `<line>`s
(stem + low cap + high cap) followed by **one center `.pk-point`** marker:

```html
<g class="pk-series" data-series="0">
  <line class="pk-whisker pk-whisker-stem" data-series="0"
        x1="128.4" y1="300.0" x2="128.4" y2="96.0" stroke="#2f7ed8" stroke-width="1.5"/>
  <line class="pk-whisker pk-whisker-cap" data-series="0"
        x1="122.4" y1="96.0"  x2="134.4" y2="96.0"  stroke="#2f7ed8" stroke-width="1.5"/>
  <line class="pk-whisker pk-whisker-cap" data-series="0"
        x1="122.4" y1="300.0" x2="134.4" y2="300.0" stroke="#2f7ed8" stroke-width="1.5"/>
  <circle class="pk-point" data-series="0"
          data-series-name="p50 latency" data-x="/login" data-y="182"
          data-low="168" data-high="201"
          data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
          cx="128.4" cy="198.0" r="3.5" fill="#2f7ed8"/>
  … one whisker triplet + one .pk-point per category …
</g>
```

- **Class:** the center marker is `pk-point` — the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle / keyboard nav). The
  stem and caps are `pk-whisker` (+ `pk-whisker-stem` / `pk-whisker-cap`) — purely
  cosmetic CSS hooks (adding a class the runtime must *know about* is out of scope
  — NN#2). The whisker is the visual; the center point is the hoverable datum.
- **Whisker geometry:** `cx` is the point's center x from the band layout below;
  `stem` runs `(cx, ypix(low)) → (cx, ypix(high))`; each cap is a short horizontal
  `<line>` of half-width `CAP` centered on `cx` at the stem's ends. See the pinned
  geometry section — evaluate it in the same operation order in both languages.
- **Center marker:** the `<circle|rect|polygon>` at `(cx, ypix(y))` reuses the
  four existing marker symbols (`series[].marker.symbol`), drawn **on top of** the
  whisker (last, so it wins the z-order). This is the base mark for a standalone
  plot; when overlaid via combo it is the base series' own point.
- **Stroke color:** read `fr.styles[si].solid` — the resolved **solid** color — for
  both the whisker stroke and the center-marker fill. A 1px whisker line cannot
  take a gradient/pattern, so a gradient/pattern series color resolves to its
  **stop-0 solid** (the defs pre-pass still populates `.solid`). Error-bar never
  reads `fr.styles[si].fill` (that is the column bar-paint) and never reads
  `area_fill` (line's under-fill).
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (the whisker center x) — the
  crosshair reads it — and by convention `cy = ypix(y)` (the center-value pixel).
  Without `cx` the crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Whisker geometry — the pinned geometry (copied VERBATIM from the blueprint)

Evaluate the arithmetic in **exactly this operation order** in both languages so
`f1` / `:.1f` rounding lands ULP-for-ULP identically (blueprint §3.2 band layout +
§3.3 Rank 9; the frame's `xpix` implements the band center, the marks build the
sub-band center and the whisker):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
slotW       = groupW / K
cx(i,k)     = xpix(i) - groupW/2 + slotW*k + slotW/2  # sub-band CENTER (whisker sits on the bar center)

CAP         = 6.0                                     # cap HALF-width constant (px), fixed
yLow        = ypix(low)                               # LARGER pixel y (toward the bottom)
yHigh       = ypix(high)                              # SMALLER pixel y (toward the top)
yCtr        = ypix(y)                                 # center marker
stem        : (cx,        yLow)  ->  (cx,        yHigh)
capLo       : (cx - CAP,  yLow)  ->  (cx + CAP,  yLow)
capHi       : (cx - CAP,  yHigh) ->  (cx + CAP,  yHigh)
```

- Single series ⇒ `K = 1` ⇒ `cx(i,0) = xpix(i)` (the band center); the whisker
  sits dead-center in its category slot.
- `PAD = 0.2`, `K = len(series)`, and `CAP = 6.0` are **fixed constants**, not
  per-author choices. Multiple series ⇒ `K` sub-band centers per category so
  whiskers do not overlap; when the error bar **overlays grouped columns**, `cx`
  is the same sub-band center as the bar, so the whisker lands **on** the bar.
- `ypix` is monotonic (larger data value → smaller pixel y), so `yHigh <= yCtr <=
  yLow` for well-formed input. The frame's value axis already spans `low..high`
  (Data model), so no clamping is needed inside the marks.

## Reused chrome (obtained from the frame — never re-implemented)

Error-bar inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (over the **`low..high` range span** the
  frame computes); y gridlines + labels.
- Categorical x-axis via the **band** `xpix`; the shared x-label loop lands labels
  under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle` (`.solid`
  read for the whisker stroke), id-scoping via `cid` (defs emitted only when a
  series needs them — no empty `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (generalized to `y / low / high`, §5.4b-DT) + keyboard nav. Responsive `<svg>`
  viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=True`. It passes the
bare noun **`"Error bar"`** — the frame expands it to `"Error bar chart with N
series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Band / sub-band arithmetic ORDER** — evaluate the geometry block above in that
  exact order; a reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1`
  rounding. `cx(i,k) = xpix(i) - groupW/2 + slotW*k + slotW/2` (sub-band **center**,
  not the `left(i,k)` edge column uses).
- **`CAP` is a fixed half-width constant** — the cap spans `cx-CAP … cx+CAP`
  (total width `2*CAP`). Do not make it per-author or scale it with the band.
- **Frame owns the y-domain** — the marks call `fr.ypix` only; the value axis
  already spans `low..high`. Recomputing a scale (even to identical bytes) is a
  defect (NN, §7.1).
- **Stem direction** — `yLow = ypix(low)` is the **bottom** (larger pixel), `yHigh
  = ypix(high)` the **top**; emit the stem `yLow → yHigh` and do **not** swap or
  `min/max` them. If a caller supplies `low > high` (bad input), `ypix` inverts the
  whisker consistently in both languages — pin "draw as given" so Py==Go match; a
  future `low <= high` rule is enforced by the §5.4b field validation, not by the
  marks.
- **Whisker stroke reads `.solid`, not `.fill`** — a 1px line takes a solid stroke;
  a gradient/pattern series color resolves to its **stop-0 solid**. Reading `.fill`
  (column's bar paint) or `area_fill` (line's under-fill) is a bug.
- **`data-y` vs `data-low`/`data-high`** — `data-y` carries the **center** value;
  `data-low`/`data-high` carry the raw bounds (forward-compatible, surfaced in the
  a11y data table). All three go through `esc(fmt_num(...))`.
- **Formatters** — `cx, x1, y1, x2, y2, cy` via `:.1f`/`f1`; `data-y`, `data-low`,
  `data-high`, radii, offsets via `fmt_num`/`fmtNum`; every user string via `esc`.
  A leaked raw `<` fails the XSS tests.
- **Degenerate `low == high`** — the stem is zero-length and both caps land at the
  same y; that is valid (unlike candlestick's doji, no min-1px rule is needed).
  Pin "draw both caps at the same y" identically so Py==Go match.
- **Missing bounds** — a series with no `low`/`high` (or a `null` at index `i`)
  draws the **center marker only** (a gap in the whisker, never a whisker anchored
  at 0); pin the absent→gap rule identically in both languages.
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
  integer series index, **consistent** across the group, its whiskers/points, and
  the legend item (do not renumber). The legend toggle flips `display` on every
  `[data-series="N"]`; the whisker lines and the center point inherit from the
  group.
- **Datum mark:** the center `.pk-point` carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`
  — mandatory even though the whisker lines are cosmetic. `data-low`/`data-high`
  are added as forward-compatible attributes (surfaced in the data table).
- **Crosshair anchor:** every `.pk-point` carries a `cx` (whisker center x) and by
  convention `cy = ypix(y)` (center value).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(y))`;
  `data-low = esc(fmt_num(low))`; `data-high = esc(fmt_num(high))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`.
  Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks the
  center points. `a11y:false` restores the pre-a11y bytes. **The `data` element
  type changes** (a `{y,low,high}` datum, not a bare `number`), so the data table
  MUST be **generalized in lockstep in both languages** to render `y / low / high`
  per row — not a coerced single number — with a Py==Go table-bytes test
  (§5.4b-DT, NN#4). A future error-bar renderer may not ship an a11y-broken table
  while passing the golden gates.
- **Static-first:** the chart is fully readable with JS disabled — whiskers and
  center markers are server-rendered; the crosshair ships `display:none`; the
  tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "error-bar",
  "title": "Mean Request Latency with 95% CI",
  "subtitle": "Aggregated over the last 24h, by endpoint",
  "xAxis": { "title": "Endpoint", "categories": ["/login", "/search", "/checkout", "/profile", "/feed"] },
  "yAxis": { "title": "Latency (ms)" },
  "series": [
    {
      "name": "p50 latency",
      "data": [182, 240, 355, 128, 210],
      "low":  [168, 219, 331, 119, 193],
      "high": [201, 268, 384, 140, 233],
      "marker": { "enabled": true, "symbol": "circle", "radius": 4 }
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered whiskers, symmetric CI, center marker on top |
| [`examples/overlay-grouped.json`](examples/overlay-grouped.json) | 2 series, `grouping:true`, sub-band **centered** whiskers (the band-layout reuse — whiskers land on the bar) |
| [`examples/asymmetric.json`](examples/asymmetric.json) | asymmetric `low`/`high` about `y` (p05..p95 spread), `yAxis.min` clamp |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + custom whisker color + diamond center marker (chrome reuse + solid-stroke resolution) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom color) so the XSS tests run against the
error-bar marks (§5.5d). `ERROR_BAR_CASES = ["basic","overlay-grouped","asymmetric","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/error-bar/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="error-bar",
    title="Mean Request Latency with 95% CI",
    x_axis=Axis(title="Endpoint", categories=["/login", "/search", "/checkout", "/profile", "/feed"]),
    y_axis=Axis(title="Latency (ms)"),
    series=[
        Series("p50 latency", [182, 240, 355, 128, 210],
               low=[168, 219, 331, 119, 193], high=[201, 268, 384, 140, 233]),
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
- **Hover a center point** → tooltip (x, series, center y) + point highlight +
  crosshair; `low`/`high` are surfaced in the a11y data table.
- **Click a legend item** → toggle that series (whiskers + points) on/off.
- **Keyboard** → arrows walk the center points; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — whiskers + markers drawn
  and readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) over the **whisker extents**
  (`min(low)…max(high)`) so no bar clips; `yAxis.min/max` clamp it.
- Whiskers use the **band** x-scale (`x_scale="band"`) — categories occupy equal
  bands; multi-series whiskers occupy `K` sub-band centers so they do not overlap
  (and land on the bar when overlaid on grouped columns).
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color resolves to its **stop-0 solid** for the 1px whisker.
- Error-bar is a **point-model sibling**: it rides the same `_cartesian` substrate
  as column/line and adds **only** its whisker marks — never a fork.

## Not yet supported (roadmap)

- Live renderers (`error_bar.py` / `errorbar.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **Horizontal** error bars (the orientation transpose — whiskers along x).
- **Combo overlay** — error bars co-plotted on a base column/line/scatter via the
  composition layer (rank 6); today's examples are standalone whisker plots.
- The **five-place lockstep** for `low`/`high` (schema + both validators + both
  spec models + invalid fixtures) and the point-model byte-identity gate (Rank 9)
  land with the renderer; until then the bounds ride as forward-compatible arrays.
- `drilldown`, rotated x-labels, per-point cap-width overrides — variants layered
  on this base.
