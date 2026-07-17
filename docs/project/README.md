---
id: SC-OPS-001
title: StoneCharts Project Operating Model
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: all
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Project Operating Model

## Purpose

This model turns approved product contracts into reviewable work and release
evidence. It is intentionally lighter than the governance layer: project tracking
coordinates execution but cannot redefine a requirement, ADR, contract, risk, or
release gate.

Execution board: [StoneCharts GitHub Project #2](https://github.com/users/dharmik136/projects/2).

## Sources of truth

Precedence is explicit:

1. Approved normative documents and release contracts.
2. Requirements, risks, decisions, and evidence registries.
3. The GitHub Project for current status, ownership, priority, and dependencies.
4. GitHub issues for bounded outcomes and pull requests for reviewed changes.
5. Generated qualification and release evidence for what was actually proved.

When these disagree, the higher source controls and the lower source is corrected.

## Work-item contract

Every item admitted to `Ready` has the following information:

| Field | Required meaning |
|---|---|
| Outcome | One externally verifiable result |
| Type | Defect, capability, decision, qualification, documentation, or operations |
| Workstream | One primary ownership and reporting lane |
| Target | A release or an explicit unscheduled state |
| Traceability | Applicable requirement, ADR, contract, risk, or a reason none applies |
| Priority | P0 blocker, P1 milestone requirement, P2 deferrable value, or P3 exploration |
| Acceptance | Observable pass/fail conditions |
| Verification | Tests, benchmarks, review, or evidence that will prove the outcome |
| Dependencies | Blocking decisions and work items |
| Compatibility | Schema, API, DOM, bytes, runtime, package, and migration impact |
| Owner | One accountable person; collaborators may be many |

## Status model

`Inbox` -> `Triage` -> `Ready` -> `In Progress` -> `In Review` ->
`Qualification` -> `Done`.

`Blocked` is a visible exception state and names the blocking item or decision.
`Done` means the change is integrated, acceptance criteria pass, required evidence is
recorded, and affected documentation is current. A merged pull request alone is not
completion.

## Flow controls

- A renderer-contract change crosses Python, Go, fixtures, and documentation as one
  coordinated item unless an approved migration plan says otherwise.
- Canonical-output work does not regenerate goldens before the intended semantic
  change is reviewed.
- Only one high-risk contract change per shared renderer surface is active at once.
- Decisions blocking Alpha 1 are resolved before expansion work enters `Ready`.
- Unplanned work enters through triage; urgency does not erase acceptance criteria.

## Project views

The recommended GitHub Project starts with five views:

| View | Purpose |
|---|---|
| Alpha 1 Board | Status flow for the active release |
| Release Gates | Only P0/P1 qualification and release blockers |
| Workstreams | Grouped ownership and dependency view |
| Decisions | Open decisions ordered by their blocking deadline |
| Risks and Evidence | Requirements, risks, and proof expected before release |

The exact fields and automation are open decisions in
[the decision backlog](decisions.md), not silently assumed here.

## Related project controls

- [Workstreams](workstreams.md)
- [Milestone map](milestones.md)
- [Decision backlog](decisions.md)
- [Alpha 1 release plan](../releases/0.0.1-alpha.1/plan.md)
- [Test strategy](../quality/test-strategy.md)
- [Risk register](../governance/risk-register.yaml)
