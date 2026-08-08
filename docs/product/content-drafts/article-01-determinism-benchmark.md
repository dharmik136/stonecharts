---
id: SC-PROD-014
title: "Content Draft: Determinism Benchmark Article"
status: draft
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.5
requirements: []
evidence: []
last_reviewed: "2026-08-07"
review_due: "2026-09-07"
supersedes: null
superseded_by: null
---

<!-- target_platform: dev.to / Hashnode / personal blog -->
<!-- sc_qual_003_citation: required -->
<!-- vendor_disclosure: required -->
<!-- product_naming: none (problem-space framing) -->

# We Measured Five Chart Libraries for Determinism. Two Failed.

Render the same chart spec twice. Get different bytes. Now your conformance
check, your audit trail, and your reproducible build all need a preprocessing
step to strip random IDs before comparing. We wanted to know which chart
libraries actually have this problem.

## Setup

Five server-side chart rendering systems. One chart specification. Ten
consecutive renders each. Byte-by-byte comparison of the SVG output.

| System | Version |
|---|---|
| Highcharts Export Server | 5.1.0 |
| Vega + Vega-Lite | 5.33.1 + 5.23.0 |
| Plotly + Kaleido | 6.9.0 + 1.3.0 |
| ECharts (Node SSR) | 6.1.0 |
| QuickChart | Hosted API |

Same Windows 11 host, same day, same spec. The author develops a sixth
rendering system that was also tested — flagged below.

## Results

**Three passed.** Vega, ECharts, and QuickChart produce byte-identical SVG on
every invocation.

**Highcharts failed.** Each render embeds a randomly generated ID in `clipPath`
attributes. We tried `useSerialIds(true)` — the Highcharts-recommended fix for
reproducible IDs — and it stabilized IDs within a single server session but not
across process restarts.

**Plotly failed.** Each render embeds a unique per-render identifier in the SVG.
No configuration flag removes it.

## Why it matters

If you rely on byte-level comparison for any of these workflows, non-deterministic
rendering forces a preprocessing step — and that preprocessing is itself a source
of false negatives:

- **Conformance gating:** "Did this dependency upgrade change chart output?"
- **Audit trails:** "Prove this quarterly filing chart matches the approved version."
- **Cross-language parity:** "Does the Python pipeline produce the same chart as the Go service?"

Stripping random IDs before comparing might mask real structural differences.
You trade a false positive problem (everything looks different) for a false
negative problem (real changes slip through).

## While we were measuring: dependencies and cold-start

| System | Dependencies | Cold-start | Peak memory |
|---|---|---|---|
| Author's system (Go) | **0** | 0.074 s | 10.8 MB |
| Author's system (Python) | **0** | 0.124 s | 20.8 MB |
| ECharts | 3–4 | 1.259 s | 60.5 MB |
| Plotly + Kaleido | 9 | 3.882 s | 588.6 MB |
| Vega + Vega-Lite | 84 (6 high-severity XSS advisories) | 1.057 s | 83.5 MB |
| Highcharts Export Server | 261 | 13.607 s | 552.9 MB |

Cold-start = time from process launch to first rendered SVG on disk.

## Methodology

- **Date:** 2026-07-29. All sessions same day, same host.
- **Host:** Windows 11 Pro, 16 logical CPUs.
- **Scope:** Seven chart shapes tested for three targets; line chart only for
  ECharts and Plotly. Determinism tested on the line chart shape.
- **Bias:** The author develops a competing system. These are vendor-run,
  single-host measurements. Not independently audited. The methodology is
  documented in a governed benchmark specification (SC-QUAL-003) with
  version-pinned configurations for each target.

## What we build

The author's system is a deterministic chart rendering system with certified
Python and Go renderers that produce byte-identical SVG from the same JSON
specification. Zero runtime dependencies in either language. Currently in
private preview for regulated reporting teams.

[Request early access to the interactive demo](#) if chart determinism matters
to your workflow.

---

*Disclosure: The author develops a competing chart rendering system. All numbers
from SC-QUAL-003, a vendor-run benchmark. Not independently audited.*
