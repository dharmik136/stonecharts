---
id: SC-OPS-016
title: StoneCharts DEC-012 Name-Clearance Decision Brief
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PROD-001, REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# DEC-012 Name-Clearance Decision Brief

## Decision question

Is the StoneCharts name cleared for public commercial use?

## Recommendation

Adopt the name-clearance policy:

1. Do not treat the name as cleared until a dated clearance record is completed and
   reviewed.
2. Require repository, package-index, domain, company-name, and trademark searches.
3. Require explicit jurisdiction and legal-review boundaries.
4. Treat technical namespace adoption as separate from legal clearance.

This is the honest boundary for the current repo state. It prevents public branding
claims from outrunning the documented diligence process.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Require a dated clearance record | Brand claims stay blocked until due diligence is complete | Best fit for current state |
| Assume the name is clear | Proceed without recorded diligence | Not defensible |
| Leave name clearance undefined | Each publication decides ad hoc | Creates legal and product ambiguity |

## Stakeholder impact

- Product: avoids premature public branding claims.
- Engineering: can keep the technical namespace without implying legal clearance.
- QA and compliance: know the exact evidence required before branding changes.
- Users and partners: do not receive an overconfident commercial claim.

## Agent review

The panel agreed the policy is the right boundary and noted that the actual dated
clearance record is still missing.

## Outcome

DEC-012 is approved as a name-clearance policy, not a clearance claim.
