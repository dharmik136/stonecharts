---
id: SC-CON-014
title: StoneCharts Compatibility Policy
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: [REQ-REL-001, REQ-PROD-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Compatibility Policy

## Purpose

This policy defines when StoneCharts begins to promise compatibility beyond the
pre-release operating baseline.

## Policy

For `0.0.0.1`, the repository may still record governed breaking changes while the
release is under active qualification. Those changes must be explicit in the decision
register, backlog, and review evidence.

After `0.0.0.1`, any change to a public schema field, API surface, DOM contract,
golden output, or supported release artifact MUST include:

1. A migration note that explains the breaking change.
2. A deprecation window where one is technically feasible.
3. Updated traceability to the impacted requirement, ADR, or decision.
4. Evidence that the change was reviewed against the release checklist.

## Scope

This policy applies to governed public surfaces only:

- JSON/YAML spec schema
- validated chart capability set
- SVG and HTML DOM contracts
- runtime interaction contract
- release artifact identifiers and packaging rules

It does not promise source-level stability for internal helpers, test scaffolding,
documentation drafts, or unreleased design-only chart types.

## Relationship to other contracts

This policy is narrower than the guarantees document. `G1-G4` define what the current
release emits and permits; this policy defines how future public changes are admitted.
It is also bounded by the runtime, accessibility, and release-checklist contracts.

## Enforcement

Compatibility changes are accepted only when the governing decision record, release
plan, and traceability map agree on the change class and the required evidence.
