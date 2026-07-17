---
id: SC-REL-001
title: StoneCharts 0.0.0.1 Release Plan
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-SCOPE-001, REQ-DET-001, REQ-VAL-001, REQ-CAP-001, REQ-STACK-001, REQ-STACK-002, REQ-LAYOUT-001, REQ-RUNTIME-001, REQ-A11Y-001, REQ-VIS-001, REQ-CUST-001, REQ-SEC-001, REQ-REL-001, REQ-PERF-001]
evidence: [TEST-DOCS-CONTROL, TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-VALIDATION-PARITY, TEST-CAPABILITY-MATRIX, TEST-STACK-SIGNED, TEST-PERCENT-DOMAIN, TEST-LAYOUT-MARGINS, TEST-XSS-ESCAPING, TEST-RUNTIME-BROWSER, REVIEW-ACCESSIBILITY-MANUAL, REVIEW-VISUAL-PROFILE, BENCH-RENDER-BASELINE, TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# 0.0.0.1 Release Plan

## Objective

Ship the first auditable proof of the StoneCharts thesis: line and column rendered
natively by Python and Go from one released specification, with canonical SVG parity,
safe validation, bounded customization, qualified browser behavior, and an immutable
evidence pack.

This is a pre-release. It does not promise a stable API, every designed chart type, a
hosted service, universal browser support, or universal pixel identity.

## Version mapping

| Surface | Version |
|---|---|
| Product and documentation | `0.0.0.1` |
| Python package (PEP 440) | `0.0.0.1` |
| Source release tag | `0.0.0.1` |
| Go module tag | Not yet approved; any published mapping must be valid Go semantic versioning |

Current Python metadata reports `0.1.0`; aligning package and runtime version metadata
is a release blocker. A `v0.0.0.1` Go tag is forbidden because it is not valid semantic
versioning. No release tag is created until distribution mappings and all release
surfaces satisfy [ADR 0007](../../architecture/adr/0007-release-identifier.md).

## Stage 0 exit gate

Implementation hardening begins after:

- Controlled documentation validates with no unresolved metadata or trace links.
- Product thesis, scope, guarantees, requirements, applicable ADRs, risks, test
  strategy, security controls, and this plan are approved.
- Every `must` requirement has acceptance criteria and a verification ID.
- Current implementation gaps are present in the risk register and work backlog.
- No new chart type or language work is active.

## Implementation stages

1. Reconcile active schema, runtime validators, package versions, and typed capability
   errors.
2. Correct signed normal stacking and restrict percent stacking as approved.
3. Add deterministic manual margins while preserving existing default goldens.
4. Correct category-length handling and all affected accessible table paths.
5. Correct runtime bar highlight, tooltip persistence, keyboard legend behavior, focus
   state, and hidden-series navigation.
6. Add browser, accessibility, fuzz, direct cross-render, and performance qualification.
7. Build packages, SBOM, provenance, checksums, and immutable release evidence.

Each stage has semantic tests before implementation and a separate reviewable commit.

## Hard release gates

- Active schema and capability manifests expose line and column only.
- Schema, Python, and Go accept and reject the same ratified domain.
- No user-controlled input causes a panic, unhandled exception, NaN, infinity, unsafe
  markup, or partial artifact.
- Signed normal-stack geometry and percent-domain rules pass in both languages.
- All approved canonical fixtures match byte for byte in Python and Go.
- Direct cross-render of all released examples and stress fixtures has zero diff.
- Chromium browser qualification passes through local HTTP.
- Manual keyboard and accessibility tasks pass or have an approved non-critical known
  limit.
- Benchmark baseline and compatibility matrix are complete.
- Python and Go packages install and execute from built artifacts.
- Release manifest, hashes, SBOM, provenance status, changelog, support status, and
  known limits are complete and immutable.

## Planning envelope

With one focused senior maintainer, Stage 0 is planned for two to four weeks and release
hardening for three to six additional weeks. This is an estimate, not a commitment.
Gate completion controls the release date; scope is reduced before quality gates are.

## Approval

The product owner approves scope and product claims. The maintainer approves technical
qualification. While both roles are held by one person, the release manifest records
`review_mode: self`; it does not represent the release as independently audited.
