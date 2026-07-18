---
id: SC-QUAL-002
title: StoneCharts Benchmark Specification
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PERF-001]
evidence: [BENCH-RENDER-BASELINE]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Benchmark Specification

## Purpose

The benchmark establishes reproducible performance and resource baselines. It does not
rank StoneCharts against unrelated libraries until equivalent workloads, output, and
environments can be defended.

## Workloads

| Profile | Shape | Purpose |
|---|---|---|
| Small | 1 series x 12 categories | CLI and report-card latency |
| Business | 8 series x 100 categories | Normal dashboard/report workload |
| Dense | 20 series x 1,000 categories | Large static output and DOM pressure |
| Stress | 20 series x 5,000 categories | Explicit limit discovery, not a default promise |

Each profile has line, grouped-column, and applicable stacked-column variants. Input
spec bytes and SHA-256 are stored with results. Random data uses a recorded generator
and seed.

## Metrics

- Cold and warm wall-clock render time.
- Throughput under a declared sequential or parallel model.
- p50, p95, p99, minimum, maximum, standard deviation, and sample count.
- Peak resident memory and language-specific allocations where supported.
- SVG and HTML output bytes and DOM element counts.
- Runtime initialization and first keyboard/tooltip interaction latency in the browser
  profile.

## Method

Record commit, dirty-tree state, product and package versions, compiler/interpreter,
dependencies, operating system, architecture, CPU, memory, power mode, container or
virtualization, and benchmark command. Pin locale and timezone. Disable unrelated
background work where practical.

Use at least five warm-up iterations and thirty measured iterations for normal
profiles unless variance analysis justifies another count. Run profile order in a
recorded deterministic or randomized sequence. Report raw samples in machine-readable
JSON and a generated human summary.

## Gates

Correctness gates remain absolute: benchmark output must validate and byte-match its
corpus. 0.0.0.1 first establishes a baseline. Absolute latency and memory budgets are
approved only after stable repeated measurements. Subsequent releases use a documented
regression budget derived from observed variance; a convenient percentage is not
invented in advance.

The governing budget policy is recorded in
[SC-CON-017](../contracts/performance-budgets.md).

Any accepted regression records the affected workload, measured change, reason,
product benefit, owner, and approval in the release manifest.
