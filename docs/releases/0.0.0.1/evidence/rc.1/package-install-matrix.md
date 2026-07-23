---
id: SC-REL-009
title: StoneCharts 0.0.0.1 Package Install Matrix
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-19"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Package Install Matrix

This matrix records the release-candidate installation and execution posture that is currently proven.
It does not claim S3 completeness.

| Surface | Command | Result | Notes |
|---|---|---|---|
| Python source package | `python -m pytest libs/python/tests -q` | PASS | Exercises the Python package directly from the current repo. |
| Go source module | `cd libs/go && go test ./...` | PASS | Exercises the Go module directly from the current repo. |
| Controlled docs | `python tools/check_docs.py` | PASS | Confirms governed document consistency. |
| Release evidence manifest | `python tools/check_release_evidence.py --manifest docs/releases/0.0.0.1/evidence/rc.1/manifest.json` | PASS | Confirms the candidate pack and its recorded hashes. |
| Python wheel install (3.14, local) | `python -m build --wheel --outdir dist libs/python` then fresh-venv install and import/render smoke test | PASS | Built a `py3-none-any` wheel, installed it into an isolated venv, confirmed the import resolves to site-packages (not the source tree), and rendered a chart from the installed copy. Confirmed no unapproved chart-type module (`bar`) is present in the built wheel. |
| Python wheel install (3.9) | CI job `python-wheel-install` (matrix: 3.9, 3.14) in `.github/workflows/quality.yml` | PASS in CI | 3.9 is not installed on this local machine; qualified via the same build-install-smoke-test sequence in GitHub Actions, which has clean access to the pinned interpreter version. |
| Go module consumption | Separate consumer module with a local `replace stonecharts => <path>` directive; `go mod tidy && go run .` | PASS | Confirms the module builds and executes when imported as a dependency by an external module, not just via its own package tests. No git tag exists yet (release publication is a separate, later gate per DEC-011), so this is local-path consumption, not a tagged-version fetch. |
