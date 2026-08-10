---
id: SC-OPS-024
title: DEC-054 Range-Point Schema Unification
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

# DEC-054 Range-Point Schema Unification

## Decision question

Should StoneCharts replace the parallel-array range data model (`data[] + low[]` or
`data[] + high[]`) with an atomic range-point structure across all range chart types?

## Background

Four chart types currently use parallel arrays to represent range data:

| Chart type | Current model | Semantic intent |
|-----------|---------------|-----------------|
| Arearange | `data[]` = high, `low[]` = low | Confidence envelope, forecast range |
| Columnrange | `data[]` = low, `high[]` = high | Category min-max comparison |
| Error-bar | `data[]` = center, `low[]` + `high[]` | Uncertainty bounds around estimate |
| Dumbbell | `data[]` = low, `high[]` = high | Before-after or min-max gap |

### The problem

Parallel arrays allow values that semantically belong together to drift apart:

```json
{
  "data": [184, 83, 121],
  "low":  [172, 83],
  "high": [199, 101, 164]
}
```

Is `low` missing its third element by mistake, or intentionally? The current
renderers handle this silently — arearange falls back to using the high value,
others pad or truncate. DEC-052 addresses the immediate validation gap, but the
structural problem remains: the schema makes it possible to express invalid states.

### The fix

An atomic range-point structure makes invalid states unrepresentable:

```json
{
  "rangeData": [
    {"category": "Motor",     "low": 172, "high": 199},
    {"category": "Property",  "low":  83, "high": 101},
    {"category": "Liability", "low": 121, "high": 164}
  ]
}
```

For error-bar, the center value is part of the same object:

```json
{
  "rangeData": [
    {"category": "Motor",     "value": 184, "low": 172, "high": 199},
    {"category": "Property",  "value":  83, "low":  78, "high":  91}
  ]
}
```

### Market context

**IFRS 17 reporting uses structured range data extensively.** Reserve ranges,
confidence intervals, scenario bands, and uncertainty margins are all naturally
represented as `{low, high}` or `{value, low, high}` tuples. Actuarial tools
(Moody's, SAS, Oracle) model these as structured objects, not parallel arrays.
StoneCharts should match the data model actuaries already think in.

**Schema strictness is a product feature.** For a product selling visual integrity,
"the schema makes it impossible to express invalid data" is a stronger claim than
"the validator catches invalid data at runtime." The first prevents bugs at the
API boundary; the second catches them after the fact.

## Recommendation

Introduce a `rangeData` field as the canonical range-point model, shared across
all four range chart types. Deprecate the parallel-array model with a migration
period.

### Schema design

Add to `spec/chart-spec.schema.json`:

```json
"RangePoint": {
  "type": "object",
  "required": ["low", "high"],
  "properties": {
    "low":      {"type": "number"},
    "high":     {"type": "number"},
    "value":    {"type": "number"},
    "category": {"type": "string"},
    "name":     {"type": "string"}
  }
}
```

Series gains a `rangeData` field: `"rangeData": {"type": "array", "items": {"$ref": "#/definitions/RangePoint"}}`.

### Migration

1. **Phase 1:** Add `rangeData` as an alternative to `data[] + low[] + high[]`.
   Both forms accepted. When `rangeData` is present, parallel arrays are ignored.
2. **Phase 2:** Log a deprecation warning when parallel arrays are used without
   `rangeData`.
3. **Phase 3:** Remove parallel-array support from the certified schema. Existing
   specs can be migrated with a `tools/migrate_range_specs.py` script.

### Validation (works with DEC-052)

When `rangeData` is used, the validator enforces:
- `low <= high` for every point (SC-SEM-004, SC-SEM-005, SC-SEM-008)
- `value` is present for error-bar type
- Array length matches `categories` length (when categories are explicit)

### Implementation scope

| File | Change |
|------|--------|
| `spec/chart-spec.schema.json` | Add `RangePoint` definition and `rangeData` field |
| `libs/python/stonecharts/spec.py` | Add `RangePoint` dataclass, parse `rangeData` |
| `libs/go/spec.go` | Add `RangePoint` struct, parse `rangeData` |
| `libs/python/stonecharts/charts/arearange.py` | Read from `rangeData` or fall back to parallel arrays |
| `libs/python/stonecharts/charts/columnrange.py` | Same |
| `libs/python/stonecharts/charts/error_bar.py` | Same, plus `value` field |
| `libs/python/stonecharts/charts/dumbbell.py` | Same |
| `libs/go/arearange.go` | Same |
| `libs/go/columnrange.go` | Same |
| `libs/go/error_bar.go` | Same |
| `libs/go/dumbbell.go` | Same |
| `libs/python/stonecharts/validate.py` | Validate `RangePoint` ordering |
| `libs/go/validate.go` | Same |
| `tools/migrate_range_specs.py` | New: convert parallel-array specs to `rangeData` |

## Options

| Option | What it means | Tradeoff |
|--------|---------------|----------|
| Unified `rangeData` with migration | One structured primitive across 4 chart types; invalid states unrepresentable | Schema change; existing specs need migration |
| Validate parallel arrays only (DEC-052) | Catches errors at runtime but schema still allows invalid states | Weaker guarantee; no structural improvement |
| Defer | Keep current parallel-array model | Drift risk remains; inconsistent with integrity story |

## Dependencies

- DEC-052 (strict input validation) provides the immediate validation fix.
- DEC-054 provides the structural fix that makes DEC-052's cardinality checks
  unnecessary for `rangeData` users (the schema enforces it).
- DEC-053 (tiered certification) — range chart types cannot be promoted to
  "certified" tier until this refactor is complete.
