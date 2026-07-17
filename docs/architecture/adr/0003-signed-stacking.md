---
id: SC-ARCH-ADR-0003
title: Define Signed and Percent Stacking Semantics
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-STACK-001, REQ-STACK-002]
evidence: [TEST-STACK-SIGNED, TEST-PERCENT-DOMAIN]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# ADR 0003: Define Signed and Percent Stacking Semantics

## Context

A single cumulative total is invalid for mixed-sign normal stacks. Percent stacking
also has multiple legitimate signed conventions: net total, absolute total, or
separate positive and negative totals. Choosing one silently assigns business meaning.

## Decision

Normal stacks use separate accumulators per category:

```text
value >= 0 -> segment spans positive_total to positive_total + value
value < 0  -> segment spans negative_total to negative_total + value
```

The frame domain includes the extrema of both accumulators. Series order remains the
pinned accumulation order within each sign.

0.0.0.1 percent stacks accept finite non-negative values only. Positive categories
normalize by their category total. An all-zero category produces zero-height segments
and zero-percent semantics. Negative values receive a canonical validation error.

## Consequences

Normal stacks represent diverging data correctly. Percent composition is unambiguous
but intentionally narrower. A future `diverging-percent` mode requires a separate ADR,
schema value, labels, examples, and conformance corpus.

## Rejected alternatives

- Net-sum normalization: cancellation can divide by zero or amplify values.
- Absolute-total normalization: valid but changes the meaning of "100%" and is not
  appropriate as an undocumented default.
- Silently discard negative values: data corruption.

