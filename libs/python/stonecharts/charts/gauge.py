"""Gauge chart renderer: ChartSpec -> SVG string.

Value-to-angle pointer over a 270-degree annular arc with colored range bands.
Non-Cartesian (Family B polar sibling) — own SVG shell, no axes.
See charts/gauge/design.md for the full geometry contract.
"""

from __future__ import annotations

import math

from ..spec import ChartSpec, Gradient
from ..util import esc, fmt_num
from ._cartesian import a11y_summary

_GAUGE_START = 3 * math.pi / 4
_GAUGE_SWEEP = 3 * math.pi / 2


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height
    theme = spec.theme
    palette = theme.palette
    _cid = esc(spec.id)

    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, "Gauge"))
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
    value = s0.data[0] if s0 and s0.data else 0.0

    gauge_min = spec.gauge_min
    gauge_max = spec.gauge_max
    if gauge_max <= gauge_min:
        gauge_max = gauge_min + 100

    bands = spec.gauge_bands or []

    ptr_color = esc(palette[0])
    if s0 is not None:
        if isinstance(s0.color, Gradient):
            ptr_color = esc(s0.color.stops[0].color) if s0.color.stops else esc(palette[0])
        elif s0.color:
            ptr_color = esc(s0.color)

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

    cx = plot_x + plot_w / 2
    cy = plot_y + plot_h / 2
    r_max = min(plot_w, plot_h) / 2
    track_w = r_max * 0.15
    r_outer = r_max
    r_inner = r_max - track_w

    track_color = theme.grid_color

    a1 = _GAUGE_START
    a2 = _GAUGE_START + _GAUGE_SWEEP
    ox1 = cx + r_outer * math.cos(a1)
    oy1 = cy + r_outer * math.sin(a1)
    ox2 = cx + r_outer * math.cos(a2)
    oy2 = cy + r_outer * math.sin(a2)
    ix1 = cx + r_inner * math.cos(a1)
    iy1 = cy + r_inner * math.sin(a1)
    ix2 = cx + r_inner * math.cos(a2)
    iy2 = cy + r_inner * math.sin(a2)
    d_track = (
        f"M {ox1:.1f} {oy1:.1f} "
        f"A {r_outer:.1f} {r_outer:.1f} 0 1 1 {ox2:.1f} {oy2:.1f} "
        f"L {ix2:.1f} {iy2:.1f} "
        f"A {r_inner:.1f} {r_inner:.1f} 0 1 0 {ix1:.1f} {iy1:.1f} Z"
    )
    p.append(f'<path class="sc-gauge-track" d="{d_track}" fill="{track_color}"/>')

    if s0 is not None:
        p.append('<g class="sc-series" data-series="0">')

        for bi, band in enumerate(bands):
            b_from = max(band.from_val, gauge_min)
            b_to = min(band.to_val, gauge_max)
            if b_to <= b_from:
                continue
            frac1 = (b_from - gauge_min) / (gauge_max - gauge_min)
            frac2 = (b_to - gauge_min) / (gauge_max - gauge_min)
            ba1 = _GAUGE_START + frac1 * _GAUGE_SWEEP
            ba2 = _GAUGE_START + frac2 * _GAUGE_SWEEP
            b_sweep = ba2 - ba1
            b_large = 1 if b_sweep > math.pi else 0

            box1 = cx + r_outer * math.cos(ba1)
            boy1 = cy + r_outer * math.sin(ba1)
            box2 = cx + r_outer * math.cos(ba2)
            boy2 = cy + r_outer * math.sin(ba2)
            bix1 = cx + r_inner * math.cos(ba1)
            biy1 = cy + r_inner * math.sin(ba1)
            bix2 = cx + r_inner * math.cos(ba2)
            biy2 = cy + r_inner * math.sin(ba2)
            d_band = (
                f"M {box1:.1f} {boy1:.1f} "
                f"A {r_outer:.1f} {r_outer:.1f} 0 {b_large} 1 {box2:.1f} {boy2:.1f} "
                f"L {bix2:.1f} {biy2:.1f} "
                f"A {r_inner:.1f} {r_inner:.1f} 0 {b_large} 0 {bix1:.1f} {biy1:.1f} Z"
            )
            p.append(
                f'<path class="sc-gauge-band" data-index="{bi}" '
                f'data-from="{esc(fmt_num(band.from_val))}" data-to="{esc(fmt_num(band.to_val))}" '
                f'd="{d_band}" fill="{esc(band.color)}"/>'
            )

        frac = max(0.0, min(1.0, (value - gauge_min) / (gauge_max - gauge_min)))
        ptr_angle = _GAUGE_START + frac * _GAUGE_SWEEP
        tip_r = r_inner - 4
        base_w = 6.0
        tail_r = 12.0
        tip_x = cx + tip_r * math.cos(ptr_angle)
        tip_y = cy + tip_r * math.sin(ptr_angle)
        left_x = cx + base_w * math.cos(ptr_angle + math.pi / 2)
        left_y = cy + base_w * math.sin(ptr_angle + math.pi / 2)
        right_x = cx + base_w * math.cos(ptr_angle - math.pi / 2)
        right_y = cy + base_w * math.sin(ptr_angle - math.pi / 2)
        tail_x = cx + tail_r * math.cos(ptr_angle + math.pi)
        tail_y = cy + tail_r * math.sin(ptr_angle + math.pi)
        d_ptr = (
            f"M {tip_x:.1f} {tip_y:.1f} "
            f"L {left_x:.1f} {left_y:.1f} "
            f"L {tail_x:.1f} {tail_y:.1f} "
            f"L {right_x:.1f} {right_y:.1f} Z"
        )
        s_name = s0.name
        p.append(
            f'<path class="sc-pointer sc-point" data-series="0" '
            f'data-series-name="{esc(s_name)}" '
            f'data-y="{esc(fmt_num(value))}" data-color="{ptr_color}" '
            f'd="{d_ptr}" fill="{ptr_color}"/>'
        )

        p.append(f'<circle class="sc-pivot" cx="{cx:.1f}" cy="{cy:.1f}" r="8" fill="{ptr_color}"/>')

        p.append("</g>")

    p.append(
        f'<text class="sc-gauge-value" x="{cx:.1f}" y="{cy + 28:.1f}" '
        f'text-anchor="middle" font-size="20" font-weight="700" '
        f'fill="{theme.title_color}">{esc(fmt_num(value))}</text>'
    )

    if spec.legend and spec.series and s0 is not None:
        gap = 22
        est = [len(s0.name) * 7 + 26]
        total_w = sum(est) + gap * (len(est) - 1) if est else 0
        lx = plot_x + (plot_w - total_w) / 2
        ly = H - 10
        p.append('<g class="sc-legend">')
        p.append('<g class="sc-legend-item" data-series="0">')
        p.append(f'<rect x="{lx:.1f}" y="{ly - 9:.1f}" width="14" height="4" rx="2" fill="{ptr_color}"/>')
        p.append(
            f'<text x="{lx + 20:.1f}" y="{ly - 2:.1f}" font-size="12" '
            f'fill="{theme.legend_text_color}">{esc(s0.name)}</text>'
        )
        p.append("</g>")
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
