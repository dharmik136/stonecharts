---
id: SC-REL-022
title: StoneCharts 0.0.0.4 Bubble Accessibility and Security Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4
requirements: [REQ-CHART-003, REQ-A11Y-001, REQ-SEC-001, REQ-RUNTIME-001]
evidence: [REVIEW-BUBBLE-ACCESSIBILITY-SECURITY, TEST-RUNTIME-BROWSER, TEST-XSS-ESCAPING, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-28"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# Bubble Accessibility and Security Review

## Scope

`GATE-S12`'s second acceptance criterion requires bubble's accessibility and security
coverage to be reviewed against the same standard as line/column/area/bar/scatter,
with a recorded review artifact - not inferred from `REQ-CHART-003`'s
implementation-time passes. Bubble carries a stricter bar than scatter's admission in
one respect: it adds a `data-z` attribute and a third accessible-table column, and it
introduces a genuinely new interaction contract (the radius does NOT grow on hover,
unlike line/scatter), so all three need direct proof.

## Accessibility

`runtime/bubble-browser-qualification.test.js` is a permanent Playwright test (added
this release cycle, wired into the `runtime-browser` CI job) that mirrors
`runtime/browser-qualification.test.js`'s exact assertions against a live bubble chart
in headless Chromium, built on explicit point-model (`[x,y,z]` positional) data: hover
tooltip content, keyboard navigation, legend toggle by click and by keyboard (Space),
and the resulting `aria-pressed`/`aria-hidden`/`display` state changes. It additionally
asserts:

- Bubble emits no `.sc-series-line` path (unconnected circles) and every mark carries
  both `.sc-point` and `.sc-bubble` classes.
- The size-scale is honored end to end in a live browser: with z values `100` and
  `5000` across two series, the rendered `r` attributes are exactly `4` and `32`
  (`RMIN`/`RMAX`), matching the pinned formula, not just the unit-tested Python/Go
  output.
- `data-r-hover` equals `data-r` for every bubble, and this holds after keyboard
  navigation moves the active point - the radius never changes on focus, unlike
  line/scatter's marker growth. Shipping a growing bubble on hover would misrepresent
  its own encoded magnitude (a bubble's whole point is that its size already carries
  meaning).

Re-run fresh for this review: `npm run test:runtime-browser` - all four suites (line,
bar, scatter, bubble) pass (4/4).

A live ARIA tree snapshot was captured separately for this review (`page.locator("body")
.ariaSnapshot()` in headless Chromium, bubble chart with 2 series x 2 points each,
positional `[x,y,z]` data, z spanning the full 100-5000 range):

```text
- 'img "Bubble Runtime Check. Bubble chart with 2 series: North, South."':
  - text: Bubble Runtime Check 1 2 3 4 10 12 14 16 18 20 X
  - button "North" [pressed]
  - button "South" [pressed]
- table "Bubble Runtime Check":
  - caption: Bubble Runtime Check
  - rowgroup:
    - row "Series X Y Z":
      - columnheader "Series"
      - columnheader "X"
      - columnheader "Y"
      - columnheader "Z"
  - rowgroup:
    - row "North 10 1 100":
      - rowheader "North"
      - cell "10"
      - cell "1"
      - cell "100"
    - row "North 20 2 5000":
      - rowheader "North"
      - cell "20"
      - cell "2"
      - cell "5000"
    - row "South 10 3 2500":
      - rowheader "South"
      - cell "10"
      - cell "3"
      - cell "2500"
    - row "South 20 4 100":
      - rowheader "South"
      - cell "20"
      - cell "4"
      - cell "100"
```

This confirms bubble exposes the same `img`-role SVG contract as line/scatter's
reviewed profile, and proves the accessible data table was genuinely generalized
(§5.4b-DT) a second time: a long-format table with a `Z` column added on top of
scatter's `(x, y)` shape, not a coerced or dropped value.

## Security

Bubble's adversarial fixture (`charts/bubble/examples/adversarial.json`, hostile
strings including `"><script>alert(1)</script>` across id/title/subtitle/xAxis
title/series name fields) is part of the active byte-parity and cross-render corpus
(`tools/check_direct_cross_render.py`) and the shared `test_xss_escaping` /
`TestXSSEscaping` tests.

Re-run fresh for this review:

- `python -m pytest libs/python/tests -k xss` (`test_xss_escaping`): pass.
- `go test ./... -run TestXSSEscaping` (`TestXSSEscaping`): pass.
- `python tools/check_direct_cross_render.py`: pass, 34 examples (bubble's 5
  included), byte-identical between Python and Go, including bubble's adversarial case.

Bubble introduces a second new validation surface after scatter's: the `{x,y,z}`
point-model element type, with `z` required (not optional) on the object form.
`charts/bubble/invalid-fixtures.json` covers it directly: a missing `z` field, an
unknown field on the object form, a wrong-length positional array, and a non-numeric
array element - each with an exact expected error, verified identical between the
JSON schema, the Python validator, and the Go validator. Bubble's size-scale itself
(`size_scale`/`sizeScale`) is pure arithmetic over already-validated numeric `z`
values with an explicit degenerate-domain guard before any divide - there is no
new string-handling or injection surface in that computation. Bubble's mark-emission
path reuses the same escaping/formatting functions as scatter's (`esc`, `fmt_num`) -
there is no bubble-specific rendering code that bypasses the shared escaping layer.
The same enforcement caveat from `security-qualification-review.md` (`SC-REL-011`)
applies unchanged: "blocks release" is procedural, not a branch-protection technical
control.

## Result

Bubble's accessibility and security coverage is qualified to the same standard as
line/column/area/bar/scatter for 0.0.0.4, including direct proof of its two genuinely
new surfaces (the size-scale honored live in a browser, and the `{x,y,z}` validation
grammar with `z` required).
