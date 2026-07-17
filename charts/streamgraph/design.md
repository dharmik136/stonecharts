# Chart: Streamgraph (`streamgraph`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> variant build detail: data model, marks, the baseline-offset transform, reused
> chrome, parity traps, and the a11y DOM contract.

- **Chart id:** `streamgraph`
- **Spec `type`:** `"streamgraph"`
- **Class:** `variant` (Family A — Cartesian/XY) · rides **Area** (Build rank 5) ·
  **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; streamgraph rides the shared cartesian frame +
  the area renderer once extraction/stacking land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2 Family A,
  §3.3 Rank 5, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/streamgraph.py` · `libs/go/streamgraph.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A streamgraph: several series drawn as **stacked, filled area ribbons** over a
shared ordered x-axis, but displaced off a **floating baseline** instead of the
zero line. The whole stack "flows" around a central axis (**silhouette /
inside-out**) or around a wiggle-minimizing spine (**wiggle**), so each series
reads as an organically-shaped river of thickness. A ribbon's *thickness* at each
x encodes its value; the *stack total* is the outer envelope. It is the
theme-river view of **event / log / request volume over time**.

Streamgraph is a **variant of Area** — it reuses the **entire** area renderer
(the stacked `pk-series-area` path builder, gradients/patterns, defs pre-pass,
markers) and adds exactly one thing: a **baseline-offset transform** that replaces
the zero baseline (`fr.ypix(0.0)`) — and the plain cumulative baseline of a
stacked area — with a per-category **wiggle** or **silhouette** offset. The
**frame** owns the resulting floating y-domain (the offset envelope), so the
marks never recompute a scale. It forces **one** reusable generalization: the
**baseline-offset transform** + the frame's **offset-aware (non-zero-anchored)
y-domain**.

## Use it when

- Your x is **ordered time / steps** (minutes, hours, weeks, versions) and you
  want to show how the **composition and total volume** of many series **evolves**
  — the overall *shape of the flow* matters more than reading any one value
  precisely.
- You have **several-to-many series** whose **sum** is meaningful (total log
  volume, total requests) and you want an organic, low-clutter "theme river."
- Rows look like: `time -> value_a, value_b, value_c …` (many series sharing one
  ordered x), values **≥ 0**.

Do **not** use it for: **precise reading** of individual values (the floating
baseline makes exact values hard — use a zero-baselined `area` (stacked/percent)
or `column`); **part-to-whole of a single total** (use pie/donut); a **trend of
one or a few series** (use `line-basic`); **x/y correlation** (use `scatter`); or
data with **meaningful negatives** (the offset envelope assumes non-negative
thickness — see roadmap). See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the ordered x labels, length `N` (absent → index `0..N-1`).
- each `series[].data`: `N` numbers **≥ 0**, aligned to `categories` by index.
- Identical value payload to `line`/`area` (`data: number[]`). The stack and the
  wiggle/silhouette displacement are **transforms over these y-values**, selected
  by the chart-level `offset` field — **not** a different data shape. A bare
  `number` stays valid (x = index), so line/area/column/streamgraph goldens never
  move when the richer point model lands (§3.3 Rank 3).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"streamgraph"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the ribbon fill) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table. `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`offset`** | string | `"wiggle"` | **NEW field.** The baseline-offset mode. `"wiggle"` = minimal-wiggle spine (the classic streamgraph); `"silhouette"` = inside-out, the whole stack centered so it spans `[-T/2, +T/2]` at each x. The **frame** owns the resulting floating y-domain (the offset envelope, not a zero anchor). Added in the §5.4b five-place lockstep (schema + both validators + both spec models + invalid fixtures) — the exact analog of column's `stacking` |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | ordered x labels (ribbon vertices) |
| `yAxis.title` | string | — | axis label (usually omitted — the floating baseline makes the absolute y scale non-literal; the axis reads relative thickness) |
| `yAxis.min` / `yAxis.max` | number | auto (offset envelope) | clamp the y range; **the value axis is NOT zero-anchored** (`include_zero=False`) — the frame's domain is the wiggle/silhouette envelope, unless clamped |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | ribbon thickness values, length `N`, **≥ 0** |
| `series[].color` | string \| gradient | palette by index | the **ribbon fill**: hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (fills the whole ribbon; legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the ribbon: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |
| `series[].fillOpacity` | number | 1 (ribbon is the mark) | ribbon fill opacity. Unlike line/area (default 0 = no fill), a streamgraph ribbon is **always** filled — it *is* the mark; `fillOpacity` only tunes translucency |
| `series[].curve` | string | — | `monotone` = smooth (Fritsch-Carlson) ribbon boundaries via the reused spline builder; default = polygonal (straight) ribbons |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:3.5}` | per-vertex point markers on the ribbon's top edge; often set `{enabled:false}` for a clean stream (the `.pk-point` element is still emitted for the DOM contract) |

Fields carried over from the line spec but **inert** for streamgraph (there is no
boundary stroke on a classic ribbon): `lineWidth`, `dashStyle`, `step` are
accepted by the shared validator (forward-compatible) but not consumed by the
streamgraph marks. The inherited stacking selectors are **implied, not authored**:
a streamgraph is inherently stacked, so `stacking` is effectively `"normal"` and
`grouping` is meaningless (a stream is one stacked band per x — never side-by-side
sub-bands). Full schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — one thickness per category,
  the same shape line/area/column use. No `{x,y}` object model (that arrives with
  scatter, rank 3).
- **Inherently stacked.** The `streamgraph` type means "stacked area with a
  floating baseline." In series index order, compute the cumulative bottom/top of
  every ribbon (the `"normal"`-stacking transform, reused from column/area):
  `cumBottom[k][i] = Σ_{j<k} v[j][i]`, `cumTop[k][i] = cumBottom[k][i] + v[k][i]`,
  and the category total `T[i] = cumTop[K-1][i] = Σ_k v[k][i]`.
- **The offset displaces the stack.** A per-category baseline `b[i]` (the y-value
  of the **bottom** of the whole stack) is added to every cumulative value:
  ribbon `k` at category `i` spans `[b[i] + cumBottom[k][i], b[i] + cumTop[k][i]]`.
  `b[i]` is `0` for a plain stacked area; the streamgraph makes it float
  (`silhouette` or `wiggle`, below).
- **The frame owns the y-domain.** It is the **offset envelope**, computed in the
  pinned order: `y_min = min_i b[i]` (the stack bottom, since `cumBottom[0][i]=0`),
  `y_max = max_i (b[i] + T[i])` (the stack top). The frame delegates with
  `include_zero=False` — the baseline floats, so 0 is **not** forced into the
  domain (forcing 0 would waste space and mis-scale a wiggle stream). The marks
  never recompute a scale.

## Baseline offset — the pinned transform (net-new; the ONE generalization)

This is the streamgraph's only net-new machinery — the analog of column's band
layout. It replaces `fr.ypix(0.0)` (line/area/column baseline) and the plain
cumulative baseline (stacked area) with a floating `b[i]`. Evaluate it in
**exactly this operation order** in both languages so the cumulative floats and
`%g` output land ULP-for-ULP identically (blueprint §3.2 stacking-transform / §4).

Common prelude (both modes) — accumulate in **series index order** (pinned):

```
T[i]          = Σ_k v[k][i]                         # category total, k = 0..K-1 in index order
cumBottom[k][i] = Σ_{j<k} v[j][i]                   # running sum below ribbon k
cumTop[k][i]    = cumBottom[k][i] + v[k][i]
```

**`silhouette` (inside-out, centered):**

```
b[i] = -T[i] / 2.0            # for every category i; stack spans [-T/2 , +T/2]
```

**`wiggle` (minimal-wiggle spine):** an iterative left→right sweep that shifts the
baseline to minimize the total weighted "wiggle" (slope²·thickness) of the layers
(Byron–Wattenberg). Pin the nested loop orders and the divide guard:

```
b[0] = 0.0
y    = 0.0
for i in 1 .. N-1:                                  # category index
    num = 0.0                                       # Σ  weight_k · move_k
    den = 0.0                                       # Σ  move_k
    for k in 0 .. K-1:                              # series INDEX order (pinned)
        move_k   = cumTop[k][i] - cumTop[k][i-1]     # Δ of ribbon k's cumulative top
        weight_k = move_k / 2.0                      # half its own move …
        for j in 0 .. k-1:                          # … plus the full move of every ribbon below it
            weight_k += cumTop[j][i] - cumTop[j][i-1]
        num += weight_k * move_k
        den += move_k
    if den != 0.0:                                  # degenerate guard BEFORE the divide (see traps)
        y -= num / den
    b[i] = y
```

- `b[0] = 0` and the commit-after-update ordering above are **fixed** — they
  reproduce the standard minimal-wiggle baseline (`b[i] = -Σ_{t≤i} (num_t/den_t)`).
- `offset` is a **fixed enum** (`wiggle` | `silhouette`), not a free author knob;
  default `wiggle` (the classic streamgraph).
- The **frame's** offset-aware y-domain uses the **same** `b[i]` array and the
  **same** summation order — pin both so the envelope and the ribbon floats match
  across languages.

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies **only**
a marks callback and re-implements no chrome (§5.2). It uses the **point** x-scale
(like line/area — categories map to vertices, ribbons connect them; **not** the
band scale, which is column/bar) and `include_zero=False` (floating baseline):

```python
# libs/python/peakcharts/charts/streamgraph.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Streamgraph", "point", _streamgraph_marks,
                            include_zero=False)   # frame reads spec.offset → floating y-domain
```
```go
// libs/go/streamgraph.go — package peakcharts
func renderStreamgraphSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Streamgraph", "point", streamgraphMarks, false)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it **one filled ribbon `<path>`** plus **one `.pk-point`
per category** (on the ribbon's cumulative-top edge — reused verbatim from the
area/line marker loop):

```html
<g class="pk-series" data-series="0">
  <path class="pk-series-area" data-series="0"
        d="M64.0 210.3 L216.0 188.7 L368.0 96.4 … L368.0 150.9 L216.0 244.1 L64.0 261.0 Z"
        fill="#2f7ed8"/>
  <circle class="pk-point" data-series="0"
          data-series-name="api" data-x="00:00" data-y="340"
          data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
          cx="64.0" cy="210.3" r="3.5" fill="#2f7ed8"/>
  … one .pk-point per category …
</g>
```

- **Ribbon path (`pk-series-area`).** Build the band exactly like stacked-area's
  band-fill-between-cumulative-baselines (§3.3 Rank 5), but with the floating
  baseline: **top edge** left→right over `ypix(b[i] + cumTop[k][i])`, then **bottom
  edge** right→left over `ypix(b[i] + cumBottom[k][i])`, then `Z`. Reuse `_path_d`
  (straight) or `_spline_d` (`curve:"monotone"`) — run once per edge — so the `f1`
  path coordinates match across languages **for free**.
- **Fill (NN#2 — never leave a ribbon unfilled).** The ribbon **is** the mark, so
  read `fr.styles[si].fill` — the always-populated resolved paint (the same field
  column's bars read) — and resolve **pattern → `url(#pat)`; gradient → `url(#grad)`;
  else the solid hex.** Do **not** read `area_fill` (it is `None` when `fillOpacity`
  is unset — a streamgraph must fill anyway). Add `fill-opacity` only when
  `series[].fillOpacity` is set (`fr.styles[si].area_op`); the default is full
  opacity (stacked ribbons don't overlap).
- **`.pk-point` per category.** Reuse the area/line marker loop verbatim, anchored
  to the **cumulative-top edge** vertex: `cx = fr.xpix(i)`, `cy = fr.ypix(b[i] +
  cumTop[k][i])`. `marker.enabled:false` hides the visual dot, but the `.pk-point`
  element (with all `data-*` + `cx`/`cy`) is **always** emitted — the runtime keys
  the tooltip / crosshair / keyboard nav on it.
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (the crosshair reads it) and
  by convention `cy` (the vertex). Without `cx` the crosshair breaks.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Reused chrome (obtained from the frame — never re-implemented)

Streamgraph inherits, with **zero** re-implementation (§3.1, §4.2), everything
area inherits:

- Plot area + margins; x/y axes + axis lines + axis titles.
- Linear y-scale via the **frame-owned offset envelope** → `ypix`; y gridlines +
  labels. (The domain is the wiggle/silhouette envelope — `include_zero=False` —
  computed by the frame, not the marks.)
- Ordered x-axis via the **point** `xpix`; the shared x-label loop lands labels
  under vertices with no per-chart label code.
- Titles + subtitle; legend (bottom-center); crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill` /
  `area_fill`, id-scoping via `cid` (defs emitted only when a series needs them —
  no empty `<defs>` under the light theme).
- The **entire area/line path machinery**: `_path_d`, `_spline_d` (`monotone`),
  the marker loop, area fill / gradient / pattern emission.
- The **stacking transform** (cumulative bottom/top in index order) — shared with
  column/bar/area.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="point"` and `include_zero=False`, passing the
bare noun **`"Streamgraph"`** — the frame expands it to `"Streamgraph chart with N
series…"` byte-for-byte. The **only** net-new logic is the baseline-offset
transform + the frame's offset-aware domain.

## Parity traps (verify before the byte-parity gate)

- **Summation order** — accumulate `T[i]`, `cumBottom`, `cumTop` in **series index
  order**; the wiggle sweep's inner `k`/`j` loops and the frame's envelope use the
  **same** order. A reassociated sum diverges after `%g`.
- **Wiggle loop order + commit timing** — evaluate the sweep exactly as written
  (`b[0]=0`; per category: build `num`/`den` over `k`, inner `j` over layers below,
  update `y` *then* commit `b[i]`). Any reorder changes the floats.
- **Degenerate wiggle divide** — a category with `den == 0` (e.g. a flat/empty
  column) would divide-by-zero; pin `if den != 0.0` **before** the divide,
  identically in both languages (Python raises `ZeroDivisionError`, Go yields
  `NaN`→`fmtNum`→`"0"` — a real divergence if unguarded). Same rule shape as the
  bubble size-scale and the percent-stacking total (§3.2, §5.6).
- **Frame owns the y-domain** — the marks must call `fr.ypix` only; recomputing
  the envelope (even to identical bytes) is a defect (NN, §7.1). `include_zero`
  MUST be **False** — a `True` would force 0 into a floating stream and mis-scale
  it (both languages wrong identically → passes byte-parity but is wrong).
- **Ribbon-fill resolution** — read `fr.styles[si].fill` (always populated): pattern
  → `url(#pat)`; gradient → `url(#grad)`; else solid hex. Reading `area_fill`
  silently drops the fill when `fillOpacity` is unset (the ribbon would vanish —
  NN#2). Never emit an unfilled ribbon.
- **`data-y` under stacking** — carries the **raw per-series thickness** `v[k][i]`,
  **not** the cumulative or offset value (the tooltip shows what the user supplied),
  while the geometry uses `b[i] + cumTop/cumBottom`.
- **Path edge direction** — top edge left→right, bottom edge right→left, then `Z`
  (a single closed ribbon per datum-column pair). Same builder run twice, so `f1`
  coords match for free (as area-range concatenates two `_path_d` passes, §3.3
  Rank 10).
- **Formatters** — `cx,cy` and every path `d` number via `:.1f`/`f1`; `data-y`,
  radii via `fmt_num`/`fmtNum`; every user string via `esc`. A leaked raw `<`
  fails the XSS tests.
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
  integer series index, **consistent** across the group, its points, and the
  legend item (do not renumber).
- **Datum mark:** `.pk-point` carries **all** of `data-series`, `data-series-name`,
  `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover` — mandatory even when
  the marker dot is hidden (`marker.enabled:false`).
- **Crosshair anchor:** every `.pk-point` carries a `cx` (vertex x) and by
  convention `cy` (top-edge y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(category)`; `data-y = esc(fmt_num(value))` — the **raw** per-series
  thickness, **not** the cumulative/offset value; `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML; keyboard nav walks the
  vertices. `a11y:false` restores the pre-a11y bytes. Streamgraph keeps
  `data: number[]` (the raw thicknesses), so the existing `number[]` data table
  renders faithfully with **no** generalization (that obligation applies only when
  the data element type changes — scatter and later, §5.4b-DT).
- **Static-first:** the chart is fully readable with JS disabled — ribbons are
  server-rendered and filled; the crosshair ships `display:none`; the tooltip is
  JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "streamgraph",
  "title": "Log Volume by Source",
  "subtitle": "Wiggle baseline — events per minute",
  "offset": "wiggle",
  "xAxis": { "title": "Time", "categories": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"] },
  "series": [
    { "name": "auth",      "data": [120, 90, 210, 480, 520, 300] },
    { "name": "api",       "data": [340, 280, 610, 1180, 1240, 720] },
    { "name": "worker",    "data": [80, 60, 150, 300, 340, 190] },
    { "name": "scheduler", "data": [30, 200, 45, 60, 55, 210] },
    { "name": "gateway",   "data": [260, 210, 500, 940, 980, 560] }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | default `offset:"wiggle"`, 5-series theme-river, minimal-wiggle spine |
| [`examples/silhouette.json`](examples/silhouette.json) | `offset:"silhouette"`, inside-out centered stack (`[-T/2,+T/2]`) |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + `offset:"wiggle"` + a gradient ribbon fill (defs pre-pass + `SeriesStyle.fill` → `url(#grad)`) + `curve:"monotone"` smooth ribbons |
| [`examples/adversarial.json`](examples/adversarial.json) | hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field (series name, category label, custom color) — drives the XSS tests against the streamgraph marks (§5.5d) |

`STREAMGRAPH_CASES = ["basic","silhouette","themed-dark","adversarial"]`. The
`adversarial` case is the golden that pins escaping: it carries hostile strings in
series name, category label, and custom ribbon color so a renderer that leaks a
raw `<` fails a test.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/streamgraph/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="streamgraph",
    title="Log Volume by Source",
    offset="wiggle",
    x_axis=Axis(title="Time", categories=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]),
    series=[
        Series("auth",      [120, 90, 210, 480, 520, 300]),
        Series("api",       [340, 280, 610, 1180, 1240, 720]),
        Series("worker",    [80, 60, 150, 300, 340, 190]),
        Series("scheduler", [30, 200, 45, 60, 55, 210]),
        Series("gateway",   [260, 210, 500, 940, 980, 560]),
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
- **Hover a ribbon vertex** → tooltip (x, series, raw thickness) + highlight + crosshair.
- **Click a legend item** → toggle that stream on/off.
- **Keyboard** → arrows walk the vertices; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — ribbons filled and readable.

## Rendering notes

- The value axis is **not** zero-anchored (`include_zero=False`); the y range is
  the wiggle/silhouette **offset envelope** the frame computes, unless
  `yAxis.min/max` clamp it. Absolute y labels are typically de-emphasized — a
  streamgraph communicates relative thickness and flow.
- Ribbons use the **point** x-scale (`x_scale="point"`, shared with line/area) —
  vertices are evenly spaced; labels land under vertices. Streamgraph does **not**
  use the band scale.
- `offset:"silhouette"` centers the stack (`b[i] = -T[i]/2`); `offset:"wiggle"`
  (default) runs the minimal-wiggle sweep. Both are pinned in evaluation order for
  Py/Go parity.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern color fills the whole ribbon via the `<defs>` pre-pass.
- `curve:"monotone"` smooths the ribbon boundaries via the reused spline builder.
- Streamgraph is a **variant**: it re-uses the area renderer wholesale and forks
  **nothing** — the only net-new code is the baseline-offset transform (shared
  substrate + one flag).

## Not yet supported (roadmap)

- Live renderers (`streamgraph.py` / `streamgraph.go`) — deferred; design +
  examples + validation are complete. Only `line` renders today; streamgraph lands
  once the §4 extraction, the stacking transform, and the area renderer are in
  place (it rides Area, Rank 5).
- **Inside-out series ORDER** (d3 `stackOrderInsideOut`) — reorder series by onset
  so the largest/earliest streams sit near the spine (the classic aesthetic).
  Today ribbons draw in series index order.
- **Negative values** — the offset envelope assumes non-negative thickness; mixed
  positive/negative streams are undefined and out of scope for v1.
- **Area-spline-only ribbons, interactive baseline toggle** (wiggle ⇄ silhouette
  in the browser), and per-stream annotations — variants layered on this base.
