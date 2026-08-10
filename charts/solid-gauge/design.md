# Solid gauge chart — design

| Field | Value |
|-------|-------|
| Type  | `"solid-gauge"` |
| Class | Family B sibling (polar arc substrate paid by pie) |
| Src   | HC |

## What it shows

A single KPI value displayed as a filled arc from the start angle to the
value's angle over a 270-degree annular track. Optional colored range bands
provide qualitative context behind the value arc.

## Data model

```jsonc
{
  "type": "solid-gauge",
  "title": "CPU Usage",
  "series": [{ "name": "CPU", "data": [72] }],
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
- Values outside [gaugeMin, gaugeMax] are clamped for the fill arc.

## Rendering

### Layout

No Cartesian axes or gridlines. Own SVG shell (like pie / funnel / gauge).

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

Value arc: annular sector from start angle to value angle. Drawn on top of
bands. Uses series color (or palette[0]). Not drawn when value equals gaugeMin
(frac = 0).

Value text: formatted number centered at (cx, cy + 28), font-size 20 bold.

### Data attributes

The value arc `<path>` carries:
`class="sc-gauge-fill sc-point"`, `data-series="0"`, `data-series-name`,
`data-y` (formatted value), `data-color`.

Band `<path>` elements carry:
`class="sc-gauge-band"`, `data-index`, `data-from`, `data-to`.

### Accessibility

`role="img"`, `aria-label`, `<desc>` summary.
Data table: Metric | Value | Min | Max columns.
