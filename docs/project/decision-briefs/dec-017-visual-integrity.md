---
id: SC-OPS-018
title: DEC-017 Visual Integrity Repositioning Brief
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: independent
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-30"
review_due: "2026-08-30"
supersedes: null
superseded_by: null
---

# DEC-017 Visual Integrity Repositioning Brief

## Decision

Accepted:

> StoneCharts will pause broad chart-family expansion after version 0.0.0.4. The
> next product phase will focus on validating Visual Integrity Infrastructure within
> one regulated-reporting segment and delivering a working StoneVerify conformance
> workflow. New chart types, languages, hosted services, and document-generation
> capabilities require either paid customer evidence or explicit approval as
> necessary validation infrastructure.

The first validation segment is insurance reporting and actuarial platforms.

## Basis

The strongest differentiated capability in the repository is not general chart
rendering. It is the combination of:

- one governed chart specification;
- independent Python and Go renderers;
- canonical SVG output;
- golden fixtures and byte-parity checks;
- release evidence packs, provenance, SBOMs, and compatibility controls;
- security, accessibility, runtime, and performance evidence.

That system maps to regulated and audit-conscious reporting better than it maps to
front-end dashboards, exploratory analytics, or generic chart catalog competition.

## Competitive assumptions to validate

The competitor frame should be evidence-led:

- Highcharts has an official Node/Puppeteer export-server path for PNG, JPG, PDF, and
  SVG rendering.
- QuickChart offers an API model for rendering Chart.js configurations to images.
- Vega supports server-side static rendering paths.

These alternatives are legitimate. StoneCharts should compete where the buyer needs
cross-runtime conformance evidence, controlled native execution, release provenance,
and audit-ready artifact history, not where the buyer wants maximum visual breadth.

## Acceptance criteria

DEC-017 is accepted with these constraints:

- use "Visual Integrity Infrastructure" as the validation category;
- freeze broad chart expansion by default after `0.0.0.4`;
- define StoneVerify-style conformance evidence as the next product proof;
- run a focused interview program in insurance reporting and actuarial platforms;
- separate measured benchmark results from unverified sales claims;
- resolve public specification and commercial runtime boundaries before external
  launch.

## Immediate work if approved

1. Rewrite market-facing product docs around visual integrity outcomes.
2. Replace generic pilot material with a real StoneCharts conformance workflow.
3. Build the end-to-end deliberate-drift demo.
4. Create a reproducible competitor benchmark methodology.
5. Build a prospect qualification scorecard and interview script.

## Internal research appendix (not normative)

[`SC-PROD-003`](../../product/visual-integrity-strategy.md)'s "Platform completion
judgment" section states its market-fit hypothesis qualitatively (evidence-confidence
bands, not scores) after an earlier draft's precise decimal PMF scores were retired
for implying a measurement precision the underlying research does not have. That
earlier scoring is kept here, unaltered, as the internal reasoning trail behind the
qualitative bands - useful for discussion, not for citation as an approved figure
anywhere else in this repository.

| Dimension | Current repository (judgment) | Completed suite (judgment) |
|---|---:|---:|
| Technical product quality | 8/10 | 9/10 |
| General chart-library competitiveness | 3/10 | 5/10 |
| Regulated-reporting fit | 6/10 | 8.5/10 |
| Competitive differentiation | 6.5/10 | 8/10 |
| Ease of adoption | 3.5/10 | 7.5/10 |
| Proven market demand | 2/10 | Still requires customers |
| Overall PMF potential | 4.5/10 today | 7.5-8/10 potential |
| Chart breadth alone (no Verify/Vault/Policy/Migrate) | - | 5-6/10 |

These are strategic judgment scores from an external market-fit analysis, not
measured market statistics, and do not supersede or restate SC-PROD-003's normative
qualitative table.
