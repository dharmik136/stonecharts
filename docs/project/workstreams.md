---
id: SC-OPS-002
title: StoneCharts Workstreams
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Workstreams

Workstreams are stable reporting lanes, not substitute departments. A work item has
one primary workstream even when it changes several repositories or languages.

| ID | Workstream | Durable outcome | Alpha 1 focus |
|---|---|---|---|
| WS-01 | Product contract and governance | Claims, scope, ownership, risks, and decisions remain explicit and traceable | Approve the release contract and resolve blockers without fictional approvals |
| WS-02 | Renderer correctness and active scope | Every accepted specification renders safely and mathematically correctly | Restrict active capability to line and column; close signed stacking, percent, layout, and edge-case gaps |
| WS-03 | Parity and conformance | Every certified renderer satisfies one executable corpus and canonical serializer | Direct cross-render, invalid parity, fuzzing, golden integrity, and deterministic evidence |
| WS-04 | Runtime, browser, and accessibility | Interactive behavior satisfies the DOM and accessibility contracts in supported browsers | Live tooltip, legend, focus, keyboard, multi-chart, and no-JS qualification |
| WS-05 | Customization, layout, and visual profiles | Structured freedom grows without invalidating safety or guarantee levels | Manual margins, theme/style boundaries, overflow behavior, and default visual profile |
| WS-06 | Packaging, release, and supply chain | Reproducible, attributable, supported artifacts can be shipped and audited | Version lockstep, artifacts, SBOM, provenance, hashes, changelog, and evidence pack |
| WS-07 | Documentation and developer experience | A developer can adopt, diagnose, and extend StoneCharts from authoritative material | API quick starts, migration notes, examples, troubleshooting, and renderer-author guidance |
| WS-08 | Chart and language expansion | New implementations reuse the same contracts instead of forking behavior | Design the admission protocol; expansion timing remains a product decision |

## Current sequence

1. Close Alpha 1 contract and correctness gaps in WS-01 and WS-02.
2. Qualify exact output and browser behavior through WS-03 and WS-04.
3. Lock the minimum customization and layout surface in WS-05.
4. Produce releasable artifacts and evidence through WS-06 and WS-07.
5. Admit WS-08 implementation only under the expansion decision and renderer
   constitution.

Security, privacy, performance, and accessibility are acceptance dimensions across
all workstreams rather than isolated final-stage checks.
