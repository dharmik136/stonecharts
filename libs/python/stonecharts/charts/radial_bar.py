"""Radial bar (racetrack / progress ring) renderer: ChartSpec -> SVG string.

Concentric track rings where angular extent encodes value. Multiple series
stack angularly within each track.
Non-Cartesian (Family B polar sibling) — own SVG shell, no axes.
See charts/radial-bar/design.md for the full geometry contract.
"""

from __future__ import annotations

import math

from ..spec import ChartSpec, Gradient
from ..util import esc, fmt_num
from ._cartesian import a11y_summary


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height
    theme = spec.theme
    palette = theme.palette
    _cid = esc(spec.id)

    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, "Radial bar"))
        a11y_attr = f' role="img" aria-label="{_sum}"'
        a11y_desc = f"<desc>{_sum}</desc>"

    m_top: float = 20
    if spec.title:
        m_top += 26
    if spec.subtitle:
        m_top += 18
    m_left: float = 22
    m_right: float = 22
    m_bottom: float = 28 + (18 if spec.legend else 0)
    if spec.layout and spec.layout.margin:
        m = spec.layout.margin
        if m.top is not None:
            m_top = m.top
        if m.left is not None:
            m_left = m.left
        if m.right is not None:
            m_right = m.right
        if m.bottom is not None:
            m_bottom = m.bottom

    plot_x, plot_y = m_left, m_top
    plot_w, plot_h = W - m_left - m_right, H - m_top - m_bottom

    cats = spec.x_axis.categories or []
    n_cats = len(cats)
    if n_cats < 1:
        n_cats = 1

    label_margin = 40.0
    cx = plot_x + plot_w / 2
    cy = plot_y + plot_h / 2
    r_max = min(plot_w, plot_h) / 2 - label_margin
    r_inner = r_max * 0.3

    y_max_spec = spec.y_axis.max
    if y_max_spec is not None:
        y_max = y_max_spec
    else:
        y_max = 0.0
        for j in range(n_cats):
            stack = 0.0
            for s in spec.series:
                v = s.data[j] if j < len(s.data) else 0.0
                stack += max(0.0, v)
            if stack > y_max:
                y_max = stack
    if y_max <= 0:
        y_max = 100.0

    band = (r_max - r_inner) / n_cats
    track_gap = 2.0

    p: list[str] = []

    _font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    if spec.responsive:
        p.append(
            f'<svg class="sc-chart"{a11y_attr} xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
            f'width="100%" {_font}>'
        )
    else:
        p.append(
            f'<svg class="sc-chart"{a11y_attr} xmlns="http://www.w3.org/2000/svg" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" {_font}>'
        )

    if a11y_desc:
        p.append(a11y_desc)

    if theme.background:
        p.append(f'<rect class="sc-bg" x="0" y="0" width="{W}" height="{H}" fill="{theme.background}"/>')

    ty = 26
    if spec.title:
        p.append(
            f'<text class="sc-title" x="{W / 2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="17" font-weight="600" fill="{theme.title_color}">{esc(spec.title)}</text>'
        )
        ty += 20
    if spec.subtitle:
        p.append(
            f'<text class="sc-subtitle" x="{W / 2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="12" fill="{theme.subtitle_color}">{esc(spec.subtitle)}</text>'
        )

    p.append(
        f'<line class="sc-crosshair" x1="0" y1="{plot_y:.1f}" x2="0" y2="{plot_y + plot_h:.1f}" '
        f'stroke="{theme.crosshair_color}" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>'
    )

    def point_at(angle: float, r: float) -> tuple[float, float]:
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    def arc_path(r_out: float, r_in: float, a_start: float, a_end: float) -> str:
        sweep = a_end - a_start
        large = 1 if abs(sweep) > math.pi else 0
        ox1, oy1 = point_at(a_start, r_out)
        ox2, oy2 = point_at(a_end, r_out)
        ix2, iy2 = point_at(a_end, r_in)
        ix1, iy1 = point_at(a_start, r_in)
        return (
            f"M {ox1:.1f} {oy1:.1f} "
            f"A {r_out:.1f} {r_out:.1f} 0 {large} 1 {ox2:.1f} {oy2:.1f} "
            f"L {ix2:.1f} {iy2:.1f} "
            f"A {r_in:.1f} {r_in:.1f} 0 {large} 0 {ix1:.1f} {iy1:.1f} Z"
        )

    for pct in (0, 25, 50, 75):
        angle = -math.pi / 2 + (pct / 100) * 2 * math.pi
        gx, gy = point_at(angle, r_max)
        p.append(
            f'<line class="sc-radialbar-grid" data-pct="{pct}" '
            f'x1="{cx:.1f}" y1="{cy:.1f}" x2="{gx:.1f}" y2="{gy:.1f}" '
            f'stroke="{theme.grid_color}" stroke-width="1"/>'
        )

    for j in range(n_cats):
        r_out = r_max - j * band
        r_in = r_out - band + track_gap
        p.append(
            f'<path class="sc-radialbar-track" data-index="{j}" '
            f'd="{arc_path(r_out, r_in, -math.pi / 2, -math.pi / 2 + 2 * math.pi - 0.001)}" '
            f'fill="{theme.grid_color}" fill-opacity="0.15" stroke="none"/>'
        )

    for j in range(n_cats):
        r_out = r_max - j * band
        r_in = r_out - band + track_gap
        label = cats[j] if j < len(cats) else str(j)
        lx = cx - r_out - 4
        ly = cy
        p.append(
            f'<text class="sc-radialbar-label" data-index="{j}" '
            f'x="{lx:.1f}" y="{ly:.1f}" text-anchor="end" '
            f'dominant-baseline="central" font-size="11" fill="{theme.axis_label_color}">'
            f"{esc(label)}</text>"
        )

    for pct in (25, 50, 75, 100):
        angle = -math.pi / 2 + (pct / 100) * 2 * math.pi
        tick_val = y_max * pct / 100
        tx, ty2 = point_at(angle, r_max + 4)
        cos_a = math.cos(angle)
        if cos_a > 0.01:
            anchor = "start"
        elif cos_a < -0.01:
            anchor = "end"
        else:
            anchor = "middle"
        p.append(
            f'<text class="sc-radialbar-tick" data-value="{esc(fmt_num(tick_val))}" '
            f'x="{tx:.1f}" y="{ty2:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="9" fill="{theme.axis_label_color}">'
            f"{esc(fmt_num(tick_val))}</text>"
        )

    cumulative = [0.0] * n_cats
    for si, s in enumerate(spec.series):
        color = palette[si % len(palette)]
        if isinstance(s.color, Gradient):
            color = s.color.stops[0].color if s.color.stops else color
        elif s.color:
            color = s.color
        color = esc(color)

        for j in range(n_cats):
            v = s.data[j] if j < len(s.data) else 0.0
            if v <= 0:
                continue
            r_out = r_max - j * band
            r_in = r_out - band + track_gap
            a_start = -math.pi / 2 + (cumulative[j] / y_max) * 2 * math.pi
            a_end = -math.pi / 2 + ((cumulative[j] + v) / y_max) * 2 * math.pi

            p.append(
                f'<path class="sc-radialbar-bar sc-point" data-series="{si}" '
                f'data-index="{j}" data-y="{esc(fmt_num(v))}" data-color="{color}" '
                f'd="{arc_path(r_out, r_in, a_start, a_end)}" '
                f'fill="{color}" stroke="{theme.background or "#fff"}" stroke-width="1"/>'
            )

        for j in range(n_cats):
            v = s.data[j] if j < len(s.data) else 0.0
            cumulative[j] += max(0.0, v)

    if spec.legend and spec.series:
        gap_l = 22
        est = [len(s.name) * 7 + 26 for s in spec.series]
        total_w = sum(est) + gap_l * (len(est) - 1) if est else 0
        lx = plot_x + (plot_w - total_w) / 2
        ly = H - 10
        p.append('<g class="sc-legend">')
        for si, s in enumerate(spec.series):
            color = palette[si % len(palette)]
            if isinstance(s.color, Gradient):
                color = s.color.stops[0].color if s.color.stops else color
            elif s.color:
                color = s.color
            color = esc(color)
            p.append(f'<g class="sc-legend-item" data-series="{si}">')
            p.append(f'<rect x="{lx:.1f}" y="{ly - 9:.1f}" width="14" height="4" rx="2" fill="{color}"/>')
            p.append(
                f'<text x="{lx + 20:.1f}" y="{ly - 2:.1f}" font-size="12" '
                f'fill="{theme.legend_text_color}">{esc(s.name)}</text>'
            )
            p.append("</g>")
            lx += est[si] + gap_l
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
