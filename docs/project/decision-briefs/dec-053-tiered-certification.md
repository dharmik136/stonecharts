---
id: SC-OPS-023
title: DEC-053 Tiered Certification Model
status: accepted
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.32 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-10"
review_due: "2026-09-10"
supersedes: null
superseded_by: null
---

# DEC-053 Tiered Certification Model

## Decision question

Should StoneCharts replace the flat "all 35 charts are certified" surface with a
tiered model that distinguishes `certified`, `candidate`, and `experimental` chart
types?

## Background

Today `capabilities()` returns all 35 chart types as a flat, undifferentiated list.
The capability matrix, CHARTS.md, and the runtime API all agree — they all say
"certified." There is no inconsistency between these three sources.

However, the 35 chart types are not equally mature:

- **7 chart types** (line, column, area, bar, scatter, bubble, combo) have
  randomized property tests, Go fuzz seeds, and the deepest golden fixture coverage.
- **~8 chart types** (waterfall, boxplot, error-bar, arearange, histogram, bullet,
  columnrange, dumbbell) are commercially high-value for the insurance segment but
  need schema fixes (DEC-052), purity fixes (DEC-049), or expanded test coverage
  (DEC-051) before they meet the proposed SC-CERT certification gate (DEC-050).
- **~20 chart types** have golden-test coverage and byte-identical cross-language
  rendering but lack property/fuzz testing, semantic invariants, and in some cases
  have code-level issues (spec mutation, niche market fit).

Presenting all 35 as equally certified is technically accurate under the current
definition of "certified" (golden tests pass, byte parity holds). But once the
SC-CERT gate model (DEC-050) is adopted, most chart types will not pass all gates
immediately.

### Market context

**Insurance buyers understand tiered certification.** Solvency II uses a tiered
approach to model validation (standard formula vs. internal model). IFRS 17
distinguishes between measurement models (PAA, BBA, VFA). Regulated buyers are
comfortable with — and often expect — explicit maturity tiers rather than a single
"everything works" claim.

**Competitors do not tier their chart types.** Highcharts lists 40+ chart types
as equally available. This is a weakness StoneCharts can exploit: "We tell you
exactly which charts have the deepest assurance, and we show our work."

**13 deeply certified charts is a stronger story than 35 uncategorized.** A
prospect who sees "35 charts, all certified" and then discovers that some mutate
their input spec or silently clamp data will lose trust. A prospect who sees
"13 certified, 8 candidate, 14 experimental — here's what each tier means" will
gain trust.

## Recommendation

Introduce three certification tiers and update `capabilities()`, the capability
matrix, and CHARTS.md to reflect them.

### Tier definitions

| Tier | Meaning | Requirements |
|------|---------|--------------|
| **Certified** | Passes all SC-CERT gates; commercially supported; included in pilot scope | SC-CERT-01 through SC-CERT-08 (DEC-050) |
| **Candidate** | Golden-tested and byte-identical; on the path to certification; may have known schema or semantic gaps | Golden tests pass; byte parity holds; specific gaps documented |
| **Experimental** | Implemented and functional; not commercially supported; may be de-scoped | Golden tests pass; no certification commitment |

### Proposed tier assignments

**Certified (7):** line, column, area, bar, scatter, bubble, combo

**Candidate (8):** waterfall, boxplot, error-bar, arearange, histogram, bullet,
columnrange, dumbbell

**Experimental (20):** lollipop, pie, gauge, solid-gauge, candlestick, funnel,
variwide, timeline, windbarb, streamgraph, vector-plot, xrange, technical-indicators,
flame-chart, radar, polar, wind-rose, nightingale, radial-bar, parliament

### Implementation

1. **Update `capabilities()`** to return tier metadata per chart type:

   ```python
   "chartTypes": {
       "line": {"tier": "certified", "since": "0.0.0.1"},
       "waterfall": {"tier": "candidate", "since": "0.0.0.10"},
       "parliament": {"tier": "experimental", "since": "0.0.0.32"},
   }
   ```

2. **Update `docs/product/capability-matrix.md`** with a tier column.

3. **Update `CHARTS.md`** to show tier labels instead of undifferentiated "certified."

4. **Update the Go `capabilities.go`** to match the Python tier metadata.

5. **Define promotion criteria.** A chart type moves from experimental → candidate
   when it passes SC-CERT-01 and SC-CERT-02. It moves from candidate → certified
   when it passes all SC-CERT gates.

### Candidate promotion path

Once DEC-049, DEC-050, DEC-051, and DEC-052 are implemented, the 8 candidate
charts can be promoted to certified in this order:

1. Waterfall (cleanest code, highest market value)
2. Boxplot (clean schema, strong market fit)
3. Bullet (simple, contained, high KPI value)
4. Histogram (after outOfRange policy fix)
5. Error-bar (after range-point schema fix, DEC-054)
6. Arearange (after range-point schema fix, DEC-054)
7. Columnrange (after range-point schema fix, DEC-054)
8. Dumbbell (after range-point schema fix, DEC-054)

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Three tiers (certified/candidate/experimental) | Clear maturity signal; promotion path defined | Reduces the "35 certified" headline number |
| Two tiers (certified/experimental) | Simpler but loses the "on the path" signal | Candidate charts have no home |
| Keep flat surface | All 35 remain equally "certified" | Undermines trust when gaps are discovered |

## Stakeholder impact

- **Product:** The headline becomes "7 certified + 8 candidate + 20 experimental"
  instead of "35 certified." This is a stronger story for regulated buyers.
- **Engineering:** `capabilities()` changes from a flat list to a dict with metadata.
  CHARTS.md and capability matrix need a tier column. Moderate effort.
- **Sales/pilots:** Pilot scope defaults to certified tier. Candidate charts can be
  included when customer evidence justifies it (per DEC-017's existing clause).

## Dependencies

- DEC-050 (certification gate model) defines what "certified" means.
- DEC-049, DEC-051, DEC-052 define the promotion requirements.

## Files requiring changes

- `libs/python/stonecharts/capabilities.py`
- `libs/go/capabilities.go`
- `docs/product/capability-matrix.md`
- `CHARTS.md`
- `README.md` (chart catalog section)
