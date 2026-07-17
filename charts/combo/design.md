# Chart: Combo (`combo`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** [`charts/column/design.md`](../column/design.md) (itself a copy of
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the combo
> build detail: the per-series mark model, the composition-layer dispatch, the
> reused chrome, the parity traps, and the a11y DOM contract.

- **Chart id:** `combo`
- **Spec `type`:** `"combo"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank 6** · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; combo rides the shared cartesian frame once
  extraction lands — see [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3.3 Rank 6, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/combo.py` · `libs/go/combo.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Reuses:** [`charts/column`](../column/design.md) (rect-mark + band-layout + stacking) · [`charts/line-basic`](../line-basic/design.md) (path + markers + area)
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A combo chart: two or more series drawn on **one shared plot area** with **more
than one mark kind at once** — typically **columns + a line**. Each series
declares its own render kind via **`series[].type ∈ {line, column}`**, so bars
and a trend line coexist against a shared (or dual) y-axis. It is the classic
"throughput bars + latency line on a shared time axis" view.

Combo is **build rank 6** — the composition sibling. It reuses **everything**
Column and Line already built (rect-mark, band-layout, stacking, path builder,
markers, area fill) and adds exactly one new machine: the **composition layer** —
compute the plot area + scales **once**, then dispatch each series to its own
mark renderer against the shared scales. It also opens (optionally) the
**secondary-y-axis** so co-plotted series with different units share one canvas.

## Use it when

- You want to show **two different measures on the same x** where one is a
  **magnitude to compare per category** (columns — throughput, request counts,
  GC pauses) and the other is a **trend to follow** (a line — latency, error
  rate, a moving average).
- The two measures share an x ordering (time buckets, intervals, versions) but
  may have **different units** (requests vs milliseconds) → give the line its own
  **secondary y-axis** (`secondaryYAxis` + `series[].yAxis: 1`).
- Rows look like: `label -> volume` drawn as bars, `label -> rate` drawn as a
  line, both aligned to the same `categories`.

Do **not** use it for: a **single mark kind** — a plain trend (use `line-basic`)
or a plain category comparison (use `column`); **x/y correlation** with no shared
category ordering (use `scatter`); **part-to-whole of a single total** (use
pie/donut); a **distribution** of raw samples (use `histogram`). See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers, aligned to `categories` by index — the
  **same** `number[]` payload line and column use.
- each `series[].type`: the per-series mark kind, `"line"` or `"column"` — the
  **only** new datum-shaping field. Absent → `"column"` (the base mark).
- Identical value payload to `line`/`column` (`data: number[]`) — combo changes
  **which mark draws a series**, never the data element type. So line and column
  goldens never move, and the a11y `number[]` data table renders unchanged
  (§5.4b-DT does **not** apply — the data element type is still `number[]`).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"combo"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle; the swatch is a bar `<rect>` for a column-type series and a line dash for a line-type series (by `series[].type`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`stacking`** | string | — (grouped) | reused from column, **applies only to `type:"column"` series**: `null`/absent = grouped; `"normal"` = column segments stacked cumulatively; `"percent"` = stacked then normalized to 100%. Line-type series are **never** stacked. The **frame** owns the stacking-aware y-domain over the column-type series (max column **total**) |
| **`grouping`** | bool | true | reused from column, **applies only to `type:"column"` series**: `true` → side-by-side sub-bands (`Kcol` = number of column-type series); `false` → column-type series overlaid in one centered slot. Ignored when `stacking` is set. Line-type series ignore it (they ride the band centers) |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the band categories; both marks align to them) |
| `yAxis.title` | string | — | **primary** value-axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the **primary** y range; the value axis always includes 0 (the bar baseline) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| **`secondaryYAxis`** | object | — | **optional second value axis** (dual units), drawn on the **right**. Same shape as `yAxis` (`title`/`min`/`max`/`gridLine`) plus `opposite` (bool, default `true`). Series bind to it with `series[].yAxis: 1`. Absent → single shared axis. Its own `nice_ticks` (byte-identical by construction — reuses the same value-axis path). Lower-priority field — follows the same five-place lockstep (§5.4b) when its validators land |
| **`series[].type`** | string | `"column"` | **NEW validated field.** The per-series mark kind: `"column"` (baseline-anchored rect via the band layout) or `"line"` (path + markers). Generalizes the top-level `type` into a per-series concept. Validated identically in both languages with **deterministic error order** (§5.4b). An unknown value is a validation error (not silently coerced) |
| **`series[].yAxis`** | int | `0` | which value axis this series is measured against: `0` = primary `yAxis` (default), `1` = `secondaryYAxis`. Ignored when `secondaryYAxis` is absent |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | values, length `N` (negatives allowed → columns drop below the baseline; line dips below) |
| `series[].color` | string \| gradient | palette by index | for a **column** series the **bar fill**; for a **line** series the **stroke + area fill** (markers/legend use stop 0). Hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object |
| `series[].pattern` | object | — | hatch fill: `{type:hatch, color, background, size, angle, strokeWidth}` → `url(#pat)`. Fills a column bar, or the area under a line |

Fields consumed **only by `type:"line"` series** (a column-type series accepts
them via the shared validator but ignores them — forward-compatible, no mark):
`fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`, `marker`. Conversely
`stacking`/`grouping` shape only the column-type series. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** every `series[].data` is `number[]` — one y per category,
  the same shape line and column use. No `{x,y}` object model (that arrives with
  scatter, rank 3). **The data element type does not change** — only a per-series
  *mark kind* is added.
- **Per-series mark kind:** `series[].type` selects the mark. The chart is the
  union of a **column sub-chart** (all `type:"column"` series) and a **line
  sub-chart** (all `type:"line"` series) sharing one plot area and x-axis.
- **Column-type series** obey the column data model: grouped (default), stacked
  (`stacking:"normal"`), or percent (`stacking:"percent"`) — **but the band split
  counts only the column-type series** (`Kcol`), never the line series. See the
  band-layout section.
- **Line-type series** obey the line data model: a path (linear / step / monotone
  spline) through the category positions, optional area fill, optional markers.
- **Shared vs dual y-scale.** With no `secondaryYAxis`, all series map through the
  **one** primary `fr.ypix`. With `secondaryYAxis`, series carrying `yAxis:1` map
  through a **second** independent scale `fr.ypix2` (its own `nice_ticks`).
- **The frame owns every y-domain.** For the primary axis the frame's domain
  spans **all primary-bound series** — the stacked/percent column **totals** (in
  the pinned summation order, §4) **and** the line maxima — with 0 forced in
  (`include_zero=True`, the bar baseline). The secondary axis spans only its
  bound series. The marks **never** recompute a scale.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). The callback is a
**composition dispatcher**: it iterates `fr.spec.series` **by index** and, per
series, emits either the column mark or the line mark based on `series[].type`:

```python
# libs/python/stonecharts/charts/combo.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Combo", "band", _combo_marks)   # include_zero defaults True (bar baseline)

def _combo_marks(fr: CartesianFrame, p: list) -> None:
    for si, s in enumerate(fr.spec.series):          # index order == draw/z order
        if _kind(s) == "line":
            _emit_line_series(fr, p, si, s)          # reuses line's path + markers
        else:
            _emit_column_series(fr, p, si, s)        # reuses column's rect + band slot
```
```go
// libs/go/combo.go — package stonecharts
func renderComboSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Combo", "band", comboMarks, true)
}
func comboMarks(f *cartesianFrame, p *strings.Builder) {
    for si := range f.spec.Series {                  // index order == draw/z order
        if kind(&f.spec.Series[si]) == "line" {
            emitLineSeries(f, p, si)
        } else {
            emitColumnSeries(f, p, si)
        }
    }
}
```

Each branch emits **exactly one** `<g class="sc-series" data-series="{si}">` per
series — the same envelope for both mark kinds, so the legend toggle and
keyboard nav treat every series uniformly.

**A `type:"column"` series** emits **one baseline-anchored `<rect class="sc-bar
sc-point">` per (category, series)** — identical to the Column exemplar:

```html
<g class="sc-series" data-series="0">
  <rect class="sc-bar sc-point" data-series="0"
        data-series-name="Requests" data-x="09:00" data-y="42"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="96.0" cy="120.0" x="80.0" y="120.0" width="32.0" height="216.0"
        fill="#2f7ed8"/>
  … one .sc-bar.sc-point per category …
</g>
```

**A `type:"line"` series** emits the line envelope — optional area `<path>`, the
`<path class="sc-series-line">`, then one `<... class="sc-point">` marker per
datum — identical to the Line reference:

```html
<g class="sc-series" data-series="1">
  <path class="sc-series-line" data-series="1" d="M96.0 88.0 L288.0 70.0 …"
        fill="none" stroke="#e0703c" stroke-width="2"
        stroke-linejoin="round" stroke-linecap="round"/>
  <circle class="sc-point" data-series="1" data-series-name="p95 latency"
          data-x="09:00" data-y="180" data-color="#e0703c"
          data-r="3.5" data-r-hover="6" cx="96.0" cy="88.0" r="3.5" …/>
  … one .sc-point per category …
</g>
```

- **Class:** column marks use `sc-bar sc-point`; line marks use
  `sc-series-line` + `sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle / keyboard); the extra
  `sc-bar` / `sc-series-line` are cosmetic CSS hooks. Adding a class the runtime
  must *know about* is out of scope — NN#2.
- **X alignment (the load-bearing combo detail):** both marks align to the
  **same** band centers. A line-type series places its vertices/markers at
  `fr.xpix(i)` (the band center). A column-type series places its bar in its
  sub-band via the band layout below. So the line runs **through the middle** of
  each category's column group.
- **Column geometry:** `x = left(i, kc)`, `width = barW`; baseline-anchored
  `y = ypix(value)`, `height = ypix(0.0) - ypix(value)` (positive). Negatives flip
  around `fr.ypix(0.0)`. Stacked/percent: floating rect between cumulative
  y-values. **Always anchor to `fr.ypix(0.0)`; never recompute a baseline.**
- **Line geometry:** `pts = [(fr.xpix(i), ypix(v)) …]`; `d` = `_path_d` (linear /
  step) or `_spline_d` (`curve:"monotone"`); optional area fill down to
  `fr.ypix(0.0)`; markers via `_marker`. **Verbatim** the line renderer.
- **Dual axis:** a series with `yAxis:1` reads `fr.ypix2` instead of `fr.ypix`
  for its `y`/`height`. Everything else is identical.
- **Fill (column):** read `fr.styles[si].fill` — pattern → `url(#pat)`; gradient
  → `url(#grad)`; else the solid hex. Never read `area_fill` (that is line's
  under-fill) and never leave a bar unfilled (NN#2). **Fill (line):** stroke =
  `fr.styles[si].stroke`; optional area = `fr.styles[si].area_fill`.
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (band center x for both mark
  kinds) — the crosshair reads it — and by convention `cy` (bar top / line y).
- **Draw / z order = series index order.** Marks are appended in `spec.series`
  order, so a series listed later draws **on top**. To get the line above the
  bars, list the line series **after** the column series. Both languages iterate
  by index and **never reorder by type** (reordering — e.g. a Go range-over-map —
  would diverge; §5.6).
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index, its shape chosen by `series[].type` (bar `<rect>` for column, line dash
  for line) — do not renumber and do not emit a legend from the marks.

## Band layout — the pinned geometry (reused from Column, generalized for combo)

Column-type series ride the exact band scheme the blueprint pins (§3.2 / §4;
identical operation order in both languages so `f1` rounding lands ULP-for-ULP).
The **only** combo generalization: **`K` counts the column-type series, not all
series** — line series occupy no sub-band.

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center (BOTH marks align here)
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
Kcol        = number of series with type == "column" # NOT len(series)
barW        = groupW / Kcol
kc          = index of THIS series among the column-type series (0-based)
left(i,kc)  = xpix(i) - groupW/2 + barW*kc
```

- A single column-type series ⇒ `Kcol = 1` ⇒ one centered bar of width `groupW`;
  line-type series overlay it at the band centers.
- `PAD = 0.2` is fixed. `Kcol` and `kc` count/enumerate **only** the column-type
  series, in **series index order** (skip line-type series when assigning `kc`).
- `grouping:false` overlays column-type series in one slot (`Kcol → 1`);
  `stacking` forces one slot with cumulative segment heights, **accumulated over
  the column-type series in series index order**, and the frame's stacked y-max
  uses that **same** order.
- Line-type series never enter this arithmetic — their x is `xpix(i)`, the band
  center — so adding or removing a line series does **not** move any bar.

## Reused chrome (obtained from the frame — never re-implemented)

Combo inherits, with **zero** re-implementation (§3.1, §4.2), the **union** of
what Line and Column already reuse:

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via `nice_ticks` → `ypix` (incl. the stacking-aware y-max the
  **frame** computes over the column-type series); y gridlines + labels.
- Categorical x-axis via the **band** `xpix`; the shared x-label loop lands labels
  under band centers with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill` (bar
  paint) + `SeriesStyle.stroke`/`area_fill` (line paint); id-scoping via `cid`
  (defs emitted only when a series needs them — no empty `<defs>` under light).
- Line's `_path_d` / `_spline_d` / `_marker`; column's rect + band slot — the two
  mark vocabularies, imported, not re-derived.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="band"` and `include_zero=True` (value axis /
bar baseline). It passes the bare noun **`"Combo"`** — the frame expands it to
`"Combo chart with N series…"` byte-for-byte.

**Net-new for combo (the only additions over Line + Column):**
- **Composition layer** — compute plot area + scales once, then dispatch each
  series to its mark renderer by `series[].type`.
- **Secondary-y-axis** — the optional `fr.ypix2` scale + right-side axis (its own
  `nice_ticks`, byte-identical path). Off by default.
- **Legend swatch variants** — bar rect vs line dash by `series[].type`.
- The new **`series[].type`** validated field (five-place lockstep, §5.4b).

## New field — the five-place lockstep (§5.4b)

`series[].type` is a **new validated spec field** (like column's `stacking`), so
it MUST be added in **five places, in lockstep**, plus invalid fixtures:

1. **Schema** (`spec/chart-spec.schema.json`): under `definitions.series`, add
   `"type": {"type":"string","enum":["line","column"],"default":"column",
   "description":"per-series mark kind for combo"}`. Keep `additionalProperties`
   open.
2. **`validate.py`:** in `_series`, `if "type" in v: _str(v["type"], f"{path}.type", errs)`
   — reuse `_str`; a non-string `series[].type` → `"$.series[i].type: expected
   string, received …"`. (Enum membership is enforced at dispatch parity, mirrored
   in both languages, with the same deterministic error text.)
3. **`validate.go`:** the exact mirror — `if hasKey(m,"type") { vstr(m["type"],
   path+".type", &errs) }` — byte-identical wording.
4. **Spec model — Python** (`spec.py`): `Series.type: str = "column"`, parsed in
   `from_dict` with default-on-absence only.
5. **Spec model — Go** (`spec.go`): `Type string \`json:"type,omitempty"\`` on the
   series struct, defaulted to `"column"` in `applyDefaults` so absent == present
   default.
6. **Invalid fixtures** (`charts/combo/invalid-fixtures.json`): ≥1 hostile case,
   e.g. `{"series":[{"data":[1],"type":5}]}` →
   `"$.series[0].type: expected string, received number"`, wired into both parity
   tests (§5.6c).

The **known-type** obligation (§5.0) also applies: register `"combo"` in the
validated known-type set in **both** `validate.py` and `validate.go` (and the
schema `type` enum + both dispatchers), so an unknown top-level `type` is rejected
identically before dispatch. `secondaryYAxis` + `series[].yAxis` follow the same
five-place drill when their (lower-priority) validators land.

## Parity traps (verify before the byte-parity gate)

- **Deterministic dispatch order** — iterate `spec.Series` **by index** in both
  languages and dispatch on `series[].type`; **never** range-over-map or sort by
  type. Draw/z order is series order (line-after-column puts the line on top).
- **Band arithmetic ORDER + `Kcol`** — evaluate the band lines in the pinned
  order; `Kcol` counts **only** column-type series and `kc` enumerates them in
  series index order. Miscounting `K` (including line series) shifts every bar and
  diverges after `f1` rounding.
- **Line rides the band center** — line vertices/markers at `fr.xpix(i)` (band
  center), NOT a sub-band slot, so bars and line align identically in both
  languages.
- **Frame owns the y-domain(s)** — the marks call `fr.ypix` / `fr.ypix2` only;
  recomputing a scale (even to identical bytes) is a defect (NN, §7.1). The
  primary domain spans column totals **and** line maxima with 0 forced in.
- **Summation order** — stacked column cumulative sums accumulate over the
  column-type series in series index order; the frame's stacked y-max uses the
  **same** order; percent divides each value by its category total in that order.
- **Bar-fill vs line-paint resolution** — column series: pattern → `url(#pat)`;
  gradient → `url(#grad)`; else solid hex (never `area_fill`, never unfilled).
  Line series: `stroke` = resolved stroke; area = `area_fill`. Reading the wrong
  field silently drops paint.
- **Negative values** — column: flip `y`/`height` around `ypix(0.0)`, never a
  negative `height`. Line: `ypix(v)` handles negatives directly.
- **`data-y` is the raw value** — for a stacked column segment `data-y` carries
  the **raw per-series value**, not the running cumulative total; for a line point
  it is the datum value. Geometry uses cumulative baselines / scale, the tooltip
  shows what the user supplied.
- **Dual-axis pixel mapping** — a `yAxis:1` series uses `fr.ypix2`; a `yAxis:0`
  (or absent) series uses `fr.ypix`. Mixing them mislocates a mark identically in
  both languages (byte-parity would still pass) — so pin the per-series axis
  selection explicitly.
- **Formatters** — `cx,cy,x,y,width,height`, path `d` numbers via `:.1f`/`f1`;
  `data-y`, radii, line-width, offsets via `fmt_num`/`fmtNum`; every user string
  via `esc`. A leaked raw `<` fails the XSS tests (run against **both** mark
  kinds — the adversarial example carries hostile strings in a column **and** a
  line series).
- **Degenerate percent** — a column category total of 0 would divide-by-zero; pin
  the rule identically **before** the divide (Python raises, Go yields
  `NaN`→`"0"`).
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index; keep series/point/legend `data-series` indices
  in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, crosshair, legend-toggle, and keyboard nav all work with
**zero JS changes** — for both mark kinds, because both emit `.sc-point`.

- **Series group:** `.sc-series[data-series=N]` — one per series regardless of
  mark kind; `N` is the integer series index, **consistent** across the group,
  its points, and the legend item (do not renumber).
- **Datum mark:** `.sc-point` (a column `<rect class="sc-bar sc-point">` or a line
  `<... class="sc-point">`) carries **all** of `data-series`, `data-series-name`,
  `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover` — mandatory even
  though a `<rect>` ignores the hover `r`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (band center x, shared by
  both marks) and by convention `cy`.
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` — the **raw** value
  (per-series segment value under stacking); `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks all
  `.sc-point`s (bars and line points alike). `a11y:false` restores the pre-a11y
  bytes. Combo keeps `data: number[]`, so the existing `number[]` data table
  renders faithfully with **no** generalization (§5.4b-DT applies only when the
  data **element type** changes — combo changes only the per-series mark kind).
- **Static-first:** the chart is fully readable with JS disabled — bars are
  server-rendered and filled, the line is drawn and its markers placed; the
  crosshair ships `display:none`; the tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "combo",
  "title": "Deploys per Day",
  "subtitle": "Daily count (columns) vs 3-day average (line)",
  "xAxis": { "title": "Day", "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"] },
  "yAxis": { "title": "Deploys" },
  "series": [
    { "name": "Deploys", "type": "column", "data": [8, 5, 11, 6, 9] },
    { "name": "3-day avg", "type": "line", "data": [8, 7, 8, 7.3, 8.7], "color": "#e0703c" }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | one column series + one line series on **one shared y-axis**; the canonical composition dispatch, line drawn over bars |
| [`examples/dual-axis.json`](examples/dual-axis.json) | `secondaryYAxis` + `series[].yAxis:1` — throughput columns (primary) + p95 latency line in ms (secondary), different units on one canvas |
| [`examples/dark.json`](examples/dark.json) | `theme:"dark"` + grouped columns (`Kcol=2`) + a styled overlay line (`dashStyle`, diamond marker) + a gradient column fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) |
| [`examples/adversarial.json`](examples/adversarial.json) | hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field of **both** a column series and a line series (name, category label, custom color) so the XSS tests run against both combo marks (§5.5d) |

The golden build set pins `COMBO_CASES = ["basic","dual-axis","dark","adversarial"]`.
The `adversarial` case is the mandatory XSS witness: it must carry hostile
strings in a `type:"column"` **and** a `type:"line"` series so a leaked raw `<`
from **either** mark fails a test.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/combo/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="combo",
    title="Deploys per Day",
    x_axis=Axis(title="Day", categories=["Mon", "Tue", "Wed", "Thu", "Fri"]),
    y_axis=Axis(title="Deploys"),
    series=[
        Series("Deploys",   [8, 5, 11, 6, 9],        type="column"),
        Series("3-day avg", [8, 7, 8, 7.3, 8.7],     type="line", color="#e0703c"),
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
- **Hover a bar or a line point** → tooltip (x, series, y) + mark highlight +
  crosshair.
- **Click a legend item** → toggle that series on/off (bars or line).
- **Keyboard** → arrows walk the points (bars and line points); Esc clears
  without stealing focus.
- Renders fully (static) even with JavaScript disabled — bars filled, line drawn
  and readable.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) and always includes 0 as the bar baseline
  unless `yAxis.min/max` clamp it. For `stacking:"percent"` the (column) axis is
  effectively 0–100%.
- Both marks use the **band** x-scale (`x_scale="band"`): categories occupy equal
  bands; column bars sit in sub-bands, line points sit at band centers, labels
  land under band centers.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern fills a column via the `<defs>` pre-pass, or an area under a
  line.
- Combo is a **composition** of the Column and Line renderers over the shared
  `_cartesian` frame — it forks **neither**; the shared substrate is reused, never
  duplicated.

## Not yet supported (roadmap)

- Live renderers (`combo.py` / `combo.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **More than two axes / more mark kinds** (meteogram: spline + column + windbarb
  + errorbar) — the composition layer generalizes to more marks once those
  siblings (error-bar, windbarb) land.
- **`series[].type` beyond `{line, column}`** (area, scatter co-plot) — added as
  each mark sibling lands and joins the dispatch.
- `drilldown`, per-axis independent gridlines, inverted axes — variants layered on
  this composition base.
