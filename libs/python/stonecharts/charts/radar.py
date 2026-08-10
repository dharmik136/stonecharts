"""Radar / spider chart renderer: ChartSpec -> SVG string.

Multi-dimensional categorical data on radial axes forming polygonal overlays.
Non-Cartesian (Family B polar sibling) — own SVG shell, no axes.
See charts/radar/design.md for the full geometry contract.
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
        _sum = esc(a11y_summary(spec, "Radar"))
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
    n_axes = len(cats)
    if n_axes < 3:
        n_axes = 3

    y_min = spec.y_axis.min if spec.y_axis.min is not None else 0.0
    y_max_spec = spec.y_axis.max
    if y_max_spec is not None:
        y_max = y_max_spec
    else:
        y_max = 0.0
        for s in spec.series:
            for v in s.data:
                if v > y_max:
                    y_max = v
    if y_max <= y_min:
        y_max = y_min + 100

    label_margin = 40.0
    cx = plot_x + plot_w / 2
    cy = plot_y + plot_h / 2
    r_max = min(plot_w, plot_h) / 2 - label_margin

    n_rings = 5

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

    def axis_angle(i: int) -> float:
        return -math.pi / 2 + i * 2 * math.pi / n_axes

    def point_at(angle: float, r: float) -> tuple[float, float]:
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    for level in range(n_rings):
        frac = (level + 1) / n_rings
        r = r_max * frac
        pts = " ".join(
            f"{point_at(axis_angle(i), r)[0]:.1f},{point_at(axis_angle(i), r)[1]:.1f}" for i in range(n_axes)
        )
        p.append(
            f'<polygon class="sc-radar-ring" data-level="{level}" '
            f'points="{pts}" fill="none" stroke="{theme.grid_color}" stroke-width="1"/>'
        )

    for i in range(n_axes):
        ex, ey = point_at(axis_angle(i), r_max)
        p.append(
            f'<line class="sc-radar-axis" data-index="{i}" '
            f'x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{theme.grid_color}" stroke-width="1"/>'
        )

    for i in range(n_axes):
        angle = axis_angle(i)
        lx, ly = point_at(angle, r_max + 12)
        cos_a = math.cos(angle)
        if cos_a > 0.01:
            anchor = "start"
        elif cos_a < -0.01:
            anchor = "end"
        else:
            anchor = "middle"
        label = cats[i] if i < len(cats) else str(i)
        p.append(
            f'<text class="sc-radar-label" data-index="{i}" '
            f'x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="11" fill="{theme.axis_label_color}">'
            f"{esc(label)}</text>"
        )

    for level in range(n_rings):
        frac = (level + 1) / n_rings
        tick_val = y_min + frac * (y_max - y_min)
        tick_r = r_max * frac
        tx, ty2 = point_at(axis_angle(0), tick_r)
        p.append(
            f'<text class="sc-radar-tick" data-value="{esc(fmt_num(tick_val))}" '
            f'x="{tx + 4:.1f}" y="{ty2 - 2:.1f}" font-size="9" '
            f'fill="{theme.axis_label_color}">{esc(fmt_num(tick_val))}</text>'
        )

    for si, s in enumerate(spec.series):
        color = palette[si % len(palette)]
        if isinstance(s.color, Gradient):
            color = s.color.stops[0].color if s.color.stops else color
        elif s.color:
            color = s.color
        color = esc(color)

        fill_opacity = s.fill_opacity

        vertices: list[tuple[float, float]] = []
        for j in range(n_axes):
            v = s.data[j] if j < len(s.data) else 0.0
            frac = (v - y_min) / (y_max - y_min)
            frac = max(0.0, min(1.0, frac))
            r = r_max * frac
            vx, vy = point_at(axis_angle(j), r)
            vertices.append((vx, vy))

        path_d = " ".join(f"{'M' if k == 0 else 'L'} {vx:.1f} {vy:.1f}" for k, (vx, vy) in enumerate(vertices))
        path_d += " Z"

        fill_attr = f'fill="{color}"' if fill_opacity > 0 else 'fill="none"'
        opacity_attr = f' fill-opacity="{fill_opacity}"' if fill_opacity > 0 else ""

        p.append(
            f'<path class="sc-radar-poly sc-point" data-series="{si}" '
            f'data-series-name="{esc(s.name)}" data-color="{color}" '
            f'd="{path_d}" {fill_attr}{opacity_attr} '
            f'stroke="{color}" stroke-width="2"/>'
        )

        for j, (vx, vy) in enumerate(vertices):
            v = s.data[j] if j < len(s.data) else 0.0
            p.append(
                f'<circle class="sc-radar-dot sc-point" data-series="{si}" '
                f'data-index="{j}" data-y="{esc(fmt_num(v))}" '
                f'cx="{vx:.1f}" cy="{vy:.1f}" r="4" fill="{color}"/>'
            )

    if spec.legend and spec.series:
        gap = 22
        est = [len(s.name) * 7 + 26 for s in spec.series]
        total_w = sum(est) + gap * (len(est) - 1) if est else 0
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
            lx += est[si] + gap
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
