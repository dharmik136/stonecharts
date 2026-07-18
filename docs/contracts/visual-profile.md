---
id: SC-CON-016
title: StoneCharts 0.0.0.1 Visual Profile
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-VIS-001, REQ-REL-001]
evidence: [REVIEW-VISUAL-PROFILE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# 0.0.0.1 Visual Profile

## Approved default profile

StoneCharts 0.0.0.1 uses the host-font semantic SVG profile as its approved visual
profile.

That profile means:

- semantic SVG `<text>` elements remain present
- chart geometry and text placement are canonical
- automatic text fitting is not promised
- pixel identity is not promised
- host font selection, shaping, hinting, and rasterization remain viewer responsibilities

## Explicit non-claims

This approved profile does not certify a pixel export path. It does not promise an
embedded font, a pinned export engine, or a fixed tolerance profile.

## Relationship to future profiles

Any later certified pixel or export profile must name its font artifact, export engine,
environment digest, and tolerance explicitly, and must be reviewed as a separate
controlled decision.

