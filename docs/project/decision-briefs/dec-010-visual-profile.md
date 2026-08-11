---
id: SC-OPS-008
title: StoneCharts DEC-010 Visual Profile Decision Brief
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-VIS-001, REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-010 Visual Profile Decision Brief

## Decision question

What is the certified visual profile for `0.0.0.1`?

## Recommendation

Approve the host-font semantic SVG profile as the certified visual profile for
`0.0.0.1`.

That means:

1. Semantic SVG `<text>` remains the released profile.
2. Canonical geometry and text placement are fixed.
3. Automatic fit and pixel identity are not part of the promise.
4. Embedded-font and pinned-exporter profiles remain future controlled decisions.

This is the smallest accurate visual promise the current release can make. It preserves
the existing release posture and avoids overstating raster determinism before the
export path is qualified.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Approve the host-font semantic profile | Release a truthful visual baseline now | No pixel/export guarantee |
| Approve a pinned exporter profile now | Promise a stronger export contract immediately | Not supported by the current evidence trail |
| Leave the visual profile undefined | Defer the decision until later | Keeps release claims vague |

## Stakeholder impact

- Product: gets a concrete visual claim without overpromising.
- Engineering: can keep canonical geometry stable while export qualification continues.
- QA and compliance: have a bounded visual contract to review.
- Users: know the default visual behavior and the exact boundary of the promise.

## Agent review

The panel approved the host-font profile and agreed that the missing exporter evidence
belongs to a separate future decision, not to the 0.0.0.1 visual baseline.

## Outcome

DEC-010 is approved and recorded as the 0.0.0.1 host-font visual profile.

