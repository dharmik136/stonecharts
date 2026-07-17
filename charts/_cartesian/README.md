---
id: PC-ARCH-003
title: PeakCharts Cartesian Substrate
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-DET-001, REQ-STACK-001, REQ-STACK-002, REQ-LAYOUT-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-STACK-SIGNED, TEST-PERCENT-DOMAIN]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# The Cartesian Substrate (`_cartesian`)

> The shared substrate every Cartesian/XY chart rides. Read this **before** building
> any cartesian sibling (column, bar, scatter, bubble, area, combo, histogram,
> candlestick, error-bar, range, waterfall, bullet, …). It is the per-family
> "perfect thing": what geometry and chrome the frame hands you for free, the one
> function you supply (the marks callback), and the parity / a11y / validation
> obligations you inherit and must not break.
>
> **Authority note:** approved requirements, contracts, and ADRs take precedence.
> Within that boundary, the detailed implementation roadmap is
> [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) **§3–§5**
> (§3 the scoped plan + generalizations, §4 the extraction contract, §5 the
> per-chart coordination contract). The DOM contract is
> [`spec/svg-contract.md`](../../spec/svg-contract.md). The recipe template every
> chart's `design.md` copies is [`charts/line-basic/design.md`](../line-basic/design.md).
> If this file and the roadmap disagree, approved requirements, contracts, and ADRs
> decide the behavior; reconcile both engineering documents before implementation.

- **Module (Python):** `libs/python/peakcharts/charts/_cartesian.py`
- **Module (Go):** `libs/go/cartesian.go` (flat `package peakcharts`)
- **Reference marks (the exemplar to imitate):** `libs/python/peakcharts/charts/line.py` · `libs/go/line.go`
- **Foundation tax:** **$0 — already paid.** The substrate was extracted out of the
  line renderer with Rank 1 (Column). Every sibling reuses and extends it; **never
  fork it.**

---

## 1. What the substrate is

A **substrate** is the coordinate system + geometry engine + scale machinery a chart
needs (chart-families.md §1.2). Family A — Cartesian/XY — is the x/y plane: linear +
category scales (log/datetime to come), a rectangular plot area, and marks =
polyline/path, rect/bar, point/symbol, whisker.

Charts are grouped by **substrate, not by looks**. Line and column look nothing alike
but share this plane, so they are the same family; a pie (polar) or a treemap
(hierarchy) do not belong here even where they resemble a bar. Grouping this way is
what makes the build economical: the family pays its foundation tax **once** (done),
then every sibling is cheap because it reuses the substrate and adds **only its
marks**.

**The one rule that defines the whole abstraction:** the chart renderer draws **only
the series marks** — the inner content of `<g class="pk-series">…</g>`. Every piece of
chrome — margins, scales, ticks, gridlines, axis lines, axis titles, legend,
crosshair, background, `<defs>`, theme resolution, a11y summary, `<svg>` open/close,
**and the value-axis domain including any stacking-aware y-max** — is obtained from the
frame. You may **never** re-implement any of it in a chart renderer (that is a defect
even if the bytes come out right — chart-families.md §7.1).

---

## 2. The `CartesianFrame` — what it provides

`build_frame` / `buildFrame` resolves the spec into a per-render frame that owns all
geometry and chrome. Canonical field lists live in chart-families.md §4.3
(`CartesianFrame` dataclass / `cartesianFrame` struct); the essentials:

**Geometry & scales the frame computes and exposes:**

- Canvas `W`,`H`, resolved `theme` + palette pickup.
- Margins (`m_top/left/right/bottom`) and the plot rect (`plot_x/y/w/h`).
- `n` and `cats` (categories, or the `0..n-1` index fallback when `categories` is absent).
- The **value axis**: range + `nice_ticks` → `y_min`, `y_max`, `y_ticks`.
- `xpix(i)` / `ypix(v)` — pixel maps; `band_width()` on the band scale.
- The `<defs>` pre-pass → per-series `SeriesStyle`, the id-scope `cid`, and `defs_parts`.
- The a11y summary strings (`a11y_attr`, `a11y_desc`).

**Chrome the frame emits** — in the exact **head → marks → tail** order (§4.1):

```
<svg …>  <desc>  <defs>  <rect pk-bg>  <text title/subtitle>
<g pk-axis-y> gridlines+labels  <line pk-axis-line>  <g pk-axis-x> labels
axis titles (x, rot-y)  <line pk-crosshair>          ┈┈ HEAD (chromeHead)
      <g class="pk-series">…</g> × N                 ┈┈ YOUR MARKS
<g pk-legend>…</g>   </svg>                           ┈┈ TAIL (chromeTail)
```

The marks are **sandwiched** between head and tail — chrome is not one contiguous
block. Byte-identity therefore forbids any "emit all chrome, then all marks"
reshuffle. This is the load-bearing design fact (§4.1).

### 2.1 Accumulator injection (why byte-identity is true by construction)

The orchestrator threads **one shared accumulator** — Python `list`, Go
`*strings.Builder` — through head → marks → tail. Your marks callback **appends into
that same buffer**; it does not return a string a caller re-joins. Same writes, same
order, same buffer as the original single-buffer renderer ⇒ identical bytes for free
(§4.7 gotcha 1).

```python
def render_cartesian(spec, chart_noun, x_scale, marks, include_zero=True) -> str:
    fr = build_frame(spec, chart_noun, x_scale, include_zero)
    p = []
    _chrome_head(fr, p)
    marks(fr, p)          # your <g class="pk-series">…</g> blocks go here
    _chrome_tail(fr, p)
    return "".join(p)     # single join, NO trailing newline
```

```go
func renderCartesian(spec *ChartSpec, noun, xScale string, marks marksFn, includeZero bool) string {
    f := buildFrame(spec, noun, xScale, includeZero)
    var p strings.Builder
    chromeHead(f, &p); marks(f, &p); chromeTail(f, &p)
    return p.String()
}
```

### 2.2 Frame configuration knobs

Three parameters the renderer chooses when it delegates; the frame does the rest.

- **`x_scale` — `"point"` | `"band"`.** The one generalization added during extraction (§4.3).
  - **point** — `xpix(i) = plot_x + plot_w*i/(n-1)`, and `plot_x + plot_w/2` when `n<=1`.
    Points land under labels. Used by line / area / scatter-with-categories. **Line MUST
    keep this formula so its bytes do not move.**
  - **band** — categories occupy equal bands, this exact operation order:
    `band_width() = plot_w / n`; `xpix(i) = plot_x + band_width()*i + band_width()/2`
    (band center). Used by column / bar. Marks build sub-bands from `band_width()` with
    the §3.2 constants (see §4 below).
  The shared x-label loop calls `frame.xpix(i)`, so labels land under points (point) or
  band centers (band) with **no per-chart label code**.
- **`include_zero` — bool.** The value-axis zero anchor (§3.2 caveat, §4.2).
  - `True` → value axis / y baseline (column/bar/area): forces 0 into the domain
    (`min(values+[0.0])` / `max(values+[0.0])`). Line passes `True` and is byte-identical
    to today.
  - `False` → a **free** numeric x (and free numeric y) axis (scatter/bubble): domain
    from the data only. **Do not carry the y-baseline zero-anchor into a free numeric
    axis** or a scatter with x∈[100,200] is wrongly anchored at 0 — and both languages
    would be wrong identically and still pass byte-parity, so the flag must be explicit.
- **`stacking` — `None`/`""` | `"normal"` | `"percent"`.** **The frame owns the
  stacking-aware y-domain**: for stacked/percent the y-max is the max column **total**
  (cumulative in the pinned summation order), **not** the per-datum max. Marks **never**
  recompute a scale. Selected by the `stacking` spec field routed through the five-place
  lockstep (§6.2).

---

## 3. What you supply — the marks callback

A chart renderer is a **one-line delegation** that supplies **only** a marks callback.

```python
# charts/<id>.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Column", "band", _column_marks)   # include_zero defaults True

def _column_marks(fr: CartesianFrame, p: list) -> None:
    for si, s in enumerate(fr.spec.series):
        # emit exactly ONE <g class="pk-series" data-series="{si}">…</g> per series into p
        ...
```

```go
// <id>.go — package peakcharts
func renderColumnSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Column", "band", columnMarks, true)
}
func columnMarks(f *cartesianFrame, p *strings.Builder) {
    for si := range f.spec.Series { /* one <g class="pk-series"> per series into p */ }
}
```

Note the **noun is the bare word** — `"Column"`, `"Line"` — not `"Column chart"`; the
frame's a11y summary expands it to `"{noun} chart with N series…"` byte-for-byte (§4.3).

### Hard rules for the marks function (chart-families.md §5.2)

- Emits **exactly one** `<g class="pk-series" data-series="{si}">…</g>` per series, and
  **nothing outside** it.
- Uses `fr.xpix` / `fr.ypix` / `fr.band_width` for **all** geometry — computes **no**
  scale of its own (the frame owns the value-axis domain, incl. the stacking-aware y-max).
- Baseline for bars/area is `fr.ypix(0.0)` — never recompute a baseline; the value axis
  (`include_zero=True`) already forced 0 into the domain.
- Bar fill reads `fr.styles[si].fill` (the resolved bar paint — see §5), never `area_fill`.
- Every number printed goes through the §5 formatters — never raw `str(float)` /
  `strconv.FormatFloat` at another precision.

### The DOM contract your marks must emit (svg-contract.md, chart-families.md §5.3)

The shared runtime (`runtime/chart-interactions.js`) keys **only** on the selectors +
`data-*` below. Emit them correctly and tooltip, highlight, crosshair, legend-toggle,
and keyboard nav all work with **zero JS changes** (adding a behavior that needs new JS
is out of scope for a chart add — non-negotiable #2).

```html
<g class="pk-series" data-series="0">
  <!-- optional visible mark(s): bar rect / area path / connecting line -->
  <rect class="pk-point" data-series="0"
        data-series-name="Tokyo" data-x="Jan" data-y="7"
        data-color="#2f7ed8" data-r="3.5" data-r-hover="6"
        cx="123.4" cy="88.0" x="…" y="…" width="…" height="…" fill="#2f7ed8"/>
  … one .pk-point per datum …
</g>
```

1. **The series group is `.pk-series[data-series=N]`.** `N` is the integer series index,
   **consistent** across the group, its points, and the legend item (emitted by the
   shared tail with the same index — do not renumber). The legend toggle flips `display`
   on every `[data-series="N"]`; nested marks inherit from the group.
2. **The datum mark is `.pk-point`** and MUST carry all of `data-series`,
   `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`, `data-r-hover` — even
   for non-circular marks (the runtime sets `r` on hover; a `<rect>` ignores it
   harmlessly, but the attributes must be present for the tooltip body).
3. **Every `.pk-point` MUST carry a `cx`** (and by convention `cy`) — the crosshair reads
   `cx` to place its vertical guide. For a bar, `cx` = bar center x; `cy` = bar top (or
   center). Without `cx` the crosshair breaks.
4. **Escaping / formatting inside `data-*`:** `data-series-name` = `esc(s.name)`;
   `data-x` = `esc(<category label>)` (or a numeric value via `fmt_num` on a numeric-x
   chart); `data-y` = `esc(fmt_num(value))`; `data-color` = `fr.styles[si].solid`;
   `data-r`/`data-r-hover` = `fmt_num(...)`. Pixel attributes (`cx,cy,x,y,width,height`)
   use `:.1f`/`f1`. **Under stacking:** geometry uses cumulative baselines, but `data-y`
   MUST carry the **raw per-series segment value**, not the running total — the tooltip
   shows the value the user supplied.
5. **Do not invent new runtime classes.** Purely-cosmetic classes for CSS (e.g. `pk-bar`)
   are fine; runtime behavior is driven only by the contract selectors.
6. **Static-first:** the chart must be fully readable with JS disabled. The crosshair
   ships `display:none`; the tooltip is JS-only; everything else is server-rendered.

---

## 4. Pinned geometry (identical bytes in both languages)

These constants and operation orders are **fixed** — evaluate them in exactly this
order so `f1` / `:.1f` rounding lands ULP-for-ULP identically in Python and Go. They are
not per-author choices.

**Band layout** (grouped rects — column/bar/histogram/candlestick/range/waterfall/bullet/combo, §3.2):

```
bandWidth   = plot_w / n
xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
PAD         = 0.2                                     # single group-padding constant
groupW      = bandWidth * (1 - PAD)
K           = len(series)
barW        = groupW / K
left(i,k)   = xpix(i) - groupW/2 + barW*k
```
Basic single-series ⇒ `K=1` ⇒ one centered bar of width `groupW`. Histogram is the
exception: bins are **contiguous — no inter-bar padding** (§3.3 Rank 7).

**Size scale** (bubble z → area-proportional radius, §3.2 / §3.3 Rank 4) — pin the
degenerate rule identically **before any division**:

```
if zmax <= zmin:  r = (rmin + rmax) / 2              # all-equal z or single point — never 0/0
else:             r = rmin + (rmax - rmin) * sqrt(clamp01((z - zmin)/(zmax - zmin)))
```
`clamp01` the ratio to `[0,1]` **before** `sqrt` (a negative domain makes Python
`math.sqrt` raise and Go `math.Sqrt` return `NaN`→`"0"`). Never perform a raw divide
Python would reject (`0/0` → `ZeroDivisionError`) or feed a negative into `sqrt`.

**Stacking** — accumulate series cumulative sums in **index order**; the frame's
stacked y-max uses that **same** order; percent divides each value by its column total.

---

## 5. Formatting parity — the #1 cause of a byte diff

Every number and string has exactly one correct formatter. Mixing formatters between
languages is the top cause of a golden diff (§5.3).

| What you emit | Python | Go |
|---|---|---|
| Pixel coordinate (`cx,cy,x,y,width,height`, path `d` numbers) | `f"{v:.1f}"` | `f1(v)` |
| Data value, radius, opacity, offset, size, angle, stroke width, tick label | `fmt_num(v)` | `fmtNum(v)` |
| Integer literal (`W`, `H`, series index, `font-size="11"`) | `str(int)` / literal | `%d` / literal |
| Any user string (name, label, color, category) | `esc(s)` | `esc(s)` |

`fmt_num`/`fmtNum` are parity-locked (`%g` 6-sig, trailing `.0` dropped, NaN/Inf→`"0"`);
`:.1f`/`f1` are parity-locked to one decimal. Any user-controlled string reaching the
SVG/HTML goes through `esc` — the frame escapes chrome/theme values; **your marks must
`esc` the strings they emit** (`data-series-name`, `data-x`, custom mark colors). A
leaked raw `<` fails the XSS tests.

**Bar-fill resolution (a real byte-parity + static-first trap, §5.3).** A bar has ONE
fill that may be solid / gradient / pattern. The line-shaped style tuple does not carry
it, so extraction added a **`fill` field to `SeriesStyle`** (populated by the defs
pre-pass; unread by line so line bytes do not move). Resolve as: **pattern → the
`url(#pat)` ref; gradient → the `url(#grad)` ref; else the solid hex.** Never leave a
basic column unfilled (a broken static chart), and never silently drop gradient/pattern
by reading `solid`.

---

## 6. Validation & spec obligations

### 6.1 If your chart adds NO new spec field

You inherit all validation for free (`type/id/theme/title/subtitle/width/height/legend/
a11y/xAxis/yAxis/series[...]`). Do nothing to the validators; just confirm every
`examples/*.json` returns `validate() == []`. A genuinely field-free sibling has a spec
shape identical to the line spec (e.g. a mark-only restyle). **Column is not one** — its
`stacking`/`grouping` selector is a new field (§6.2).

### 6.2 If your chart adds ANY new spec field — five places, in lockstep (§5.4b)

Miss one and you break byte-parity and/or strict validation. Worked instances: Column's
`stacking`/`grouping`, waterfall's `isSum`, a hypothetical `series[].borderRadius`.

1. **Schema** — `spec/chart-spec.schema.json`: property under the right `definitions`
   node with `type` + `default` + `description`; keep `additionalProperties` open
   (forward-compatible).
2. **`validate.py`** — a rule in the matching helper using existing primitives
   (`_num`/`_intnum`/`_str`/`_bool`/`_str_array`) so error text is identical. No defaults here.
3. **`validate.go`** — the exact mirror: same `$.path`, byte-identical wording.
4. **Spec model (Python)** `spec.py` — dataclass field + default, parsed in `from_dict`
   with **default-on-absence only** (never coerce a malformed present value).
5. **Spec model (Go)** `spec.go` — struct field with the right `json:` tag; use
   `*T` + accessor when "absent" must differ from a real `0`/`""` (as `Gradient`/`Marker`/
   `GridLine` do). Decode-then-default must yield the same value Python yields for both
   "absent" and "present".
6. **Invalid fixtures** — `charts/<id>/invalid-fixtures.json`: ≥1 hostile case per new
   field (e.g. `{"stacking": 5}` → identical `$.series...`/`$....: expected X, received Y`
   in both languages), wired into both parity tests.

### 6.3 Register the chart type in BOTH validators (a real divergence to close)

The validator does **not** currently gate that `type` names a *known* chart — only that
it is a string. An unknown `type` slips past validation and diverges at dispatch:
`render.py` raises a catchable `ValueError`, `render.go` **panics**. So "registering a
chart type" means all of: add it to `render.py` `_RENDERERS`, add the `case` to
`render.go` `RenderSVG`, add it to the schema `type` enum, **and** add it to a shared
**known-type validation set in both `validate.py` and `validate.go`** so an unknown
`type` is rejected identically as a `SpecError` (same `$.type` text) **before** dispatch.

### 6.4 Point-model / accessible-data-table obligation (§5.4b-DT)

The shared HTML **accessible data table** (`_data_table`/`dataTable`, a hard a11y
non-negotiable) assumes `series.data` is `number[]`. **When a chart's `data` stops being
`number[]`** (scatter `{x,y}`, bubble `{x,y,z}`, candlestick `{o,h,l,c}`, range
`{low,high}`, …), the table MUST be generalized **in lockstep in both languages** to
render the point model faithfully (not a coerced single number per row), with a test
proving Py==Go table bytes. A sibling may not ship an a11y-broken table while passing
the golden gates.

---

## 7. Accessibility, themes, non-negotiables

The frame delivers a11y and themes; do not re-derive them, and do not regress them.

- **A11y default-on:** the SVG carries `role="img"` + a concise `aria-label` + `<desc>`;
  the HTML adds a separate **visually-hidden data table**; keyboard nav walks points.
  `a11y:false` restores the pre-a11y bytes. The `a11y_summary` noun you pass is the bare
  word (§3).
- **Themes** are resolved server-side into concrete SVG attributes (`spec/themes/*.json`,
  baked + JSON-parity-tested). The frame does palette pickup; a custom theme object may
  override any field.
- **The six non-negotiables you are protecting** (chart-families.md §5): (1) Py/Go
  byte-identical SVG; (2) static-first (readable with JS disabled; the runtime only
  *enhances*, never edited for a chart add); (3) strict shared validation — identical
  `$.path: expected X, received Y`, defaults only on absence; (4) a11y default-on;
  (5) themes server-side; (6) `esc` for strings, `fmt_num`/`fmtNum` or `:.1f`/`f1` for
  numbers.

---

## 8. Generalizations the substrate already carries / that siblings force (§3.2)

Each is built **once**, then reused. Know which your chart needs before you start.

| Generalization | What it gives you | Forced by |
|---|---|---|
| **Point model** `{x,y,z,open,high,low,close,name}` | Richer datum; a bare `number` stays valid (x=index) so line/column goldens never move; absent field → **gap, never 0** | scatter, bubble, candlestick, error-bar, area-range, column-range, waterfall |
| **Numeric x-axis** | `nice_ticks` + tick labels + gridlines + `xpix` from a **value** (with `include_zero=False`) | scatter, bubble, histogram, candlestick |
| **Stacking transform** | Per-datum cumulative baselines + percent shares; **frame owns** the stacked y-domain | column, bar, area |
| **Orientation transpose** | Bar = column with value/band axes swapped (one renderer, not a fork); yields horizontal ranges + bullet | bar, column-range, bullet |
| **Band layout** | Per-category slot split into K sub-bands (the §4 pinned scheme) | every rect-based sibling |
| **Size scale** | z → area-proportional radius (the §4 pinned formula) | bubble |
| **Composition layer** | Compute plot+scales once, dispatch each series to its own mark renderer (`series[].type`) | combo |
| **Secondary y-axis** | A second independent y-scale for co-plotted units (reuses `nice_ticks`) | combo, candlestick |

**Build order** (chart-families.md §3.3, fixed so each sibling forces the fewest new
generalizations): Column → Bar → Scatter → Bubble → Area → Combo → Histogram →
Candlestick → Error bar → Area range → Column range → Waterfall → Bullet.

**One declared exception to this substrate contract:** **funnel/pyramid** uses none of
the x/y axis chrome, no gridlines, and neither the point nor band x-scale — it brings
its own centered-trapezoid mark + value→width centering layout. It is the single row in
Family A that does **not** ride this frame (chart-families.md §2, Family A note).

---

## 9. The gates every sibling must pass (§5.6, §4.6)

- **Gate A** *(only when you performed the §4 extraction)* — line goldens byte-unchanged
  (`git diff` empty, incl. the widened `cats>n` / `cats<n` / `cats-absent` fixtures); both
  suites green. Unchanged goldens + green tests = the extraction moved no bytes.
- **Gate A′** *(any rank that changes the `data` element type, e.g. scatter's point
  model)* — `git diff` empty on **ALL** existing goldens (every line fixture **and** every
  prior sibling), proving the bare-number fast path reproduces the exact pre-change bytes;
  plus a Py==Go cross-render on all of them. A golden-diff **proof**, not an assertion.
- **Gate B** — both suites pass the new chart's cases against the **same**
  `charts/<id>/golden/*.svg` ⇒ Python == Go on every fixture. Belt-and-suspenders: render
  one fixture in each language and `diff` — empty.
- **Gate C** — output is **additive-only**: no existing golden changes (`git status
  charts/*/golden/` shows only new files); the head/tail emit **no** empty `<defs>` or
  background `<rect>` under the default light theme (defs are gated on `defs_parts`).

**Goldens carry no trailing newline and are UTF-8 (no BOM).** They are generated once
from the **Python** renderer (canonical), then both suites verify them. If Go fails, it
is a **code divergence to fix**, never a golden to regenerate to match a broken language.

**Byte-parity traps checklist (verify before Gate B):** trailing newline in a golden; a
float printed with `str()`/`FormatFloat(...,-1,64)` instead of `fmt_num`/`f1`; Go
`range`-over-map output ordering (always iterate `spec.Series` by index); a `data-*`
string not run through `esc`; series/point/legend `data-series` indices drifting apart; a
default resolved differently across languages for an absent field (Go zero-value vs
Python `None` — use pointers/accessors); a degenerate numeric op diverging (Python raises,
Go yields `NaN`→`"0"` — pin the rule **before** the divide); an unconditional
`<defs>`/background `<rect>`.

---

## 10. Definition of Done (per sibling, chart-families.md §5.8)

A cartesian chart is done only when **all** hold: `design.md` (self-contained, copies the
[line-basic template](../line-basic/design.md)) + `examples/*.json` + `golden/*.svg`
exist; the renderer is a one-line delegation in **both** languages re-implementing no
chrome; it is registered in both dispatchers + the schema enum + the shared known-type
set; marks emit the svg-contract structure exactly (`.pk-series[data-series=N]`,
`.pk-point` with all `data-*` **and** `cx`, bar fill from `SeriesStyle.fill`, never
unfilled); every new spec field is present and consistent across schema + both validators
+ both spec models with defaults only on absence, and both validators reject
`invalid-fixtures.json` identically; if the `data` element type changed, the data table is
generalized in lockstep with a Py==Go test and **Gate A′** passes; all strings via `esc`,
all numbers via the §5 formatters, XSS + a11y-toggle tests pass **against this chart's
marks**, any new numeric transform has a finite-output edge-case test; **Gates A/B/C**
green; both test suites fully green; CHARTS.md + the roadmap ticked.

> If any box is unchecked the chart is **not done — regardless of visual appearance.**

---

## 11. Canonical sources (do not duplicate — point here)

| Need | Canonical home |
|---|---|
| Binding substrate + extraction + coordination contract | [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5 |
| DOM / `data-*` / runtime selector contract | [`spec/svg-contract.md`](../../spec/svg-contract.md) |
| `design.md` recipe template | [`charts/line-basic/design.md`](../line-basic/design.md) |
| Reference marks (imitate these) | `libs/python/peakcharts/charts/line.py` · `libs/go/line.go` |
| Frame implementation | `libs/python/peakcharts/charts/_cartesian.py` · `libs/go/cartesian.go` |
| Spec model / validators / utils | `spec.py`·`spec.go` / `validate.py`·`validate.go` / `util.py`·`util.go` |
| Themes | `spec/themes/{light,dark}.json` |
| Golden harness | `libs/python/tests/test_golden.py` · `libs/go/render_test.go` |
