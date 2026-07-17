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
last_reviewed: "2026-07-18"
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
| DEC-007 | GitHub Project fields and workflow | Use the schema-validated backlog, controlled status model, stable IDs, traceability fields, and local/remote conformance checks | [Project operating model](README.md), [Stage 0 gate](stage-0.md) | 2026-07-18 |

## Open decisions

| Priority | ID | Decision | Current recommendation | Decide before |
|---:|---|---|---|---|
| 1 | DEC-002 | Does 0.0.0.1 actively accept only line and column? | Yes; keep the other chart designs informative until each has a renderer and conformance corpus | S1 active-schema change |
| 2 | DEC-003 | Do additional languages start before or after 0.0.0.1 qualification? | Design the language conformance kit now; defer implementations until Python and Go prove the contract end to end | Any language implementation |
| 3 | DEC-004 | Which customization primitives are guaranteed in 0.0.0.1? | Ship validated margins, themes, palettes, series styles, gradients, patterns, and existing mark controls; defer arbitrary CSS, callbacks, and raw SVG injection | S1 schema freeze |
| 4 | DEC-005 | What compatibility promise begins at 0.0.0.1? | Permit documented pre-release breaks now; after 0.0.0.1, require migration notes and a deprecation window for public spec/API/DOM changes | S3 release candidate |
| 5 | DEC-006 | Should the default branch become `main`, and which merge strategy is authoritative? | Rename to `main`; use short-lived branches and squash merge with automatic source-branch deletion | Stage 0 exit review |
| 6 | DEC-008 | What is the supported runtime and platform matrix? | Pin explicit Python, Go, browser, OS, and exporter profiles from CI evidence rather than broad untested claims | S2 qualification plan |
| 7 | DEC-009 | What performance and artifact-size budgets block release? | Establish measured budgets for 10, 100, 1,000, and stress-point profiles before optimizing implementation details | S2 benchmark gate |
| 8 | DEC-010 | What is the certified visual profile for 0.0.0.1? | Guarantee semantic SVG under the host-font profile; treat embedded font plus pinned exporter as a separate certified profile | S2 visual qualification |
| 9 | DEC-011 | When and where are packages and source made public? | Keep the repository and registries private until S3 evidence is complete; publish only channels with an explicit support policy | S3 distribution plan |
| 10 | DEC-012 | Is the StoneCharts name cleared for public commercial use? | Complete repository, package-index, domain, and trademark due diligence before public announcement; technical adoption is not legal clearance | Public branding or registration |
| 11 | DEC-013 | What commercial license, contribution terms, and support model apply? | Keep the current proprietary boundary until a written business model and contributor agreement are approved | External access or contributions |

## Discussion order

Resolve DEC-002, DEC-003, DEC-004, and DEC-006 to close Stage 0. DEC-008 through
DEC-010 define qualification. DEC-005 and DEC-011 through DEC-013 govern release and
public exposure and must not be inferred from engineering progress.
