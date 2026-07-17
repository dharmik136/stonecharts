# Chart: Financial — Candlestick / OHLC (`candlestick`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file copies the
> [`column`](../column/design.md) exemplar (itself modeled on
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the sibling
> build detail: the `(o,h,l,c)` point model, the wick + floating-body marks, the
> reused band layout and chrome, the parity traps, and the a11y DOM contract.

- **Chart id:** `candlestick`
- **Spec `type`:** `"candlestick"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 8** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; candlestick rides the shared cartesian frame
  once the `(o,h,l,c)` point model lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 8, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/candlestick.py` · `libs/go/candlestick.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A financial chart: one price series drawn as **one glyph per time window**, each
encoding four values — **open, high, low, close** (OHLC) — over a shared
categorical-or-datetime x-axis and a numeric price y-axis. The default subtype is
the **candlestick**: a thin **wick** `<line>` spanning `high → low` plus a
**floating body** `<rect>` between `open` and `close`. The body is colored **up**
when `close >= open` and **down** otherwise. Each candle is the hoverable,
interactive element (it replaces the line chart's point markers).

Candlestick is **build rank 8**. It introduces two reusable generalizations the
later range/waterfall siblings depend on: the **`(o,h,l,c)` point model** (a datum
richer than a single `y`, which `number[]` cannot express) and the **floating-bar
primitive** (a `<rect>` between two arbitrary y-values, **not** baseline-anchored)
— shared with `columnrange` (Rank 11) and `waterfall` (Rank 12). It also adds the
**wick line primitive** and the **up/down two-color legend**.

## Use it when

- Your x is a set of **time windows** (days, hours, sessions, buckets) and each
  window has a **min / max / first / last** — the classic **OHLC** summary of a
  price, an index level, or any metric aggregated per window (e.g. per-interval
  latency where you want open/high/low/close of the bucket).
- You want to see **direction** (up vs down window) and **range** (wick length) at
  a glance, not just a single closing value.
- Rows look like: `window -> {open, high, low, close}`.

Do **not** use it for: a plain **trend** of one value over time (use `line-basic`),
**category counts / magnitudes** (use `column`), a **(low,high) band with no
open/close** (use `arearange` or `columnrange`), or a **distribution** with
quartiles + whiskers (use `boxplot`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the window labels, length `N` (absent → index `0..N-1`; a
  `datetime` axis carries ISO date strings here). One candle per category.
- each `series[]`: `N` OHLC records aligned to `categories` by index.
- **The value payload is richer than `number[]`.** A candle needs four numbers per
  window; a bare number cannot express it (the point-model generalization,
  blueprint §3.2, lands with this rank). See **Data model** for how the payload is
  carried today (validator-compatible) vs. after the point model lands.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"candlestick"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle. The candlestick legend is a **two-swatch up/down key** (an up-colored + a down-colored body rect) rather than one per series |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (one row per window carrying **all four** O/H/L/C values — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`subtype`** | string | `candlestick` | **NEW field.** Which financial glyph to draw: `candlestick` (wick + floating body), `ohlc` (vertical high→low tick + left `open` / right `close` ticks), `hlc` (high→low tick + right `close` tick, no open), `heikin-ashi` (candlestick over the smoothed HA transform of O/H/L/C), `hollow` (candlestick whose body is **outlined** when `close >= prevClose` / filled otherwise). All subtypes share the band slot, the y-scale, and the up/down comparator |
| **`upColor`** | string \| gradient | theme up green | **NEW field.** Fill/stroke for an **up** window (`close >= open`). Absent → the theme's up color (light `#3f9b6a`) |
| **`downColor`** | string \| gradient | theme down red | **NEW field.** Fill/stroke for a **down** window (`close < open`). Absent → the theme's down color (light `#d65f5f`) |
| `xAxis.title` | string | — | axis label |
| `xAxis.type` | string | `category` | `category` (band labels) or `datetime` (labels are dates; still laid out on the band scale — one slot per record, evenly spaced) |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (one per window) |
| `yAxis.title` | string | — | axis label (price / level) |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks over `low..high`) | clamp the price range. **The price axis is NOT zero-anchored** — it spans the data's `min(low) .. max(high)`, never forced to include 0 (a $150 stock must not anchor at 0). `include_zero=False` |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the representative **close** series, length `N` (validator-compatible today; see **Data model**). After the point model lands this becomes the array of `{open,high,low,close}` datums |
| `series[].ohlc` | object[] | — | **NEW field (forward-compatible companion).** `N` records `{open, high, low, close}` aligned to `categories`. Carries the full OHLC payload the marks draw while `data` stays `number[]` (see **Data model**) |
| `series[].color` | string \| gradient | up/down by window | inert for candlestick unless `subtype` ignores up/down — the candle color comes from `upColor`/`downColor` keyed on `close >= open`, not a single per-series color |

Fields carried over from the line spec but **inert** for candlestick (no line to
draw): `fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`, `marker`,
`pattern` are accepted by the shared validator (forward-compatible) but not
consumed by the candlestick marks. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** each window carries **four** numbers `{open, high, low, close}`
  — the OHLC datum. This is the `(o,h,l,c)` **point model** (blueprint §3.2), a
  richer datum than the single-`y` `number[]` line/column use.
- **Carried today (validator-compatible):** the strict validator still requires
  `series[].data` to be `number[]` (the point model lands at this rank, not before
  — blueprint §3.3 Rank 8). So each example carries the OHLC payload in the
  **forward-compatible `series[].ohlc` companion** (an array of
  `{open,high,low,close}` objects the validator ignores), and keeps `series[].data`
  as the representative **close** series so the spec validates (`validate() == []`)
  and the a11y fallback / data table render a meaningful value. The example specs in
  this folder use exactly this encoding.
- **After the point model lands (Rank 3 → consumed here at Rank 8):**
  `series[].data` **becomes** the array of `{open,high,low,close}` datums (positional
  `[o,h,l,c]` is sugar); `ohlc` folds into `data`; the validator + both spec models
  gain the OHLC datum shape in the §5.4b five-place lockstep; and the accessible
  data table generalizes off `number[]` in lockstep (§5.4b-DT). A bare number stays
  valid elsewhere (line/column goldens never move).
- **Up / down classification:** a window is **up** iff `close >= open` (the `>=`
  makes a doji count as up), else **down**. The mark color is `upColor` / `downColor`
  resolved per window — **not** a single per-series color.
- **The frame owns the y-domain.** The price axis spans `min(all lows) .. max(all
  highs)` across every window (the frame's y-range extractor reads `low`/`high`, not
  just `close`), with **`include_zero=False`** — the value axis is **not** forced to
  0 (unlike column/bar). `nice_ticks` still produces ~6 nice ticks over that span.
  The marks never recompute a scale.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). Note `include_zero=False` (the
price axis is not baseline-anchored):

```python
# libs/python/stonecharts/charts/candlestick.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Candlestick", "band", _candlestick_marks,
                            include_zero=False)   # floating bodies — price axis spans low..high
```
```go
// libs/go/candlestick.go — package stonecharts
func renderCandlestickSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Candlestick", "band", candlestickMarks, false)
}
```

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series, and inside it **one `.sc-point` group per window** wrapping the wick
and the body:

```html
<g class="sc-series" data-series="0">
  <g class="sc-candle sc-point" data-series="0"
     data-series-name="ACME" data-x="Jan 2" data-y="153.4"
     data-open="150" data-high="154.2" data-low="149.1" data-close="153.4"
     data-color="#3f9b6a" data-r="3.5" data-r-hover="6"
     cx="128.4" cy="96.0">
    <line class="sc-wick" x1="128.4" y1="40.0" x2="128.4" y2="120.0"
          stroke="#3f9b6a" stroke-width="1"/>
    <rect class="sc-body" x="112.0" y="72.0" width="32.8" height="24.0"
          fill="#3f9b6a" stroke="#3f9b6a"/>
  </g>
  … one .sc-candle.sc-point per window …
</g>
```

- **Class:** `sc-candle sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `sc-candle` is a
  purely-cosmetic CSS hook. The `.sc-point` here is a **`<g>`** because a datum
  needs two primitives (wick + body); the runtime's `querySelectorAll('.sc-point')`,
  `getAttribute('cx')`, and hover `setAttribute('r', …)` all operate harmlessly on a
  group. The candle **is** the hoverable point; there are no separate markers.
- **Candlestick geometry (default subtype):**
  - **Band slot** from the layout below: candle center `xc = xpix(i)`; body
    `x = left(i, k)`, `width = barW` (single-series ⇒ `K = 1` ⇒ `width = groupW`).
  - **Wick** `<line>` at `x1 = x2 = xc`, `y1 = ypix(high)`, `y2 = ypix(low)`.
  - **Floating body** `<rect>` between open and close — **not** baseline-anchored:
    `y = ypix(max(open, close))` (the higher price is the smaller y-pixel — y grows
    downward), `height = |ypix(open) - ypix(close)|`.
  - **Doji (open == close):** the body has zero height; pin a **min-1px** rule
    identically in both languages — `height = max(|ypix(open) - ypix(close)|, 1.0)` —
    so the flat candle is still visible and Py == Go.
- **OHLC-bar subtype (`subtype:"ohlc"`):** no body rect. A vertical tick
  `<line>` `high → low` at `xc`, an **open** tick from `(left, ypix(open))` to
  `(xc, ypix(open))`, and a **close** tick from `(xc, ypix(close))` to
  `(right, ypix(close))`. `hlc` drops the open tick.
- **Up/down color:** `col = upColor if close >= open else downColor`, resolved to a
  concrete hex/`url(#…)` and applied to **both** the wick stroke and the body
  fill+stroke. `hollow` fills up-candles with `none` (outline only), keeping the
  stroke. Never leave a candle uncolored (a colorless financial glyph is a broken
  static chart — NN#2).
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (candle center `xc`) — the
  crosshair reads it — and by convention `cy = ypix(close)`.
- **Legend swatch:** the shared **tail** emits the **up/down two-swatch** key with
  `data-series` indices — do not emit a legend from the marks.

## Band layout — the pinned geometry (reused VERBATIM from column / the blueprint)

Candlestick rides the **band** x-scale (`x_scale="band"`). Evaluate the arithmetic
in **exactly this operation order** in both languages so `f1` / `:.1f` rounding
lands ULP-for-ULP identically (blueprint §3.2 / §4; the frame's `xpix` implements
the band center, the marks build the slot):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center = candle center xc
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
barW        = groupW / K
left(i,k)   = xpix(i) - groupW/2 + barW*k
```

- Candlestick is normally **single-series** ⇒ `K = 1` ⇒ one centered body of width
  `groupW`, wick at the band center. Multi-series (rare — e.g. two instruments) uses
  `K = len(series)` side-by-side slots, exactly like grouped column.
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author choices.
- Candlestick uses **no** `stacking` (bodies are floating O↔C ranges, not cumulative)
  — a stacked financial chart is meaningless; the `stacking`/`grouping` selectors are
  ignored for this type.

## Reused chrome (obtained from the frame — never re-implemented)

Candlestick inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear price y-scale via `nice_ticks` → `ypix` (over `low..high`, with
  **`include_zero=False`** — the frame computes the non-zero-anchored domain);
  y gridlines + labels.
- Categorical / datetime x-axis via the **band** `xpix`; the shared x-label loop
  lands labels under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center, up/down key); crosshair.
- Themes (light/dark/custom) resolved server-side; up/down palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and **`include_zero=False`** (floating
price range — the value axis is not anchored to 0). It passes the bare noun
**`"Candlestick"`** — the frame expands it to `"Candlestick chart with N series…"`
byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **`include_zero=False`** — the price axis must span `min(low)..max(high)`, **not**
  force 0 in. Passing `True` (column's value) would wrongly anchor a $150 candle to
  0 in **both** languages (a silent, byte-parity-passing bug — the flag must be
  explicit; blueprint §3.2 caveat).
- **Body geometry** — `y = ypix(max(open, close))`, `height = |ypix(open) -
  ypix(close)|`, evaluated in this order in both languages; the higher price is the
  smaller y-pixel. Never emit a negative `height`.
- **Doji min-1px rule** — `height = max(|ypix(open) - ypix(close)|, 1.0)` pinned
  **identically** in both languages before formatting, or the flat (open == close)
  candle vanishes in one language and diverges.
- **Up/down comparator** — `close >= open` (inclusive) is up; keep the `>=`
  identical in both languages so a doji classifies the same way and picks the same
  color.
- **Band arithmetic ORDER** — evaluate the seven lines above in that exact order; a
  reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1` rounding.
- **Wick vs body coordinates** — wick endpoints (`y1=ypix(high)`, `y2=ypix(low)`)
  and body corners use `:.1f`/`f1`; the candle center `xc` is shared by the wick
  (`x1=x2=xc`) and the body center — compute it once.
- **`data-*` carries all four values** — `data-open`/`data-high`/`data-low`/
  `data-close` via `fmt_num`, plus `data-y = close` for the base tooltip; every
  user string via `esc`. A leaked raw `<` fails the XSS tests.
- **Color resolution** — resolve `upColor`/`downColor` through the same
  gradient/pattern → `url(#…)` else solid-hex path used for bars; apply to **both**
  wick stroke and body fill+stroke. `hollow` sets up-body `fill="none"` but keeps the
  stroke — never a fully uncolored candle.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` and the OHLC records by index (never range-over-map); keep
  series/point/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the selectors
+ `data-*` below (`spec/svg-contract.md`). Emit them correctly and tooltip,
highlight, crosshair, legend-toggle, and keyboard nav all work with **zero JS
changes**.

- **Series group:** `.sc-series[data-series=N]` — one per series; `N` is the integer
  series index, **consistent** across the group, its points, and the legend item.
- **Datum mark:** `.sc-candle.sc-point` (a `<g>`) carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`
  (mandatory even though a `<g>`/`<rect>` ignores the hover `r`), **plus** the
  financial extension `data-open`, `data-high`, `data-low`, `data-close`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (candle center) and by
  convention `cy = ypix(close)`.
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(close))`;
  `data-open/high/low/close = esc(fmt_num(v))`; `data-color = ` the resolved up/down
  solid; `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG; a
  separate **visually-hidden data table** in the HTML with **one row per window
  carrying all four O/H/L/C values** (the data table generalizes off `number[]` in
  lockstep in both languages — §5.4b-DT — since the datum is no longer a single
  number); keyboard nav walks candles. `a11y:false` restores the pre-a11y bytes.
- **Static-first:** the chart is fully readable with JS disabled — candles are
  server-rendered and colored; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "candlestick",
  "title": "ACME Corp — Daily Price",
  "subtitle": "Candlestick, one bar per trading day",
  "subtype": "candlestick",
  "xAxis": {
    "title": "Session",
    "categories": ["Jan 2", "Jan 3", "Jan 4", "Jan 5", "Jan 8", "Jan 9", "Jan 10", "Jan 11"]
  },
  "yAxis": { "title": "Price (USD)" },
  "series": [
    {
      "name": "ACME",
      "data": [153.4, 152.6, 149.0, 151.2, 155.1, 153.8, 157.6, 156.4],
      "ohlc": [
        { "open": 150.0, "high": 154.2, "low": 149.1, "close": 153.4 },
        { "open": 153.4, "high": 156.0, "low": 152.0, "close": 152.6 },
        { "open": 152.6, "high": 153.1, "low": 148.4, "close": 149.0 },
        { "open": 149.0, "high": 151.8, "low": 148.2, "close": 151.2 },
        { "open": 151.2, "high": 155.5, "low": 150.9, "close": 155.1 },
        { "open": 155.1, "high": 156.3, "low": 153.0, "close": 153.8 },
        { "open": 153.8, "high": 158.0, "low": 153.5, "close": 157.6 },
        { "open": 157.6, "high": 159.2, "low": 156.1, "close": 156.4 }
      ]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | default `candlestick` subtype, category x-axis, single series, up/down default colors, wick + floating body |
| [`examples/ohlc.json`](examples/ohlc.json) | `subtype:"ohlc"` (bar ticks, no body) on a `datetime` x-axis |
| [`examples/heikin-ashi.json`](examples/heikin-ashi.json) | `subtype:"heikin-ashi"` + custom `upColor`/`downColor` config, category x-axis |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `subtype:"hollow"` + `datetime` axis + custom up/down colors + a **doji** (open == close) exercising the min-1px body rule |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom up/down color) so the XSS tests run against the
candlestick marks (§5.5d). `CANDLESTICK_CASES = ["basic","ohlc","heikin-ashi","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/candlestick/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="candlestick",
    title="ACME Corp — Daily Price",
    x_axis=Axis(title="Session", categories=["Jan 2", "Jan 3", "Jan 4", "Jan 5"]),
    y_axis=Axis(title="Price (USD)"),
    series=[
        # OHLC travels in the forward-compatible `ohlc` companion until the point
        # model lands; `data` carries the close series so the spec validates.
        Series("ACME", [153.4, 152.6, 149.0, 151.2]),
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
- **Hover a candle** → tooltip (window, series, O/H/L/C) + candle highlight + crosshair.
- **Click the up/down legend key** → toggle the series on/off.
- **Keyboard** → arrows walk the candles; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — candles colored and readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) over `min(low)..max(high)` and is **not**
  zero-anchored (`include_zero=False`) unless `yAxis.min/max` clamp it — a financial
  price axis frames the data range, not 0.
- Candles use the **band** x-scale (`x_scale="band"`) — each window occupies one
  equal slot; labels land under band centers. A `datetime` x-axis still uses the band
  layout (one slot per record, evenly spaced), not a continuous time scale.
- Up/down color comes from `upColor`/`downColor` keyed on `close >= open` — it does
  **not** cycle the series palette. Absent → the theme's up/down colors.
- Candlestick shares the **floating-bar primitive** with `columnrange` (Rank 11) and
  `waterfall` (Rank 12): once this rank lands the rect-between-two-y-values is reused,
  never forked.

## Not yet supported (roadmap)

- Live renderers (`candlestick.py` / `candlestick.go`) — deferred; design + examples
  + validation are complete. Only `line` renders today. Landing them consumes the
  `(o,h,l,c)` point model (blueprint §3.3 Rank 8) under the §5.4b five-place field
  lockstep + the §5.4b-DT data-table generalization + the Rank-3 byte-identity gate.
- A true **continuous datetime x-scale** (non-uniform spacing by real timestamps) —
  today `datetime` labels ride the uniform band layout.
- **Volume subpanel**, **flags/events** annotations, and **technical overlays**
  (SMA/EMA, Bollinger, MACD, RSI, VWAP) — later derived-series overlays layered on
  this base (blueprint Family A "Technical indicators & overlays").
- Real **Heikin-Ashi / hollow** transforms are specified here as `subtype`s; their
  smoothing/prev-close math lands with the renderer.
