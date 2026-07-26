---
id: SC-OPS-004
title: StoneCharts Decision Register
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-17"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Decision Register

Recommendations are starting positions, not approvals. Accepted architectural choices
receive an ADR; bounded operating decisions name their controlling project document.

## Resolved decisions

| ID | Decision | Resolution | Authority | Resolved |
|---|---|---|---|---|
| DEC-001 | Canonical first release identifier | Use exactly `0.0.0.1`; do not represent it as SemVer or publish invalid `v0.0.0.1` Go tags | [ADR 0007](../architecture/adr/0007-release-identifier.md) | 2026-07-18 |
| DEC-002 | Active 0.0.0.1 chart scope | Accept `line`, `column`, and `area` in the active release scope; keep the other chart designs informative until each has a renderer and conformance corpus | [Project operating model](README.md), [Stage 0 gate](stage-0.md), [Positioning and alpha scope](../product/positioning-and-scope.md) | 2026-07-20 |
| DEC-003 | Additional language renderer timing | Design the language conformance kit now, but defer new language implementation until Python and Go have proven the contract end to end through 0.0.0.1 qualification | [Renderer constitution](../architecture/renderer-constitution.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |
| DEC-004 | Structured customization surface for 0.0.0.1 | Keep customization typed, deterministic, and schema-governed; allow themes, sizing, margins, palettes, series styling, gradients, patterns, and supported mark controls; exclude raw CSS, raw SVG, callbacks, DOM mutation, and other executable escape hatches from certified output | [Customization boundary](../contracts/customization-boundary.md), [ADR 0005](../architecture/adr/0005-layout-and-fonts.md) | 2026-07-18 |
| DEC-005 | Compatibility policy beginning with 0.0.0.1 | Allow governed pre-release breaks during qualification; after release, require migration notes, deprecation windows where feasible, traceability updates, and checklist evidence for public-surface changes | [Compatibility policy](../contracts/compatibility-policy.md), [Release plan](../releases/0.0.0.1/plan.md) | 2026-07-18 |
| DEC-006 | Default branch and merge strategy | Use `main` as the default branch and keep the authoritative merge policy recorded in the governed project documents | [Project operating model](README.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |
| DEC-007 | GitHub Project fields and workflow | Use the schema-validated backlog, controlled status model, stable IDs, traceability fields, and local/remote conformance checks | [Project operating model](README.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |
| DEC-008 | Supported runtime and platform matrix | Support Python 3.9 and 3.14, Go 1.26, Chromium on the pinned desktop Linux profile through local HTTP, and no certified exporter profile for 0.0.0.1 | [Runtime matrix](../contracts/runtime-matrix.md), [Visual profile](../contracts/visual-profile.md), [Release plan](../releases/0.0.0.1/plan.md) | 2026-07-18 |
| DEC-010 | Certified visual profile for 0.0.0.1 | Use the host-font semantic SVG profile as the certified visual baseline; reserve embedded-font and pinned-exporter profiles for later decisions | [Visual profile](../contracts/visual-profile.md), [Typography and export profiles](../contracts/typography-and-export-profiles.md) | 2026-07-18 |
| DEC-009 | Performance and artifact-size release budgets | Use a reproducible baseline across small, business, dense, and stress workloads, with regression budgets derived from observed variance rather than invented thresholds | [Performance budget policy](../contracts/performance-budgets.md), [Benchmark specification](../quality/benchmark-spec.md) | 2026-07-18 |
| DEC-011 | Package and source publication channels | Keep the repository and registries private until S3 evidence is complete; publish only through supportable channels recorded in the release plan and supply-chain policy | [Publication policy](../contracts/publication-policy.md), [Supply-chain policy](../security/supply-chain.md), [Release plan](../releases/0.0.0.1/plan.md) | 2026-07-18 |
| DEC-012 | StoneCharts name clearance for public commercial use | Require a dated due-diligence record before any public commercial name claim; technical namespace adoption is not legal clearance | [Name-clearance policy](../contracts/name-clearance-policy.md), [ADR 0006](../architecture/adr/0006-stonecharts-namespace.md) | 2026-07-18 |
| DEC-013 | Commercial license, contribution, support, and access model | Keep the product proprietary until a written business policy is approved; internal access does not imply external rights | [Commercial terms policy](../contracts/commercial-terms-policy.md), [Product positioning and alpha scope](../product/positioning-and-scope.md) | 2026-07-18 |
| DEC-014 | Post-0.0.0.1 expansion order | Admit `bar` as the next chart type, targeting release `0.0.0.2`; per the roadmap's own analysis it reuses column's band-layout, stacking, and all shared chrome via a pure orientation transpose, with no new data or point model. No other chart type or language is admitted by this decision. Implementation follows the chart admission checklist in full - this decision closes only its Phase 0. | [Chart admission checklist](../architecture/chart-admission-checklist.md), [Chart families roadmap](../roadmap/chart-families.md), [Stage 5 expansion gate](backlog.yaml) | 2026-07-26 |

## Open decisions

| Priority | ID | Decision | Current recommendation | Decide before |
|---:|---|---|---|---|

## Discussion order

DEC-005, DEC-006, DEC-008, DEC-009, DEC-010, DEC-011, DEC-012, and DEC-013 are resolved.
The commercial boundary is governed by the approved policy document and must not be inferred from engineering progress.

DEC-005 stakeholder brief: [Compatibility decision brief](decision-briefs/dec-005-compatibility.md).
