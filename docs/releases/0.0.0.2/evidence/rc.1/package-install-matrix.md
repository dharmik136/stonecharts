---
id: SC-REL-017
title: StoneCharts 0.0.0.2 Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# Package Install Matrix

This matrix records the `0.0.0.2` release-candidate installation and execution
posture, proven fresh on this candidate commit. Unlike `0.0.0.1`'s matrix, every row
here specifically exercises `bar`, the chart type this release adds.

| Surface | Command | Result | Notes |
|---|---|---|---|
| Python source package | `python -m pytest libs/python/tests -q` | PASS (26 tests) | Includes `test_bar_goldens` and `test_bar_edge_cases`. |
| Go source module | `cd libs/go && go test ./...` | PASS | Includes bar in `TestGolden`, plus `TestBarEdgeCases`. |
| Controlled docs | `python tools/check_docs.py` | PASS | 71 documents, 19 evidence definitions, 40 project items. |
| Release evidence manifest | `python tools/check_release_evidence.py --manifest docs/releases/0.0.0.2/evidence/rc.1/manifest.json` | PASS | Confirms this candidate pack and its recorded hashes. |
| Python wheel install (3.14, local) | `python -m build --wheel --outdir dist libs/python` (produces `stonecharts-0.0.0.2-py3-none-any.whl`), fresh-venv install, then `import stonecharts; assert stonecharts.__version__ == "0.0.0.2"` and render a `bar` chart | PASS | Installed copy resolved from `site-packages`, not the source tree; rendered `bar` successfully from the installed wheel. |
| Python wheel install (3.9) | CI job `python-wheel-install` (matrix: 3.9, 3.14) in `.github/workflows/quality.yml`, updated to install `stonecharts-0.0.0.2-py3-none-any.whl` and assert the bar render path | PASS in CI | 3.9 is not installed on this local machine; qualified via the same build-install-smoke-test sequence in GitHub Actions. |
| Go module consumption | Separate consumer module (`go.mod` with `replace stonecharts => <path to libs/go>`); `go mod tidy && go run .` rendering a `bar` `ChartSpec` | PASS | Confirms the module builds and executes `bar` when imported as a dependency by an external module. No git tag exists for the Go module (unchanged posture from `0.0.0.1`; ADR 0007). |
