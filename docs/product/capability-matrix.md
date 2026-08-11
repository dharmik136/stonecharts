---
id: SC-PROD-004
title: StoneCharts Capability Matrix
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: independent
applies_to: 0.0.0.32 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-10"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# Capability Matrix

This is the authoritative product-facing capability matrix. Other product,
marketing, and pilot documents should link here instead of restating release scope.

## Current technical capabilities

36 chart types across three tiers: 7 certified, 9 candidate, 20 experimental.

<!-- BEGIN:GENERATED:capabilities -->
| Capability | Tier | First release | Notes |
|---|---|---:|---|
| Shared chart specification | Certified | 0.0.0.1 | JSON-compatible schema with governed validation boundaries. |
| Python renderer | Certified | 0.0.0.1 | Native SVG rendering for the certified corpus. |
| Go renderer | Certified | 0.0.0.1 | Native SVG rendering for the certified corpus. |
| Static SVG output | Certified | 0.0.0.1 | Browser-free generation for supported specifications. |
| Self-contained HTML runtime | Certified | 0.0.0.1 | Enhances already-complete SVG with the governed interaction runtime. |
| Release evidence packs | Certified | 0.0.0.1 | Manifest, provenance, SBOM, hashes, and qualification evidence. |
| Line | Certified | 0.0.0.1 | `line` and `line-basic` aliases map to the certified line renderer. |
| Column | Certified | 0.0.0.1 | Includes grouped, stacked, and non-negative percent-stacked column profiles. |
| Area | Certified | 0.0.0.3 | Includes basic, stacked, and percent-stacked area profiles. |
| Bar | Certified | 0.0.0.2 | Orientation transpose of the column substrate, independently qualified. |
| Scatter | Certified | 0.0.0.3 | Introduces the governed point model and numeric x-axis. |
| Bubble | Certified | 0.0.0.4 | Extends the point model with `z` and a deterministic size scale. |
| Combo | Certified | 0.0.0.5 | Per-series mark types (column + line) on shared axes with optional dual y-axis. |
| Histogram | Candidate | 0.0.0.6 | Binning transform with optional pareto line and bellcurve overlay. |
| Candlestick | Experimental | 0.0.0.7 | OHLC financial chart with candlestick, ohlc, hlc, heikin-ashi, hollow subtypes. |
| Error Bar | Candidate | 0.0.0.8 | Whisker marks showing center value with low/high uncertainty bounds. |
| Area Range | Candidate | 0.0.0.9 | Band-fill between low and high data paths for intervals and envelopes. |
| Column Range | Candidate | 0.0.0.9 | Floating bars between low and high values per category. |
| Waterfall | Candidate | 0.0.0.10 | Signed deltas as floating bars with running-total transform and connector lines. |
| Bullet | Candidate | 0.0.0.11 | Compact KPI bar against qualitative range bands and a comparison target. |
| Boxplot | Candidate | 0.0.0.12 | Box-and-whisker glyphs showing 5-number summary with optional outliers. |
| Lollipop | Experimental | 0.0.0.13 | Thin stems from baseline capped with marker heads for category comparison. |
| Dumbbell | Candidate | 0.0.0.14 | Connected-dot plot for before/after and min-max comparison. |
| Funnel | Experimental | 0.0.0.15 | Centered trapezoid stack for conversion and drop-off visualization. |
| Variwide | Experimental | 0.0.0.16 | Column chart where each bar width also encodes a second data metric. |
| Timeline | Experimental | 0.0.0.17 | Events on a time axis with markers, leader lines, and alternating labels. |
| Windbarb | Experimental | 0.0.0.18 | Meteorological wind-barb glyphs encoding speed and direction. |
| Streamgraph | Experimental | 0.0.0.19 | Stacked area ribbons over a floating baseline (wiggle/silhouette). |
| Vector Plot | Experimental | 0.0.0.20 | Arrow glyphs encoding direction and magnitude on a numeric x/y plane. |
| X-Range | Experimental | 0.0.0.21 | Horizontal span bars on lane categories for Gantt charts and trace waterfalls. |
| Technical Indicators | Experimental | 0.0.0.22 | Derived overlays (SMA, EMA, Bollinger, RSI, MACD) on a base metric. |
| Flame Chart | Experimental | 0.0.0.23 | Time-ordered stack frames for profiling views. |
| Pie | Experimental | 0.0.0.24 | Part-to-whole composition with sector arcs. Donut and variable-radius variants. |
| Gauge | Experimental | 0.0.0.25 | Single-value dial on a 270-degree arc with colored range bands. |
| Solid Gauge | Experimental | 0.0.0.26 | Filled arc for utilization and progress views. |
| Radar | Experimental | 0.0.0.27 | Multi-dimensional comparison on N radial axes with polygon gridlines. |
| Polar | Experimental | 0.0.0.28 | Circular polar grid with categories at equal angular spacing. |
| Wind Rose | Experimental | 0.0.0.29 | Stacked polar columns for directional distribution. |
| Nightingale | Experimental | 0.0.0.30 | Radius-proportional sectors (rose/coxcomb) with multi-series overlay. |
| Radial Bar | Experimental | 0.0.0.31 | Concentric progress rings for categorical progress views. |
| Parliament | Experimental | 0.0.0.32 | Semicircular hemicycle of unit dots for proportional allocation. |
| Development Triangle | Candidate | unreleased | Actuarial loss development triangle. Target release: 0.0.0.33. |
<!-- END:GENERATED:capabilities -->

## Commercial pilot scope

The next pilot scope is intentionally narrower than the full design roadmap:

- insurance reporting and actuarial workflows;
- Python and Go only;
- all 36 chart types (7 certified, 9 candidate, 20 experimental; 26 Cartesian +
  9 Polar/radial + 1 candidate unreleased) unless a specific pilot workflow
  constrains the subset;
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

