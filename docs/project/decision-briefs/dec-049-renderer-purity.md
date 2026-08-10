---
id: SC-OPS-019
title: DEC-049 Renderer Purity Invariant
status: proposed
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

# DEC-049 Renderer Purity Invariant

## Decision question

Should StoneCharts mandate that `render_svg(spec)` / `RenderSVG(spec)` must never
mutate the input `ChartSpec`, and enforce this with a cross-chart test gate?

## Background

An external code review identified that four Python renderers and two Go renderers
mutate their input `ChartSpec` during rendering. For a product selling visual integrity,
rendering should be a pure function:

```
SVG = render(spec)
```

not:

```
spec' = mutate(spec)
SVG   = render(spec')
```

### Confirmed violations

| Renderer | Mutation | Impact |
|----------|----------|--------|
| `xrange.py` / `xrange.go` | Overwrites `x_axis.categories`, pads `series[].data`, sets `y_axis.min`/`y_axis.max` | Calling render twice appends more padding zeros; categories overwritten |
| `flame_chart.py` / `flame_chart.go` | Overwrites `x_axis.categories`, pads `series[].data`, sets `y_axis.min`/`y_axis.max` | Same pattern as xrange |
| `technical_indicators.py` | Sets `y_axis.min`/`y_axis.max` when `None` | Idempotent but still mutates caller's object |
| `vector_plot.py` | Sets `series[].data_points` when falsy | Creates derived data on the caller's spec |

### Why this matters for StoneCharts specifically

1. **Evidence provenance.** StoneVerify hashes the input spec. If the renderer rewrites
   fields before the hash is taken, the evidence bundle's `input-spec.json` may not
   match the caller's original input.
2. **Determinism under repeated render.** If `render_svg(spec)` is called twice, the
   second call may see padded data from the first call. Two calls to the same function
   with the same argument should produce the same result.
3. **Composability.** A caller who renders a spec and then inspects it (for logging,
   auditing, or forwarding) will see the renderer's internal state, not their original
   input.

## Market context

**Immutable architecture is now an industry-standard pattern.** The functional
programming community has converged on the principle that business logic should be
pure and side effects isolated at system boundaries. React, Redux, and event-sourcing
architectures all rely on immutability for correctness and auditability. Facebook
reported 20% rendering efficiency gains from adopting immutable data structures.

**Regulatory requirements now demand reproducible outputs.** U.S. interagency guidance
SR 26-2 (April 2026, Federal Reserve / OCC / FDIC) requires that models produce
reproducible outputs for validation. The EU AI Act classifies risk-scoring AI as
high-risk, requiring explainability and auditability. A renderer that mutates its
input undermines reproducibility — the same spec rendered twice may produce different
results, which fails the reproducibility test.

**Competitors do not offer this guarantee.** Highcharts' export server uses
Puppeteer (browser-based rendering), which introduces non-deterministic factors
(font rendering, layout engine state). Vega's server-side path uses headless
browsers. Neither can make a "pure function" claim about their render pipeline.
StoneCharts' native SVG rendering is architecturally positioned to make this claim
— but only if the renderer is actually pure.

**IFRS 17 and Solvency II reporting require data lineage.** Actuarial reporting
under IFRS 17 requires transparency across the modeling and reporting chain. If a
renderer modifies the input spec, the data lineage between "what the actuary
specified" and "what was rendered" is broken. Regulators will ask about this during
examination.

## Recommendation

Accept the Renderer Purity Invariant as a project-wide engineering rule:

> **Renderers must not modify any field of the input `ChartSpec` or its nested
> objects. Internal transformations operate on copies or local variables.**

### Implementation

1. **Add a purity test** to both test suites that runs every chart type's golden
   examples through `render_svg`, comparing a deep copy of the spec before and after:

   ```python
   before = deep_copy(spec)
   render_svg(spec)
   assert spec == before, f"Renderer mutated spec for {chart_type}"
   ```

   Go equivalent uses `reflect.DeepEqual`.

2. **Fix the four Python renderers** by working on a local copy or computing derived
   values without writing them back to the spec:
   - `xrange.py`: Build lane categories and axis domain in local variables; pass them
     to `render_cartesian` via the frame, not via spec mutation.
   - `flame_chart.py`: Same pattern as xrange.
   - `technical_indicators.py`: Compute y-axis domain locally; pass to frame builder.
   - `vector_plot.py`: Build `data_points` locally instead of writing to `s.data_points`.

3. **Fix the two Go renderers** (`xrange.go`, `flame_chart.go`) with the same approach.

4. **Add the purity test to CI** as a required gate. Name the gate `renderer-purity`.

### Naming

Call this the **Renderer Purity Invariant** and reference it as `SC-CERT-03` in the
certification gate checklist (see DEC-050).

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Accept purity invariant and fix violations | Renderers become pure functions; spec provenance is trustworthy | Requires refactoring 6 files across Python and Go |
| Accept invariant but allow documented exceptions | Some renderers may still mutate under controlled conditions | Weakens the guarantee; harder to reason about |
| Defer | Leave current behavior unchanged | Mutation-based bugs are possible; undermines visual integrity story |

## Stakeholder impact

- **Product:** The purity invariant becomes a product differentiator — StoneCharts can
  claim that rendering never corrupts the input, which matters for audit trails.
- **Engineering:** Six renderer files need refactoring. The fix pattern is
  straightforward — copy-on-read for derived fields.
- **QA:** One new cross-chart test gate catches future violations automatically.

## Scope

This decision covers only the render path (`render_svg` / `RenderSVG`). The
`save_html` convenience wrapper and StoneVerify pipeline are not in scope.

## Files requiring changes

- `libs/python/stonecharts/charts/xrange.py`
- `libs/python/stonecharts/charts/flame_chart.py`
- `libs/python/stonecharts/charts/technical_indicators.py`
- `libs/python/stonecharts/charts/vector_plot.py`
- `libs/go/xrange.go`
- `libs/go/flame_chart.go`
- `libs/python/tests/test_renderer_purity.py` (new)
- `libs/go/render_test.go` (add `TestRendererPurity`)
