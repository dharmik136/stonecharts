"""Basic line chart renderer: ChartSpec -> SVG string.

Produces SVG that follows spec/svg-contract.md so the shared JS runtime can
enhance it (tooltip, highlight, legend toggle, crosshair). This module does the
real drawing (scales, axes, gridlines, series paths, points, legend) in pure
Python — no third-party charting deps.
"""
from __future__ import annotations

from typing import List

from ..spec import ChartSpec, GridLine
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
        color = s.color or PALETTE[si % len(PALETTE)]
        pts = [(xpix(i), ypix(v)) for i, v in enumerate(s.data)]
        d = " ".join(
            ("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts)
        )
        p.append(f'<g class="pk-series" data-series="{si}">')
        p.append(
            f'<path class="pk-series-line" data-series="{si}" d="{d}" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        for i, (x, y) in enumerate(pts):
            xlabel = cats[i] if i < len(cats) else str(i)
            p.append(
                f'<circle class="pk-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" data-color="{color}" '
                f'data-r="3.5" data-r-hover="6" cx="{x:.1f}" cy="{y:.1f}" r="3.5" '
                f'fill="{color}" stroke="#fff" stroke-width="1"/>'
            )
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
            color = s.color or PALETTE[si % len(PALETTE)]
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
