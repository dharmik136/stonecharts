---
id: SC-PROD-002
title: StoneCharts Positioning and Scope
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: [REQ-SCOPE-001]
evidence: [TEST-CAPABILITY-MATRIX]
last_reviewed: "2026-08-10"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# Positioning and Scope

## Positioning

StoneCharts is a deterministic, multi-language chart specification and native SVG
rendering system. Its differentiation is not maximum chart count. It is the ability to
carry one validated chart contract across language and delivery boundaries with
explicit, testable guarantees.

Established browser chart libraries provide broad interactive feature catalogs.
StoneCharts serves workflows where native server rendering, canonical output,
auditability, self-contained artifacts, and cross-language equivalence matter more
than browser-only breadth.

Per [`DEC-017`](../project/decisions.md), the active go-to-market positioning is
**Visual Integrity Infrastructure**, validated first in insurance reporting and
actuarial platforms. That category framing, initial message, and competitive frame
are governed by [`SC-PROD-003`](visual-integrity-strategy.md) and are not restated
here; this document governs technical scope, not go-to-market language.

## Certified user outcomes

An authorized user of a certified release can:

- Describe a supported chart in one JSON-compatible specification.
- Validate and render it natively in Python or Go.
- Obtain identical canonical SVG for the release conformance corpus.
- Produce self-contained interactive HTML using the shared runtime.
- Apply supported themes, series styling, gradients, patterns, sizing, and declared
  layout controls without leaving the structured specification.
- Verify cross-runtime conformance directly with `tools/stonecharts_verify.py` and
  keep the resulting evidence bundle.
- Inspect known limits, compatibility, qualification evidence, and release provenance.

## In scope

Current certified chart types, customization surface, and language support are
tracked authoritatively in [`SC-PROD-004`](capability-matrix.md); this document does
not restate that table. As of `0.0.0.34` the certified set includes 36 chart types:
two complete families — Family A (Cartesian, 26 types) and Family B (Polar/radial,
9 types) — plus development-triangle, with certified implementations in Python and
Go. All 36 share the same executable eight-gate certification ledger.

The `0.0.0.1` initial release scope (historical, satisfies `REQ-SCOPE-001`) was:

- Chart types `line`, `column`, and `area` only.
- Grouped, overlaid, normal-stacked, and non-negative percent-stacked columns.
- Categorical x axes and linear numeric y axes.
- Light, dark, and structured custom themes already represented by the schema.
- Static SVG, self-contained HTML, the shared DOM contract, and declared runtime
  interactions.
- Python and Go as the first certified language implementations.

Per [`DEC-017`](../project/decisions.md), chart-family expansion beyond `0.0.0.4`
required explicit approval as necessary validation infrastructure. Decisions
DEC-020 through DEC-048 admitted 28 additional chart types under that clause,
completing Family A (Cartesian) and Family B (Polar/radial). Language expansion
beyond Python and Go remains paused pending paid customer evidence; see
[`SC-PROD-003`](visual-integrity-strategy.md) for the validation gate.

## Not in scope

- The design-only Cartesian chart recipes under `charts/<id>/design.md` as released
  capabilities, until each passes the chart admission checklist.
- Arbitrary CSS, raw SVG fragments, executable callbacks, or DOM mutation inside a
  certified profile.
- Automatic text measurement, collision avoidance, or universal label fitting.
- A universal pixel guarantee outside a named certified visual profile.
- Hosted chart rendering, accounts, billing, collaboration, telemetry, or an uptime
  commitment.
- Hosted immutable evidence storage (`StoneVault`) and organization-level policy
  enforcement (`StonePolicy`); both are later product surfaces, not current scope.
- A stable public API or backward-compatibility promise beyond the specific certified
  release manifests.

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
