---
id: SC-CON-004
title: Browser Runtime Semantics
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-RUNTIME-001, REQ-A11Y-001]
evidence: [TEST-RUNTIME-BROWSER, REVIEW-ACCESSIBILITY-MANUAL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Runtime Semantics

The normative DOM vocabulary is [`spec/svg-contract.md`](../../spec/svg-contract.md).
This document defines observable state and the adaptive boundary of the shared runtime.

## Invariants

- Tooltip title, series, raw value, and color derive from contracted data attributes.
- Pointer and keyboard activation of one datum expose equivalent content.
- Keyboard navigation follows DOM series order and datum order.
- Escape clears the active datum without moving focus and bubbles when no datum is
  active.
- Legend state updates the target series, the legend control state, and authored ARIA
  state consistently.
- Legend controls are focusable and activatable by pointer and keyboard.
- A hidden series is excluded from active navigation until restored.
- Runtime initialization is idempotent for a chart root.

## Adaptive presentation

Tooltip placement is a function of container bounds, viewport, input location, and
tooltip dimensions. 0.0.0.1 guarantees containment and a preferred placement order,
not one screen coordinate across environments. The runtime may use DOM measurement for
this adaptive overlay; it MUST NOT recompute chart data geometry or change canonical
SVG coordinates.

## Input state model

| Input | Result |
|---|---|
| Pointer enter datum | Activate datum, show tooltip/highlight/crosshair |
| Pointer move datum | Reposition tooltip within container |
| Pointer leave datum and tooltip | Clear pointer activation unless focus owns it |
| Focus chart | Activate the first available datum if none is active |
| Arrow keys | Move through available data by declared series/datum order |
| Home / End | Move to first / last datum in current series |
| Escape | Clear active state; retain chart focus |
| Legend activation | Toggle series, update control state, and expose the resulting state |

Tooltip hover persistence, bar highlight geometry, focus appearance, and full browser
qualification remain open until `TEST-RUNTIME-BROWSER` passes.

## Embedding profiles

- **Inline interactive HTML:** full runtime and authored accessibility contract.
- **Standalone interactive SVG:** only features present in that document and allowed by
  the viewer; 0.0.0.1 HTML runtime is not automatically embedded in raw SVG.
- **SVG image (`img`, CSS image, email):** static presentation; internal script and
  interaction are not part of the profile.
- **Converted export:** behavior is static and governed by the selected export profile.

## Event boundary

StoneCharts prevents default behavior only for handled navigation keys. It does not
guarantee browser event object identity or undocumented bubbling details. Host
applications remain responsible for integration conflicts outside the chart wrapper.
