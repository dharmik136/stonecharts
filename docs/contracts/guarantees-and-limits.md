---
id: SC-CON-001
title: StoneCharts Guarantees and Limits
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
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

## Known limits

<!-- BEGIN:GENERATED:capabilities -->
- 36 chart types exist in the certified tier, spanning Family A (Cartesian),
  Family B (Polar/radial), and the certified development-triangle chart.
<!-- END:GENERATED:capabilities -->
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

## StoneVerify and renderer resource limits

The Python and Go renderers reject inputs that exceed these concrete limits with a
stable `LIMIT.*` code before producing output:

| Limit | Value | Code |
|-------|-------|------|
| Input specification size | 1,000,000 bytes | `LIMIT.SPEC_BYTES` |
| Series count | 50 series | `LIMIT.SERIES_COUNT` |
| Points per series | 10,000 points | `LIMIT.POINTS_PER_SERIES` |
| Total points | 50,000 points | `LIMIT.TOTAL_POINTS` |
| Label length | 512 Unicode code points | `LIMIT.LABEL_LENGTH` |
| Generated SVG size | 5,000,000 UTF-8 bytes | `LIMIT.SVG_BYTES` |
| Render time per runtime inside StoneVerify | 10 seconds | `LIMIT.RENDER_TIMEOUT` |
| Evidence bundle size | 10,000,000 bytes | `LIMIT.EVIDENCE_BUNDLE_BYTES` |
| Reported finding count | 100 findings | `LIMIT.FINDING_COUNT` |
| Evidence comparison time | 10 seconds | `LIMIT.COMPARISON_TIMEOUT` |

StoneVerify reports resource-limit and timeout failures with exit code `5`.
Python-side renderer limits, Go adapter runtime timeouts, evidence-bundle size
limits, finding-count limits, and comparison timeouts all use stable `LIMIT.*`
codes. A Go adapter process can still report renderer-side `LIMIT.*` text on
stderr; StoneVerify classifies adapter-process failures separately unless and
until the adapter protocol gains a structured error channel.

The render and comparison timeouts can be overridden via the
`STONEVERIFY_RENDER_TIMEOUT` and `STONEVERIFY_COMPARISON_TIMEOUT` environment
variables (positive float, in seconds). The normative default is 10 seconds;
the override exists for deployment environments with known higher
process-startup latency (e.g. Windows hosts where antivirus scanning delays
the first execution of a freshly built adapter binary).

## Presentation advisories

StoneVerify may attach presentation advisories to evidence bundles when it
detects configurations that, while technically valid, carry elevated risk of
visual misinterpretation.

| Advisory | Code | Trigger | Severity |
|----------|------|---------|----------|
| Dual y-axis | `ADV-DUAL-AXIS` | `secondaryYAxis` present in spec | `info` |

Advisories are informational. They do not block rendering, change exit codes,
or appear in the SVG output. They appear only in the evidence bundle's
`manifest.json` under the `presentationAdvisories` key.

## Legal boundary

These are engineering conformance statements. License rights, warranties, liability,
support response, service levels, and indemnities are governed only by applicable
legal agreements.
