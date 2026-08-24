---
id: SC-REL-035
title: StoneCharts 0.0.0.34 Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.34
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE, TEST-CERTIFICATION-MATRIX, TEST-PACKAGE-INSTALL]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# StoneCharts 0.0.0.34 release-candidate checklist

Candidate: `rc.1`
Source commit and tag: `038b69504bfbc879cfe9fe781e470bb7838b59f9` / `0.0.0.34`
Engineering status: approved after the commands in `qualification-results.json` pass.

The candidate requalifies all 36 charts against all eight SC-CERT gates, verifies
real Chromium behavior for every chart, installs warning-free Python artifacts in an
isolated environment, and records clean-tag provenance. Package-registry distribution
and a real customer pilot are explicitly deferred; neither is claimed by this pack.
