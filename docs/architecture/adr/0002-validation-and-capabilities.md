---
id: SC-ARCH-ADR-0002
title: Separate Schema Validity and Renderer Capability
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1 and later
requirements: [REQ-PROD-001, REQ-SCOPE-001, REQ-VAL-001, REQ-CAP-001]
evidence: [TEST-VALIDATION-PARITY, TEST-CAPABILITY-MATRIX]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# ADR 0002: Separate Schema Validity and Renderer Capability

## Context

The current schema and validators recognize design-only chart types while dispatchers
render only line and column. Structural validity and implementation capability are
therefore conflated, and accepted input can reach a panic or exception.

## Decision

Validation has two explicit phases:

1. Validate against the active versioned schema and semantic rules.
2. Validate the requested features against a machine-readable renderer capability
   manifest before rendering.

The 0.0.0.1 active schema contains only line and column. Unreleased designs remain
non-normative. A future spec valid under a newer schema may receive an unsupported
capability error from an older renderer. All user-input failures are typed and
non-fatal.

## Consequences

The release cannot claim a chart because a design or example exists. Schema, runtime
validators, capability manifests, and dispatch must move in lockstep. Older renderers
can fail safely when the specification evolves.

## Rejected alternatives

- Keep all future types in the active enum: it continues the broken contract.
- Treat capability failure as an internal panic: unsafe and not actionable.
- Maintain language-specific schemas: guarantees drift.

