"""Development-triangle chart renderer: ChartSpec -> SVG string.

Actuarial loss-development matrix with optional diagonal highlight,
development factors, color scale, and cell annotations. Does NOT use
render_cartesian — this is a matrix/table layout with its own SVG shell.
See charts/development-triangle/design.md for the full geometry contract.
"""

from __future__ import annotations

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import a11y_summary

CELL_W = 72.0
CELL_H = 28.0
HEADER_W = 68.0
HEADER_H = 24.0

_LIGHT_R, _LIGHT_G, _LIGHT_B = 227, 242, 253
_DARK_R, _DARK_G, _DARK_B = 21, 101, 192


def _scale_color(t: float) -> str:
    r = int(_LIGHT_R + t * (_DARK_R - _LIGHT_R) + 0.5)
    g = int(_LIGHT_G + t * (_DARK_G - _LIGHT_G) + 0.5)
    b = int(_LIGHT_B + t * (_DARK_B - _LIGHT_B) + 0.5)
    return f"#{r:02x}{g:02x}{b:02x}"


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height
    theme = spec.theme
    cid = esc(spec.id)

    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, "Development triangle"))
        a11y_attr = f' role="img" aria-label="{_sum}"'
        a11y_desc = f"<desc>{_sum}</desc>"

    m_top: float = 20
    if spec.title:
        m_top += 26
    if spec.subtitle:
        m_top += 18
    m_left: float = 22
    m_right: float = 22
    m_bottom: float = 20
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

    tri = spec.triangle
    origins = tri.origins if tri else []
    periods = tri.periods if tri else []
    values = tri.values if tri else []
    n_rows = len(origins)
    n_cols = len(periods)

    show_factors = spec.factors_config is not None and spec.factors_config.show
    use_color = spec.color_scale is not None
    diag_on = spec.diagonal is not None and spec.diagonal.highlight

    all_vals: list[float] = []
    for row in values:
        all_vals.extend(row)
    min_val = min(all_vals) if all_vals else 0.0
    max_val = max(all_vals) if all_vals else 0.0
    val_range = max_val - min_val if max_val > min_val else 1.0

    grid_x = m_left + HEADER_W
    grid_y = m_top + HEADER_H
    factor_h = CELL_H if show_factors else 0.0

    cell_color = theme.grid_color or "#d8d8e0"
    text_color = theme.title_color or "#22223a"
    header_color = theme.axis_label_color or "#666"
    diag_color = "#e65100"
    ann_color = "#d32f2f"

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

    p.append('<g class="sc-dt-headers">')
    for c in range(n_cols):
        cx = grid_x + c * CELL_W + CELL_W / 2
        cy = grid_y - 6
        p.append(
            f'<text class="sc-dt-period-header" x="{cx:.1f}" y="{cy:.1f}" '
            f'text-anchor="middle" font-size="11" font-weight="600" fill="{header_color}">'
            f'{esc(fmt_num(float(periods[c])))}</text>'
        )
    p.append("</g>")

    p.append('<g class="sc-dt-origins">')
    for r in range(n_rows):
        ox = grid_x - 8
        oy = grid_y + r * CELL_H + CELL_H / 2 + 4
        p.append(
            f'<text class="sc-dt-origin-header" x="{ox:.1f}" y="{oy:.1f}" '
            f'text-anchor="end" font-size="11" font-weight="600" fill="{header_color}">'
            f'{esc(origins[r])}</text>'
        )
    p.append("</g>")

    p.append('<g class="sc-dt-grid">')
    for r in range(n_rows):
        row = values[r] if r < len(values) else []
        p.append(f'<g class="sc-dt-row" data-origin="{r}">')
        for c in range(len(row)):
            v = row[c]
            x = grid_x + c * CELL_W
            y = grid_y + r * CELL_H
            if use_color:
                t = (v - min_val) / val_range
                fill = _scale_color(t)
            else:
                fill = "none"
            p.append(
                f'<rect class="sc-dt-cell sc-point" data-origin="{r}" data-period="{c}" '
                f'x="{x:.1f}" y="{y:.1f}" width="{CELL_W:.1f}" height="{CELL_H:.1f}" '
                f'fill="{fill}" stroke="{cell_color}"/>'
            )
            tx = x + CELL_W / 2
            ty_cell = y + CELL_H / 2 + 4
            v_color = "#ffffff" if use_color and (v - min_val) / val_range > 0.55 else text_color
            p.append(
                f'<text class="sc-dt-value" x="{tx:.1f}" y="{ty_cell:.1f}" '
                f'text-anchor="middle" font-size="10" fill="{v_color}">{esc(fmt_num(v))}</text>'
            )
        p.append("</g>")
    p.append("</g>")

    if diag_on:
        p.append('<g class="sc-dt-diagonal">')
        for r in range(n_rows):
            c = n_rows - 1 - r
            row = values[r] if r < len(values) else []
            if c < len(row):
                x = grid_x + c * CELL_W
                y = grid_y + r * CELL_H
                p.append(
                    f'<rect class="sc-dt-diag" data-origin="{r}" data-period="{c}" '
                    f'x="{x:.1f}" y="{y:.1f}" width="{CELL_W:.1f}" height="{CELL_H:.1f}" '
                    f'fill="none" stroke="{diag_color}" stroke-width="2"/>'
                )
        if spec.diagonal and spec.diagonal.label:
            lx = grid_x + n_cols * CELL_W + 8
            ly = grid_y + CELL_H / 2 + 4
            p.append(
                f'<text class="sc-dt-diag-label" x="{lx:.1f}" y="{ly:.1f}" '
                f'font-size="10" fill="{diag_color}">{esc(spec.diagonal.label)}</text>'
            )
        p.append("</g>")

    if show_factors:
        factors: list[float] = []
        for c in range(n_cols - 1):
            num = 0.0
            den = 0.0
            for r in range(n_rows):
                row = values[r] if r < len(values) else []
                if c + 1 < len(row):
                    num += row[c + 1]
                    den += row[c]
            factors.append(num / den if den > 0 else 0.0)
        fy = grid_y + n_rows * CELL_H
        flx = grid_x - 8
        fly = fy + CELL_H / 2 + 4
        p.append('<g class="sc-dt-factors">')
        p.append(
            f'<text class="sc-dt-factor-header" x="{flx:.1f}" y="{fly:.1f}" '
            f'text-anchor="end" font-size="10" font-weight="600" fill="{header_color}">Factors</text>'
        )
        for c in range(len(factors)):
            fx = grid_x + c * CELL_W + CELL_W / 2 + CELL_W / 2
            p.append(
                f'<text class="sc-dt-factor" x="{fx:.1f}" y="{fly:.1f}" '
                f'text-anchor="middle" font-size="10" fill="{text_color}">{factors[c]:.3f}</text>'
            )
        p.append("</g>")

    if spec.triangle_annotations:
        origin_idx = {o: i for i, o in enumerate(origins)}
        period_idx = {int(periods[i]): i for i in range(n_cols)}
        p.append('<g class="sc-dt-annotations">')
        for ann in spec.triangle_annotations:
            ri = origin_idx.get(ann.origin)
            ci = period_idx.get(ann.period)
            if ri is not None and ci is not None:
                row = values[ri] if ri < len(values) else []
                if ci < len(row):
                    ax = grid_x + ci * CELL_W + CELL_W - 6
                    ay = grid_y + ri * CELL_H + 6
                    p.append(
                        f'<circle class="sc-dt-annotation" cx="{ax:.1f}" cy="{ay:.1f}" '
                        f'r="4" fill="{ann_color}" opacity="0.8"/>'
                    )
                    p.append(
                        f'<text class="sc-dt-annotation-text" x="{ax:.1f}" y="{ay + 3:.1f}" '
                        f'text-anchor="middle" font-size="7" font-weight="700" fill="#ffffff">!</text>'
                    )
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
