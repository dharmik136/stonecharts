---
id: SC-REL-003
title: StoneCharts Alpha 1 Evidence Pack Format
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Alpha 1 Evidence Pack

This directory defines the release evidence format. Actual candidate evidence is
generated under a candidate-specific directory and is immutable after sign-off.

```text
evidence/<candidate>/
  manifest.json
  qualification-checklist.md
  tests/
  cross-render/
  browser/
  accessibility/
  benchmarks/
  security/
  sbom/
  provenance/
  packages/
  hashes.sha256
```

`manifest.json` is the index. It records every required evidence ID as passed, failed,
skipped, or unavailable and references files by relative path and SHA-256. Missing
evidence is never represented as passing. Raw machine output is retained alongside
human summaries.

Candidate evidence should not be committed until the release workflow exists and the
candidate is being qualified. Temporary local runs belong in ignored build output.

