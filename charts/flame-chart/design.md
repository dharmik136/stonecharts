# Chart: Flame Chart — time-ordered (`flame-chart`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any StoneCharts language library without looking anywhere
> else. Format is identical for every chart type — this recipe copies the
> Cartesian **exemplar** [`charts/column/design.md`](../column/design.md) and swaps
> in the flame-chart build detail: the `{x, x2, depth, name}` frame point model,
> the floating-bar mark on a **numeric value x-axis**, the **depth lane** (per-row
> stack level), the per-frame label, the reused chrome, the parity traps, and the
> a11y DOM contract.

- **Chart id:** `flame-chart`
- **Spec `type`:** `"flame-chart"`
- **Class:** `sibling` (Family A — Cartesian/XY) · **Build rank:** late sibling —
  reuses **band-layout** (Rank 1), **orientation transpose** (Rank 2),
  **numeric x-axis** (Rank 3), and the **floating-bar primitive** (Rank 8);
  forces no new *primitive*, only the frame composition · **Src:** PS
- **Status:** design-complete + examples validated
- **Renderers:** `libs/python/stonecharts/charts/flame_chart.py` · `libs/go/flame_chart.go`
- **Substrate:** [`charts/_cartesian/README.md`](../_cartesian/README.md) — the shared frame
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md) · binding build contract
  [`docs/roadmap/chart-families.md`](../../docs/roadmap/chart-families.md) §3–§5

## What it is

A flame chart: one or more series of **call frames** (function invocations)
drawn as **horizontal floating bars** spanning `[start, end]` on a **wall-clock
numeric x-axis**, stacked by **depth** on the y-axis (depth 0 = root/outermost at
bottom, increasing upward). Each bar represents one function call's duration at
its stack level. This is the **time-ordered** view — Chrome DevTools Performance,
Perfetto, async-profiler timeline — not the aggregated flame graph (which lives
in Family D / Hierarchy).

## Use it when

- Your data is a set of **timed function calls** — each has a **start, end, and
  stack depth**, and optionally a **name** and **category/color**.
- Classic cases:
  - **CPU profiler timeline** — wall-clock function call intervals per thread.
  - **Trace span breakdown** — detailed per-thread span stack from a distributed
    trace.
  - **Async task timeline** — overlapping async operations stacked by depth.

## Don't use it when

| Instead of flame-chart | Use |
|---|---|
| Aggregated stack profiles (width = sample count) | Flame graph (Family D, planned) |
| Spans across categorical lanes (Gantt / swimlane) | `xrange` |
| Single point events on a time axis | `timeline` |
| Plain time-series trend | `line-basic` |

## Spec fields (flame-chart-specific)

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `type` | `"flame-chart"` | yes | — | |
| `series[].frames` | `array of Frame` | yes | — | One frame per function call |
| `series[].frames[].x` | `number` | yes | — | Start time/position |
| `series[].frames[].x2` | `number` | yes | — | End time/position |
| `series[].frames[].depth` | `integer` | yes | — | Stack depth (0 = root at bottom) |
| `series[].frames[].name` | `string` | no | `""` | Function/frame name (rendered as label when bar is wide enough) |
| `series[].frames[].color` | `string` | no | palette | Per-frame color override |

All standard Cartesian fields (`title`, `subtitle`, `xAxis`, `yAxis`, `theme`,
`width`, `height`, `legend`, `a11y`, `responsive`, `layout`) apply.

## Example spec

```json
{
  "type": "flame-chart",
  "title": "Request Handler Profile",
  "xAxis": { "title": "Time (ms)" },
  "yAxis": { "title": "Stack Depth" },
  "series": [
    {
      "name": "main",
      "frames": [
        { "x": 0, "x2": 100, "depth": 0, "name": "handleRequest" },
        { "x": 0, "x2": 60,  "depth": 1, "name": "parseBody" },
        { "x": 60, "x2": 100, "depth": 1, "name": "respond" },
        { "x": 5, "x2": 45,  "depth": 2, "name": "jsonDecode" },
        { "x": 60, "x2": 85, "depth": 2, "name": "serialize" },
        { "x": 85, "x2": 98, "depth": 2, "name": "write" }
      ]
    }
  ]
}
```

## Rendering rules

1. **Orientation:** horizontal (value axis on x, depth lanes on y). The chart
   rides `render_cartesian(spec, "Flame chart", "band", marks, include_zero=False,
   orientation="horizontal")`.
2. **Y-axis lanes:** one lane per depth level (0 through max_depth). Depth 0
   appears at the **bottom** of the plot area (y grows upward — inverted from
   typical band layout). Categories are generated as `["0", "1", ..., "N"]`.
3. **Frame bars:** each frame is a `<rect class="sc-frame sc-point">` spanning
   `x..x2` horizontally and occupying the depth lane vertically. Bar thickness
   is `lane_height * 0.8`. Minimum width clamped to 1px.
4. **Frame labels:** if the frame bar is wide enough (>40px), the frame `name`
   is rendered as `<text class="sc-frame-label">` centered inside the bar,
   truncated with `…` if too wide.
5. **Color:** per-frame `color` field overrides the series palette color. Bars
   use `fill` (the resolved paint for bar-type series).
6. **Data attributes:** each `<rect>` carries `data-series`, `data-series-name`,
   `data-x` (depth label), `data-y` (start), `data-start`, `data-end`,
   `data-depth`, `data-name`, `data-duration`, `data-color`, `data-r`,
   `data-r-hover`, `cx`, `cy`.
7. **Data table (a11y):** columns: Series, Depth, Start, End, Duration, Name.
   One row per frame.

## Parity traps

- Depth 0 at bottom, max depth at top — requires reversing the band y-mapping.
- Frame label truncation must match pixel-for-pixel between Python and Go.
- Bar width clamping at 1px minimum to keep zero-duration frames visible.
