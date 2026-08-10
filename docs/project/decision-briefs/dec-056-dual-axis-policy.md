---
id: SC-OPS-026
title: DEC-056 Combo Dual-Axis Presentation Safety Policy
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.32 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-08-10"
review_due: "2026-09-10"
supersedes: null
superseded_by: null
---

# DEC-056 Combo Dual-Axis Presentation Safety Policy

## Decision question

Should StoneCharts introduce a presentation-safety policy for combo charts using
dual y-axes, differentiating between single-axis (fully certified) and dual-axis
(certified with documented risk)?

## Background

Combo charts with `secondaryYAxis` render two independent value scales on the same
chart. This is technically correct and the implementation is golden-tested with
byte-identical Python/Go output (including a Go fuzz corpus seed).

However, dual-axis charts are a well-documented source of misleading visualizations.
Two series with unrelated scales can create visual correlations that do not exist in
the data — the viewer perceives a relationship because the lines cross or track
together, when the apparent relationship is an artifact of scale selection.

### Example of misleading dual-axis

```
Left axis:  Loss ratio (60%–80%)
Right axis: Premium volume ($100M–$500M)

Visual impression: "Premium and loss ratio move together"
Reality: Scales were chosen to make the lines overlap
```

### Why this matters for StoneCharts

StoneCharts' value proposition is visual integrity. A chart that renders correctly
but communicates misleadingly is a failure of integrity even though it is technically
accurate.

For insurance reporting specifically, misleading dual-axis charts have been cited in
regulatory reviews. An auditor who sees a dual-axis chart in a regulatory submission
may question whether the visual relationship is genuine.

### Market context

**This is a differentiation opportunity.** No competitor flags presentation-safety
risks. Highcharts, Chart.js, and Vega all render dual-axis charts without comment.
StoneCharts can say: "We don't merely render allowable charts — we identify risky
presentation semantics."

**Edward Tufte and the data visualization community** have argued against dual-axis
charts for decades. StoneCharts can align with best-practice data visualization
principles while still supporting the use case when the user explicitly opts in.

## Recommendation

Introduce a presentation-safety policy for dual-axis combo charts:

### Tier model

| Configuration | Status | Behavior |
|--------------|--------|----------|
| Combo, single y-axis | `CERTIFIED` | No additional policy |
| Combo, dual y-axis | `CERTIFIED_WITH_ADVISORY` | Render normally; include advisory metadata in evidence |

### Advisory metadata

When `secondaryYAxis` is used, StoneVerify evidence bundles should include:

```json
{
  "presentationAdvisory": {
    "code": "ADV-DUAL-AXIS",
    "severity": "info",
    "message": "This chart uses dual y-axes. Visual relationships between series on different axes may be artifacts of scale selection.",
    "recommendation": "Consider whether the implied visual relationship is genuine. For regulatory submissions, document the rationale for scale selection."
  }
}
```

### No blocking, no breaking

This is explicitly **not** a validation error. The chart renders normally. The
advisory appears only in StoneVerify evidence metadata, not in the rendered SVG.
Users who do not use StoneVerify see no difference.

### Future extension: scale-relationship analysis

A later version could analyze the actual data and flag cases where the visual
relationship is driven primarily by scale selection rather than data correlation.
This would be genuinely innovative — no charting library does this today.

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Advisory in evidence metadata | Dual-axis works normally; StoneVerify notes the risk | Zero breaking change; differentiator |
| Validation warning | `validate()` emits a warning (not error) for dual-axis | More visible but may annoy users who intentionally use dual-axis |
| Block dual-axis by default | Require explicit opt-in flag | Too restrictive; dual-axis is a legitimate use case |
| Do nothing | Treat dual-axis the same as single-axis | Misses a differentiation opportunity |

## Implementation scope

| File | Change |
|------|--------|
| `libs/python/stonecharts/verify/cli.py` | Detect dual-axis in spec; add advisory to manifest |
| `libs/go/cmd/stoneverify-go-render/main.go` | Same |
| `spec/stoneverify-result.schema.json` | Add `presentationAdvisory` field |
| `docs/contracts/guarantees-and-limits.md` | Document dual-axis advisory policy |

## Dependencies

- None blocking. This can be implemented independently of DEC-049–055.
