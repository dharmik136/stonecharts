---
id: SC-PROD-001-ANTIGRAVITY
title: StoneCharts Product Thesis (Antigravity Version)
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: all
requirements: [REQ-PROD-001]
evidence: []
last_reviewed: "2026-07-21"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Product Thesis

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

## Thesis

StoneCharts is a deterministic visualization infrastructure layer for teams that must reproduce, validate, and audit the same chart across backend languages and reporting environments—without relying on a browser rendering service.

The product is not primarily a collection of chart drawings; it is a portable chart contract providing one governed chart specification, native Python and Go rendering, and reproducible SVG for reports, services, and regulated workflows.

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

The thesis is intentionally aligned with the current baseline: `line` and `column`
are the only active 0.0.0.1 chart types, and all other chart recipes remain
informative until their contracts and renderers are admitted.

## Primary users

- **Embedded analytics vendors** supporting multiple backend stacks, white-labeling, self-hosting, and customer-controlled deployments.
- **Regulated and audit-conscious report-generation platforms** (financial, clinical, insurance, or government) that need a versioned specification, deterministic SVG artifacts, repeatable reports, and reproducible release evidence.
- **Security and observability vendors** generating static incident reports, running in restricted environments, and requiring consistent visual output.
- **Enterprise document automation platforms** producing large numbers of recurring HTML and PDF reports across backend languages without browser-based rendering dependencies.

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
