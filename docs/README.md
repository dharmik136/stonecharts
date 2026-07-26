---
id: SC-GOV-005
title: StoneCharts Documentation Index
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: all
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# StoneCharts Documentation

This index is the entry point to StoneCharts product and engineering controls.
Document status and classification are authoritative in each file's metadata.

## Start here

- [Documentation control policy](governance/documentation-policy.md)
- [Controlled glossary](governance/glossary.md)
- [Product thesis](product/thesis.md)
- [Positioning and first-release scope](product/positioning-and-scope.md)
- [Requirements registry](requirements/registry.yaml)
- [Requirements and traceability guide](requirements/README.md)
- [Risk register](governance/risk-register.yaml)

## Project execution

- [StoneCharts GitHub Project](https://github.com/users/dharmik136/projects/2)
- [Project operating model](project/README.md)
- [Stage 0 foundation gate](project/stage-0.md)
- [Governed execution backlog](project/backlog.yaml)
- [Workstreams](project/workstreams.md)
- [Milestone map](project/milestones.md)
- [Open decision backlog](project/decisions.md)

## Architecture and contracts

- [System design](architecture/system-design.md)
- [Renderer constitution](architecture/renderer-constitution.md)
- [Chart admission checklist](architecture/chart-admission-checklist.md)
- [Architecture decisions](architecture/adr/README.md)
- [Guarantees and limits](contracts/guarantees-and-limits.md)
- [Validation and capabilities](contracts/validation-and-capabilities.md)
- [Runtime semantics](contracts/runtime-semantics.md)
- [Customization boundary](contracts/customization-boundary.md)
- [Typography and export profiles](contracts/typography-and-export-profiles.md)
- [Accessibility contract](contracts/accessibility.md)

## Qualification and release

- [Test strategy](quality/test-strategy.md)
- [Benchmark specification](quality/benchmark-spec.md)
- [Evidence registry](quality/evidence-registry.yaml)
- [Threat model](security/threat-model.md)
- [Supply-chain policy](security/supply-chain.md)
- [0.0.0.1 release plan](releases/0.0.0.1/plan.md)
- [0.0.0.1 qualification checklist](releases/0.0.0.1/checklist.md)
- [0.0.0.1 release findings](releases/0.0.0.1/evidence/release-findings.md)

Research and long-range roadmaps remain under `docs/research` and `docs/roadmap`.
They inform decisions but do not override approved requirements, ADRs, or contracts.
