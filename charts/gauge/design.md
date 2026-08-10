# Gauge chart — design

| Field | Value |
|-------|-------|
| Type  | `"gauge"` |
| Class | Family B sibling (polar arc substrate paid by pie) |
| Src   | HC |

## What it shows

A single KPI value displayed as a pointer on a 270-degree annular arc with
optional colored range bands. The pointer angle is proportional to the value
within [gaugeMin, gaugeMax].

## Data model

```jsonc
{
  "type": "gauge",
  "title": "Speed",
  "series": [{ "name": "Speed", "data": [72] }],
  "gaugeMin": 0,
  "gaugeMax": 100,
  "gaugeBands": [
    { "from": 0, "to": 40, "color": "#55bf3b" },
    { "from": 40, "to": 70, "color": "#dddf0d" },
    { "from": 70, "to": 100, "color": "#df5353" }
  ]
}
```

- `series[0].data[0]` is the gauge value (single series, single point).
- `gaugeMin` / `gaugeMax` define the scale range (defaults 0 / 100).
- `gaugeBands` is an optional array of `{from, to, color}` colored arc segments.
- Values outside [gaugeMin, gaugeMax] are clamped for pointer positioning.

## Rendering

### Layout

No Cartesian axes or gridlines. Own SVG shell (like pie / funnel).

- Title and subtitle at top (same positioning as Cartesian charts).
- Gauge centered in the remaining plot area.
- Legend at bottom using the shared legend renderer.

### Geometry

270-degree arc with a 90-degree gap at the bottom (6 o'clock).

- Start angle: 3pi/4 (7:30 clock position, lower-left).
- Sweep: 3pi/2 (270 degrees clockwise to 4:30, lower-right).
- `r_max = min(plot_w, plot_h) / 2`
- Track width: `r_max * 0.15`
- `r_outer = r_max`, `r_inner = r_max - track_width`

Track arc: annular sector from start to end (gray, using `theme.grid_color`).

Band arcs: each band maps [from, to] to an angle range within the track,
clipped to [gaugeMin, gaugeMax]. Same annular geometry as the track.

Pointer: a kite-shaped path (4 vertices):
- Tip at `r_inner - 4` from center in the value direction.
- Two base points at 6px perpendicular from center.
- Tail at 12px opposite from center.

Pivot: filled circle (r=8) at center, same color as pointer.

Value text: formatted number centered at (cx, cy + 28), font-size 20 bold.

### Data attributes

The pointer `<path>` carries:
`class="sc-pointer sc-point"`, `data-series="0"`, `data-series-name`,
`data-y` (formatted value), `data-color`.

Band `<path>` elements carry:
`class="sc-gauge-band"`, `data-index`, `data-from`, `data-to`.

### Accessibility

`role="img"`, `aria-label`, `<desc>` summary.
Data table: Metric | Value | Min | Max columns.
