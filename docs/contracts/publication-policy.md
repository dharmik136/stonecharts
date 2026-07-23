---
id: SC-CON-018
title: StoneCharts Publication Policy
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001, REQ-SEC-001]
evidence: [TEST-RELEASE-EVIDENCE, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Publication Policy

## Policy

StoneCharts 0.0.0.1 remains private until S3 evidence is complete. No public source or
package publication occurs before the release evidence pack, provenance, hashes, SBOM,
and support policy are sealed.

After S3 approval, publication may occur only through supportable channels that are
recorded in the release plan and supply-chain policy. Each channel must have an explicit
owner, support boundary, and rollback path.

## Required publication record

The release record must name:

- source publication path
- package publication path for each ecosystem
- evidence archive location
- support owner
- rollback or withdrawal path

## Non-claim

This policy does not promise public availability before release. It does not grant
support for unspecified mirrors, registries, or ad hoc distribution channels.

