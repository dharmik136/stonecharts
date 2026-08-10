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
    "values": [[v00, v01, v02], [v10, v11], [v20]]
  }
}
```

`values[i]` has at most `len(periods) - i` entries (triangular shape).

## Layout

- Cell grid: fixed 72 x 28 px cells
- Row headers: 68 px wide column for origin labels
- Column headers: 24 px tall row for period labels
- Margins: 22 px left/right, 20 px top (+ title/subtitle), 20 px bottom

## Features

| Feature | Spec field | Default |
|---------|-----------|---------|
| Color scale | `colorScale.type: "sequential"` | off |
| Diagonal highlight | `diagonal.highlight: true` | off |
| Development factors | `factors.show: true` | off |
| Cell annotations | `annotations: [{origin, period, text}]` | none |

## Semantic invariants (SC-SEM)

- Triangular shape: `values[i].length <= periods.length - i`
- Renderer does not modify input triangle (DEC-049)
- Development factors are computed for display only, never written back
- Color scale maps to actual value range, not arbitrary normalization

## Certification

Admitted at `0.0.0.33` as **certified** tier (DEC-057).
