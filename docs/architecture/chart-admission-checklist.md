---
id: SC-ARCH-011
title: StoneCharts Chart Admission Checklist
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: post-0.0.0.1
requirements: [REQ-DET-001, REQ-SEC-001, REQ-A11Y-001, REQ-PERF-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-26"
review_due: "2026-10-26"
supersedes: null
superseded_by: null
---

# Chart Admission Checklist

## Purpose

This is the companion to [`renderer-constitution.md`](renderer-constitution.md)
(`SC-ARCH-002`): that document governs how a new **language** earns certification,
this one governs how a new **chart type** earns certification. Together they are the
"renderer conformance kit and chart admission checklist" `GATE-S5` requires before any
post-0.0.0.1 expansion is authorized.

This checklist is normative for admitting `bar`, `arearange`, `combo`, `histogram`,
`scatter`, or any of the other design-only recipes in `charts/*/design.md`, and for
any chart type not yet designed at all.

## The rule this checklist exists to enforce

From [`docs/product/positioning-and-scope.md`](../product/positioning-and-scope.md)
("Expansion rule"):

> A chart type, language, export engine, or customization feature may enter the public
> scope only after its contract, acceptance criteria, conformance fixtures, ownership,
> compatibility matrix, performance evidence, security review, and release
> documentation are complete. Files on disk and passing examples do not establish
> support.

## Why this checklist exists (the concrete failure it prevents)

During the 0.0.0.1 qualification pass, a branch accumulated full Python and Go
renderers, golden fixtures, and schema/capability registrations for `bar`,
`arearange`, `combo`, `histogram`, and `scatter` - all without an approved `DEC-*` or
`REQ-*` decision. The code worked. The tests passed. It was still a governance
violation: those five chart types became live, callable capabilities with no decision
trail, directly contradicting `AGENTS.md`'s "do not widen chart scope... unless
approved first" and Stage 0's own exit criterion that "no unapproved chart-type... 
implementation is active." The fix required removing five languages' worth of
renderer code, golden fixtures, and schema entries, and restoring the affected charts
to their prior informative-only state. This checklist exists so that work never has to
happen again: **do the phases in order, and phase 0 blocks every phase after it.**

## Admission phases

A chart type may only progress to the next phase once the current phase's items are
complete and, where marked, approved. **No implementation work (phase 3 onward) starts
before phase 0 is closed.**

### Phase 0 - Decision (blocking gate)

- [ ] A `DEC-*` decision record in `docs/project/decisions.md` names the specific
      chart type(s) being admitted.
- [ ] A `REQ-*` requirement entry exists in `docs/requirements/registry.yaml` stating
      the acceptance contract for this chart type.
- [ ] A Project item (`WORK-*` or `REQ-*`) exists in `docs/project/backlog.yaml` and is
      synced to the GitHub Project (`python tools/check_github_project.py --apply`).
- [ ] The decision names the target release (which release this chart ships in - see
      `GATE-S5` acceptance criterion "expansion order and next release target are
      approved").

**Nothing below this line may be implemented until every box above is checked and the
decision is genuinely approved (not just drafted) by both the product-owner and
maintainer roles.**

### Phase 1 - Design

- [ ] `charts/<id>/design.md` exists and is current (most design-only recipes already
      have this; verify it against the current schema, not an old draft).
- [ ] The design names every field the chart introduces beyond the existing schema,
      and how each interacts with existing customization (themes, gradients, patterns,
      layout margins).

### Phase 2 - Contract

- [ ] `spec/chart-spec.schema.json`: the chart type is added to the `type` enum, and
      any chart-specific properties are added with full validation (`type`, `enum`,
      `minimum`, etc. - not left permissive).
- [ ] `spec/svg-contract.md` is updated if the chart introduces a new DOM shape not
      already covered.
- [ ] Orphaned-schema check: if an earlier attempt left schema properties for this
      chart type that were never removed, verify they still match the current design
      (schema drift silently reintroducing removed scope is exactly the phase-0
      failure mode above, in reverse).

### Phase 3 - Implementation (both languages)

- [ ] Python renderer (`libs/python/stonecharts/charts/<id>.py`).
- [ ] Go renderer (`libs/go/<id>.go`).
- [ ] Both registered in the dispatch table (`render.py`/`render.go`) and the
      capabilities manifest (`capabilities.py`/`capabilities.go`) - **in the same
      commit or PR as the decision sync, not before it.**
- [ ] Shared substrate reuse per `renderer-constitution.md`: stacking, band layout,
      and point normalization come from the shared transform layer, not a
      chart-local reimplementation.

### Phase 4 - Conformance fixtures

- [ ] Golden SVG fixtures (`charts/<id>/golden/*.svg`) for every documented variant
      (basic, themed-dark, and any chart-specific variant named in the design).
- [ ] `charts/<id>/invalid-fixtures.json` covering every validation rule the schema
      and both validators enforce, with identical expected errors in both languages.
- [ ] Adversarial/edge-case example (XSS payloads in user-facing strings, extreme
      data values, empty/degenerate series).

### Phase 5 - Cross-language verification

- [ ] `libs/python/tests/test_golden.py` and `libs/go/render_test.go` both updated to
      exercise every new golden.
- [ ] `tools/check_direct_cross_render.py`'s `ACTIVE` corpus includes the new chart
      type (this exact omission - for `area` - was found and fixed during 0.0.0.1
      qualification; do not repeat it).
- [ ] `tools/check_fuzz_property.py` corpus extended if the chart introduces a new
      data shape (not just new styling of the existing `number[]` shape).

### Phase 6 - Accessibility

- [ ] The accessible data table (`_data_table`/`dataTable`) correctly represents the
      chart's data shape. If the chart's `series[].data` stops being a plain
      `number[]` (e.g. `{low,high}` ranges, `{x,y}` points), the table MUST be
      generalized in lockstep in both languages - it must not silently coerce or drop
      values.
- [ ] `TEST-RUNTIME-BROWSER` and `TEST-RUNTIME-SMOKE` harnesses exercise the new mark
      type's keyboard/focus/tooltip behavior if it introduces new interactive
      elements.

### Phase 7 - Security

- [ ] Every new user-facing string field is covered by the XSS/injection test
      (`test_xss_escaping`/`TestXSSEscaping`).
- [ ] Any new style-bearing field (color, pattern, gradient) has explicit validation
      or safe encoding, not implicit trust.

### Phase 8 - Performance

- [ ] The chart type is added to the benchmark workload matrix
      (`libs/python/benchmark.py` / `libs/go/cmd/benchmark/main.go`) across the
      approved Small/Business/Dense/Stress profiles.
- [ ] A fresh baseline is recorded in `docs/releases/<release>/evidence/` following the
      pattern in `performance-baseline-review.md`.

### Phase 9 - Documentation

- [ ] `README.md` status table adds a row for the chart.
- [ ] `docs/product/positioning-and-scope.md` "In scope" section is updated - and
      cross-checked against every other document that states scope (`backlog.yaml`
      decision titles, the release plan's Objective line, this file). The 0.0.0.1
      qualification found the exact same scope claim stated four different ways in
      four documents, three of them stale. Update all of them in the same change.
- [ ] `CHARTS.md`'s status column moves from "Design ✅ · render deferred" to
      "Design ✅ · render ✅".
- [ ] `docs/architecture/renderer-constitution.md` admission-gate item 5 (the
      language-conformance corpus list) is updated to include the newly certified
      chart type, so future language renderers are held to the correct, current
      corpus.

### Phase 10 - Release evidence

- [ ] `tools/build_release_evidence.py` regenerated against the commit that completes
      phases 1-9, and `tools/check_release_evidence.py` passes.
- [ ] The chart's admission is recorded in `CHANGELOG.md`.

## Closing the loop

Only after every phase above is complete does the chart type's Project item move to
`Done`, and only then may product documentation describe the chart as supported. Per
the expansion rule: files on disk and passing examples do not establish support - a
closed decision record and a green conformance corpus do.
