"""Bar chart renderer: ChartSpec -> SVG string.

Bar is column transposed: the value axis runs along x, the category (band)
axis runs along y. Shared Cartesian chrome (including the orientation-aware
axis/gridline chrome) comes from _cartesian.py; this module draws only bar
marks: one baseline-anchored <rect> per category/series segment, widened
along x instead of column's height along y. See charts/bar/design.md for the
full geometry contract.
"""
from __future__ import annotations

from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


PAD = 0.2


def render_svg(spec) -> str:
    return render_cartesian(spec, "Bar", "band", _bar_marks, orientation="horizontal")


def _bar_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    band_height = fr.band_height()
    group_h = band_height * (1 - PAD)
    stacked = fr.stacking in ("normal", "percent")
    k_slots = 1 if stacked or not fr.spec.grouping else max(len(fr.spec.series), 1)
    bar_h = group_h / k_slots
    baseline = fr.value_zero()

    totals = [0.0] * fr.n
    if stacked:
        for s in fr.spec.series:
            for i, v in enumerate(s.data):
                if i < fr.n:
                    totals[i] += v

    positive = [0.0] * fr.n
    negative = [0.0] * fr.n
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        p.append(f'<g class="sc-series" data-series="{si}">')
        for i, raw in enumerate(s.data):
            if i >= fr.n:
                break
            cy_band = fr.band_center(i)
            if stacked:
                top = cy_band - group_h / 2
                if fr.stacking == "percent":
                    total = totals[i]
                    value = 0.0 if total == 0.0 else raw / total * 100.0
                else:
                    value = raw
                if value >= 0:
                    left_v = positive[i]
                    right_v = left_v + value
                    positive[i] = right_v
                else:
                    left_v = negative[i]
                    right_v = left_v + value
                    negative[i] = right_v
                x0 = fr.value_pix(left_v)
                x1 = fr.value_pix(right_v)
                x = min(x0, x1)
                w = abs(x0 - x1)
                tip = x1
            else:
                top = cy_band - group_h / 2 + bar_h * (si if fr.spec.grouping else 0)
                xv = fr.value_pix(raw)
                x = min(baseline, xv)
                w = abs(baseline - xv)
                tip = xv
            ylabel = fr.cats[i] if i < len(fr.cats) else str(i)
            cy = top + bar_h / 2
            common = (
                f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(ylabel)}" data-y="{esc(fmt_num(raw))}" '
                f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
            )
            p.append(
                f'<rect {common} cx="{tip:.1f}" cy="{cy:.1f}" x="{x:.1f}" y="{top:.1f}" '
                f'width="{w:.1f}" height="{bar_h:.1f}" fill="{st.fill}"/>'
            )
        p.append("</g>")
