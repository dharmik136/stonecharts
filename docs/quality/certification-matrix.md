---
id: SC-QUAL-036
title: StoneCharts complete chart certification matrix
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.34 and later
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

The machine-readable source is
[`certification-ledger.json`](certification-ledger.json). It contains exactly 36 chart
records and eight named gates per record. Generate and verify it with:

```text
py -3 tools/generate_certification_ledger.py --generate --check
```

The executable matrix check is:

```text
py -3 tools/check_certification_matrix.py
```

The matrix checks the chart-specific fixtures and goldens directly; executes schema
and runtime validation; verifies renderer purity, named property cases, semantic
invariant IDs, real-browser fixtures, and certified dual-runtime baseline hashes;
then runs the focused Python, Go, browser, and direct-parity suites. The full release
qualification commands remain the authority for the complete repository:

- `py -3 -m pytest libs/python/tests -q`
- `go test ./...` from `libs/go`
- `npm test`
- `py -3 tools/generate_certification_baselines.py --check`
- `py -3 tools/check_release_evidence.py --manifest docs/releases/0.0.0.34/evidence/rc.1/manifest.json`

No chart may be moved back to candidate or experimental solely by documentation
editing; any tier change must be generated from the canonical capability registry
after the matrix and release evidence are updated.
