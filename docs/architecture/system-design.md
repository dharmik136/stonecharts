---
id: SC-ARCH-001
title: StoneCharts System Design
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PROD-001, REQ-DET-001, REQ-VAL-001, REQ-CAP-001, REQ-RUNTIME-001]
evidence: [TEST-PYTHON-GOLDENS, TEST-GO-GOLDENS, TEST-VALIDATION-PARITY]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# System Design

## Context

StoneCharts receives a versioned chart specification from an application, validates it,
resolves defaults and capabilities, and produces canonical SVG. An optional shared
browser runtime enhances the static SVG inside self-contained HTML. Export tools may
convert the SVG to raster or document formats under separately declared profiles.

External actors are application developers, report pipelines, browser users, assistive
technology users, package registries, and downstream export engines.

## Containers

| Container | Responsibility | Authoritative source |
|---|---|---|
| Specification | Language-neutral fields, types, defaults, and structural rules | `spec/chart-spec.schema.json` |
| Python library | Python model, validation, SVG serialization, HTML assembly | `libs/python/stonecharts` |
| Go library | Go model, validation, SVG serialization, HTML assembly | `libs/go` |
| Shared runtime | Adaptive tooltip, navigation, crosshair, and legend behavior | `runtime/chart-interactions.js` |
| Contract corpus | Released designs, invalid fixtures, examples, and goldens | `charts/line-basic`, `charts/column`, `spec` |
| Governance system | Requirements, ADRs, risks, evidence definitions, release gates | `docs` |

No certified renderer may delegate chart generation to another language renderer. The
independent implementations are intentional: agreement against the same contract is
the evidence.

## Render flow

```text
untrusted input
  -> parse JSON / construct typed spec
  -> structural and semantic validation
  -> renderer capability validation
  -> canonical default and theme resolution
  -> shared substrate + chart marks
  -> canonical SVG serialization
  -> optional HTML wrapper + shared runtime
  -> optional certified export profile
```

Each stage either returns a complete value or a typed error. User-controlled input
MUST NOT cause a panic, process termination, partial file, or silent feature drop.

## Source-of-truth boundaries

- The active JSON Schema owns public structure and documented defaults.
- Normative contracts own semantics not fully expressible in JSON Schema.
- ADRs own the rationale and consequences of architecture choices.
- The requirement registry owns acceptance criteria and trace links.
- Goldens own reviewed canonical serialization for named fixtures.
- The runtime source is shared verbatim; it is not reimplemented per language.
- Release manifests own the evidence result for an immutable candidate.

Duplicated language constants, themes, error messages, and formatting rules MUST have a
parity test or be generated from a shared source.

## Trust boundaries

Chart specifications, themes, labels, identifiers, colors, and embedded metadata are
untrusted. SVG/HTML serializers are security boundaries. The runtime consumes only
contracted DOM attributes and must encode values before inserting HTML. Font and export
artifacts are supply-chain inputs and must be pinned by hash in certified profiles.

## Compatibility surfaces

The release manifest records product release, schema version, SVG contract version,
runtime version, language package versions, supported runtime/toolchain versions, and
certified export profiles. These versions need not all increment independently in
0.0.0.1, but their exact revisions must be identifiable.

## Failure model

Errors have a stable machine code, JSON path when applicable, human message, and
category: parse, validation, capability, rendering, runtime initialization, export, or
internal defect. Error text may improve in future releases; machine codes and paths are
the compatibility surface once approved.

An internal invariant failure is not converted into plausible output. It is reported as
an internal error and blocks qualification until understood.

