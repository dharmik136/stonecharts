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
evidence: [BENCH-COMPETITOR-HIGHCHARTS-20260729, BENCH-COMPETITOR-VEGA-20260729, BENCH-COMPETITOR-QUICKCHART-20260729, BENCH-COMPETITOR-ECHARTS-20260729, BENCH-COMPETITOR-PLOTLY-20260729]
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# Competitor Benchmark Results (2026-07)

This is a completed measurement run under
[`SC-PROD-005`](../product/competitor-benchmark-methodology.md). It reports what was
actually measured on one date, on one host, against the three targets named in the
[`DEC-017`](../project/decisions.md) brief, plus two additional targets (ECharts,
Plotly/Kaleido) added afterward under the same methodology to broaden the evidence
base. It supersedes no hypothesis in [`SC-PROD-003`](../product/visual-integrity-strategy.md);
it is the first evidence toward validating it.

**Coverage is uneven by design, and that unevenness is disclosed rather than
smoothed over:** Highcharts Export Server, Vega/Vega-Lite, and QuickChart were
measured across six chart shapes (line, scatter, bubble, area, column, bar).
ECharts and Plotly/Kaleido were added later and measured on the line chart only.
Do not read a blank cell elsewhere in this document as "not applicable" — it means
"not yet measured for that target."

## Method summary

- **Date:** 2026-07-29 (initial three-shape, three-target run and its extension to
  area/column/bar and to ECharts/Plotly both happened the same day, in separate
  measurement sessions hours apart).
- **Host:** Windows 11 Pro (build 10.0.26200), 16 logical CPUs, single developer
  machine. No other CPU-intensive process was deliberately started during timed
  measurement, following the same clean-run discipline used for StoneCharts' own
  release benchmarks (see [benchmark-spec.md](benchmark-spec.md)). **Disclosed
  deviation:** the area/column/bar cold-start numbers were measured several hours
  into the same long session as the line/scatter/bubble numbers, at ~23-26% baseline
  CPU load (checked via `wmic cpu get loadpercentage`) rather than an idle host, and
  read 20-60% higher across the board for both StoneCharts and Highcharts than the
  original line/scatter/bubble batch. This was checked, not ignored: measurements
  were re-run once load was confirmed non-zero-but-modest, and the relative gap
  between targets held even though the absolute numbers are session-dependent.
  Treat cross-shape absolute-time comparisons within this document with that caveat;
  the orders-of-magnitude gaps between targets are not affected by it.
- **Charts under test:** six chart shapes, each expressed as the equivalent native
  config for every target measured on that shape: a two-series, twelve-category
  **line** chart (`Monthly Average Temperature`, Tokyo vs. London); a 15-point
  single-series **scatter** chart (`Response Latency by Sample`); a 6-point
  single-series **bubble** chart (`Endpoint Latency vs Payload`, `[x, y, z]`
  triples); a two-series **area** chart (`Memory Usage by Region`); a single-series
  **column** chart (`HTTP Requests per Interval`); and a single-series **bar**
  (horizontal) chart (`Top API Endpoints by Request Volume`). All six mirror
  StoneCharts' own certified `charts/<type>/examples/basic.json` fixtures. A
  **combo** chart was considered and rejected: it is not in StoneCharts' certified
  chart-type list (`area`, `bar`, `bubble`, `column`, `line`, `scatter` only, per
  `libs/go/capabilities.go`), so there is no certified StoneCharts baseline to
  compare it against. For Chart.js's bubble dataset, which takes a literal pixel
  radius rather than a size value, the six radii were precomputed with StoneCharts'
  own published size-scale formula
  (`r = 4 + 28 * sqrt(clamp01((z - zmin) / (zmax - zmin)))`, `RMIN=4`, `RMAX=32`) so
  the rendered bubble areas are comparable, not just the raw data. Source specs are
  in the evidence bundle (see [Reproduction](#reproduction)).
- **Harness:** a fresh child process per run, wall-clock timed from spawn to exit,
  peak resident-set size sampled by polling the process and all of its descendants
  (`psutil`) every 5 ms. This matters for the headless-browser targets, whose
  renderer runs as a child process the parent alone does not account for.
- **Versions measured:** StoneCharts `4eff89a`..`eb3228a` (this repository, Python
  3.14.4 / Go 1.26.4); `vega@5.33.1` + `vega-lite@5.23.0` on Node v24.15.0;
  `highcharts-export-server@5.1.0` (bundling `puppeteer@22.15.0`) on Node v24.15.0;
  QuickChart's public hosted endpoint at `https://quickchart.io/chart` as served on
  the measurement date; `echarts@6.1.0` on Node v24.15.0 (server-side SVG SSR mode,
  no browser); `plotly@6.9.0` + `kaleido@1.3.0` on Python 3.14.4.
- **Docker for Highcharts:** an attempt was made to start Docker Desktop
  (`v29.6.1` CLI installed) specifically to re-measure Highcharts Export Server via
  its official container image instead of the npm-CLI fallback. It failed with a
  concrete, diagnosed error: `getting backend binary path: cannot find registry key
  "SOFTWARE\Docker Inc.\Docker Desktop"` — the Desktop application itself is not
  fully installed/initialized on this host, distinct from the CLI tooling being
  present. This was not worked around (fixing a local Docker Desktop installation is
  outside a benchmark measurement's scope); the npm-CLI measurement remains in use
  and the same "this likely understates Highcharts' real containerized cost"
  caveat from the original run still applies.

## Operational footprint

Cold-start wall-clock time and peak memory for one fresh-process render of the
equivalent chart. StoneCharts and Vega ran 10 timed invocations per chart type; the
Highcharts Export Server ran 5 per chart type (at ~13-15 s per run, 5 gave a stable
median without an excessive total run time). QuickChart is a hosted call, not a local
process — its numbers are network request latency, reported separately below, not
merged into these tables.

### Line chart

The only shape measured against all five targets:

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.074 s | 0.070-0.336 s | 10.8 MB |
| StoneCharts (Python) | 0.124 s | 0.102-0.133 s | 20.8 MB |
| ECharts (Node, server-side SVG SSR, no browser) | 1.259 s | 1.079-1.342 s | 60.5 MB |
| Vega/Vega-Lite (Node, no browser) | 1.057 s | 0.987-1.093 s | 83.5 MB |
| Plotly/Kaleido (Python, drives a headless Chrome via `choreographer`) | 3.882 s | 3.850-3.957 s | 588.6 MB |
| Highcharts Export Server (Node + Puppeteer/Chromium) | 13.607 s | 13.332-14.298 s | 552.9 MB |

The Go outlier at 0.336 s was the first run in the batch (cold OS file-cache); the
remaining 9 runs were 0.070-0.078 s. Plotly's Kaleido export path also drives a real
headless browser (via `choreographer`, not Puppeteer) and lands between the two
pure-JS-runtime targets (Vega, ECharts) and Highcharts' Puppeteer/Chromium cost —
one more real data point that "a JS charting library's static-export path frequently
means a bundled browser," not something unique to Highcharts.

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

### Area chart

Measured several hours later in the same session; see the disclosed CPU-load
deviation in [Method summary](#method-summary) before comparing absolute times
across shapes.

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.136 s | 0.108-0.175 s | 10.2 MB |
| StoneCharts (Python) | 0.188 s | 0.171-0.233 s | 21.0 MB |
| Vega-Lite (`area` mark, no browser) | not measured | - | - |
| Highcharts Export Server | 17.816 s | 16.166-17.880 s | 537.3 MB |

### Column chart

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.124 s | 0.115-0.160 s | 8.7 MB |
| StoneCharts (Python) | 0.187 s | 0.174-0.266 s | 20.9 MB |
| Highcharts Export Server | 17.665 s | 16.059-17.823 s | 539.3 MB |

### Bar chart (horizontal)

| Target | Median cold-start | Min-max | Median peak RSS (process tree) |
|---|---:|---:|---:|
| StoneCharts (Go) | 0.097 s | 0.088-0.105 s | 10.2 MB |
| StoneCharts (Python) | 0.187 s | 0.146-0.222 s | 21.0 MB |
| Highcharts Export Server | 17.856 s | 16.289-18.298 s | 535.8 MB |

Vega-Lite's cold-start was rendered and consistency-checked for area/column/bar (see
[Cross-invocation consistency](#cross-invocation-consistency)) but its timed
cold-start measurement was not re-run for these three shapes — an honest gap, not a
zero. The area/column/bar Highcharts numbers (~16-18 s) read higher than the
line/scatter/bubble batch (~13-15 s); given the disclosed CPU-load difference between
sessions, this is more likely session-to-session variance than a per-shape effect,
but it was not isolated further.

The orders-of-magnitude gaps hold consistently across all six chart shapes measured:
they are not an artifact of the line chart being an easy case for any one target.

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

This section measures one connection at a time, sequentially. See the next section
for genuinely concurrent load.

## Concurrent load

16 simultaneous requests/processes (matching this host's 16 logical CPUs), line
chart, using `ThreadPoolExecutor` to fire all 16 at once rather than one after
another:

| Target | Concurrency | Result | Overall wall time | Effective req/s |
|---|---:|---|---:|---:|
| StoneCharts (Go), 16 concurrent processes | 16 | 16/16 succeeded | 0.281 s | 57.0 |
| StoneCharts (Python), 16 concurrent processes | 16 | 16/16 succeeded | 0.434 s | 36.9 |
| Vega, 16 concurrent processes | 16 | 16/16 succeeded | 3.901 s | 4.1 |
| QuickChart, 16 concurrent hosted requests | 16 | 16/16 succeeded | 1.608 s | 10.0 |
| Highcharts Export Server, 16 concurrent requests **right as the pool signaled ready** | 16 | **6/16 succeeded, 10 failed** | 9.870 s | 1.6 (on the 6 that succeeded) |
| Highcharts Export Server, second 16-request burst immediately after (pool now scaled from handling the first) | 16 | 16/16 succeeded | 0.500 s | 32.0 |

The Highcharts result is the most important finding in this section and is reported
in full rather than only the favorable second number: a fresh Highcharts Export
Server, hit with a burst of concurrent requests at the moment its own log reports
"the pool is ready," rejects **10 of 16** requests outright while its worker pool
(configured `min: 4, max: 8`) scales up to meet the burst. The second identical
burst, fired immediately after against the now-scaled pool, succeeds completely and
quickly. This is a real, load-dependent failure mode a production deployment would
need to protect against (e.g. a queue in front of the pool, pre-warming to `max`
workers, or a slower ramp of incoming traffic) — it is not present in
StoneCharts, Vega, or QuickChart's concurrent results, all of which succeeded
16/16 on a single attempt with no warm-up burst required.

Vega's concurrent-process number (4.1 effective req/s) is lower than its serial warm
number would suggest, because this test spawns 16 full processes at once (each
paying its own ~1 s cold-start cost and contending for CPU), not 16 requests against
one already-warm process — it is answering a different question ("what if 16 cold
Vega processes start at once") than the warm-throughput section above ("what if one
warm process serves 200 requests in a row").

## Cross-invocation consistency

Each target rendered the same input twice through its own supported path, for every
chart shape it was measured on; outputs were compared byte-for-byte.

| Target | Line | Scatter | Bubble | Area | Column | Bar | Detail |
|---|---|---|---|---|---|---|---|
| StoneCharts | Identical | Identical | Identical | Identical | Identical | Identical | Also byte-identical **across** the Python and Go renderers on every chart shape, not just across two runs of one renderer — this is the product's core contract, not a benchmark finding. |
| Vega/Vega-Lite | Identical | Identical | Identical | Identical | Identical | Identical | Every `node render.js` invocation of a given spec produced identical SVG bytes, across all six chart shapes. |
| QuickChart | Identical | Identical | Identical | Identical | Identical | Identical | Every pair of hosted requests with the same Chart.js config produced identical PNG bytes on every shape. |
| ECharts | Identical | not measured | not measured | not measured | not measured | not measured | Two `render.js` invocations of the line chart produced identical SVG bytes. |
| Highcharts Export Server | **Differs** | **Differs** | **Differs** | **Differs** | **Differs** | **Differs** | Every chart shape reproduced the same finding: same-length output, byte-different at the same offset (char 4211, line 79) every single time across all six shapes. The diff is confined to a randomly generated per-render instance ID string (e.g. `highcharts-8sa4j9f-21-` vs. `highcharts-ats9qkf-21-`) embedded in `clipPath`/`id` attributes and their references, repeated at every point that ID is used. |
| Plotly/Kaleido | **Differs** | not measured | not measured | not measured | not measured | not measured | Two `fig.write_image()` calls for the identical figure produced same-length output (12,343 B both), byte-different starting at char 267 — the very start of the file. The diff is a random per-render ID (e.g. `defs-98fac5` vs. `defs-8f0ea1`) baked into `clipPath` IDs **and** into trace group class names (`trace2ca153` vs. `traceeb2f16`), the same category of defect as Highcharts, independently discovered in a completely different rendering engine. |

**Two of the five competitors tested (Highcharts, Plotly) share the exact same class
of defect** — a random per-render ID embedded in the output that makes raw-byte
conformance checking impossible without the caller stripping it first. StoneCharts,
Vega, ECharts, and QuickChart do not exhibit it. This is reported as a pattern across
independently-built rendering engines, not evidence about any one vendor's
engineering quality specifically.

The Highcharts finding means a naive byte-diff or content-hash conformance check
against raw Highcharts Export Server SVG output will report a false change on every
regeneration, even with no configuration change, and it reproduces identically across
all six chart shapes tested rather than being specific to one chart's geometry. This
was not evaluated for whether the drawn geometry is otherwise pixel-identical beyond
the ID strings; only the raw SVG bytes were diffed. The same caveat applies to the
Plotly finding.

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
| ECharts (as measured) | None | The SSR `render.js` harness compiles and renders fully in-process; no network call was made during a render. |
| Plotly/Kaleido (as measured) | None | `choreographer` drives a local headless browser binary already resolved on disk; no network call was made during a render. |
| Highcharts Export Server | None, once the dependency cache is populated | The CLI's first-ever run (see [operational footprint](#operational-footprint)) fetched Highcharts core and module scripts from `code.highcharts.com` before rendering; once cached, no measured render made a network call. A deployment that discards its cache between invocations would re-incur this fetch each time. |
| QuickChart | Always | The service is a hosted third-party API by design; every render sends the chart configuration to `quickchart.io` over the network. This is not a defect, it is the product's operating model, and it is the reason regulated/air-gapped buyers named in `SC-PROD-003` disqualify it. |

## Dependency and CVE surface

Snapshot as of the exact versions installed on the measurement date; will drift as
upstream releases patches.

| Target | Direct + transitive runtime dependencies | Audit findings |
|---|---:|---|
| StoneCharts (Python) | 0 | `pyproject.toml` declares `dependencies = []`. |
| StoneCharts (Go) | 0 | `go.mod` has no `require` block; stdlib only. |
| ECharts | 3-4 | `npm audit`: **0 vulnerabilities**. Apache-2.0 licensed. |
| Vega + Vega-Lite | 84 | `npm audit`: 6 **high**-severity advisories on the installed version ranges, all cross-site-scripting issues in `vega`, `vega-expression`, `vega-functions`, `vega-lite`, `vega-parser`, and `vega-view` (`toString`/`setdata` expression-evaluation abuse under `VEGA_DEBUG`). |
| Plotly + Kaleido | 9 (`plotly`, `kaleido`, `choreographer`, `logistro`, `narwhals`, `orjson`, `packaging`, `platformdirs`, `simplejson`) | `pip-audit`, run in an **isolated venv** containing only these 9 packages (a first attempt against the machine's general Python environment produced noise from unrelated installed packages and was discarded as an invalid measurement): **0 vulnerabilities** in the plotly/kaleido dependency tree itself. `pip-audit` additionally flagged 4 advisories in `pip` (the packaging tool used to install the audit tool into the venv), which are not a plotly/kaleido runtime dependency and are excluded from this count. |
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
as a surprise finding. ECharts and Plotly/Kaleido were not checked for provenance
attestations with the same rigor as the original three targets (no `npm view
dist.attestations` or equivalent PyPI check was completed) — an honest gap in this
document's coverage, not a claim that they lack provenance.

## What this does and does not establish

This is six chart shapes against three targets (Highcharts, Vega, QuickChart) and one
chart shape against two more targets (ECharts, Plotly), on one host, across a few
hours of one day, run by the vendor whose product is being compared favorably. It
establishes real, reproducible orders-of-magnitude gaps in cold-start time, memory,
and dependency-surface size that hold consistently across every shape measured
rather than being an artifact of picking an easy chart; a serial warm-throughput gap
that persists (though narrower) even after removing cold-start and browser-launch
cost from the comparison entirely; a concurrent-load failure mode in Highcharts
Export Server (10 of 16 simultaneous requests rejected while its pool scales up from
a cold start) that does not appear in StoneCharts, Vega, or QuickChart's concurrent
results; and — independently found in two unrelated rendering engines — a
non-determinism defect (a random ID baked into output) in both Highcharts Export
Server and Plotly/Kaleido that survives the one documented Highcharts mitigation
tested and was not found in StoneCharts, Vega, ECharts, or QuickChart. It also
establishes, favorably for the competitors, that the "13.6 s" Highcharts number is
specific to a one-process-per-render deployment and does not represent the product
run as its own documentation recommends. It does **not** establish results for chart
shapes beyond line/scatter/bubble/area/column/bar, results for ECharts or Plotly on
any shape besides line, a production Linux/container measurement (the Docker
comparison was attempted and blocked by a local installation issue, not run), an
assessment of any target's actual security posture beyond the specific advisories
listed, or release-provenance findings for ECharts/Plotly checked with the same rigor
as the original three targets. None of the recurring-cost or willingness-to-pay
claims in `SC-PROD-003`'s validation gate are addressed by this document; only real
interviews close that gate.

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

Scatter, bubble, area, column, and bar repeat the same commands against
`stonecharts-<shape>-spec.json`, `vega-lite-<shape>-spec.json`,
`highcharts-<shape>-config.json`, and `chartjs-<shape>-config.json` respectively.

ECharts and Plotly/Kaleido (line chart only):

```bash
# ECharts - server-side SVG SSR, no browser
npm install echarts
python measure.py echarts-line 10 -- node render.js echarts-line-config.json out-echarts.svg

# Plotly/Kaleido - static export via a real headless browser (choreographer)
pip install plotly kaleido
python measure.py plotly-kaleido 5 -- python plotly_render.py out-plotly.svg
```

Concurrent load (16 simultaneous requests/processes):

```bash
# StoneCharts / Vega: 16 concurrent process invocations
python concurrent_load.py process 16 ./stonecharts_render.exe stonecharts-spec.json out.svg
python concurrent_load.py process 16 python stonecharts_render_cli.py stonecharts-spec.json out.svg
python concurrent_load.py process 16 node render.js vega-lite-spec.json out.svg

# QuickChart: 16 concurrent hosted requests
python concurrent_load.py quickchart-http 16 chartjs-config.json

# Highcharts Export Server: start the persistent server, wait for "pool is ready"
# in its own log, then fire 16 concurrent requests
node node_modules/highcharts-export-server/bin/cli.js --enableServer 1 --host 127.0.0.1 --port 7801 &
python concurrent_load.py highcharts-http 16 highcharts-config.json
```

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

The `measure.py` harness, the concurrent-load harness, the equivalent chart specs
(six shapes across the original three targets, one shape across all five), the
throughput scripts, the isolated Plotly/Kaleido venv, the raw per-run JSON output,
`npm audit --json` / `pip-audit` captures, and all rendered artifacts from this run
are retained locally alongside this document's evidence entries; they are not
committed to source control (they are throwaway measurement artifacts, not release
fixtures).
