# Chart: Column Range (`columnrange`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this recipe copies the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and swaps in
> the range-sibling build detail: the `{low,high}` point model, the floating-bar
> mark, the free (non-zero-anchored) value axis, the reused band layout + chrome,
> the parity traps, and the a11y DOM contract.

- **Chart id:** `columnrange`
- **Spec `type`:** `"columnrange"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 11** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; column range rides the shared cartesian frame
  once the point model + floating-bar primitive land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 11, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/columnrange.py` · `libs/go/columnrange.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A column range chart: one or more series drawn as **floating, low-to-high bars**
over a shared categorical x-axis and a numeric y-axis. Each bar spans a
`(low, high)` interval per category — it is **not** anchored to a zero baseline
the way `column` is; it floats between its two values. Bars are grouped
side-by-side (multi-series) inside the same band slots `column` uses. The bar is
the hoverable, interactive element (it replaces the line chart's point markers).

Column range is **build rank 11** — a late, cheap sibling. By the time it is
built, `candlestick` (rank 8) has already introduced the **floating-bar
primitive** (a `<rect>` between two arbitrary y-values) and `area-range`
(rank 10) has introduced the **`{low,high}` point model**. Column range reuses
both and forces **no net-new mark**: it is `column`'s band layout + the floating
bar + the range point model, wired together. Its one genuinely new configuration
is that it delegates with the **value axis free of the zero anchor**
(`include_zero=False`) — a floating band of `[95, 105]` must not waste the whole
axis down to 0.

## Use it when

- Your x is a set of **discrete categories** (days, endpoints, roles, racks) and
  each category has a **low–high interval** you want to show as a band: min–max,
  p10–p90, first–last, budget floor–ceiling.
- You want to compare **where each category's band sits and how wide it is**
  across categories, or compare a few series' bands within each category
  (grouped).
- Rows look like: `label -> (low, high)` (one range) or
  `label -> (low_a, high_a), (low_b, high_b)` (several series sharing one x).

Do **not** use it for: a single **magnitude** per category anchored at zero (use
`column`), a **band that also has a center value** to plot (use `errorbar`'s
`{y,low,high}` whisker, or overlay one), a **filled band over ordered/continuous
x** with no discrete slots (use `arearange`), or **open/high/low/close** market
data (use `candlestick`). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each series carries **two parallel `N`-length numeric arrays** — a **low** bound
  and a **high** bound — aligned to `categories` by index. `data[i]` pairs with
  `high[i]` to make the `i`-th category's floating band.
- **Interim validator-clean encoding (important).** The eventual canonical datum
  is the `{low,high}` point model with positional `[low,high]` sugar (blueprint
  §3.2 point-model row, §3.3 Rank 10/11), **shared with `area-range`**. Today's
  strict validator (`validate.py`/`validate.go`) still only accepts
  `series[].data` as `number[]`, so these examples encode the pair as
  **`data` = the low bounds** (the required, validator-covered array) **plus a
  parallel forward-compatible `high` array** for the high bounds. Both languages'
  validators ignore the unknown `high` key (forward-compatible), so every example
  passes `validate() == []` unchanged. When the point model lands, `data` becomes
  a `{low,high}` datum (positional `[low,high]` sugar), the two-array encoding is
  read into the same struct, and the accessible data table generalizes in lockstep
  (§5.4b-DT). A bare `number` in `data` stays valid (interpreted as `low` with an
  absent `high` → a degenerate zero-width band), so line/column goldens never move.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"columnrange"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the floating-bar `<rect>`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (generalized to render **both** low and high per row — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`orientation`** | string | `vertical` | **NEW field (forward-compatible).** `vertical` (default) → floating **columns**, value on y, categories on x (band). `horizontal` → floating **bars**, value on x, categories on y (band) — the orientation transpose (§3.2), which yields the horizontal bar-range **for free**. Selects the vertical/horizontal subtype. Wire it through the §5.4b five-place lockstep when the renderer lands |
| **`grouping`** | bool | true | **NEW field (forward-compatible).** `true` → `K = len(series)` side-by-side sub-bands per category (the pinned band layout, several bands per slot); `false` → `K = 1`, all series share one centered slot (overlaid, drawn in series order). Same selector `column` uses |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks over lows **and** highs; **0 NOT forced in**) | clamp the value range; unlike `column`, the value axis is **not** zero-anchored (floating bars) — see Rendering notes |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the **low** bounds, length `N` (interim encoding — see Data shape) |
| **`series[].high`** | number[] | — | **NEW field (forward-compatible).** the **high** bounds, length `N`, parallel to `data`; `high[i]` pairs with `data[i]` (low) to make category `i`'s band |
| `series[].color` | string \| gradient | palette by index | the **bar fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole floating bar; legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the bar: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line spec but **inert** for column range (no line to
draw, and ranges don't stack): `fillOpacity`, `lineWidth`, `dashStyle`, `step`,
`curve`, `marker`, and `stacking` are accepted by the shared validator
(forward-compatible) but not consumed by the column-range marks. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** each series is a `(low, high)` pair per category — `data` is
  the `number[]` of lows and `high` the parallel `number[]` of highs (interim
  encoding above; canonical `{low,high}` datum once the point model lands). There
  is **no center y** — this is the pure range model, distinct from the error-bar
  `{y,low,high}` center+range model (blueprint §3.3 Rank 9 vs Rank 10/11).
- **Grouped (default, `grouping:true`):** each category slot is split into
  `K = len(series)` equal sub-bands; series `k`'s floating bar sits in sub-band
  `k`. Basic single-series ⇒ `K = 1` ⇒ one centered floating bar of width
  `groupW`.
- **Overlaid (`grouping:false`):** `K = 1`; all series share one centered slot,
  drawn in series order (later series paint over earlier ones — use with distinct
  colors / opacity).
- **No stacking.** Ranges are not cumulative — `stacking` is meaningless here and
  is ignored if present (unlike `column`/`bar`/`area`). Each bar floats on its own
  `(low, high)`; the frame never computes a cumulative baseline for this chart.
- **The frame owns the value-domain, over BOTH bounds.** The value axis spans
  `nice_ticks(min(all lows), max(all highs))` with **`include_zero=False`** —
  0 is **not** forced in (floating bars need no baseline). The marks never
  recompute a scale; they call `fr.ypix` only.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). Note the
**`include_zero=False`** — the single thing that differs from `column`'s
delegation:

```python
# libs/python/stonecharts/charts/columnrange.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Column range", "band", _columnrange_marks,
                            include_zero=False)   # floating bars — NO zero anchor
```
```go
// libs/go/columnrange.go — package stonecharts
func renderColumnRangeSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Column range", "band", columnRangeMarks, false)
}
```

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
per series, and inside it **one floating `<rect>` per (category, series)** spanning
`ypix(high)` (top) to `ypix(low)` (bottom):

```html
<g class="sc-series" data-series="0">
  <rect class="sc-bar sc-point" data-series="0"
        data-series-name="Ambient range" data-x="Mon" data-y="22.1"
        data-low="12.4" data-high="22.1"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="88.0" cy="96.0" x="71.6" y="96.0" width="32.8" height="188.0"
        fill="#2f7ed8"/>
  … one .sc-bar.sc-point per category …
</g>
```

- **Class:** `sc-bar sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `sc-bar` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The floating bar **is** the hoverable point; there are no
  separate markers.
- **Geometry (vertical, the floating-bar primitive shared with candlestick):**
  `x = left(i,k)`, `width = barW`, from the band layout below. The rect floats —
  it is **not** zero-anchored — spanning the two data values:
  `y = ypix(max(low, high))`, `height = |ypix(low) - ypix(high)|`. Using
  `max` + `abs` (identical to candlestick's body geometry) keeps `height`
  non-negative even if a spec supplies `low > high`, and is parity-safe.
  **Never** anchor to `ypix(0.0)` — that is `column`'s baseline; column range
  floats.
- **Degenerate band (`low == high`):** the rect would have zero height — apply the
  **min-1px** rule (the same doji rule candlestick pins for `open == close`):
  `height = max(1.0, |ypix(low) - ypix(high)|)`, evaluated **identically** in both
  languages so a flat band stays a visible hairline.
- **Geometry (horizontal, `orientation:"horizontal"`):** the orientation transpose
  (§3.2) — the value axis moves to x, the band axis to y. The rect floats
  horizontally: `x = xpix(min(low,high))`, `width = |xpix(high) - xpix(low)|`
  (min-1px), with `y`/`height` from the band slot down the category (y) axis.
  Parity is free — orientation is a coordinate remap only.
- **Fill:** read `fr.styles[si].fill` — the resolved bar paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a bar unfilled
  (an unfilled range bar is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (bar center x) — the crosshair
  reads it — and by convention `cy` (bar top = `ypix(high)`). Without `cx` the
  crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (copied VERBATIM from the blueprint)

Column range reuses `column`'s band layout **unchanged** — the only difference is
what the bar spans vertically (a floating `(low,high)` instead of a zero-anchored
value). Evaluate the arithmetic in **exactly this operation order** in both
languages so `f1` / `:.1f` rounding lands ULP-for-ULP identically (blueprint
§3.2 / §4; the frame's `xpix` implements the band center, the marks build the
sub-bands):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
barW        = groupW / K
left(i,k)   = xpix(i) - groupW/2 + barW*k
```

- Basic single-series ⇒ `K = 1` ⇒ one centered floating bar of width `groupW`.
- `PAD = 0.2` and `K = len(series)` are **fixed constants**, not per-author
  choices. `grouping:false` forces `K = 1` (overlaid).
- The **value axis**, by contrast, is **not** shared verbatim with `column`:
  column range passes `include_zero=False` so the domain spans lows→highs without
  forcing 0.

## Reused chrome (obtained from the frame — never re-implemented)

Column range inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear value-scale via `nice_ticks` → `ypix` — computed by the **frame** over
  both bounds with `include_zero=False`; y gridlines + labels.
- Categorical x-axis via the **band** `xpix` (shared with `column`); the shared
  x-label loop lands labels under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (generalized for `{low,high}`, §5.4b-DT) + keyboard nav. Responsive `<svg>`
  viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and **`include_zero=False`** (floating
value axis). It passes the noun **`"Column range"`** — the frame expands it to
`"Column range chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **`include_zero=False`, NOT True** — column range is the one band-scale sibling
  whose value axis is **not** zero-anchored. Copying `column`'s
  `include_zero=True` would force 0 into the domain and squash a band of
  `[95, 105]` against the axis top. Pin `include_zero=False` in both languages.
- **Value-domain over BOTH bounds** — the frame's value-range extractor must span
  `min(all lows)`..`max(all highs)`, considering **every low and every high**, not
  just one array. The marks call `fr.ypix` only; recomputing a scale (even to
  identical bytes) is a defect (NN, §7.1).
- **Band arithmetic ORDER** — evaluate the seven band lines above in that exact
  order; a reassociated `plot_w/n` or `bandWidth*(1-PAD)` diverges after `f1`
  rounding.
- **Floating-bar geometry** — `y = ypix(max(low,high))`,
  `height = |ypix(low) - ypix(high)|`; **min-1px** when `low == high` (the shared
  doji rule with candlestick). Never emit a negative `height`; never anchor to
  `ypix(0.0)`.
- **Bar-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field. Never emit an unfilled bar.
- **Low/high pairing + length** — `data` (lows) and `high` (highs) are parallel
  and equal-length; iterate by index and pair `data[i]` with `high[i]`. A missing
  `high[i]` (absent/short) is a **gap**, never coerced to 0 (blueprint point-model
  rule).
- **`data-y` vs `data-low`/`data-high`** — `data-y` carries a single representative
  value (`fmt_num(high)`, the bar top / `cy` anchor) so the existing runtime
  tooltip has a body with **zero JS changes**; the full band rides the
  forward-compatible `data-low` / `data-high` attributes and the generalized a11y
  data table. All three are `esc(fmt_num(...))`.
- **Formatters** — `cx,cy,x,y,width,height` via `:.1f`/`f1`; `data-y`,
  `data-low`, `data-high`, radii via `fmt_num`/`fmtNum`; every user string via
  `esc`. A leaked raw `<` fails the XSS tests.
- **No stacking path** — do not route column range through the stacking transform;
  ranges never accumulate. Ignore `stacking` if present.
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
  `data-r-hover` — mandatory even though a `<rect>` ignores the hover `r` — plus
  the range-specific `data-low` / `data-high`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (bar center x) and by
  convention `cy` (bar top = `ypix(high)`).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(high))`;
  `data-low = esc(fmt_num(low))`; `data-high = esc(fmt_num(high))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(...)`.
  Pixel attrs use `:.1f`/`f1`.
- **A11y default-on + the point-model data-table obligation (§5.4b-DT):**
  `role="img"` + concise `aria-label` + `<desc>` in the SVG; a separate
  **visually-hidden data table** in the HTML; keyboard nav walks bars. Because
  column range's `data` stops being `number[]` (it is a `{low,high}` pair,
  shared with `area-range`), the data table MUST be generalized **in lockstep in
  both languages** to render **both** the low and the high per category (not a
  coerced single number), proven by a Py==Go table-bytes test. `a11y:false`
  restores the pre-a11y bytes.
- **Static-first:** the chart is fully readable with JS disabled — bars are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "columnrange",
  "title": "Daily Temperature Range",
  "subtitle": "Low–high band per day, single series (K=1 centered floating bars)",
  "xAxis": {
    "title": "Day",
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
  },
  "yAxis": { "title": "Temperature (°C)" },
  "series": [
    {
      "name": "Ambient range",
      "data": [12.4, 11.8, 13.1, 14.6, 13.9, 12.2, 10.7],
      "high": [22.1, 21.4, 24.3, 26.0, 25.2, 23.1, 20.8]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, `K=1` centered floating bars, `(low,high)` band, free (non-zero-anchored) value axis |
| [`examples/grouped.json`](examples/grouped.json) | 2 series side-by-side, `grouping:true`, band sub-slots, per-series bands |
| [`examples/horizontal.json`](examples/horizontal.json) | `orientation:"horizontal"` — the vertical/horizontal subtype selector; floating bars along the value-x axis |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + grouped + a gradient bar fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, category label, custom bar color) so the XSS tests run against the
column-range marks (§5.5d).
`COLUMNRANGE_CASES = ["basic","grouped","horizontal","themed-dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/columnrange/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="columnrange",
    title="Daily Temperature Range",
    x_axis=Axis(title="Day", categories=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
    y_axis=Axis(title="Temperature (°C)"),
    series=[
        # low bounds in data; high bounds parallel (interim encoding of {low,high})
        Series("Ambient range", [12.4, 11.8, 13.1, 14.6, 13.9, 12.2, 10.7]),
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
- **Hover a bar** → tooltip (x, series, value) + bar highlight + crosshair; the
  generalized tooltip/data table surface the full `low–high` band.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the bars; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — floating bars filled and
  readable.

## Rendering notes

- The value axis uses "nice numbers" ticks (~6) over **both** the low and high
  bounds and — unlike `column` — **does not force 0** into the domain (floating
  bars are not baseline-anchored). Clamp with `yAxis.min`/`yAxis.max` if you want
  a fixed window.
- Bars use the **band** x-scale (`x_scale="band"`) — categories occupy equal
  bands; labels land under band centers; `grouping` splits each band into `K`
  sub-slots exactly as `column` does.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole floating bar via the `<defs>` pre-pass.
- Column range adds **no net-new mark**: it composes `column`'s band layout, the
  **floating-bar primitive** (from `candlestick`), and the **`{low,high}` point
  model** (from `area-range`). The orientation transpose gives the horizontal
  bar-range for free.

## Not yet supported (roadmap)

- Live renderers (`columnrange.py` / `columnrange.go`) — deferred; design +
  examples + validation are complete. Only `line` renders today. Landing them
  depends on the `{low,high}` point model (Rank 10) and the floating-bar
  primitive (Rank 8) being extracted into the shared frame first.
- Canonical `{low,high}` datum + positional `[low,high]` sugar — today the pair
  is the interim `data` (low) + parallel `high` encoding.
- The generalized `{low,high}` accessible data table (§5.4b-DT) — lands with the
  point model.
- Per-point colors, rounded bar corners, connecting whiskers, and the `errorbar`
  overlay (`{y,low,high}` center+range) — variants layered on this base.
