---
id: SC-REQ-001
title: StoneCharts Requirements and Traceability Guide
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: all
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Requirements and Traceability

[`registry.yaml`](registry.yaml) is the authoritative requirements source. Product
narratives, contracts, ADRs, code paths, tests, risks, and release targets link through
stable IDs in that registry. A separate hand-maintained PRD and software requirements
document would duplicate the same obligations and is intentionally avoided.

The documentation validator checks every reference and can produce a deterministic
machine-readable traceability snapshot:

```powershell
python tools/check_docs.py --traceability-json build/traceability.json
```

The generated snapshot contains document status, requirement sources, ADRs, contracts,
verification implementation status, code paths, and linked risks. It is a build or
release artifact, not a second source of truth.

## Requirement lifecycle

1. `proposed`: acceptance and impact are reviewable.
2. `approved`: product obligation is authorized for its target.
3. `implemented`: code exists but qualification may be incomplete.
4. `verified`: required release evidence passed for the target artifact.
5. `deferred` or `rejected`: not part of the active target, with rationale retained in
   Git history or a decision record.

A `must` requirement cannot be approved without acceptance criteria and at least one
verification ID. It cannot be marked verified from a planned or partial evidence
definition; the immutable release result must pass.

