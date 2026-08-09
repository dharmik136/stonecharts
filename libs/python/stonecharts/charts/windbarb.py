"""Windbarb chart renderer: ChartSpec -> SVG string.

Wind-barb glyphs on a fixed lane, each encoding speed (feathers) and direction
(SVG rotate transform — no trig). Uses render_cartesian with x_scale="band".
"""

from __future__ import annotations

import math

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


def render_svg(spec: ChartSpec) -> str:
    return render_cartesian(spec, "Windbarb", "band", _windbarb_marks)


STAFF_W = 1.5
FEATHER_DX = 7.0
FEATHER_DY = 3.0
HALF_DX = 3.5
HALF_DY = 1.5
STEP = 3.0
R_CALM = 3.5


def _windbarb_marks(fr: CartesianFrame, p: list[str]) -> None:
    spec = fr.spec

    barb_len = spec.barb_length
    calm_thr = spec.calm_threshold
    hemi = spec.hemisphere
    y_off = spec.y_offset

    dx = FEATHER_DX if hemi != "S" else -FEATHER_DX
    hdx = HALF_DX if hemi != "S" else -HALF_DX

    lane_y = fr.plot_y + fr.plot_h / 2 + y_off

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        color = st.stroke
        solid = st.solid

        p.append(f'<g class="sc-series" data-series="{si}">')
        for k in range(len(s.data)):
            speed = s.data[k]
            direction = s.direction[k] if s.direction and k < len(s.direction) else 0.0
            xc = fr.xpix(k)

            cat = ""
            if fr.spec.x_axis.categories and k < len(fr.spec.x_axis.categories):
                cat = fr.spec.x_axis.categories[k]
            else:
                cat = str(k)

            p.append(
                f'<g class="sc-barb sc-point" data-series="{si}" '
                f'data-series-name="{esc(s.name)}" data-x="{esc(cat)}" '
                f'data-y="{esc(fmt_num(speed))}" '
                f'data-speed="{esc(fmt_num(speed))}" data-direction="{esc(fmt_num(direction))}" '
                f'data-color="{solid}" data-r="{fmt_num(R_CALM)}" data-r-hover="{fmt_num(R_CALM + 3)}" '
                f'cx="{xc:.1f}" cy="{lane_y:.1f}" '
                f'transform="rotate({fmt_num(direction)} {xc:.1f} {lane_y:.1f})">'
            )

            if speed < calm_thr:
                p.append(
                    f'<circle class="sc-calm" cx="{xc:.1f}" cy="{lane_y:.1f}" '
                    f'r="{fmt_num(R_CALM)}" fill="none" stroke="{color}" stroke-width="{fmt_num(STAFF_W)}"/>'
                )
            else:
                tip_y = lane_y - barb_len
                p.append(
                    f'<line class="sc-staff" x1="{xc:.1f}" y1="{lane_y:.1f}" '
                    f'x2="{xc:.1f}" y2="{tip_y:.1f}" '
                    f'stroke="{color}" stroke-width="{fmt_num(STAFF_W)}"/>'
                )

                s5 = int(math.floor(speed / 5 + 0.5)) * 5
                n_flags = s5 // 50
                n_full = (s5 % 50) // 10
                n_half = (s5 % 10) // 5

                fi = 0
                for _ in range(n_flags):
                    y0 = tip_y + fi * STEP
                    y_base = tip_y + (fi + 2) * STEP
                    p.append(
                        f'<polygon class="sc-flag" '
                        f'points="{xc:.1f},{y0:.1f} {xc + dx:.1f},{y0 - FEATHER_DY:.1f} {xc:.1f},{y_base:.1f}" '
                        f'fill="{color}" stroke="{color}" stroke-width="{fmt_num(STAFF_W)}"/>'
                    )
                    fi += 2
                for _ in range(n_full):
                    y = tip_y + fi * STEP
                    p.append(
                        f'<line class="sc-feather" x1="{xc:.1f}" y1="{y:.1f}" '
                        f'x2="{xc + dx:.1f}" y2="{y - FEATHER_DY:.1f}" '
                        f'stroke="{color}" stroke-width="{fmt_num(STAFF_W)}"/>'
                    )
                    fi += 1
                if n_half > 0:
                    y = tip_y + fi * STEP
                    p.append(
                        f'<line class="sc-feather-half" x1="{xc:.1f}" y1="{y:.1f}" '
                        f'x2="{xc + hdx:.1f}" y2="{y - HALF_DY:.1f}" '
                        f'stroke="{color}" stroke-width="{fmt_num(STAFF_W)}"/>'
                    )

            p.append("</g>")
        p.append("</g>")
