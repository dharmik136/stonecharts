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
| DEC-002 | Active 0.0.0.1 chart scope | Accept only `line` and `column` in the active release scope; keep the other chart designs informative until each has a renderer and conformance corpus | [Project operating model](README.md), [Stage 0 gate](stage-0.md), [Positioning and alpha scope](../product/positioning-and-scope.md) | 2026-07-17 |
| DEC-003 | Additional language renderer timing | Design the language conformance kit now, but defer new language implementation until Python and Go have proven the contract end to end through 0.0.0.1 qualification | [Renderer constitution](../architecture/renderer-constitution.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |
| DEC-004 | Structured customization surface for 0.0.0.1 | Keep customization typed, deterministic, and schema-governed; allow themes, sizing, margins, palettes, series styling, gradients, patterns, and supported mark controls; exclude raw CSS, raw SVG, callbacks, DOM mutation, and other executable escape hatches from certified output | [Customization boundary](../contracts/customization-boundary.md), [ADR 0005](../architecture/adr/0005-layout-and-fonts.md) | 2026-07-18 |
| DEC-006 | Default branch and merge strategy | Use `main` as the default branch and keep the authoritative merge policy recorded in the governed project documents | [Project operating model](README.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |
| DEC-007 | GitHub Project fields and workflow | Use the schema-validated backlog, controlled status model, stable IDs, traceability fields, and local/remote conformance checks | [Project operating model](README.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |

## Open decisions

| Priority | ID | Decision | Current recommendation | Decide before |
|---:|---|---|---|---|
| 2 | DEC-005 | What compatibility promise begins at 0.0.0.1? | Permit documented pre-release breaks now; after 0.0.0.1, require migration notes and a deprecation window for public spec/API/DOM changes | S3 release candidate |
| 3 | DEC-008 | What is the supported runtime and platform matrix? | Pin explicit Python, Go, browser, OS, and exporter profiles from CI evidence rather than broad untested claims | S2 qualification plan |
| 4 | DEC-009 | What performance and artifact-size budgets block release? | Establish measured budgets for 10, 100, 1,000, and stress-point profiles before optimizing implementation details | S2 benchmark gate |
| 5 | DEC-010 | What is the certified visual profile for 0.0.0.1? | Guarantee semantic SVG under the host-font profile; treat embedded font plus pinned exporter as a separate certified profile | S2 visual qualification |
| 6 | DEC-011 | When and where are packages and source made public? | Keep the repository and registries private until S3 evidence is complete; publish only channels with an explicit support policy | S3 distribution plan |
| 7 | DEC-012 | Is the StoneCharts name cleared for public commercial use? | Complete repository, package-index, domain, and trademark due diligence before public announcement; technical adoption is not legal clearance | Public branding or registration |
| 8 | DEC-013 | What commercial license, contribution terms, and support model apply? | Keep the current proprietary boundary until a written business model and contributor agreement are approved | External access or contributions |

## Discussion order

DEC-006 is resolved. DEC-008 through DEC-010 define qualification. DEC-005 and DEC-011 through
DEC-013 govern release and public exposure and must not be inferred from engineering
progress.
