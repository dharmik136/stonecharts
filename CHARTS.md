# CHARTS.md — the smart chart router

Hand this file to an agent (or read it yourself) with **your data and your
intent**, and it tells you **which chart to use and exactly how to build it**.
Each chart's own `design.md` is the complete build recipe; this file is the map
to them.

## How to use this file

1. **Describe the data shape.** How many columns, what are their types, is x
   ordered/categorical/continuous, how many series?
2. **Describe the intent.** Trend over time? Compare categories? Part-to-whole?
   Correlation? Distribution?
3. **Match** against the catalog below (use the decision guide if unsure).
4. **Open that chart's `design.md`** (linked in the table). It lists every spec
   field, an example spec, and the code to render it in each language.
5. **Build the spec** to `spec/chart-spec.schema.json` and render with any
   language library (e.g. Python `stonecharts.save_html(spec, "out.html")`).

An agent should output: the chosen chart id, a filled-in spec (JSON matching the
schema), and the one render call — nothing more is needed.

## Decision guide (data shape + intent → chart)

| Your data / intent | Use |
|--------------------|-----|
| Ordered x (time/categories) + continuous y, show a **trend** or compare a few series | **`line-basic`** |
| Compare a value **across categories** (ranking, few groups) | `bar` / `column` |
| Trend **plus magnitude/volume** under the line | `area` |
| Composition + **volume flow** of many series over ordered time (theme river) | `streamgraph` |
| **Part-to-whole** of a single total | `pie` / `donut` _(planned)_ |
| **Correlation** between two continuous variables (x,y points) | `scatter` |
| Correlation + a third value as size | `bubble` |
| Value across a **2-D grid** (matrix) | `heatmap` _(planned)_ |
| A single KPI against a range | `gauge` _(planned)_ |

## Catalog

| Chart id | Fits this data | Use when | Not for | Status | Recipe |
|----------|----------------|----------|---------|--------|--------|
| `line-basic` | categories[N] + one-or-more series of N numbers | trend / compare a few series over shared x | part-to-whole, x/y correlation, distributions | **Python ✅ · Go ✅ (byte-identical)** | [design.md](charts/line-basic/design.md) |
| `column` | categories[N] + one-or-more series of N numbers | compare a value across categories; grouped, stacked, or percent-stacked composition | trend (use line), x/y correlation (use scatter), part-to-whole (use pie/donut), distributions (use histogram) | Design ✅ · render ✅ (certified, 0.0.0.1) | [design.md](charts/column/design.md) |
| `bar` | categories[N] + series of numbers | compare categories horizontally (grouped/stacked/percent), ranked; long labels | trend (use line), correlation (use scatter) | Design ✅ · render ✅ (certified, 0.0.0.2) | [design.md](charts/bar/design.md) |
| `area` | categories[N] + series of numbers | trend + volume/magnitude under the line; stacked/percent composition over time | trend without volume (use `line-basic`), part-to-whole of one total (use pie), x/y correlation (use `scatter`) | Design ✅ · render ✅ (certified, 0.0.0.1) | [design.md](charts/area/design.md) |
| `streamgraph` | ordered x[N] + several series of numbers (≥0) | composition + volume flow of many streams over time (wiggle / silhouette) | precise value reading, part-to-whole, few series | Design ✅ · render deferred | [design.md](charts/streamgraph/design.md) |
| `arearange` | categories[N] + per-series `(low,high)` band (highs in `data`, lows in the forward-compatible `low` companion until the `{low,high}` point model lands) | show an interval / envelope / confidence band over ordered x (p50–p95 latency, min–max range, forecast ±) | single trends (use `line-basic`), floating per-category bars (use `columnrange`), interval with a meaningful center estimate (use `errorbar`), part-to-whole (use stacked `area`) | Design ✅ · render deferred | [design.md](charts/arearange/design.md) |
| `columnrange` | categories[N] + a (low,high) band per category (interim encoding: `data`=low + parallel `high[]`) | show a min–max / low–high band per category as floating bars (grouped; vertical or horizontal) | single-value comparison (use `column`), band over continuous x (use `arearange`), OHLC (use `candlestick`) | Design ✅ · render deferred | [design.md](charts/columnrange/design.md) |
| `scatter` | series of (x,y) numeric points | correlation / spread / clustering between two continuous variables | trend (use line), category ranking (use column/bar), one-variable distribution (use histogram) | Design ✅ · render ✅ (targeting 0.0.0.3, DEC-015) | [design.md](charts/scatter/design.md) |
| `bubble` | series of [x,y,z] coordinates | correlation + bubble size representing volume | simple comparison | Design ✅ · render deferred | [design.md](charts/bubble/design.md) |
| `combo` | categories[N] + series of numbers, each tagged `type`∈{line,column} | overlay two mark kinds (throughput bars + latency/trend line) on a shared or dual y-axis | single-mark data (use line or column), x/y correlation (use scatter), part-to-whole (use pie) | Design ✅ · render deferred | [design.md](charts/combo/design.md) |
| `candlestick` | window[N] + {open,high,low,close} per window | show OHLC min/max/first/last per time window (direction + range at a glance) | plain trend (use line), category counts (use column), (low,high) band (use arearange/columnrange) | Design ✅ · render deferred | [design.md](charts/candlestick/design.md) |
| `error-bar` | categories[N] + series of center `y` plus parallel `low`/`high` bounds | show a magnitude and its uncertainty (CI / std error / percentile spread), often overlaid on column/line/scatter | pure range with no center (arearange/columnrange), full distribution (boxplot), plain trend (line) | Design ✅ · render deferred | [design.md](charts/error-bar/design.md) |
| `boxplot` | 5-number distributions per category | statistical summary of latency distributions | single trends | Design ✅ · render deferred | [design.md](charts/boxplot/design.md) |
| `waterfall` | stage-by-stage delta calculations | budget or latency breakdowns with running totals | raw distributions | Design ✅ · render deferred | [design.md](charts/waterfall/design.md) |
| `histogram` | raw sample list (number[]) or pre-binned counts + binEdges | show the distribution / shape of one continuous variable (binned) | category ranking (use column), correlation (use scatter), 5-number summary (use boxplot) | Design ✅ · render deferred | [design.md](charts/histogram/design.md) |
| `lollipop` | categories[N] + series of numbers | rank/compare categories with a light stem+dot (many categories, or a ranking) | trend (use line), part-to-whole (use pie), magnitude-as-area (use column) | Design ✅ · render deferred | [design.md](charts/lollipop/design.md) |
| `dumbbell` | categories[N] + a `{low,high}` range per category (`data`=lows, `high`=highs) | before/after or min–max comparison across categories where the gap is the story (grouped / horizontal ranked) | single value per category (use `column`/`lollipop`), trend over time (use `line-basic`), filled band (use `arearange`), solid floating-bar range (use `columnrange`), center+interval (use `error-bar`) | Design ✅ · render deferred | [design.md](charts/dumbbell/design.md) |
| `timeline` | series of dated events (datetime position + label) | show WHEN deploys/incidents/releases/milestones happened along a time axis | magnitude over time (use line/column), spans with start+end (use xrange/Gantt), per-bucket counts (use histogram) | Design ✅ · render deferred | [design.md](charts/timeline/design.md) |
| `xrange` | series of spans `{x:start, x2:end, y:lane}` across category lanes on a datetime x-axis (+ Gantt milestones & dependencies) | Gantt charts, distributed-trace span waterfalls, per-thread swimlanes over time | single magnitude per category (use column/bar), a value band with no time semantics (use columnrange), single-point events (use timeline), aggregated flame graphs (Hierarchy) | Design ✅ · render deferred | [design.md](charts/xrange/design.md) |
| `funnel` | one series of N stage values + stage labels (categories[N]) | conversion / drop-off across ordered pipeline stages | trend (line), category ranking (column/bar), true part-to-whole of one total (pie/donut) | Design ✅ · render deferred | [design.md](charts/funnel/design.md) |
| `variwide` | categories[N] + per-category (height y, width z) pairs | compare a value where each category also has a meaningful width (e.g. cost/capita × population) | equal-width comparison (use column), trend (use line) | Design ✅ · render deferred | [design.md](charts/variwide/design.md) |
| `technical-indicators` | ordered/time x + a base metric or price series (number[]) | overlay derived indicators (SMA/EMA, Bollinger bands, MACD, RSI, VWAP) + plot bands/lines + event flags on a metric/price trend | plain trend (line-basic), OHLC glyph per window (candlestick), two authored measures with no transform (combo), a supplied static (low,high) band (arearange) | Design ✅ · render deferred | [design.md](charts/technical-indicators/design.md) |
| `vector-plot` | series of [x,y,direction,length] field samples | show direction + magnitude at each point of a field (wind / flow / force / gradient) | x/y correlation only (use scatter), size-only third value (use bubble), category ranking (use column) | Design ✅ · render deferred | [design.md](charts/vector-plot/design.md) |
| `windbarb` | datetime[N] + per-point {speed, direction} (speed in `data`, direction in the forward-compatible companion) | show wind **speed and direction** at a glance along a time axis (meteogram wind strip) | speed trend (use line), direction frequency (use wind rose), generic vector field (use vector plot) | Design ✅ · render deferred | [design.md](charts/windbarb/design.md) |

_Every Cartesian (Family A) Highcharts-baseline type above is design-complete with validated example specs; renderers land per the build order in [docs/roadmap/chart-families.md](docs/roadmap/chart-families.md) (§3.3), starting with `column`. Other families (pie/polar, heatmap/matrix, treemap/hierarchy, sankey/flow, geo, KPI) open later per the same roadmap._

## Add a chart (for contributors / agents extending this)

1. Create `charts/<id>/design.md` (copy the structure of `line-basic/design.md`)
   and `charts/<id>/examples/`.
2. Add a renderer per language: `libs/<lang>/.../charts/<id>` following
   `spec/svg-contract.md`.
3. Register the `type` in `spec/chart-spec.schema.json` and each language's
   render registry.
4. Add a catalog row here and a decision-guide entry.
