---
id: SC-REL-005
title: StoneCharts 0.0.0.1 Visual Profile Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-VIS-001]
evidence: [REVIEW-VISUAL-PROFILE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-19"
review_due: "2026-08-19"
supersedes: null
superseded_by: null
---

# Visual Profile Review

## Scope

This review covers the approved 0.0.0.1 visual profile as documented in
[`docs/contracts/visual-profile.md`](../../../contracts/visual-profile.md),
[`docs/contracts/typography-and-export-profiles.md`](../../../contracts/typography-and-export-profiles.md),
[`docs/contracts/guarantees-and-limits.md`](../../../contracts/guarantees-and-limits.md),
and the approved decision record for DEC-010.

## Reviewed claims

- The released visual profile is host-font semantic SVG, not a certified pixel profile.
- Semantic `<text>` remains part of the released profile.
- Pixel identity is not promised outside a separately named export profile.
- Any future embedded-font or pinned-export profile must be a separate controlled decision.

## Result

The 0.0.0.1 visual profile is approved as documented. The release currently makes a
truthful host-font promise and no stronger pixel-export claim.
