---
id: SC-REL-008
title: StoneCharts 0.0.0.1 Candidate Evidence Checklist
status: proposed
classification: normative
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

# 0.0.0.1 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `4734f310c31229b171edafbaadea937f80aac243`
- Generated at: `2026-07-23T23:17:37+05:30`

This pack records the governed release evidence state that is currently available in the repo.
It is not a publication approval.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass.
- [x] Shared validation parity and capability coverage pass.
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual profile, performance, direct cross-render, and fuzz/property evidence are attached.
- [x] Release evidence validator is present.
- [x] SBOM generation and validation.
- [x] Provenance statement.
- [x] Package install matrix: Python wheel install (3.14 local, 3.9 in CI) and Go module consumption via local `replace` both proven.

## Still open before S3

- [ ] Release tag and publication.
- [ ] Public support channel sign-off.
