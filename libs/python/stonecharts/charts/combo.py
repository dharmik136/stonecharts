"""Combo chart renderer: ChartSpec -> SVG string.

Composition layer dispatching per-series to column or line marks on a shared
plot area. Shared chrome from _cartesian.py; mark logic from column and line.
"""

from __future__ import annotations

from ..spec import Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, dash_array, render_cartesian
from .line import _marker, _path_d, _spline_d

PAD = 0.2


def _kind(s) -> str:
    return s.type if s.type else "column"


def _ypix_for(fr: CartesianFrame, s):
    return fr.ypix2 if s.y_axis == 1 and fr.secondary_axis is not None else fr.ypix


def render_svg(spec) -> str:
    return render_cartesian(spec, "Combo", "band", _combo_marks)


def _combo_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    band_width = fr.band_width()
    group_w = band_width * (1 - PAD)
    stacked = fr.stacking in ("normal", "percent")

    col_indices = [si for si, s in enumerate(fr.spec.series) if _kind(s) == "column"]
    k_col = len(col_indices)
    k_slots = 1 if stacked or not fr.spec.grouping else max(k_col, 1)
    bar_w = group_w / k_slots

    kc_map: dict[int, int] = {}
    kc = 0
    for si, s in enumerate(fr.spec.series):
        if _kind(s) == "column":
            kc_map[si] = kc
            kc += 1

    totals = [0.0] * fr.n
    if stacked:
        for si in col_indices:
            s = fr.spec.series[si]
            for i, v in enumerate(s.data):
                if i < fr.n:
                    totals[i] += v

    positive = [0.0] * fr.n
    negative = [0.0] * fr.n

    for si, s in enumerate(fr.spec.series):
        if _kind(s) == "line":
            _emit_line_series(fr, p, si, s)
        else:
            _emit_column_series(
                fr,
                p,
                si,
                s,
                group_w,
                bar_w,
                kc_map,
                stacked,
                totals,
                positive,
                negative,
            )


def _emit_column_series(fr, p, si, s, group_w, bar_w, kc_map, stacked, totals, positive, negative):
    st = fr.styles[si]
    ypix = _ypix_for(fr, s)
    baseline = ypix(0.0)
    kc = kc_map[si]

    p.append(f'<g class="sc-series" data-series="{si}">')
    for i, raw in enumerate(s.data):
        if i >= fr.n:
            break
        cx_band = fr.xpix(i)
        if stacked:
            left = cx_band - group_w / 2
            if fr.stacking == "percent":
                total = totals[i]
                value = 0.0 if total == 0.0 else raw / total * 100.0
            else:
                value = raw
            if value >= 0:
                bottom_v = positive[i]
                top_v = bottom_v + value
                positive[i] = top_v
            else:
                bottom_v = negative[i]
                top_v = bottom_v + value
                negative[i] = top_v
            y0 = ypix(bottom_v)
            y1 = ypix(top_v)
            y = min(y0, y1)
            h = abs(y0 - y1)
        else:
            left = cx_band - group_w / 2 + bar_w * (kc if fr.spec.grouping else 0)
            yv = ypix(raw)
            y = min(baseline, yv)
            h = abs(baseline - yv)
        xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
        cx = left + bar_w / 2
        common = (
            f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
            f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(raw))}" '
            f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
        )
        p.append(
            f'<rect {common} cx="{cx:.1f}" cy="{y:.1f}" x="{left:.1f}" y="{y:.1f}" '
            f'width="{bar_w:.1f}" height="{h:.1f}" fill="{st.fill}"/>'
        )
    p.append("</g>")


def _emit_line_series(fr, p, si, s):
    st = fr.styles[si]
    ypix = _ypix_for(fr, s)
    theme = fr.theme
    pts = [(fr.xpix(i), ypix(v)) for i, v in enumerate(s.data)]
    d = _spline_d(pts) if s.curve == "monotone" else _path_d(pts, s.step)
    lw = s.line_width if s.line_width is not None else 2
    line_dash = dash_array(s.dash_style)
    line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
    p.append(f'<g class="sc-series" data-series="{si}">')
    if st.area_fill is not None and pts:
        base = ypix(0.0)
        area_d = f"{d} L{pts[-1][0]:.1f} {base:.1f} L{pts[0][0]:.1f} {base:.1f} Z"
        p.append(
            f'<path class="sc-series-area" data-series="{si}" d="{area_d}" '
            f'fill="{st.area_fill}"{st.area_op} stroke="none"/>'
        )
    p.append(
        f'<path class="sc-series-line" data-series="{si}" d="{d}" fill="none" '
        f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}" stroke-linejoin="round" '
        f'stroke-linecap="round"{line_dash_attr}/>'
    )
    mk = s.marker or Marker()
    if mk.enabled:
        radius = mk.radius
        radius_hover = radius + 2.5
        for i, (x, y) in enumerate(pts):
            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
            common = (
                f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" '
                f'data-color="{st.solid}" data-r="{fmt_num(radius)}" '
                f'data-r-hover="{fmt_num(radius_hover)}"'
            )
            p.append(_marker(mk.symbol, x, y, radius, common, st.solid, theme.marker_halo))
    p.append("</g>")
