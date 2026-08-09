"""Boxplot chart renderer: ChartSpec -> SVG string.

Box-and-whisker glyphs over a categorical axis. Each glyph shows a 5-number
summary (low, q1, median, q3, high) plus optional outlier circles. Shared
Cartesian chrome comes from _cartesian.py; this module draws only the boxplot
marks. See charts/boxplot/design.md for the full geometry contract.
"""

from __future__ import annotations

import copy

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian

PAD = 0.2
CAP = 0.5
BOX_OPACITY = 0.5
OUTLIER_R = 2.5
MIN_BOX = 1.0


def render_svg(spec: ChartSpec) -> str:
    mod = copy.copy(spec)
    mod.y_axis = copy.copy(spec.y_axis)

    all_vals: list[float] = []
    for s in mod.series:
        for bd in s.box_data or []:
            all_vals.append(bd.low)
            all_vals.append(bd.high)
            all_vals.extend(bd.outliers)

    if not all_vals:
        all_vals = [v for s in mod.series for v in s.data]

    if mod.y_axis.min is None and all_vals:
        mod.y_axis.min = min(all_vals)
    if mod.y_axis.max is None and all_vals:
        mod.y_axis.max = max(all_vals)

    orientation = mod.orientation or "vertical"
    return render_cartesian(mod, "Boxplot", "band", _boxplot_marks, include_zero=False, orientation=orientation)


def _boxplot_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    horiz = fr.orientation == "horizontal"
    K = max(len(spec.series), 1)

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        box_data = s.box_data or []
        p.append(f'<g class="sc-series" data-series="{si}">')

        for i in range(min(len(box_data), fr.n)):
            bd = box_data[i]
            cat = fr.cats[i] if i < len(fr.cats) else str(i)

            if horiz:
                band_sz = fr.band_height()
                group_sz = band_sz * (1 - PAD)
                bar_sz = group_sz / K
                band_c = fr.band_center(i)
                slot_start = band_c - group_sz / 2 + bar_sz * si
                mid = slot_start + bar_sz / 2
                cap_half = bar_sz * CAP / 2

                xq1 = fr.value_pix(bd.q1)
                xq3 = fr.value_pix(bd.q3)
                xmed = fr.value_pix(bd.median)
                xlow = fr.value_pix(bd.low)
                xhigh = fr.value_pix(bd.high)

                bx = min(xq1, xq3)
                bw = abs(xq3 - xq1)
                if bw < MIN_BOX:
                    bw = MIN_BOX

                cx_val = xmed
                cy_val = mid

                common = (
                    f'class="sc-box sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(cat)}" data-y="{esc(fmt_num(bd.median))}" '
                    f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
                )
                p.append(
                    f'<rect {common} cx="{cx_val:.1f}" cy="{cy_val:.1f}" '
                    f'x="{bx:.1f}" y="{slot_start:.1f}" width="{bw:.1f}" height="{bar_sz:.1f}" '
                    f'fill="{st.fill}" fill-opacity="{BOX_OPACITY}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-median" x1="{xmed:.1f}" y1="{slot_start:.1f}" '
                    f'x2="{xmed:.1f}" y2="{slot_start + bar_sz:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker" x1="{xq3:.1f}" y1="{mid:.1f}" '
                    f'x2="{xhigh:.1f}" y2="{mid:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker-cap" x1="{xhigh:.1f}" y1="{mid - cap_half:.1f}" '
                    f'x2="{xhigh:.1f}" y2="{mid + cap_half:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker" x1="{xq1:.1f}" y1="{mid:.1f}" '
                    f'x2="{xlow:.1f}" y2="{mid:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker-cap" x1="{xlow:.1f}" y1="{mid - cap_half:.1f}" '
                    f'x2="{xlow:.1f}" y2="{mid + cap_half:.1f}" stroke="{st.solid}"/>'
                )
                for o in bd.outliers:
                    ox = fr.value_pix(o)
                    p.append(
                        f'<circle class="sc-outlier" cx="{ox:.1f}" cy="{mid:.1f}" r="{OUTLIER_R}" fill="{st.solid}"/>'
                    )
            else:
                band_sz = fr.band_width()
                group_sz = band_sz * (1 - PAD)
                bar_sz = group_sz / K
                band_c = fr.xpix(i)
                slot_start = band_c - group_sz / 2 + bar_sz * si
                mid = slot_start + bar_sz / 2
                cap_half = bar_sz * CAP / 2

                yq3 = fr.ypix(bd.q3)
                yq1 = fr.ypix(bd.q1)
                ymed = fr.ypix(bd.median)
                yhigh = fr.ypix(bd.high)
                ylow = fr.ypix(bd.low)

                box_h = yq1 - yq3
                if box_h < MIN_BOX:
                    box_h = MIN_BOX

                cx_val = mid
                cy_val = ymed

                common = (
                    f'class="sc-box sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(cat)}" data-y="{esc(fmt_num(bd.median))}" '
                    f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
                )
                p.append(
                    f'<rect {common} cx="{cx_val:.1f}" cy="{cy_val:.1f}" '
                    f'x="{slot_start:.1f}" y="{yq3:.1f}" width="{bar_sz:.1f}" height="{box_h:.1f}" '
                    f'fill="{st.fill}" fill-opacity="{BOX_OPACITY}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-median" x1="{slot_start:.1f}" y1="{ymed:.1f}" '
                    f'x2="{slot_start + bar_sz:.1f}" y2="{ymed:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker" x1="{mid:.1f}" y1="{yq3:.1f}" '
                    f'x2="{mid:.1f}" y2="{yhigh:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker-cap" x1="{mid - cap_half:.1f}" y1="{yhigh:.1f}" '
                    f'x2="{mid + cap_half:.1f}" y2="{yhigh:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker" x1="{mid:.1f}" y1="{yq1:.1f}" '
                    f'x2="{mid:.1f}" y2="{ylow:.1f}" stroke="{st.solid}"/>'
                )
                p.append(
                    f'<line class="sc-whisker-cap" x1="{mid - cap_half:.1f}" y1="{ylow:.1f}" '
                    f'x2="{mid + cap_half:.1f}" y2="{ylow:.1f}" stroke="{st.solid}"/>'
                )
                for o in bd.outliers:
                    oy = fr.ypix(o)
                    p.append(
                        f'<circle class="sc-outlier" cx="{mid:.1f}" cy="{oy:.1f}" r="{OUTLIER_R}" fill="{st.solid}"/>'
                    )

        p.append("</g>")
