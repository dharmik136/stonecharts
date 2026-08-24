---
id: SC-QUAL-036
title: StoneCharts complete chart certification matrix
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.33 and later
requirements: [REQ-CHART-001, REQ-DET-001, REQ-VAL-001, REQ-A11Y-001, REQ-REL-001]
evidence: [TEST-CERTIFICATION-MATRIX]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# Complete chart certification matrix

Every chart type uses the same SC-CERT evidence surface established by the seed
charts (`line`, `column`, `area`, `bar`, `scatter`, `bubble`, and `combo`). A chart
is certified only when its contract, fixtures, Python/Go parity, validation,
property, semantic, purity, accessibility, StoneVerify, and release evidence gates
are present and passing.

The machine-enforced inventory check is:

```text
py -3 tools/check_certification_matrix.py
```

The matrix intentionally checks both chart-specific evidence (design, examples,
goldens, invalid fixtures, and source references) and shared portfolio gates. The
full qualification commands remain the authority for execution results:

- `py -3 -m pytest libs/python/tests -q`
- `go test ./...` from `libs/go`
- `npm test`
- `py -3 tools/check_release_evidence.py --manifest docs/releases/0.0.0.33/evidence/rc.1/manifest.json`

No chart may be moved back to candidate or experimental solely by documentation
editing; any tier change must be generated from the canonical capability registry
after the matrix and release evidence are updated.
