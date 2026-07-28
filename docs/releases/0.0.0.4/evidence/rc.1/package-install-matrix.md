---
id: SC-REL-025
title: StoneCharts 0.0.0.4 Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.4
requirements: [REQ-CHART-003]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-28"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# Package Install Matrix

This matrix records the `0.0.0.4` release-candidate installation and execution
posture, proven fresh on this candidate commit. Every row here specifically
exercises `bubble`, the chart type this release adds.

| Surface | Command | Result | Notes |
|---|---|---|---|
| Python source package | `python -m pytest libs/python/tests -q` | PASS (30 tests) | Includes `test_bubble_goldens` and `test_bubble_edge_cases`. |
| Go source module | `cd libs/go && go test ./...` | PASS | Includes bubble in `TestGolden`, plus `TestBubbleEdgeCases`. |
| Controlled docs | `python tools/check_docs.py` | PASS | 79 documents, 23 evidence definitions, 50 project items. |
| Release evidence manifest | `python tools/check_release_evidence.py --manifest docs/releases/0.0.0.4/evidence/rc.1/manifest.json` | PASS | Confirms this candidate pack and its recorded hashes. |
| Python wheel install (3.14, local) | `python -m build --wheel --outdir dist libs/python` (produces `stonecharts-0.0.0.4-py3-none-any.whl`), fresh-venv install, then `import stonecharts; assert stonecharts.__version__ == "0.0.0.4"` and render a `bubble` chart via the typed `ChartSpec(series=[Series(data=[[x,y,z],...])])` constructor | PASS | Installed copy resolved from `site-packages`, not the source tree; rendered `bubble` successfully from the installed wheel, exercising the `ChartSpec.__post_init__` point-model backfill extended for `z`. |
| Python wheel install (3.9) | CI job `python-wheel-install` (matrix: 3.9, 3.14) in `.github/workflows/quality.yml`, updated to install `stonecharts-0.0.0.4-py3-none-any.whl` and assert the bubble render path | PASS in CI | 3.9 is not installed on this local machine; qualified via the same build-install-smoke-test sequence in GitHub Actions. |
| Go module consumption | Separate consumer module (`go.mod` with `replace stonecharts => <path to libs/go>`); `go mod tidy && go run .` rendering a `bubble` `ChartSpec` built with `Series.DataPoints` and `Datum.Z` set directly | PASS | Confirms the module builds and executes `bubble` when imported as a dependency by an external module. No git tag exists for the Go module (unchanged posture from prior releases; ADR 0007). |
