"""Column chart renderer: ChartSpec -> SVG string.

Shared Cartesian chrome comes from _cartesian.py. This module draws only column
marks: one <rect> per category/series segment.
"""
from __future__ import annotations

from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


PAD = 0.2


def render_svg(spec) -> str:
    return render_cartesian(spec, "Column", "band", _column_marks)


def _column_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    band_width = fr.band_width()
    group_w = band_width * (1 - PAD)
    stacked = fr.stacking in ("normal", "percent")
    k_slots = 1 if stacked or not fr.spec.grouping else max(len(fr.spec.series), 1)
    bar_w = group_w / k_slots
    baseline = fr.ypix(0.0)

    totals = [0.0] * fr.n
    if stacked:
        for s in fr.spec.series:
            for i, v in enumerate(s.data):
                if i < fr.n:
                    totals[i] += v

    cumulative = [0.0] * fr.n
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        p.append(f'<g class="sc-series" data-series="{si}">')
        for i, raw in enumerate(s.data):
            if i >= fr.n:
                break
            cx_band = fr.xpix(i)
            if stacked:
                left = cx_band - group_w / 2
                if fr.stacking == "percent":
                    total = totals[i]
                    value = 0.0 if total == 0.0 else raw / total * 100.0
                else:
                    value = raw
                bottom_v = cumulative[i]
                top_v = bottom_v + value
                cumulative[i] = top_v
                y0 = fr.ypix(bottom_v)
                y1 = fr.ypix(top_v)
                y = min(y0, y1)
                h = abs(y0 - y1)
            else:
                left = cx_band - group_w / 2 + bar_w * (si if fr.spec.grouping else 0)
                yv = fr.ypix(raw)
                y = min(baseline, yv)
                h = abs(baseline - yv)
            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
            cx = left + bar_w / 2
            common = (
                f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(raw))}" '
                f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
            )
            p.append(
                f'<rect {common} cx="{cx:.1f}" cy="{y:.1f}" x="{left:.1f}" y="{y:.1f}" '
                f'width="{bar_w:.1f}" height="{h:.1f}" fill="{st.fill}"/>'
            )
        p.append("</g>")
