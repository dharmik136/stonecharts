---
id: SC-PROD-007
title: StoneCharts One-Pager (Insurance Reporting Pilot)
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: [BENCH-COMPETITOR-VEGA-20260729, BENCH-COMPETITOR-HIGHCHARTS-20260729, BENCH-COMPETITOR-QUICKCHART-20260729]
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# StoneCharts One-Pager (Insurance Reporting Pilot)

A leave-behind for the initial validation segment named in
[`DEC-017`](../project/decisions.md): insurance reporting and actuarial platforms.
Every claim below is either the approved pitch language from
[`SC-PROD-003`](visual-integrity-strategy.md) or a measured number from
[`SC-QUAL-003`](../quality/competitor-benchmark-results-2026-07.md), cited as such.
Do not add a number here that is not in that results document.

## The pitch

> StoneCharts helps regulated software teams generate, verify, and audit consistent
> charts across backend languages without relying on browser-based rendering
> infrastructure.

**Every chart change should be provable.**

## The problem, in the prospect's own terms

Insurance reporting and actuarial teams generate the same figures across a Python
analysis pipeline and a Go (or other backend) production service. When those two
renderings drift — even by one pixel, even for an internally cosmetic reason — that
drift can raise an audit question or a client complaint, at a point in the process
that is expensive to re-open.

## What we can already show, measured, today

From a single-host measurement run against three real alternatives (Vega/Vega-Lite,
Highcharts Export Server, QuickChart), across three chart shapes (line, scatter,
bubble) — see `SC-QUAL-003` for the full method, host spec, and caveats:

- **Highcharts Export Server's own raw SVG output is not byte-stable across identical
  re-renders** of the same chart configuration — a randomly generated ID gets baked
  into `clipPath` attributes on every render, confirmed on all three chart shapes
  tested. A byte-diff or hash-based conformance check against it will report a false
  change on every regeneration, with no configuration change at all. StoneCharts, Vega,
  and QuickChart all rendered byte-identically on repeat in the same test.
- **StoneCharts renders in ~0.07-0.16 s cold and serves ~5,000-6,500 renders/second
  once warm**, with **zero runtime dependencies** in either its Python or Go
  implementation (`pyproject.toml` declares `dependencies = []`; `go.mod` has no
  `require` block).
- Vega/Vega-Lite carried **6 high-severity npm advisories** on the installed version
  range at measurement time; Highcharts Export Server carried **261 npm dependencies**
  and printed its own install-time warnings that its bundled Puppeteer and Multer
  versions are outdated/vulnerable.
- Highcharts Export Server, once warm, still costs materially more per request than
  StoneCharts even after removing its ~13.6 s cold-start/browser-launch cost from the
  comparison (see `SC-QUAL-003`'s sustained-throughput section for the exact numbers
  and the fairness caveats).

These are single-host, single-day, vendor-run measurements — real, reproducible, and
disclosed as such, not independently audited. `SC-QUAL-003` states plainly what they
do and do not establish.

## What this is not

- Not open source, and not represented as such — the repository, specification,
  renderers, and tooling are proprietary under the current license
  ([`SC-CON-020`](../contracts/commercial-terms-policy.md); see `DEC-018`).
- Not a completed sale, case study, or reference customer — no paid pilot exists yet.
- Not a claim about every chart type or every competitor; scope is the certified
  `line`/`column`/`area`/`bar`/`scatter`/`bubble`/`combo` set against the three
  named competitors, as measured.

## Next step for a qualified prospect

A short discovery conversation using
[`SC-PROD-006`](prospect-qualification-scorecard.md)'s script, followed by a
technical proof of value using [`SC-QUAL-004`](../quality/stoneverify-quickstart.md)'s
StoneVerify workflow against one of the prospect's own real chart specifications.
