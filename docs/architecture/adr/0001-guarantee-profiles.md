---
id: SC-ARCH-ADR-0001
title: Separate Product Guarantee Profiles
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1 and later
requirements: [REQ-DET-001, REQ-VIS-001, REQ-CUST-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, REVIEW-VISUAL-PROFILE]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# ADR 0001: Separate Product Guarantee Profiles

## Context

"Same chart" can mean identical serialized SVG, equivalent interaction behavior,
similar visual geometry, or identical raster pixels. Treating these as one promise
would make the product either misleading or impractical.

## Decision

StoneCharts defines four independent technical profiles:

1. Canonical output: identical validated SVG serialization under a named release.
2. Behavioral parity: equivalent DOM inputs and observable interaction semantics.
3. Certified visual: qualified pixels only in a pinned font and export environment.
4. Customization boundary: structured features covered by the preceding profiles.

All product claims name their profile and applicability. These technical commitments
do not create legal warranties or service levels; those require license or commercial
terms.

## Consequences

Byte parity remains a powerful internal oracle without being marketed as universal
pixel parity. Browser adaptation remains possible. Customers can choose portable SVG
or a more constrained certified export. Unsupported escape hatches can exist later
only with an explicit downgrade of guarantees.

## Rejected alternatives

- One universal determinism claim: technically false across host viewers.
- Text outlines for every output: damages selection and semantics and increases size.
- No guarantees: discards the central product differentiation.

