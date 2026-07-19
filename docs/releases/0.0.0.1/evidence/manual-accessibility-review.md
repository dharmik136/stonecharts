---
id: SC-REL-004
title: StoneCharts 0.0.0.1 Manual Accessibility Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-A11Y-001, REQ-RUNTIME-001]
evidence: [TEST-RUNTIME-SMOKE, TEST-RUNTIME-BROWSER, REVIEW-ACCESSIBILITY-MANUAL]
last_reviewed: "2026-07-19"
review_due: "2026-08-19"
supersedes: null
superseded_by: null
---

# Manual Accessibility Review

## Scope

This review covers the StoneCharts chart component in Chromium over local HTTP, using
the live runtime, authored ARIA attributes, keyboard navigation, and the semantic data
table emitted by the HTML renderer.

## Observed tasks

- Confirmed the SVG renders with `role="img"` and a concise accessible name/description.
- Confirmed the legend controls are focusable buttons with `aria-pressed` state.
- Confirmed keyboard navigation reaches the chart, moves between data points, and keeps
  focus on the chart when Escape clears the active datum.
- Confirmed the hidden-series state is reflected through `display:none` and
  `aria-hidden`.
- Confirmed the HTML output includes the visually-hidden data table with matching
  series/category alignment.

## ARIA tree snapshot

The live Chromium ARIA tree for the chart component exposed the expected structure:

```text
- img "Runtime Check. Line chart with 2 series: North, South. Categories from Jan to Mar."
  - text: Runtime Check 0 2 4 6 8 10 Jan Feb Mar
  - button "North" [pressed]
  - button "South" [pressed]
```

The surrounding wrapper exposed the same chart image and the complete semantic table
with row and column headers.

## Result

The component-level accessibility profile is qualified for 0.0.0.1 on the declared
browser/runtime path. The remaining release evidence work is now outside the runtime
and accessibility gate.
