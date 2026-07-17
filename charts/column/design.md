# Chart: Column Chart (`column`)

- **Chart id:** `column`
- **Spec `type`:** `"column"`
- **Status:** Scaffolded (Pilot Exemplar)
- **Renderers:** `libs/python/peakcharts/charts/column.py` · `libs/go/column.go`
- **Contract:** [`spec/svg-contract.md`](../../spec/svg-contract.md)

## What it is

A column chart displays categorical values vertically as rectangular bars. Multiple series are displayed grouped (side-by-side) or stacked.

## Data shape

- `xAxis.categories`: the categories x labels, length `N`.
- each `series[].data`: `N` numbers, aligned to categories.

## Spec fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `type` | string | — | must be `"column"` |
| `stacking` | string | — | `normal` (stacked) or `percent` (100% stacked); default is grouped/side-by-side |

## Stacking Arithmetic

Cumulative values are accumulated in index order. Category widths are divided evenly between series in grouped mode.
