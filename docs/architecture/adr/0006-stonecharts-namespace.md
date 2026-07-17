---
id: SC-ARCH-ADR-0006
title: Adopt the StoneCharts Namespace Before Alpha
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1 and later
requirements: [REQ-DET-001, REQ-RUNTIME-001]
evidence: [TEST-DOCS-CONTROL, TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# ADR 0006: Adopt the StoneCharts Namespace Before Alpha

## Context

The product is not yet publicly released, so this is the last low-cost point at
which to align its product identity and technical interfaces. A display-name-only
rename would leave contradictory package names, DOM selectors, runtime globals,
document identifiers, and repository references throughout the public contract.

## Decision

StoneCharts is the sole canonical product and technical namespace:

- Product and repository name: `StoneCharts` and `stonecharts`.
- Python distribution and import package: `stonecharts`.
- Go module, package, and import path: `stonecharts` for the current local module.
- Browser API: `window.StoneCharts`.
- Runtime environment variable: `STONECHARTS_RUNTIME`.
- SVG, CSS, and generated-definition prefix: `sc-`; default chart ID: `sc`.
- Controlled-document prefix: `SC-`.

No compatibility package, browser alias, or dual DOM selector is carried into
Alpha 1. Canonical SVG goldens are requalified under the `sc-` namespace, and both
certified renderers must continue to match the same files byte for byte.

## Consequences

All active interfaces tell one coherent product story, and future renderers can
copy one namespace contract. Code written against unpublished pre-alpha names must
be updated. Historical Git commits remain immutable evidence and may retain prior
working terminology.

Changing the DOM prefix intentionally changes canonical SVG hashes. This is an
approved baseline reset only when documentation control, both golden suites, and a
direct cross-render comparison pass in the same change.

## Rejected alternatives

- Rename only visible prose: leaves public technical debt and ambiguous examples.
- Keep permanent aliases: expands the compatibility surface before a first release.
- Preserve the old DOM prefix: makes the normative runtime contract contradict the
  product namespace indefinitely.
