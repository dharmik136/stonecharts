---
id: SC-REL-013
title: StoneCharts 0.0.0.2 Release Plan
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# 0.0.0.2 Release Plan

## Objective

Ship `bar` as a certified chart type alongside the existing `line`, `column`, and
`area` from `0.0.0.1`. This release is deliberately narrow: one chart type, already
implemented and byte-parity verified in both languages, admitted through the
governed expansion process. It does not reopen any `0.0.0.1` guarantee, does not
add a second language, and does not admit any other chart type.

## Relationship to 0.0.0.1 and the expansion gate

Unlike `0.0.0.1`, this release does not start from zero governance. The foundational
decisions are already resolved and are not re-litigated here:

- `GATE-S5` (admit post-0.0.0.1 expansion) is Done.
- `DEC-014` names bar as the specific chart and `0.0.0.2` as the specific target -
  the exact two things `GATE-S5` required before any implementation could start.
- `REQ-CHART-001` states bar's acceptance contract and is `implemented`: schema,
  both renderers, 5 cross-verified goldens, invalid-fixtures, the direct
  cross-render sweep, accessibility, XSS coverage, and the benchmark matrix are
  all done (chart admission checklist `SC-ARCH-011`, phases 1-9).

What `0.0.0.2` still requires is the same thing Stage 2 onward required for
`0.0.0.1`: formal qualification review, an immutable release evidence pack, and an
authorized tag. That work is tracked by three new gates, continuing the
established `GATE-S*` sequence rather than restarting it:

- `GATE-S6` - 0.0.0.2 qualification gate.
- `GATE-S7` - 0.0.0.2 release-candidate gate.
- `GATE-S8` - 0.0.0.2 release gate.

## Version mapping

| Surface | Version |
|---|---|
| Product and documentation | `0.0.0.2` |
| Python package (PEP 440) | `0.0.0.2` |
| Source release tag | `0.0.0.2` |
| Go module tag | Still not approved - no ecosystem-mapping decision exists (unchanged from `0.0.0.1`; see ADR 0007) |

## What is frozen from 0.0.0.1

`line`, `column`, and `area` are not requalified from scratch. Their existing
goldens, schema entries, and evidence remain exactly as `0.0.0.1` shipped them; this
release only adds bar. If any change to the shared cartesian substrate were needed
to admit bar, it would have been required to keep `line`/`column`/`area` goldens
byte-identical (verified: all existing tests passed throughout bar's
implementation) - the compatibility policy's "existing goldens remain frozen unless
the change is reviewed" rule applied to bar's admission exactly as it would to any
other change.

## Hard release gates (0.0.0.2-specific)

- Active schema and capability manifests expose `line`, `column`, `area`, and `bar`.
- Schema, Python, and Go accept and reject bar specs identically (done -
  `REQ-CHART-001`).
- Bar's canonical output matches its golden corpus byte-for-byte in both
  languages, and the direct cross-render sweep has zero diff (done).
- Bar's accessible data table and XSS/injection coverage match the standard already
  proven for line/column/area (done).
- Bar is in the benchmark workload matrix across all four approved profiles (done).
- Python and Go packages install and execute bar from built artifacts (pending -
  `GATE-S7`).
- Release manifest, hashes, SBOM, provenance status, changelog, support status, and
  known limits are complete and immutable for `0.0.0.2` specifically, not inherited
  unchanged from `0.0.0.1`'s already-tagged `rc.1` pack (pending - `GATE-S7`).

## Approval

The product owner approves scope and product claims. The maintainer approves
technical qualification. While both roles are held by one person, the release
manifest records `review_mode: self`; it does not represent the release as
independently audited.
