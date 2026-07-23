---
id: SC-OPS-006
title: StoneCharts DEC-005 Compatibility Decision Brief
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: [REQ-PROD-001, REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# DEC-005 Compatibility Decision Brief

## Decision question

What compatibility promise begins at `0.0.0.1`?

## Recommendation

Approve a two-phase policy:

1. `0.0.0.1` remains a governed pre-release baseline, so documented breaks are allowed
   while qualification work is still active.
2. After `0.0.0.1`, any public schema, API, DOM, golden, or release-artifact change
   requires a migration note, deprecation window where feasible, traceability updates,
   and review evidence.

This matches the current release posture and keeps the first release honest: the team
can still fix contract errors now without pretending the public surface is frozen.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Accept pre-release breaks only before `0.0.0.1` | Free to correct contract mistakes during qualification, with explicit documentation | Best fit for the current stage; preserves release honesty |
| Freeze compatibility from `0.0.0.1` onward | Treat the first release like a stable API boundary | Too rigid for the current qualification state and likely to preserve early defects |
| Leave compatibility undefined | Decide case by case with no written policy | Creates ambiguity for users, agents, and future releases |

## Stakeholder impact

- Product: gets a clear line between pre-release flexibility and release-era promises.
- Engineering: can still fix correctness issues before release without rewriting the
  release process each time.
- QA and compliance: get an explicit review checklist for future public changes.
- Users: know when to expect stable migration behavior and when the product is still
  maturing.

## Agent review

Three internal agents reviewed the recommendation. All three answered YES.

- The policy matches the current governed pre-release posture.
- The policy does not pretend `0.0.0.1` is already frozen.
- The wording is broad enough to cover schema, API, DOM, golden, and release-artifact
  changes without changing the release boundary.

## Approve or reject

Approve the recommended two-phase policy or replace it with a stricter release boundary
before `DEC-005` is moved to resolved.

## Outcome

DEC-005 is approved and recorded as a resolved decision in the governed register.
