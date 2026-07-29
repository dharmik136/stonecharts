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
- **Charts under test:** three chart shapes, each expressed as the equivalent native
  config for every target: a two-series, twelve-category **line** chart (`Monthly
  Average Temperature`, Tokyo vs. London); a 15-point single-series **scatter** chart
  (`Response Latency by Sample`); and a 6-point single-series **bubble** chart
  (`Endpoint Latency vs Payload`, `[x, y, z]` triples). Scatter and bubble mirror
  StoneCharts' own `charts/scatter/examples/basic.json` and
  `charts/bubble/examples/basic.json` fixtures. For Chart.js's bubble dataset, which
  takes a literal pixel radius rather than a size value, the six radii were
  precomputed with StoneCharts' own published size-scale formula
  (`r = 4 + 28 * sqrt(clamp01((z - zmin) / (zmax - zmin)))`, `RMIN=4`, `RMAX=32`) so
  the rendered bubble areas are comparable, not just the raw data. Source specs are
  in the evidence bundle (see [Reproduction](#reproduction)).
- **Harness:** a fresh child process per run, wall-clock timed from spawn to exit,
  peak resident-set size sampled by polling the process and all of its descendants
  (`psutil`) every 5 ms. This matters for the headless-browser targets, whose
  renderer runs as a child process the parent alone does not account for.
- **Versions measured:** StoneCharts `4eff89a` (this repository, Python 3.14.4 / Go
  1.26.4); `vega@5.33.1` + `vega-lite@5.23.0` on Node v24.15.0; `highcharts-export-server@5.1.0`
  (bundling `puppeteer@22.15.0`) on Node v24.15.0; QuickChart's public hosted endpoint
  at `https://quickchart.io/chart` as served on the measurement date.

## Operational footprint

Cold-start wall-clock time and peak memory for one fresh-process render of the
equivalent chart. StoneCharts and Vega ran 10 timed invocations per chart type; the
Highcharts Export Server ran 5 per chart type (at ~13-15 s per run, 5 gave a stable
median without an excessive total run time). QuickChart is a hosted call, not a local
process — its numbers are network request latency, reported separately below, not
merged into these tables.

### Line chart

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.074 s | 0.070-0.336 s | 10.8 MB |
| StoneCharts (Python) | 0.124 s | 0.102-0.133 s | 20.8 MB |
| Vega/Vega-Lite (Node, no browser) | 1.057 s | 0.987-1.093 s | 83.5 MB |
| Highcharts Export Server (Node + Puppeteer/Chromium) | 13.607 s | 13.332-14.298 s | 552.9 MB |

The Go outlier at 0.336 s was the first run in the batch (cold OS file-cache); the
remaining 9 runs were 0.070-0.078 s.

### Scatter chart

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.088 s | 0.084-0.090 s | 10.4 MB |
| StoneCharts (Python) | 0.132 s | 0.123-0.149 s | 20.9 MB |
| Vega-Lite (`point` mark, no browser) | 1.038 s | 1.010-1.057 s | 70.4 MB |
| Highcharts Export Server | 13.707 s | 12.906-13.992 s | 550.7 MB |

### Bubble chart

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.089 s | 0.082-0.093 s | 10.2 MB |
| StoneCharts (Python) | 0.139 s | 0.126-0.160 s | 20.8 MB |
| Vega-Lite (`circle` mark, sqrt size scale) | 1.038 s | 1.008-1.101 s | 73.6 MB |
| Highcharts Export Server (bubble series) | 14.519 s | 14.131-15.298 s | 541.2 MB |

The orders-of-magnitude gaps hold consistently across all three chart shapes: they are
not an artifact of the line chart being an easy case for any one target.

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

## Sustained (warm) throughput

Cold-start is the fairest number for "spawn a fresh process per chart," but it is not
the only real deployment shape. A production report-rendering service typically stays
warm. This section measures per-render latency **inside one already-running process**
for the line chart, after one untimed warm-up render, so process-start and (for
Highcharts) browser-launch cost are excluded:

| Target | Warm median latency | Renders/second (median) | How it was kept warm |
|---|---:|---:|---|
| StoneCharts (Python) | 0.000152 s | 6,570 | 200 in-process renders, same `ChartSpec`, no restart. |
| StoneCharts (Go) | 0.000190 s | 5,274 | 20,000 in-process renders (batched for timer resolution), no restart. |
| Vega/Vega-Lite (Node, no browser) | 0.00576 s | 173 | 200 renders in one Node process; each still re-parses the Vega-Lite spec and builds a fresh `View`, matching a stateless per-request service rather than caching a compiled view. |
| Highcharts Export Server | 0.052 s | ~19 | Ran with `--enableServer 1` (its own persistent HTTP server mode, pool of 4-8 warm browser workers) instead of the one-shot CLI; 10 sequential HTTP requests to the already-warm server, first request excluded as pool warm-up. |

This changes the picture materially from the cold-start table above: once warm,
Highcharts Export Server serves a request in ~52 ms, not ~13.6 s — the 13.6 s number
is specific to spawning a fresh process (and browser) per render, not to the
product's actual recommended deployment shape. **Even so**, StoneCharts remains
roughly 30x faster than Vega and roughly 270x faster than a warm Highcharts server on
this measure, and does so with a request path that never launches a browser process
at all. Both framings are reported because a naive "13.6 s vs 0.07 s" comparison would
overstate the gap for anyone who deploys Highcharts Export Server correctly (as a
long-lived server), and it is more defensible to disclose that than to leave it for a
skeptical reader to find.

This section measures one connection at a time, sequentially. It does not measure
concurrent/parallel request throughput, which depends on worker-pool sizing and is a
different and unmeasured question.

## Cross-invocation consistency

Each target rendered the same input twice through its own supported path, for all
three chart shapes; outputs were compared byte-for-byte.

| Target | Line | Scatter | Bubble | Detail |
|---|---|---|---|---|
| StoneCharts | Identical | Identical | Identical | Also byte-identical **across** the Python and Go renderers on every chart shape, not just across two runs of one renderer — this is the product's core contract, not a benchmark finding. |
| Vega/Vega-Lite | Identical | Identical | Identical | Every `node render.js` invocation of a given spec produced identical SVG bytes, across all three chart shapes. |
| QuickChart | Identical | Identical | Identical | Every pair of hosted requests with the same Chart.js config produced identical PNG bytes (line: 66,631 B; scatter: 36,743 B; bubble: 46,633 B). |
| Highcharts Export Server | **Differs** | **Differs** | **Differs** | Every chart shape reproduced the same finding: same-length output (line 25,338 B; scatter 19,478 B; bubble 15,011 B), byte-different at the same offset (char 4211, line 79) every time. The diff is confined to a randomly generated per-render instance ID string (e.g. `highcharts-8sa4j9f-21-` vs. `highcharts-ats9qkf-21-`) embedded in `clipPath`/`id` attributes and their references, repeated at every point that ID is used. |

The Highcharts finding means a naive byte-diff or content-hash conformance check
against raw Highcharts Export Server SVG output will report a false change on every
regeneration, even with no configuration change, and it reproduces identically across
three unrelated chart types rather than being specific to one chart's geometry. This
was not evaluated for whether the drawn geometry is otherwise pixel-identical beyond
the ID strings; only the raw SVG bytes were diffed.

**Tested and ruled out:** Highcharts core exposes `Highcharts.useSerialIds(flag)`, an
internal API used in Highcharts' own test suite to make generated IDs deterministic.
This was tested directly — injected via the export server's own `--customCode`
option (`Highcharts.useSerialIds(true);`, with `--allowCodeExecution true`) — before
two repeat renders of the line chart. The ID stayed consistent **within** a single
render (used identically at every reference point in that one SVG), but a fresh
process invocation still produced a different ID than the previous one
(`highcharts-44tomdw-21-` vs. `highcharts-p3zp66k-21-`). `useSerialIds` does not
appear to fix cross-invocation determinism for this ID as exercised through the
export server; no other configuration option was found in the export server's own
README that addresses it. This should be read as "not fixed by the option tested," not
as a claim that no fix exists anywhere in Highcharts' full configuration surface.

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

This is three chart shapes (line, scatter, bubble), on one host, on one day, run by
the vendor whose product is being compared favorably. It establishes real,
reproducible orders-of-magnitude gaps in cold-start time, memory, and
dependency-surface size that hold consistently across all three shapes rather than
being an artifact of picking an easy chart; a serial warm-throughput gap that
persists (though narrower) even after removing cold-start and browser-launch cost
from the comparison entirely; one concrete, previously-unquantified
non-determinism finding in Highcharts Export Server's raw output that also
reproduces across all three shapes and survives the one documented mitigation
tested; and, favorably for the competitors, that the "13.6 s" Highcharts number is
specific to a one-process-per-render deployment and does not represent the product
run as its own documentation recommends. It does **not** establish results for chart
types outside these three, a production Linux/container measurement, concurrent
or parallel-request throughput (only serial warm requests were measured), or an
assessment of Highcharts' or Vega's actual security posture beyond the specific
advisories listed. None of the recurring-cost or willingness-to-pay claims in
`SC-PROD-003`'s validation gate are addressed by this document; only real interviews
close that gate.

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

Scatter and bubble repeat the same commands against
`stonecharts-scatter-spec.json` / `stonecharts-bubble-spec.json`,
`vega-lite-scatter-spec.json` / `vega-lite-bubble-spec.json`,
`highcharts-scatter-config.json` / `highcharts-bubble-config.json`, and
`chartjs-scatter-config.json` / `chartjs-bubble-config.json` respectively.

Sustained-throughput and `useSerialIds` reproduction:

```bash
# StoneCharts (Python) - 200 in-process renders after 1 untimed warm-up
python stonecharts_throughput.py stonecharts-spec.json 200

# StoneCharts (Go) - 20,000 in-process renders, batched for timer resolution
go run throughput.go stonecharts-spec.json 20000

# Vega/Vega-Lite - 200 in-process renders, fresh View per render
node throughput.js vega-lite-spec.json 200

# Highcharts Export Server - persistent server mode, then 10 warm HTTP requests
node node_modules/highcharts-export-server/bin/cli.js --enableServer 1 --host 127.0.0.1 --port 7801 &
curl -X POST -H "Content-Type: application/json" \
  -d '{"infile": <highcharts-config.json contents>, "type": "svg"}' \
  http://127.0.0.1:7801

# useSerialIds test (does not fix cross-invocation determinism - see above)
echo "Highcharts.useSerialIds(true);" > highcharts-customcode.js
node node_modules/highcharts-export-server/bin/cli.js \
  --infile highcharts-config.json --outfile out.svg --type svg \
  --customCode highcharts-customcode.js --allowCodeExecution true
```

The `measure.py` harness, the twelve equivalent chart specs (three shapes across four
targets), the throughput scripts, the raw per-run JSON output, `npm audit --json`
captures, and all rendered artifacts from this run are retained locally alongside
this document's evidence entries; they are not committed to source control (they are
throwaway measurement artifacts, not release fixtures).
