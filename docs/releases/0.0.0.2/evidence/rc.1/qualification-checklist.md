---
id: SC-REL-016
title: StoneCharts 0.0.0.2 Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# 0.0.0.2 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `92b3a40b291fc2106050129a89f8d16dffcc393c`
- Generated at: `2026-07-26T21:50:09+05:30`

This pack records the governed release evidence state for `0.0.0.2` specifically. It
is a fresh, independently-generated pack, not a copy or overwrite of `0.0.0.1`'s
already-tagged `rc.1` evidence.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass, including bar (freshly re-run for `GATE-S6`).
- [x] Shared validation parity and capability coverage pass, including bar.
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual
      profile, performance, direct cross-render, and fuzz/property evidence are
      attached - the frozen `0.0.0.1` evidence for line/column/area plus the new
      bar-specific accessibility/security and performance baseline reviews
      (`SC-REL-014`, `SC-REL-015`) from `GATE-S6`.
- [x] Release evidence validator is present and passes against this manifest.
- [x] SBOM generation and validation, versioned `0.0.0.2`.
- [x] Provenance statement for the `0.0.0.2` candidate commit.
- [x] Package install matrix: Python wheel install (built and installed fresh at
      version `0.0.0.2`, smoke-tested importing and rendering `bar` from the
      installed copy) and Go module consumption via local `replace` (rendering
      `bar` through a separate consumer module), both proven on this commit.

## GATE-S7 acceptance

- A `0.0.0.2`-specific evidence pack (manifest, SBOM, provenance, hashes, package
  install matrix) is built here, independently of `0.0.0.1`'s `rc.1` pack.
- Built artifacts (Python wheel, Go module via local `replace`) install and execute
  `bar` - the profile added by this release - proven fresh on this commit.
- The evidence manifest validates against `docs/releases/0.0.0.2/evidence/manifest.schema.json`
  and references immutable, hash-verified results for this candidate commit.

## GATE-S8 sign-off

Not yet recorded. Tagging `0.0.0.2` remains a separate, later authorization
(`GATE-S8`), matching how `0.0.0.1`'s tag was a distinct step after its `rc.1` pack
was built and validated.

## Still open before further publication

- [ ] `GATE-S8` product-owner/maintainer sign-off and the `0.0.0.2` source-control tag.
- [ ] Repository visibility / public distribution decision (not authorized yet;
      unchanged from `0.0.0.1`).
- [ ] Go module ecosystem-mapping decision (required before any Go tag; ADR 0007;
      unchanged from `0.0.0.1`).
