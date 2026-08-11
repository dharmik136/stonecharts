---
chart: development-triangle
tier: candidate
date: "2026-08-11"
reviewer: engineering
verdict: NOT CERTIFIED — candidate tier, promotion requires separate reviewed decision
---

# Development Triangle Certification Readiness Report

## Current status

```
Tier:            candidate
Target release:  0.0.0.33
Since:           unreleased
```

## SC-CERT gate assessment

| Gate | Name | Status | Evidence |
|------|------|--------|----------|
| SC-CERT-01 | Schema strictness | PASS | `chart-spec.schema.json` validates triangle, factors, annotations; integer periods with `uniqueItems: true` |
| SC-CERT-02 | Cross-language byte parity | PASS | 7 golden SVGs byte-identical Python/Go; `TestGolden` and `test_development_triangle_goldens` pass |
| SC-CERT-03 | Renderer purity | PASS | `test_renderer_purity.py` covers all dev-triangle fixtures; `TestRendererPurity` in Go covers same |
| SC-CERT-04 | Property/fuzz coverage | PASS | 8 randomized Python cases in `test_property_rendering.py`; 8 Go cases in `TestRandomizedAll36Types`; 7 Go fuzz seeds in `FuzzFromJSON` |
| SC-CERT-05 | Adversarial inputs | PASS | 22 invalid fixtures covering: missing/malformed triangle, boolean/fractional/duplicate/non-increasing periods, boolean/NaN values, shape violations, factor cardinality, annotation targeting |
| SC-CERT-06 | Semantic invariants | PASS | DT-SEM-001 through DT-SEM-010 implemented in both Python (`test_semantic_invariants.py`) and Go (`TestSemanticInvariantsDevelopmentTriangle`) |
| SC-CERT-07 | Accessibility contract | PASS | `aria-label` on annotations; `data-triangle-view`/`data-triangle-value-type` metadata attributes; unit label in accessible summary |
| SC-CERT-08 | Evidence baseline | NOT CHECKED | StoneVerify evidence bundle not yet generated for dev-triangle in evaluation mode; requires --profile evaluation run against all fixtures |

## Contract summary

| Property | Implementation |
|----------|---------------|
| Periods | Non-negative integers, strictly increasing, no duplicates |
| Values | Finite numbers only; booleans/NaN/Infinity rejected |
| Triangle shape | Non-increasing row lengths; rectangular and jagged supported; zero-length rows rejected |
| Latest diagonal | Rightmost populated cell per row (`len(row)-1`) |
| Factors | Supplied by caller; renderer does not compute; `len(values) == len(periods)-1` enforced |
| Unit | Rendered as label below title; included in a11y |
| View/valueType | Metadata attributes (`data-triangle-view`, `data-triangle-value-type`) on SVG group |
| Annotation text | Rendered in `<title>` and `aria-label`; visual marker retained |
| Annotation validation | Unknown origin, unknown period, unpopulated cell all rejected |
| Spec coverage | `test_development_triangle_spec_coverage` proves no public field is silently ignored |

## Blockers for certification promotion

1. **SC-CERT-08 (evidence baseline)**: StoneVerify evidence pack not yet generated for development-triangle examples in evaluation mode
2. **Actuarial design-partner review**: No external actuarial practitioner has reviewed the triangle contract
3. **Separate reviewed certification decision**: Promotion from candidate to certified requires a DEC-level governance decision, not an engineering self-promotion

## Remaining P1 work (not blocking certification)

- Hypothesis migration for property tests (currently using `random.Random`)
- Additional Go fuzz seeds (DEC-051 recommends 2+ per type; currently 7 seeds)
- `outOfRange: "overflow"` histogram bin option
- RangePoint renderer migration (Phases 2-3 of DEC-054)
