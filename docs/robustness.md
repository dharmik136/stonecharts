# Robustness & Known Limitations

Results of an adversarial stress-test pass against the three load-bearing walls
(byte parity, the DOM contract, the spec schema). Each item has a regression test
unless noted.

## Fixed

| # | Risk | Status |
|---|------|--------|
| 1 | **Multi-chart `<defs>` id collision** — two charts with the default `id` both emit `pk-grad-0`; a second chart's `url(#…)` fill resolved to the first's gradient. | **Fixed.** The runtime uniquifies each chart's `<defs>` ids on load (`pkc0-…`, `pkc1-…`) and rewrites that chart's own refs. Static SVG bytes unchanged. For pure-static multi-embed (no runtime), set a unique `id` per chart. |
| 2 | **Float parity** — `data-y` diverged on floats needing >6 sig figs (Py `%g` vs Go shortest); `int(v)` could overflow Go's int64. | **Fixed.** Both `fmt_num`/`fmtNum` use `%g`/6-sig, guard `NaN`/`Inf` → `"0"`, and bound the integer path to `|v| < 1e18`. Golden: `adversarial.svg`. |
| 3 | **XSS** — color and `id` fields were injected raw into SVG attributes. | **Fixed.** Every color sink (series color, gradient stops, pattern color/bg, custom theme colors + palette) and the chart `id` are escaped. Test: `test_xss_escaping` / `TestXSSEscaping`. |
| 4 | **Malformed specs** — `data:null`, `data:[1,null,3]`, `width:"auto"` crashed Python. | **Fixed.** `_num`/`_int` coerce (bad → `0.0` / default). Both languages produce valid SVG or a clean error, never a panic. Test: `test_malformed_no_crash` / `TestMalformedNoPanic`. |

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
