"""Streamgraph chart renderer: ChartSpec -> SVG string.

Stacked, filled area ribbons over a shared x-axis displaced off a floating
baseline (wiggle or silhouette). Rides the area renderer's path builder and
the shared cartesian frame with include_zero=False.
"""

from __future__ import annotations

from ..spec import Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker, _path_d, _spline_d


def render_svg(spec) -> str:
    return render_cartesian(spec, "Streamgraph", "point", _streamgraph_marks,
                            include_zero=False)


def _streamgraph_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    K = len(fr.spec.series)
    N = fr.n

    baseline = fr.sg_baseline
    cum_bottom = fr.sg_cum_bottom
    cum_top = fr.sg_cum_top

    all_vals: list[list[float]] = []
    for s in fr.spec.series:
        all_vals.append([float(v) for v in s.data[:N]])

    theme = fr.theme
    for si in range(K):
        s = fr.spec.series[si]
        st = fr.styles[si]
        raw_vals = all_vals[si]

        top_pts = []
        bottom_pts = []
        for i in range(len(raw_vals)):
            x = fr.xpix(i)
            top_y = fr.ypix(baseline[i] + cum_top[si][i])
            bot_y = fr.ypix(baseline[i] + cum_bottom[si][i])
            top_pts.append((x, top_y))
            bottom_pts.append((x, bot_y))

        p.append(f'<g class="sc-series" data-series="{si}">')

        if top_pts:
            top_d = _spline_d(top_pts) if s.curve == "monotone" else _path_d(top_pts, None)
            bottom_rev = list(reversed(bottom_pts))
            bottom_d = _spline_d(bottom_rev) if s.curve == "monotone" else _path_d(bottom_rev, None)
            if bottom_d.startswith("M"):
                bottom_d = "L" + bottom_d[1:]
            ribbon_d = f"{top_d} {bottom_d} Z"

            fill = st.fill
            fill_op = st.area_op if st.area_op else ""
            p.append(
                f'<path class="sc-series-area" data-series="{si}" d="{ribbon_d}" '
                f'fill="{fill}"{fill_op} stroke="none"/>'
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
