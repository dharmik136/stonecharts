---
id: SC-OPS-003
title: StoneCharts Milestone Map
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-24"
review_due: "2026-09-29"
supersedes: null
superseded_by: null
---

# Stage And Milestone Map

Dates are assigned only after scope, capacity, and blocking decisions are known.
Milestones are exited by evidence, not elapsed time.

| Stage | Outcome | Entry condition | Exit gate | State |
|---|---|---|---|---|
| S0: Foundation | One named product, governed repository, explicit guarantees, and traceable `0.0.0.1` plan | Line, column, and area implementations exist | Required Stage 0 decisions resolved; controlled baseline reviewed; local and remote Project conformance passes | Complete |
| S1: Contract closure | Active line, column, bar, and area behavior is complete and internally consistent | `GATE-S0` passes | Active scope, stacking, margins, validation, capabilities, customization, and runtime semantics satisfy shared tests | Complete |
| S2: Qualification | Claims are backed by repeatable conformance, browser, security, visual, accessibility, and performance evidence | `GATE-S1` passes | Python/Go parity, direct sweep, invalid/fuzz tests, browser suite, manual review, benchmark baseline, and threat review pass | Complete |
| S3: Release candidate | Installable artifacts and release documentation can be reproduced from one commit | `GATE-S2` passes | Version mapping, package checks, SBOM, provenance, hashes, changelog, known limits, support matrix, and evidence manifest are complete | Complete |
| S4: Release 0.0.0.1 | A deliberately bounded first release is available to its approved audience | `GATE-S3` passes | Authorized source tag and artifacts published; evidence archived; support and feedback channels active | Complete |
| S5: Expansion admission | New charts and languages can enter without weakening the core contract | `GATE-S4` passes and release findings are reviewed | Expansion order, conformance kit, compatibility policy, and next release scope approved | Complete (0.0.0.2–0.0.0.33: 33 chart types admitted via DEC-014 through DEC-060; complete 36-chart certified portfolio) |
| S6: Portfolio requalification | Every chart is held to the executable evidence standard established by the seed charts | Complete 36-chart portfolio exists | All 36 charts pass all eight SC-CERT gates, browser qualification, dual-runtime baselines, package-install checks, and clean release evidence | Complete (0.0.0.34) |

## Critical dependency chain

Active scope -> stacking and layout semantics -> frozen canonical corpus -> browser and
performance qualification -> packaging and evidence -> release. External distribution
and a real customer pilot remain separate business gates and are not represented as
completed engineering milestones.
