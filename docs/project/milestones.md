---
id: SC-OPS-003
title: StoneCharts Milestone Map
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

# Milestone Map

Dates are assigned only after scope, capacity, and blocking decisions are known.
Milestones are exited by evidence, not elapsed time.

| Milestone | Outcome | Entry condition | Exit gate | State |
|---|---|---|---|---|
| M0: Product foundation | One named product, governed repository, explicit guarantees, and traceable Alpha plan | Line and column implementations exist | Branches reconciled; StoneCharts namespace is coherent; documentation control and project intake exist | Foundation implemented; approvals remain proposed |
| M1: Alpha contract closure | The active Alpha behavior is complete and internally consistent | M0 controls are available | Only line and column are actively supported; signed/percent stacking, layout margins, metadata, empty/single-point behavior, and typed capability errors satisfy shared tests | Next |
| M2: Alpha qualification | Claims are backed by repeatable conformance, browser, security, and performance evidence | M1 behavior is frozen | Python/Go byte parity, direct sweep, invalid/fuzz tests, browser accessibility suite, benchmark budgets, threat review, and deterministic evidence generation pass | Pending |
| M3: Alpha release candidate | Installable artifacts and release documentation can be reproduced from one commit | M2 evidence passes | Version lockstep, wheel/module checks, SBOM, provenance, golden hashes, changelog, known limits, support matrix, and release checklist are complete | Pending |
| M4: 0.0.1-alpha.1 release | A deliberately bounded alpha is available to its approved audience | M3 candidate is accepted | Signed tag and artifacts published; evidence manifest archived; support and feedback channels active | Pending |
| M5: Expansion admission | New charts and languages can enter without weakening the core contract | Alpha findings reviewed | Expansion order, language conformance kit, compatibility policy, and next release scope approved | Pending |

## Critical dependency chain

Active scope -> stacking and layout semantics -> frozen canonical corpus -> browser and
performance qualification -> packaging and evidence -> release. Chart or language
expansion does not sit on this chain until the Alpha expansion decision changes it.
