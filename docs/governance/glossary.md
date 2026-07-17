---
id: PC-GOV-002
title: PeakCharts Controlled Glossary
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: all
requirements: [REQ-PROD-001]
evidence: []
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Controlled Glossary

- **Active schema:** The versioned public schema whose values are supported for a
  release. Design-only chart types are not members of the active schema.
- **Adaptive runtime:** Browser behavior whose result depends on declared environment
  inputs such as viewport, container bounds, pointer position, or focus state.
- **Canonical SVG:** UTF-8 SVG serialization produced by a certified renderer under
  a named contract version, including element order, attribute order, escaping,
  number formatting, whitespace, and line-ending rules.
- **Capability:** A renderer feature it can execute, distinct from structural schema
  validity. Capabilities include chart types, stacking modes, and contract versions.
- **Certified language:** A language implementation that passes the complete required
  conformance corpus for the release and publishes a supported runtime matrix.
- **Certified visual profile:** A pinned font, viewer/export engine, configuration,
  and environment under which visual comparisons are qualified.
- **Contract:** A normative, versioned description of accepted input, emitted output,
  behavior, errors, or compatibility.
- **Evidence:** A stable test, benchmark, review, or audit definition plus an immutable
  result captured for one release candidate.
- **Golden:** A reviewed canonical output fixture. A golden proves regression parity;
  it does not by itself prove that the behavior is semantically correct.
- **Guarantee profile:** A named boundary describing exactly what PeakCharts commits
  to reproduce and the conditions under which the commitment applies.
- **Renderer:** A language-specific implementation that validates a chart spec and
  produces canonical SVG without requiring a browser.
- **Requirement:** A uniquely identified, testable product obligation with an owner,
  target, rationale, and verification method.
- **Runtime contract:** The invariant DOM inputs and observable interaction semantics
  shared by generated interactive HTML.
- **Spec:** A versioned, language-neutral structured chart description.
- **Supported:** Implemented, documented, tested, packaged, and covered by the stated
  release guarantee. A design document alone does not make a feature supported.

