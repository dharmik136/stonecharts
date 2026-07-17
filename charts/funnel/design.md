# Chart: Funnel / Pyramid (`funnel`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file copies
> [`charts/line-basic/design.md`](../line-basic/design.md) and the sibling
> exemplar [`charts/column/design.md`](../column/design.md), then documents the
> **one declared exception** in Family A: funnel rides none of the axis chrome
> and brings its own centered-trapezoid mark + value→width layout.

- **Chart id:** `funnel`
- **Spec `type`:** `"funnel"`
- **Class:** `sibling` (Family A — Cartesian/XY, **declared substrate exception**) · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; funnel is validated + design-complete with
  rendering deferred — see [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2 Family A row, §3.3, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/funnel.py` · `libs/go/funnel.go`
- **Substrate:** **none of the shared cartesian frame's axis machinery** — see
  "Reused chrome" below. Funnel is the **only** Family A chart that does **not**
  delegate to [`render_cartesian`](../_cartesian/README.md).
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A funnel chart: a single ordered set of **pipeline stages**, each stage drawn as
a **horizontal, center-aligned band** whose **width encodes the stage value**.
Consecutive stages are joined into **centered trapezoids** (the top edge is this
stage's width, the bottom edge is the next stage's width), so the shape tapers
from the widest stage (top) to the narrowest (bottom) — the classic conversion /
drop-off silhouette. The **pyramid** is the same chart flipped so the base is at
the bottom; the **area / neck** funnel adds a straight vertical neck below a
threshold.

Funnel is the **declared exception to the Family A substrate contract**
(blueprint §2, Family A row + the substrate-contract note). Highcharts derives it
from the pie / part-to-whole module, and it behaves like one: it uses **no x/y
axis chrome, no gridlines, and neither the point nor the band x-scale**. It
brings its **own** centered-trapezoid mark and its **own** value→width centering
layout (a "cartesian-lite" linear scale), and reuses only the substrate's
theme/palette, `<defs>`, a11y, runtime, and formatting parity helpers.

## Use it when

- Your rows are the **ordered stages of one pipeline** (visitors → sign-ups →
  trials → paid; leads → qualified → proposal → won) and each stage carries a
  **single count or magnitude** that generally **decreases** stage to stage.
- You want to read **conversion** and **drop-off** at a glance — the narrowing of
  the funnel *is* the message.
- Rows look like: `stage -> value` — **one value per stage**, one series.

Do **not** use it for: a **trend** over ordered/continuous x (use `line-basic`),
**comparing categories** that are not a monotone pipeline (use `column` / `bar`),
**true part-to-whole of a single total** where slices sum to 100% of one number
(use pie / donut — funnel stages are *successive* subsets, not disjoint slices),
or a **distribution** of raw samples (use `histogram`). See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- `series[0].data`: the stage values, length `N` (one number per stage) — the
  **same `number[]` payload** line and column use, so the accessible data table
  and validator are inherited with **zero** generalization.
- `xAxis.categories`: the stage **labels**, length `N`, aligned to the values by
  index (absent → index `0..N-1`). Funnel reads `categories` as **data** (the
  stage names), **not** as an x-axis to draw — there is no x-axis.
- **One series.** Funnel is single-series by construction (the stages *are* the
  breakdown). A second series is not part-to-whole of one pipeline; the validator
  accepts it (forward-compatible) but the renderer draws only `series[0]`.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"funnel"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle. **Funnel is single-series**, so the default legend renders one entry; idiomatic funnels set `legend:false` and rely on the in-band stage labels (per-**stage** legend/toggle is a pie-family concern, deferred — see roadmap) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (stage → value). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | accepted (forward-compatible) but **inert** — funnel draws no axis; use it only as document metadata |
| `xAxis.categories` | string[] | index `0..N-1` | the **stage labels** (read as data, not drawn as an axis) |
| `yAxis.*` | object | — | accepted by the shared validator (forward-compatible) but **inert** — funnel has no value axis, no gridlines, no ticks |
| `series[].name` | string | `Series i` | legend + tooltip series name (the funnel name, e.g. "Conversion") |
| `series[].data` | number[] | — | the **stage values**, length `N`. Values are expected non-negative and (usually) descending; a `0` collapses that band to a point |
| `series[].color` | string \| gradient | palette by **stage** | the funnel paint. **Default (colorByPoint): each stage takes the next palette color by stage index** (like a pie). Set `series[].color` to paint the **whole funnel** one color instead — hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills every trapezoid; legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the whole funnel: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |
| **`subtype`** | string | `"funnel"` | **NEW field.** `"funnel"` = taper top→bottom, widest stage on top, last stage a rectangle of its own width; `"pyramid"` = the funnel **vertically flipped** (apex/point at top, widest base at the bottom — for hierarchies / population pyramids); `"neck"` = area/neck funnel (see `neckWidth`/`neckHeight`). Added via the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) |
| **`neckWidth`** | number | `0.3` | **NEW field.** Only meaningful for `subtype:"neck"`: the neck width as a **fraction of plot width** (0–1). Below the neck line the funnel stops tapering and runs straight down at this width |
| **`neckHeight`** | number | `0.25` | **NEW field.** Only meaningful for `subtype:"neck"`: the neck's **height as a fraction of plot height** (0–1), measured up from the bottom — the tapering region is the remaining `1 - neckHeight` on top |
| **`minWidth`** | number | `0` | **NEW field.** Minimum trapezoid edge width as a **fraction of plot width** (0–1), so a tiny (but non-zero) stage stays visible/hoverable instead of collapsing to an invisible sliver |
| **`reversed`** | bool | `false` | **NEW field.** Draw stages bottom-to-top (an alternate route to the `pyramid` silhouette while keeping data order); ignored when `subtype:"pyramid"` already sets the flip |

The new fields (`subtype`, `neckWidth`, `neckHeight`, `minWidth`, `reversed`) are
funnel-only selectors with no existing home in the line/column spec, so — exactly
as column did for `stacking`/`grouping` — they must be added in the **§5.4b
five-place lockstep** (schema + `validate.py` + `validate.go` + `spec.py` +
`spec.go`) plus `invalid-fixtures.json` when the renderers land. Until then they
are tolerated by the forward-compatible validator (unknown keys are ignored), so
every example here already passes `validate() == []`.

Fields carried over from the line/column spec but **inert** for funnel (no line,
no bars, no axes): `fillOpacity`, `lineWidth`, `dashStyle`, `step`, `curve`,
`marker`, `grouping`, `stacking`, `xAxis.title`, `yAxis.*` are accepted by the
shared validator (forward-compatible) but not consumed by the funnel marks. Full
schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[0].data` is `number[]` — one value per stage, the
  same shape line and column use. No `{x,y}` object model, so the `number[]`
  accessible data table renders faithfully with **no** generalization (the
  §5.4b-DT obligation applies only when the data element type changes).
- **Stages, not series.** The breakdown lives **inside one series**: N stages =
  N `data` entries. `data-color` cycles the palette **by stage index**
  (colorByPoint), the way a pie colors slices — not by series index.
- **Ordering.** Values are consumed in `data` order top→bottom for `funnel`,
  bottom→top for `pyramid`/`reversed`. The renderer does **not** sort — the author
  controls stage order.
- **The chart owns its scale.** There is no frame and no y-domain: the funnel
  computes its **own** value→width linear scale from `maxVal = max(data)`. Nothing
  is anchored to `ypix(0)`; there is no `nice_ticks`, no include-zero flag.

## Marks — what this renderer draws

Funnel is the **one Family A chart that does not delegate to `render_cartesian`**.
Its planned `render_svg` composes the substrate's **frame-independent** helpers —
theme resolution, the `<defs>` pre-pass + `SeriesStyle.fill`, `a11y_summary`, the
`<svg>` shell (open / background / title / subtitle / legend / close), `esc`,
`fmt_num`/`fmtNum`, `f1`/`:.1f`, and the shared runtime — and, **in place of the
axis+marks body**, emits its own centered-trapezoid marks. It calls **none** of
`build_frame` / `xpix` / `ypix` / `nice_ticks` / the axis or gridline emitters.

```python
# libs/python/peakcharts/charts/funnel.py  (planned)
from ._cartesian import resolve_theme, defs_prepass, a11y_summary, chrome_shell
from ..util import esc, fmt_num

def render_svg(spec) -> str:
    # own body between the shared shell's title/subtitle and legend — NO axes.
    return chrome_shell(spec, "Funnel", _funnel_body)   # _funnel_body emits the trapezoids
```
```go
// libs/go/funnel.go — package peakcharts  (planned)
func renderFunnelSVG(spec *ChartSpec) string {
    return chromeShell(spec, "Funnel", funnelBody)   // funnelBody emits the trapezoids; no axes
}
```

The body emits **exactly one** `<g class="pk-series" data-series="0">` and, inside
it, **one centered trapezoid `<polygon class="pk-slice pk-point">` per stage**:

```html
<g class="pk-series" data-series="0">
  <polygon class="pk-slice pk-point" data-series="0"
           data-series-name="Conversion" data-x="Visitors" data-y="18400"
           data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
           cx="410.0" cy="72.0"
           points="80.0,48.0 740.0,48.0 690.5,144.0 129.5,144.0"
           fill="#2f7ed8"/>
  … one .pk-slice.pk-point per stage …
</g>
```

- **Class:** `pk-slice pk-point`. `pk-point` is the **contract** class the runtime
  keys on (tooltip / highlight / legend-toggle / keyboard); `pk-slice` is a
  purely-cosmetic CSS hook (adding a class the runtime must *know about* is out of
  scope — NN#5). The trapezoid **is** the hoverable point; there are no separate
  markers.
- **Geometry:** each stage `i` occupies an equal-height horizontal band; the top
  edge width is `wscale(data[i])`, the bottom edge width is `wscale(data[i+1])`
  (the next stage), both **centered on `cx`** — see "Funnel layout" below. Emit as
  a `<polygon>` with four points in the pinned order (TL, TR, BR, BL). The last
  stage's bottom width is its own width (`funnel`, a rectangle) or `0` (a pointed
  apex for `pyramid`/`neck`).
- **Fill:** default **colorByPoint** — stage `i` uses palette color `i % len(palette)`
  (resolved server-side, like a pie). If `series[0].color`/`pattern` is set, read
  `fr.styles[0].fill` (**pattern → `url(#pat)`; gradient → `url(#grad)`; else the
  solid hex**) and paint **every** trapezoid with that single funnel-wide paint.
  Never leave a trapezoid unfilled (an unfilled funnel is a broken static chart —
  NN#5).
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (the funnel center x, constant
  for all stages) — the crosshair reads it — and by convention `cy` (the band's
  vertical center).
- **Labels:** the idiomatic funnel draws the stage label + value (and, optionally,
  conversion %) centered in each band as `<text>` — but that is a cosmetic
  overlay, not a contract element; keep it out of the `data-*` set.
- **Legend swatch:** with one series the shared **tail** emits one swatch (the
  funnel name). Set `legend:false` for the usual label-in-band funnel look.

## Funnel layout — the pinned geometry (its OWN, not the band/point scale)

Funnel does not touch `xpix`/`ypix`/`band_width`. Evaluate this arithmetic in
**exactly this operation order** in both languages so `f1` / `:.1f` rounding lands
ULP-for-ULP identically:

```
n         = len(data)
maxVal    = max(data)                                # the value→width reference
bandH     = plot_h / n                               # equal-height stage bands
cx        = plot_x + plot_w / 2                       # every band centered here
wscale(v) = plot_w * v / maxVal                       # value→width LINEAR scale (multiply THEN divide)

# per stage i (0-based, top→bottom for subtype "funnel"):
wtop(i)   = wscale(data[i])
wbot(i)   = wscale(data[i+1])   if i < n-1
            else wscale(data[i])            # subtype "funnel": last band is a rectangle
            else 0.0                        # subtype "pyramid"/"neck": last band tapers to a point
yTop(i)   = plot_y + bandH * i
yBot(i)   = plot_y + bandH * (i + 1)
xTL = cx - wtop/2 ; xTR = cx + wtop/2       # top edge
xBL = cx - wbot/2 ; xBR = cx + wbot/2       # bottom edge
points    = f"{xTL},{yTop} {xTR},{yTop} {xBR},{yBot} {xBL},{yBot}"   # TL TR BR BL
```

- **`maxVal = max(data)` is fixed**, not the first value — a non-monotone stage
  cannot overflow the plot. Pin `max` (not `data[0]`) in both languages.
- **`minWidth`** (fraction of `plot_w`): clamp every edge width up to
  `max(w, minWidth*plot_w)` **before** computing `xTL…xBR`, so a tiny non-zero
  stage stays visible. Apply the clamp identically in both languages.
- **`subtype:"pyramid"`** = the funnel **vertically flipped**: reflect each band's
  `yTop`/`yBot` about the plot mid-line (`y' = plot_y + plot_h - (y - plot_y)`) so
  the apex is at the top and the widest base at the bottom; the four points are
  re-ordered to stay CCW. `reversed:true` reaches the same silhouette by iterating
  stages bottom→top instead — pick one, do not double-flip.
- **`subtype:"neck"`** (area/neck funnel): split the plot into a **taper region**
  (top `1 - neckHeight` of `plot_h`) and a **neck** (bottom `neckHeight`). In the
  taper region widths run from `wscale(data[0])` down to `neckWidth*plot_w` at the
  neck line; in the neck every edge is exactly `neckWidth*plot_w` (a straight
  vertical column). Bands are still equal-height by stage; a stage straddling the
  neck line is split at the line. Pin `neckWidth`/`neckHeight` defaults (0.3 / 0.25).
- **Conversion / drop-off annotations** (optional labels): stage-vs-first =
  `data[i] / data[0] * 100`; drop-off-vs-previous = `data[i] / data[i-1] * 100`.
  These divisions need the **degenerate guard below** before dividing.

## Reused chrome (obtained from the substrate — never re-implemented)

Funnel is the **declared exception** (blueprint §2 Family A substrate-contract
note). It rides **NONE** of the x/y axis chrome — **no** plot axes, **no** axis
lines, **no** axis titles, **no** gridlines, **no** tick labels, **no**
`nice_ticks`/`ypix` value scale, and **neither** the point **nor** the band
x-scale. It shares only the **frame-independent** substrate:

- **Theme / palette** — resolved server-side (light/dark/custom); palette drives
  the per-stage colorByPoint fills.
- **`<defs>` pre-pass** — gradient / pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when the funnel needs them — no empty
  `<defs>` under the light theme).
- **A11y** — `role="img"` + `aria-label` + `<desc>` in the SVG + a visually-hidden
  **data table** (stage → value) in the HTML + keyboard nav. `a11y:false` restores
  the pre-a11y bytes. `data` stays `number[]`, so the existing table renders with
  **no** generalization.
- **`<svg>` shell** — open / background `<rect>` / title / subtitle / legend
  (bottom-center) / close, and the responsive `viewBox`.
- **Runtime** — `runtime/chart-interactions.js` unchanged (tooltip, highlight,
  legend-toggle, keyboard, crosshair).
- **Parity helpers** — `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1`
  (pixel coords) — all parity-locked.

Because funnel does not call `render_cartesian`, the substrate must expose these
non-axis helpers as reusable seams (a `chrome_shell` that emits the `<svg>` shell
+ title/subtitle/legend around a chart-supplied body). Factoring that seam is
funnel's only net-new substrate work; it emits **no** axis code, so Gate C
(additive-only, no stray `<defs>`/background under light) is preserved.

It passes the bare noun **`"Funnel"`** — expanded to `"Funnel chart with N stages…"`
by the shared `a11y_summary` (byte-for-byte, same helper line/column use).

## Parity traps (verify before the byte-parity gate)

- **Value→width ORDER** — evaluate `wscale(v) = plot_w * v / maxVal` as multiply
  **then** divide, in that order; a reassociated `plot_w * (v / maxVal)` can
  diverge after `f1` rounding.
- **`maxVal` source** — pin `max(data)` (not `data[0]`) in both languages so a
  non-monotone stage is handled identically.
- **Degenerate scale** — `maxVal <= 0` (all-zero data) would divide-by-zero; pin
  the rule identically **before** the divide (Python guards → width 0; Go yields
  `NaN`→`fmtNum`→`"0"`). Same guard on the conversion-% divides (`data[0]==0`,
  `data[i-1]==0`). Mirror the size-scale degenerate discipline (§3.2).
- **Polygon point ORDER** — TL, TR, BR, BL (clockwise); for `pyramid`/`reversed`
  keep the winding consistent after the vertical flip. A flipped winding still
  fills but the `points` string bytes must match across languages.
- **`minWidth` clamp** — apply `max(w, minWidth*plot_w)` **before** deriving
  corner x's, in both languages, or a clamped-vs-unclamped edge diverges.
- **Neck split math** — `neckHeight`/`neckWidth` fractions and the taper→neck
  transition must be computed in the same order; a stage straddling the neck line
  is split at the same y in both languages.
- **colorByPoint index** — stage color = palette`[i % len(palette)]`; keep the
  modulo and palette order identical (never range-over-map in Go).
- **`data-y` is the raw stage value** — carries `esc(fmt_num(data[i]))`, the value
  the user supplied, never a width or a percentage.
- **Formatters** — `cx,cy` and every `points` coordinate via `:.1f`/`f1`;
  `data-y`, radii via `fmt_num`/`fmtNum`; every user string (`data-series-name`,
  `data-x`, custom color) via `esc`. A leaked raw `<` fails the XSS tests.
- **No stray chrome** — shell emits no empty `<defs>` and no axis/gridline bytes
  under the light theme (additive-only — Gate C).
- **Byte-parity hygiene** — goldens carry **no trailing newline**, UTF-8 no BOM;
  iterate stages by index; keep the single series/point/legend `data-series="0"`
  in lockstep.

## Accessibility & DOM contract

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the
selectors + `data-*` below (`spec/svg-contract.md`). Emit them correctly and
tooltip, highlight, legend-toggle, and keyboard nav all work with **zero JS
changes**.

- **Series group:** `.pk-series[data-series=0]` — one group (funnel is
  single-series); every stage `.pk-point` inside it carries `data-series="0"`,
  consistent with the one legend item (do not renumber).
- **Datum mark:** `.pk-slice.pk-point` per stage carries **all** of `data-series`,
  `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover` —
  mandatory even though a `<polygon>` ignores the hover `r`.
- **Crosshair anchor:** every `.pk-point` carries a `cx` (funnel center x) and by
  convention `cy` (band vertical center).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(stage label)`; `data-y = esc(fmt_num(value))` — the raw stage
  value; `data-color = fr.styles resolved stage color (colorByPoint)`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs (`cx,cy`, `points`) use
  `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** (stage → value) in the HTML; keyboard
  nav walks the stages. `a11y:false` restores the pre-a11y bytes. Funnel keeps
  `data: number[]`, so the existing `number[]` data table renders faithfully with
  **no** generalization.
- **Static-first:** the chart is fully readable with JS disabled — trapezoids are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "funnel",
  "title": "Signup Conversion Funnel",
  "subtitle": "Stage-by-stage drop-off, last 30 days",
  "legend": false,
  "xAxis": { "categories": ["Visitors", "Signups", "Trials", "Active", "Paid"] },
  "series": [
    { "name": "Conversion", "data": [18400, 9200, 5100, 2600, 1180] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, default `funnel` subtype, colorByPoint palette, `legend:false`, last stage a rectangle |
| [`examples/pyramid.json`](examples/pyramid.json) | `subtype:"pyramid"` — vertical flip, apex at top / widest base at bottom |
| [`examples/neck.json`](examples/neck.json) | `subtype:"neck"` + `neckWidth`/`neckHeight` — area/neck funnel with a straight closing neck |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a whole-funnel gradient `series[].color` (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) + `minWidth` floor |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field
(series name, stage label, custom color) so the XSS tests run against the funnel
marks (§5.5d). `FUNNEL_CASES = ["basic","pyramid","neck","dark","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/funnel/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="funnel",
    title="Signup Conversion Funnel",
    legend=False,
    x_axis=Axis(categories=["Visitors", "Signups", "Trials", "Active", "Paid"]),
    series=[Series("Conversion", [18400, 9200, 5100, 2600, 1180])],
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
- **Hover a stage** → tooltip (stage, series, value) + trapezoid highlight.
- **Click the legend item** → toggle the funnel on/off (single series).
- **Keyboard** → arrows walk the stages; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — trapezoids filled and
  readable, stage labels in-band.

## Rendering notes

- No axes, no gridlines, no ticks — funnel draws **only** the centered trapezoid
  stack plus optional in-band labels. Width is the sole value encoding.
- Stage colors cycle the theme palette by **stage index** (colorByPoint); a single
  `series[].color`/`pattern` overrides the whole funnel with one paint via the
  `<defs>` pre-pass.
- `subtype` picks the silhouette: `funnel` (taper, rectangular base), `pyramid`
  (flipped, pointed apex), `neck` (taper into a straight neck via
  `neckWidth`/`neckHeight`). `minWidth` keeps tiny stages visible.
- Funnel is the **declared substrate exception** — it does not go through
  `render_cartesian` and forces **no** axis generalization; its only net-new
  substrate seam is the non-axis `chrome_shell` (title/subtitle/legend/shell)
  that every future pie-family part-to-whole chart can reuse.

## Not yet supported (roadmap)

- Live renderers (`funnel.py` / `funnel.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today.
- **Per-stage legend + per-stage toggle** (pie-style colorByPoint legend) — needs
  a legend variant keyed on stage, not series; a shared pie/part-to-whole concern.
- **Per-stage color override** and in-band data-label templating — arrive with the
  point-model + label engine (they need a per-datum `name`/`color`).
- **`funnel3d` / `pyramid3d`** — 3D isometric variants require the deferred
  depth-projection layer that conflicts with static-first byte-parity (blueprint §6).
- Horizontal (left→right) funnel, sliced/exploded stages, and a rotated-neck
  variant — later variants layered on this base.
