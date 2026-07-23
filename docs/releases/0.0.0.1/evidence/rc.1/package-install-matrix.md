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
| Python wheel install | pending | not run | Release artifact packaging has not been qualified yet. |
| Go release module install | pending | not run | Release-tagged module publication has not been qualified yet. |
