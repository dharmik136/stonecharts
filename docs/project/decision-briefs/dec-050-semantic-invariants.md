---
id: SC-OPS-020
title: DEC-050 Semantic Invariant Tests
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

# DEC-050 Semantic Invariant Tests

## Decision question

Should StoneCharts add chart-type-specific semantic correctness assertions that verify
the *meaning* of rendered output, beyond byte-identical cross-language parity?

## Background

StoneCharts currently verifies visual integrity through two mechanisms:

1. **Golden fixture tests** — specific example specs produce expected SVG bytes.
2. **Cross-language byte parity** — Python and Go produce identical SVG from the same
   spec.

Both are necessary. Neither is sufficient.

Two renderers implementing the same bug produce byte-identical wrong output. A golden
fixture that encodes a semantic error locks in that error as the "correct" baseline.

### The gap

Cross-language parity proves:

> "Python and Go agree."

Semantic invariants prove:

> "The output is *correct*."

For a product selling visual integrity to regulated industries, the second class of
assurance is what makes the certification story credible.

### Market context

**IFRS 17 requires that visualizations accurately represent underlying calculations.**
Actuarial reporting under IFRS 17 demands transparency across the entire chain from
model to financial statement. A waterfall chart showing reserve movements must balance
mathematically — not just render visually. A histogram of loss distributions must
account for every observation. Regulators expect drill-down and reconciliation, which
means the visualization layer must be provably correct, not just visually consistent.

**No competitor offers semantic correctness guarantees.** Highcharts (40+ chart types,
market leader) tests rendering but not mathematical correctness of chart semantics.
Vega tests grammar compilation but not domain invariants. This is a genuine
whitespace in the market — a charting library that can prove "this waterfall balances"
or "this histogram accounts for all observations" would be unique.

**The insurance analytics market is growing at 15.6% CAGR** (USD 15.4B in 2026,
projected USD 31.8B by 2031). AI-driven actuarial tools and advanced visualization
dashboards are top investment priorities. Buyers in this market care about
correctness and auditability, not just visual appeal.

**The certification gate model becomes a competitive moat.** Enterprise chart libraries
charge $500–$2,000 per developer per year. None offer a formal certification gate
with numbered assurance requirements. The SC-CERT-01 through SC-CERT-08 model
proposed here creates a differentiated product story that regulated buyers will
recognize from their own compliance frameworks (SOC 2, ISO 27001, Solvency II).

### Proposed invariants

Each invariant is a testable mathematical property of the chart type's semantics:

| Chart type | Invariant | ID |
|------------|-----------|-----|
| Histogram | `sum(bin_counts) == len(observations)` (unless explicit overflow policy) | `SC-SEM-001` |
| Waterfall | `closing_total == opening + sum(deltas)` | `SC-SEM-002` |
| Boxplot | `low <= q1 <= median <= q3 <= high` for every datum | `SC-SEM-003` |
| Arearange | `low[i] <= high[i]` for every point | `SC-SEM-004` |
| Error Bar | `low <= value <= high` for every whisker | `SC-SEM-005` |
| Bubble | `z[a] > z[b]` implies `radius[a] >= radius[b]` under the same scale | `SC-SEM-006` |
| Percent Stack | Each non-empty category sums to 100% | `SC-SEM-007` |
| Column Range | `low[i] <= high[i]` for every floating bar | `SC-SEM-008` |
| Pie | `sum(slices) == sum(data)`, no negative values | `SC-SEM-009` |
| Gauge | `gaugeMin <= value <= gaugeMax` | `SC-SEM-010` |

### Two kinds of semantic tests

**Input validation invariants** (SC-SEM-003, 004, 005, 008, 009, 010): The renderer
should reject or warn when input data violates the invariant. These belong in the
validation layer (`validate.py` / `validate.go`).

**Output correctness invariants** (SC-SEM-001, 002, 006, 007): The renderer's
computed output must satisfy the invariant. These are tested by inspecting the
rendered SVG or intermediate state, not by validating input.

## Recommendation

Accept semantic invariants as a new assurance layer and implement them incrementally,
starting with the chart types closest to certification hardening (waterfall, boxplot,
histogram, error-bar, arearange, bullet).

### Implementation

1. **Create `libs/python/tests/test_semantic_invariants.py`** with one test function
   per invariant ID. Each test generates or loads specs that exercise the invariant
   and asserts the mathematical property holds.

2. **Create corresponding Go tests** in `libs/go/render_test.go` under a
   `TestSemanticInvariants` group.

3. **Add input validation** for invariants that are input properties (ordering
   constraints). `validate()` should reject specs where `low > high` in range types,
   negative values in pie, or out-of-order boxplot quartiles.

4. **Add the invariants to the certification gate** as `SC-CERT-06` (see the
   certification gate proposal below).

### Certification gate proposal

A chart should not receive "Certified" status without passing all applicable gates:

| Gate | Name | Description |
|------|------|-------------|
| SC-CERT-01 | Schema strictness | Spec validates against `chart-spec.schema.json` |
| SC-CERT-02 | Cross-language byte parity | Python SVG == Go SVG for all fixtures |
| SC-CERT-03 | Renderer purity | Input spec unchanged after render (DEC-049) |
| SC-CERT-04 | Property/fuzz coverage | Randomized inputs tested (DEC-051) |
| SC-CERT-05 | Adversarial inputs | Edge cases and malformed data handled |
| SC-CERT-06 | Semantic invariants | Chart-specific correctness (this decision) |
| SC-CERT-07 | Accessibility contract | Screen reader + keyboard nav verified |
| SC-CERT-08 | Evidence baseline | StoneVerify evidence pack generated |

This gate model makes certification a **product asset** rather than a label.

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Accept semantic invariants as certification requirement | Each chart type has testable correctness properties | Adds test complexity; catches semantically wrong but byte-identical output |
| Add as advisory tests only | Tests exist but don't block certification | Weaker assurance story |
| Defer | Rely on golden parity only | Two renderers can implement the same bug undetected |

## Stakeholder impact

- **Product:** "We test visual truth, not just visual consistency" becomes a concrete,
  defensible claim for regulated buyers.
- **Engineering:** ~10 new test functions per language, each short and mathematical.
  These can be implemented incrementally per chart type.
- **QA:** Invariants serve as executable acceptance criteria — QA knows exactly what
  "correct" means for each chart type.

## Dependencies

- DEC-052 (strict input validation) handles the input-side invariants.
- DEC-049 (renderer purity) is a prerequisite — semantic tests assume the spec isn't
  modified during rendering.
