---
id: SC-QUAL-003
title: Competitor Benchmark Results (2026-07)
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: [BENCH-COMPETITOR-HIGHCHARTS-20260729, BENCH-COMPETITOR-VEGA-20260729, BENCH-COMPETITOR-QUICKCHART-20260729]
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# Competitor Benchmark Results (2026-07)

This is a completed measurement run under
[`SC-PROD-005`](../product/competitor-benchmark-methodology.md). It reports what was
actually measured on one date, on one host, against the three targets named in the
[`DEC-017`](../project/decisions.md) brief. It supersedes no hypothesis in
[`SC-PROD-003`](../product/visual-integrity-strategy.md); it is the first evidence
toward validating it.

## Method summary

- **Date:** 2026-07-29.
- **Host:** Windows 11 Pro (build 10.0.26200), 16 logical CPUs, single developer
  machine. No other CPU-intensive process was running during timed measurement,
  following the same clean-run discipline used for StoneCharts' own release
  benchmarks (see [benchmark-spec.md](benchmark-spec.md)).
- **Chart under test:** one two-series, twelve-category line chart (`Monthly Average
  Temperature`, Tokyo vs. London), expressed as the equivalent native config for each
  target. Source specs are in the evidence bundle (see
  [Reproduction](#reproduction)).
- **Harness:** a fresh child process per run, wall-clock timed from spawn to exit,
  peak resident-set size sampled by polling the process and all of its descendants
  (`psutil`) every 20 ms. This matters for the headless-browser targets, whose
  renderer runs as a child process the parent alone does not account for.
- **Versions measured:** StoneCharts `4eff89a` (this repository, Python 3.14.4 / Go
  1.26.4); `vega@5.33.1` + `vega-lite@5.23.0` on Node v24.15.0; `highcharts-export-server@5.1.0`
  (bundling `puppeteer@22.15.0`) on Node v24.15.0; QuickChart's public hosted endpoint
  at `https://quickchart.io/chart` as served on the measurement date.

## Operational footprint

Cold-start wall-clock time and peak memory for one fresh-process render of the
equivalent chart. StoneCharts and Vega ran 10 timed invocations; the Highcharts
Export Server ran 5 (at ~13-14 s per run, 5 gave a stable median without an
excessive total run time). QuickChart is a hosted call, not a local process — its
number is network request latency, reported separately below, not merged into this
table.

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.074 s | 0.070-0.336 s | 10.8 MB |
| StoneCharts (Python) | 0.124 s | 0.102-0.133 s | 20.8 MB |
| Vega/Vega-Lite (Node, no browser) | 1.057 s | 0.987-1.093 s | 83.5 MB |
| Highcharts Export Server (Node + Puppeteer/Chromium) | 13.607 s | 13.332-14.298 s | 552.9 MB |

The Go outlier at 0.336 s was the first run in the batch (cold OS file-cache); the
remaining 9 runs were 0.070-0.078 s.

Highcharts Export Server was run via its npm CLI directly
(`node bin/cli.js --infile ... --outfile ... --type svg`), not the official Docker
image, because the sandbox this measurement ran in did not have a running Docker
daemon available. This is disclosed as a methodology deviation and, if anything,
understates Highcharts' real operational cost in a containerized deployment: a
`docker run` cold start adds image-pull and container-init overhead on top of the
in-process numbers measured here. The first pool-worker creation attempt in this
run's very first invocation of the session failed with a timeout and was retried
automatically by the export server's own worker pool; it succeeded on that retry and
on every subsequent measured run, and is reported here as an observed real-world
cold-start characteristic rather than excluded as an anomaly.

## Cross-invocation consistency

Each target rendered the same input twice through its own supported path; outputs
were compared byte-for-byte.

| Target | Result | Detail |
|---|---|---|
| StoneCharts | Byte-identical | Also byte-identical **across** the Python and Go renderers, not just across two runs of one renderer — this is the product's core contract, not a benchmark finding. |
| Vega/Vega-Lite | Byte-identical | Two `node render.js` invocations of the same spec produced identical SVG bytes. |
| QuickChart | Byte-identical | Two hosted requests with the same Chart.js config produced identical PNG bytes (66,631 bytes both times). |
| Highcharts Export Server | **Differs** | Two invocations of the identical input config produced same-length (25,338 bytes) but byte-different SVG. The diff is confined to a randomly generated per-render instance ID string (e.g. `highcharts-8sa4j9f-21-` vs. `highcharts-ats9qkf-21-`) embedded in `clipPath`/`id` attributes and their references, repeated at every point that ID is used. |

The Highcharts finding means a naive byte-diff or content-hash conformance check
against raw Highcharts Export Server SVG output will report a false change on every
regeneration, even with no configuration change. This was not evaluated for whether
the drawn geometry is otherwise pixel-identical beyond the ID strings; only the raw
SVG bytes were diffed.

## Data egress

Fact-check, not a measurement:

| Target | Egress on a self-hosted render | Basis |
|---|---|---|
| StoneCharts | None | Native library call, no network I/O in the render path. |
| Vega/Vega-Lite (as measured) | None | The `render.js` harness compiles and renders fully in-process; no network call was made during a render. |
| Highcharts Export Server | None, once the dependency cache is populated | The CLI's first-ever run (see [operational footprint](#operational-footprint)) fetched Highcharts core and module scripts from `code.highcharts.com` before rendering; once cached, no measured render made a network call. A deployment that discards its cache between invocations would re-incur this fetch each time. |
| QuickChart | Always | The service is a hosted third-party API by design; every render sends the chart configuration to `quickchart.io` over the network. This is not a defect, it is the product's operating model, and it is the reason regulated/air-gapped buyers named in `SC-PROD-003` disqualify it. |

## Dependency and CVE surface

Snapshot as of the exact versions installed on the measurement date; will drift as
upstream releases patches.

| Target | Direct + transitive runtime dependencies | `npm audit` / registry findings |
|---|---:|---|
| StoneCharts (Python) | 0 | `pyproject.toml` declares `dependencies = []`. |
| StoneCharts (Go) | 0 | `go.mod` has no `require` block; stdlib only. |
| Vega + Vega-Lite | 84 | `npm audit`: 6 **high**-severity advisories on the installed version ranges, all cross-site-scripting issues in `vega`, `vega-expression`, `vega-functions`, `vega-lite`, `vega-parser`, and `vega-view` (`toString`/`setdata` expression-evaluation abuse under `VEGA_DEBUG`). |
| Highcharts Export Server | 261 (257 prod + 5 optional) | `npm audit`: 1 **moderate** advisory, transitively via `uuid@10.0.0` (a buffer-bounds-check issue), surfaced against `highcharts-export-server` itself. Separately, `npm install` itself printed deprecation warnings that the bundled `puppeteer@22.15.0` is "no longer supported" (project's own stated support floor is `>=24.15.0`) and that the bundled `multer@1.4.5-lts.2` "is impacted by a number of vulnerabilities, which have been patched in 2.x." |
| QuickChart | Not applicable (hosted) | There is no local dependency tree to audit; the entire trust and patching posture is opaque to the caller and delegated to a third party. |

## Release provenance

`npm view <package> dist.attestations` returned no attestation data for either
`highcharts-export-server` or `vega` as published — neither currently ships npm
build-provenance attestations. Neither publishes an SBOM or signed provenance
document comparable to StoneCharts' own per-release evidence packs (`manifest.json`,
`sbom.spdx.json`, `provenance.json` — see `docs/releases/0.0.0.4/evidence/`).
QuickChart, as a hosted API, exposes no client-visible build artifact to check at
all. This axis favors StoneCharts by construction of its own release process, not by
a discovered gap in the competitors; it is reported for completeness, not presented
as a surprise finding.

## What this does and does not establish

This is one chart, on one host, on one day, run by the vendor whose product is being
compared favorably. It establishes real, reproducible orders-of-magnitude gaps in
cold-start time, memory, and dependency-surface size, and one concrete,
previously-unquantified non-determinism finding in Highcharts Export Server's raw
output. It does **not** establish a controlled multi-chart-type comparison, a
production Linux/container measurement, sustained-load behavior, or an assessment of
Highcharts' or Vega's actual security posture beyond the specific advisories listed.
None of the recurring-cost or willingness-to-pay claims in `SC-PROD-003`'s validation
gate are addressed by this document; only real interviews close that gate.

## Reproduction

Exact commands, per [`SC-PROD-005`](../product/competitor-benchmark-methodology.md)'s
fair-comparison rules:

```bash
# StoneCharts (Go) - build once, then measure cold start
go build -o stonecharts_render.exe ./cmd/line_basic
python measure.py stonecharts-go 10 -- ./stonecharts_render.exe stonecharts-spec.json out-go.svg

# StoneCharts (Python)
python measure.py stonecharts-python 10 -- python stonecharts_render_cli.py stonecharts-spec.json out-py.svg

# Vega/Vega-Lite (server-side, no browser)
npm install vega@5 vega-lite@5
python measure.py vega-nodejs 10 -- node render.js vega-lite-spec.json out-vega.svg

# Highcharts Export Server (npm CLI; Docker unavailable in this sandbox)
npm install highcharts-export-server
python measure.py highcharts-export-server-cli 5 -- \
  node node_modules/highcharts-export-server/bin/cli.js \
  --infile highcharts-config.json --outfile out-highcharts.svg --type svg

# QuickChart (hosted)
# POST chartjs-config.json as {"chart": <config>} to https://quickchart.io/chart
```

The `measure.py` harness, the four equivalent chart specs, the raw per-run JSON
output, `npm audit --json` captures, and all rendered artifacts from this run are
retained locally alongside this document's evidence entries; they are not committed
to source control (they are throwaway measurement artifacts, not release fixtures).
