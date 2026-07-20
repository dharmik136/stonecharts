"""Range area chart renderer: ChartSpec -> SVG string.

This chart draws a filled band between low and high boundaries on the shared
cartesian frame. The shipped examples keep the current flat payload shape:
series.data carries highs and series.low carries lows.
"""
from __future__ import annotations

from typing import List

from ..spec import ChartSpec, Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker as _line_marker, _path_d


def _range_points(fr: CartesianFrame, highs: List[float], lows: List[float]):
    hi_pts = [(fr.xpix(i), fr.ypix(v)) for i, v in enumerate(highs)]
    lo_pts = [(fr.xpix(i), fr.ypix(v)) for i, v in enumerate(lows)]
    return hi_pts, lo_pts


def _band_d(hi_pts, lo_pts) -> str:
    top = _path_d(hi_pts, None)
    tail = "".join(f" L{x:.1f} {y:.1f}" for x, y in reversed(lo_pts))
    return top + tail + " Z"


def render_svg(spec) -> str:
    return render_cartesian(spec, 'Range area', 'point', _arearange_marks)


def _arearange_marks(fr: CartesianFrame, p: List[str]) -> None:
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        highs = list(s.data)
        lows = list(s.low or s.data)
        if not highs:
            p.append(f'<g class="sc-series" data-series="{si}"></g>')
            continue
        count = min(len(highs), len(lows))
        if count == 0:
            p.append(f'<g class="sc-series" data-series="{si}"></g>')
            continue
        highs = highs[:count]
        lows = lows[:count]
        hi_pts, lo_pts = _range_points(fr, highs, lows)
        band_d = _band_d(hi_pts, lo_pts)
        fill_opacity = s.fill_opacity if s.fill_opacity > 0 else 0.5
        p.append(f'<g class="sc-series" data-series="{si}">')
        p.append(
            f'<path class="sc-series-range sc-band" data-series="{si}" d="{band_d}" '
            f'fill="{st.fill}" fill-opacity="{fmt_num(fill_opacity)}" stroke="none"/>'
        )
        mk = s.marker or Marker()
        if mk.enabled:
            radius = mk.radius
            radius_hover = radius + 2.5
            for i, (x, y) in enumerate(hi_pts):
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-low="{esc(fmt_num(lows[i]))}" '
                    f'data-high="{esc(fmt_num(highs[i]))}" data-y="{esc(fmt_num(lows[i]))}–{esc(fmt_num(highs[i]))}" '
                    f'data-color="{st.solid}" data-r="{fmt_num(radius)}" data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(_line_marker(mk.symbol, x, y, radius, common, st.solid, fr.theme.marker_halo))
        p.append('</g>')
