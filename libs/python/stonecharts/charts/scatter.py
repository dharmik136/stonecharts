"""Scatter chart renderer: ChartSpec -> SVG string.

Scatter rides the shared cartesian frame with free y-domain and point-based x
placement. The shipped examples keep the current number[] payload shape: a bare
number means the y-value at sample index i. When series.regression is true the
renderer draws an OLS trend line over that point cloud.
"""
from __future__ import annotations

import math
from typing import List, Tuple

from ..spec import ChartSpec, Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker as _line_marker, _path_d


def _points(values: List[float]) -> List[Tuple[int, float]]:
    return [(i, v) for i, v in enumerate(values)]


def _ols_endpoints(values: List[float]) -> Tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return values[0], values[0]
    xs = list(range(n))
    sx = float(sum(xs))
    sy = float(sum(values))
    sxx = float(sum(x * x for x in xs))
    sxy = float(sum(x * y for x, y in zip(xs, values)))
    denom = float(n) * sxx - sx * sx
    if denom == 0.0:
        mean = sy / float(n)
        return mean, mean
    slope = (float(n) * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / float(n)
    return intercept, slope * float(n - 1) + intercept


def render_svg(spec) -> str:
    return render_cartesian(spec, 'Scatter', 'point', _scatter_marks, include_zero=False)


def _scatter_marks(fr: CartesianFrame, p: List[str]) -> None:
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        pts = [(fr.xpix(i), fr.ypix(v)) for i, v in enumerate(s.data)]
        p.append(f'<g class="sc-series" data-series="{si}">')
        if getattr(s, 'regression', False) and len(s.data) >= 1:
            y0, y1 = _ols_endpoints(s.data)
            reg_pts = [(fr.xpix(0), fr.ypix(y0)), (fr.xpix(len(s.data) - 1), fr.ypix(y1))]
            d = _path_d(reg_pts, None)
            p.append(
                f'<path class="sc-series-line sc-trend" data-series="{si}" d="{d}" '
                f'fill="none" stroke="{st.stroke}" stroke-width="{fmt_num(s.line_width or 2)}" '
                f'stroke-linejoin="round" stroke-linecap="round"/>'
            )
        mk = s.marker or Marker()
        if mk.enabled:
            radius = mk.radius
            radius_hover = radius + 2.5
            opacity = s.fill_opacity if s.fill_opacity > 0 else 1.0
            for i, (x, y) in enumerate(pts):
                common = (
                    f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(fmt_num(float(i)))}" data-y="{esc(fmt_num(s.data[i]))}" '
                    f'data-color="{st.solid}" data-r="{fmt_num(radius)}" data-r-hover="{fmt_num(radius_hover)}" '
                    f'fill-opacity="{fmt_num(opacity)}"'
                )
                p.append(_line_marker(mk.symbol, x, y, radius, common, st.solid, fr.theme.marker_halo))
        p.append('</g>')
