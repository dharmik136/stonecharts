---
id: SC-REL-008
title: StoneCharts 0.0.0.1 Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-24"
review_due: "2026-08-24"
supersedes: null
superseded_by: null
---

# 0.0.0.1 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `da9f7004774fa5dc5a42618df01d018a5e989fa3`
- Generated at: `2026-07-24T22:30:52+05:30`

This pack records the governed release evidence state that is currently available in the repo.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass.
- [x] Shared validation parity and capability coverage pass.
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual profile, performance, direct cross-render, and fuzz/property evidence are attached.
- [x] Release evidence validator is present.
- [x] SBOM generation and validation.
- [x] Provenance statement.
- [x] Package install matrix: Python wheel install (3.14 local, 3.9 in CI) and Go module consumption via local `replace` both proven.

## GATE-S4 sign-off

Product-owner and maintainer approval for tagging `0.0.0.1` on the qualified commit
above is recorded here (`review_mode: self` - both roles are held by dharmik136; this is
not an independent audit). Scope of this authorization, per DEC-011 and the commercial
terms policy (`SC-CON-020`): create and push the source-control tag on the qualified
commit only. No repository visibility change, package-registry upload, or Go module tag
is authorized by this sign-off - those remain separately gated (Go module publication
additionally requires an ecosystem-mapping decision that does not yet exist, per
ADR 0007).

## Still open before further publication

- [ ] Repository visibility / public distribution decision (not authorized yet).
- [ ] Go module ecosystem-mapping decision (required before any Go tag; ADR 0007).
- [ ] Public support channel sign-off.
