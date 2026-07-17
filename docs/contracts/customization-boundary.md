---
id: PC-CON-005
title: Customization Boundary
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-CUST-001, REQ-LAYOUT-001, REQ-SEC-001]
evidence: [TEST-VALIDATION-PARITY, TEST-XSS-ESCAPING, TEST-LAYOUT-MARGINS]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Customization Boundary

## Principle

PeakCharts aims for broad visual authorship, not one fixed house style. The certified
path accepts customization as structured, typed, deterministic data. The boundary
protects portability and security; it does not prohibit meaningful branding.

## Layering

Resolved values follow a documented order:

```text
release defaults < named theme < custom theme < chart options < series options
```

Later layers may override only fields allowed by the active schema. Resolution happens
before SVG serialization and is equivalent in every renderer.

## Certified Alpha primitives

- Fixed and responsive chart sizing already represented by the schema.
- Light, dark, and structured custom theme colors and palettes.
- Titles, subtitles, axis titles, categories, limits, gridline styles, legend toggle,
  line width/dash/curve/markers, gradients, patterns, and area opacity.
- Grouped, overlaid, and supported stack modes for columns.
- Manual margins after `REQ-LAYOUT-001` is implemented.

The capability manifest, not the presence of a field in a design document, determines
which primitives are certified.

## Prohibited in certified output

- Raw CSS strings or selectors.
- Raw SVG, HTML, foreign objects, scripts, event-handler attributes, or URL-bearing
  markup supplied by a chart spec.
- Executable formatter callbacks or language-specific objects.
- Direct DOM mutation as part of canonical rendering.
- Viewer-dependent automatic behavior presented as canonical geometry.

Calling this boundary a security sandbox would be inaccurate. Safety comes from
schema validation, contextual encoding, restricted sinks, runtime controls, and
testing. Those controls must be threat-modeled independently.

## Future extension lane

An advanced application may eventually need custom render hooks or raw overlays. Such
an API must be explicit, opt-in, and excluded from canonical and security guarantees
unless its output is normalized and verified. The product may provide both a certified
declarative lane and an unverified expert lane; it must never blur them.

## Compatibility

Adding an optional primitive is backward-compatible only when old specs retain the
same canonical bytes. Changing a default, resolution order, or serialization is a
contract change and requires an ADR, golden review, and release note.

