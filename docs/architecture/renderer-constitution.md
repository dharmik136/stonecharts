---
id: SC-ARCH-002
title: StoneCharts Renderer Constitution
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: all certified language renderers
requirements: [REQ-PROD-001, REQ-DET-001, REQ-VAL-001, REQ-CAP-001, REQ-PERF-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-VALIDATION-PARITY, BENCH-RENDER-BASELINE]
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Renderer Constitution

## Purpose

This constitution defines the admission and maintenance rules for every StoneCharts
language implementation. A binding or wrapper is not automatically a certified
renderer.

## Admission gate

A new language renderer MUST provide:

1. An idiomatic typed spec model covering the active schema.
2. Structural, semantic, and capability validation equivalent to existing certified
   renderers.
3. Canonical number formatting, escaping, ordering, whitespace, and UTF-8 output.
4. Native SVG generation without invoking Python, Go, Node, a browser, or a remote
   rendering service.
5. Complete line, column, area, and bar conformance against the release corpus.
6. Identical canonical error codes and paths for shared invalid fixtures.
7. Package metadata, supported runtime versions, license metadata, and installation
   documentation appropriate to the ecosystem.
8. Benchmark results under the approved workload protocol.
9. A named maintainer and a policy for keeping the renderer current.

The renderer remains experimental until every mandatory item passes in an immutable
release candidate.

## Deterministic implementation rules

- Evaluate parity-sensitive arithmetic in the operation order defined by the relevant
  substrate and chart contract.
- Iterate ordered arrays by index. Map or dictionary iteration MUST NOT determine SVG
  order.
- Route every user-controlled string through context-appropriate encoding.
- Use the canonical formatter for data values and the canonical coordinate formatter
  for geometry.
- Do not infer behavior from language truthiness, locale, host timezone, environment
  font discovery, or platform-dependent hash order.
- Do not add renderer-specific defaults or conveniences to the certified path.
- Do not regenerate a golden merely to make a failing implementation pass.

## Architecture rules

Chart renderers supply marks to a shared substrate and MUST NOT fork axes, themes,
legend, accessibility, serialization, or runtime contracts without an approved ADR.
Reusable transforms such as stacking, band layout, and point normalization belong to
the substrate or a shared transform layer, not one chart implementation.

The active schema and capability manifest are separate checks. A renderer MUST reject
unsupported input before mark generation and MUST NOT panic or throw an undocumented
exception for user input.

## Change protocol

A contract-affecting change begins with a requirement and, when architecturally
significant, an ADR. Semantic fixtures are added before or with implementation. Existing
goldens remain frozen unless the approved decision intentionally changes output; in
that case every changed byte is reviewed and recorded in release evidence.

## Certification levels

- **Prototype:** may render examples; no compatibility claim.
- **Conforming:** passes structural and semantic tests for the active schema.
- **Canonical:** also byte-matches the complete canonical corpus.
- **Certified:** canonical, packaged, benchmarked, security-reviewed, documented, and
  included in a signed release manifest.

Product documentation may call a language supported only at the Certified level.

## Removal and drift

A renderer that misses a mandatory release, lacks a maintainer, or fails the current
conformance corpus is marked deprecated or experimental. StoneCharts MUST narrow its
language claim rather than silently shipping unequal implementations.

