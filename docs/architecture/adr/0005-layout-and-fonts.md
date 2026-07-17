---
id: PC-ARCH-ADR-0005
title: Use Manual Alpha Layout and Tiered Font Profiles
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1 and later
requirements: [REQ-LAYOUT-001, REQ-VIS-001]
evidence: [TEST-LAYOUT-MARGINS, REVIEW-VISUAL-PROFILE]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# ADR 0005: Use Manual Alpha Layout and Tiered Font Profiles

## Context

Host text metrics, shaping, and rasterization vary. Alpha 1 needs usable label space
without adding a heavy shaping dependency or weakening canonical output.

## Decision

Alpha 1 uses fixed deterministic defaults plus validated manual margins. It performs
no automatic text fitting, wrapping, ellipsis, or margin expansion. Overflow behavior
and the minimum remaining plot area are explicit contract rules.

The default profile uses semantic SVG text and a declared host font stack without a
pixel guarantee. An optional embedded-font profile may later use one prebuilt,
licensed, hashed WOFF2 artifact copied identically by every renderer. Dynamic
per-language font subsetting is prohibited in certified output. Pixel qualification
requires a pinned exporter and full environment profile.

## Consequences

Alpha output stays lightweight and deterministic while users can fix known label
constraints. Embedded fonts improve metric consistency but are not described as
universal raster identity. Text outlines remain an export-only option with a parallel
semantic alternative when required.

## Rejected alternatives

- Host measurement in each language: not parity-safe.
- HarfBuzz in Alpha 1: valuable later, disproportionate now.
- Universal text outlines: weakens selection, search, and intrinsic text semantics.

