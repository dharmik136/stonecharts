---
id: SC-QUAL-003
title: Legacy Robustness and Known Limitations Report
status: superseded
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: historical implementation through 7ccfe63
requirements: [REQ-DET-001, REQ-VAL-001, REQ-SEC-001]
evidence: [TEST-VALIDATION-PARITY, TEST-XSS-ESCAPING]
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: SC-GOV-003
---

# Robustness & Known Limitations

> Superseded as the active risk source by
> [`SC-GOV-003`](governance/risk-register.yaml). Retained as the historical report
> for the adversarial pass that produced these fixes and observations.

Results of an adversarial stress-test pass against the three load-bearing walls
(byte parity, the DOM contract, the spec schema). Each item has a regression test
unless noted.

## Fixed

| # | Risk | Status |
|---|------|--------|
| 1 | **Multi-chart `<defs>` id collision** — two charts with the default `id` both emit `sc-grad-0`; a second chart's `url(#…)` fill resolved to the first's gradient. | **Fixed.** The runtime uniquifies each chart's `<defs>` ids on load (`scc0-…`, `scc1-…`) and rewrites that chart's own refs. Static SVG bytes unchanged. For pure-static multi-embed (no runtime), set a unique `id` per chart. |
| 2 | **Float parity** — `data-y` diverged on floats needing >6 sig figs (Py `%g` vs Go shortest); `int(v)` could overflow Go's int64. | **Fixed.** Both `fmt_num`/`fmtNum` use `%g`/6-sig, guard `NaN`/`Inf` → `"0"`, and bound the integer path to `|v| < 1e18`. Golden: `adversarial.svg`. |
| 3 | **XSS** — color and `id` fields were injected raw into SVG attributes. | **Fixed.** Every color sink (series color, gradient stops, pattern color/bg, custom theme colors + palette) and the chart `id` are escaped. Test: `test_xss_escaping` / `TestXSSEscaping`. |
| 4 | **Malformed specs** — `data:null`, `data:[1,null,3]`, `width:"auto"` crashed Python; and Python-vs-Go handling of malformed numeric fields diverged. | **Fixed — strict, both languages.** A shared validator (`validate.py` / `validate.go`, identical rules + error text) runs before parsing and **rejects** malformed input with structured errors (`$.series[0].marker.radius: expected number, received string`). Defaults apply only when a field is absent — never as a cover for a wrong-typed value. Tests: `test_invalid_fixtures_parity` / `TestInvalidFixturesParity` assert both renderers reject the **same** shared fixtures with the **same** errors. |

## Spec-validation policy (the trust boundary)

> The core guarantee: **the same spec produces the same SVG — or the same
> validation error — in every renderer.**

- **Strict, not coercing.** A property present with the wrong type is an error; it
  is never silently replaced with a default. Silent coercion turns a broken client
  integration into a plausible-but-wrong chart.
- **Numeric fields reject** strings, booleans, null, NaN and Infinity. `width`/
  `height` additionally require an integer value.
- **Defaults apply only on absence.** Absent ≠ malformed.
- **Errors are structured and identical across languages** (path + expected +
  received), verified by the shared `charts/line-basic/invalid-fixtures.json`.
- **Coercion belongs at the boundary, not in the parser.** If a web form or legacy
  source needs lenient input, normalize it in an explicitly-named input adapter
  *before* it becomes a canonical spec — do not weaken the renderer's spec parser.

## Known limitations (mitigations, not bugs)

- **#5 Scale.** The renderer handles 50k points server-side without crashing (~0.5s),
  but the output has one `<circle>` per point and one data-table row per point, so
  the *browser* paint is the ceiling (10k+ DOM nodes stutter). Mitigation today: for
  large series set `marker.enabled: false` (the line is a single `<path>`, cheap) and
  consider `a11y: false` (drops the per-point table). A decimation / downsampling pass
  is a proper future feature, not yet implemented.
- **#6 CSS bleed when embedded.** The visually-hidden data table uses the `!important`
  sr-only pattern, so ordinary host CSS can't reveal it and the chart survives hostile
  global styles (verified). Host CSS using `!important` on `table`/`svg` can still
  interfere — for fully hostile environments, embed in an `<iframe>` or a Shadow-DOM
  container. (Web-Component/Shadow-DOM embedding is a separate planned track.)

## Active resource limits

The current renderers and StoneVerify now enforce the concrete resource limits
documented in [`SC-CON-001`](contracts/guarantees-and-limits.md): specification
bytes, series count, points per series, total points, label length, generated SVG
bytes, render timeout, evidence-bundle bytes, finding count, and comparison
timeout. A limit failure uses a stable `LIMIT.*` code rather than a partial
evidence bundle or an unbounded render attempt.
