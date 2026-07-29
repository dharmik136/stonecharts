---
id: SC-PROD-002-ANTIGRAVITY
title: StoneCharts Positioning and Alpha Scope (Antigravity Version)
status: superseded
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-SCOPE-001]
evidence: [TEST-CAPABILITY-MATRIX]
last_reviewed: "2026-07-30"
review_due: "2027-07-30"
supersedes: null
superseded_by: SC-PROD-002
---

# Positioning and Alpha Scope

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

## Positioning

StoneCharts is a deterministic visualization infrastructure layer for teams that must reproduce, validate, and audit the same chart across backend languages and reporting environments—without relying on a browser rendering service. Its differentiation is not maximum chart count or interactive browser breadth. It is the ability to carry one governed, auditable chart contract across language and delivery boundaries with explicit, testable guarantees.

Established browser chart libraries provide broad interactive feature catalogs. StoneCharts serves workflows where native server rendering, deterministic canonical output, auditability, self-contained interactive HTML, and cross-language equivalence matter more than browser-only visualization.

## 0.0.0.1 user outcomes

An authorized 0.0.0.1 user can:

- Describe a supported line or column chart in one JSON-compatible specification.
- Validate and render it natively in Python or Go.
- Obtain identical canonical SVG for the release conformance corpus.
- Produce self-contained interactive HTML using the shared runtime.
- Apply supported themes, series styling, gradients, patterns, sizing, and declared
  layout controls without leaving the structured specification.
- Inspect known limits, compatibility, qualification evidence, and release provenance.

## In scope

- Chart types `line` and `column` only (bar, area, and scatter are deferred to Post-0.0.0.1).
- Grouped, overlaid, normal-stacked, and non-negative percent-stacked columns.
- Categorical x axes and linear numeric y axes.
- Light, dark, and structured custom themes already represented by the schema.
- Static SVG, self-contained HTML, the shared DOM contract, and declared runtime
  interactions.
- Python and Go as the first certified language implementations.

## Default Render Limits & Bounds

To protect hosting applications against Denial of Service (DoS) and memory exhaustion, the `0.0.0.1` specification enforces the following default constraints:
- **Maximum Dimensions**: 4096px x 4096px.
- **Maximum Series Count**: 50 series per chart.
- **Maximum Data Points**: 1000 data points per series.
- **Maximum String Lengths**: 256 characters for titles, subtitles, and labels.
- **Nested Styles Limit**: Maximum of 8 gradient stops per gradient or pattern element.

## Not in scope

- The 23 design-only Cartesian chart recipes as released capabilities.
- Arbitrary CSS, raw SVG fragments, executable callbacks, or DOM mutation inside a
  certified profile.
- Automatic text measurement, collision avoidance, or universal label fitting.
- A universal pixel guarantee outside a named certified visual profile.
- Hosted chart rendering, accounts, billing, collaboration, telemetry, or an uptime
  commitment.
- A stable public API or backward-compatibility promise beyond the specific 0.0.0.1
  release manifest.

## Commercial and business model positioning

StoneCharts is commercially positioned as a governed infrastructure asset rather than a general-purpose developer utility. Strategic business models currently under validation include:

- **Commercial Embedded SDK**: Licensing StoneCharts to software vendors embedding deterministic reporting in SaaS or on-premise platforms, priced by deployed environment, redistribution rights, and active language renderers.
- **Open Core + Parity Certification**: Making the base schema and standard renderers open, while charging for certified cross-language parity, compliance evidence, security updates, and certified export profiles.
- **Enterprise Source License**: Providing source access, audited release evidence packs, and direct support to highly regulated or air-gapped organizations.

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
