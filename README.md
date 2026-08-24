# StoneCharts

[![CI](https://github.com/dharmik136/stonecharts/actions/workflows/quality.yml/badge.svg)](https://github.com/dharmik136/stonecharts/actions/workflows/quality.yml)
![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red)
![Python ≥3.9](https://img.shields.io/badge/python-%E2%89%A53.9-3776AB)
![Go ≥1.26](https://img.shields.io/badge/go-%E2%89%A51.26-00ADD8)
![Charts: 36](https://img.shields.io/badge/chart_types-36-28a745)
![Dependencies: 0](https://img.shields.io/badge/runtime_deps-0-brightgreen)

**Visual Integrity Infrastructure** for deterministic reporting charts — one governed
JSON specification, certified Python and Go renderers producing byte-identical SVG,
and formal conformance proofs that every visual stays consistent across language,
release, and environment boundaries.

> **Not** a fork or copy of any commercial charting library. Every renderer is written
> from scratch. All rights reserved.

---

## Why StoneCharts

- **Byte-identical cross-language output.** The same JSON spec renders to the exact
  same SVG in Python and Go — verified by 177 golden-test fixtures across 36 chart
  types (7 certified, 9 candidate, 20 experimental).
- **Deterministic and runtime-free.** Charts are fully rendered server-side without a
  browser, DOM, or JavaScript. The SVG is complete on its own; the interaction runtime
  only *enhances* it.
- **Zero runtime dependencies.** Both the Python package and Go module ship with zero
  runtime dependencies.
- **Formal conformance proofs.** [StoneVerify](#stoneverify) produces local evidence
  bundles proving visual integrity between releases — auditable artifacts, not just
  test assertions.
- **Governed engineering.** 48 formal decisions, requirements traceability, evidence
  packs, and a [12-job CI pipeline](#ci). Every chart type is admitted through a
  governed process with its own decision record.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Chart Spec (JSON)                                  │
│  spec/chart-spec.schema.json                        │
├──────────────────────┬──────────────────────────────┤
│  Python Renderer     │  Go Renderer                 │
│  libs/python/        │  libs/go/                    │
├──────────────────────┴──────────────────────────────┤
│              Deterministic SVG                      │
│              (byte-identical across languages)      │
├─────────────────────────────────────────────────────┤
│  Interaction Runtime (optional enhancement)         │
│  runtime/chart-interactions.js                      │
│  Tooltip · Crosshair · Legend toggle · Keyboard nav │
│  Screen-reader summary · Navigable data table       │
├─────────────────────────────────────────────────────┤
│         Self-contained interactive HTML              │
└─────────────────────────────────────────────────────┘
```

1. A **spec** — a language-agnostic JSON recipe (type, data, axes, titles, colors).
   Schema: [`spec/chart-spec.schema.json`](spec/chart-spec.schema.json).
2. A **renderer** per language turns the spec into an **SVG** that follows the
   [SVG DOM contract](spec/svg-contract.md).
3. The shared **interaction runtime**
   ([`runtime/chart-interactions.js`](runtime/chart-interactions.js)) enhances that
   SVG with tooltip, crosshair, legend toggle, keyboard navigation, and accessibility
   (screen-reader summary + navigable data table). Output is a single, self-contained
   interactive HTML file.

## Requirements

| Dependency | Version |
|------------|---------|
| Python     | ≥ 3.9   |
| Go         | ≥ 1.26  |
| Browser (for interactive HTML) | Any modern browser |

Both renderers have **zero runtime dependencies**. Dev/test dependencies are listed
in [`pyproject.toml`](libs/python/pyproject.toml) and [`go.mod`](libs/go/go.mod).

## Quickstart

### Python

```bash
cd libs/python
pip install -e .
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

### Go

```bash
cd libs/go
go test ./...                                              # golden test vs shared reference
go run ./cmd/line_basic ../../charts/line-basic/examples/basic.json out.svg out.html
```

```go
import "stonecharts"

spec, _ := stonecharts.FromJSON(specJSON)   // matches spec/chart-spec.schema.json
stonecharts.SaveHTML(spec, "chart.html", "")
```

## Chart Catalog

**36 chart types**, all certified with byte-identical Python and Go renderers pinned
by golden tests.

| Tier | Count | Meaning |
|------|-------|---------|
| **Certified** | 36 | Passes all SC-CERT gates; commercially supported |
| **Candidate** | 0 | No chart types are awaiting certification |
| **Experimental** | 0 | No chart types are outside the certified tier |

### Certified (36 types)

| Chart | ID | Release |
|-------|----|---------|
| Line | `line` | 0.0.0.1 |
| Column | `column` | 0.0.0.1 |
| Area | `area` | 0.0.0.3 |
| Bar | `bar` | 0.0.0.2 |
| Scatter | `scatter` | 0.0.0.3 |
| Bubble | `bubble` | 0.0.0.4 |
| Combo | `combo` | 0.0.0.5 |
| Histogram | `histogram` | 0.0.0.6 |
| Error Bar | `error-bar` | 0.0.0.8 |
| Area Range | `arearange` | 0.0.0.9 |
| Column Range | `columnrange` | 0.0.0.9 |
| Waterfall | `waterfall` | 0.0.0.10 |
| Bullet | `bullet` | 0.0.0.11 |
| Boxplot | `boxplot` | 0.0.0.12 |
| Dumbbell | `dumbbell` | 0.0.0.14 |
| Development Triangle | `development-triangle` | 0.0.0.33 |
| Candlestick | `candlestick` | 0.0.0.7 |
| Lollipop | `lollipop` | 0.0.0.13 |
| Funnel | `funnel` | 0.0.0.15 |
| Variwide | `variwide` | 0.0.0.16 |
| Timeline | `timeline` | 0.0.0.17 |
| Windbarb | `windbarb` | 0.0.0.18 |
| Streamgraph | `streamgraph` | 0.0.0.19 |
| Vector Plot | `vector-plot` | 0.0.0.20 |
| X-Range | `xrange` | 0.0.0.21 |
| Tech. Indicators | `technical-indicators` | 0.0.0.22 |
| Flame Chart | `flame-chart` | 0.0.0.23 |
| Pie | `pie` | 0.0.0.24 |
| Gauge | `gauge` | 0.0.0.25 |
| Solid Gauge | `solid-gauge` | 0.0.0.26 |
| Radar | `radar` | 0.0.0.27 |
| Polar | `polar` | 0.0.0.28 |
| Wind Rose | `wind-rose` | 0.0.0.29 |
| Nightingale | `nightingale` | 0.0.0.30 |
| Radial Bar | `radial-bar` | 0.0.0.31 |
| Parliament | `parliament` | 0.0.0.32 |

### Candidate (0 types)

No candidate chart types.

### Experimental (0 types)

No experimental chart types.

Every chart type has a `design.md`, example specs, and golden SVGs in
[`charts/<id>/`](charts/). See [`CHARTS.md`](CHARTS.md) to look up which chart type
fits a given data shape and intent.

## Guarantees and Limitations

StoneCharts generates deterministic static SVG for supported chart specifications.
Canonical output, browser behavior, visual export, and customization have separate
applicability boundaries documented in the
[guarantees and limits contract](docs/contracts/guarantees-and-limits.md).

- **Deterministic and runtime-free rendering.** The SVG is fully drawn server-side —
  no browser or JS needed to produce it; the runtime only *enhances* an
  already-complete chart.
- **Cross-language byte parity** is verified per fixture by golden tests in both
  languages; it is a guarantee for *covered* specs, not an untested claim for every
  possible input (see [`docs/robustness.md`](docs/robustness.md)).
- **Interactivity and accessibility are optional layers.** Disable the a11y layer
  with `a11y: false`; the interactive HTML is one self-contained file.
- **Export is out of scope of the core.** PDF/PNG/email delivery is a downstream
  concern — convert or rasterize the SVG with the tool of your choice.

## StoneVerify

StoneVerify is the conformance proof system: it renders a chart spec, compares the
output against an approved baseline, and produces a local evidence bundle proving
visual integrity.

```bash
# Create an approved baseline
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python --evidence .tmp-baseline

# Verify a candidate against the baseline
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --baseline-evidence .tmp-baseline --evidence .tmp-candidate

# Cross-language proof (Python + Go produce identical SVG)
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python --runtime go --from-source --evidence .tmp-proof
```

Each evidence bundle contains `manifest.json`, the input spec, rendered SVGs,
`comparison.json` with semantic difference classification, `report.html` for
reviewers, and `checksums.txt` for tamper detection.

Supports JUnit XML output, GitHub Actions annotations, baseline supersession
tracking, and stable exit codes for automation. See the full
[StoneVerify Quick Start](docs/quality/stoneverify-quickstart.md) for the complete
reference.

## Repo Layout

```
spec/            Shared JSON Schema + SVG DOM contract
runtime/         Shared vanilla-JS interaction runtime
charts/<id>/     Per-chart design.md, example specs, golden SVGs
libs/python/     Python renderer (stonecharts package)
libs/go/         Go renderer (stonecharts module)
docs/            Governance, architecture, contracts, quality, releases
tools/           Build, check, and verification scripts
site/            Gated demo site (Astro)
CHARTS.md        Data shape + intent → chart type router
CHANGELOG.md     Full release history
```

## Documentation

| Topic | Location |
|-------|----------|
| Documentation index | [`docs/README.md`](docs/README.md) |
| Product thesis | [`docs/product/thesis.md`](docs/product/thesis.md) |
| System architecture | [`docs/architecture/system-design.md`](docs/architecture/system-design.md) |
| Renderer constitution | [`docs/architecture/renderer-constitution.md`](docs/architecture/renderer-constitution.md) |
| Guarantees and limits | [`docs/contracts/guarantees-and-limits.md`](docs/contracts/guarantees-and-limits.md) |
| Capability matrix | [`docs/product/capability-matrix.md`](docs/product/capability-matrix.md) |
| Test strategy | [`docs/quality/test-strategy.md`](docs/quality/test-strategy.md) |
| StoneVerify quick start | [`docs/quality/stoneverify-quickstart.md`](docs/quality/stoneverify-quickstart.md) |
| Threat model | [`docs/security/threat-model.md`](docs/security/threat-model.md) |
| Decision log (48 decisions) | [`docs/project/decisions.md`](docs/project/decisions.md) |

Execution is tracked in the private
[StoneCharts GitHub Project](https://github.com/users/dharmik136/projects/2).

## CI

The [quality workflow](.github/workflows/quality.yml) runs on every push and pull
request with 12 jobs:

- **Lint and static analysis** — ruff, mypy, go vet, golangci-lint, CodeQL
- **Cross-platform tests** — Python 3.9 + 3.14, Go, on Ubuntu and Windows
- **Wheel install smoke test** — build, install, and verify all 36 chart types
- **Documentation validation** — structure, metadata, and cross-references
- **Cross-language parity** — Python/Go byte-identical output verification
- **Schema compatibility** — backward-compatibility check on PRs
- **StoneVerify pilot gate** — full conformance proof with artifact upload
- **Browser qualification** — Playwright interaction and accessibility tests

## Contributing

StoneCharts is proprietary software. Contributions are accepted only from authorized
collaborators under written terms. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Report vulnerabilities privately via GitHub's security advisory facility. See
[SECURITY.md](SECURITY.md) for scope and process.

## License

**Proprietary** — Copyright © 2026 Dharmik Shingala. **All rights reserved.**
No use, copying, modification, or distribution without prior written permission.
See [LICENSE](LICENSE).
