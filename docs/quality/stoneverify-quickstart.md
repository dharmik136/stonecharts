---
id: SC-QUAL-004
title: StoneVerify Quick Start
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# StoneVerify Quick Start

`tools/stonecharts_verify.py` is the flagship conformance workflow described in
[`SC-PROD-003`](../product/visual-integrity-strategy.md): it renders one chart
specification through Python and Go, compares the output, and produces a local
evidence bundle a customer keeps in their own repository or artifact system. This
document is the practical "how do I actually run this" guide; it does not restate the
strategy or positioning behind the tool.

## Prerequisites

- Python 3.9 or 3.14, with this repository's `libs/python` package importable
  (`pip install -e "libs/python[dev]"` from the repository root, or run from a
  checkout where `stonecharts` is already installed).
- Go 1.26 on `PATH`, only if verifying the Go runtime (`--runtime go`, the default
  alongside Python). The tool shells out to `go run` directly; there is no separate
  Go build step to run yourself.
- No network access is required. Nothing in this workflow sends chart data anywhere.

## Run it against one chart

```bash
python tools/stonecharts_verify.py <path-to-spec.json> \
  --runtime python --runtime go \
  --evidence <output-directory>
```

Exit code `0` and `StoneVerify PASS: All requested runtime outputs are byte-identical.`
means the two runtimes produced byte-identical SVG for that spec. A non-zero exit
means they did not, and the evidence bundle explains exactly where the outputs
diverged (see [Reading a bundle](#reading-a-bundle-and-the-comparisonjson-file)
below).

## See it prove failure, not just success

A conformance tool that never demonstrates a failing case is not yet trustworthy.
Prove it fails honestly before trusting that it passes honestly:

```bash
python tools/stonecharts_verify.py <path-to-spec.json> \
  --runtime python --runtime go \
  --demo-drift text \
  --evidence <output-directory>
```

This applies a deliberate, clearly-labeled mutation to the last runtime's output and
must exit non-zero with `StoneVerify FAIL: Runtime outputs differ.` `--demo-drift` is
for exactly this demonstration; it must never be used to accept a real spec as
passing.

## Reading a bundle and the `comparison.json` file

A completed run produces:

```text
<output-directory>/
├── manifest.json        # tool identity/version, timestamp, status, drift label
├── input-spec.json      # the exact spec that was rendered, for hash verification
├── python-output.svg    # or whichever runtimes were requested
├── go-output.svg
├── comparison.json      # per-runtime byte size, tag inventory, first difference, likely cause
├── report.html          # human-readable version of comparison.json
└── checksums.txt        # sha256 of every file above, for tamper detection
```

`comparison.json` classifies any difference runtime-by-runtime: it separates "the
input spec itself changed" from "the same spec rendered differently," reports the
exact byte offset and line of the first difference, and names a likely cause rather
than just dumping a diff. Read `report.html` in a browser for the same information
formatted for a non-technical reviewer.

## Checking a bundle later, or comparing two bundles

```bash
# Did this stored bundle get tampered with, or is it internally consistent?
python tools/stonecharts_verify.py --check-evidence <output-directory>

# Compare two previously generated bundles without re-rendering anything
python tools/stonecharts_verify.py --compare-evidence <left-dir> <right-dir> \
  --compare-report <path-to-report.html>

# Compare a fresh run against a previously approved bundle
python tools/stonecharts_verify.py <path-to-spec.json> \
  --baseline-evidence <approved-baseline-dir> \
  --evidence <output-directory>
```

## A worked sample

[`docs/quality/stoneverify-sample-evidence/`](stoneverify-sample-evidence/) is a real,
committed bundle generated from
[`charts/bubble/examples/basic.json`](../../charts/bubble/examples/basic.json) — open
`report.html` directly to see what a passing bundle looks like before running the
tool yourself. It is a fixed, illustrative sample, not a per-release evidence
artifact; it is not regenerated automatically and will not track future renderer
changes.

## Dropping this into a customer's own CI

The following is a template, not a workflow this repository runs itself (StoneVerify
is a tool this repository ships, not a check on its own PRs). Adapt the paths to
wherever the pilot customer's own chart specs and CI live:

```yaml
# .github/workflows/stonecharts-verify.yml (in the CUSTOMER's own repository)
name: StoneCharts conformance
on: [pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.14" }
      - uses: actions/setup-go@v5
        with: { go-version: "1.26" }
      - run: pip install -e "path/to/stonecharts/libs/python[dev]"
      - run: |
          python path/to/stonecharts/tools/stonecharts_verify.py \
            path/to/customer/chart-spec.json \
            --runtime python --runtime go \
            --evidence conformance-evidence
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: stonecharts-conformance-evidence
          path: conformance-evidence
```

The job fails the pull request on a non-zero exit (real drift), and the uploaded
evidence bundle is the artifact an auditor or reviewer opens to see exactly what
changed. This template is illustrative; it has not been run in a real customer CI
environment and should be adapted and tested there before being relied on.

## What this tool does not do

Hosted storage, approval workflows, identity, retention controls, audit logs, and
PDF/controlled document-generation output are explicitly deferred — see
[`SC-PROD-004`](../product/capability-matrix.md)'s deferred-capabilities list. This
tool produces local files; where they are stored and who approves them is the
customer's own process, not something StoneVerify manages today.
