# PeakCharts

An original, proprietary charting library. One shared chart-spec model, a
standalone renderer per language, and a shared interaction runtime — so the same
chart "recipe" produces the same interactive chart in Python, Go, and beyond.

**Not** a fork or copy of any commercial charting library. The chart-type catalog
is inspired by common visualization types (line, bar, pie, scatter, heatmap, …);
every renderer here is written from scratch. All rights reserved.

## What a chart is here

1. A **spec** — a language-agnostic recipe (type, data, axes, titles, colors).
   Schema: [`spec/chart-spec.schema.json`](spec/chart-spec.schema.json).
2. A **renderer** per language turns the spec into an **SVG** that follows
   [`spec/svg-contract.md`](spec/svg-contract.md).
3. The shared **interaction runtime**
   ([`runtime/chart-interactions.js`](runtime/chart-interactions.js)) enhances that
   SVG (tooltip, point highlight, legend toggle, crosshair). Output is a single,
   self-contained interactive HTML file.

## Repo layout

```
spec/          shared spec schema + the SVG DOM contract
runtime/       the shared vanilla-JS interaction runtime (written once)
charts/<id>/   per-chart docs: design.md, examples/, golden/
libs/python/   Python renderer (peakcharts package)
libs/go/       Go renderer (next)
CHARTS.md      the "smart" router: data + intent -> which chart + its design.md
```

Every new chart type = one `charts/<id>/` folder (with its `design.md`) plus a
renderer in each `libs/<lang>`. See any chart's `design.md` to generate it.

## Quickstart (Python)

```bash
cd libs/python
python examples/line_basic.py       # writes examples/line_basic.out.html
```

```python
from peakcharts import Axis, ChartSpec, Series, save_html

spec = ChartSpec(
    title="Monthly Average Temperature",
    x_axis=Axis(categories=["Jan", "Feb", "Mar"]),
    series=[Series(name="Tokyo", data=[7.0, 6.9, 9.5])],
)
save_html(spec, "chart.html")   # self-contained interactive HTML
```

## Status

| Chart | Spec | Python | Go | Interactivity |
|-------|------|--------|----|----|
| Basic line (`line-basic`) | ✅ | ✅ | ⏳ | tooltip · highlight · legend toggle · crosshair |

Roadmap: replicate the common chart-type catalog one type at a time (bar/column,
area, pie, scatter, bubble, heatmap, gauge, …), each with its own `design.md`.

## License

**Proprietary** — Copyright © 2026 Dharmik Shingala. **All rights reserved.**
No use, copying, modification, or distribution without prior written permission.
See [LICENSE](LICENSE).
