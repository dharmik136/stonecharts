---
id: SC-REL-024
title: StoneCharts 0.0.0.4 Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.4
requirements: [REQ-CHART-003]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-28"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# 0.0.0.4 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `70a40aef96069b1df3e044f46e87c162f43a8c24`
- Generated at: `2026-07-28T11:02:18+05:30`

This pack records the governed release evidence state for `0.0.0.4` specifically. It
is a fresh, independently-generated pack, not a copy or overwrite of `0.0.0.1`'s,
`0.0.0.2`'s, or `0.0.0.3`'s already-tagged `rc.1` evidence.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass, including bubble (freshly re-run for `GATE-S12`).
- [x] Shared validation parity and capability coverage pass, including bubble's
      extended `{x,y,z}` point-model element type.
- [x] Byte-identity gate: every existing line/column/area/bar/scatter golden
      confirmed unchanged after the `Datum.z` field addition, verified before any
      bubble-specific golden was added (not alongside it).
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual
      profile, performance, direct cross-render, and fuzz/property evidence are
      attached - the frozen `0.0.0.1`/`0.0.0.2`/`0.0.0.3` evidence for
      line/column/area/bar/scatter plus the new bubble-specific
      accessibility/security and performance baseline reviews (`SC-REL-022`,
      `SC-REL-023`) from `GATE-S12`.
- [x] Release evidence validator is present and passes against this manifest.
- [x] SBOM generation and validation, versioned `0.0.0.4`.
- [x] Provenance statement for the `0.0.0.4` candidate commit.
- [x] Package install matrix: Python wheel install (built and installed fresh at
      version `0.0.0.4`, smoke-tested importing and rendering `bubble` via the
      typed-construction path from the installed copy) and Go module consumption
      via local `replace` (rendering `bubble` through a separate consumer module
      using `Series.DataPoints` with `Datum.Z` set directly), both proven on this
      commit.

## GATE-S13 acceptance

- A `0.0.0.4`-specific evidence pack (manifest, SBOM, provenance, hashes, package
  install matrix) is built here, independently of the prior three `rc.1` packs.
- Built artifacts (Python wheel, Go module via local `replace`) install and execute
  `bubble` - the profile added by this release - proven fresh on this commit.
- The evidence manifest validates against `docs/releases/0.0.0.4/evidence/manifest.schema.json`
  and references immutable, hash-verified results for this candidate commit.

## GATE-S14 sign-off

Not yet recorded. Tagging `0.0.0.4` remains a separate, later authorization
(`GATE-S14`), matching how `0.0.0.1`'s, `0.0.0.2`'s, and `0.0.0.3`'s tags were each a
distinct step after their `rc.1` packs were built and validated.

## Still open before further publication

- [ ] `GATE-S14` product-owner/maintainer sign-off and the `0.0.0.4` source-control tag.
- [ ] Repository visibility / public distribution decision (not authorized yet;
      unchanged from prior releases).
- [ ] Go module ecosystem-mapping decision (required before any Go tag; ADR 0007;
      unchanged from prior releases).
- [ ] Public support channel sign-off (unchanged from prior releases).
