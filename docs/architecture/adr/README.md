---
id: SC-ARCH-010
title: StoneCharts Architecture Decision Log
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

# Architecture Decision Log

ADRs capture one architecturally significant decision, its rationale, alternatives,
and consequences. An ADR is immutable after approval except for status and links;
changing the decision requires a superseding ADR.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-guarantee-profiles.md) | Separate canonical, behavioral, visual, and customization guarantees | Proposed |
| [0002](0002-validation-and-capabilities.md) | Separate active-schema validity from renderer capability | Proposed |
| [0003](0003-signed-stacking.md) | Diverging normal stacks; non-negative percent stacks in 0.0.0.1 | Approved |
| [0004](0004-runtime-boundary.md) | Invariant semantics with adaptive viewport presentation | Proposed |
| [0005](0005-layout-and-fonts.md) | Manual Alpha layout and tiered font/export profiles | Proposed |
| [0006](0006-stonecharts-namespace.md) | One StoneCharts product and technical namespace before Alpha | Proposed |
| [0007](0007-release-identifier.md) | `0.0.0.1` is the canonical first release identifier | Approved |
