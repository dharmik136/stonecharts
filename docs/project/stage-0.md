---
id: SC-OPS-005
title: StoneCharts Stage 0 Foundation Gate
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PROD-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Stage 0 Foundation Gate

## Purpose

Stage 0 establishes the product and engineering contract that all implementation,
qualification, packaging, and publication work must follow. It is not a documentation
pause and it does not certify renderer behavior. Its output is an approved, internally
consistent baseline with every known gap represented as governed work.

Release `0.0.0.1` cannot enter contract hardening until `GATE-S0` is complete.

## Entry state

- StoneCharts is the canonical product and technical namespace.
- Python and Go line and column renderers exist with a shared golden corpus.
- Repository and documentation controls execute successfully.
- Known correctness, runtime, customization, release, and evidence gaps are recorded.

## Required decisions

Stage 0 resolves the following decisions before its exit review:

- `DEC-001`: canonical release identifier.
- `DEC-002`: active chart scope.
- `DEC-003`: language-expansion timing.
- `DEC-004`: guaranteed customization boundary.
- `DEC-006`: branch and merge policy, including the private-plan protection limit.
- `DEC-007`: GitHub Project fields, workflow, and conformance controls.

Later decisions remain scheduled and owned; they do not silently block Stage 0 unless
an accepted Stage 0 decision makes them prerequisites.

## Controlled baseline

The product owner and maintainer review the following as one baseline:

- Product thesis, positioning, guarantees, and known limits.
- System design, renderer constitution, and applicable ADRs.
- Specification, validation, SVG/DOM, runtime, accessibility, customization, layout,
  typography, and export contracts.
- Requirements, risks, evidence definitions, test strategy, benchmark protocol,
  threat model, and supply-chain policy.
- `0.0.0.1` release plan, qualification checklist, and evidence format.
- Project operating model, workstreams, stage map, decision backlog, and execution
  backlog registry.

Approval is truthful: `review_mode: self` remains visible while one person holds both
accountable roles. Proposed documents do not become approved merely because a linter
passes.

## Exit criteria

`GATE-S0` closes only when:

1. The canonical release identity and required Stage 0 decisions are recorded.
2. Every applicable normative document has a truthful lifecycle status and review date.
3. Every `must` requirement has acceptance criteria, ownership, and verification IDs.
4. Every open implementation gap and release-significant risk maps to a Project item.
5. Project fields and item values conform to `docs/project/backlog.yaml`.
6. Documentation, schema, reference, and Project conformance checks pass.
7. No chart-type or language-expansion implementation is active.
8. Stage 1 items remain outside `Ready` until this gate is closed.

## Evidence

The Stage 0 review records the exact commit, clean-tree state, documentation-control
output, Project-conformance output, open decision list, open risk list, and the identity
of the product-owner and maintainer approvals. These records become inputs to the
release evidence pack; they are not substituted by a screenshot of the board.

## Change control

After Stage 0, any change to the guarantee model, active scope, customization boundary,
or release identity requires an updated decision record and impact review before the
affected work can return to `Ready`.
