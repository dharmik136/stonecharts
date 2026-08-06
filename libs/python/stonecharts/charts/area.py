"""Area chart renderer: ChartSpec -> SVG string.

Shared cartesian chrome comes from _cartesian.py. This module draws the area
fill, the top-edge line, and markers for each series.
"""

from __future__ import annotations

from ..spec import Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, dash_array, render_cartesian
from .line import _marker, _path_d, _spline_d


def render_svg(spec) -> str:
    return render_cartesian(spec, "Area", "point", _area_marks)


def _top_path(pts, step, curve) -> str:
    return _spline_d(pts) if curve == "monotone" else _path_d(pts, step)


def _area_path(top_pts, bottom_pts, step, curve) -> str:
    top_d = _top_path(top_pts, step, curve)
    bottom_d = _top_path(list(reversed(bottom_pts)), step, curve)
    if bottom_d.startswith("M"):
        bottom_d = "L" + bottom_d[1:]
    return f"{top_d} {bottom_d} Z"


def _series_fill(st) -> str:
    if st.area_fill is not None:
        return st.area_fill
    if st.stroke.startswith("url("):
        return st.stroke
    return st.solid


def _area_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    stacked = fr.stacking in ("normal", "percent")
    totals = [0.0] * fr.n
    if fr.stacking == "percent":
        for s in fr.spec.series:
            for i, v in enumerate(s.data):
                if i < fr.n:
                    totals[i] += v

    running = [0.0] * fr.n
    theme = fr.theme
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        raw_vals = [float(v) for v in s.data[: fr.n]]
        top_pts = []
        p.append(f'<g class="sc-series" data-series="{si}">')

        if stacked:
            vals = []
            for i, raw in enumerate(raw_vals):
                if fr.stacking == "percent":
                    total = totals[i]
                    vals.append(0.0 if total == 0.0 else raw / total * 100.0)
                else:
                    vals.append(raw)
            bottom_vals = running[: len(vals)]
            top_vals = [bottom_vals[i] + vals[i] for i in range(len(vals))]
            running[: len(vals)] = top_vals
            top_pts = [(fr.xpix(i), fr.ypix(top_vals[i])) for i in range(len(vals))]
            bottom_pts = [(fr.xpix(i), fr.ypix(bottom_vals[i])) for i in range(len(vals))]
            if top_pts:
                fill_op = st.area_op if st.area_op else ' fill-opacity="0.75"'
                p.append(
                    f'<path class="sc-series-area" data-series="{si}" d="{_area_path(top_pts, bottom_pts, s.step, s.curve)}" '
                    f'fill="{_series_fill(st)}"{fill_op} stroke="none"/>'
                )
                line_dash = dash_array(s.dash_style)
                line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
                p.append(
                    f'<path class="sc-series-line" data-series="{si}" d="{_top_path(top_pts, s.step, s.curve)}" fill="none" '
                    f'stroke="{st.stroke}" stroke-width="{fmt_num(s.line_width if s.line_width is not None else 2)}" '
                    f'stroke-linejoin="round" stroke-linecap="round"{line_dash_attr}/>'
                )
        else:
            top_pts = [(fr.xpix(i), fr.ypix(raw_vals[i])) for i in range(len(raw_vals))]
            if top_pts:
                base = fr.ypix(0.0)
                area_d = f"{_top_path(top_pts, s.step, s.curve)} L{top_pts[-1][0]:.1f} {base:.1f} L{top_pts[0][0]:.1f} {base:.1f} Z"
                fill_op = st.area_op if st.area_op else ' fill-opacity="0.75"'
                p.append(
                    f'<path class="sc-series-area" data-series="{si}" d="{area_d}" '
                    f'fill="{_series_fill(st)}"{fill_op} stroke="none"/>'
                )
                line_dash = dash_array(s.dash_style)
                line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
                p.append(
                    f'<path class="sc-series-line" data-series="{si}" d="{_top_path(top_pts, s.step, s.curve)}" fill="none" '
                    f'stroke="{st.stroke}" stroke-width="{fmt_num(s.line_width if s.line_width is not None else 2)}" '
                    f'stroke-linejoin="round" stroke-linecap="round"{line_dash_attr}/>'
                )

        mk = s.marker or Marker()
        if mk.enabled and top_pts:
            radius = mk.radius
            radius_hover = radius + 2.5
            for i, (x, y) in enumerate(top_pts):
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(raw_vals[i]))}" '
                    f'data-color="{st.solid}" data-r="{fmt_num(radius)}" '
                    f'data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(_marker(mk.symbol, x, y, radius, common, st.solid, theme.marker_halo))
        p.append("</g>")
