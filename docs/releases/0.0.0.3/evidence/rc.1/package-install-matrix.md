---
id: SC-REL-021
title: StoneCharts 0.0.0.3 Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.3
requirements: [REQ-CHART-002]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-27"
review_due: "2026-08-27"
supersedes: null
superseded_by: null
---

# Package Install Matrix

This matrix records the `0.0.0.3` release-candidate installation and execution
posture, proven fresh on this candidate commit. Every row here specifically
exercises `scatter`, the chart type this release adds, including both the
`from_dict`/`FromJSON` path and the typed-construction path whose point-model gap
was found and fixed during `GATE-S9`.

| Surface | Command | Result | Notes |
|---|---|---|---|
| Python source package | `python -m pytest libs/python/tests -q` | PASS (28 tests) | Includes `test_scatter_goldens` and `test_scatter_edge_cases`. |
| Go source module | `cd libs/go && go test ./...` | PASS | Includes scatter in `TestGolden`, plus `TestScatterEdgeCases`. |
| Controlled docs | `python tools/check_docs.py` | PASS | 75 documents, 21 evidence definitions, 45 project items. |
| Release evidence manifest | `python tools/check_release_evidence.py --manifest docs/releases/0.0.0.3/evidence/rc.1/manifest.json` | PASS | Confirms this candidate pack and its recorded hashes. |
| Python wheel install (3.14, local) | `python -m build --wheel --outdir dist libs/python` (produces `stonecharts-0.0.0.3-py3-none-any.whl`), fresh-venv install, then `import stonecharts; assert stonecharts.__version__ == "0.0.0.3"` and render a `scatter` chart via the typed `ChartSpec(series=[Series(data=[[x,y],...])])` constructor | PASS | Installed copy resolved from `site-packages`, not the source tree; rendered `scatter` successfully from the installed wheel, exercising the `ChartSpec.__post_init__` point-model backfill. |
| Python wheel install (3.9) | CI job `python-wheel-install` (matrix: 3.9, 3.14) in `.github/workflows/quality.yml`, updated to install `stonecharts-0.0.0.3-py3-none-any.whl` and assert the scatter render path | PASS in CI | 3.9 is not installed on this local machine; qualified via the same build-install-smoke-test sequence in GitHub Actions. |
| Go module consumption | Separate consumer module (`go.mod` with `replace stonecharts => <path to libs/go>`); `go mod tidy && go run .` rendering a `scatter` `ChartSpec` built with `Series.DataPoints` set directly | PASS | Confirms the module builds and executes `scatter` when imported as a dependency by an external module. No git tag exists for the Go module (unchanged posture from `0.0.0.1`/`0.0.0.2`; ADR 0007). |
