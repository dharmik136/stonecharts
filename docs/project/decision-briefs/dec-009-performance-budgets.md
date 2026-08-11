---
id: SC-OPS-014
title: StoneCharts DEC-009 Performance Budgets Decision Brief
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PERF-001, REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-009 Performance Budgets Decision Brief

## Decision question

What performance and artifact-size budgets block release?

## Recommendation

Approve a baseline-first budget policy:

1. 0.0.0.1 establishes a reproducible benchmark baseline across the small, business,
   dense, and stress profiles.
2. Release blocking is driven by measured regression against that baseline, not by an
   invented percentage threshold.
3. Artifact-size evidence is tracked alongside the benchmark results and release
   manifest.
4. Later releases may derive explicit regression budgets from observed variance.

This matches the benchmark spec and keeps the release from pretending it has precise
performance thresholds before the measurement program is mature.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Approve the baseline-first policy | Performance gates stay honest and evidence-based | No fixed absolute threshold yet |
| Invent fixed budgets now | Easy to communicate on paper | Risky without a stable measurement baseline |
| Leave budgets undefined | No policy until the release candidate stage | Ambiguous and hard to enforce |

## Stakeholder impact

- Product: gets a truthful non-functional boundary.
- Engineering: can measure and optimize against real workloads.
- QA and compliance: have a verifiable release gate instead of an arbitrary number.
- Users: see a release policy grounded in recorded evidence.

## Agent review

The panel approved the baseline-first policy and agreed that the missing piece is the
immutable benchmark record, not a fabricated percentage budget.

## Outcome

DEC-009 is approved and recorded as a baseline-first performance and artifact-size
policy.
