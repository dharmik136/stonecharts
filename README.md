# StoneCharts

StoneCharts is Visual Integrity Infrastructure for deterministic reporting charts:
one governed chart specification, certified Python and Go renderers, and evidence
that supported visuals stay consistent across language and release boundaries.

StoneCharts is currently entering a governed Alpha qualification phase. Product scope,
guarantees, requirements, architecture decisions, risks, evidence, and release gates
are indexed in [`docs/README.md`](docs/README.md). Execution is tracked in the private
[StoneCharts GitHub Project](https://github.com/users/dharmik136/projects/2).

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

## StoneVerify Proof

The primary Visual Integrity proof compares a candidate render against an
approved local evidence bundle:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --evidence .tmp-stoneverify-baseline
```

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --baseline-evidence .tmp-stoneverify-baseline \
  --baseline-note "approved baseline for release review" \
  --evidence .tmp-stoneverify-candidate
```

When `--baseline-evidence` is supplied and no runtime is specified, StoneVerify
defaults to one Python render. Use explicit repeated `--runtime` flags for a
cross-runtime proof:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --from-source \
  --evidence .tmp-stoneverify-bubble
```

It writes `manifest.json`, `input-spec.json`, runtime SVG outputs,
`comparison.json`, `report.html`, and `checksums.txt`. This is a local
conformance proof, not hosted storage or a PDF/document-generation system.

To demonstrate a CI failure without corrupting a renderer, apply an explicit
demo-only drift to the last runtime output:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --from-source \
  --demo-drift text \
  --evidence .tmp-stoneverify-drift
```

To record that a new approved baseline replaces an older one:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --baseline-evidence .tmp-stoneverify-baseline \
  --supersedes-baseline .tmp-stoneverify-older-baseline \
  --baseline-note "replaces baseline after dependency upgrade review" \
  --evidence .tmp-stoneverify-candidate
```

To validate that an existing evidence bundle still matches its recorded checksums:

```bash
python tools/stonecharts_verify.py --check-evidence .tmp-stoneverify-bubble
```

To compare two stored evidence bundles directly:

```bash
python tools/stonecharts_verify.py --compare-evidence .tmp-stoneverify-bubble .tmp-stoneverify-baseline-check
```

The comparison reports each runtime separately, and it separates a changed input
spec from a changed rendering of the same spec. Only the second is renderer drift:

```text
StoneVerify compare FAIL: Evidence bundles differ: the same input spec produced different output.
input spec: match
  go: FAIL - same input spec rendered differently: attribute, numeric formatting, ordering, or text-content drift
  python: PASS - hash match
```

Bundles that cover different runtimes are reported as a mismatch rather than
compared on the runtimes they happen to share.

To write that comparison to a reviewable HTML report:

```bash
python tools/stonecharts_verify.py \
  --compare-evidence .tmp-stoneverify-bubble .tmp-stoneverify-baseline-drift \
  --compare-report .tmp-stoneverify-compare/report.html
```

For CI systems that ingest test reports, add a JUnit XML report:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --from-source \
  --demo-drift text \
  --evidence .tmp-stoneverify-drift \
  --junit-report .tmp-stoneverify-drift/junit.xml
```

The XML report has one testcase per compared runtime pair, or one testcase per
runtime in baseline mode. A passing comparison writes zero failures; a failing
comparison writes failure text from StoneVerify's semantic findings. The XML
does not decide job status by itself: StoneVerify's exit code remains the source
of pass/fail behavior.

When `GITHUB_ACTIONS=true`, StoneVerify also emits GitHub workflow annotations
and appends a concise job summary if `GITHUB_STEP_SUMMARY` is available. This
happens without requiring `--junit-report`.

StoneVerify uses stable exit codes for automation:

| Code | Meaning |
|------|---------|
| 0 | Verification completed and passed. |
| 1 | Verification completed, but differences or invalid evidence were found. |
| 2 | CLI usage error, such as missing required arguments. |
| 3 | Invalid or unsupported chart specification. |
| 4 | Renderer or adapter execution failure. |
| 5 | Reserved for resource-limit or timeout failure. |
| 70 | Reserved for internal StoneVerify failure. |

When installed from the Python wheel, StoneVerify is available as `stoneverify`.
For `--runtime go`, it invokes a prebuilt `stoneverify-go-render` adapter
resolved from `--go-binary`, `STONEVERIFY_GO_BINARY`, or `PATH`. The adapter
contract is intentionally small: `stoneverify-go-render <spec.json>` writes SVG
to stdout, `stoneverify-go-render --version` reports `adapter=`,
`stonecharts=`, and `module=` fields, and failures write stderr with a non-zero
exit. `--from-source` is only the development fallback for running against this
checkout with `go run`.

## Status

| Chart | Spec | Python | Go | Interactivity |
|-------|------|--------|----|----|
| Basic line (`line-basic`) | ✅ certified (0.0.0.1) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Column (`column`) | ✅ certified (0.0.0.1) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Area (`area`) | ✅ certified (0.0.0.1) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Bar (`bar`) | ✅ certified (0.0.0.2) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Scatter (`scatter`) | ✅ certified (0.0.0.3) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Bubble (`bubble`) | ✅ certified (0.0.0.4) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |
| Combo (`combo`) | ✅ certified (0.0.0.5) | ✅ | ✅ | tooltip · highlight · legend toggle · crosshair |

Python and Go render **byte-identical SVG** from the same spec, pinned by golden
tests (`libs/go/render_test.go`, `libs/python/tests/test_golden.py`).

The released scope is line, column, and area (0.0.0.1), bar (0.0.0.2), scatter
(0.0.0.3), bubble (0.0.0.4), and combo (0.0.0.5). See
[`docs/product/capability-matrix.md`](docs/product/capability-matrix.md) for the
authoritative distinction between certified technical capability, commercial pilot
scope, and design-only roadmap material.

## License

**Proprietary** — Copyright © 2026 Dharmik Shingala. **All rights reserved.**
No use, copying, modification, or distribution without prior written permission.
See [LICENSE](LICENSE).
