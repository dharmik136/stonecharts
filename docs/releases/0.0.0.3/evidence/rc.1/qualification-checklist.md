---
id: SC-REL-020
title: StoneCharts 0.0.0.3 Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.3
requirements: [REQ-CHART-002]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-27"
review_due: "2026-08-27"
supersedes: null
superseded_by: null
---

# 0.0.0.3 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `ca9a5bff0adf7acd5e4aa1ba9689dd74f86a911f`
- Generated at: `2026-07-27T11:13:05+05:30`

This pack records the governed release evidence state for `0.0.0.3` specifically. It
is a fresh, independently-generated pack, not a copy or overwrite of `0.0.0.1`'s or
`0.0.0.2`'s already-tagged `rc.1` evidence.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass, including scatter (freshly re-run for `GATE-S9`).
- [x] Shared validation parity and capability coverage pass, including scatter's new
      point-model element type.
- [x] Byte-identity gate: every existing line/column/area/bar golden confirmed
      unchanged after the point-model and linear-x-scale generalization landed,
      verified before any scatter-specific golden was added (not alongside it).
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual
      profile, performance, direct cross-render, and fuzz/property evidence are
      attached - the frozen `0.0.0.1`/`0.0.0.2` evidence for line/column/area/bar
      plus the new scatter-specific accessibility/security and performance baseline
      reviews (`SC-REL-018`, `SC-REL-019`) from `GATE-S9`.
- [x] Release evidence validator is present and passes against this manifest.
- [x] SBOM generation and validation, versioned `0.0.0.3`.
- [x] Provenance statement for the `0.0.0.3` candidate commit.
- [x] Package install matrix: Python wheel install (built and installed fresh at
      version `0.0.0.3`, smoke-tested importing and rendering `scatter` via the
      typed-construction path from the installed copy) and Go module consumption
      via local `replace` (rendering `scatter` through a separate consumer module
      using `DataPoints` directly), both proven on this commit.

## GATE-S10 acceptance

- A `0.0.0.3`-specific evidence pack (manifest, SBOM, provenance, hashes, package
  install matrix) is built here, independently of `0.0.0.1`'s and `0.0.0.2`'s `rc.1`
  packs.
- Built artifacts (Python wheel, Go module via local `replace`) install and execute
  `scatter` - the profile added by this release - proven fresh on this commit,
  including the typed-construction code paths whose point-model gap was found and
  fixed during `GATE-S9`.
- The evidence manifest validates against `docs/releases/0.0.0.3/evidence/manifest.schema.json`
  and references immutable, hash-verified results for this candidate commit.

## GATE-S11 sign-off

Not yet recorded. Tagging `0.0.0.3` remains a separate, later authorization
(`GATE-S11`), matching how `0.0.0.1`'s and `0.0.0.2`'s tags were each a distinct step
after their `rc.1` packs were built and validated.

## Still open before further publication

- [ ] `GATE-S11` product-owner/maintainer sign-off and the `0.0.0.3` source-control tag.
- [ ] Repository visibility / public distribution decision (not authorized yet;
      unchanged from `0.0.0.1`/`0.0.0.2`).
- [ ] Go module ecosystem-mapping decision (required before any Go tag; ADR 0007;
      unchanged from `0.0.0.1`/`0.0.0.2`).
- [ ] Public support channel sign-off (unchanged from `0.0.0.1`/`0.0.0.2`).
