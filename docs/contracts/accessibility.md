---
id: PC-CON-007
title: Accessibility Contract
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-A11Y-001, REQ-RUNTIME-001]
evidence: [TEST-RUNTIME-BROWSER, REVIEW-ACCESSIBILITY-MANUAL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Accessibility Contract

## Scope

PeakCharts qualifies the generated chart component, not the complete host page. A host
application can break accessibility through surrounding labels, CSS, focus management,
contrast changes, hidden containers, or incompatible embedding.

Alpha 1 targets applicable WCAG 2.2 Level A and AA component behavior but MUST NOT
claim full conformance until automated and manual qualification is complete.

## Static requirements

- The SVG has a concise accessible name and description when accessibility is enabled.
- Interactive HTML contains a complete semantic data table with safe category and
  series alignment.
- Meaning is not conveyed by color alone where the active style profile offers a
  pattern or equivalent cue.
- Text remains text in the default profile.
- Static SVG remains understandable without JavaScript at the declared level.

## Interactive requirements

- The chart and every interactive legend control are keyboard operable.
- Focus is visible and not trapped.
- Navigation order is stable and documented.
- Tooltip information shown on pointer hover is also available through focus and may be
  dismissed without moving focus.
- Hoverable supplemental content remains available long enough to inspect under the
  approved tooltip behavior.
- Hidden-series state is programmatically exposed.
- Reduced-motion preferences are honored if animation is introduced.

## Assistive-technology boundary

PeakCharts authors SVG/HTML/ARIA inputs and tests them in a declared matrix. Browsers,
operating systems, and assistive technologies generate accessibility trees and speech
output; those products may differ. The guarantee is equivalent authored semantics and
qualified task outcomes, not byte-identical accessibility trees.

## Required qualification record

The release evidence records browser and assistive-technology versions, operating
system, input method, tested tasks, result, defects, and reviewer. Automated checks are
supporting evidence and do not replace keyboard and screen-reader review.

