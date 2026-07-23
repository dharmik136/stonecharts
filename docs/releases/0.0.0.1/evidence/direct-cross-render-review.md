---
id: SC-REL-007
title: StoneCharts 0.0.0.1 Direct Cross-Render Review
status: approved
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-DET-001]
evidence: [TEST-DIRECT-CROSS-RENDER, TEST-DOCS-CONTROL]
last_reviewed: "2026-07-19"
review_due: "2026-08-19"
supersedes: null
superseded_by: null
---

# Direct Cross-Render Review

## Scope

This review records the byte-level Python-to-Go cross-render comparison for the
active 0.0.0.1 release examples. It covers the line-basic and column example
corpora only.

## Command run

- `python tools/check_direct_cross_render.py`

## Result

The active release corpus renders to identical UTF-8 SVG bytes in Python and Go for
all active release examples.

## Evidence

- [`tools/check_direct_cross_render.py`](../../../../tools/check_direct_cross_render.py)
