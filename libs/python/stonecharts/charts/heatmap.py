"""Heatmap chart renderer: ChartSpec -> SVG string.

Family C (Matrix / Grid) foundational renderer.
Renders a 2-D categorical grid with color-scale mapping and color-axis legend.
See charts/heatmap/design.md for the canonical contract.
"""

from __future__ import annotations

import math

from ..spec import ChartSpec, ColorAxisConfig
from ..util import esc, fmt_num
from ._cartesian import a11y_summary

_DEFAULT_STOPS: list[tuple[float, str]] = [
    (0.0, "#e0f3f8"),
    (0.5, "#4eb3d3"),
    (1.0, "#084081"),
]


def _parse_hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    if len(c) == 3 or len(c) == 4:
        return int(c[0] * 2, 16), int(c[1] * 2, 16), int(c[2] * 2, 16)
    if len(c) >= 6:
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return 0, 0, 0


def _interpolate_color(t: float, stops: list[tuple[float, str]]) -> str:
    if not stops:
        return "#e0f3f8"
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        s0, s1 = stops[i], stops[i + 1]
        if s0[0] <= t <= s1[0]:
            span = s1[0] - s0[0]
            u = (t - s0[0]) / span if span > 0 else 0.0
            c0 = _parse_hex(s0[1])
            c1 = _parse_hex(s1[1])
            r = int(c0[0] + u * (c1[0] - c0[0]) + 0.5)
            g = int(c0[1] + u * (c1[1] - c0[1]) + 0.5)
            b = int(c0[2] + u * (c1[2] - c0[2]) + 0.5)
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            return f"#{r:02x}{g:02x}{b:02x}"
    return stops[-1][1]


def _resolve_stops(ca: ColorAxisConfig | None) -> list[tuple[float, str]]:
    if ca is not None and ca.stops:
        res = [(float(st[0]), str(st[1])) for st in ca.stops]
        res.sort(key=lambda s: s[0])
        return res
    if ca is not None and (ca.min_color is not None or ca.max_color is not None):
        c_min = ca.min_color or "#e0f3f8"
        c_max = ca.max_color or "#084081"
        return [(0.0, c_min), (1.0, c_max)]
    return list(_DEFAULT_STOPS)


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height
    theme = spec.theme
    x_cats = spec.x_axis.categories if spec.x_axis and spec.x_axis.categories else []
    y_cats = spec.y_axis.categories if spec.y_axis and spec.y_axis.categories else []
    nx = len(x_cats)
    ny = len(y_cats)

    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, "Heatmap"))
        a11y_attr = f' role="img" aria-label="{_sum}"'
        a11y_desc = f"<desc>{_sum}</desc>"

    show_legend = spec.legend is not False and (spec.color_axis is None or spec.color_axis.visible is not False)

    m_top = 20.0
    if spec.title:
        m_top += 26.0
    if spec.subtitle:
        m_top += 18.0

    max_y_len = max((len(c) for c in y_cats), default=0)
    m_left = max(52.0, max_y_len * 7.5 + 24.0)
    if spec.y_axis and spec.y_axis.title:
        m_left += 18.0

    m_right = 24.0

    m_bottom = 46.0
    if spec.x_axis and spec.x_axis.title:
        m_bottom += 18.0
    if show_legend:
        m_bottom += 36.0

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

    plot_w = W - m_left - m_right
    plot_h = H - m_top - m_bottom
    cell_w = plot_w / nx if nx > 0 else 0.0
    cell_h = plot_h / ny if ny > 0 else 0.0

    all_vals: list[float] = []
    for s in spec.series:
        for pt in s.heatmap_data or []:
            if pt.value is not None and not math.isnan(pt.value) and not math.isinf(pt.value):
                all_vals.append(pt.value)

    ca = spec.color_axis
    if ca is not None and ca.min is not None:
        min_val = ca.min
    elif all_vals:
        min_val = min(all_vals)
    else:
        min_val = 0.0

    if ca is not None and ca.max is not None:
        max_val = ca.max
    elif all_vals:
        max_val = max(all_vals)
    else:
        max_val = 100.0

    val_range = max_val - min_val
    if val_range < 0:
        val_range = 0.0

    stops = _resolve_stops(ca)
    stroke_color = "#1e1e2f" if theme.name == "dark" else "#ffffff"

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

    cid = spec.id or "sc"
    gid = f"{cid}-color-axis-grad"
    if show_legend:
        if ca is not None and ca.reversed:
            legend_stops = [(1.0 - st[0], st[1]) for st in stops]
            legend_stops.sort(key=lambda s: s[0])
        else:
            legend_stops = stops
        grad_stops = "".join(f'<stop offset="{fmt_num(st[0])}" stop-color="{st[1]}"/>' for st in legend_stops)
        p.append(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">{grad_stops}</linearGradient></defs>')

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
        ty += 16

    # Y-axis categories and title
    p.append('<g class="sc-axis sc-axis-y">')
    for r in range(ny):
        oy = m_top + r * cell_h + cell_h / 2.0 + 4.0
        p.append(
            f'<text x="{m_left - 8.0:.1f}" y="{oy:.1f}" text-anchor="end" '
            f'font-size="11" fill="{theme.axis_label_color}">{esc(y_cats[r])}</text>'
        )
    p.append("</g>")

    if spec.y_axis and spec.y_axis.title:
        yc = m_top + plot_h / 2.0
        p.append(
            f'<text x="14" y="{yc:.1f}" text-anchor="middle" font-size="12" '
            f'fill="{theme.axis_title_color}" transform="rotate(-90 14 {yc:.1f})">{esc(spec.y_axis.title)}</text>'
        )

    # X-axis categories and title
    p.append('<g class="sc-axis sc-axis-x">')
    for c in range(nx):
        cx = m_left + c * cell_w + cell_w / 2.0
        cy = m_top + plot_h + 16.0
        p.append(
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{theme.axis_label_color}">{esc(x_cats[c])}</text>'
        )
    p.append("</g>")

    if spec.x_axis and spec.x_axis.title:
        xt_y = m_top + plot_h + 34.0
        p.append(
            f'<text x="{m_left + plot_w / 2.0:.1f}" y="{xt_y:.1f}" text-anchor="middle" '
            f'font-size="12" fill="{theme.axis_title_color}">{esc(spec.x_axis.title)}</text>'
        )

    # Series and cell marks
    for si, s in enumerate(spec.series):
        p.append(f'<g class="sc-series sc-series-heatmap" data-series="{si}" data-name="{esc(s.name)}">')
        for pt in s.heatmap_data or []:
            x_cat = x_cats[pt.x] if pt.x < len(x_cats) else str(pt.x)
            y_cat = y_cats[pt.y] if pt.y < len(y_cats) else str(pt.y)

            if pt.value is None or math.isnan(pt.value) or math.isinf(pt.value):
                fill_color = ca.null_color if (ca and ca.null_color) else "#f0f0f0"
            else:
                t = (pt.value - min_val) / val_range if val_range > 0 else 0.5
                t = max(0.0, min(1.0, t))
                if ca and ca.reversed:
                    t = 1.0 - t
                fill_color = _interpolate_color(t, stops)

            rect_x = m_left + pt.x * cell_w + 0.5
            rect_y = m_top + pt.y * cell_h + 0.5
            rect_w = cell_w - 1.0
            rect_h = cell_h - 1.0

            aria_label = f"{y_cat}, {x_cat}: {fmt_num(pt.value)}"

            p.append(
                f'<rect class="sc-cell sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(x_cat)}" data-y="{esc(fmt_num(pt.value))}" data-cell-x="{pt.x}" '
                f'data-cell-y="{pt.y}" data-value="{esc(fmt_num(pt.value))}" data-color="{fill_color}" '
                f'x="{rect_x:.1f}" y="{rect_y:.1f}" width="{rect_w:.1f}" height="{rect_h:.1f}" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="1" tabindex="0" '
                f'aria-label="{esc(aria_label)}"/>'
            )
        p.append("</g>")

    # Legend (color-axis)
    if show_legend:
        bar_w = 200.0
        bar_h = 10.0
        bar_x = m_left + (plot_w - bar_w) / 2.0
        bar_y = m_top + plot_h + 48.0 if spec.x_axis and spec.x_axis.title else m_top + plot_h + 30.0
        label_y = bar_y + bar_h + 12.0
        mid_val = (min_val + max_val) / 2.0
        p.append('<g class="sc-color-axis">')
        p.append(
            f'<rect x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'fill="url(#{gid})" rx="2"/>'
        )
        p.append(
            f'<text x="{bar_x:.1f}" y="{label_y:.1f}" text-anchor="start" font-size="10" '
            f'fill="{theme.axis_label_color}">{esc(fmt_num(min_val))}</text>'
        )
        p.append(
            f'<text x="{bar_x + bar_w / 2.0:.1f}" y="{label_y:.1f}" text-anchor="middle" font-size="10" '
            f'fill="{theme.axis_label_color}">{esc(fmt_num(mid_val))}</text>'
        )
        p.append(
            f'<text x="{bar_x + bar_w:.1f}" y="{label_y:.1f}" text-anchor="end" font-size="10" '
            f'fill="{theme.axis_label_color}">{esc(fmt_num(max_val))}</text>'
        )
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
