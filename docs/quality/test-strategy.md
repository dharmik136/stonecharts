---
id: SC-QUAL-001
title: StoneCharts Test and Conformance Strategy
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-DET-001, REQ-VAL-001, REQ-CAP-001, REQ-STACK-001, REQ-STACK-002, REQ-RUNTIME-001, REQ-A11Y-001, REQ-SEC-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-VALIDATION-PARITY, TEST-CAPABILITY-MATRIX, TEST-STACK-SIGNED, TEST-PERCENT-DOMAIN, TEST-XSS-ESCAPING, TEST-RUNTIME-BROWSER]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Test and Conformance Strategy

## Principle

StoneCharts tests meaning before serialization and serialization before release. Two
implementations can be wrong in exactly the same way, so byte parity is necessary but
not sufficient.

## Test layers

| Layer | Purpose | Release expectation |
|---|---|---|
| Schema fixtures | Prove the active structural domain | All shared valid/invalid cases pass |
| Semantic invariants | Prove geometry, domains, errors, and state meaning | All mandatory requirements covered |
| Cross-language parity | Compare Python and Go values and errors | Zero unexplained differences |
| Golden serialization | Lock reviewed canonical SVG | Zero unapproved byte changes |
| Property and fuzz tests | Explore unenumerated valid and invalid inputs | No panic, crash, NaN, infinity, or unsafe output |
| Runtime browser tests | Verify DOM state and adaptive behavior | Certified browser matrix passes |
| Accessibility review | Verify real keyboard and assistive-technology tasks | No unresolved release-blocking defect |
| Security tests | Exercise injection and trust boundaries | Zero known critical/high release defect |
| Packaging tests | Install and execute shipped artifacts | Every supported runtime passes |

## Fixture policy

Each defect receives the smallest cross-language fixture that demonstrates its semantic
failure. Semantic assertions inspect domain and geometry invariants before a new golden
is approved. Fixture names and input bytes are stable within a release line.

Existing line goldens are frozen witnesses for shared-substrate changes. Existing
column goldens change only when an approved bug fix necessarily changes canonical
output. Regeneration is a controlled operation: render both languages, directly diff
them, review every golden diff, record hashes, and capture approval in release evidence.

## Required Alpha edge matrix

- Empty, single-point, and uneven series lengths.
- Missing, equal, shorter, and longer category arrays.
- Flat, all-zero, positive-only, negative-only, and mixed-sign values.
- Normal and percent stacking across zero and extreme magnitudes.
- Unicode titles, categories, and series names, including non-BMP characters.
- Long labels and manual-margin boundaries.
- Minimum/maximum dimensions and axis overrides.
- Hostile strings in every text, color, identifier, and style-bearing field.
- Ten-series grouped and stacked stress fixtures.
- Multiple charts with colliding default identifiers.

## Browser matrix

Alpha 1 certifies Chromium on one pinned desktop environment after automated testing.
Firefox, WebKit, mobile viewports, and assistive-technology combinations are recorded
as tested, experimental, or untested; they are not implied by generic "browser"
language. Tests run through a local HTTP server, not `file://`, so the environment
matches normal web security and resource behavior.

## Coverage and pass rules

Line coverage is diagnostic, not a release claim. Requirement coverage is the gate:
every `must` requirement has at least one implemented verification ID, and every
required verification has a passing immutable result. Skips, quarantines, flaky
reruns, and manual exceptions are visible in the release manifest.

No failing test is converted into a new golden without a requirement or ADR explaining
why the previous behavior was wrong.

