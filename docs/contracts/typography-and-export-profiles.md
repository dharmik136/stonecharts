---
id: PC-CON-006
title: Typography, Layout, and Export Profiles
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

# Typography, Layout, and Export Profiles

## Alpha default profile

Alpha 1 emits semantic SVG `<text>` with a declared host font stack. Text positions and
chart geometry are canonical, but glyph selection, shaping, hinting, antialiasing, and
raster pixels are host responsibilities. The profile does not guarantee automatic fit
or pixel identity.

Layout uses deterministic defaults plus planned explicit margins. Margin fields are
finite non-negative pixels. Validation rejects a result that leaves less than the
contracted minimum plot dimensions. Existing defaults remain byte-identical.

## Embedded-font profile

An embedded font can stabilize font files, outlines, and metrics while preserving text
nodes. It does not by itself pin every shaping or rasterization result. A certified
embedded profile MUST:

- Use one prebuilt WOFF2 artifact shared byte-for-byte by all renderers.
- Record font name, version, license, coverage, and SHA-256.
- Prohibit independent runtime subsetting by each language.
- Define fallback and unsupported-codepoint behavior.
- Test all supported embedding and export environments.

No embedded font is selected for Alpha 1 until licensing, size, coverage, and exporter
compatibility are reviewed.

## Certified export profile

A pixel or PDF profile records at least:

- PeakCharts release and canonical SVG hash.
- Export engine, exact version, build or container digest, and flags.
- Font artifact hashes and font configuration.
- Operating system, architecture, locale, timezone, viewport, scale factor, and color
  profile.
- Output format, dimensions, comparison method, and allowed tolerance.

GPU acceleration SHOULD be disabled for a software-rendered reference unless evidence
shows a stable alternative. The selected exporter follows an ADR after a comparative
spike; naming Chromium or librsvg in a draft does not certify either.

## Outlined-text export

Text outlines MAY be offered for static print workflows. The outlined visual artifact
must retain a parallel semantic source or accessible alternative when accessibility is
required. Outlines are not the default interactive profile.

