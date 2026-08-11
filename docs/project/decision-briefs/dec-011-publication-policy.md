---
id: SC-OPS-015
title: StoneCharts DEC-011 Publication Decision Brief
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001, REQ-SEC-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-011 Publication Decision Brief

## Decision question

When and where are packages and source made public?

## Recommendation

Approve a private-until-S3 publication policy:

1. Keep the repository and registries private until the S3 evidence pack is complete.
2. Publish only through supportable channels recorded in the release plan and supply-chain policy.
3. Require explicit ownership and rollback information for each publication path.

This matches the current release posture and keeps publication honest about provenance,
support, and rollback.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Keep publication private until S3 | No public source or package release before evidence is sealed | Best fit for current release posture |
| Publish earlier | Broader visibility sooner | Undermines evidence and provenance discipline |
| Leave publication undefined | Ad hoc release timing and channels | Ambiguous support and rollback responsibility |

## Stakeholder impact

- Product: no premature public promise.
- Engineering: release work stays tied to evidence.
- QA and compliance: can audit the publication boundary.
- Users: know when the project becomes public and which paths are official.

## Agent review

The panel agreed that the boundary is correct and that the remaining task is to name
the exact supported publication channels when the release record is assembled.

## Outcome

DEC-011 is approved as a private-until-S3 publication policy.

