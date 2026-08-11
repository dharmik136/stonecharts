# Development Triangle Chart Design

## Overview

The development triangle renders an actuarial loss-development matrix as a
grid of cells with origin rows (accident years) and development-period columns.
It is a non-Cartesian chart type with its own SVG shell (no shared axes).

## Spec shape

```json
{
  "type": "development-triangle",
  "triangle": {
    "origins": ["2021", "2022", "2023"],
    "periods": [12, 24, 36],
    "values": [[v00, v01, v02], [v10, v11], [v20]],
    "view": "cumulative",
    "valueType": "incurred",
    "unit": "millions"
  }
}
```

### Periods

Non-negative integers, strictly increasing, no duplicates. Booleans, floats
like 12.5, NaN, and Infinity are rejected.

### Values shape

- Each row has 1..len(periods) contiguous values.
- Row lengths must be non-increasing (newer origins have fewer or equal values).
- Equal row lengths are allowed (rectangular triangles).
- Zero-length rows are rejected.
- Rows longer than periods are rejected.

### Supplied factors

Development factors are supplied by the caller, not computed by the renderer.
When `factors.show` is true, `factors.values` must be present with exactly
`len(periods) - 1` finite numbers. The renderer displays them below the grid,
formatted to 3 decimal places.

```json
"factors": {"show": true, "values": [1.476, 1.133]}
```

### Unit rendering

When `triangle.unit` is non-empty, a "Unit: {unit}" label is rendered below
the title/subtitle. The unit is included in the aria-label summary.

### Metadata attributes

The root `<g class="sc-dt-triangle">` element carries:
- `data-triangle-view="{view}"` (e.g. "cumulative" or "incremental")
- `data-triangle-value-type="{valueType}"` (e.g. "incurred" or "paid")

Both attributes are also included in the aria-label summary.

### Latest diagonal

The latest diagonal highlights the rightmost populated cell of each non-empty
row: for each row r, `c = len(values[r]) - 1`.

### Annotation text

Each annotation renders the visual red circle + "!" marker inside a group
element with:
- `<title>{escaped_text}</title>` for tooltip/screen-reader access
- `aria-label="{escaped_text}"` on the group

Annotations referencing an unknown origin, unknown period, or a period with
no populated cell for that origin are rejected at validation time.

## Layout

- Cell grid: fixed 72 x 28 px cells
- Row headers: 68 px wide column for origin labels
- Column headers: 24 px tall row for period labels
- Margins: 22 px left/right, 20 px top (+ title/subtitle/unit), 20 px bottom

## Features

| Feature | Spec field | Default |
|---------|-----------|---------|
| Color scale | `colorScale.type: "sequential"` | off |
| Diagonal highlight | `diagonal.highlight: true` | off |
| Supplied factors | `factors.show: true, factors.values: [...]` | off |
| Cell annotations | `annotations: [{origin, period, text}]` | none |
| Unit label | `triangle.unit: "millions"` | off |
| View metadata | `triangle.view: "cumulative"` | cumulative |
| Value type metadata | `triangle.valueType: "incurred"` | incurred |

## Semantic invariants (SC-SEM)

- Values shape: non-increasing row lengths, each row 1..len(periods)
- Renderer does not modify input triangle (DEC-049)
- Development factors are supplied, never computed (authority boundary)
- Color scale maps to actual value range, not arbitrary normalization
- Latest diagonal uses rightmost populated cell, not square-matrix formula

## Certification

Admitted at `0.0.0.33` as **certified** tier (DEC-057).
