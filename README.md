# StoneCharts

An original, proprietary charting library. One shared chart-spec model, a
standalone renderer per language, and a shared interaction runtime — so the same
chart "recipe" produces the same interactive chart in Python, Go, and beyond.

StoneCharts is currently entering a governed Alpha qualification phase. Product scope,
guarantees, requirements, architecture decisions, risks, evidence, and release gates
are indexed in [`docs/README.md`](docs/README.md).

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
   SVG (tooltip, point highlight, legend toggle, crosshair, keyboard navigation)
   and layers on accessibility (a concise screen-reader summary plus a
   navigable data table). Output is a single, self-contained interactive HTML file.

## Repo layout

```
spec/          shared spec schema + the SVG DOM contract
runtime/       the shared vanilla-JS interaction runtime (written once)
charts/<id>/   per-chart docs: design.md, examples/, golden/
libs/python/   Python renderer (stonecharts package)
libs/go/       Go renderer
CHARTS.md      the "smart" router: data + intent -> which chart + its design.md
```

Every new chart type = one `charts/<id>/` folder (with its `design.md`) plus a
renderer in each `libs/<lang>`. See any chart's `design.md` to generate it.

## Guarantees & limitations

StoneCharts generates deterministic static SVG without a browser runtime for
supported chart specifications. Go and Python outputs are byte-identical for
covered fixtures. Canonical output, browser behavior, visual export, and
customization have separate applicability boundaries in the governed
[`guarantees and limits`](docs/contracts/guarantees-and-limits.md).

- **Deterministic & runtime-free rendering.** The SVG is fully drawn server-side —
  no browser or JS needed to produce it; the runtime only *enhances* an
  already-complete chart.
- **Cross-language byte parity** is verified per fixture by the golden tests in
  both languages; it is a guarantee for *covered* specs, not an untested claim for
  every possible input (see [`docs/robustness.md`](docs/robustness.md)).
- **Interactivity & accessibility are optional layers.** Disable the a11y layer
  with `a11y: false`; the interactive HTML is one self-contained file.
- **Export is out of scope of the core.** PDF/PNG/email delivery is a downstream
  concern — convert or rasterize the SVG with the tool of your choice.

## Quickstart (Python)

```bash
cd libs/python
python examples/line_basic.py       # writes examples/line_basic.out.html
```

```python
from stonecharts import Axis, ChartSpec, Series, save_html

spec = ChartSpec(
    title="Monthly Average Temperature",
    x_axis=Axis(categories=["Jan", "Feb", "Mar"]),
    series=[Series(name="Tokyo", data=[7.0, 6.9, 9.5])],
)
save_html(spec, "chart.html")   # self-contained interactive HTML
```

## Quickstart (Go)

```bash
cd libs/go
go test ./...                                              # golden test vs the shared reference
go run ./cmd/line_basic ../../charts/line-basic/examples/basic.json out.svg out.html
```

```go
import "stonecharts"

spec, _ := stonecharts.FromJSON(specJSON)   // matches spec/chart-spec.schema.json
stonecharts.SaveHTML(spec, "chart.html", "")
```

## Status

| Chart | Spec | Python | Go | Interactivity |
|-------|------|--------|----|----|
| Basic line (`line-basic`) | ✅ | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Column (`column`) | qualification pending | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |

Python and Go render **byte-identical SVG** from the same spec, pinned by golden
tests (`libs/go/render_test.go`, `libs/python/tests/test_golden.py`).

The active Alpha scope is line and column. Other chart designs remain roadmap
material until the schema, capability, conformance, packaging, and release gates
for each type are complete.

## License

**Proprietary** — Copyright © 2026 Dharmik Shingala. **All rights reserved.**
No use, copying, modification, or distribution without prior written permission.
See [LICENSE](LICENSE).
