---
id: SC-OPS-003
title: StoneCharts Milestone Map
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Stage And Milestone Map

Dates are assigned only after scope, capacity, and blocking decisions are known.
Milestones are exited by evidence, not elapsed time.

| Stage | Outcome | Entry condition | Exit gate | State |
|---|---|---|---|---|
| S0: Foundation | One named product, governed repository, explicit guarantees, and traceable `0.0.0.1` plan | Line, column, and area implementations exist | Required Stage 0 decisions resolved; controlled baseline reviewed; local and remote Project conformance passes | Complete |
| S1: Contract closure | Active line, column, and area behavior is complete and internally consistent | `GATE-S0` passes | Active scope, stacking, margins, validation, capabilities, customization, and runtime semantics satisfy shared tests | Complete |
| S2: Qualification | Claims are backed by repeatable conformance, browser, security, visual, accessibility, and performance evidence | `GATE-S1` passes | Python/Go parity, direct sweep, invalid/fuzz tests, browser suite, manual review, benchmark baseline, and threat review pass | Pending |
| S3: Release candidate | Installable artifacts and release documentation can be reproduced from one commit | `GATE-S2` passes | Version mapping, package checks, SBOM, provenance, hashes, changelog, known limits, support matrix, and evidence manifest are complete | Pending |
| S4: Release 0.0.0.1 | A deliberately bounded first release is available to its approved audience | `GATE-S3` passes | Authorized source tag and artifacts published; evidence archived; support and feedback channels active | Pending |
| S5: Expansion admission | New charts and languages can enter without weakening the core contract | `GATE-S4` passes and release findings are reviewed | Expansion order, conformance kit, compatibility policy, and next release scope approved | Pending |

## Critical dependency chain

Active scope -> stacking and layout semantics -> frozen canonical corpus -> browser and
performance qualification -> packaging and evidence -> release. Chart or language
expansion does not sit on this chain until `GATE-S5` authorizes it.
