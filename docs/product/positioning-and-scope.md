---
id: PC-PROD-002
title: PeakCharts Positioning and Alpha Scope
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-SCOPE-001]
evidence: [TEST-CAPABILITY-MATRIX]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Positioning and Alpha Scope

## Positioning

PeakCharts is a deterministic, multi-language chart specification and native SVG
rendering system. Its differentiation is not maximum chart count. It is the ability to
carry one validated chart contract across language and delivery boundaries with
explicit, testable guarantees.

Established browser chart libraries provide broad interactive feature catalogs.
PeakCharts initially serves workflows where native server rendering, canonical output,
auditability, self-contained artifacts, and cross-language equivalence matter more
than browser-only breadth.

## Alpha 1 user outcomes

An authorized Alpha 1 user can:

- Describe a supported line or column chart in one JSON-compatible specification.
- Validate and render it natively in Python or Go.
- Obtain identical canonical SVG for the release conformance corpus.
- Produce self-contained interactive HTML using the shared runtime.
- Apply supported themes, series styling, gradients, patterns, sizing, and declared
  layout controls without leaving the structured specification.
- Inspect known limits, compatibility, qualification evidence, and release provenance.

## In scope

- Chart types `line` and `column` only.
- Grouped, overlaid, normal-stacked, and non-negative percent-stacked columns.
- Categorical x axes and linear numeric y axes.
- Light, dark, and structured custom themes already represented by the schema.
- Static SVG, self-contained HTML, the shared DOM contract, and declared runtime
  interactions.
- Python and Go as the first certified language implementations.

## Not in scope

- The 23 design-only Cartesian chart recipes as released capabilities.
- Arbitrary CSS, raw SVG fragments, executable callbacks, or DOM mutation inside a
  certified profile.
- Automatic text measurement, collision avoidance, or universal label fitting.
- A universal pixel guarantee outside a named certified visual profile.
- Hosted chart rendering, accounts, billing, collaboration, telemetry, or an uptime
  commitment.
- A stable public API or backward-compatibility promise beyond the specific Alpha 1
  release manifest.

## Commercial and legal boundary

The guarantee documents are technical conformance statements, not warranties, service
levels, indemnities, or a substitute for license terms. Any commercial liability,
support obligation, or service commitment must be stated in an executed agreement.
Product documentation MUST use "guarantee" only with a named technical profile and
its applicability conditions.

## Expansion rule

A chart type, language, export engine, or customization feature may enter the public
scope only after its contract, acceptance criteria, conformance fixtures, ownership,
compatibility matrix, performance evidence, security review, and release documentation
are complete. Files on disk and passing examples do not establish support.

