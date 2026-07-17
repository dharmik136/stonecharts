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
   language library (e.g. Python `peakcharts.save_html(spec, "out.html")`).

An agent should output: the chosen chart id, a filled-in spec (JSON matching the
schema), and the one render call — nothing more is needed.

## Decision guide (data shape + intent → chart)

| Your data / intent | Use |
|--------------------|-----|
| Ordered x (time/categories) + continuous y, show a **trend** or compare a few series | **`line-basic`** |
| Compare a value **across categories** (ranking, few groups) | `bar` / `column` _(planned)_ |
| Trend **plus magnitude/volume** under the line | `area` _(planned)_ |
| **Part-to-whole** of a single total | `pie` / `donut` _(planned)_ |
| **Correlation** between two continuous variables (x,y points) | `scatter` _(planned)_ |
| Correlation + a third value as size | `bubble` _(planned)_ |
| Value across a **2-D grid** (matrix) | `heatmap` _(planned)_ |
| A single KPI against a range | `gauge` _(planned)_ |

## Catalog

| Chart id | Fits this data | Use when | Not for | Status | Recipe |
|----------|----------------|----------|---------|--------|--------|
| `line-basic` | categories[N] + one-or-more series of N numbers | trend / compare a few series over shared x | part-to-whole, x/y correlation, distributions | Python ✅ · Go ✅ | [design.md](charts/line-basic/design.md) |

_Everything below is the coverage roadmap (the chart-type checklist), added one
at a time, each becoming a row above with its own `charts/<id>/design.md`:_

- `column` / `bar`, `area` / `area-stacked`, `line-spline`
- `pie` / `donut`, `scatter`, `bubble`
- `heatmap`, `treemap`, `gauge`, `candlestick`, `boxplot`, `radar`

## Add a chart (for contributors / agents extending this)

1. Create `charts/<id>/design.md` (copy the structure of `line-basic/design.md`)
   and `charts/<id>/examples/`.
2. Add a renderer per language: `libs/<lang>/.../charts/<id>` following
   `spec/svg-contract.md`.
3. Register the `type` in `spec/chart-spec.schema.json` and each language's
   render registry.
4. Add a catalog row here and a decision-guide entry.
