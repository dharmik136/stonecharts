# Chart: Technical indicators & overlays (`technical-indicators`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** ([`charts/column/design.md`](../column/design.md), itself a copy of
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the sibling
> build detail: the base-plus-derived data model, the transform layer
> (SMA/EMA/Bollinger/MACD/RSI/VWAP), the extra line/band/flag marks, the plot
> band/line chrome, the oscillator pane, the reused chrome, the parity traps, and
> the a11y DOM contract.

- **Chart id:** `technical-indicators`
- **Spec `type`:** `"technical-indicators"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Src:** HC
- **Build order:** derived-overlay sibling — **not** one of the §3.3 core ranks
  (1–13). It is built **after** the generalizations it composes land:
  **Combo** (r6 — composition-layer / secondary axis), **Area** (r5) +
  **Arearange** (r10 — band-fill between two data paths), and **Candlestick**
  (r8 — flags/events). It introduces **no new substrate** — only a derived-series
  transform layer, plot-band/plot-line chrome, a flag mark, and an oscillator pane.
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; technical-indicators rides the shared
  cartesian frame once the composition-layer, band-fill, and transform layer land
  — see [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md)
  §2 Family A "Technical indicators & overlays", §3.2, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/technical_indicators.py` · `libs/go/technical_indicators.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Reuses:** [`charts/line-basic`](../line-basic/design.md) (path + markers + area) ·
  [`charts/combo`](../combo/design.md) (composition-layer + secondary axis) ·
  [`charts/arearange`](../arearange/design.md) (band-fill between two data paths) ·
  [`charts/candlestick`](../candlestick/design.md) (flags/events)
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A technical-indicators chart: **one base cartesian series** (a metric or price
line/area over an ordered/datetime x-axis) **plus derived series computed by
transforms** — moving averages (**SMA**, **EMA**), **Bollinger bands**, **VWAP**,
and the oscillators **MACD** and **RSI** — drawn **on** the base plot (overlays)
or **in an extra pane beneath it** (oscillators). It also layers **plot bands**
(shaded axis regions), **plot lines** (reference lines), and **flags** (event
markers) over the base plot.

Crucially, the overlays are **not authored as raw series** — they are **derived**
from the base series by a **transform layer** (blueprint §3.2 "derived-series
transforms"). You supply the base `data` and an indicator config
(`type` + `period`/params); the renderer synthesizes the overlay's y-values,
assigns it a `data-series` index, and draws it with the **existing** line / area /
band marks. This is a **composition** over Combo + Arearange + Candlestick — it
forks **no** renderer and adds **no** substrate.

## Use it when

- Your x is **ordered time** (days, sessions, intervals) and your y is a
  **continuous metric or price** you want to read **together with its own smoothed
  / statistical context** — a moving average, a volatility band, a momentum
  oscillator.
- You want **anomaly / regime overlays on a metric series** — e.g. p95 latency
  with a 7-point SMA + EMA and an SLO threshold `plotLine`, throughput with a
  Bollinger band to flag out-of-band spikes, or a price with an RSI pane to spot
  overbought/oversold turns.
- You want to **annotate events** on the trend (deploys, incidents, news) with
  **flags**, or **highlight windows** (an incident, a maintenance window) with a
  **plot band**.
- Rows look like: `time -> value` for the **base** series; the overlays and panes
  are *computed*, not supplied.

Do **not** use it for: a plain **trend** with no derived context (use
`line-basic`), an **OHLC** price glyph per window (use `candlestick`), two
independent **authored** measures of different units with no transform (use
`combo`), a **static (low,high) band you supply directly** with no indicator math
(use `arearange`), or **category counts** (use `column`). See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the time/interval labels, length `N` (absent → index
  `0..N-1`; a `datetime` axis carries ISO date strings here, as candlestick does).
- each `series[].data`: `N` numbers — the **base** metric/price aligned to
  `categories` by index. The **same** `number[]` payload line/column/combo use.
- each `series[].indicators`: the overlay/indicator configs computed **from** that
  base series (a **forward-compatible companion**, see **Data model**). The derived
  overlay y-values are **not** supplied — the transform layer produces them.
- **The data element type does NOT change.** The base payload stays `number[]`, so
  line/column goldens never move and the a11y `number[]` data table needs only the
  additive per-overlay generalization (§5.4b-DT applies **only** to the derived
  columns, not to a changed base element type).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"technical-indicators"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle; **one item per series, base and derived alike** (SMA, EMA, Bollinger, VWAP, MACD, RSI each get their own toggleable legend item + `data-series` index) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table with **one column per series (base + each derived overlay/oscillator)** (§5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | axis label |
| `xAxis.type` | string | `category` | `category` (band/point labels) or `datetime` (labels are dates; laid out on the shared point scale — one slot per record, evenly spaced) |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (one per record; both base and overlays align to them) |
| **`xAxis.plotBands`** | object[] | — | **NEW field.** Shaded **vertical** regions spanning a range of x. Each `{from, to, color, label?, opacity?}` (`from`/`to` are category **indices** or datetime strings). Rendered as `<rect class="pk-plotband">` **behind** all marks — frame chrome (§ Marks) |
| **`xAxis.plotLines`** | object[] | — | **NEW field.** Vertical reference lines at an x. Each `{value, color, width?, dashStyle?, label?}`. Rendered as `<line class="pk-plotline">` behind marks — frame chrome |
| `yAxis.title` | string | — | axis label (value / price) |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks) | clamp the base-pane value range. **The base value axis is NOT zero-anchored** — it spans the data (base + overlay extents, incl. Bollinger band edges), never forced to include 0 (a $150 price / a 200 ms latency must not anchor at 0). `include_zero=False` |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| **`yAxis.plotBands`** | object[] | — | **NEW field.** Shaded **horizontal** value regions. Each `{from, to, color, label?, opacity?}`. Rendered as `<rect class="pk-plotband">` behind marks — frame chrome. (In an oscillator pane, `pane: n` scopes the band to that pane's axis — e.g. RSI 30–70.) |
| **`yAxis.plotLines`** | object[] | — | **NEW field.** Horizontal reference lines at a value (an SLO threshold, VWAP anchor, RSI 30/70). Each `{value, color, width?, dashStyle?, label?, pane?}`. Rendered as `<line class="pk-plotline">` behind marks — frame chrome |
| **`panes`** | object[] | — (single base pane) | **NEW field.** Vertical split of the plot area into stacked panes. `panes[0]` = base pane; `panes[1..]` = oscillator panes. Each `{height?, min?, max?, title?}` (`height` = fraction or px). Absent → a single base pane; an oscillator indicator (`macd`/`rsi`) **auto-creates** `panes[1]` if none is declared. The **frame** owns each pane's value axis (§ Pane layout) |
| **`flags`** | object[] | — | **NEW field (chart-level).** Event markers anchored along the base plot. Each `{x, title, text?, color?, shape?}` (`x` = category index or datetime string; `shape` ∈ `flag`/`circlepin`/`squarepin`, default `flag`). Rendered as a `.pk-series` group of `.pk-point` flag glyphs (§ Marks) — hoverable |
| `series[].name` | string | `Series i` | legend + tooltip name (the **base** series name; each derived overlay is named `"<base> <IND>(<period>)"`, e.g. `"Price SMA(20)"`) |
| **`series[].type`** | string | `line` | **NEW field.** Base mark kind: `"line"` (path + markers) or `"area"` (path + fill down to the pane floor). Reused from the Area/Combo mark vocabulary. Overlays are **always** lines (or a band); this field styles only the base series |
| `series[].data` | number[] | — | the **base** metric/price values, length `N`. The overlays are derived from these, not supplied |
| **`series[].volume`** | number[] | — | **NEW field (forward-compatible companion).** Per-record volume, length `N`, aligned to `data`. **Required only for a `vwap` indicator** (VWAP is volume-weighted); ignored otherwise |
| **`series[].indicators`** | object[] | — | **NEW field.** The indicators/overlays derived from this base series. Each `{type, period?, color?, dashStyle?, params?, pane?}` — see **Data model** / **Derived-series transforms**. `type` ∈ `sma`/`ema`/`bollinger`/`vwap`/`macd`/`rsi`. Overlays (`sma`/`ema`/`bollinger`/`vwap`) draw on the base pane; oscillators (`macd`/`rsi`) draw in an oscillator pane |
| `series[].color` | string \| gradient | palette by index | the **base** series paint: line stroke (+ area fill for `type:"area"`) — hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object. Each derived overlay's color comes from its `indicators[].color` (else the next palette slot) |
| `series[].fillOpacity` | number | 0 | area fill opacity for a `type:"area"` base series (>0 fills under the base line) |
| `series[].pattern` | object | — | hatch fill for a `type:"area"` base area: `{type:hatch, color, background, size, angle, strokeWidth}` → `url(#pat)` |

Fields carried over from the line spec and consumed by the **base** series when
relevant (`lineWidth`, `dashStyle`, `step`, `curve`, `marker`); they are accepted
by the shared validator (forward-compatible) and shape only the base mark. Full
schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** every `series[].data` is `number[]` — one base value per
  record, the **same** shape line/column/combo use. **No** `{x,y}` / `{o,h,l,c}`
  object model; the derived context is *computed*, not a richer datum.
- **Derived series = transforms over the base.** Each entry in
  `series[].indicators` names a transform (`type`) and its parameters
  (`period`, …); the renderer runs the transform over the base `data` (and
  `volume` for VWAP) to synthesize the overlay's y-values, then draws it as an
  extra series. One base series may carry several indicators; each becomes its own
  toggleable series with the **next** `data-series` index (authored series first,
  then their derived overlays in `indicators` order, then oscillators, then flags).
- **Carried today (validator-compatible):** the strict validator requires only
  `series[].data` to be `number[]`; **`indicators`, `volume`, `flags`, `panes`,
  and the axis `plotBands`/`plotLines` are forward-compatible companions the
  validator ignores** (like candlestick's `ohlc` and arearange's `low`). So every
  example validates (`validate() == []`) while carrying the full overlay config,
  and the base `data` renders as a plain line/area under the fallback. The example
  specs in this folder use exactly this encoding.
- **After the transform layer lands:** `indicators`/`volume`/`flags`/`panes`/
  `plotBands`/`plotLines` gain validators + spec-model fields in the §5.4b
  five-place lockstep; the accessible data table generalizes to one column per
  derived series in lockstep (§5.4b-DT). The base `number[]` fast path is
  unchanged, so line/column/combo goldens never move.
- **The frame owns every axis domain.** The **base pane** axis spans the base
  series **and** every overlay it carries — including the Bollinger **band edges**
  (`min(all lowers) .. max(all uppers)`) and VWAP — with **`include_zero=False`**
  (a price/latency axis frames the data, not 0). Each **oscillator pane** has its
  own axis: MACD around 0 (`include_zero=True`, its histogram is baseline-anchored),
  RSI fixed **0..100**. `nice_ticks` still produces ~6 ticks per pane. The marks
  never recompute a scale.

## Derived-series transforms — the pinned math (parity-critical)

Every transform is **pure arithmetic over the base `data` in ascending index
order**. Pin the accumulation order, the seed, the population-vs-sample choice,
and the degenerate guard **identically in both languages** — a divergence here
corrupts the overlay y-values **before** any formatting, so byte-parity would fail
at the first overlay coordinate. Absent leading values (before a window fills)
are a **gap (null), never coerced to 0** (blueprint §3.2 point-model rule).

| Indicator | Params (default) | Output series | Pane | Formula (evaluate in index order) | Degenerate rule (pin BEFORE any divide) |
|-----------|------------------|---------------|------|-----------------------------------|------------------------------------------|
| **SMA** | `period` (20) | 1 line | base | `sma[i] = (Σ_{j=i-p+1..i} data[j]) / p` for `i ≥ p-1`; `i < p-1` → **gap** | none (p ≥ 1 required; p==0 → validation error) |
| **EMA** | `period` (20) | 1 line | base | `α = 2/(p+1)`; **seed** `ema[p-1] = SMA(data[0..p-1])`; `ema[i] = α·data[i] + (1-α)·ema[i-1]` for `i ≥ p`; `i < p-1` → **gap** | seed is the SMA of the first `p` (NOT `data[0]`) — pin identically |
| **Bollinger** | `period` (20), `stdDev` k (2) | band (upper↔lower) + mid line | base | `mid = SMA(p)`; `σ[i] = sqrt( (Σ_{j=i-p+1..i} (data[j]-mid[i])²) / p )` (**population** std — divide by **p**, not p−1); `upper = mid + k·σ`, `lower = mid - k·σ` | variance ≥ 0 by construction; still `clamp(var, ≥0)` **before** `sqrt` so a −0.0 float never feeds `sqrt` (Python raises / Go `NaN`) |
| **VWAP** | (session `anchor` optional) | 1 line | base | `vwap[i] = (Σ_{0..i} data[j]·vol[j]) / (Σ_{0..i} vol[j])` (cumulative) | if `Σvol == 0` at `i` → **gap** (guard the divide; Python would raise, Go yields `NaN` — pin the gap check first) |
| **MACD** | `fast` (12), `slow` (26), `signal` (9) | macd line + signal line + histogram | osc | `macd = EMA(fast) − EMA(slow)` (defined where both EMAs are); `signal = EMA(macd, signalPeriod)`; `hist = macd − signal` | subtraction only — no divide; the histogram is baseline-anchored at 0 (`include_zero=True` for the pane) |
| **RSI** | `period` (14) | 1 line | osc | `Δ[i]=data[i]−data[i-1]`; `gain=max(Δ,0)`, `loss=max(−Δ,0)`; **seed** `avgGain[p]=mean(gain[1..p])`, `avgLoss[p]=mean(loss[1..p])` (Wilder); then `avgGain[i]=(avgGain[i-1]·(p−1)+gain[i])/p`, likewise loss; `RS=avgGain/avgLoss`; `RSI = 100 − 100/(1+RS)` | if `avgLoss == 0` → `RSI = 100` (pin **before** the `avgGain/avgLoss` divide, identically in both languages) |

- **Gap semantics.** Leading indices where a window is not yet full emit **no
  point and no path vertex** (the path starts at the first defined index) — never
  a `0`. The a11y table renders those cells blank, not `0`.
- **`period == 0` / `period > N`.** A zero/negative period is a **validation
  error** (five-place lockstep, § New fields). A period larger than `N` yields an
  all-gap overlay (drawn as an empty series with a legend item, no vertices) —
  identically in both languages.
- **Float order is load-bearing.** Accumulate every Σ (SMA window, Bollinger
  variance, VWAP cumulative, EMA recurrence, RSI Wilder recurrence) in **ascending
  index order** in both languages so the `%g` 6-sig output matches ULP-for-ULP.
  Reassociating a sum diverges after `fmt_num`.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). Note `include_zero=False`
(the base value axis is not baseline-anchored):

```python
# libs/python/peakcharts/charts/technical_indicators.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Technical indicators", "point",
                            _ti_marks, include_zero=False)   # base price/metric axis spans the data
```
```go
// libs/go/technical_indicators.go — package peakcharts
func renderTechnicalIndicatorsSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Technical indicators", "point", tiMarks, false)
}
```

The callback is a **composition dispatcher** (like Combo). It iterates the
authored series **by index**, and for each: draws the **base** mark, then runs its
`indicators` transforms and draws each **derived overlay** — base-pane overlays
(SMA/EMA/VWAP lines, Bollinger band) and oscillator-pane series (MACD/RSI) — then
finally the **flag** markers. Each is exactly one `<g class="pk-series"
data-series="{si}">` (indices continue past the authored series):

```html
<!-- base metric (series 0) -->
<g class="pk-series" data-series="0">
  <path class="pk-series-line" data-series="0" d="M64.0 210.0 L112.0 198.0 …"
        fill="none" stroke="#2f7ed8" stroke-width="2"
        stroke-linejoin="round" stroke-linecap="round"/>
  <circle class="pk-point" data-series="0" data-series-name="Price"
          data-x="2024-06-03" data-y="153.4" data-color="#2f7ed8"
          data-r="3.5" data-r-hover="6" cx="64.0" cy="210.0" r="3.5" …/>
  … one .pk-point per record …
</g>

<!-- derived SMA(20) overlay (series 1) — starts at the first defined index -->
<g class="pk-series" data-series="1">
  <path class="pk-series-line pk-indicator" data-series="1" data-indicator="sma"
        d="M…" fill="none" stroke="#e0703c" stroke-width="1.5"/>
  … one .pk-point per DEFINED index (leading gap indices omitted) …
</g>

<!-- derived Bollinger band (upper↔lower) — arearange band-fill reused -->
<g class="pk-series" data-series="3">
  <path class="pk-series-range pk-band pk-indicator" data-series="3"
        data-indicator="bollinger" d="M…(upper L→R) L…(lower R→L) Z"
        fill="#9b8cf7" fill-opacity="0.15" stroke="none"/>
  … one .pk-point per index carrying data-low/data-high …
</g>

<!-- oscillator pane: RSI(14) line in panes[1] -->
<g class="pk-series" data-series="4">
  <path class="pk-series-line pk-indicator" data-series="4" data-indicator="rsi"
        d="M…" fill="none" stroke="#7a58c9" stroke-width="1.5"/>
  … one .pk-point per defined index, y via the pane-scoped ypix …
</g>

<!-- flags / events -->
<g class="pk-series pk-flags" data-series="5">
  <g class="pk-flag pk-point" data-series="5" data-series-name="Events"
     data-x="2024-06-06" data-y="Deploy v1.4" data-color="#5b8def"
     data-r="3.5" data-r-hover="6" cx="208.0" cy="72.0">
    <path class="pk-flag-glyph" d="M208.0 72.0 l0 -14 l28 0 l0 14 l-28 0 z"
          fill="#5b8def" stroke="#5b8def"/>
    <text class="pk-flag-label" x="222.0" y="62.0">Deploy v1.4</text>
  </g>
  … one .pk-flag.pk-point per event …
</g>
```

- **Class:** the base uses `pk-series-line`/`pk-point` (verbatim line); overlays
  add the cosmetic `pk-indicator` hook (+ `data-indicator="<type>"`); the Bollinger
  band reuses arearange's `pk-series-range pk-band`; a flag is a `<g class="pk-flag
  pk-point">`. `pk-point` is the **contract** class the runtime keys on
  (tooltip/highlight/crosshair/legend-toggle/keyboard) — the extras are pure CSS
  hooks (adding a class the runtime must *know about* is out of scope, NN#2).
- **Base mark:** verbatim the line renderer — `pts = [(fr.xpix(i), fr.ypix(v)) …]`,
  `d = _spline_d(pts)` if `curve:"monotone"` else `_path_d(pts, s.step)`; optional
  area fill down to the base-pane floor for `type:"area"`; markers via `_marker`.
- **Overlay lines (SMA/EMA/VWAP):** the **same** `_path_d` over the transform's
  y-values, thinner default stroke, markers **off** by default, **gap-aware** — the
  path starts at the first defined index; leading gaps emit no vertex.
- **Bollinger band:** reuse arearange's **band-fill** — one `<path>` = upper
  boundary `L→R` then lower boundary `R→L` then `Z` (both passes reuse `_path_d`/
  `pathD`, so `f1` coords match for free), plus an optional dashed **mid** line
  (another overlay). `data-low`/`data-high` on each `.pk-point`.
- **Oscillator series (MACD/RSI):** drawn against a **pane-scoped `ypix`** (the
  oscillator pane's own axis, § Pane layout). MACD's histogram is a baseline-
  anchored `<rect>` per index (column mark reused, anchored at the pane's
  `ypix(0.0)`); MACD/signal/RSI are lines. RSI uses the pane axis fixed 0..100.
- **Flags:** a `.pk-series` group of `.pk-point` flag glyphs anchored at
  `xpix(flagX)` on the base pane top; each is a small pennant `<path>` + `<text>`
  label. Hoverable (carries `data-x`/`data-y`=title/`data-series-name`).
- **Plot bands / plot lines are NOT marks — they are frame chrome (head).** The
  frame emits `<rect class="pk-plotband">` and `<line class="pk-plotline">` from
  `xAxis`/`yAxis` `plotBands`/`plotLines` **behind** every series (right after the
  gridlines, before the marks — the §4.1 head), scoped to the right pane axis.
  This is the one **new frame generalization** this chart forces (analogous to how
  Column forced band-layout); it is a shared-core change with its own parity tests,
  **not** something the marks emit.
- **`cx` / `cy`:** every `.pk-point` (base, overlay, band, oscillator, flag) MUST
  carry `cx` (the shared point x) — the crosshair reads it — and by convention `cy`.
- **Legend swatch:** the shared **tail** emits one legend item per series (base +
  each overlay + each oscillator + flags) with the matching `data-series` index —
  do not renumber and do not emit a legend from the marks.

## Pane layout — the pinned geometry

The base chart uses the **point** x-scale (`x_scale="point"`, like line) so
overlays and base share the exact vertex x's. When an oscillator (`macd`/`rsi`) is
present, the frame splits the plot area **vertically** into stacked panes. Pin the
split arithmetic in **exactly this order** in both languages so pane floors/ceilings
round ULP-for-ULP:

```
PANE_GAP  = 24.0                                   # px between panes (fixed constant)
oscFrac   = panes[1].height or 0.30                # oscillator pane height fraction
oscH      = (plot_h - PANE_GAP) * oscFrac
baseH     = (plot_h - PANE_GAP) * (1 - oscFrac)
basePane  : y ∈ [plot_y,               plot_y + baseH]                 # base ypix domain
oscPane   : y ∈ [plot_y + baseH + PANE_GAP, plot_y + plot_h]           # osc  ypix domain
```

- **No oscillator ⇒ one pane** = the full plot area (`baseH = plot_h`), byte-
  identical to a plain line/area chart with overlays.
- The **shared x** (`fr.xpix(i)`) is used by **every** pane — panes split y only.
- Each pane owns an independent value axis (its own `nice_ticks`): the base pane
  over base+overlay extents (`include_zero=False`), the MACD pane around 0
  (`include_zero=True`), the RSI pane fixed 0..100. The **frame** computes all of
  them; the marks read `fr.ypix` (base) / `fr.ypix_pane(k, v)` (oscillator) and
  never recompute a scale.
- `PANE_GAP = 24.0` and `oscFrac` default `0.30` are **fixed constants** unless a
  `panes[k].height` overrides the fraction — not per-mark choices.

## Reused chrome (obtained from the frame — never re-implemented)

Technical-indicators inherits, with **zero** re-implementation (§3.1, §4.2), the
**union** of what Line, Combo, and Arearange already reuse:

- Plot area + margins; x/y axes + axis lines + axis titles (per pane).
- Linear value y-scale via `nice_ticks` → `ypix` (base pane, `include_zero=False`;
  each oscillator pane its own domain — the **frame** computes every pane axis);
  y gridlines + labels.
- Point / datetime x-axis via `xpix`; the shared x-label loop lands labels under
  the vertices with no per-chart label code.
- Titles + subtitle; legend (bottom-center, one item per base + derived series);
  crosshair (shared across panes on the common x).
- Themes (light/dark/custom) resolved server-side; palette pickup (base + overlay
  colors).
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`/
  `stroke`/`area_fill`, id-scoping via `cid` (defs emitted only when a series needs
  them — no empty `<defs>` under the light theme).
- Line's `_path_d` / `_spline_d` / `_marker`; arearange's band-fill; combo's
  per-series dispatch + secondary axis — imported, **not** re-derived.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="point"` and **`include_zero=False`** (base
value axis frames the data). It passes the bare noun **`"Technical indicators"`**
— the frame expands it to `"Technical indicators chart with N series…"`
byte-for-byte.

**Net-new for this chart (the only additions over Line + Combo + Arearange):**
- **Derived-series transform layer** — SMA/EMA/Bollinger/VWAP/MACD/RSI computed
  from the base series (the parity-critical math above).
- **Plot-band / plot-line chrome** — axis-scoped background `<rect>`/`<line>`
  emitted by the frame head, behind marks (a shared-core generalization).
- **Oscillator pane** — a vertical plot-area split with a pane-scoped value axis
  (generalizes Combo's secondary axis from a right-side dual axis to a stacked
  pane).
- **Flag / event mark** — a `.pk-point` pennant glyph anchored on the x-axis
  (shared conceptually with Candlestick's flags/events).
- The new validated fields `series[].type`, `series[].indicators`,
  `series[].volume`, `flags`, `panes`, and axis `plotBands`/`plotLines`
  (five-place lockstep, § New fields).

## New fields — the five-place lockstep (§5.4b)

Each new field is a **validated spec field** and MUST be added in **five places,
in lockstep**, plus invalid fixtures — or you break non-negotiable #3 (strict
validation) and/or #1 (byte parity). The pattern is identical to Combo's
`series[].type` and Candlestick's `subtype`. Worked outline (do this for
**every** field below):

1. **Schema** (`spec/chart-spec.schema.json`): add the property under the right
   `definitions` node with `type` + `default` + `description`; keep
   `additionalProperties` open (forward-compatible).
2. **`validate.py`:** add a rule using the existing primitives so error text is
   identical — e.g. in `_series`, `if "volume" in v: ` iterate `_num` over the
   array; for `indicators`, validate it is an array of objects and each
   `type` is a string / `period` a number (reuse `_str`/`_num`, never bespoke
   errors). Defaults are **not** applied here.
3. **`validate.go`:** the exact mirror — same `$.path`, byte-identical wording.
4. **Spec model — Python** (`spec.py`): dataclass field + default, parsed in
   `from_dict` with **default-on-absence only** (never coerce).
5. **Spec model — Go** (`spec.go`): struct field with the right `json:` tag +
   `omitempty`/pointer semantics reproducing the Python default exactly; wire the
   default into `applyDefaults`.
6. **Invalid fixtures** (`charts/technical-indicators/invalid-fixtures.json`): ≥1
   hostile case per field, e.g. `{"series":[{"data":[1],"volume":["x"]}]}` →
   `"$.series[0].volume[0]: expected number, received string"`, and
   `{"series":[{"data":[1],"indicators":[{"type":5}]}]}` →
   `"$.series[0].indicators[0].type: expected string, received number"`, wired into
   both parity tests (§5.6c).

Fields to add: `series[].type` (string enum `line`/`area`), `series[].indicators`
(object[]), `series[].volume` (number[]), `flags` (object[]), `panes` (object[]),
`xAxis.plotBands`/`xAxis.plotLines`, `yAxis.plotBands`/`yAxis.plotLines`.

The **known-type** obligation (§5.0) also applies: register
`"technical-indicators"` in the validated known-type set in **both**
`validate.py` and `validate.go` (and the schema `type` enum + both dispatchers),
so an unknown/bogus top-level `type` is rejected **identically as a `SpecError`
before dispatch** (same `$.type` error text) instead of Python-raises /
Go-panics.

## Parity traps (verify before the byte-parity gate)

- **Transform accumulation ORDER** — every Σ (SMA window, Bollinger variance,
  VWAP cumulative, EMA/RSI recurrence) accumulates in **ascending index order** in
  both languages; a reassociated sum diverges after `fmt_num`. This is the single
  biggest trap — the overlay y-values are computed, not supplied.
- **EMA seed + α** — `α = 2/(p+1)`; seed `ema[p-1] = SMA(first p)` (**not**
  `data[0]`); pin both identically or the whole EMA path drifts.
- **Bollinger population std** — divide the squared-deviation sum by **`p`** (not
  `p−1`); `clamp(var, ≥0)` **before** `sqrt` so a −0.0 float never reaches `sqrt`
  (Python raises / Go `NaN`).
- **RSI zero-loss guard** — if `avgLoss == 0`, `RSI = 100` pinned **before** the
  `avgGain/avgLoss` divide, identically in both languages (Python would raise, Go
  yields `NaN`).
- **VWAP zero-volume guard** — if cumulative `Σvol == 0` at an index, emit a
  **gap** (checked **before** the divide) — do not divide `x/0`.
- **Gaps are omitted, not zero** — leading indices before a window fills emit **no
  vertex and no `.pk-point`**; never coerce to `0` (the path starts at the first
  defined index). Both languages skip the same indices.
- **`include_zero=False` (base pane)** — the base value axis spans base+overlay
  extents (incl. Bollinger band edges), **not** forced to 0. Passing `True`
  (column's value) would wrongly anchor a $150 price at 0 in **both** languages (a
  silent, byte-parity-passing bug — the flag must be explicit; blueprint §3.2
  caveat). The **MACD** pane is the opposite: `include_zero=True` (histogram is
  0-anchored). RSI is fixed 0..100.
- **Pane split ORDER** — evaluate the pane arithmetic in the pinned order with
  `PANE_GAP = 24.0` and `oscFrac` (default 0.30); a reassociated `(plot_h -
  PANE_GAP) * oscFrac` diverges after `f1` rounding.
- **`data-series` index continuity** — authored series first, then each series'
  derived overlays in `indicators` order, then oscillators, then flags. Assign
  indices **once**, in that order, in both languages; the legend/points must use
  the same index (never renumber, never range-over-map).
- **Band-fill = two `_path_d` passes** — Bollinger upper `L→R` + lower `R→L` + `Z`
  reuse the parity-locked `_path_d`/`pathD` → `f1` coords match for free.
- **Plot bands/lines are behind marks** — emitted in the frame **head** (after
  gridlines, before series), scoped to the correct pane axis; never in the marks.
  A band emitted after the marks would occlude the data in one language.
- **`data-*` values** — `data-y` carries the **raw** transform output at that
  index (via `fmt_num`); Bollinger points carry `data-low`/`data-high`; flags
  carry `data-y` = the event title; every user string via `esc`. A leaked raw `<`
  fails the XSS tests.
- **Formatters** — `cx,cy,x,y,width,height`, path `d` numbers via `:.1f`/`f1`;
  `data-y`, radii, opacity, stroke width via `fmt_num`/`fmtNum`; every user string
  via `esc`.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series`, `indicators`, and record arrays **by index** (never
  range-over-map); keep series/point/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes** — for base, overlay, band, oscillator, and flag alike,
because every one emits `.pk-point`.

- **Series group:** `.pk-series[data-series=N]` — one per series (base **and**
  each derived overlay/oscillator/flags group); `N` is the integer series index,
  **consistent** across the group, its points, and the legend item (do not
  renumber; assign in the pinned base→overlays→oscillators→flags order).
- **Datum mark:** `.pk-point` (a base/overlay `<circle|…>`, a band `<... >`, an
  oscillator mark, or a flag `<g>`) carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`
  — mandatory even for non-circular marks. Bollinger points add
  `data-low`/`data-high`; overlays add `data-indicator="<type>"`.
- **Crosshair anchor:** every `.pk-point` carries a `cx` (the shared point x) and
  by convention `cy`.
- **Escaping/formatting in `data-*`:** `data-series-name = esc(name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` (the raw transform
  output, or the flag title for a flag); `data-color =` the resolved solid;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML with **one column per
  series** — base + each derived overlay/oscillator — the table generalizing
  additively off `number[]` in lockstep in both languages (§5.4b-DT), with gap
  cells rendered blank (not `0`); keyboard nav walks every `.pk-point`.
  `a11y:false` restores the pre-a11y bytes.
- **Static-first:** the chart is fully readable with JS disabled — the base line/
  area, every overlay, the band fill, oscillator panes, plot bands/lines, and
  flags are all server-rendered; the crosshair ships `display:none`; the tooltip
  is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "technical-indicators",
  "title": "API p95 Latency with Moving Averages",
  "subtitle": "Base latency line + SMA(7) & EMA(7) overlays, SLO plot line",
  "xAxis": {
    "title": "Day",
    "categories": ["Jun 1","Jun 2","Jun 3","Jun 4","Jun 5","Jun 6","Jun 7","Jun 8","Jun 9","Jun 10","Jun 11","Jun 12","Jun 13","Jun 14"]
  },
  "yAxis": {
    "title": "p95 latency (ms)",
    "plotLines": [
      { "value": 250, "color": "#d65f5f", "width": 1.5, "dashStyle": "dashed", "label": "SLO 250ms" }
    ]
  },
  "series": [
    {
      "name": "p95 latency",
      "type": "line",
      "data": [186, 192, 205, 198, 221, 244, 233, 218, 226, 241, 258, 247, 231, 224],
      "color": "#2f7ed8",
      "indicators": [
        { "type": "sma", "period": 7, "color": "#e0703c" },
        { "type": "ema", "period": 7, "color": "#3f9b6a", "dashStyle": "dashed" }
      ]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | base latency **line** + **SMA(7)** & **EMA(7)** overlays on one pane + a **`yAxis.plotLine`** SLO threshold — the canonical moving-average overlay |
| [`examples/bollinger.json`](examples/bollinger.json) | base throughput line + a **Bollinger(10, 2)** band (arearange band-fill: upper↔lower) + its mid **SMA(10)** line + an `xAxis.plotBand` incident window |
| [`examples/rsi-pane.json`](examples/rsi-pane.json) | base price line on a **`datetime`** x-axis + an **RSI(14)** oscillator in a second **pane** with **`yAxis.plotBands`** at 30/70 (overbought/oversold) |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + base **area** series (gradient fill) + **VWAP** (with a `volume` companion) + **EMA(9)** overlays + **flags/events** markers + a `yAxis.plotLine` |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom base/overlay color, flag title/text) so the
XSS tests run against the technical-indicators marks (§5.5d).
`TECHNICAL_INDICATORS_CASES = ["basic","bollinger","rsi-pane","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/technical-indicators/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="technical-indicators",
    title="API p95 Latency with Moving Averages",
    x_axis=Axis(title="Day", categories=["Jun 1", "Jun 2", "Jun 3", "Jun 4"]),
    y_axis=Axis(title="p95 latency (ms)"),
    series=[
        # Overlays travel in the forward-compatible `indicators` companion until the
        # transform layer lands; `data` carries the base series so the spec validates.
        Series("p95 latency", [186, 192, 205, 198]),
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
- **Hover the base, an overlay, a band, an oscillator point, or a flag** → tooltip
  (x, series, y — plus low/high for a band) + mark highlight + crosshair across
  panes.
- **Click a legend item** → toggle that series on/off (base, any overlay, any
  oscillator, or the flags group).
- **Keyboard** → arrows walk the points; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — base, overlays, band,
  panes, plot bands/lines, and flags all server-rendered and readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) per pane. The base pane is **not**
  zero-anchored (`include_zero=False`) — a price/latency axis frames the data.
  The MACD pane is 0-anchored; the RSI pane is fixed 0..100.
- The base + overlays use the **point** x-scale (`x_scale="point"`, like line) so
  every overlay vertex shares the base vertex x. A `datetime` x-axis rides the same
  uniform point layout (one slot per record), not a continuous time scale.
- Overlays are **derived** — you supply the base `data` + an indicator config, and
  the transform layer computes the overlay y-values. Overlay colors come from
  `indicators[].color`, else the next palette slot.
- Plot bands/lines are **axis chrome** drawn behind the marks; flags are hoverable
  `.pk-point` markers; oscillators live in a stacked pane. The chart is a
  **composition** over the Line, Combo, and Arearange renderers — it forks none;
  the shared substrate is reused, never duplicated.

## Not yet supported (roadmap)

- Live renderers (`technical_indicators.py` / `technical_indicators.go`) —
  deferred; design + examples + validation are complete. Only `line` renders
  today. Landing them consumes the composition-layer (r6), band-fill (r10), and a
  new derived-series **transform layer**, under the §5.4b five-place field lockstep
  (for `type`/`indicators`/`volume`/`flags`/`panes`/`plotBands`/`plotLines`) + the
  §5.4b-DT data-table generalization.
- A true **continuous datetime x-scale** (non-uniform spacing by real timestamps)
  — today `datetime` labels ride the uniform point layout.
- **More indicators** (Stochastic, ATR, OBV, Ichimoku, Keltner, Donchian,
  PSAR, Aroon, Supertrend) — added to the transform-layer registry as each lands.
- **Overlaying on a candlestick base** (indicators on OHLC rather than a line) —
  once the `(o,h,l,c)` point model (Candlestick, r8) and this transform layer both
  land, VWAP/Bollinger etc. compute over the OHLC typical price.
- **Multiple oscillator panes** (MACD **and** RSI stacked) — the pane split
  generalizes to `panes[2..]` once one oscillator pane is proven.
- `drilldown`, log axis, zoom/pan window — variants layered on this base.
