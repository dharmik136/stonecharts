---
chart: development-triangle
tier: certified
date: "2026-08-11"
reviewer: engineering
verdict: CERTIFIED — all SC-CERT gates pass, promoted via DEC-060
---

# Development Triangle Certification Readiness Report

## Current status

```
Tier:            certified
Release:         0.0.0.33
Since:           0.0.0.33
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
| SC-CERT-08 | Evidence baseline | PASS | StoneVerify evaluation-mode evidence bundle generated; Python/Go byte-identical; `evidence-baselines/development-triangle/` committed |

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

All blockers resolved:

1. ~~**SC-CERT-08 (evidence baseline)**~~: Generated 2026-08-11 via `--profile evaluation --from-source`
2. ~~**Actuarial design-partner review**~~: Product owner (Dharmik Shingala) reviewed the contract as domain expert. The triangle contract is faithful to standard actuarial loss development methodology: cumulative/incremental views, development periods, origin-period layout, and link-ratio factors. External review deferred to pilot engagement.
3. ~~**Separate reviewed certification decision**~~: DEC-060 approved

## Remaining P1 work (not blocking certification)

- Hypothesis migration for property tests (currently using `random.Random`)
- Additional Go fuzz seeds (DEC-051 recommends 2+ per type; currently 7 seeds)
- `outOfRange: "overflow"` histogram bin option
- RangePoint renderer migration (Phases 2-3 of DEC-054)
