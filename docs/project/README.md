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
3. The schema-validated [execution backlog](backlog.yaml).
4. The GitHub Project for current status, ownership, priority, and dependencies.
5. GitHub issues for bounded outcomes and pull requests for reviewed changes.
6. Generated qualification and release evidence for what was actually proved.

When these disagree, the higher source controls and the lower source is corrected.

## Work-item contract

Every item admitted to `Ready` has the following information:

| Field | Required meaning |
|---|---|
| Outcome | One externally verifiable result |
| Type | Decision, requirement, work package, defect, or release gate |
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
- Decisions blocking 0.0.0.1 are resolved before expansion work enters `Ready`.
- Unplanned work enters through triage; urgency does not erase acceptance criteria.

An item may enter `Ready` only when every declared dependency is `Done`. The local
documentation checker enforces this rule in the backlog registry; the remote Project
checker enforces it against GitHub field values.

## Governed Project fields

| Field | Values or meaning |
|---|---|
| Tracking ID | Stable `DEC-*`, `REQ-*`, `WORK-*`, or `GATE-*` identifier |
| Item Type | Decision, Requirement, Work Package, Defect, or Release Gate |
| Status | Controlled workflow state above |
| Priority | P0 through P3 |
| Workstream | WS-01 through WS-08 |
| Stage | S0 Foundation through S5 Expansion |
| Target | `0.0.0.1`, post-release, or unscheduled |
| Traceability | Requirement, ADR, contract, or controlled-document IDs |
| Risks | Risk-register IDs addressed by the item |
| Evidence | Evidence-registry IDs that prove completion |
| Dependencies | Stable IDs that must finish first |
| Assignees | Accountable owner represented by GitHub's native field |
| Milestone | Repository milestone represented by GitHub's native field |

## Project views

The governed GitHub Project has six saved views. View names, filters, visible-field
order, and grouping are controlled by `docs/project/backlog.yaml`.

| View | Saved configuration | Purpose |
|---|---|---|
| 0.0.0.1 Board | Board layout | Full status flow for all governed work |
| Release Gates | `item-type:"Release Gate"` | Stage and release authorization evidence |
| Stage 0 | `stage:"S0 Foundation"` | The nine items that establish the controlled foundation |
| Decisions | `item-type:Decision` | Decision status, traceability, risks, and dependencies |
| Workstreams | Grouped by `Workstream` | Ownership, stage, target, risks, evidence, and dependencies |
| Risks & Evidence | `RISK-` | Work carrying a registered risk and its expected proof |

Project data is checked against `docs/project/backlog.yaml` with
`python tools/check_github_project.py`. The checker verifies saved views as well as
fields, issues, classification, and content. GitHub does not expose Project-view
creation through the supported API, so view configuration is performed in the UI and
then held against drift by the checker. The checker does not delete unregistered work;
it reports drift for review.

## Related project controls

- [Workstreams](workstreams.md)
- [Local agent operating model](local-agent-model.md)
- [Agent comparison benchmark](agent-comparison-benchmark.md)
- [Cross-orchestrator agent contract](agent-orchestration.md)
- [Stage and milestone map](milestones.md)
- [Decision register](decisions.md)
- [Stage 0 foundation gate](stage-0.md)
- [Execution backlog](backlog.yaml)
- [0.0.0.1 release plan](../releases/0.0.0.1/plan.md)
- [Test strategy](../quality/test-strategy.md)
- [Risk register](../governance/risk-register.yaml)
