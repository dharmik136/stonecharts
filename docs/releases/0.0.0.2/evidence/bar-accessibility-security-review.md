---
id: SC-REL-014
title: StoneCharts 0.0.0.2 Bar Accessibility and Security Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001, REQ-A11Y-001, REQ-SEC-001, REQ-RUNTIME-001]
evidence: [REVIEW-BAR-ACCESSIBILITY-SECURITY, TEST-RUNTIME-BROWSER, TEST-XSS-ESCAPING, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# Bar Accessibility and Security Review

## Scope

`GATE-S6`'s second acceptance criterion requires bar's accessibility and security
coverage to be reviewed against the same standard as line/column/area, with a recorded
review artifact — not inferred from `REQ-CHART-001`'s implementation-time passes. This
review records a fresh, bar-specific pass of both.

## Accessibility

`runtime/bar-browser-qualification.test.js` is a permanent Playwright test (added this
release cycle, wired into the `runtime-browser` CI job) that mirrors
`runtime/browser-qualification.test.js`'s exact assertions against a live bar chart in
headless Chromium instead of line: hover tooltip content, keyboard navigation (arrow
keys move the active point, focus stays on the chart, Escape clears the tooltip without
losing focus), legend toggle by click and by keyboard (Space), and the resulting
`aria-pressed`/`aria-hidden`/`display` state changes.

Re-run fresh for this review: `npm run test:runtime-browser` — both the line and bar
suites pass (2/2).

A live ARIA tree snapshot was captured separately for this review (`page.locator("body")
.ariaSnapshot()` in headless Chromium, bar chart with 2 series x 3 categories):

```text
- 'img "Bar Runtime Check. Bar chart with 2 series: North, South. Categories from Jan to Mar."':
  - text: Bar Runtime Check 0 2 4 6 Jan Feb Mar
  - button "North" [pressed]
  - button "South" [pressed]
- table "Bar Runtime Check":
  - caption: Bar Runtime Check
  - rowgroup:
    - row "Jan Feb Mar":
      - cell
      - columnheader "Jan"
      - columnheader "Feb"
      - columnheader "Mar"
  - rowgroup:
    - row "North 1 2 3":
      - rowheader "North"
      - cell "1"
      - cell "2"
      - cell "3"
    - row "South 4 5 6":
      - rowheader "South"
      - cell "4"
      - cell "5"
      - cell "6"
```

This confirms bar exposes the identical accessible contract as line's reviewed profile
in `manual-accessibility-review.md` (`SC-REL-004`): an `img`-role SVG with a concise
accessible name/description, focusable legend toggle buttons carrying `aria-pressed`,
and a parallel semantic data table with correct row/column headers — orientation
(horizontal bars vs. vertical columns) changes none of the accessibility contract, only
the visual geometry.

## Security

Bar's adversarial fixture (`charts/bar/examples/adversarial.json`, hostile strings
including `"><script>alert(1)</script>` across id/title/subtitle/axis/category/series
fields, plus unsafe style values) is part of the active byte-parity and cross-render
corpus (`tools/check_direct_cross_render.py`) and the shared `test_xss_escaping` /
`TestXSSEscaping` tests, which run across every chart type's adversarial fixture, not
just line's.

Re-run fresh for this review:

- `python -m pytest libs/python/tests -k xss` (`test_xss_escaping`): pass.
- `go test ./... -run TestXSSEscaping` (`TestXSSEscaping`): pass.
- `python tools/check_direct_cross_render.py`: pass, 23 examples (bar's 5 included),
  byte-identical between Python and Go, including bar's adversarial case.

Bar's mark-emission path (`_bar_marks` / `barMarks`) reuses the same value/label
encoding functions as column's (`escape_svg_text`, style allowlist validation) — there
is no bar-specific rendering code that bypasses the shared escaping layer. This is the
same conclusion `security-qualification-review.md` (`SC-REL-011`) reached for line, and
the same enforcement caveat applies unchanged: "blocks release" is procedural
(`GATE-S2`/`GATE-S6`-style gate sequence and the risk-acceptance policy in
`docs/security/threat-model.md`), not a branch-protection technical control, per the
already-disclosed limitation in `SC-REL-011`.

## Result

Bar's accessibility and security coverage is qualified to the same standard as
line/column/area for 0.0.0.2. No bar-specific gap was found in either dimension.
