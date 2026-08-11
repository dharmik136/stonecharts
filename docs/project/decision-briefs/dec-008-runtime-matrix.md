---
id: SC-OPS-007
title: StoneCharts DEC-008 Runtime Matrix Decision Brief
status: accepted
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-RUNTIME-001, REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-008 Runtime Matrix Decision Brief

## Decision question

What is the supported runtime and platform matrix for `0.0.0.1`?

## Recommendation

Approve the narrow matrix recorded in the supported-runtime document:

1. Python 3.9 and 3.14 are the only supported Python versions.
2. Go 1.26 is the only supported Go version.
3. Chromium on the pinned desktop Linux qualification profile is the only supported
   browser runtime.
4. No certified exporter profile is promised for `0.0.0.1`.

This keeps support claims aligned with the evidence already present in CI and the
release plan. It does not imply support for broader browser or platform families than
the repo has actually qualified.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Approve the narrow evidence-backed matrix | Support claims stay bounded to what CI and release evidence prove | Best fit for 0.0.0.1 qualification |
| Broaden support to additional browsers or OS profiles | More users appear covered without more evidence | Creates claims the release cannot currently defend |
| Leave the matrix undefined | Each consumer infers support ad hoc | Makes qualification and support policy ambiguous |

## Stakeholder impact

- Product: support claims stay honest and auditable.
- Engineering: implementation and testing focus on the profiles that matter first.
- QA and compliance: have a single matrix to verify against release evidence.
- Users: know which runtime combinations are actually supported.

## Agent review

The panel did not reach unanimous approval.

- One agent approved the narrow runtime/browser boundary.
- One agent rejected the draft because DEC-008 also covers exporter profiles and the
  draft explicitly left export certification undefined.
- The reviewer said the runtime/browser/toolchain part is consistent, but the exporter
  profile is still the missing piece for end-to-end qualification.

## Outcome

DEC-008 is approved and recorded in the governed register with the host-font visual
profile as the companion visual baseline.

## Approve or reject

Approved.
