---
id: SC-REL-002
title: StoneCharts 0.0.0.1 Qualification Checklist
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# 0.0.0.1 Qualification Checklist

Unchecked items are incomplete. This source checklist is copied into the immutable
release evidence directory for the candidate and completed there.

## Governance

- [ ] Controlled-document validation passes.
- [ ] Applicable normative documents are approved and not overdue.
- [ ] Every `must` requirement has passing release evidence.
- [ ] Open critical/high risks are closed or explicitly accepted with expiry.
- [ ] Product claims match the guarantee and known-limit contracts.

## Source and versions

- [ ] Git tree is clean and commit is immutable.
- [ ] Product version is `0.0.0.1`.
- [ ] Python package version is `0.0.0.1` everywhere.
- [ ] Source release tag is `0.0.0.1`.
- [ ] Any published Go module mapping is approved, valid, and recorded; `v0.0.0.1`
  is not used.
- [ ] Schema, SVG contract, runtime, and capability revisions are recorded.

## Correctness and parity

- [ ] Schema and both validators pass shared valid/invalid fixtures.
- [ ] Capability matrix rejects unsupported types/features without panic.
- [ ] Python and Go golden suites pass.
- [x] Direct cross-render sweep has zero byte differences.
- [ ] Signed stack and percent-domain invariants pass.
- [x] Category, Unicode, dimension, empty-data, and long-label edges pass.
- [ ] Fuzz/property run completes with recorded seed and limits.

## Runtime and accessibility

- [x] Automated runtime smoke passes for tooltip, legend, focus, keyboard, and ARIA state.
- [x] Local HTTP browser suite passes in the pinned Chromium profile. This is the next
      release gate after the automated smoke check.
- [x] Tooltip pointer and keyboard semantics pass.
- [x] Legend is pointer and keyboard operable with exposed state.
- [x] Focus order, appearance, Escape behavior, and hidden-series navigation pass.
- [x] Accessible name, description, and complete data table pass.
- [x] Manual keyboard and assistive-technology review is attached.

## Security and supply chain

- [ ] Injection and unsafe-value corpus passes.
- [ ] Dependency and vulnerability review is attached.
- [ ] SPDX SBOM is generated and validated.
- [ ] Provenance statement is generated and achieved status is truthful.
- [ ] All package, SBOM, provenance, and evidence files have SHA-256 hashes.
- [ ] Vulnerability reporting path is operational.

## Performance and packaging

- [ ] Benchmark environment and raw samples are captured.
- [ ] Baseline report covers small, business, dense, and stress profiles.
- [ ] Python wheel/source artifact installs in every supported Python runtime.
- [ ] Go source or module artifact can be fetched, tested, and used through its
  approved distribution mapping.
- [ ] Package contents and license metadata are reviewed.

## Publication

- [ ] Changelog, compatibility matrix, known limits, installation, and support policy
  are included.
- [ ] Evidence manifest validates against its schema.
- [ ] Artifact hashes are independently recomputed from the publication candidate.
- [ ] Product owner and maintainer sign-off are recorded.
- [ ] Tag and packages are published only after the evidence pack is sealed.
