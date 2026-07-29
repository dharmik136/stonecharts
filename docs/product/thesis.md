---
id: SC-PROD-001
title: StoneCharts Product Thesis
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: all
requirements: [REQ-PROD-001]
evidence: []
last_reviewed: "2026-07-29"
review_due: "2026-10-29"
supersedes: null
superseded_by: null
---

# Product Thesis

## Thesis

StoneCharts turns one structured chart specification into the same validated,
auditable chart across certified programming languages, reports, dashboards, and
exports.

The product is not primarily a collection of chart drawings. It is a portable chart
contract: shared input semantics, independent native renderers, canonical output,
bounded customization, and evidence that the implementations agree.

## Problem

Organizations commonly reproduce the same chart in application code, notebooks,
backend reports, browser dashboards, scheduled exports, and multiple service
languages. Each implementation introduces different defaults, validation, formatting,
accessibility, layout, and export behavior. Visual review catches some drift but does
not provide a reliable or auditable system contract.

## Product promise

For a supported specification and declared guarantee profile, StoneCharts provides:

1. One language-neutral input model.
2. Equivalent validation and capability errors in every certified renderer.
3. Canonical static SVG produced without a browser.
4. Shared interaction semantics for self-contained HTML.
5. Structured personalization that remains portable and testable.
6. Release evidence showing which claims were verified for the shipped artifacts.

The exact boundary of each promise is defined by
[`SC-CON-001`](../contracts/guarantees-and-limits.md). Product language MUST NOT turn
an internal byte-parity oracle into an unsupported claim of universal pixel identity.

The thesis is intentionally aligned with the current baseline: `line`, `column`,
`area`, `bar`, `scatter`, and `bubble` are certified across releases `0.0.0.1`
through `0.0.0.4` (see [`SC-PROD-004`](capability-matrix.md) for the authoritative
capability table). All other chart recipes under `charts/<id>/design.md` remain
informative until each passes the chart admission checklist. Per
[`DEC-017`](../project/decisions.md), broad chart-family expansion is paused after
`0.0.0.4`; new chart types, languages, hosted services, or document-generation
capabilities require paid customer evidence or explicit approval as necessary
validation infrastructure.

## Primary users

- Backend and platform engineers producing charts from Python, Go, and later native
  language environments without adding a JavaScript rendering service.
- Reporting and analytics teams requiring repeatable visuals across scheduled jobs,
  services, and embedded applications.
- Regulated or audit-conscious organizations that need a versioned specification,
  deterministic artifacts, traceable decisions, and reproducible release evidence.
- Product teams that need brand and domain customization without maintaining separate
  chart implementations in every stack.

## Current validation focus

The thesis above is the enduring technical contract. The active go-to-market
category, initial validation segment, and product-surface roadmap
(StoneSpec/StoneRender/StoneVerify/StoneVault/StonePolicy/StoneMigrate) are governed
separately by [`SC-PROD-003`](visual-integrity-strategy.md), since that framing is
subject to market validation and may change faster than this technical thesis. Do
not restate the go-to-market category or validation-gate criteria here; link to
`SC-PROD-003` instead.

## Product principles

- **Evidence before claims.** A guarantee exists only for a named scope and passing
  evidence set.
- **Static first.** SVG is complete without JavaScript; the runtime enhances it.
- **Independent implementations, shared contract.** Languages do not call one hidden
  reference renderer and do not invent local behavior.
- **Customization without ambiguity.** Personalization is broad but structured,
  validated, versioned, and subject to explicit guarantee profiles.
- **Capability is honest.** Designed, experimental, implemented, certified, and
  supported are different states.
- **Failures are products too.** Invalid or unsupported input returns stable,
  actionable errors rather than crashes or plausible but incorrect charts.

## Non-goals

StoneCharts does not promise arbitrary executable extensions inside certified output,
automatic layout intelligence without a declared metrics profile, universal pixel
identity in uncontrolled viewers, or immediate breadth across every chart type and
language. Those would weaken the core contract if claimed before they are verified.

## Success measures

The initial product succeeds when independent teams can use one supported spec in two
certified languages, receive the same canonical chart or equivalent error, customize
it within the declared boundary, operate it accessibly in the certified browser
profile, and audit the release evidence without relying on the implementation author.
