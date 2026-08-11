---
id: SC-OPS-024
title: DEC-058 Batch Candidate-to-Certified Promotion
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.32 and later
requirements: [DEC-050, DEC-053]
evidence: [SC-CERT-01 through SC-CERT-08]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-058 Batch Candidate-to-Certified Promotion

## Decision question

Should the 8 candidate chart types (histogram, error-bar, arearange, columnrange,
waterfall, bullet, boxplot, dumbbell) be promoted to certified tier?

## Background

DEC-053 established the three-tier certification model and defined the promotion
path: a candidate chart moves to certified when it passes all SC-CERT gates
(01 through 08). At the time of DEC-053, these 8 chart types had gaps in
SC-CERT-06 (semantic invariants) and SC-CERT-08 (evidence baselines).

Both gaps have now been closed:

- **SC-CERT-06**: 16 semantic invariant tests added across 4 invariant families
  (SC-SEM-011 range bounds, SC-SEM-012 error-bar bounds, SC-SEM-013 boxplot
  structure, SC-SEM-014 bullet structure) in both Python and Go. All 43 tests
  in `test_semantic_invariants.py` pass; all Go subtests in
  `TestSemanticInvariants` pass.

- **SC-CERT-08**: StoneVerify evidence bundles generated for all 8 chart types
  using `--profile evaluation --from-source`. All 38 fixtures across all 8 types
  produce byte-identical Python/Go output. Evidence bundles pass self-check
  integrity verification.

### Gate-by-gate status for all 8 candidates

| Gate | Name | Status | Notes |
|------|------|--------|-------|
| SC-CERT-01 | Schema strictness | PASS | All 8 types validated by `chart-spec.schema.json` |
| SC-CERT-02 | Cross-language byte parity | PASS | Golden SVGs byte-identical Python/Go for all fixtures |
| SC-CERT-03 | Renderer purity | PASS | Covered by `test_renderer_purity.py` and Go `TestRendererPurity` |
| SC-CERT-04 | Property/fuzz coverage | PASS | Randomized property tests in both runtimes |
| SC-CERT-05 | Adversarial inputs | PASS | Invalid-input fixtures exist for all 8 types |
| SC-CERT-06 | Semantic invariants | PASS | SC-SEM-011 through SC-SEM-014 implemented |
| SC-CERT-07 | Accessibility contract | PASS | `aria-label`, ARIA roles, data attributes present |
| SC-CERT-08 | Evidence baseline | PASS | Evaluation-mode bundles in `evidence-baselines/` |

## Recommendation

Promote all 8 candidate chart types to certified tier in a single batch:

- histogram
- error-bar
- arearange
- columnrange
- waterfall
- bullet
- boxplot
- dumbbell

This brings the certified count from 7 to 15.

### Exclusion: development-triangle

Development-triangle remains at candidate tier. It requires:

1. SC-CERT-08 evidence baseline (not yet generated)
2. External actuarial design-partner review
3. Separate reviewed certification decision

See `docs/reviews/development-triangle-certification-readiness.md` for details.

## Implementation

1. Update `spec/capabilities.json` to change tier from `candidate` to `certified`
   for all 8 chart types.
2. Commit SC-CERT-06 semantic invariant tests and SC-CERT-08 evidence baselines.

## Stakeholder impact

- **Product:** Certified tier grows from 7 to 15 chart types. The headline
  becomes "15 certified + 1 candidate + 20 experimental."
- **Sales/pilots:** All 8 high-value insurance-segment charts are now covered
  by the certified guarantee, strengthening pilot positioning.
- **Engineering:** No code changes to renderers. Tests and evidence added only.

## Dependencies

- DEC-050 (semantic invariant gate model) — satisfied
- DEC-053 (tiered certification model) — satisfied
