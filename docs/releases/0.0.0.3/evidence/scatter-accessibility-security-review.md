---
id: SC-REL-018
title: StoneCharts 0.0.0.3 Scatter Accessibility and Security Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.3
requirements: [REQ-CHART-002, REQ-A11Y-001, REQ-SEC-001, REQ-RUNTIME-001]
evidence: [REVIEW-SCATTER-ACCESSIBILITY-SECURITY, TEST-RUNTIME-BROWSER, TEST-XSS-ESCAPING, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-27"
review_due: "2026-08-27"
supersedes: null
superseded_by: null
---

# Scatter Accessibility and Security Review

## Scope

`GATE-S9`'s second acceptance criterion requires scatter's accessibility and security
coverage to be reviewed against the same standard as line/column/area/bar, with a
recorded review artifact - not inferred from `REQ-CHART-002`'s implementation-time
passes. Scatter carries a stricter bar than bar's admission did: it changes the
`data-x` contract (numeric, not a category label) and the accessible data table's
shape (long-format `(x, y)` rows, not a coerced single number per category), so both
need their own direct proof, not an assumption that the existing line/bar reviews
still apply unchanged.

## Accessibility

`runtime/scatter-browser-qualification.test.js` is a permanent Playwright test (added
this release cycle, wired into the `runtime-browser` CI job) that mirrors
`runtime/browser-qualification.test.js`'s exact assertions against a live scatter
chart in headless Chromium instead of line, built on explicit point-model
(`[x,y]` positional) data rather than the bare-number fast path: hover tooltip
content, keyboard navigation (arrow keys move the active point, focus stays on the
chart, Escape clears the tooltip without losing focus), legend toggle by click and by
keyboard (Space), and the resulting `aria-pressed`/`aria-hidden`/`display` state
changes. It additionally asserts scatter emits no `.sc-series-line` path (unconnected
points) and that `.sc-point` selectors key on the numeric `data-x` value ("10", "20"),
not a category label - the single biggest `data-*` contract difference from line/bar.

This test caught a real bug during development: the typed Python construction path
(`ChartSpec(series=[Series(data=[[10,1],[20,2]])])`, documented in
`charts/scatter/design.md`'s "Generate it - typed" section) rendered **zero points**
because point-model normalization only ran inside `ChartSpec.from_dict()`, not the
dataclass constructor. Fixed with a `ChartSpec.__post_init__` that normalizes
`data_points` for the typed path too (`libs/python/stonecharts/spec.py`), and the
symmetric gap in Go (`libs/go/scatter.go`'s `renderScatterSVG` now backfills
`DataPoints` from `Data` when a caller builds a `*ChartSpec` struct literal directly
instead of going through `FromJSON`). Both fixes were verified before this review was
written, not after.

Re-run fresh for this review: `npm run test:runtime-browser` - all three suites (line,
bar, scatter) pass (3/3).

A live ARIA tree snapshot was captured separately for this review (`page.locator("body")
.ariaSnapshot()` in headless Chromium, scatter chart with 2 series x 3 points each,
positional `[x,y]` data):

```text
- 'img "Scatter Runtime Check. Scatter chart with 2 series: North, South."':
  - text: Scatter Runtime Check 1 2 3 4 5 6 10 15 20 25 30 X
  - button "North" [pressed]
  - button "South" [pressed]
- table "Scatter Runtime Check":
  - caption: Scatter Runtime Check
  - rowgroup:
    - row "Series X Y":
      - columnheader "Series"
      - columnheader "X"
      - columnheader "Y"
  - rowgroup:
    - row "North 10 1":
      - rowheader "North"
      - cell "10"
      - cell "1"
    - row "North 20 2":
      - rowheader "North"
      - cell "20"
      - cell "2"
    - row "North 30 3":
      - rowheader "North"
      - cell "30"
      - cell "3"
    - row "South 10 4":
      - rowheader "South"
      - cell "10"
      - cell "4"
    - row "South 20 5":
      - rowheader "South"
      - cell "20"
      - cell "5"
    - row "South 30 6":
      - rowheader "South"
      - cell "30"
      - cell "6"
```

This confirms scatter exposes the same `img`-role SVG contract as line/bar's reviewed
profile, and proves the accessible data table was genuinely generalized (§5.4b-DT):
a long-format table with one row per `(series, x, y)` point, not a coerced or dropped
value - the shape `_data_table`'s scatter branch (`render.py`) and `scatterDataTable`
(Go `render.go`) were built to produce.

## Security

Scatter's adversarial fixture (`charts/scatter/examples/adversarial.json`, hostile
strings including `"><script>alert(1)</script>` across id/title/subtitle/xAxis
title/series name fields) is part of the active byte-parity and cross-render corpus
(`tools/check_direct_cross_render.py`) and the shared `test_xss_escaping` /
`TestXSSEscaping` tests, which run across every chart type's adversarial fixture, not
just line's.

Re-run fresh for this review:

- `python -m pytest libs/python/tests -k xss` (`test_xss_escaping`): pass.
- `go test ./... -run TestXSSEscaping` (`TestXSSEscaping`): pass.
- `python tools/check_direct_cross_render.py`: pass, 29 examples (scatter's 6
  included), byte-identical between Python and Go, including scatter's adversarial
  case.

Scatter also introduces a genuinely new validation surface - the point-model element
type (`number | [x,y] | {x,y}`) - which is a **new** avenue for structurally malformed
input, not just hostile strings in already-validated fields. `charts/scatter/
invalid-fixtures.json` covers it directly: a missing `y` field, an unknown field on
the object form, a wrong-length positional array, and a non-numeric array element -
each with an exact expected error, verified identical between the JSON schema, the
Python validator, and the Go validator (`test_invalid_fixtures_parity`,
`TestInvalidFixturesParity`, and the schema `oneOf`/`allOf` conditional in
`spec/chart-spec.schema.json`). Scatter's mark-emission path (`_scatter_marks` /
`scatterMarks`) reuses the same escaping/formatting functions as line's marker builder
(`esc`, `fmt_num`) - there is no scatter-specific rendering code that bypasses the
shared escaping layer. This is the same conclusion `security-qualification-review.md`
(`SC-REL-011`) reached for line, and the same enforcement caveat applies unchanged:
"blocks release" is procedural (the governed gate sequence and the risk-acceptance
policy in `docs/security/threat-model.md`), not a branch-protection technical control,
per the already-disclosed limitation in `SC-REL-011`.

## Result

Scatter's accessibility and security coverage is qualified to the same standard as
line/column/area/bar for 0.0.0.3, including direct proof of its two genuinely new
surfaces (numeric `data-x` / long-format data table, and the point-model validation
grammar). Two real gaps were found and fixed during this review's own preparation
(the typed-construction point-model gap in both languages), not left for later.
