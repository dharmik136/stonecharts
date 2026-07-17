---
id: SC-OPS-004
title: StoneCharts Open Decision Backlog
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Open Decision Backlog

These are questions to resolve with evidence. A recommendation is a starting
position, not an approved decision; accepted architectural choices receive an ADR.

| Priority | ID | Decision | Current recommendation | Decide before |
|---:|---|---|---|---|
| 1 | DEC-001 | What is the canonical first release identifier across product, Python, and Go? | Product/tag `0.0.1-alpha.1`, Python `0.0.1a1`, Go tag `v0.0.1-alpha.1`; do not invent a fourth spelling | M1 metadata implementation |
| 2 | DEC-002 | Does Alpha 1 actively accept only line and column? | Yes; keep the other chart designs informative until each has a renderer and conformance corpus | M1 active-schema change |
| 3 | DEC-003 | Do additional languages start before or after Alpha 1 qualification? | Design the language conformance kit now; defer implementations until Python and Go prove the contract end to end | Any language implementation |
| 4 | DEC-004 | Which customization primitives are guaranteed in Alpha 1? | Ship validated margins, themes, palettes, series styles, gradients, patterns, and existing mark controls; defer arbitrary CSS, callbacks, and raw SVG injection | M1 schema freeze |
| 5 | DEC-005 | What compatibility promise begins at Alpha 1? | Permit documented pre-alpha breaks now; after Alpha 1, require migration notes and a deprecation window for public spec/API/DOM changes | M3 release candidate |
| 6 | DEC-006 | Should the default branch become `main`, and which merge strategy is authoritative? | Rename to `main`; use short-lived branches and squash merge with automatic source-branch deletion | Project automation and branch protection |
| 7 | DEC-007 | Which GitHub Project fields and automations are necessary? | Status, priority, workstream, target release, requirement/ADR, risk, evidence, owner, and dependency; automate intake and merged/closed transitions only | Project population |
| 8 | DEC-008 | What is the supported runtime and platform matrix? | Pin explicit Python, Go, browser, OS, and exporter profiles from CI evidence rather than broad untested claims | M2 qualification plan |
| 9 | DEC-009 | What performance and artifact-size budgets block release? | Establish measured budgets for 10, 100, 1,000, and stress-point profiles before optimizing implementation details | M2 benchmark gate |
| 10 | DEC-010 | What is the certified visual profile for Alpha 1? | Guarantee semantic SVG under the host-font profile; treat embedded font plus pinned exporter as a separate certified profile | M2 visual qualification |
| 11 | DEC-011 | When and where are packages and source made public? | Keep the repository and registries private until M3 evidence is complete; publish only channels with an explicit support policy | M3 distribution plan |
| 12 | DEC-012 | Is the StoneCharts name cleared for public commercial use? | Complete repository, package-index, domain, and trademark due diligence before public announcement; technical adoption is not legal clearance | Public branding or registration |
| 13 | DEC-013 | What commercial license, contribution terms, and support model apply? | Keep the current proprietary boundary until a written business model and contributor agreement are approved | External access or contributions |

## Discussion order

Resolve DEC-001 through DEC-004 first because they define M1 scope. DEC-005 through
DEC-010 define qualification and release operations. DEC-011 through DEC-013 govern
public exposure and should not be inferred from engineering progress.
