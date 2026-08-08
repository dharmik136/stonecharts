"""Range area chart renderer: ChartSpec -> SVG string.

A filled band between two data boundaries (high and low) over a shared
categorical x-axis. Shared Cartesian chrome comes from _cartesian.py.
"""

from __future__ import annotations

import copy

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, dash_array, render_cartesian
from .line import _path_d, _spline_d


def render_svg(spec: ChartSpec) -> str:
    mod = copy.copy(spec)
    mod.y_axis = copy.copy(spec.y_axis)

    # Pre-set y-axis domain over BOTH boundaries (high=data, low=low)
    all_vals: list[float] = []
    for s in mod.series:
        all_vals.extend(s.data)
        low = getattr(s, "low", None)
        if low is not None:
            all_vals.extend(low)
    if mod.y_axis.min is None and all_vals:
        mod.y_axis.min = min(all_vals)
    if mod.y_axis.max is None and all_vals:
        mod.y_axis.max = max(all_vals)

    return render_cartesian(mod, "Range area", "point", _arearange_marks)


def _arearange_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    use_spline = getattr(spec, "subtype", None) == "areasplinerange"

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        low_arr = getattr(s, "low", None) or []
        curve = getattr(s, "curve", None)
        spline = use_spline or curve == "monotone"

        n = min(len(s.data), fr.n)

        # Build points for high (data) and low boundaries
        hi_pts = [(fr.xpix(i), fr.ypix(s.data[i])) for i in range(n)]
        lo_pts = [(fr.xpix(i), fr.ypix(low_arr[i] if i < len(low_arr) else s.data[i])) for i in range(n)]

        if not hi_pts:
            continue

        p.append(f'<g class="sc-series" data-series="{si}">')

        top_d = _spline_d(hi_pts) if spline else _path_d(hi_pts, None)

        # Low boundary reversed
        lo_reversed = list(reversed(lo_pts))
        bottom_parts = "".join(f" L{x:.1f} {y:.1f}" for x, y in lo_reversed)
        band_d = f"{top_d}{bottom_parts} Z"

        # Fill opacity
        fill_op_val = getattr(s, "fill_opacity", None)
        if not fill_op_val:
            fill_op_val = 0.5
        fill_op = f' fill-opacity="{fmt_num(fill_op_val)}"'

        p.append(
            f'<path class="sc-series-range sc-band" data-series="{si}"'
            f' d="{band_d}" fill="{st.fill}"{fill_op} stroke="none"/>'
        )

        # Optional bounding strokes
        line_w = getattr(s, "line_width", None)
        if line_w is not None and line_w > 0:
            stroke_dash = dash_array(getattr(s, "dash_style", None) or "")
            dash_attr = f' stroke-dasharray="{stroke_dash}"' if stroke_dash else ""
            hi_stroke_d = _spline_d(hi_pts) if spline else _path_d(hi_pts, None)
            p.append(
                f'<path class="sc-series-line sc-range-hi" data-series="{si}"'
                f' d="{hi_stroke_d}" fill="none" stroke="{st.stroke}"'
                f' stroke-width="{fmt_num(line_w)}" stroke-linejoin="round"'
                f' stroke-linecap="round"{dash_attr}/>'
            )
            lo_stroke_d = _spline_d(lo_pts) if spline else _path_d(lo_pts, None)
            p.append(
                f'<path class="sc-series-line sc-range-lo" data-series="{si}"'
                f' d="{lo_stroke_d}" fill="none" stroke="{st.stroke}"'
                f' stroke-width="{fmt_num(line_w)}" stroke-linejoin="round"'
                f' stroke-linecap="round"{dash_attr}/>'
            )

        # Points at high edge
        radius = 3.5
        radius_hover = radius + 2.5
        for i in range(n):
            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
            hi_val = s.data[i]
            lo_val = low_arr[i] if i < len(low_arr) else hi_val
            cx = fr.xpix(i)
            cy = fr.ypix(hi_val)
            p.append(
                f'<circle class="sc-point" data-series="{si}"'
                f' data-series-name="{esc(s.name)}"'
                f' data-x="{esc(xlabel)}"'
                f' data-low="{esc(fmt_num(lo_val))}"'
                f' data-high="{esc(fmt_num(hi_val))}"'
                f' data-y="{esc(fmt_num(lo_val) + "–" + fmt_num(hi_val))}"'  # noqa: RUF001
                f' data-color="{st.solid}"'
                f' data-r="{fmt_num(radius)}" data-r-hover="{fmt_num(radius_hover)}"'
                f' cx="{cx:.1f}" cy="{cy:.1f}" r="{fmt_num(radius)}"/>'
            )

        p.append("</g>")
