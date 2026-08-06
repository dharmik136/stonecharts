"""Scatter chart renderer: ChartSpec -> SVG string.

Unconnected point marks at (x, y) on a free numeric x-axis and a free numeric
y-axis (§3.3 Rank 3 of docs/roadmap/chart-families.md). Rides the shared
cartesian frame with x_scale="linear" and include_zero=False on both axes;
this module supplies only the marks callback, reusing line's marker builder
(circle/square/triangle/diamond) exactly as area.py already does.
"""

from __future__ import annotations

from ..spec import Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker


def render_svg(spec) -> str:
    return render_cartesian(spec, "Scatter", "linear", _scatter_marks, include_zero=False)


def _scatter_marks(fr: CartesianFrame, p: list) -> None:
    theme = fr.theme
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        # Point fill-opacity (NN#2 — never emit an unfilled point): the shared
        # Series.fill_opacity default (0.0) is indistinguishable from an
        # explicit 0, so scatter treats 0.0 as "unset -> fully opaque" and
        # only a truthy (>0) value dims the fill.
        op = s.fill_opacity if s.fill_opacity > 0 else 1.0
        p.append(f'<g class="sc-series" data-series="{si}">')
        mk = s.marker or Marker()
        if mk.enabled:
            radius = mk.radius
            radius_hover = radius + 2.5
            for d in s.data_points or []:
                x, y = fr.xpix(d.x), fr.ypix(d.y)
                common = (
                    f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(fmt_num(d.x))}" data-y="{esc(fmt_num(d.y))}" '
                    f'data-color="{st.solid}" data-r="{fmt_num(radius)}" '
                    f'data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(_marker(mk.symbol, x, y, radius, common, st.fill, theme.marker_halo, op))
        p.append("</g>")
