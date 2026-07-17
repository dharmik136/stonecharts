"""Basic line chart renderer: ChartSpec -> SVG string.

Produces SVG that follows spec/svg-contract.md so the shared JS runtime can
enhance it (tooltip, highlight, legend toggle, crosshair). This module does the
real drawing (scales, axes, gridlines, series paths, points, legend) in pure
Python — no third-party charting deps.
"""
from __future__ import annotations

import math
from typing import List

from ..spec import ChartSpec, Gradient, GridLine, Marker, Pattern
from ..util import esc, fmt_num, nice_ticks

# Default categorical palette (original values; not copied from any library).
PALETTE: List[str] = [
    "#2f7ed8", "#f45b5b", "#8bbc21", "#e4a812",
    "#1aadce", "#8e44ad", "#f28f43", "#77a1e5",
]

# dashStyle name -> SVG stroke-dasharray value ("" = solid, no attribute).
_DASH = {"dashed": "5 5", "dotted": "2 3"}


def _dash_array(style: str) -> str:
    return _DASH.get(style, "")


def _path_d(pts, step) -> str:
    """Build the line path 'd'. step in {None, before, after, center}."""
    if not step:
        return " ".join(
            ("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts)
        )
    parts: List[str] = []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            parts.append(f"M{x:.1f} {y:.1f}")
            continue
        px, py = pts[i - 1]
        if step == "before":
            parts.append(f"L{px:.1f} {y:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
        elif step == "center":
            mx = (px + x) / 2
            parts.append(f"L{mx:.1f} {py:.1f}")
            parts.append(f"L{mx:.1f} {y:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
        else:  # after
            parts.append(f"L{x:.1f} {py:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
    return " ".join(parts)


def _spline_d(pts) -> str:
    """Monotone cubic spline path (Fritsch-Carlson). Identical math to line.go."""
    n = len(pts)
    if n < 3:
        return _path_d(pts, None)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    delta = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [0.0] * n
    m[0] = delta[0]
    m[n - 1] = delta[n - 2]
    for i in range(1, n - 1):
        if delta[i - 1] * delta[i] <= 0:
            m[i] = 0.0
        else:
            m[i] = (delta[i - 1] + delta[i]) / 2
    for i in range(n - 1):
        if delta[i] == 0:
            m[i] = 0.0
            m[i + 1] = 0.0
        else:
            a = m[i] / delta[i]
            b = m[i + 1] / delta[i]
            s = a * a + b * b
            if s > 9:
                t = 3.0 / math.sqrt(s)
                m[i] = t * a * delta[i]
                m[i + 1] = t * b * delta[i]
    parts = [f"M{xs[0]:.1f} {ys[0]:.1f}"]
    for i in range(n - 1):
        h = xs[i + 1] - xs[i]
        c1x = xs[i] + h / 3
        c1y = ys[i] + m[i] * h / 3
        c2x = xs[i + 1] - h / 3
        c2y = ys[i + 1] - m[i + 1] * h / 3
        parts.append(
            f"C{c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {xs[i + 1]:.1f} {ys[i + 1]:.1f}"
        )
    return " ".join(parts)


def _marker(symbol, x, y, r, common, color) -> str:
    """One data-point marker. `common` = the shared class + data-* attributes.
    Non-circle shapes carry cx/cy attrs so the JS runtime (crosshair) still works."""
    fs = f'fill="{color}" stroke="#fff" stroke-width="1"'
    if symbol == "square":
        return (
            f'<rect {common} cx="{x:.1f}" cy="{y:.1f}" x="{x-r:.1f}" y="{y-r:.1f}" '
            f'width="{2*r:.1f}" height="{2*r:.1f}" {fs}/>'
        )
    if symbol == "triangle":
        poly = f"{x:.1f},{y-r:.1f} {x-r:.1f},{y+r:.1f} {x+r:.1f},{y+r:.1f}"
        return f'<polygon {common} cx="{x:.1f}" cy="{y:.1f}" points="{poly}" {fs}/>'
    if symbol == "diamond":
        poly = f"{x:.1f},{y-r:.1f} {x+r:.1f},{y:.1f} {x:.1f},{y+r:.1f} {x-r:.1f},{y:.1f}"
        return f'<polygon {common} cx="{x:.1f}" cy="{y:.1f}" points="{poly}" {fs}/>'
    # circle (default)
    return f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(r)}" {fs}/>'


def _gradient_def(gid: str, g: Gradient) -> str:
    """<linearGradient> def. Direction is x1,y1->x2,y2 (objectBoundingBox)."""
    stops = []
    for st in g.stops:
        op = f' stop-opacity="{fmt_num(st.opacity)}"' if st.opacity is not None else ""
        stops.append(f'<stop offset="{fmt_num(st.offset)}" stop-color="{st.color}"{op}/>')
    return (
        f'<linearGradient id="{gid}" x1="{fmt_num(g.x1)}" y1="{fmt_num(g.y1)}" '
        f'x2="{fmt_num(g.x2)}" y2="{fmt_num(g.y2)}">' + "".join(stops) + "</linearGradient>"
    )


def _pattern_def(pid: str, pat: Pattern) -> str:
    """<pattern> def: a diagonal hatch tile (userSpaceOnUse, rotated)."""
    sz = fmt_num(pat.size)
    bg = (
        f'<rect width="{sz}" height="{sz}" fill="{pat.background}"/>'
        if pat.background else ""
    )
    hatch = (
        f'<line x1="0" y1="0" x2="0" y2="{sz}" stroke="{pat.color}" '
        f'stroke-width="{fmt_num(pat.stroke_width)}"/>'
    )
    return (
        f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{sz}" height="{sz}" '
        f'patternTransform="rotate({fmt_num(pat.angle)})">' + bg + hatch + "</pattern>"
    )


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height

    # Margins adapt to which chrome is present.
    m_top = 20
    if spec.title:
        m_top += 26
    if spec.subtitle:
        m_top += 18
    m_left = 62 if spec.y_axis.title else 52
    m_right = 22
    m_bottom = 46 + (18 if spec.legend else 0) + (18 if spec.x_axis.title else 0)

    plot_x, plot_y = m_left, m_top
    plot_w, plot_h = W - m_left - m_right, H - m_top - m_bottom

    # X categories (labels). Numeric fallback to index.
    n = max((len(s.data) for s in spec.series), default=0)
    cats = spec.x_axis.categories or [str(i) for i in range(n)]

    # Y range across all series, always including 0 as a baseline anchor.
    values = [v for s in spec.series for v in s.data]
    lo = spec.y_axis.min if spec.y_axis.min is not None else min(values + [0.0])
    hi = spec.y_axis.max if spec.y_axis.max is not None else max(values + [0.0])
    y_min, y_max, y_ticks = nice_ticks(lo, hi)

    def xpix(i: int) -> float:
        if n <= 1:
            return plot_x + plot_w / 2
        return plot_x + plot_w * i / (n - 1)

    def ypix(v: float) -> float:
        return plot_y + plot_h * (1 - (v - y_min) / (y_max - y_min))

    # Resolve per-series styling and collect <defs> (gradients/patterns). Defs are
    # emitted ONLY when something needs them, so default output stays byte-identical.
    defs_parts: List[str] = []
    sstyle = []
    for si, s in enumerate(spec.series):
        if isinstance(s.color, Gradient):
            gid = f"{spec.id}-grad-{si}"
            defs_parts.append(_gradient_def(gid, s.color))
            ref = f"url(#{gid})"
            stroke = ref
            fill_color = ref
            solid = s.color.stops[0].color if s.color.stops else PALETTE[si % len(PALETTE)]
        elif s.color:
            stroke = fill_color = solid = s.color
        else:
            stroke = fill_color = solid = PALETTE[si % len(PALETTE)]
        if s.pattern is not None:
            pid = f"{spec.id}-pat-{si}"
            defs_parts.append(_pattern_def(pid, s.pattern))
            area_fill = f"url(#{pid})"
            area_op = ""
        elif s.fill_opacity > 0:
            area_fill = fill_color
            area_op = f' fill-opacity="{fmt_num(s.fill_opacity)}"'
        else:
            area_fill = None
            area_op = ""
        sstyle.append((stroke, solid, area_fill, area_op))

    p: List[str] = []
    _font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    if spec.responsive:
        p.append(
            f'<svg class="pk-chart" xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
            f'width="100%" {_font}>'
        )
    else:
        p.append(
            f'<svg class="pk-chart" xmlns="http://www.w3.org/2000/svg" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" {_font}>'
        )

    # Gradient / pattern defs (only present when a series needs them).
    if defs_parts:
        p.append("<defs>" + "".join(defs_parts) + "</defs>")

    # Titles.
    ty = 26
    if spec.title:
        p.append(
            f'<text class="pk-title" x="{W/2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="17" font-weight="600" fill="#1a1a2e">{esc(spec.title)}</text>'
        )
        ty += 20
    if spec.subtitle:
        p.append(
            f'<text class="pk-subtitle" x="{W/2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="12" fill="#6b6b80">{esc(spec.subtitle)}</text>'
        )

    # Y gridlines + labels. Defaults reproduce the built-in look byte-for-byte.
    gl = spec.y_axis.grid_line or GridLine()
    grid_color = gl.color or "#e8e8ee"
    grid_dash = _dash_array(gl.dash_style)
    dash_attr = f' stroke-dasharray="{grid_dash}"' if grid_dash else ''
    p.append('<g class="pk-axis pk-axis-y">')
    for tv in y_ticks:
        gy = ypix(tv)
        if gl.enabled:
            p.append(
                f'<line class="pk-gridline" x1="{plot_x:.1f}" y1="{gy:.1f}" '
                f'x2="{plot_x+plot_w:.1f}" y2="{gy:.1f}" stroke="{grid_color}" '
                f'stroke-width="1"{dash_attr}/>'
            )
        p.append(
            f'<text x="{plot_x-8:.1f}" y="{gy+4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#6b6b80">{esc(fmt_num(tv))}</text>'
        )
    p.append("</g>")

    # Axis lines.
    p.append(
        f'<line class="pk-axis-line" x1="{plot_x:.1f}" y1="{plot_y+plot_h:.1f}" '
        f'x2="{plot_x+plot_w:.1f}" y2="{plot_y+plot_h:.1f}" stroke="#b6b6c2" stroke-width="1"/>'
    )

    # X labels.
    p.append('<g class="pk-axis pk-axis-x">')
    for i, label in enumerate(cats[:n]):
        lx = xpix(i)
        p.append(
            f'<text x="{lx:.1f}" y="{plot_y+plot_h+18:.1f}" text-anchor="middle" '
            f'font-size="11" fill="#6b6b80">{esc(label)}</text>'
        )
    p.append("</g>")

    # Axis titles.
    if spec.x_axis.title:
        p.append(
            f'<text x="{plot_x+plot_w/2:.1f}" y="{H-6}" text-anchor="middle" '
            f'font-size="12" fill="#4a4a5a">{esc(spec.x_axis.title)}</text>'
        )
    if spec.y_axis.title:
        yc = plot_y + plot_h / 2
        p.append(
            f'<text x="14" y="{yc:.1f}" text-anchor="middle" font-size="12" '
            f'fill="#4a4a5a" transform="rotate(-90 14 {yc:.1f})">{esc(spec.y_axis.title)}</text>'
        )

    # Crosshair (hidden until a point is hovered; driven by the JS runtime).
    p.append(
        f'<line class="pk-crosshair" x1="0" y1="{plot_y:.1f}" x2="0" y2="{plot_y+plot_h:.1f}" '
        f'stroke="#c0c0cc" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>'
    )

    # Series: one group per series (data-series drives legend toggle).
    for si, s in enumerate(spec.series):
        stroke, color, area_fill, area_op = sstyle[si]
        pts = [(xpix(i), ypix(v)) for i, v in enumerate(s.data)]
        d = _spline_d(pts) if s.curve == "monotone" else _path_d(pts, s.step)
        lw = s.line_width if s.line_width is not None else 2
        line_dash = _dash_array(s.dash_style)
        line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
        p.append(f'<g class="pk-series" data-series="{si}">')
        # Area fill (under the line, drawn first so the line sits on top).
        if area_fill is not None and pts:
            base = ypix(0.0)
            area_d = f"{d} L{pts[-1][0]:.1f} {base:.1f} L{pts[0][0]:.1f} {base:.1f} Z"
            p.append(
                f'<path class="pk-series-area" data-series="{si}" d="{area_d}" '
                f'fill="{area_fill}"{area_op} stroke="none"/>'
            )
        p.append(
            f'<path class="pk-series-line" data-series="{si}" d="{d}" fill="none" '
            f'stroke="{stroke}" stroke-width="{fmt_num(lw)}" stroke-linejoin="round" '
            f'stroke-linecap="round"{line_dash_attr}/>'
        )
        mk = s.marker or Marker()
        if mk.enabled:
            radius = mk.radius
            radius_hover = radius + 2.5
            for i, (x, y) in enumerate(pts):
                xlabel = cats[i] if i < len(cats) else str(i)
                common = (
                    f'class="pk-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" '
                    f'data-color="{color}" data-r="{fmt_num(radius)}" '
                    f'data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(_marker(mk.symbol, x, y, radius, common, color))
        p.append("</g>")

    # Legend (bottom center).
    if spec.legend and spec.series:
        gap = 22
        est = [len(s.name) * 7 + 26 for s in spec.series]
        total = sum(est) + gap * (len(spec.series) - 1)
        lx = plot_x + (plot_w - total) / 2
        ly = H - (10 + (18 if spec.x_axis.title else 0))
        p.append('<g class="pk-legend">')
        for si, s in enumerate(spec.series):
            color = sstyle[si][1]
            p.append(f'<g class="pk-legend-item" data-series="{si}">')
            p.append(
                f'<rect x="{lx:.1f}" y="{ly-9:.1f}" width="14" height="4" rx="2" fill="{color}"/>'
            )
            p.append(
                f'<text x="{lx+20:.1f}" y="{ly-2:.1f}" font-size="12" fill="#33334d">{esc(s.name)}</text>'
            )
            p.append("</g>")
            lx += est[si] + gap
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
