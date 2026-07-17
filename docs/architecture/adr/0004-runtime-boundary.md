---
id: PC-ARCH-ADR-0004
title: Separate Runtime Semantics from Adaptive Placement
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.1-alpha.1 and later
requirements: [REQ-RUNTIME-001, REQ-A11Y-001]
evidence: [TEST-RUNTIME-BROWSER, REVIEW-ACCESSIBILITY-MANUAL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# ADR 0004: Separate Runtime Semantics from Adaptive Placement

## Context

Tooltip coordinates and some presentation depend on container geometry, viewport,
scroll position, input modality, and browser behavior. Requiring the same screen
coordinates would conflict with usable responsive placement.

## Decision

The runtime contract pins tooltip content, data identity, navigation transitions,
legend state, focus behavior, and DOM/ARIA state updates. It defines adaptive
placement constraints and a preferred fallback order, not universal absolute screen
coordinates.

PeakCharts guarantees authored DOM and ARIA semantics, not identical platform
accessibility trees across browsers, operating systems, and assistive technologies.
Embedding modes are qualified separately because inline SVG, standalone SVG, and SVG
used as an image do not expose the same interaction model.

## Consequences

One runtime can remain responsive while semantic tests stay deterministic. Browser and
assistive-technology matrices become release evidence. Event propagation is specified
only where PeakCharts intentionally handles or cancels an event.

## Rejected alternatives

- Pin tooltip screen pixels: breaks responsive containment.
- Leave behavior unspecified: makes cross-language DOM parity meaningless.
- Claim identical accessibility trees: those trees are produced by host platforms.

