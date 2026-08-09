"""Funnel chart renderer: ChartSpec -> SVG string.

Centered trapezoid stack with value->width scaling. Does NOT use
render_cartesian — funnel is the declared substrate exception (no axes).
See charts/funnel/design.md for the full geometry contract.
"""

from __future__ import annotations

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
        _sum = esc(a11y_summary(spec, "Funnel"))
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
    funnel_fill = ""
    if s0 is not None:
        if isinstance(s0.color, Gradient):
            gid = f"{cid}-grad-0"
            defs_parts.append(gradient_def(gid, s0.color))
            funnel_fill = f"url(#{gid})"
            color_by_point = False
        elif s0.color:
            funnel_fill = esc(s0.color)
            color_by_point = False
        if s0.pattern is not None:
            pid = f"{cid}-pat-0"
            defs_parts.append(pattern_def(pid, s0.pattern))
            funnel_fill = f"url(#{pid})"
            color_by_point = False

    solid0 = ""
    if s0 is not None:
        if isinstance(s0.color, Gradient):
            solid0 = esc(s0.color.stops[0].color) if s0.color.stops else esc(palette[0])
        elif s0.color:
            solid0 = esc(s0.color)
        else:
            solid0 = esc(palette[0])

    subtype = spec.subtype or "funnel"
    min_w_frac = spec.min_width
    neck_w_frac = spec.neck_width
    neck_h_frac = spec.neck_height

    max_val = max(data) if data else 0.0

    def wscale(v: float) -> float:
        if max_val <= 0:
            return 0.0
        return plot_w * v / max_val

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

    if n > 0 and s0 is not None:
        band_h = plot_h / n
        cx = plot_x + plot_w / 2

        order = list(range(n))
        if subtype == "pyramid":
            order = list(reversed(order))

        p.append('<g class="sc-series" data-series="0">')

        for draw_idx, stage_idx in enumerate(order):
            v = data[stage_idx]
            w_top = wscale(v)
            w_top = max(w_top, min_w_frac * plot_w)

            if subtype == "neck":
                neck_y = plot_y + plot_h * (1 - neck_h_frac)
                neck_w = neck_w_frac * plot_w
                y_top = plot_y + band_h * draw_idx
                y_bot = plot_y + band_h * (draw_idx + 1)

                if draw_idx < n - 1:
                    next_stage = order[draw_idx + 1]
                    w_next = wscale(data[next_stage])
                    w_next = max(w_next, min_w_frac * plot_w)
                else:
                    w_next = 0.0

                if y_top >= neck_y:
                    w_top = neck_w
                    w_bot = neck_w
                elif y_bot <= neck_y:
                    taper_h = neck_y - plot_y
                    if taper_h <= 0:
                        t_top = 0.0
                        t_bot = 0.0
                    else:
                        t_top = (y_top - plot_y) / taper_h
                        t_bot = (y_bot - plot_y) / taper_h
                    w0 = wscale(data[order[0]])
                    w0 = max(w0, min_w_frac * plot_w)
                    w_top = w0 + (neck_w - w0) * t_top
                    w_bot = w0 + (neck_w - w0) * t_bot
                else:
                    taper_h = neck_y - plot_y
                    t_top = 0.0 if taper_h <= 0 else (y_top - plot_y) / taper_h
                    w0 = wscale(data[order[0]])
                    w0 = max(w0, min_w_frac * plot_w)
                    w_top = w0 + (neck_w - w0) * t_top
                    w_bot = neck_w
            else:
                y_top = plot_y + band_h * draw_idx
                y_bot = plot_y + band_h * (draw_idx + 1)

                if draw_idx < n - 1:
                    next_stage = order[draw_idx + 1]
                    w_bot = wscale(data[next_stage])
                    w_bot = max(w_bot, min_w_frac * plot_w)
                else:
                    w_bot = 0.0 if subtype == "pyramid" else w_top

            x_tl = cx - w_top / 2
            x_tr = cx + w_top / 2
            x_bl = cx - w_bot / 2
            x_br = cx + w_bot / 2
            band_cy = y_top + band_h / 2

            fill = esc(palette[stage_idx % len(palette)]) if color_by_point else funnel_fill

            cat = cats[stage_idx] if stage_idx < len(cats) else str(stage_idx)
            s_name = s0.name

            p.append(
                f'<polygon class="sc-slice sc-point" data-series="0" '
                f'data-series-name="{esc(s_name)}" data-x="{esc(cat)}" '
                f'data-y="{esc(fmt_num(v))}" data-color="{fill}" '
                f'data-r="3.5" data-r-hover="6" '
                f'cx="{cx:.1f}" cy="{band_cy:.1f}" '
                f'points="{x_tl:.1f},{y_top:.1f} {x_tr:.1f},{y_top:.1f} {x_br:.1f},{y_bot:.1f} {x_bl:.1f},{y_bot:.1f}" '
                f'fill="{fill}"/>'
            )

        p.append("</g>")

    if spec.legend and spec.series:
        gap = 22
        est = [len(s0.name) * 7 + 26] if s0 else []
        total = sum(est) + gap * (len(est) - 1) if est else 0
        lx = plot_x + (plot_w - total) / 2
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
