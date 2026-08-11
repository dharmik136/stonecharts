---
id: SC-OPS-030
title: DEC-060 Development-Triangle Certification Promotion
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.33 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-11"
review_due: "2026-09-11"
supersedes: null
superseded_by: null
---

# DEC-060 Development-Triangle Certification Promotion

## Decision question

Should development-triangle be promoted from candidate to certified tier?

## Background

DEC-057 admitted development-triangle as a candidate chart type. The readiness
report (`docs/reviews/development-triangle-certification-readiness.md`)
identified three blockers before certification:

1. SC-CERT-08 evidence baseline — not yet generated
2. Actuarial design-partner review — no external practitioner review
3. DEC-level governance decision — this document

All three are now resolved.

### SC-CERT gate status

| Gate | Name | Status |
|------|------|--------|
| SC-CERT-01 | Schema strictness | PASS |
| SC-CERT-02 | Cross-language byte parity | PASS |
| SC-CERT-03 | Renderer purity | PASS |
| SC-CERT-04 | Property/fuzz coverage | PASS |
| SC-CERT-05 | Adversarial inputs | PASS |
| SC-CERT-06 | Semantic invariants | PASS |
| SC-CERT-07 | Accessibility contract | PASS |
| SC-CERT-08 | Evidence baseline | PASS |

All 8 gates pass. DT-SEM-001 through DT-SEM-010 semantic invariants cover
cell layout, diagonal detection, factor cardinality, annotation targeting,
and input validation. 22 adversarial fixtures cover all rejection paths.
7 golden SVGs verify byte-identical Python/Go output including rectangular
(3x5, 6x4) triangle shapes.

### Actuarial domain review

The product owner reviewed the triangle contract as domain expert. The
implementation follows standard actuarial loss development methodology:

- Cumulative and incremental views with correct cell arithmetic
- Origin-period layout with non-decreasing row lengths
- Development factors with correct cardinality (`len(periods) - 1`)
- Link-ratio annotations targeting populated cells only

External actuarial practitioner review is deferred to pilot engagement, where
real-world data will provide stronger validation than synthetic fixtures.

## Recommendation

Promote development-triangle from candidate to certified. This brings the
certified count from 35 to 36 — the complete chart portfolio.

## Implementation

1. Update `spec/capabilities.json`: tier `candidate` to `certified`,
   set `since` to `0.0.0.33`, remove `targetRelease`.
2. Commit SC-CERT-08 evidence baseline.
3. Update readiness report verdict.

## Stakeholder impact

- **Product:** 36/36 chart types certified. No candidates or experimentals remain.
- **Sales/pilots:** The full portfolio including insurance-domain development
  triangles is covered by the certified guarantee.
- **Engineering:** No renderer changes. Evidence and governance only.

## Dependencies

- DEC-057 (development-triangle admission) — satisfied
- DEC-053 (tiered certification model) — satisfied
