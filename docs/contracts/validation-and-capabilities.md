---
id: SC-CON-002
title: Specification Validation and Renderer Capabilities
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PROD-001, REQ-SCOPE-001, REQ-VAL-001, REQ-CAP-001, REQ-STACK-001, REQ-STACK-002]
evidence: [TEST-VALIDATION-PARITY, TEST-CAPABILITY-MATRIX, TEST-STACK-SIGNED, TEST-PERCENT-DOMAIN]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Validation and Capabilities

## Validation pipeline

All public entry points apply the same ordered phases:

1. Parse the transport representation without coercing wrong-typed values.
2. Validate active-schema structure and primitive constraints.
3. Validate cross-field semantic rules.
4. Validate the renderer capability manifest.
5. Resolve defaults and render.

An error in one phase prevents later phases and produces no output artifact.

## Active Alpha schema

The active type set is `line` and `column`. Other chart design directories are roadmap
inputs and MUST NOT be accepted by the 0.0.0.1 schema. Python and Go capability
manifests MUST additionally declare:

```json
{
  "specVersion": "0.0.0.1",
  "svgContractVersion": "0.0.0.1",
  "chartTypes": ["column", "line"],
  "column": {
    "grouping": ["grouped", "overlay"],
    "stacking": ["none", "normal", "percent-nonnegative"]
  }
}
```

Array order is canonical. The final manifest shape will be added to the active schema
before approval.

## Semantic rules requiring ratification in code

- `series` is required. Whether an empty list and empty series data are valid must be
  identical in schema and both validators; 0.0.0.1 currently treats the mismatch as a
  release blocker rather than silently choosing.
- Width and height minimums must be identical in every validation path.
- An explicit category array shorter than rendered data must either fail or be padded
  by one documented rule; indexing beyond the array is forbidden.
- Normal stacks accept signed values and use separate sign accumulators.
- Percent stacks reject negative values. All-zero categories are valid and represent
  zero percent.
- Non-finite values are invalid even where a host JSON or API can construct them.
- Unknown fields remain forward-compatible only when ignoring them cannot change the
  meaning of a released capability. Security-sensitive and discriminating objects may
  require stricter rules in a future schema revision.

## Errors

The target error model contains:

| Field | Meaning |
|---|---|
| `code` | Stable machine identifier such as `E_SPEC_TYPE` or `E_CAPABILITY` |
| `path` | JSON path to the failing value when applicable |
| `message` | Human-readable explanation |
| `details` | Optional structured expected/received/capability data |

Python may expose an exception object and Go may return an `error`, but their code,
path, and semantic details MUST match. Panics and undocumented exceptions are defects.

## Capability evolution

A new renderer may consume an older active schema if its manifest declares that
version. An older renderer may reject a newer valid spec with `E_CAPABILITY` without
claiming the spec is structurally invalid. No renderer silently drops an unsupported
field that changes visible output or behavior.

