---
id: SC-REL-033
title: StoneCharts 0.0.0.33 Candidate Evidence Checklist
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.33
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# StoneCharts 0.0.0.33 release-candidate checklist

Candidate: `rc.1`  
Source commit: `5b66d35f7630b03f4abf21c27ed33f695cdbcbe3`  
Status: proposed; publication approval remains a separate gate.

## Automated evidence

- Python verification suite: `py -3 -m pytest libs/python/tests -q`
- Go verification suite: `go test ./...` from `libs/go`
- Browser qualification: `npm test`
- Documentation control: `py -3 tools/check_docs.py`
- Capability derivation: `py -3 tools/generate_capabilities.py --check`
- Release manifest integrity: `py -3 tools/check_release_evidence.py --manifest docs/releases/0.0.0.33/evidence/rc.1/manifest.json`

The candidate records the completed 36-chart certified portfolio, including the
development-triangle and the nine polar/radial chart types. It does not itself
approve publication or create a public tag.
