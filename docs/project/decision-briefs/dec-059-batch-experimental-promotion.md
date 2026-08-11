---
id: SC-OPS-025
title: DEC-059 Batch Experimental-to-Certified Promotion
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.32 and later
requirements: [DEC-050, DEC-053, DEC-058]
evidence: [SC-CERT-01 through SC-CERT-08]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-059 Batch Experimental-to-Certified Promotion

## Decision question

Should the 20 experimental chart types be promoted to certified tier?

## Background

DEC-058 established the precedent for batch promotion, moving 8 candidate chart
types to certified after verifying all SC-CERT gates (01 through 08). The same
gate audit has now been completed for the remaining 20 experimental chart types:

**Cartesian (Family A):** candlestick, lollipop, funnel, variwide, timeline,
windbarb, streamgraph, vector-plot, xrange, technical-indicators, flame-chart

**Polar/Radial (Family B):** pie, gauge, solid-gauge, radar, polar, wind-rose,
nightingale, radial-bar, parliament

All gaps have been closed:

- **SC-CERT-06**: 40 semantic invariant tests added across 20 invariant families
  (SC-SEM-015 through SC-SEM-034) in both Python and Go. All 83 tests in
  `test_semantic_invariants.py` pass; all Go subtests in `TestSemanticInvariants`
  pass. Each invariant family tests a chart-type-specific mathematical
  correctness property appropriate to its data model.

- **SC-CERT-08**: StoneVerify evidence bundles generated for all 20 chart types
  using `--profile evaluation --from-source`. All fixtures across all 20 types
  produce byte-identical Python/Go output. Evidence bundles pass self-check
  integrity verification.

### Gate-by-gate status for all 20 experimental types

| Gate | Name | Status | Notes |
|------|------|--------|-------|
| SC-CERT-01 | Schema strictness | PASS | All 20 types validated by `chart-spec.schema.json` |
| SC-CERT-02 | Cross-language byte parity | PASS | Golden SVGs byte-identical Python/Go for all fixtures |
| SC-CERT-03 | Renderer purity | PASS | Covered by `test_renderer_purity.py` and Go `TestRendererPurity` |
| SC-CERT-04 | Property/fuzz coverage | PASS | Randomized property tests in both runtimes |
| SC-CERT-05 | Adversarial inputs | PASS | `adversarial.json` examples with golden SVGs exist for all 20 types |
| SC-CERT-06 | Semantic invariants | PASS | SC-SEM-015 through SC-SEM-034 implemented |
| SC-CERT-07 | Accessibility contract | PASS | `aria-label`, ARIA roles, data attributes present |
| SC-CERT-08 | Evidence baseline | PASS | Evaluation-mode bundles in `evidence-baselines/` |

### Semantic invariant families

| Code | Chart type | Invariant |
|------|-----------|-----------|
| SC-SEM-015 | candlestick | OHLC bounds: high >= max(open,close), low <= min(open,close) |
| SC-SEM-016 | lollipop | Stem count equals head count (1:1 glyph integrity) |
| SC-SEM-017 | funnel | Slice widths monotonically non-increasing top to bottom |
| SC-SEM-018 | variwide | Bar widths sum to total plot width (proportional layout) |
| SC-SEM-019 | timeline | Event count equals marker count on time axis |
| SC-SEM-020 | windbarb | Barb count equals data point count, rotation within [0,360) |
| SC-SEM-021 | streamgraph | Layer count equals series count, vertical stacking integrity |
| SC-SEM-022 | vector-plot | Arrow count equals data point count |
| SC-SEM-023 | xrange | Span rect count equals data span count |
| SC-SEM-024 | technical-indicators | Indicator overlay count matches spec indicator count |
| SC-SEM-025 | flame-chart | Frame rect count equals data frame count |
| SC-SEM-026 | pie | Slice percentages sum to 100% (within tolerance) |
| SC-SEM-027 | gauge | Pointer count equals series value count |
| SC-SEM-028 | solid-gauge | Fill arc count equals series value count |
| SC-SEM-029 | radar | Vertex count per polygon equals category count |
| SC-SEM-030 | polar | Dot count per series equals category count |
| SC-SEM-031 | wind-rose | Sector count equals directions x series |
| SC-SEM-032 | nightingale | Sector count equals categories x series |
| SC-SEM-033 | radial-bar | Track arc count equals categories x series |
| SC-SEM-034 | parliament | Dot count equals total seat sum |

## Recommendation

Promote all 20 experimental chart types to certified tier in a single batch.
This brings the certified count from 15 to 35.

### Exclusion: development-triangle

Development-triangle remains at candidate tier. It requires:

1. SC-CERT-08 evidence baseline (not yet generated)
2. External actuarial design-partner review
3. Separate reviewed certification decision

See `docs/reviews/development-triangle-certification-readiness.md` for details.

## Implementation

1. Update `spec/capabilities.json` to change tier from `experimental` to
   `certified` for all 20 chart types.
2. Commit SC-CERT-06 semantic invariant tests and SC-CERT-08 evidence baselines.

## Stakeholder impact

- **Product:** Certified tier grows from 15 to 35 chart types. The headline
  becomes "35 certified + 1 candidate (development-triangle)."
- **Sales/pilots:** The full chart portfolio (minus development-triangle) is now
  covered by the certified guarantee, enabling unrestricted pilot positioning
  across all visualization families.
- **Engineering:** No code changes to renderers. Tests and evidence added only.

## Dependencies

- DEC-050 (semantic invariant gate model) — satisfied
- DEC-053 (tiered certification model) — satisfied
- DEC-058 (batch candidate promotion precedent) — satisfied
