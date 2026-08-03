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

`stoneverify` is the flagship conformance workflow described in
[`SC-PROD-003`](../product/visual-integrity-strategy.md): it renders one chart
specification, compares the result with an approved baseline, and produces a
local evidence bundle a customer keeps in their own repository or artifact system. This
document is the practical "how do I actually run this" guide; it does not restate the
strategy or positioning behind the tool.

## Prerequisites

- Python 3.9 or 3.14, with the `stonecharts` wheel installed. In a development
  checkout, `python tools/stonecharts_verify.py` remains a compatibility wrapper.
- A prebuilt `stoneverify-go-render` adapter binary, only if explicitly verifying
  the Go runtime (`--runtime go`). Resolve it with
  `--go-binary`, `STONEVERIFY_GO_BINARY`, or `PATH`. In a development checkout,
  `--from-source` can run the adapter via `go run` instead.
- No network access is required. Nothing in this workflow sends chart data anywhere.

## Compare a candidate against a baseline

First create or choose the approved baseline bundle:

```bash
stoneverify <path-to-spec.json> \
  --runtime python \
  --evidence <approved-baseline-dir>
```

Then compare a candidate render against it:

```bash
stoneverify <path-to-spec.json> \
  --baseline-evidence <approved-baseline-dir> \
  --baseline-note "approved in ticket SC-123" \
  --evidence <candidate-output-dir>
```

When `--baseline-evidence` is supplied and no runtime is specified, StoneVerify
defaults to a single Python render. This makes the release-to-release check useful
without requiring a second runtime. Add `--runtime go` only when the approved
baseline was also built with Go coverage.

Exit code `0` means the requested verification completed and passed. Exit code
`1` means verification completed but found differences or invalid evidence. Exit
code `2` is a CLI usage error. Exit code `3` is an invalid or unsupported chart
specification. Exit code `4` is a renderer or adapter execution failure. Exit
code `5` is reserved for resource-limit or timeout failures, and exit code `70`
is reserved for internal StoneVerify failures. When verification completes, the
evidence bundle explains exactly where the outputs diverged (see
[Reading a bundle](#reading-a-bundle-and-the-comparisonjson-file) below).

If the new approved baseline replaces an older one, record that relationship:

```bash
stoneverify <path-to-spec.json> \
  --baseline-evidence <approved-baseline-dir> \
  --supersedes-baseline <older-baseline-dir> \
  --baseline-note "replaces baseline after dependency upgrade review" \
  --evidence <candidate-output-dir>
```

The baseline record in `manifest.json` stores the baseline evidence directory,
baseline manifest hash, tool version, generation timestamp, optional superseded
baseline identity, and optional plain-text note.

## Cross-runtime proof

```bash
stoneverify <path-to-spec.json> \
  --runtime python --runtime go \
  --go-binary <path-to-stoneverify-go-render> \
  --evidence <output-directory>
```

This advanced proof checks that Python and Go produce byte-identical SVG for the
same spec. It remains useful for StoneCharts release qualification and adapter
testing, but cross-release baseline comparison is the primary pilot workflow.

## See it prove failure, not just success

A conformance tool that never demonstrates a failing case is not yet trustworthy.
Prove it fails honestly before trusting that it passes honestly:

```bash
stoneverify <path-to-spec.json> \
  --runtime python --runtime go \
  --go-binary <path-to-stoneverify-go-render> \
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
stoneverify --check-evidence <output-directory>

# Compare two previously generated bundles without re-rendering anything
stoneverify --compare-evidence <left-dir> <right-dir> \
  --compare-report <path-to-report.html>

# Compare a fresh single-runtime run against a previously approved bundle
stoneverify <path-to-spec.json> \
  --baseline-evidence <approved-baseline-dir> \
  --evidence <output-directory>
```

## CI-native reports

StoneVerify can write a JUnit-compatible XML report for CI systems that already
ingest test artifacts:

```bash
stoneverify <path-to-spec.json> \
  --runtime python --runtime go \
  --go-binary <path-to-stoneverify-go-render> \
  --evidence <output-directory> \
  --junit-report <output-directory>/junit.xml
```

In cross-runtime mode, the JUnit file contains one testcase per compared runtime
pair. In baseline mode, it contains one testcase per runtime being compared to
the approved baseline. Passing comparisons report zero failures; failing
comparisons include StoneVerify's semantic finding text, including the stable
`VERIFY.*` code, category, equality level, confidence, and basis. The JUnit file
is an integration artifact only; StoneVerify's own exit code is still what fails
or passes the CI job.

When `GITHUB_ACTIONS=true`, StoneVerify also emits GitHub-compatible workflow
annotations for failures, or a notice for a pass. If `GITHUB_STEP_SUMMARY` is set,
it appends a concise Markdown summary. This GitHub Actions behavior is automatic
and does not require `--junit-report`.

## Go adapter contract

StoneVerify treats the Go renderer as a process adapter, not as checked-out
source. The adapter interface is:

```bash
stoneverify-go-render <spec.json>     # writes rendered SVG to stdout
stoneverify-go-render --version       # writes adapter=, stonecharts=, module=
```

Any render failure must write a diagnostic to stderr and exit non-zero. The
Python CLI records the adapter's `stonecharts` and `module` fields in
`manifest.json`; if version reporting is unavailable, those fields are recorded
as `unknown` rather than being invented by the Python package.

## A worked sample

[`docs/quality/stoneverify-sample-evidence/`](stoneverify-sample-evidence/) is a real,
committed bundle generated from
[`charts/bubble/examples/basic.json`](../../charts/bubble/examples/basic.json) — open
`report.html` directly to see what a passing bundle looks like before running the
tool yourself. It is a fixed, illustrative sample, not a per-release evidence
artifact; it is not regenerated automatically and will not track future renderer
changes.

## Internal evaluation kit build

For internal review of the pilot workflow, build the self-contained evaluation kit:

```bash
python tools/build_stoneverify_eval_kit.py
```

The builder writes an ignored `dist/stoneverify-evaluation-kit/` directory and
`dist/stoneverify-evaluation-kit.zip`. The kit contains the built Python wheel,
the prebuilt Go adapter, one certified sample spec, the StoneVerify schemas, this
quickstart, and links-by-copy to the governed limits, robustness, security, and
supply-chain notes. Its own README is marked internal/build-only; it does not
authorize external distribution or commercial use.

After extracting the kit, verify it without a repository checkout:

```bash
python scripts/run_demo.py
```

The demo creates a local virtual environment, installs only from the kit's
`packages/` directory with `--no-index`, runs `stoneverify --demo-drift text`
against the included Go adapter, and expects exit code `1` because the drift is
intentional.

To run the same kit workflow against a fixture outside the repository examples,
pass a separate spec path after extracting the kit:

```bash
python scripts/run_demo.py --spec <path-to-external-fixture.json>
```

## CI integration

This repository's `quality` workflow includes a `stoneverify-pilot-gate` job. It
builds the Python wheel and Go adapter, installs StoneVerify from the wheel with
`--no-index`, creates an external fixture outside the repository examples, runs a
deliberate demo-drift proof, writes `junit.xml`, and uploads the evidence bundle.
The workflow also supports manual execution through `workflow_dispatch`, so the
pilot-gate path can be run directly from GitHub Actions after the workflow change
has been pushed.

For a customer repository, adapt the same pattern to the customer's own chart specs
and CI paths:

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
      - run: cd path/to/stonecharts/libs/go && go build -o /usr/local/bin/stoneverify-go-render ./cmd/stoneverify-go-render
      - run: |
          stoneverify \
            path/to/customer/chart-spec.json \
            --runtime python --runtime go \
            --evidence conformance-evidence \
            --junit-report conformance-evidence/junit.xml
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: stonecharts-conformance-evidence
          path: conformance-evidence
```

The job fails the pull request on a non-zero exit (real drift), emits GitHub
annotations/job-summary output when running inside GitHub Actions, and saves the
evidence bundle an auditor or reviewer opens to see exactly what changed. The
customer template still must be adapted and tested in the customer's own CI before
being relied on operationally.

## What this tool does not do

Hosted storage, approval workflows, identity, retention controls, audit logs, and
PDF/controlled document-generation output are explicitly deferred — see
[`SC-PROD-004`](../product/capability-matrix.md)'s deferred-capabilities list. This
tool produces local files; where they are stored and who approves them is the
customer's own process, not something StoneVerify manages today.
