---
target_platform: dev.to / Hashnode / personal blog
status: draft
sc_qual_003_citation: required
vendor_disclosure: required
product_naming: none (problem-space framing)
---

# We Measured Five Chart Libraries for Determinism. Two Failed.

If you render the same chart specification twice with the same library and get
different bytes, you cannot do byte-level conformance checks, reproducible builds,
or audit-safe reporting without additional preprocessing. We tested whether that
actually happens.

## The test

We took five server-side chart rendering systems — Highcharts Export Server (5.1.0),
Vega/Vega-Lite (5.33.1 + 5.23.0), Plotly/Kaleido (6.9.0 + 1.3.0), ECharts (6.1.0
via Node SSR), and QuickChart (hosted API) — and rendered the same line chart
specification ten consecutive times in each. Then we compared the SVG output files
byte by byte.

All tests ran on the same Windows 11 host, same day, same chart specification. This
is a vendor-run measurement by the author of a sixth rendering system that also
participated in the test. Draw your own conclusions about bias; the methodology is
fully described below.

## Results

**Three of five produced byte-identical output on every invocation.** Vega,
ECharts, and QuickChart all passed the byte-identity check.

**Highcharts Export Server did not.** Each render embeds a randomly generated ID in
`clipPath` attributes. The SVG output is structurally equivalent but never
byte-identical across invocations. We tested `useSerialIds(true)` — the
Highcharts-recommended fix for reproducible IDs — and it stabilized IDs within a
single server session but did not produce cross-invocation determinism.

**Plotly/Kaleido did not.** Each render embeds a unique per-render identifier in the
SVG output, making raw-byte comparison impossible without stripping it.

## Why this matters

If your workflow involves:

- **Conformance checking** — "did this dependency upgrade change our chart output?"
- **Audit trails** — "prove this quarterly report chart is identical to the approved
  version"
- **Multi-language parity** — "does the Python analysis pipeline produce the same
  chart as the Go production service?"

...then non-deterministic rendering means you need a preprocessing step (strip random
IDs, normalize whitespace, etc.) before you can compare. That preprocessing is itself
a source of false negatives — it might mask real differences.

## The dependency angle

While we were measuring, we also looked at the dependency and security surface:

| System | Dependencies | Security findings |
|---|---|---|
| Vega + Vega-Lite | 84 npm packages | 6 high-severity advisories (XSS) |
| Highcharts Export Server | 261 npm packages | 1 moderate; install-time warnings about outdated Puppeteer |
| ECharts | 3–4 packages | 0 vulnerabilities |
| Plotly + Kaleido | 9 Python packages | 0 vulnerabilities |
| QuickChart | Hosted API (N/A) | N/A (your data leaves your network) |

The author's system has zero runtime dependencies in both its Python and Go
implementations. We acknowledge this is a competitive claim and flag it as such.

## The cold-start angle

Since we had the test harness running, we also measured cold-start latency (time from
process launch to first rendered SVG):

| System | Median cold-start | Peak memory |
|---|---|---|
| Author's system (Go) | 0.074 s | 10.8 MB |
| Author's system (Python) | 0.124 s | 20.8 MB |
| Vega/Vega-Lite | 1.057 s | 83.5 MB |
| ECharts (Node SSR) | 1.259 s | 60.5 MB |
| Plotly/Kaleido | 3.882 s | 588.6 MB |
| Highcharts Export Server | 13.607 s | 552.9 MB |

## Methodology and caveats

- **Date:** 2026-07-29. All sessions on the same day and host.
- **Host:** Windows 11 Pro, 16 logical CPUs, single developer machine.
- **Disclosure:** The author develops a competing chart rendering system. These
  measurements are vendor-run, single-host, and not independently audited. They are
  reproducible — the methodology is documented in a governed benchmark specification
  with version-pinned configurations for each target.
- **Scope:** Six chart shapes tested (line, column, area, bar, scatter, bubble) for
  three targets; line chart only for ECharts and Plotly. Cross-invocation determinism
  tested on the line chart shape.

## What we build

The author's system is a deterministic, multi-language chart specification and
native SVG rendering system. It produces byte-identical output across its Python and
Go implementations from the same JSON specification. It is currently in private
preview for regulated reporting teams.

If you work on insurance reporting, actuarial platforms, or other regulated reporting
workflows and chart consistency matters to your audit or compliance process, you can
[request early access to the interactive demo](#).

---

*Disclosure: The author develops a competing chart rendering system and has a
commercial interest in the outcome of these comparisons. All numbers are from a
single governed benchmark document (SC-QUAL-003), measured on a single host on a
single day, and disclosed as vendor-run. They are not independently audited.*
