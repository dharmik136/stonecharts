# Chart: Timeline (`timeline`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type — this file mirrors the
> **exemplar** [`charts/column/design.md`](../column/design.md) (which copies
> [`charts/line-basic/design.md`](../line-basic/design.md)) and adds the sibling
> build detail: data model, marks, leader layout, reused chrome, parity traps,
> and the a11y DOM contract.

- **Chart id:** `timeline`
- **Spec `type`:** `"timeline"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank:** later sibling —
  rides Rank 3 (numeric-x-axis) for datetime placement and Rank 2 (orientation)
  for the vertical subtype · **Src:** HC
- **Status:** design-complete + examples validated · renderers deferred (only
  `line` has a live renderer today; timeline rides the shared cartesian frame
  once the numeric-x-axis lands — see
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §2
  Family A "Timeline" row, §3.2 numeric-x-axis + orientation, §4, §5)
- **Renderers (planned):** `libs/python/peakcharts/charts/timeline.py` · `libs/go/timeline.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A timeline chart: a set of **events** placed along **one** time axis. Each event
is a **marker** on a single baseline (the "spine") at the pixel that its
**datetime** maps to, annotated by a **label** connected with a short **leader
line**. There is no value (magnitude) dimension — every marker sits on the same
spine; the axis encodes *when*, the label encodes *what*.

Timeline is a **later Cartesian sibling**. It adds no new substrate: it reuses
the **numeric-x (datetime) axis** that scatter introduces (Rank 3), the shared
**marker** primitive, the frame's **single axis line** as its spine, and every
piece of chrome/a11y/parity. Its only net-new marks are the **leader line** and
the **event label** (an alternating above/below data-label), plus the
**orientation** flag (horizontal ⇄ vertical) it borrows from bar (Rank 2). The
value axis is **collapsed** — the frame is asked for the time axis only.

## Use it when

- Your data is a **list of dated events** — deploys, incidents, releases,
  migrations, contract milestones — and you want to show **when** each happened
  along a continuous time axis, not a magnitude.
- Rows look like: `datetime -> label` (one event) — an ordered sequence of
  `{when, what}` with **no y-value**.
- You want one axis (time) plus **annotations**: a marker per event and a text
  label with a leader, laid out so labels don't collide.

Do **not** use it for: a **magnitude over time** (use `line-basic` or
`column`), **spans with a start and end** (use `xrange`/Gantt — a timeline is
instants, not intervals), **counts per time bucket** (use `column`/`histogram`),
or **before/after per category** (use `dumbbell`). See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- each `series[].data`: `N` **numbers** — the event **positions on the time
  axis** (epoch-milliseconds for a `datetime` axis, or a plain ordinal). This is
  the same `number[]` payload line/column use, so timeline goldens never move
  when the point model lands.
- each `series[].labels` (parallel): `N` **strings** — the event **names**
  (the `{name}` half of each `{x, name}` event). Aligned to `data` by index.
- `xAxis.type: "datetime"` (optional): marks the numeric x as a **datetime**
  domain so ticks format as dates; absent → a plain numeric/ordinal axis.
- multiple series = **parallel event lanes** on one shared time axis (e.g.
  Deploys and Incidents), each lane offset from the spine in series-index order.

The richer end-state datum is `{x: <datetime>, name: <label>}` (the point
model's `x` + `name` fields, §3.2). Today it is expressed as the `data:number[]`
positions plus the parallel `labels:string[]`; when the point model lands the
two collapse into one `data: [{x, name}]` array with **no golden churn** (the
bare-number fast path keeps `x = value`).

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"timeline"` |
| `id` | string | `pk` | chart instance id; namespaces `<defs>` ids (gradients/patterns) so multiple charts on one page don't collide — set a unique value per chart when embedding several |
| `theme` | string \| object | `light` | color theme: `light` (default) / `dark`, or a full theme object overriding any field; resolved server-side into concrete SVG colors. Canonical values in `spec/themes/*.json` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle (swatch is the event marker) — meaningful when several event lanes share the axis |
| `a11y` | bool | true | accessibility (on by default): SVG gets `role="img"` + a summary `aria-label` + `<desc>`; HTML adds a visually-hidden data table (event label + date per row). `false` restores the pre-a11y bytes |
| `responsive` | bool | false | scale to container (viewBox + `width:100%`) instead of fixed px |
| **`orientation`** | string | `"horizontal"` | **NEW field.** `"horizontal"` = time runs along **x**, spine horizontal, labels alternate above/below; `"vertical"` = time runs down **y**, spine vertical, labels alternate left/right. This is the **orientation-transpose** (§3.2), shared with bar — a coordinate remap, not a forked renderer. Added via the §5.4b five-place lockstep |
| **`leaders`** | bool | true | **NEW field.** Draw a short **leader line** from each marker to its label. `false` = labels sit adjacent with no connector. Added via the §5.4b five-place lockstep |
| `xAxis.type` | string | — | `"datetime"` marks the time axis as a datetime domain (ticks format as dates, deferred); absent → numeric/ordinal axis. Forward-compatible axis field |
| `xAxis.title` | string | — | time-axis label |
| `xAxis.min` / `xAxis.max` | number | auto (nice ticks over the data, **zero NOT forced in**) | clamp the visible time window. Unlike the value axis, the time axis does **not** anchor at 0 (`include_zero=False`, §3.2) — a Q2 window must not stretch back to epoch 0 |
| `xAxis.gridLine` | object | `{enabled:true, color:#e8e8ee, dashStyle:solid}` | vertical time-gridline styling; `dashStyle` ∈ solid/dashed/dotted |
| `series[].name` | string | `Series i` | legend + tooltip name (the lane name, e.g. "Deploys") |
| `series[].data` | number[] | — | event **positions on the time axis**, length `N` (epoch-ms or ordinal) |
| **`series[].labels`** | string[] | — | **NEW field.** event **names**, length `N`, aligned to `data` by index — the label text rendered next to each marker and shown in the data table. Every entry `esc`'d. Added via the §5.4b five-place lockstep |
| `series[].color` | string \| gradient | palette by index | the **marker fill**: hex `#2f7ed8`, or a `{type:linearGradient, …}` object (legend swatch uses stop 0) |
| `series[].pattern` | object | — | hatch fill for the marker: `{type:hatch, color, background, size, angle, strokeWidth}` (resolves to `url(#pat)`) |
| `series[].marker` | object | `{enabled:true, symbol:circle, radius:5}` | event marker; `symbol` ∈ circle/square/triangle/diamond, `radius` sizes the glyph. Events are larger than line points by default (they are the focal element) |

Fields carried over from the line/column spec but **inert** for timeline (no
line to draw, no magnitude to stack): `fillOpacity`, `lineWidth`, `dashStyle`,
`step`, `curve`, `stacking`, `grouping`, `yAxis.*` are accepted by the shared
validator (forward-compatible) but not consumed by the timeline marks — the
value axis is collapsed to the single spine. Full schema:
[`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Data model

- **Value payload:** `series[].data` is `number[]` — one **time position** per
  event, the same shape line/column use. No `{x,name}` object model yet (that
  arrives with the point model, Rank 3); today the parallel `series[].labels`
  carries the `name` half.
- **Single lane (basic):** one series → one spine; markers at `xpix(data[i])`
  along it; labels alternate above/below (horizontal) to avoid collision.
- **Parallel lanes (multi-series):** each series `k` gets its own spine offset
  from the plot center, assigned in **series index order**; all lanes share the
  **same** time axis so events line up in time across lanes.
- **The frame owns the time axis.** Timeline delegates with the **numeric-x
  (datetime) scale** and **`include_zero=False`** — the x-domain is
  `nice_ticks` over the event positions with **0 NOT forced in** (§3.2 caveat:
  never carry the value-axis zero-anchor into a free time axis). The marks never
  recompute a scale — they call `fr.xpix` only. The **value (y) axis is
  suppressed**: no y-scale, no y-gridlines; the spine is a single baseline the
  marks draw (or reuse from the axis line).

## Marks — what this renderer draws

The renderer is a **one-line delegation** to the shared frame; it supplies
**only** a marks callback and re-implements no chrome (§5.2). It passes the
**numeric-x scale** and **`include_zero=False`** (free time axis, §3.2):

```python
# libs/python/peakcharts/charts/timeline.py
from ._cartesian import CartesianFrame, render_cartesian

def render_svg(spec) -> str:
    return render_cartesian(spec, "Timeline", "numeric", _timeline_marks,
                            include_zero=False)   # free datetime x, no zero-anchor
```
```go
// libs/go/timeline.go — package peakcharts
func renderTimelineSVG(spec *ChartSpec) string {
    return renderCartesian(spec, "Timeline", "numeric", timelineMarks, false)
}
```

The marks callback emits **exactly one** `<g class="pk-series" data-series="{si}">`
per series, and inside it, **per event**, a **leader line + marker + label**:

```html
<g class="pk-series" data-series="0">
  <line class="pk-leader" data-series="0"
        x1="128.4" y1="230.0" x2="128.4" y2="202.0" stroke="#c8c8d0"/>
  <circle class="pk-event pk-point" data-series="0"
        data-series-name="Deploys" data-x="v4.4.0 — cache layer" data-y="1.77872e+12"
        data-color="#2f7ed8" data-r="5" data-r-hover="8"
        cx="128.4" cy="230.0" r="5" fill="#2f7ed8"/>
  <text class="pk-label" data-series="0" x="128.4" y="196.0"
        text-anchor="middle">v4.4.0 — cache layer</text>
  … one leader+marker+label per event …
</g>
```

- **Class:** `pk-event pk-point`. `pk-point` is the **contract** class the
  runtime keys on (tooltip / highlight / crosshair / legend-toggle); `pk-event`
  is a purely-cosmetic CSS hook (adding a class the runtime must *know about* is
  out of scope — NN#2). The marker **is** the hoverable point. `pk-leader` and
  `pk-label` are cosmetic too — they carry `data-series="{si}"` (or sit inside
  the group) so the legend toggle hides them with the series.
- **Geometry (horizontal):** `cx = fr.xpix(data[i])` (datetime → pixel via the
  numeric-x scale); `cy = baseY` (the spine, `plot_y + plot_h/2`). The leader
  runs from the spine to the label anchor `labelY(k) = baseY + side(k)*LEAD`;
  the label `<text>` sits just beyond it (`text-anchor="middle"`), alternating
  above/below by `side(k)`.
- **Geometry (vertical):** the orientation-transpose swaps the axes — the time
  axis becomes **y** (`cy = fr.ypix_time(data[i])`), the spine is vertical
  (`cx = spineX`), leaders run left/right by `side(k)`, labels are
  `text-anchor="start"`/`"end"`. Same `fmt_num`/`f1` and constants — orientation
  is a coordinate remap only (parity is free).
- **Marker shape:** reuse the four shared marker symbols (circle/square/
  triangle/diamond) via the shared `_marker`/`markerSVG` helper — timeline adds
  **no** new glyph.
- **Fill:** read `fr.styles[si].fill` — the resolved marker paint. Resolve as
  **pattern → `url(#pat)`; gradient → `url(#grad)`; else the solid hex.** Never
  read `area_fill` (that is line's under-fill); never leave a marker unfilled.
- **`cx` / `cy`:** every `.pk-point` MUST carry `cx` (marker center on the time
  axis) — the crosshair reads it — and by convention `cy`.
- **Legend swatch:** emitted by the shared **tail** with the same `data-series`
  index — do not renumber and do not emit a legend from the marks.

## Layout — the pinned geometry (leaders + lanes)

Evaluate the arithmetic in **exactly this operation order** in both languages so
`f1` / `:.1f` rounding lands ULP-for-ULP identically (blueprint §3.2 numeric-x +
orientation; the frame's `xpix` implements the datetime→pixel map, the marks
build the spine + leaders):

```
# horizontal orientation (default)
baseY(k)   = plot_y + plot_h/2 + laneOffset(k)   # spine for lane k (single series ⇒ laneOffset=0)
xpix(t)    = numeric-x datetime scale of value t # frame method; include_zero=False
LEAD       = 28.0                                # leader length (px) — fixed constant
side(k)    = -1.0 if (k % 2 == 0) else +1.0      # alternate above(-)/below(+) by EVENT index k
labelY(k)  = baseY + side(k)*LEAD                # leader end / label anchor
markerR    = marker.radius (default 5.0)         # event glyph radius

# single event (n == 1): place at the spine center of the plot
xpix(t)    = plot_x + plot_w/2                    # mirror the point-scale n<=1 rule; pin identically
```

- `LEAD = 28.0` and the `side(k)` even/odd alternation are **fixed constants**,
  not per-author choices — pin both, evaluated in this order, in Python and Go.
- **The alternation index `k` is the EVENT index within the series** (0-based),
  not the series index. Pin it so labels above/below match across languages.
- **Multi-series lanes:** `laneOffset(k)` is assigned in **series index order**
  (lane 0 on the spine, lane 1 offset, …); pin the offset sequence so parallel
  lanes land identically. All lanes share the **same** `xpix` (one time axis).
- **Vertical orientation** transposes: `baseX(k) = plot_x + plot_w/2 +
  laneOffset(k)`; the time value maps through the y-scale; `side(k)` flips
  leaders left/right; same `LEAD`, same constants — a pure coordinate remap.
- **The frame owns the time domain** with `include_zero=False` — the marks call
  `fr.xpix` only and never force 0 in (a Q2 window must not anchor at epoch 0).

## Reused chrome (obtained from the frame — never re-implemented)

Timeline inherits, with **zero** re-implementation (§3.1, §4.2):

- Plot area + margins; the **single axis line** used as the spine; axis title.
- **Numeric-x (datetime) scale** via `nice_ticks` → `xpix` (the same
  parity-locked machinery scatter introduces, Rank 3) with `include_zero=False`;
  x tick labels + vertical time-gridlines.
- Titles + subtitle; legend (bottom-center, one swatch per event lane);
  crosshair.
- Themes (light/dark/custom) resolved server-side; palette pickup.
- `<defs>` pre-pass: gradient/pattern paint resolution + `SeriesStyle.fill`,
  id-scoping via `cid` (defs emitted only when a series needs them — no empty
  `<defs>` under the light theme).
- A11y: `role="img"` + `aria-label` + `<desc>` + visually-hidden data table +
  keyboard nav. Responsive `<svg>` viewBox; the shared JS runtime.
- `esc`, `fmt_num`/`fmtNum` (`%g` 6-sig values), `:.1f`/`f1` (pixel coords) —
  all parity-locked.

The chart delegates with `x_scale="numeric"` and `include_zero=False` (free time
axis). It passes the bare noun **`"Timeline"`** — the frame expands it to
`"Timeline chart with N series…"` byte-for-byte. The **value (y) axis is
collapsed**: timeline does not request y-gridlines or y-labels.

## Parity traps (verify before the byte-parity gate)

- **Leader/lane arithmetic ORDER** — evaluate `baseY`, `labelY`, `laneOffset` in
  the exact order above; a reassociated `plot_y + plot_h/2` or `side(k)*LEAD`
  diverges after `f1` rounding.
- **Alternation index** — `side(k)` keys on the **event** index (even/odd), pinned
  identically; a series-index mixup flips labels on one side.
- **Free time axis (`include_zero=False`)** — the time axis reuses the value-axis
  routine with the zero-anchor **OFF** (§3.2). Both languages would be wrong
  *identically* (and pass byte-parity) if zero were forced in — so the
  `include_zero=False` flag must be explicit, and the marks must never
  recompute the scale.
- **Single-event degenerate** — `n == 1` must place the marker at
  `plot_x + plot_w/2` (mirror the point-scale `n<=1` rule); pin identically so a
  one-event timeline doesn't divide by `n-1 == 0`.
- **Marker-fill resolution** — pattern → `url(#pat)`; gradient → `url(#grad)`;
  else solid hex. Reading `solid` silently drops gradient/pattern; reading
  `area_fill` is line's field. Never emit an unfilled marker.
- **`data-x` is the label, `data-y` is the position** — `data-x = esc(labels[i])`
  (the event name — the meaningful x annotation, exactly as column uses the
  category label), `data-y = esc(fmt_num(data[i]))` (the datetime/ordinal). The
  pixel `cx` derives from `data[i]` via `fr.xpix`, **not** from `data-x`. Keep
  this split identical in both languages.
- **Formatters** — `cx,cy,x1,y1,x2,y2,x,y` via `:.1f`/`f1`; `data-y`, radii via
  `fmt_num`/`fmtNum`; every user string (`data-series-name`, `data-x`, label
  text, custom color) via `esc`. A leaked raw `<` fails the XSS tests.
- **Orientation transpose is a remap only** — vertical must reuse the same
  constants (`LEAD`, `side`) and formatters; it may not fork a second geometry.
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

- **Series group:** `.pk-series[data-series=N]` — one per event lane; `N` is the
  integer series index, **consistent** across the group, its markers, and the
  legend item (do not renumber). The leader and label carry `data-series="N"`
  (or nest in the group) so they toggle/highlight with the series.
- **Datum mark:** `.pk-point` (here also `.pk-event`) carries **all** of
  `data-series`, `data-series-name`, `data-x`, `data-y`, `data-color`, `data-r`,
  `data-r-hover`.
- **Crosshair anchor:** every `.pk-point` carries a `cx` (marker center on the
  time axis) and by convention `cy`.
- **Escaping/formatting in `data-*`:** `data-series-name = esc(s.name)`;
  `data-x = esc(labels[i])` (the event name; falls back to
  `esc(fmt_num(data[i]))` when no label); `data-y = esc(fmt_num(data[i]))` (the
  datetime/ordinal); `data-color = fr.styles[si].solid`;
  `data-r`/`data-r-hover = fmt_num(...)`. Pixel attrs use `:.1f`/`f1`.
- **A11y default-on:** `role="img"` + concise `aria-label` + `<desc>` in the SVG;
  a separate **visually-hidden data table** in the HTML pairing each event's
  **label** with its **date/position**; keyboard nav walks the markers.
  `a11y:false` restores the pre-a11y bytes. Timeline keeps `data: number[]`, so
  the existing `number[]` data table renders the positions faithfully and the
  parallel `labels` enrich each row. **When the point model lands** (`data`
  becomes `{x,name}`) the data table MUST generalize in lockstep so each row
  shows the label + date, not a coerced single number (§5.4b-DT).
- **Static-first:** the chart is fully readable with JS disabled — markers,
  leaders, and labels are server-rendered; the crosshair ships `display:none`;
  the tooltip is JS-only.

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "timeline",
  "title": "Production Deploys — Q2 2026",
  "subtitle": "Release timeline on a datetime axis, with labels and leaders",
  "orientation": "horizontal",
  "leaders": true,
  "xAxis": { "type": "datetime", "title": "Date" },
  "series": [
    {
      "name": "Deploys",
      "data": [1775088000000, 1776729600000, 1778716800000, 1780444800000, 1782345600000],
      "labels": [
        "v4.2.0 — API gateway",
        "v4.3.0 — auth revamp",
        "v4.4.0 — cache layer",
        "v4.5.0 — query planner",
        "v4.6.0 — cold-start fix"
      ]
    }
  ]
}
```

## Examples

Each file is a complete, realistic spec that passes `validate() == []`:

| File | Exercises |
|------|-----------|
| [`examples/basic.json`](examples/basic.json) | single lane, horizontal, datetime axis, labels + leaders, alternating above/below |
| [`examples/multi.json`](examples/multi.json) | two parallel lanes (Deploys + Incidents) sharing one time axis, custom colors + marker symbols (circle/diamond) |
| [`examples/vertical.json`](examples/vertical.json) | `orientation:"vertical"` roadmap milestones (time top-to-bottom), square markers, left/right leaders |
| [`examples/adversarial.json`](examples/adversarial.json) | `theme:"dark"` + hostile strings (`<script>`, `"`, `<`, `&`) in **every** marks-emitted field (series name, event label, custom color) — the XSS fixture |

The full golden build set pins the **`adversarial`** case as the hostile-string
witness so the XSS tests run against the timeline marks (§5.5d).
`TIMELINE_CASES = ["basic","multi","vertical","adversarial"]`.

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/timeline/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    type="timeline",
    title="Production Deploys — Q2 2026",
    x_axis=Axis(title="Date"),                       # xAxis.type="datetime" via from_dict
    series=[
        Series("Deploys",
               [1775088000000, 1776729600000, 1778716800000, 1780444800000, 1782345600000]),
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
- **Hover an event marker** → tooltip (label, lane, date) + marker highlight + crosshair.
- **Click a legend item** → toggle that event lane on/off.
- **Keyboard** → arrows walk the markers in time order; Esc clears without stealing focus.
- Renders fully (static) even with JavaScript disabled — markers, leaders, and labels are all server-rendered.

## Rendering notes

- The time axis uses "nice numbers" ticks (~6) over the event positions and does
  **not** force 0 into the domain (`include_zero=False`) — the window fits the
  events, not epoch 0.
- Timeline uses the **numeric-x (datetime)** scale (`x_scale="numeric"`) —
  markers land proportionally in time; labels alternate above/below to avoid
  collision. Evenly-spaced milestone timelines can instead ride the point scale
  (index positions) with labels driving the annotation.
- Colors cycle the theme palette (`theme.palette`) when `series[].color` is
  unset; a gradient/pattern color fills the marker via the `<defs>` pre-pass.
- The value (y) axis is **collapsed** — no magnitude, no y-gridlines; the single
  spine is the only baseline.

## Not yet supported (roadmap)

- Live renderers (`timeline.py` / `timeline.go`) — deferred; design + examples +
  validation are complete. Only `line` renders today. Timeline lands after the
  numeric-x-axis (Rank 3) and orientation (Rank 2) generalizations exist.
- **Spans/intervals** (an event with a start *and* end) — that is `xrange`/Gantt,
  not timeline (timeline is instants).
- Automatic **datetime tick formatting** (epoch-ms → readable dates), smart
  label de-collision (beyond simple above/below alternation), and a `leader`
  **object** for per-lane leader styling — variants layered on this base.
- A dedicated `series[].labels` → point-model `{x,name}` migration (collapses the
  parallel array into the datum), under the Rank-3 byte-identity gate (§3.3).
