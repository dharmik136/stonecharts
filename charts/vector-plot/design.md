# Chart: Vector plot (`vector-plot`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this file follows the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which itself
> copies [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the
> sibling build detail: data model, marks, the arrow-glyph + length-scale, reused
> chrome, parity traps, and the a11y DOM contract.

- **Chart id:** `vector-plot`
- **Spec `type`:** `"vector-plot"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; vector-plot rides the shared cartesian frame
  once scatter's numeric-x-axis + point model land — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2 Family A, §3.2, §4, §5)
- **Renderers (planned):** `libs/python/stonecharts/charts/vector_plot.py` · `libs/go/vector_plot.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A vector plot (quiver / vector-field chart): one or more series drawn as
**arrow glyphs** on a plane with a **numeric x-axis** and a **numeric y-axis**.
Each datum carries **four** numbers — `x`, `y`, `direction`, and `length`.
`(x, y)` place the arrow's anchor; **`direction` rotates the arrow** (degrees,
`0` = north / up, increasing clockwise) and **`length` scales its pixel size**
through a shared **length-scale**. The arrow **is** the hoverable, interactive
element (it replaces the line chart's point marker, the column chart's bar, and
the bubble chart's circle).

Vector-plot is a Cartesian sibling that rides directly on **scatter** (which
landed the **numeric-x-axis** and the **`{x,y}` point model**) and adds exactly
two things: a **length-scale** (`length → arrow pixel length`, analogous to
bubble's `z → radius` size-scale) and an **arrow-glyph mark** (a rotated shaft +
arrowhead path). It introduces no new chrome and no new axis machinery.

## Use it when

- You have a **field of directed magnitudes** sampled over a plane — a wind
  field (heading + speed), a fluid/flow field, a gradient field, a force field,
  a current map — and you want direction **and** magnitude at each `(x, y)`
  location shown at a glance.
- The x and y are both **continuous numbers** (positions in a field, no shared
  category ordering) and each sample has an **angle** (`direction`) and a
  **non-negative magnitude** (`length`).
- Rows look like: `x, y, direction, length` per point (position=(30,25),
  heading=90°, speed=12).

Do **not** use it for: an x/y correlation with **no** direction/magnitude (use
`scatter`), correlation **plus a size magnitude only** (use `bubble`), a
**trend** over ordered/continuous x (use `line-basic`), a **magnitude across
discrete categories** (use `column`), or **part-to-whole** (use pie/donut). For
a **meteorological** speed+direction glyph specifically, `windbarb` is the
domain-specific sibling. See [`CHARTS.md`](../../CHARTS.md).

## Data shape

- Each point is an `{x, y, direction, length}` tuple: `x`/`y` are numeric
  coordinates, `direction` is an **angle in degrees** (`0` = up/north, clockwise
  positive), `length` is a **non-negative magnitude** mapped to a pixel arrow
  length by the length-scale.
- The **length-domain is global** — `lmax` is reduced over **every** point of
  **every** series (see [Length scale](#length-scale--the-pinned-geometry)) so a
  given `length` maps to the **same** pixel size everywhere and arrows are
  comparable across the field and across series.
- **Transitional representation (what the examples carry today).** The canonical
  `{x,y,direction,length}` datum (and its positional `[x,y,direction,length]`
  sugar) is the **point model** that scatter/bubble introduce (§3.2, §3.3
  Rank 3–4); it is **not yet accepted by the current validator**, which still
  requires `series[].data` to be `number[]` (the "bare number stays valid" fast
  path — a bare number is `y`, `x = index`). So until the point model lands, an
  example vector-plot carries four parallel arrays, exactly as `bubble` carries
  `x`/`data`/`z`:
  - `series[].data` — the **`y`** values, `number[]` (validated today);
  - `series[].x` — the **`x`** values, `number[]` (forward-compatible, ignored by
    the validator);
  - `series[].direction` — the **`direction`** angles (degrees), `number[]`
    (forward-compatible);
  - `series[].length` — the **`length`** magnitudes, `number[]`
    (forward-compatible).

  These four parallel arrays are the transitional bridge to the future datum
  `{x: x[i], y: data[i], direction: direction[i], length: length[i]}`; when the
  point-model normalization lands they fold into
  `data: [{x,y,direction,length}, …]` (or `[[x,y,direction,length], …]`) with
  **no change to the rendered bytes**, and the bare-number path keeps
  line/column goldens frozen (§3.3 Rank 3 byte-identity gate).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"vector-plot"` |
| `id` | string | `sc` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is a small arrow glyph in the series color) |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (generalized to render `x, y, direction, length` per row — §5.4b-DT). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| `xAxis.title` | string | — | axis label |
| `xAxis.min` / `xAxis.max` | number | auto (nice ticks, **no** forced 0) | clamp the **numeric** x range; unlike a value axis the x-domain is **not** zero-anchored (`include_zero=False`) — a field with x∈[100,200] must not be dragged to 0 |
| `xAxis.gridLine` | object | `{enabled:false}` | **vertical** x-gridline styling (meaningful — the x-axis is numeric): `{enabled, color, dashStyle}`, `dashStyle` ∈ solid/dashed/dotted. Reuses the existing gridLine object, applied to the x ticks |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, **no** forced 0) | clamp the numeric y range; the free numeric y-axis is likewise **not** zero-anchored |
| `yAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | horizontal gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| **`vectorLength`** | number | `20` | **NEW field.** The **pinned max arrow pixel length** — the longest magnitude (`lmax`) maps to this many pixels; every other arrow scales linearly against it (see [Length scale](#length-scale--the-pinned-geometry)). Chart-level. Ignored by today's validator (unknown key); folds in forward-compatibly |
| **`rotationOrigin`** | string | `center` | **NEW field.** Where the arrow pivots on its `(x,y)` anchor: `center` (arrow midpoint at the point), `start` (tail at the point), or `end` (head at the point). Forward-compatible; default `center` |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | the **`y`** values, length `N` (see [Data shape](#data-shape)) |
| **`series[].x`** | number[] | index `0..N-1` | **the `x` values**, length `N`, aligned to `data` by index. Forward-compatible parallel array (folds into the `{x,y,direction,length}` datum). Absent → `x = index` |
| **`series[].direction`** | number[] | — | **the `direction` angles** in degrees, length `N`, aligned to `data` by index (`0` = up/north, clockwise positive). Forward-compatible parallel array |
| **`series[].length`** | number[] | — | **the `length` magnitudes**, length `N`, aligned to `data` by index. Non-negative; drives the arrow pixel length via the length-scale. Forward-compatible parallel array |
| `series[].color` | string \| gradient | palette by index | the **arrow paint** (applied to the glyph **stroke** — a vector is a line glyph, not a filled area): hex `#2f7ed8`, or a `{type:linearGradient, x1,y1,x2,y2, stops:[{offset,color,opacity}]}` object (paints every arrow; legend swatch + `data-color` use stop 0) |
| `series[].lineWidth` | number | `1.5` | **arrow stroke width** (px). Vector-plot **consumes** `lineWidth` (the shaft/arrowhead thickness); line's default is `2`, vector-plot's is a slightly thinner `1.5` so a dense field stays legible |
| `series[].pattern` | object | — | hatch paint for the arrow: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`, applied to the stroke) |

Fields carried over from the line spec but **inert** for vector-plot (no line
path, no area, no bands): `fillOpacity`, `dashStyle`, `step`, `curve` are
accepted by the shared validator (forward-compatible) but not consumed by the
vector marks. `marker` is **ignored** — the arrow glyph is the mark, not a
circle/square marker. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** four aligned `number[]` arrays per series — `data` (`y`),
  `x`, `direction`, and `length` — one tuple
  `{x[i], y[i], direction[i], length[i]}` per index `i`. This is the transitional
  form of the canonical `{x,y,direction,length}` datum (see
  [Data shape](#data-shape)). A missing `x` array defaults to `x = index`;
  `direction` and `length` are required for a genuine vector (absent `length`
  degenerates every arrow to the same fixed pixel length; absent `direction`
  points every arrow up/north at `0°`).
- **Numeric x, numeric y — no zero-anchor.** Both axes are **free numeric** axes
  built by the shared value-axis routine with **`include_zero=False`**: the
  domain comes from the data only (`nice_ticks` over `min/max`), never forced
  through 0. This is scatter's rank-3 caveat (§3.2, §4.2) — carrying the
  column/bar/area y-baseline zero-anchor into a free x (or free y) would wrongly
  drag a field sampled at x∈[100,200] down to the origin. `xAxis.min/max` and
  `yAxis.min/max` clamp the respective domain when set.
- **direction → rotation.** The angle (degrees) rotates the arrow. Convention is
  pinned: **`0°` = up/north**, increasing **clockwise** (so `90°` = east/right,
  `180°` = down/south, `270°` = west/left). Converted to an SVG unit vector
  (y grows downward) below.
- **length → arrow pixels (the length-scale).** One of the two net-new
  generalizations. `length` maps **linearly** to a pixel arrow length
  `≤ vectorLength`, scaled against the **global** `lmax`. The reduction and
  formula are pinned below.
- **The frame owns the axis domains.** The marks call `fr.xpix`/`fr.ypix` only
  and compute the length-scale + arrow geometry themselves; they **never**
  recompute an axis scale (NN, §7.1).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). It delegates with
the **numeric** x-scale (`x_scale="linear"`, landed by scatter) and
**`include_zero=False`** (free numeric x/y):

```python
# libs/python/stonecharts/charts/vector_plot.py
from ._cartesian import render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Vector plot", "linear", _vector_marks, include_zero=False)
```
```go
// libs/go/vector_plot.go — package stonecharts
func renderVectorPlotSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Vector plot", "linear", vectorMarks, false)
}
```

The marks callback first reduces the **global** length-domain
(§ Length scale), then emits **exactly one**
`<g class="sc-series" data-series="{si}">` per series, and inside it **one arrow
`<path>` per point**:

```html
<g class="sc-series" data-series="0">
  <path class="sc-vector sc-point" data-series="0"
        data-series-name="10:00 UTC" data-x="30" data-y="25"
        data-direction="90" data-length="12"
        data-color="#2f7ed8" data-r="1.5" data-r-hover="1.5"
        cx="512.0" cy="188.0"
        d="M502.0 188.0 L522.0 188.0 M516.6 183.7 L522.0 188.0 L516.6 192.3"
        fill="none" stroke="#2f7ed8" stroke-width="1.5"
        stroke-linecap="round" stroke-linejoin="round"/>
  … one .sc-vector.sc-point per point …
</g>
```

- **Class:** `sc-vector sc-point`. `sc-point` is the **contract** class the
  runtime keys on (tooltip / highlight / crosshair / legend-toggle / keyboard
  nav); `sc-vector` is a purely-cosmetic CSS hook (adding a class the runtime
  must *know about* is out of scope — NN#2). The arrow **is** the hoverable
  point; there are no separate markers.
- **Geometry:** the arrow is anchored on `(cx, cy) = (fr.xpix(x), fr.ypix(y))`,
  rotated by `direction`, and sized by `arrow_px(length)` (below). The full
  shaft + arrowhead path is built in the [Arrow glyph](#arrow-glyph--the-pinned-geometry)
  section, in a **pinned operation order** so `:.1f`/`f1` rounding lands
  identically. Emit every path coordinate (and `cx`/`cy`) via `:.1f`/`f1`.
- **Paint:** read `fr.styles[si].fill` — the resolved arrow paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex** — and
  apply it to **`stroke`** (a vector is a line glyph; `fill="none"`). Never read
  `area_fill` (that is line's under-fill), and never emit a colorless arrow (an
  invisible vector field is a broken static chart — NN#2).
- **Stroke width:** `stroke-width = fmt_num(lineWidth)` — vector-plot's `lineWidth`
  default is a pinned **`1.5`** (line's is `2`), so a dense field stays legible.
  `stroke-linecap="round"` and `stroke-linejoin="round"` are emitted so the
  shaft and arrowhead read cleanly.
- **`cx` / `cy`:** every `.sc-point` MUST carry `cx` (the arrow's `(x,y)` anchor
  x) — the crosshair reads it — and by convention `cy` (anchor y). The anchor is
  the point location regardless of `rotationOrigin` (which only shifts where the
  glyph sits relative to it).
- **`data-direction` / `data-length`:** the **new** datum attributes — the raw
  `direction` (degrees) and `length` (magnitude) via `fmt_num`. Alongside the
  inherited `data-x`/`data-y`, they let the tooltip and data table show the full
  `(x, y, direction, length)` tuple.
- **`data-r` / `data-r-hover`:** carried for `.sc-point` contract conformance
  (the runtime calls `pt.setAttribute("r", …)` on hover — a `<path>` ignores `r`,
  harmless). Set both to `fmt_num(lineWidth)` (the glyph does not grow on hover,
  so `data-r-hover == data-r`).
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Length scale — the pinned geometry

Evaluate the length-scale in **exactly this operation order** in both languages
so `%g`/`fmt_num` and `:.1f`/`f1` rounding land identically. This is the **first**
of vector-plot's two net-new transforms (parallel to bubble's size-scale):

```
VECTOR_LENGTH = 20.0                                # pinned default max arrow pixel length
                                                    #   (overridden by spec.vectorLength when present)

# 1. Global length-domain — reduce over EVERY point of EVERY series, in
#    series-index order then point order. One domain for the whole chart
#    (arrows comparable across the field and across series).
lmax = max(length over all points, all series)

# 2. Degenerate rule — pinned identically, evaluated BEFORE any division.
def arrow_px(length):
    if lmax <= 0.0:                                 # no magnitude anywhere (all zero / absent)
        return 0.0                                  # zero-length glyphs — NEVER divide by 0
    return VECTOR_LENGTH * (length / lmax)          # linear: longest magnitude → VECTOR_LENGTH px
```

- **`VECTOR_LENGTH = 20.0` is a fixed constant** (Highcharts' `vectorLength`
  default), overridable by the chart-level `vectorLength` field but never a
  per-author free-for-all inside the renderer (analogous to column's `PAD = 0.2`
  and bubble's `RMIN`/`RMAX`). Pinning it makes every arrow length reproducible
  across languages.
- **Linear (not `sqrt`) mapping** — unlike bubble (where *area* encodes `z`, so
  `r ∝ sqrt(z)`), a vector's **pixel length** encodes magnitude directly, so the
  map is **linear**: `arrow_px = VECTOR_LENGTH * length / lmax`. The longest
  magnitude reaches exactly `VECTOR_LENGTH` px.
- **Degenerate domain (`lmax <= 0`)** — every `length` zero or absent — returns a
  **fixed `0.0`** pixel length (a dot at the anchor). This is the pinned rule that
  must fire **before** the divide: a raw `x/0` is a `ZeroDivisionError` in Python
  and `+Inf`/`NaN` in Go — the two languages would diverge and both silently
  pass byte-parity if one is not pinned. Pin it identically.
- **All-equal positive length** — every `length == L > 0` gives `lmax = L`, so
  every arrow is `VECTOR_LENGTH * (L / L) = VECTOR_LENGTH` px: a **direction-only
  field** (all arrows the same size, only their headings differ). See
  [`examples/uniform-length.json`](examples/uniform-length.json).

This is covered by a **vector-plot edge-case parity test** (analogous to
`test_spline_edge_cases` / bubble's size-scale test): all-zero `length`, a single
point, and a mixed field — each asserts a **finite** arrow length and **Py == Go**
(§7 gauntlet).

## Arrow glyph — the pinned geometry

Build the arrow path in **exactly this operation order** in both languages so
every coordinate rounds ULP-for-ULP identically under `:.1f`/`f1`. This is the
**second** net-new transform (the mark primitive). Pinned constants:

```
HEAD_LEN   = 6.0                                    # arrowhead barb length (px)
HEAD_ANGLE = 25.0                                   # arrowhead half-angle (degrees)

# 1. Direction → SVG unit vector (y grows DOWNWARD; 0deg = up/north, clockwise).
rad = direction * PI / 180.0
ux  =  sin(rad)                                     # 0deg -> 0 ; 90deg -> +1 (east)
uy  = -cos(rad)                                     # 0deg -> -1 (up) ; 180deg -> +1 (down)

# 2. Pixel length of THIS arrow (from the length-scale above).
L    = arrow_px(length)
half = L / 2.0

# 3. Tail & head from the anchor (cx, cy), per rotationOrigin (default "center").
#    center: midpoint at the anchor ; start: tail at anchor ; end: head at anchor.
if rotationOrigin == "start":  ax, ay = cx,            cy              # tail at anchor
elif rotationOrigin == "end":  ax, ay = cx - ux*L,     cy - uy*L       # head at anchor
else:                          ax, ay = cx - ux*half,  cy - uy*half    # center (default)
tailx, taily = ax,          ay
headx, heady = ax + ux*L,   ay + uy*L

# 4. Arrowhead barbs — rotate the reversed shaft unit vector (-ux,-uy) by +/-HEAD_ANGLE.
ha  = HEAD_ANGLE * PI / 180.0
ca, sa = cos(ha), sin(ha)
# left barb: rotate (-ux,-uy) by +ha ; right barb: by -ha
lbx = headx + HEAD_LEN * ((-ux)*ca - (-uy)*sa)
lby = heady + HEAD_LEN * ((-ux)*sa + (-uy)*ca)
rbx = headx + HEAD_LEN * ((-ux)*ca + (-uy)*sa)
rby = heady + HEAD_LEN * (-(-ux)*sa + (-uy)*ca)

# 5. One stroked path: shaft, then the two arrowhead barbs meeting at the head.
d = f"M{tailx:.1f} {taily:.1f} L{headx:.1f} {heady:.1f} "
    f"M{lbx:.1f} {lby:.1f} L{headx:.1f} {heady:.1f} L{rbx:.1f} {rby:.1f}"
```

- **`HEAD_LEN = 6.0` / `HEAD_ANGLE = 25.0` are fixed constants** — pin them so the
  arrowhead is byte-reproducible.
- **A zero-length arrow (`L == 0`)** collapses the shaft to a point; still emit
  the path (`tail == head`), so the datum stays a hoverable `.sc-point` with its
  `data-*`. Do **not** skip zero-magnitude points.
- **Anchor vs origin:** `cx`/`cy` (the crosshair anchor + `data`-implied
  position) always carry `(fr.xpix(x), fr.ypix(y))` — the sample location —
  **regardless** of `rotationOrigin`, which only decides where the glyph is drawn
  relative to that anchor.
- **Operation order is load-bearing:** compute `ux`/`uy` first, then `L`/`half`,
  then tail/head, then barbs — a reassociated `ux*L` vs `ux*half` or an early
  round diverges after `:.1f`.

## Reused chrome (obtained from the frame — never re-implemented)

Vector-plot inherits, with **zero** re-implementation (§3.1, §4.2), everything
scatter/bubble already reuse:

- Plot area + margins; x/y axes + axis lines + axis titles.
- **Numeric x-axis** (scatter's rank-3 net-new) — `nice_ticks` + x tick labels +
  vertical gridlines + `xpix` from a **value** (`x_scale="linear"`); reused
  verbatim.
- Linear **numeric** y-scale via `nice_ticks` → `ypix`, **both** built with
  `include_zero=False`; y gridlines + labels.
- Titles + subtitle; legend (bottom-center); crosshair (two-axis for the free x/y).
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme). Vector-plot applies the resolved paint to the
  arrow **stroke**.
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table
  (generalized for the `{x,y,direction,length}` point model — §5.4b-DT) +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- The **point model** (`{x,y}` normalization) from scatter — vector-plot extends
  it with `direction` + `length` only.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) — all
  parity-locked.

The chart delegates with `x_scale="linear"` and `include_zero=False`. It passes
the bare noun **`"Vector plot"`** — the frame expands it to
`"Vector plot chart with N series…"` byte-for-byte.

## Parity traps (verify before the byte-parity gate)

- **Length-scale ORDER** — reduce the **global** `lmax` first (series-index order
  then point order), check `lmax <= 0` **before** any divide, then
  `VECTOR_LENGTH * length / lmax`. A reassociated ratio diverges after `fmt_num`.
- **Degenerate length-domain** — all-zero / absent `length` must return the fixed
  `0.0`; a raw `x/0` is a `ZeroDivisionError` (Python) vs `+Inf`/`NaN` (Go). Pin
  the rule identically **before** the divide (mirrors bubble's degenerate size-domain).
- **length-domain scope** — reduce `lmax` **globally** across all series (not
  per-series), so a given magnitude maps to the same pixel length everywhere; a
  per-series reduction would make arrows non-comparable and is a defect.
- **Arrow-geometry ORDER** — evaluate `ux/uy → L/half → tail/head → barbs` in the
  pinned order (see [Arrow glyph](#arrow-glyph--the-pinned-geometry)); reassociating
  the trig products or rounding early diverges after `:.1f`.
- **Direction convention** — `0°` = up/north, **clockwise** (`ux = sin(rad)`,
  `uy = -cos(rad)`). Emitting `uy = +cos(rad)` (screen-y up) flips every arrow
  vertically; both languages would agree and still be wrong — pin the convention.
- **`include_zero=False` on BOTH axes** — vector-plot passes `False`; carrying
  line's / column's zero-anchor into the free x **or** y domain wrongly re-anchors
  the field at 0. Both languages would be wrong identically and still pass
  byte-parity — so the flag must be explicit (§3.2 caveat, §4.2).
- **Arrow paint on the STROKE** — pattern → `url(#pat)`; gradient → `url(#grad)`;
  else solid hex, applied to **`stroke`** with `fill="none"`. Reading `solid`
  silently drops gradient/pattern; reading `area_fill` is line's field; filling
  instead of stroking paints nothing (a stroked path has no area). Never emit a
  colorless arrow.
- **`lineWidth` default** — vector-plot's default is **`1.5`**, not line's `2`;
  emit `stroke-width` identically in both languages (absent field → the pinned
  `1.5`). `data-r`/`data-r-hover` mirror it and are equal (no hover growth).
- **Zero-length arrow** — still emit the `.sc-point` path (tail == head) with its
  `data-*`; do not drop zero-magnitude datums.
- **Formatters** — every path/`cx`/`cy` coordinate via `:.1f`/`f1`;
  `data-x`, `data-y`, `data-direction`, `data-length`, `data-r` via
  `fmt_num`/`fmtNum`; every user string via `esc`. A leaked raw `<` fails the XSS
  tests.
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
- **Datum mark:** `.sc-point` (here also `.sc-vector`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, **`data-direction`**,
  **`data-length`**, `data-color`, `data-r`, `data-r-hover` — `data-direction`
  and `data-length` are the new vector attributes; the tooltip shows the full
  `(x, y, direction, length)` tuple.
- **Crosshair anchor:** every `.sc-point` carries `cx` (arrow anchor x) and by
  convention `cy` (anchor y).
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(fmt_num(x))`; `data-y = esc(fmt_num(y))`;
  `data-direction = esc(fmt_num(direction))`; `data-length = esc(fmt_num(length))`;
  `data-color = fr.styles[si].solid`; `data-r`/`data-r-hover = fmt_num(lineWidth)`.
  Pixel attrs (`cx,cy`, path `d` numbers) use `:.1f`/`f1`.
- **A11y default-on + data-table generalization (§5.4b-DT):** vector-plot's
  `data` stops being a plain `number[]` (each row is an
  `{x,y,direction,length}` tuple), so the shared **visually-hidden data table**
  MUST be generalized — in lockstep in both languages — to render `x`, `y`,
  `direction`, and `length` per row (not a single coerced number), with a
  Py==Go table-bytes test. Shipping the old `number[]` table would misrepresent
  the data and is an a11y non-negotiable failure (NN#4). `a11y:false` restores
  the pre-a11y bytes. Keyboard nav walks the arrows.
- **Static-first:** the chart is fully readable with JS disabled — arrows are
  server-rendered, rotated, and sized; the crosshair ships `display:none`; the
  tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "vector-plot",
  "title": "Surface Wind Field",
  "subtitle": "Arrow heading = wind direction, length = speed",
  "xAxis": { "title": "East offset (km)" },
  "yAxis": { "title": "North offset (km)" },
  "series": [
    {
      "name": "10:00 UTC",
      "x":         [0, 25, 50, 0, 25, 50, 0, 25, 50],
      "data":      [0, 0, 0, 25, 25, 25, 50, 50, 50],
      "direction": [10, 30, 50, 40, 60, 80, 70, 90, 110],
      "length":    [6, 8, 5, 9, 12, 7, 4, 10, 8]
    }
  ]
}
```

`data` is the `y` array; `x`, `direction`, and `length` are the
forward-compatible parallel arrays (see [Data shape](#data-shape)). The spec
passes `validate() == []` today and folds into the `{x,y,direction,length}`
datum with no byte change when the point model lands.

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single series, a 3×3 numeric field, `direction` rotation + `length → arrow px`, default `vectorLength`/`center` origin |
| [`examples/field.json`](examples/field.json) | 2 series (two snapshots overlaid), **global** length-domain comparability, custom `lineWidth`, a chart-level `vectorLength` override |
| [`examples/themed-dark.json`](examples/themed-dark.json) | `theme:"dark"` + a gradient arrow paint (defs pre-pass + `SeriesStyle.fill` → `url(#grad)` on the stroke) + `rotationOrigin:"start"` |
| [`examples/uniform-length.json`](examples/uniform-length.json) | all-equal `length` → the **degenerate length-domain** (every arrow = `vectorLength` px, a direction-only field); also clamps `xAxis`/`yAxis` |

The full golden build set additionally pins an **`adversarial`** case carrying
hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted string
field (series name, custom arrow color) so the XSS tests run against the vector
marks (§5.5d). `VECTOR_PLOT_CASES =
["basic","field","themed-dark","uniform-length","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from stonecharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/vector-plot/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from stonecharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="vector-plot",
    title="Surface Wind Field",
    x_axis=Axis(title="East offset (km)"),
    y_axis=Axis(title="North offset (km)"),
    series=[
        Series("10:00 UTC", [0, 0, 0, 25, 25, 25, 50, 50, 50],
               x=[0, 25, 50, 0, 25, 50, 0, 25, 50],
               direction=[10, 30, 50, 40, 60, 80, 70, 90, 110],
               length=[6, 8, 5, 9, 12, 7, 4, 10, 8]),
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
- **Hover an arrow** → tooltip (x, y, direction, length, series) + arrow highlight
  (halo) + crosshair.
- **Click a legend item** → toggle that series on/off.
- **Keyboard** → arrows walk the vector glyphs; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — arrows rotated and sized.

## Rendering notes

- **Both** axes use "nice numbers" ticks (~6) over the **data** domain with
  `include_zero=False` — the free numeric x/y is **not** zero-anchored (a field
  sampled at x∈[100,200] stays there). `xAxis.min/max` and `yAxis.min/max` clamp
  the respective domain.
- Arrow pixel length comes from the **length-scale** of `length` (linear,
  `arrow_px = vectorLength * length / lmax`), never from `marker.radius`
  (ignored). The length-domain is **global** across all series.
- Arrow rotation follows the pinned convention: `0°` = up/north, clockwise.
  `rotationOrigin` (`center`/`start`/`end`) decides where the glyph sits on its
  `(x,y)` anchor; the crosshair anchor is always the sample location.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is unset;
  a gradient/pattern paints the arrow **stroke** via the `<defs>` pre-pass.
- Vector-plot reuses the **exact** substrate scatter/bubble extended — it forks
  **nothing**; its only net-new is the length-scale + the arrow-glyph mark.

## Not yet supported (roadmap)

- Live renderers (`vector_plot.py` / `vector_plot.go`) — deferred; design +
  examples + validation are complete. Only `line` renders today. Vector-plot lands
  **after** scatter supplies the numeric-x-axis + point model it reuses.
- The `{x,y,direction,length}` datum in `data` (objects / positional
  `[x,y,direction,length]`) — accepted once the point-model normalization +
  validator update land (§3.3 Rank 3); until then the parallel-array transitional
  form is used.
- Per-magnitude **color scale** (arrow color encoding `length`), an explicit
  `lengthMin`/`lengthMax` domain override, a size legend of sample arrows, and a
  categorical/grid-snapped x variant — variants layered on this base.
- **Windbarb** — the meteorological speed+direction glyph (barbs/flags) is its
  own sibling, not a `vector-plot` variant.
