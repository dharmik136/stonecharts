---
id: SC-SEC-002
title: StoneCharts Supply-Chain Policy
status: proposed
classification: normative
owner: security-contact
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-SEC-001, REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Supply-Chain Policy

## Objectives

Consumers must be able to identify what source, inputs, toolchains, and process produced
each distributed artifact. 0.0.0.1 targets an SPDX SBOM and SLSA-compatible build
provenance statement; it MUST report the achieved level accurately rather than claim a
level from planned controls.

## Source controls

- Releases originate from an immutable Git commit with a clean tree.
- Release tags are not moved or reused.
- Contract-affecting changes receive review according to the documented review mode.
- Generated artifacts are not committed as source unless the release process requires
  and verifies them.

## Dependency controls

- Runtime dependencies remain minimal and are declared in ecosystem manifests.
- Development and release dependencies are version-constrained and recorded.
- Third-party GitHub Actions are pinned to immutable commit SHAs with readable
  release-tag comments and receive automated update pull requests.
- New dependencies receive license, maintenance, vulnerability, size, and determinism
  review.
- Font files and export engines are dependencies and follow the same review.
- Vulnerability scanning results are captured in release evidence, including accepted
  findings and rationale.

## Build and package controls

The release workflow builds Python and Go artifacts in a pinned environment, runs all
qualification gates, records package contents, and computes SHA-256 hashes. It produces:

- Package artifacts and checksums.
- SPDX SBOM covering release dependencies and bundled assets.
- Provenance identifying source commit, builder, invocation, and materials.
- Test, benchmark, and compatibility evidence references.
- Known limits and security finding disposition.

Signing and key management are not considered implemented until the key lifecycle,
protected storage, rotation, revocation, and verification instructions are approved.

## Verification

The evidence manifest is validated before tag publication. Consumers receive commands
for checksum and provenance verification. A release with missing provenance may be
published only if it explicitly reports that status and Alpha policy permits it; it
must not present planned provenance as completed.
