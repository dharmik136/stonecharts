# Chart: Basic Line (`line-basic`)

> A single-file, self-describing spec for this chart. Read this and you can
> produce the chart in any PeakCharts language library without looking anywhere
> else. Format is identical for every chart type.

- **Chart id:** `line-basic`
- **Spec `type`:** `"line"`
- **Status:** Python ✅ · Go ⏳
- **Renderers:** `libs/python/peakcharts/charts/line.py`
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md)

## What it is

A line chart: one or more series drawn as connected lines over a shared
categorical x-axis and a numeric y-axis. Points are marked and interactive.

## Use it when

- Your x is **ordered categories or time** (months, days, steps, versions) and
  your y is a **continuous number**.
- You want to show a **trend** or **compare a few series** over the same x.
- Rows look like: `label -> value` (one column) or `label -> value_a, value_b`
  (several series sharing one x).

Do **not** use it for: part-to-whole (use pie/donut), distributions (histogram),
or x/y correlation with no shared x ordering (use scatter). See
[`CHARTS.md`](../../CHARTS.md).

## Data shape

- `xAxis.categories`: the x labels, length `N`.
- each `series[].data`: `N` numbers, aligned to `categories` by index.

## Spec fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | must be `"line"` |
| `title` | string | — | top title |
| `subtitle` | string | — | under the title |
| `width` / `height` | int | 820 / 460 | px |
| `legend` | bool | true | bottom legend + click-to-toggle |
| `xAxis.title` | string | — | axis label |
| `xAxis.categories` | string[] | index `0..N-1` | x labels |
| `yAxis.title` | string | — | axis label |
| `yAxis.min` / `yAxis.max` | number | auto (nice ticks, includes 0) | clamp the y range |
| `series[].name` | string | `Series i` | legend + tooltip name |
| `series[].data` | number[] | — | y-values, length `N` |
| `series[].color` | string | palette by index | hex, e.g. `#2f7ed8` |

Full schema: [`spec/chart-spec.schema.json`](../../spec/chart-spec.schema.json).

## Example spec

See [`examples/basic.json`](examples/basic.json):

```json
{
  "type": "line",
  "title": "Monthly Average Temperature",
  "xAxis": { "title": "Month", "categories": ["Jan", "Feb", "Mar"] },
  "yAxis": { "title": "Temperature (°C)" },
  "series": [
    { "name": "Tokyo",  "data": [7.0, 6.9, 9.5] },
    { "name": "London", "data": [3.9, 4.2, 5.7] }
  ]
}
```

## Generate it

**Python — from a dict/JSON spec:**
```python
import json
from peakcharts import ChartSpec, save_html

spec = ChartSpec.from_dict(json.load(open("charts/line-basic/examples/basic.json")))
save_html(spec, "out.html")
```

**Python — typed:**
```python
from peakcharts import Axis, ChartSpec, Series, save_html
save_html(ChartSpec(
    title="Monthly Average Temperature",
    x_axis=Axis(title="Month", categories=["Jan", "Feb", "Mar"]),
    y_axis=Axis(title="Temperature (°C)"),
    series=[Series("Tokyo", [7.0, 6.9, 9.5]), Series("London", [3.9, 4.2, 5.7])],
), "out.html")
```

**Go —** _(pending; same spec, same output)._

## Output & interactivity

A self-contained interactive HTML file: inline SVG + CSS + the shared runtime.
- **Hover a point** → tooltip (x, series, y) + point highlight + crosshair.
- **Click a legend item** → toggle that series on/off.
- Renders fully (static) even with JavaScript disabled.

## Rendering notes

- Y-axis uses "nice numbers" ticks (~6) and always includes 0 as a baseline
  unless `yAxis.min/max` clamp it.
- Colors cycle the palette in `charts/line.py` when `series[].color` is unset.

## Not yet supported (roadmap)

- `[x, y]` numeric point pairs (only category-aligned y-values today)
- Log y-axis, dual y-axis, missing/`null` points (gaps)
- Spline (smoothed) variant → will be its own chart id `line-spline`
