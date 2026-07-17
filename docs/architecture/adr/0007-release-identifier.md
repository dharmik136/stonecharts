---
id: SC-ARCH-ADR-0007
title: Adopt 0.0.0.1 as the Canonical First Release Identifier
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# ADR 0007: Adopt 0.0.0.1 as the Canonical First Release Identifier

## Context

The first governed release was provisionally called `0.0.1-alpha.1`. The product owner
has selected `0.0.0.1` as the exact StoneCharts product identity for the first release.
Continuing to use competing names across planning, documentation, packages, evidence,
and GitHub would make qualification and support records ambiguous.

`0.0.0.1` has four numeric components and therefore is not a Semantic Versioning 2.0.0
identifier. Git and GitHub can use it directly, and Python packaging accepts four-part
release segments. Go module release tags require semantic-version-compatible tags, so
Go publication cannot pretend that `v0.0.0.1` is valid module versioning.

## Decision

- The canonical StoneCharts product, documentation, milestone, Project target, release
  record, and source tag identifier is exactly `0.0.0.1`.
- StoneCharts does not claim that this identifier follows Semantic Versioning.
- Python package metadata will use `0.0.0.1` before release qualification.
- No `v0.0.0.1` Go module tag will be published. Before any Go module publication,
  the distribution decision must approve a valid ecosystem mapping and record both the
  canonical product identifier and mapped module version in the evidence manifest.
- Existing `0.1.0` Python source metadata is historical, unqualified metadata and
  remains a release blocker until its implementation work is completed.
- No release tag is created as part of this planning decision.

## Consequences

All controlled release planning and GitHub execution records use one product identity.
Consumers will not be misled into treating a four-part identifier as SemVer. Package
publication cannot proceed until ecosystem mappings, artifact names, and support
channels are approved and tested.

The identifier is intentionally unusual. Documentation must write it exactly and must
not shorten it to `0.0.1`, append an unapproved alpha suffix, or silently substitute a
package-manager version.

## Rejected alternatives

- Keep `0.0.1-alpha.1`: contradicts the product-owner release decision.
- Call `0.0.0.1` SemVer: factually incorrect and unsafe for tooling assumptions.
- Publish `v0.0.0.1` as a Go module tag: not valid Go semantic-version tagging.
- Maintain two product release names: breaks traceability, support, and evidence lookup.
