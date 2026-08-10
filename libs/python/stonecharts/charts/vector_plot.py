"""Vector-plot chart renderer: ChartSpec -> SVG string.

Arrow glyphs on a numeric x/y plane. Each datum carries (x, y, direction, length).
Rides the shared cartesian frame with x_scale="linear" and include_zero=False.
"""

from __future__ import annotations

import math

from ..spec import Datum
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


def render_svg(spec) -> str:
    for s in spec.series:
        if not s.data_points:
            x_arr = s.x or [float(i) for i in range(len(s.data))]
            s.data_points = [Datum(x=x_arr[i], y=s.data[i]) for i in range(min(len(x_arr), len(s.data)))]
    return render_cartesian(spec, "Vector plot", "linear", _vector_marks, include_zero=False)


HEAD_LEN = 6.0
HEAD_ANGLE = 25.0


def _vector_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    K = len(fr.spec.series)

    vector_length = fr.spec.vector_length if fr.spec.vector_length else 20.0
    rotation_origin = fr.spec.rotation_origin if fr.spec.rotation_origin else "center"

    lmax = 0.0
    for s in fr.spec.series:
        ln = s.length or []
        for v in ln:
            if v > lmax:
                lmax = v

    def arrow_px(length: float) -> float:
        if lmax <= 0.0:
            return 0.0
        return vector_length * (length / lmax)

    ha = HEAD_ANGLE * math.pi / 180.0
    ca = math.cos(ha)
    sa = math.sin(ha)

    for si in range(K):
        s = fr.spec.series[si]
        st = fr.styles[si]

        x_arr = s.x or [float(i) for i in range(len(s.data))]
        y_arr = s.data
        dir_arr = s.direction or [0.0] * len(s.data)
        len_arr = s.length or [0.0] * len(s.data)

        n_pts = min(len(x_arr), len(y_arr), len(dir_arr), len(len_arr))

        stroke = st.fill
        line_width = s.line_width if s.line_width is not None else 1.5

        p.append(f'<g class="sc-series" data-series="{si}">')

        for i in range(n_pts):
            xv = x_arr[i]
            yv = y_arr[i]
            dv = dir_arr[i]
            lv = len_arr[i]

            cx = fr.xpix(xv)
            cy = fr.ypix(yv)

            rad = dv * math.pi / 180.0
            ux = math.sin(rad)
            uy = -math.cos(rad)

            big_l = arrow_px(lv)
            half = big_l / 2.0

            if rotation_origin == "start":
                ax, ay = cx, cy
            elif rotation_origin == "end":
                ax, ay = cx - ux * big_l, cy - uy * big_l
            else:
                ax, ay = cx - ux * half, cy - uy * half

            tailx, taily = ax, ay
            headx, heady = ax + ux * big_l, ay + uy * big_l

            lbx = headx + HEAD_LEN * ((-ux) * ca - (-uy) * sa)
            lby = heady + HEAD_LEN * ((-ux) * sa + (-uy) * ca)
            rbx = headx + HEAD_LEN * ((-ux) * ca + (-uy) * sa)
            rby = heady + HEAD_LEN * (ux * sa + (-uy) * ca)

            d = (
                f"M{tailx:.1f} {taily:.1f} L{headx:.1f} {heady:.1f} "
                f"M{lbx:.1f} {lby:.1f} L{headx:.1f} {heady:.1f} L{rbx:.1f} {rby:.1f}"
            )

            xlabel = esc(fmt_num(xv))
            ylabel = esc(fmt_num(yv))

            p.append(
                f'<path class="sc-vector sc-point" data-series="{si}" '
                f'data-series-name="{esc(s.name)}" '
                f'data-x="{xlabel}" data-y="{ylabel}" '
                f'data-direction="{esc(fmt_num(dv))}" data-length="{esc(fmt_num(lv))}" '
                f'data-color="{st.solid}" data-r="{fmt_num(line_width)}" data-r-hover="{fmt_num(line_width)}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}" '
                f'd="{d}" fill="none" stroke="{stroke}" stroke-width="{fmt_num(line_width)}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>'
            )

        p.append("</g>")
