"""Pie chart renderer: ChartSpec -> SVG string.

Centered sector arcs with value-to-angle mapping. Does NOT use
render_cartesian — pie has no axes (Family B polar foundation).
See charts/pie/design.md for the full geometry contract.
"""

from __future__ import annotations

import math

from ..spec import ChartSpec, Gradient
from ..util import esc, fmt_num
from ._cartesian import a11y_summary, gradient_def, pattern_def


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height
    theme = spec.theme
    palette = theme.palette
    cid = esc(spec.id)

    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, "Pie"))
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

    s0 = spec.series[0] if spec.series else None
    data = list(s0.data) if s0 else []
    n = len(data)
    cats = spec.x_axis.categories or [str(i) for i in range(n)]

    defs_parts: list[str] = []
    color_by_point = True
    pie_fill = ""
    if s0 is not None:
        if isinstance(s0.color, Gradient):
            gid = f"{cid}-grad-0"
            defs_parts.append(gradient_def(gid, s0.color))
            pie_fill = f"url(#{gid})"
            color_by_point = False
        elif s0.color:
            pie_fill = esc(s0.color)
            color_by_point = False
        if s0.pattern is not None:
            pid = f"{cid}-pat-0"
            defs_parts.append(pattern_def(pid, s0.pattern))
            pie_fill = f"url(#{pid})"
            color_by_point = False

    solid0 = ""
    if s0 is not None:
        if isinstance(s0.color, Gradient):
            solid0 = esc(s0.color.stops[0].color) if s0.color.stops else esc(palette[0])
        elif s0.color:
            solid0 = esc(s0.color)
        else:
            solid0 = esc(palette[0])

    total = sum(v for v in data if v > 0)

    stroke_color = "#1e1e2f" if theme.background else "#ffffff"

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

    if defs_parts:
        p.append("<defs>" + "".join(defs_parts) + "</defs>")

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

    cx = plot_x + plot_w / 2
    cy = plot_y + plot_h / 2
    r = min(plot_w, plot_h) / 2

    if n > 0 and s0 is not None and total > 0:
        p.append('<g class="sc-series" data-series="0">')

        positive_count = sum(1 for v in data if v > 0)

        if positive_count == 1:
            idx = next(i for i, v in enumerate(data) if v > 0)
            fill = esc(palette[idx % len(palette)]) if color_by_point else pie_fill
            cat = cats[idx] if idx < len(cats) else str(idx)
            pct = f"{100.0:.1f}%"
            p.append(
                f'<circle class="sc-slice sc-point" data-series="0" '
                f'data-series-name="{esc(s0.name)}" data-x="{esc(cat)}" '
                f'data-y="{esc(fmt_num(data[idx]))}" data-color="{fill}" '
                f'data-index="{idx}" data-percentage="{pct}" '
                f'data-r="{r:.1f}" data-r-hover="{r + 4:.1f}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{fill}" stroke="{stroke_color}" stroke-width="2"/>'
            )
        else:
            angle = -math.pi / 2
            for i in range(n):
                v = data[i]
                if v <= 0:
                    continue
                sweep = (v / total) * 2 * math.pi
                x1 = cx + r * math.cos(angle)
                y1 = cy + r * math.sin(angle)
                end_angle = angle + sweep
                x2 = cx + r * math.cos(end_angle)
                y2 = cy + r * math.sin(end_angle)
                large_arc = 1 if sweep > math.pi else 0

                fill = esc(palette[i % len(palette)]) if color_by_point else pie_fill
                cat = cats[i] if i < len(cats) else str(i)
                pct = f"{(v / total) * 100:.1f}%"

                p.append(
                    f'<path class="sc-slice sc-point" data-series="0" '
                    f'data-series-name="{esc(s0.name)}" data-x="{esc(cat)}" '
                    f'data-y="{esc(fmt_num(v))}" data-color="{fill}" '
                    f'data-index="{i}" data-percentage="{pct}" '
                    f'data-r="{r:.1f}" data-r-hover="{r + 4:.1f}" '
                    f'cx="{cx:.1f}" cy="{cy:.1f}" '
                    f'd="M {cx:.1f} {cy:.1f} L {x1:.1f} {y1:.1f} '
                    f'A {r:.1f} {r:.1f} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z" '
                    f'fill="{fill}" stroke="{stroke_color}" stroke-width="2"/>'
                )

                angle = end_angle

        p.append("</g>")

    if spec.legend and spec.series and s0 is not None:
        gap = 22
        est = [len(s0.name) * 7 + 26]
        total_w = sum(est) + gap * (len(est) - 1) if est else 0
        lx = plot_x + (plot_w - total_w) / 2
        ly = H - 10
        p.append('<g class="sc-legend">')
        p.append('<g class="sc-legend-item" data-series="0">')
        p.append(f'<rect x="{lx:.1f}" y="{ly - 9:.1f}" width="14" height="4" rx="2" fill="{solid0}"/>')
        p.append(
            f'<text x="{lx + 20:.1f}" y="{ly - 2:.1f}" font-size="12" '
            f'fill="{theme.legend_text_color}">{esc(s0.name)}</text>'
        )
        p.append("</g>")
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
