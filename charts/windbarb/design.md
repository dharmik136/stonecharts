# Chart: Windbarb (`windbarb`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file copies the
> [`column`](../column/design.md) exemplar (itself modeled on
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the sibling
> build detail: the `{speed, direction}` point model, the wind-barb glyph mark
> (feathers + rotation), the fixed lane, the reused datetime axis and chrome, the
> parity traps, and the a11y DOM contract.

- **Chart id:** `windbarb`
- **Spec `type`:** `"windbarb"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Src:** HC · a later Family A
  sibling (beyond the §3.3 rank-1–13 core sequence — like `timeline`, `dumbbell`,
  and `xrange` it rides substrate the ranked siblings already generalized)
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; windbarb rides the shared cartesian frame once
  the datetime axis + `{speed, direction}` point model land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2 Family A (Windbarb), §3.2, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/windbarb.py` · `libs/go/windbarb.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Reuses:** [`charts/candlestick`](../candlestick/design.md) (the `datetime` band axis) ·
  [`charts/combo`](../combo/design.md) (the composition layer, when co-plotted in a meteogram)
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A windbarb chart: one series drawn as **one meteorological wind-barb glyph per
time point**, each encoding two values — **wind speed** and **wind direction** —
placed along a shared **datetime** x-axis. Every barb sits on **one fixed
horizontal lane**; the glyph — a staff with feathers/flags — encodes the **speed**
(number and kind of feathers, per the meteorological convention) and the whole
glyph is **rotated** to show the **direction** the wind blows *from*. A speed below
the calm threshold renders as a small open **calm circle** (no staff). Each barb is
the hoverable, interactive element (it replaces the line chart's point markers).

Windbarb is a Family A **sibling**. It reuses the **datetime band axis** (from
`candlestick`), the plot area, and all chrome, and adds two small pieces: a
**`{speed, direction}` point model** (a datum richer than a single `y`, which
`number[]` cannot express) and the **barb-glyph mark** (a `<g>` of a staff +
feathers, oriented by an SVG `rotate` transform — **no trig in either language**,
see the parity traps). It is **most often a companion series in a meteogram** — a
`combo` co-plotting a temperature spline, a pressure line, and a windbarb strip on
one shared time axis (the composition layer, blueprint §3.2).

## Use it when

- Your x is a run of **timestamps** (hourly forecast, buoy/station observations,
  a flight/marine track) and each point has a **wind speed and a wind direction**
  you want to read **at a glance** — the classic meteorological barb row.
- You want direction and speed **without spending a y-axis on either** — the barb
  glyph carries both, so the row can sit as a thin strip **above a temperature
  spline / below a pressure line** in a meteogram.
- Rows look like: `time -> {speed, direction}`.

Do **not** use it for: a plain **speed trend** over time (use `line-basic`),
**direction frequency** as a polar rose (use `wind rose`, Family B — Polar),
a generic **vector field** where every arrow's *length* also encodes magnitude at
an arbitrary `(x,y)` (use `vector plot`), or **category counts** (use `column`).
See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the time labels, length `N` (absent → index `0..N-1`; a
  `datetime` axis carries ISO timestamp strings here). One barb per category.
- `series[].data`: `N` numbers — the **wind speed** per time point (the
  representative `number[]`, validator-compatible; see **Data model**).
- `series[].direction`: `N` numbers — the **wind direction** in degrees, parallel
  to `data` by index (the forward-compatible companion the marks rotate by).
- **The value payload is richer than `number[]`.** A barb needs speed **and**
  direction per point; a bare number cannot express it (the point-model
  generalization, blueprint §3.2, lands with this type). See **Data model** for how
  the payload is carried today (validator-compatible) vs. after the point model lands.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"windbarb"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (the swatch is a miniature barb; one entry per series) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (one row per time point carrying **both** speed and direction — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`speedUnit`** | string | `kt` | **NEW field.** The wind-speed unit for the tooltip/label and the feather convention: `kt` (knots), `mps` (m/s), `mph`, `kmh`. Feather increments always follow the meteorological convention in the barb's native unit — **half-barb = 5, full-barb = 10, pennant/flag = 50** — so a 25 kt barb is two full barbs + one half regardless of `speedUnit` label |
| **`calmThreshold`** | number | `2` | **NEW field.** Speeds `< calmThreshold` render as the **calm** glyph (a small open circle at the anchor, no staff), matching station-model convention. In the barb's native unit |
| **`hemisphere`** | string | `N` | **NEW field.** Which side the feathers sit on: `N` (Northern — feathers/flags on the **right** of the staff) or `S` (Southern — mirrored to the **left**). A single sign flip on the feather offset; no trig |
| **`barbLength`** | number | `20` | **NEW field.** Staff length of the barb glyph in px (feather spacing scales with it). The glyph is a fixed pixel size — it does **not** stretch to a band width |
| **`yOffset`** | number | `0` | **NEW field.** Pixel offset of the barb **lane** from the plot-area vertical center (`laneY = plot_y + plot_h/2 + yOffset`). Lets a meteogram place the barb strip near the top or bottom while a spline uses the rest of the plot |
| `xAxis.title` | string | — | axis label |
| `xAxis.type` | string | `category` | `category` (band labels) or `datetime` (labels are ISO timestamps; still laid out on the band scale — one slot per point, evenly spaced) |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (one per time point) |
| `yAxis.title` | string | — | axis label. **The barb never maps its value to a y-position** (see **Data model**); the value axis is a decorative/reference speed scale and is commonly hidden in a meteogram |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the reference speed range; the value axis is 0-anchored (`include_zero=True`) because speed is a non-negative magnitude |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | **wind speed** per time point, length `N` (the representative payload; validator-compatible today — see **Data model**) |
| `series[].direction` | number[] | — | **NEW field (forward-compatible companion).** `N` wind directions in **degrees** (0–360, meteorological "**from**" bearing: `0`/`360` = N, `90` = E, `180` = S, `270` = W), aligned to `data`. Carries the direction the marks rotate by while `data` stays `number[]` (see **Data model**) |
| `series[].color` | string \| gradient | palette by index | the **barb stroke** (staff + feathers): hex `#2f7ed8`, or a gradient object (legend swatch uses stop 0). A pattern is inert (a barb is stroked line-work, not a filled area) |

Fields carried over from the line spec but **inert** for windbarb (no line/area to
draw): `fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`, `marker`,
`pattern` are accepted by the shared validator (forward-compatible) but not
consumed by the windbarb marks (the barb staff uses a fixed stroke width). Full
schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** each time point carries **two** numbers `{speed, direction}`
  — the windbarb datum. This is a `{speed, direction}` **point model** (a
  specialization of blueprint §3.2), richer than the single-`y` `number[]`
  line/column use.
- **Carried today (validator-compatible):** the strict validator still requires
  `series[].data` to be `number[]` (the point model lands with this type, not
  before). So each example keeps `series[].data` as the **speed** series (which the
  a11y fallback / data table can render meaningfully) and carries **direction** in
  the **forward-compatible `series[].direction` companion** — a parallel `number[]`
  the validator ignores (exactly the pattern `error-bar` uses for `low`/`high`). The
  example specs in this folder use exactly this encoding, and each passes
  `validate() == []`.
- **After the point model lands:** `series[].data` **becomes** the array of
  `{speed, direction}` datums (positional `[speed, direction]` is sugar); `direction`
  folds into `data`; the validator + both spec models gain the datum shape in the
  §5.4b five-place lockstep; and the accessible data table generalizes off `number[]`
  in lockstep (§5.4b-DT). A bare number stays valid elsewhere (line/column goldens
  never move).
- **No value → y-position mapping (the defining trait).** Unlike `column`
  (value → bar height) or `candlestick` (value → floating body), the windbarb does
  **not** position its datum on the value axis. **Every barb sits on the SAME
  lane** — `laneY = plot_y + plot_h/2 + yOffset` — and the **speed is read from the
  glyph** (feathers), the **direction from its rotation**. The value axis is
  therefore a decorative/reference speed scale (or hidden in a meteogram). The frame
  is still built with **`include_zero=True`** only so a shared/secondary axis has a
  defined 0-based speed domain; the barb marks never call `ypix` for positioning.
- **Speed → feathers (the meteorological decomposition).** Split the speed into
  flags, full barbs and half barbs with **integer arithmetic** (parity-safe): round
  the speed to the nearest 5 first (`s5 = round(speed / 5) * 5`), then
  `flags = s5 // 50`, `full = (s5 % 50) // 10`, `half = (s5 % 10) // 5`. A calm barb
  (`speed < calmThreshold`) draws none of these — just the calm circle.
- **The frame owns the y-domain.** `nice_ticks` over the speed data with 0 forced in
  (`include_zero=True`). The marks never recompute a scale.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2):

```python
# libs/python/peakcharts/charts/windbarb.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Windbarb", "band", _windbarb_marks)   # include_zero defaults True
```
```go
// libs/go/windbarb.go — package peakcharts
func renderWindbarbSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Windbarb", "band", windbarbMarks, true)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one `.pk-point` group per time point** wrapping the
staff + feathers (or the calm circle), rotated to the wind direction:

```html
<g class="pk-series" data-series="0">
  <g class="pk-barb pk-point" data-series="0"
     data-series-name="Buoy 41010" data-x="09:00" data-y="25"
     data-speed="25" data-direction="220" data-color="#2f7ed8"
     data-r="3.5" data-r-hover="6"
     cx="128.4" cy="230.0"
     transform="rotate(220 128.4 230.0)">
    <line class="pk-staff" x1="128.4" y1="230.0" x2="128.4" y2="210.0"
          stroke="#2f7ed8" stroke-width="1.5"/>
    <line class="pk-feather" x1="128.4" y1="210.0" x2="135.4" y2="207.0"
          stroke="#2f7ed8" stroke-width="1.5"/>
    <line class="pk-feather" x1="128.4" y1="213.0" x2="135.4" y2="210.0"
          stroke="#2f7ed8" stroke-width="1.5"/>
    <line class="pk-feather-half" x1="128.4" y1="216.0" x2="131.9" y2="214.5"
          stroke="#2f7ed8" stroke-width="1.5"/>
  </g>
  … one .pk-barb.pk-point per time point (a calm point emits a single
    <circle class="pk-calm"> with no staff) …
</g>
```

- **Class:** `pk-barb pk-point`. `pk-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `pk-barb` is a
  purely-cosmetic CSS hook. The `.pk-point` here is a **`<g>`** because a datum needs
  several primitives (staff + feathers); the runtime's `querySelectorAll('.pk-point')`,
  `getAttribute('cx')`, and hover `setAttribute('r', …)` all operate harmlessly on a
  group. The barb **is** the hoverable point; there are no separate markers.
- **Anchor:** barb center `xc = fr.xpix(i)` (band center); lane
  `laneY = fr.plot_y + fr.plot_h/2 + yOffset` — a **fixed pixel**, the **same for
  every point** (the barb does not use `ypix` for positioning). Compute `xc` once and
  share it between the staff, the feathers and the `cx`/rotate.
- **Direction by SVG transform (NO trig).** Draw the whole glyph in a **canonical
  north-pointing local orientation** — staff straight **up** from the anchor
  (`x1=x2=xc`, `y1=laneY`, `y2=laneY - barbLength`), feathers/flags on the right
  (Northern hemisphere) — then rotate the `<g>` with
  `transform="rotate({fmt_num(direction)} {xc:.1f} {laneY:.1f})"`. SVG `rotate` is
  clockwise-positive in screen coords, and meteorological direction is the clockwise
  "from" bearing, so the emitted angle is the direction **verbatim** — a `220` wind
  blows **from** the SW and the staff points that way. **Both languages emit the same
  literal number; the browser does the rotation** — so there is no `sin`/`cos` to
  diverge across libms (see the parity traps).
- **Feathers (canonical, constant offsets).** Along the upper staff, spaced by a
  fixed `step`, from the tip inward: `flags` full-barbs first, then `full` full-barbs,
  then one `half`-barb. A **full barb** is a short line from the staff to
  `(xc + featherDX, y - featherDY)`; a **half barb** uses half the reach; a **flag/
  pennant** is a small filled `<polygon>` triangle. `featherDX`, `featherDY` and
  `step` are **fixed constants** (Southern hemisphere negates `featherDX`) — no
  per-point angle math, so all offsets format through `:.1f` identically.
- **Calm glyph:** when `speed < calmThreshold`, emit a single
  `<circle class="pk-calm" cx="{xc}" cy="{laneY}" r="{rCalm}" fill="none"
  stroke="{color}"/>` (no staff, no rotation needed — a circle is rotation-invariant,
  but the `<g>` transform is harmless). Never leave a point unmarked (an empty point
  is a broken static chart — NN#2).
- **Stroke color:** read `fr.styles[si].stroke` (the resolved series paint —
  solid hex or `url(#grad)`); apply to the staff and every feather stroke, and to the
  flag polygon fill. Cycles the theme palette when `series[].color` is unset.
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx = xc` — the crosshair reads it —
  and by convention `cy = laneY`.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (reused VERBATIM from column / the blueprint)

Windbarb rides the **band** x-scale (`x_scale="band"`) — one slot per time point,
barb anchored at the band **center**. Evaluate the arithmetic in **exactly this
operation order** in both languages so `f1` / `:.1f` rounding lands ULP-for-ULP
identically (blueprint §3.2 / §4; the frame's `xpix` implements the band center):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center = barb center xc
```

- Windbarb is normally **single-series** — one barb per time point at the band
  center. It does **not** use the `groupW`/`barW` sub-band split (`PAD`, `K`): the
  barb glyph is a **fixed pixel size** (`barbLength`), not a bar whose width is a
  fraction of the band. Multi-series windbarb (rare — e.g. two stations) draws one
  barb per series at the **same** band center (differentiated by `color`); it does
  not fan them across sub-bands.
- Windbarb uses **no** `stacking`/`grouping` (there is nothing to stack — the barbs
  are glyphs on a fixed lane); those selectors are ignored for this type.
- A `datetime` x-axis still rides the **uniform band layout** (one slot per record,
  evenly spaced) — not a continuous time scale (roadmap).

## Reused chrome (obtained from the frame — never re-implemented)

Windbarb inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear speed y-scale via `nice_ticks` → `ypix` (with **`include_zero=True`** — a
  0-based speed reference domain the frame computes); y gridlines + labels. (The barb
  marks never call `ypix`; the axis is a reference scale.)
- Categorical / datetime x-axis via the **band** `xpix`; the shared x-label loop
  lands labels under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle`, id-scoping
  via `cid` (defs emitted only when a series needs them — no empty `<defs>` under the
  light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=True` (0-based speed
reference axis). It passes the bare noun **`"Windbarb"`** — the frame expands it to
`"Windbarb chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Rotation via `transform`, NOT trig (the headline trap).** Do **not** compute
  the staff/feather endpoints with `sin`/`cos` on the direction in either language —
  `math.sin`/`math.Sin` are IEEE-754 but **not guaranteed bit-identical across
  libms**, so a rotated coordinate would diverge and fail byte-parity. Instead draw
  the glyph in canonical (north-up) local coords with **linear arithmetic only**
  (`:.1f`) and emit `transform="rotate({fmt_num(direction)} {xc:.1f} {laneY:.1f})"` —
  the **direction is formatted as a plain number** and the SVG engine rotates. Both
  languages emit the identical literal.
- **Speed decomposition is INTEGER arithmetic.** `s5 = round(speed/5)*5`;
  `flags = s5//50`; `full = (s5%50)//10`; `half = (s5%10)//5`. Pin the rounding rule
  (round-half-to-even vs half-up) **identically** in both languages, or a 22.5 kt wind
  gets a different feather count. Prefer computing on integers to avoid float `%`.
- **Fixed lane, not `ypix`.** `laneY = plot_y + plot_h/2 + yOffset` is the **same
  pixel for every point** and is computed from frame fields with plain arithmetic; the
  marks must **not** call `fr.ypix` for the barb position (that would map value → y and
  is not what a windbarb does).
- **Feather constants are literals, not per-point.** `featherDX`, `featherDY`, `step`,
  `rCalm`, staff stroke width are **fixed constants** identical in both languages;
  Southern hemisphere negates `featherDX` (a sign flip), nothing else.
- **Band arithmetic ORDER** — evaluate `bandWidth = plot_w/n` then
  `xpix(i) = plot_x + bandWidth*i + bandWidth/2` in that exact order; a reassociated
  form diverges after `f1` rounding.
- **`data-*` carries both values** — `data-speed` and `data-direction` via
  `fmt_num`, plus `data-y = speed` for the base tooltip; every user string via `esc`.
  A leaked raw `<` fails the XSS tests.
- **Calm glyph rule** — pin `speed < calmThreshold` (strict `<`) identically so the
  same points become circles in both languages.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>` under
  the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` and the per-point arrays by index (never range-over-map);
  keep series/point/legend `data-series` indices in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the selectors
+ `data-*` below (`spec/svg-contract.md`). Emit them correctly and tooltip,
highlight, crosshair, legend-toggle, and keyboard nav all work with **zero JS
changes**.

- **Series group:** `.pk-series[data-series=N]` — one per series; `N` is the integer
  series index, **consistent** across the group, its points, and the legend item (do
  not renumber).
- **Datum mark:** `.pk-barb.pk-point` (a `<g>`) carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover`
  (mandatory even though a `<g>` ignores the hover `r`), **plus** the windbarb
  extension `data-speed` and `data-direction`.
- **Crosshair anchor:** every `.pk-point` carries a `cx` (barb center) and by
  convention `cy = laneY`.
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(speed))`;
  `data-speed = esc(fmt_num(speed))`; `data-direction = esc(fmt_num(direction))`;
  `data-color = fr.styles[si].solid` (already escaped); `data-r`/`data-r-hover =
  fmt_num(...)`. Pixel attrs (`cx,cy,x1,y1,…`) and the rotate pivot use `:.1f`/`f1`;
  the rotate angle uses `fmt_num`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG; a
  separate **visually-hidden data table** in the HTML with **one row per time point
  carrying both speed and direction** (the data table generalizes off `number[]` in
  lockstep in both languages — §5.4b-DT — since the datum is no longer a single
  number); keyboard nav walks barbs. `a11y:false` restores the pre-a11y bytes.
- **Static-first:** the chart is fully readable with JS disabled — barbs are
  server-rendered and stroked; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "windbarb",
  "title": "Coastal Wind — Station KBOS",
  "subtitle": "Hourly wind barbs (speed + direction), knots",
  "speedUnit": "kt",
  "xAxis": {
    "title": "Hour (local)",
    "categories": ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00"]
  },
  "yAxis": { "title": "Wind speed (kt)" },
  "series": [
    {
      "name": "KBOS surface wind",
      "data":      [5, 12, 18, 25, 33, 0, 47, 55],
      "direction": [200, 210, 225, 220, 240, 0, 260, 255]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, category x-axis, default `kt`/Northern hemisphere; speeds spanning half/full/flag feathers plus one **calm** point (`speed < calmThreshold`) |
| [`examples/datetime.json`](examples/datetime.json) | `xAxis.type:"datetime"` (ISO timestamps) + `speedUnit:"mps"`; a day of buoy wind |
| [`examples/southern-hemisphere.json`](examples/southern-hemisphere.json) | `hemisphere:"S"` (mirrored feathers) + `yOffset` (barb strip placement) + custom series `color` — the meteogram-strip configuration |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `speedUnit:"mph"` + custom barb color + a tightened `calmThreshold` |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom barb color) so the XSS tests run against the
windbarb marks (§5.5d). `WINDBARB_CASES = ["basic","datetime","southern-hemisphere","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/windbarb/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="windbarb",
    title="Coastal Wind — Station KBOS",
    x_axis=Axis(title="Hour (local)", categories=["06:00", "07:00", "08:00", "09:00"]),
    y_axis=Axis(title="Wind speed (kt)"),
    series=[
        # direction travels in the forward-compatible `direction` companion until the
        # point model lands; `data` carries the speed series so the spec validates.
        Series("KBOS surface wind", [5, 12, 18, 25]),
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
- **Hover a barb** → tooltip (time, series, speed, direction) + barb highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the barbs; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — barbs stroked and readable.

## Rendering notes

- The **value axis is a reference speed scale**, not a positional encoding: barbs
  sit on a fixed lane and read speed from feathers. `include_zero=True` gives a
  0-based speed domain (for a shared/secondary axis in a meteogram); in a standalone
  windbarb the axis is commonly hidden.
- Barbs use the **band** x-scale (`x_scale="band"`) — each time point occupies one
  equal slot; labels land under band centers. A `datetime` x-axis rides the same
  uniform band layout (one slot per record, evenly spaced), not a continuous time
  scale.
- Direction is applied as an SVG `rotate` **transform** (no trig) — the barb is drawn
  north-up canonically and the whole glyph is rotated to the meteorological "from"
  bearing.
- Colors cycle the theme palette when `series[].color` is unset; a gradient strokes
  the barb via the `<defs>` pre-pass.
- Windbarb is **most useful co-plotted**: as a `combo` meteogram companion (spline +
  windbarb + column + error-bar on one time axis) the barb strip sits on its
  `yOffset` lane while the primary series own the value axis (the composition layer,
  blueprint §3.2 / §3.3 Rank 6).

## Not yet supported (roadmap)

- Live renderers (`windbarb.py` / `windbarb.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Landing them consumes the
  `{speed, direction}` point model (blueprint §3.2) under the §5.4b five-place field
  lockstep + the §5.4b-DT data-table generalization + a byte-identity gate.
- A true **continuous datetime x-scale** (non-uniform spacing by real timestamps) —
  today `datetime` labels ride the uniform band layout.
- **Meteogram composition** (spline + column + windbarb + error-bar on one plot with
  shared/secondary axes) — the `combo` composition layer (blueprint §3.3 Rank 6);
  today each windbarb example is a standalone strip.
- **Color-by-speed** barb shading, gust barbs (a second feathered tick), and a
  **speed-scale legend** (feather key) — later variants layered on this base.
