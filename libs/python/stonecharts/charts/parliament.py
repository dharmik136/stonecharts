"""Parliament / hemicycle chart renderer: ChartSpec -> SVG string.

Unit dots arranged in concentric semicircular arcs — one dot per item,
colored by category. Single-series only; total dots = sum of values.
Non-Cartesian (Family B polar sibling) — own SVG shell, no axes.
See charts/parliament/design.md for the full geometry contract.
"""

from __future__ import annotations

import math

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import a11y_summary


def _hemicycle_layout(total: int, r_min: float, r_max: float):
    """Compute row radii and per-row capacities for a hemicycle of *total* dots.

    Returns (rows, dot_r) where rows is a list of (radius, capacity) tuples
    and dot_r is the rendered dot radius.
    """
    if total <= 0:
        return [], 2.0

    n_rows = max(1, math.ceil((-r_min + math.sqrt(r_min**2 + 2 * (r_max - r_min) * total / math.pi)) / (r_max - r_min)))
    n_rows = max(1, min(n_rows, total))

    if n_rows == 1:
        radii = [0.5 * (r_min + r_max)]
    else:
        radii = [r_min + k * (r_max - r_min) / (n_rows - 1) for k in range(n_rows)]

    raw_caps = [max(1, math.floor(math.pi * r)) for r in radii]
    raw_total = sum(raw_caps)

    if raw_total < total:
        scale = total / raw_total if raw_total > 0 else 1
        raw_caps = [max(1, math.ceil(c * scale)) for c in raw_caps]

    rows: list[tuple[float, int]] = []
    assigned = 0
    for k in range(n_rows):
        cap = total - assigned if k == n_rows - 1 else min(raw_caps[k], total - assigned)
        if cap <= 0:
            continue
        rows.append((radii[k], cap))
        assigned += cap

    row_gap = (r_max - r_min) / n_rows if n_rows > 1 else r_max - r_min
    dot_r = max(1.5, min(6.0, row_gap * 0.35))

    return rows, dot_r


def render_svg(spec: ChartSpec) -> str:
    W, H = spec.width, spec.height
    theme = spec.theme
    palette = theme.palette
    _cid = esc(spec.id)

    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, "Parliament"))
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
    plot_w = W - m_left - m_right
    plot_h = H - m_top - m_bottom

    cx = plot_x + plot_w / 2
    cy = plot_y + plot_h * 0.92

    r_max = min(plot_w / 2, plot_h * 0.85)
    r_min = r_max * 0.35

    bg = theme.background or "#ffffff"
    fg_title = theme.title_color
    fg_sub = theme.subtitle_color
    fg_legend = theme.legend_text_color

    s0 = spec.series[0] if spec.series else None
    data = list(s0.data) if s0 else []
    cats = spec.x_axis.categories or []
    n_cats = max(len(data), len(cats))
    while len(data) < n_cats:
        data.append(0)
    while len(cats) < len(data):
        cats.append(str(len(cats)))

    int_data = [max(0, round(v)) for v in data]
    total = sum(int_data)

    rows, dot_r = _hemicycle_layout(total, r_min, r_max)

    colors = [palette[j % len(palette)] for j in range(n_cats)]

    cat_assignments: list[int] = []
    for j, count in enumerate(int_data):
        cat_assignments.extend([j] * count)

    p: list[str] = []

    vb = f"0 0 {W} {H}"
    resp = f' style="max-width:{W}px"' if spec.responsive else ""
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
        f'class="sc-chart" font-family="Segoe UI,Helvetica,Arial,sans-serif"'
        f"{a11y_attr}{resp}>"
    )
    if a11y_desc:
        p.append(a11y_desc)

    p.append(f'<defs><clipPath id="{_cid}-clip"><rect x="0" y="0" width="{W}" height="{H}"/></clipPath></defs>')

    p.append(f'<rect class="sc-bg" x="0" y="0" width="{W}" height="{H}" fill="{bg}"/>')

    ty = 18
    if spec.title:
        p.append(
            f'<text class="sc-title" x="{W / 2:.1f}" y="{ty}" '
            f'text-anchor="middle" font-size="16" font-weight="600" '
            f'fill="{fg_title}">{esc(spec.title)}</text>'
        )
        ty += 20
    if spec.subtitle:
        p.append(
            f'<text class="sc-subtitle" x="{W / 2:.1f}" y="{ty}" '
            f'text-anchor="middle" font-size="12" fill="{fg_sub}">'
            f"{esc(spec.subtitle)}</text>"
        )

    dot_idx = 0
    for radius, cap in rows:
        for i in range(cap):
            if dot_idx >= total:
                break
            angle = math.pi - (i + 0.5) * math.pi / cap
            dx = cx + radius * math.cos(angle)
            dy = cy - radius * math.sin(angle)
            cat_j = cat_assignments[dot_idx]
            fill = colors[cat_j]
            p.append(
                f'<circle class="sc-parliament-dot sc-point" '
                f'data-category="{cat_j}" data-index="{dot_idx}" '
                f'data-color="{esc(fill)}" '
                f'cx="{dx:.1f}" cy="{dy:.1f}" r="{fmt_num(dot_r)}" '
                f'fill="{esc(fill)}"/>'
            )
            dot_idx += 1

    if spec.legend:
        legend_y = H - m_bottom + 14
        legend_items: list[str] = []
        for j in range(n_cats):
            legend_items.append(
                f'<rect x="0" y="0" width="10" height="10" rx="2" fill="{esc(colors[j])}"/>'
                f'<text x="14" y="9" font-size="11" fill="{fg_legend}">'
                f"{esc(cats[j])}</text>"
            )
        total_w = n_cats * 80
        lx = (W - total_w) / 2
        p.append(f'<g class="sc-legend" transform="translate({lx:.1f},{legend_y:.1f})">')
        for j, item in enumerate(legend_items):
            p.append(
                f'<g class="sc-legend-item" data-series="{j}" '
                f'transform="translate({j * 80},0)">{item}</g>'
            )
        p.append("</g>")

    p.append("</svg>")
    return "".join(p)
