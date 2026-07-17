# Chart: Variwide (`variwide`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this recipe copies the
> Cartesian exemplar [`charts/column/design.md`](../column/design.md) (itself
> modeled on [`charts/line-basic/design.md`](../line-basic/design.md)) and adds
> the two things that make `variwide` its own chart: a **width-encoding field**
> (`z` → bar width) and a **cumulative-width x-layout** that replaces column's
> equal band layout. It is column's rect-mark and y-scale, drawn in slots whose
> *widths are data*, not equal.

- **Chart id:** `variwide`
- **Spec `type`:** `"variwide"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank:** post-Column sibling (reuses Rank 1 column primitives) · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; variwide rides the shared cartesian frame —
  the same frame column uses — once the extraction, column's rect-mark, and the
  cumulative-width x-scale land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2
  Family A (Variwide row), §3.3 Rank 1, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/variwide.py` · `libs/go/variwide.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A variwide chart: a column chart in which **each bar's WIDTH also encodes a
value**. Bars are still **vertical, baseline-anchored `<rect>`s** whose *height*
encodes a first metric (the y-value); on top of that a **second metric (the
width metric, `z`) sets how wide each bar is**, and the bars are laid out
**edge-to-edge with widths proportional to `z`** — a *cumulative-width* x-layout,
not the equal categorical bands column uses. A category with a large `z` gets a
wide bar and occupies a large share of the plot; a category with a small `z` is
narrow. The bars are the hoverable, interactive elements (they replace the line
chart's point markers), exactly as in column.

Variwide is a **later Family A sibling** that reuses **column's rect-mark and
y-scale (Rank 1)** wholesale and forces exactly **two** net-new things:

1. a **width-encoding field** — `series[].widths` (the per-datum `z`), and
2. a **cumulative-width x-layout** — a new x-scale strategy (`x_scale="variwide"`)
   in which slot widths are proportional to `z` and slots tile the plot area,
   **replacing** column's equal band layout (`bandWidth = plot_w / n`).

Everything else — the value (y) axis, the rect mark, the baseline anchor, the
`<defs>`/fill pre-pass, all chrome, all parity paths — is column's, reused
without a fork.

## The one idea: width is data (cumulative-width x-layout)

In column every category owns an **equal** band (`bandWidth = plot_w / n`). In
variwide every category owns a slot whose **width is proportional to its `z`
value**, and the slots are packed left-to-right across the plot so their widths
**accumulate** to fill it:

| Concern | Column (equal bands) | Variwide (cumulative widths) |
|---|---|---|
| **Slot width** | `bandWidth = plot_w / n` (every category equal) | `slotW(k) = plot_w * z_k / Z` (proportional to `z`) |
| **Slot left edge** | `plot_x + bandWidth*k` | `plot_x + plot_w * (cum_k / Z)` (cumulative) |
| **Slot center (label + `cx`)** | `xpix(k) = plot_x + bandWidth*k + bandWidth/2` | `xpix(k) = slotLeft(k) + slotW(k)/2` |
| **Encodes** | height only | height (**y**) **and** width (**z**) |
| **x-axis meaning** | categorical, equal bands | categorical, **width-weighted** bands |

Both keep the **same value (y) axis** (`nice_ticks`/`ypix`, `include_zero=True`,
0 forced in as the bar baseline), the **same rect mark**, the **same** negative
handling, the **same** fill pre-pass, and the **same** chrome. Variwide is column
with `bandWidth` replaced by a per-category proportional slot width — nothing
else moves. That single substitution is the whole chart.

## Use it when

- You have **one category axis** and want to compare a **first magnitude across
  categories (bar height)** while *also* showing a **second "weight" per
  category (bar width)** — e.g. p95 latency per service **weighted by traffic**,
  GDP-per-capita per country **weighted by population**, price per unit
  **weighted by volume sold**, variance per team **weighted by budget size**.
- The width metric is a **meaningful magnitude** (population, revenue, request
  volume, budget) whose *relative share* you want visible: wide bars draw the eye
  to the categories that carry the most weight.
- Rows look like: `label -> (value, width)` — one value that sets height and one
  that sets width, per category.

Do **not** use it for: a plain **magnitude across equal categories** (use
`column` — equal bands, no width metric), a **trend** over ordered/continuous x
(use `line-basic`), a **distribution** of raw samples (use `histogram` — its bars
are contiguous but equal-information, widths are *bin sizes* not a data value),
**x/y correlation** (use `scatter`), or **part-to-whole of a single total** (use
pie/donut). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers — the **height** metric (the y-value),
  aligned to `categories` by index. Same shape column/line use.
- each `series[].widths`: `N` numbers — the **width** metric (`z`), aligned to
  `data`/`categories` by index. This is the one new payload variwide adds; a bar
  with a larger `widths[i]` is drawn wider. Absent → all widths equal (variwide
  degenerates to a plain equal-width column). See **Data model**.

Variwide is **single-series** in the canonical case (like Highcharts variwide —
you cannot meaningfully group or stack variable-width columns). Multi-series
variwide is out of scope (see roadmap); when present, the frame reads the **first
series'** `widths` for the shared x-layout (all series share the category
widths).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"variwide"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the bar `<rect>`) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`series[].widths`** | number[] | equal (all `1`) | **NEW field.** The per-datum **width metric** (`z`), length `N`, aligned to `data` by index. Sets each bar's width via the cumulative-width x-layout: `slotW(k) = plot_w * z_k / Z` where `Z = Σ z`. Negatives are clamped to `0` **before** summation; absent (or all-zero → `Z == 0`) falls back to **equal** widths (`z_k = 1`, i.e. a plain column). Added via the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures). Bridges to the shared **point model** (§3.3 Rank 3) `z` field — see **Data model** |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels (the width-weighted band categories) |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the **height** (y) range; the value axis always includes 0 (the bar baseline) unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | bar **heights** (the y-value), length `N` (negatives allowed → bars drop below the baseline) |
| `series[].color` | string \| gradient | palette by index | the **bar fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole bar; legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the bar: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |

Fields carried over from the line/column spec but **inert** for variwide (no line
to draw; single-series, so no group/stack of author series): `fillOpacity`,
`lineWidth`, `dashStyle`, `step`, `curve`, `marker`, `grouping`, `stacking` are
accepted by the shared validator (forward-compatible) but not consumed by the
variwide marks. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — one **height** per category,
  the exact shape line/column use. No `{x,y}` object model (that arrives with
  scatter, Rank 3), so line/column/variwide goldens never move when the richer
  point model lands.
- **Width payload:** `series[].widths` is a **parallel `number[]`** — one `z` per
  category, aligned to `data` by index. This is the pre-point-model **bridge** for
  the width metric, exactly analogous to histogram expressing a pre-binned bucket
  as `data:[counts]` + `xAxis.binEdges` until the point model lands: keeping
  `data` a bare `number[]` and carrying `z` in a sibling array means today's
  `number[]` validator and the existing `number[]` accessible data table both
  accept it **unchanged**. When the shared **point model** (§3.3 Rank 3) lands, a
  datum becomes `{x,y,z,…}` and `widths[i]` migrates into the datum's `z` (the
  same `z` bubble uses for marker size — here it drives bar **width** instead);
  the `widths` parallel array remains valid sugar.
- **The frame owns the y-domain.** Heights feed the usual `nice_ticks` with 0
  forced in (`include_zero=True`) — the bar baseline. The marks never recompute a
  scale. This is column's value axis verbatim.
- **The frame owns the x-layout.** The cumulative-width slots are computed by the
  frame from the width metric (`x_scale="variwide"`), **not** by the marks — the
  marks read `fr.xpix(k)` (slot center) and the frame's slot geometry the same way
  column's marks read `fr.xpix(i)` + `fr.band_width()`. The **degenerate rule**
  (`Z <= 0` → equal widths) is pinned on the frame, identically in both languages,
  **before** any division (see parity traps).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). The single
difference from column is the x-scale — `"variwide"` (cumulative widths) instead
of `"band"` (equal bands). The value axis stays zero-anchored (`include_zero`
defaults `True` — the bar baseline):

```python
# libs/python/stonecharts/charts/variwide.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Variwide", "variwide", _variwide_marks)  # include_zero defaults True (height baseline)
```
```go
// libs/go/variwide.go — package stonecharts
func renderVariwideSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Variwide", "variwide", variwideMarks, true)
}
```

> **The cumulative-width x-scale is a frame parameter, added once.** `build_frame`
> gains a third `x_scale` strategy, `"variwide"`, alongside `"point"` (line) and
> `"band"` (column). Under `"variwide"` the frame reads the first series'
> `widths`, clamps negatives, computes the total `Z`, applies the degenerate
> fallback, and precomputes per-category `slotLeft`/`slotW`; `xpix(k)` returns the
> **slot center** so the shared x-label loop lands category labels under
> width-weighted band centers with **no per-chart label code** (exactly as `band`
> does for column). Because `"point"` and `"band"` are untouched, **all existing
> line and column goldens are byte-unchanged** after the variwide scale lands
> (Gate A/C — the new strategy is purely additive).

The marks callback emits **exactly one** `<g class="sc-series" data-series="{si}">`
(single series in the canonical case), and inside it **one baseline-anchored
`<rect>` per category**:

```html
<g class="sc-series" data-series="0">
  <rect class="sc-bar sc-point" data-series="0"
        data-series-name="p95 latency" data-x="search" data-y="176" data-z="610"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="712.4" cy="120.0" x="640.8" y="120.0" width="143.2" height="216.0"
        fill="#2f7ed8"/>
  … one .sc-bar.sc-point per category …
</g>
```

- **Class:** `sc-bar sc-point`. `sc-point` is the **contract** class the runtime
  keys on (tooltip / highlight / crosshair / legend-toggle); `sc-bar` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#2). The bar **is** the hoverable point; there are no separate markers.
- **Geometry (x — the net-new).** From the cumulative-width layout below:
  `x = barLeft(k)`, `width = barW(k)` — the bar sits inside category `k`'s
  proportional slot, inset by `PAD` so neighbouring bars keep a small gap.
- **Geometry (y — column's, verbatim).** Baseline-anchored: for a **positive**
  height `y = fr.ypix(value)` and `height = fr.ypix(0.0) - fr.ypix(value)`.
  **Negatives:** a value below 0 flips the rect — `y = min(fr.ypix(0.0),
  fr.ypix(value))`, `height = |fr.ypix(0.0) - fr.ypix(value)|` — so the bar drops
  from the baseline downward. Always anchor to `fr.ypix(0.0)`; never recompute a
  baseline (the value axis already forced 0 into the domain).
- **Fill:** read `fr.styles[si].fill` — the resolved bar paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill), and never leave a bar unfilled
  (an unfilled variwide bar is a broken static chart — NN#2).
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (bar center x = the slot
  center `fr.xpix(k)`) — the crosshair reads it — and by convention `cy` (bar
  top). Without `cx` the crosshair breaks.
- **`data-z`:** each bar additionally carries `data-z = esc(fmt_num(widths[k]))`
  — the width metric — as a documented **forward-compatible extra** (mirrors
  bubble's `data-z`). The runtime does not require it; the tooltip/data table
  surface it so the reader sees *why* the bar is wide. It is **not** a contract
  attribute (adding a runtime behavior that reads it is out of scope — NN#2).
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Cumulative-width x-layout — the pinned geometry

This is variwide's one net-new geometry — it **replaces** column's band layout
(`bandWidth = plot_w / n`). Evaluate the arithmetic in **exactly this operation
order** in both languages so `f1` / `:.1f` rounding lands ULP-for-ULP identically
(mirrors the discipline of the blueprint's §3.2 band layout; the frame's `xpix`
implements the slot center, the frame precomputes the slots, the marks inset the
bar):

```
# per-category width metric (clamp negatives BEFORE anything else)
z_k       = max(widths[k], 0.0)                       for k = 0 … n-1
Z         = z_0 + z_1 + … + z_{n-1}                   # total, accumulate in index order

# DEGENERATE FALLBACK (pinned identically, BEFORE any division):
#   Z <= 0  (widths absent, or all-zero, or all-negative)  → equal widths
if Z <= 0.0:  z_k = 1.0 for all k;  Z = float(n)

# cumulative slot layout (fraction FIRST, then multiply — pin this associativity)
cum_0     = 0.0
cum_k     = cum_{k-1} + z_{k-1}                        # cumulative z BEFORE category k
slotLeft(k) = plot_x + plot_w * (cum_k / Z)
slotW(k)    = plot_w * (z_k / Z)
xpix(k)     = slotLeft(k) + slotW(k) / 2              # slot CENTER — label + cx anchor

# bar inset (reuse column's single padding constant)
PAD       = 0.2
barW(k)   = slotW(k) * (1 - PAD)
barLeft(k)= slotLeft(k) + slotW(k) * PAD / 2         # centered in the slot
```

- **Slots tile the plot with no overlap and no gap** — `Σ slotW(k) = plot_w`,
  `slotLeft(k+1) = slotLeft(k) + slotW(k)`. The visible inter-bar gap comes only
  from the `PAD` inset applied per slot, so wide slots and narrow slots keep a
  *proportional* gap (unlike histogram, where bars are fully contiguous with
  **no** padding).
- **`PAD = 0.2` is the same fixed constant column uses**, not a per-author choice
  — reusing it keeps variwide's gap visually consistent with column.
- **Divide-by-zero is impossible after the fallback** — the `Z <= 0` rule sets
  `Z = n > 0` **before** `cum_k / Z` / `z_k / Z`. Pin it identically: without the
  guard Python raises `ZeroDivisionError` while Go yields `NaN`→`fmtNum`→`"0"` —
  a divergence. (Same shape as bubble's degenerate size-scale and column/percent's
  zero-total, §3.2 / §3.3.)
- **Clamp negatives before summation** — `z_k = max(widths[k], 0.0)` first, so a
  stray negative width can never make `Z` shrink below a later positive slot or go
  negative. Evaluate the `max` identically in both languages.
- **The frame owns this layout.** `build_frame(x_scale="variwide")` precomputes
  `slotLeft`/`slotW` and exposes them (plus `xpix(k)` = center); the marks read
  them and apply `PAD`. The marks compute **no** scale of their own (NN, §7.1).

## Reused chrome (obtained from the frame — never re-implemented)

Variwide inherits, with **zero** re-implementation, everything column inherits;
only the x-layout differs (§3.1, §4.2):

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear **height** (y) scale via `nice_ticks` → `ypix` (0 forced in as the bar
  baseline); y gridlines + labels — **column's value axis verbatim**.
- Categorical x-axis via the **variwide** `xpix` (width-weighted slot centers);
  the shared x-label loop lands labels under slot centers with no per-chart label
  code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="variwide"` and `include_zero=True` (height
axis / baseline). It passes the bare noun **`"Variwide"`** — the frame expands it
to `"Variwide chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

Column's height/rect/fill traps, all still in force, plus the cumulative-width
x-layout.

- **Cumulative-width arithmetic ORDER** — evaluate the layout block above in that
  exact order and associativity (`z_k` clamp → `Z` sum in index order → `cum_k` in
  index order → **`cum_k / Z` first, then `* plot_w`**). A reassociated
  `plot_w * cum_k / Z` or a summation in a different order diverges after `f1`
  rounding.
- **Degenerate `Z <= 0` fallback** — pin the equal-width fallback identically
  **before** the divide (Python raises, Go yields `NaN`→`"0"`). Absent/all-zero/
  all-negative widths must both render as a plain equal-width column *and* match
  byte-for-byte across languages.
- **Clamp negatives before summing** — `z_k = max(widths[k], 0.0)` first; do not
  let a negative width enter `Z` or a slot width.
- **Frame owns the x-layout** — the marks must read `fr.xpix`/the frame slots
  only; recomputing the cumulative layout in the marks (even to identical bytes)
  is a defect (NN, §7.1).
- **Frame owns the y-domain** — the marks call `fr.ypix` only; the height axis is
  column's, zero-anchored.
- **Bar-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`; else
  solid hex. Reading `solid` silently drops gradient/pattern; reading `area_fill`
  is line's field. Never emit an unfilled bar.
- **Negative bars** — flip `y`/`height` around `fr.ypix(0.0)`; do not emit a
  negative `height`. (Width is always ≥ 0 after the clamp.)
- **`data-y` vs `data-z`** — `data-y` carries the **height** value; `data-z`
  carries the **width metric** — both the raw per-datum values via
  `esc(fmt_num(...))`, never a pixel or a normalized share.
- **Formatters** — `cx,cy,x,y,width,height` via `:.1f`/`f1`; `data-y`, `data-z`,
  radii, offsets via `fmt_num`/`fmtNum`; every user string via `esc`. A leaked raw
  `<` fails the XSS tests.
- **No stray chrome** — head/tail emit no empty `<defs>` or background `<rect>`
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate `spec.Series` by index (never range-over-map); keep series/point/legend
  `data-series` indices in lockstep.

## New spec field — the five-place lockstep (§5.4b)

`series[].widths` is a genuinely new validated field (there is no existing
selector for the width metric anywhere), so it MUST be added in **five places, in
lockstep**, or you break non-negotiable #3 and/or #1:

1. **Schema** (`spec/chart-spec.schema.json`): add `widths` under `series.properties`:
   `{"type":"array","items":{"type":"number"},"description":"Per-datum width metric (z); sets each bar's width via the cumulative-width x-layout. Aligned to data by index."}`.
   Keep the `additionalProperties`-open, forward-compatible stance; add `"variwide"`
   to `properties.type.enum` (registration).
2. **`validate.py`:** in `_series`, add a numeric-array check (mirror `_str_array`
   using `_num`, or inline the loop like `data`) so error text is identical:
   `if "widths" in v: <for i,e in enumerate(v["widths"]): _num(e, f"{path}.widths[{i}]", errs)>`
   → e.g. `$.series[0].widths[2]: expected number, received string`. Defaults are
   **not** applied here.
3. **`validate.go`:** the exact mirror — same path, byte-identical wording
   (`$.series[0].widths[2]: expected number, received string`).
4. **Spec model — Python** (`spec.py`): add `widths: Optional[List[float]] = None`
   parsed in `from_dict` with **default-on-absence only** (never coerce). `None` =
   absent = equal-width fallback.
5. **Spec model — Go** (`spec.go`): add a `Widths []float64` field with a
   `json:"widths,omitempty"` tag (a nil slice = absent = equal-width fallback),
   reproducing the Python "absent → equal widths" behavior exactly.
6. **Invalid fixtures** (`charts/variwide/invalid-fixtures.json`): add ≥1 hostile
   case (`{"widths":["x"]} → "$.series[0].widths[0]: expected number, received string"`;
   `{"widths":"wide"} → "$.series[0].widths: expected array, received string"`) and
   wire the file into both parity tests (§5.5c). This proves the two validators
   reject identically.

**Registration** also = adding `"variwide"` to `render.py` `_RENDERERS`, the
`render.go` `RenderSVG` switch, the schema `type` enum, **and** the shared
known-type validation set in both `validate.py`/`validate.go` (so an unknown
`type` is rejected identically as a `SpecError` before dispatch, not
Python-raises / Go-panics — §5.0).

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
  `data-r-hover` (plus the extra `data-z` width metric) — mandatory even though a
  `<rect>` ignores the hover `r`.
- **Crosshair anchor:** every `.sc-point` carries a `cx` (bar center x = slot
  center) and by convention `cy` (bar top).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(height))`;
  `data-z = esc(fmt_num(width))`; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks bars.
  `a11y:false` restores the pre-a11y bytes. Variwide keeps `data: number[]` (the
  heights) and carries the width metric in the parallel `widths` array, so the
  existing `number[]` data table renders the **heights** faithfully with **no**
  generalization (the §5.4b-DT obligation fires only when the `data` **element
  type** changes — which it does not here). The width metric is surfaced per bar
  via `data-z` and MAY be added as an extra table **column** as a
  forward-compatible enhancement; the full "width as a first-class datum field in
  the table" generalization arrives with the point model (§5.4b-DT, §3.3 Rank 3).
- **Static-first:** the chart is fully readable with JS disabled — bars are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "variwide",
  "title": "p95 Latency by Service, Weighted by Traffic",
  "subtitle": "Bar height = p95 latency (ms); bar width = request share (k req/min)",
  "xAxis": { "title": "Service", "categories": ["auth", "catalog", "cart", "payments", "search"] },
  "yAxis": { "title": "p95 latency (ms)" },
  "series": [
    { "name": "p95 latency", "data": [88, 142, 119, 210, 176], "widths": [320, 540, 180, 90, 610] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, per-category `widths`, cumulative-width slots, height baseline anchor |
| [`examples/dark.json`](examples/dark.json) | `theme:"dark"` + a top→bottom gradient bar fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) + widths spanning three orders of magnitude (very wide vs very narrow slots) |
| [`examples/negative.json`](examples/negative.json) | negative heights (baseline flip, column rect-mark reuse) combined with variable widths + a custom solid bar color |
| [`examples/adversarial.json`](examples/adversarial.json) | hostile strings (`<script>`, `"`, `<`, `&`, `'`) in **every** marks-emitted field — series name, category labels, custom bar color — so the XSS tests run against the variwide marks (§5.5d) |

`VARIWIDE_CASES = ["basic","dark","negative","adversarial"]` — wire these into
both golden suites (`test_golden.py`, `render_test.go`, §5.5a/b). The
`adversarial` case is the one the XSS assertion keys on: its golden must contain
the **escaped** bytes and **no** raw `<script>` (§5.5d).

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/variwide/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="variwide",
    title="p95 Latency by Service, Weighted by Traffic",
    x_axis=Axis(title="Service", categories=["auth", "catalog", "cart", "payments", "search"]),
    y_axis=Axis(title="p95 latency (ms)"),
    series=[Series("p95 latency", [88, 142, 119, 210, 176], widths=[320, 540, 180, 90, 610])],
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
- **Hover a bar** → tooltip (category, series, height, width metric) + bar
  highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the bars; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — bars filled and readable.

## Rendering notes

- The **height** (y) axis uses "nice numbers" ticks (~6) and always includes 0 as
  the bar baseline unless `yAxis.min/max` clamp it — column's value axis verbatim.
- Bars use the **variwide** x-scale (`x_scale="variwide"`) — category slots have
  **widths proportional to `z`** and tile the plot area; labels land under slot
  centers. This is the deliberate replacement for column's equal band layout.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole bar via the `<defs>` pre-pass.
- Variwide is column with `bandWidth` replaced by a proportional slot width — it
  reuses the **same** extracted substrate (`_cartesian.py` / `cartesian.go`) and
  column's rect-mark + y-scale; the width field and the cumulative-width x-scale
  are its only net-new, and it is **never** forked from column.

## Not yet supported (roadmap)

- Live renderers (`variwide.py` / `variwide.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Variwide lands after the
  extraction (§4) and column's rect-mark (Rank 1), adding the cumulative-width
  x-scale + the `widths` field.
- The **`{y, z}` point object** as a `data` element (`z` = width) — arrives with
  the shared point model (§3.3 Rank 3); until then the width metric is the
  parallel `series[].widths` array. When it lands, the accessible data table gains
  a width column in lockstep (§5.4b-DT).
- **Multi-series / grouped / stacked** variwide — out of scope (variable-width
  columns do not group or stack meaningfully); the canonical chart is single
  series, matching Highcharts variwide.
- **Horizontal variwide** (widths → row heights via the orientation transpose,
  Rank 2), rotated x-labels, and per-category color zones — variants layered on
  this base.
