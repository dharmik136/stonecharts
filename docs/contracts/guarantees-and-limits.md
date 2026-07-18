---
id: SC-CON-001
title: StoneCharts Guarantees and Limits
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-DET-001, REQ-VIS-001, REQ-CUST-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, REVIEW-VISUAL-PROFILE]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Guarantees and Limits

## Applicability

Every guarantee applies only to an immutable release, active schema version, certified
renderer version, supported capability set, and stated environment profile. Modified
output, experimental fields, design-only chart types, downstream converters, and
unlisted environments are outside the guarantee unless explicitly included.

## G1: Canonical output

For a valid supported spec in the release conformance corpus, certified renderers MUST
emit the same UTF-8 SVG bytes. Canonical bytes include XML structure, element and
attribute order, identifiers, escaped text, numeric strings, whitespace, and line
endings. SHA-256 equality is the release check.

This is currently fixture-bounded. StoneCharts does not claim that untested inputs are
proven merely because covered fixtures pass. Property tests and corpus breadth expand
confidence without changing the scope wording.

## G2: Behavioral parity

Self-contained HTML MUST expose the same contracted DOM attributes, tooltip content,
navigation transitions, legend state, and authored accessibility semantics. Adaptive
presentation MAY vary with declared environment inputs. StoneCharts does not guarantee
identical tooltip screen coordinates, browser event internals, or platform-generated
accessibility trees.

## G3: Certified visual profile

Pixel qualification exists only for a named profile recording font artifact, export
engine and version, operating system or container digest, viewport, device scale,
locale, timezone, color configuration, flags, and comparison tolerance. Identical SVG
outside that profile is not a pixel guarantee.

0.0.0.1 has no certified pixel profile until its exporter evaluation and visual
evidence are approved.

## G4: Customization boundary

Structured schema fields covered by the active capability manifest remain eligible for
G1-G3 as stated. Arbitrary CSS, raw SVG/HTML, script callbacks, unsupported fonts, DOM
mutation, and third-party plugins are outside certified guarantees. A future escape
hatch may be useful, but it must be labeled unverified and isolated from the certified
path.

## Compatibility policy

StoneCharts uses a separate compatibility policy to govern future public-surface
changes. `0.0.0.1` may still carry controlled pre-release breaks while the release is
under qualification, but every post-release public change must follow the approved
compatibility policy and its evidence requirements.

## 0.0.0.1 known limits

- Only line and column are released chart types.
- Layout uses deterministic defaults and manual margins; there is no automatic text
  measurement, wrapping, collision avoidance, or legend pagination.
- The default font stack depends on the host viewer and has no pixel identity promise.
- Locale-specific number and date formatting are not released capabilities.
- Interactivity requires an inline or standalone interactive document context; SVG
  used as an image is a static profile.
- Accessibility is a component contract and does not establish whole-page WCAG
  conformance for a host application.
- PDF, PNG, and email conversion are downstream until a certified export profile is
  published.

## Legal boundary

These are engineering conformance statements. License rights, warranties, liability,
support response, service levels, and indemnities are governed only by applicable
legal agreements.
