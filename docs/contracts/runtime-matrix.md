---
id: SC-CON-015
title: StoneCharts Supported Runtime Matrix
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1 and later
requirements: [REQ-RUNTIME-001, REQ-REL-001]
evidence: [TEST-RUNTIME-BROWSER, TEST-RELEASE-EVIDENCE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-29"
review_due: "2026-09-29"
supersedes: null
superseded_by: null
---

# Supported Runtime Matrix

## Supported profiles

StoneCharts supports only the following qualification profiles, unchanged since
0.0.0.1 through the current release:

| Area | Supported profile |
|---|---|
| Python | 3.9 and 3.14 |
| Go | 1.26 |
| Browser runtime | Chromium on the pinned desktop Linux qualification profile, exercised through local HTTP |
| Operating system | Desktop Linux qualification profile used by browser evidence |
| Exporter | No certified exporter profile |

## Evidence basis

- Python qualification is exercised in CI across the recorded version matrix.
- Go qualification is exercised from the module version declared in `libs/go/go.mod`.
- Browser qualification is exercised through a local HTTP harness against the pinned
  Chromium profile.
- Exporter behavior remains outside the certified support claim until a visual
  profile is approved.

## Support rule

Anything outside the supported profiles above is experimental or untested. StoneCharts
does not imply support for other Python versions, other Go versions, other browsers,
mobile profiles, host-specific desktop variations, or any exporter not named here.

## Relationship to other contracts

This matrix narrows the general runtime and release language in the plan and test
strategy. It does not expand the browser, accessibility, or export guarantees beyond the
named profiles.
