---
id: SC-PROD-004
title: StoneCharts Capability Matrix
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: independent
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-28"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# Capability Matrix

This is the authoritative product-facing capability matrix. Other product,
marketing, and pilot documents should link here instead of restating release scope.

## Current certified technical capabilities

| Capability | Status | First certified release | Notes |
|---|---|---:|---|
| Shared chart specification | Certified | 0.0.0.1 | JSON-compatible schema with governed validation boundaries. |
| Python renderer | Certified | 0.0.0.1 | Native SVG rendering for the certified corpus. |
| Go renderer | Certified | 0.0.0.1 | Native SVG rendering for the certified corpus. |
| Static SVG output | Certified | 0.0.0.1 | Browser-free generation for supported specifications. |
| Self-contained HTML runtime | Certified | 0.0.0.1 | Enhances already-complete SVG with the governed interaction runtime. |
| Release evidence packs | Certified | 0.0.0.1 | Manifest, provenance, SBOM, hashes, and qualification evidence. |
| Line | Certified | 0.0.0.1 | `line` and `line-basic` aliases map to the certified line renderer. |
| Column | Certified | 0.0.0.1 | Includes grouped, stacked, and non-negative percent-stacked column profiles. |
| Area | Certified | 0.0.0.1 | Includes basic, stacked, and percent-stacked area profiles. |
| Bar | Certified | 0.0.0.2 | Orientation transpose of the column substrate, independently qualified. |
| Scatter | Certified | 0.0.0.3 | Introduces the governed point model and numeric x-axis. |
| Bubble | Certified | 0.0.0.4 | Extends the point model with `z` and a deterministic size scale. |

## Commercial pilot scope

The next pilot scope is intentionally narrower than the full design roadmap:

- insurance reporting and actuarial workflows;
- Python and Go only;
- line, column, bar, area, scatter, and bubble only unless a paid validation workflow
  requires another chart type;
- local evidence bundles stored by the customer, not hosted StoneVault storage;
- StoneVerify-style conformance checks before new chart-family breadth.

## Design-only or deferred capabilities

The repository contains many chart design documents under `charts/<id>/design.md`.
Those designs are roadmap assets, not supported product scope, until each chart type
passes the chart admission checklist and release gates.

Deferred capabilities include:

- additional language runtimes beyond Python and Go;
- hosted rendering, accounts, billing, or telemetry;
- hosted immutable storage and approval workflows;
- PDF/A or controlled document-generation profiles;
- full migration compatibility with Vega-Lite, Chart.js, Highcharts, or other chart
  configuration systems;
- third-party audits, FIPS claims, indemnity, or support SLAs beyond a signed
  agreement.

## Licensing boundary

The current repository license is proprietary. Public specification, public fixtures,
open-core packaging, or community runtimes require a separate licensing and
publication decision before they may be described as available.

