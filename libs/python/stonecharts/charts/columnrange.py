"""Column range chart renderer: ChartSpec -> SVG string.

Floating low-to-high bars over a shared categorical x-axis and numeric y-axis.
Shared Cartesian chrome comes from _cartesian.py; this module draws only the
floating bar marks: one <rect> per (category, series) floating between its low
and high values. See charts/columnrange/design.md for the full geometry contract.
"""

from __future__ import annotations

import copy

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian

PAD = 0.2


def render_svg(spec: ChartSpec) -> str:
    mod = copy.copy(spec)
    mod.y_axis = copy.copy(spec.y_axis)

    # Pre-set y_axis min/max from data (lows) and high (highs).
    all_lows: list[float] = []
    all_highs: list[float] = []
    for s in mod.series:
        all_lows.extend(s.data)
        high = getattr(s, "high", None) or []
        all_highs.extend(high)
    if mod.y_axis.min is None and all_lows:
        mod.y_axis.min = min(all_lows)
    if mod.y_axis.max is None and all_highs:
        mod.y_axis.max = max(all_highs)

    orientation = getattr(mod, "orientation", "vertical")
    return render_cartesian(
        mod,
        "Column range",
        "band",
        _columnrange_marks,
        include_zero=False,
        orientation=orientation,
    )


def _columnrange_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    horiz = fr.orientation == "horizontal"

    band = fr.band_height() if horiz else fr.band_width()
    group_w = band * (1 - PAD)
    k = 1 if not fr.spec.grouping else max(len(fr.spec.series), 1)
    bar_w = group_w / k

    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        high_arr = getattr(s, "high", None) or []
        p.append(f'<g class="sc-series" data-series="{si}">')

        for i in range(min(len(s.data), fr.n)):
            if i >= len(high_arr):
                continue  # missing high[i] -> gap

            lo_val = s.data[i]
            hi_val = high_arr[i]

            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)

            if horiz:
                cy_band = fr.band_center(i)
                top = cy_band - group_w / 2 + bar_w * (si if fr.spec.grouping else 0)
                cy = top + bar_w / 2
                x_lo = fr.value_pix(min(lo_val, hi_val))
                x_hi = fr.value_pix(max(lo_val, hi_val))
                x = min(x_lo, x_hi)
                w = max(abs(x_hi - x_lo), 1.0)
                cx = fr.value_pix(max(lo_val, hi_val))
                p.append(
                    f'<rect class="sc-bar sc-point" data-series="{si}"'
                    f' data-series-name="{esc(s.name)}" data-x="{esc(xlabel)}"'
                    f' data-y="{esc(fmt_num(hi_val))}"'
                    f' data-low="{esc(fmt_num(lo_val))}" data-high="{esc(fmt_num(hi_val))}"'
                    f' data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
                    f' cx="{cx:.1f}" cy="{cy:.1f}"'
                    f' x="{x:.1f}" y="{top:.1f}"'
                    f' width="{w:.1f}" height="{bar_w:.1f}"'
                    f' fill="{st.fill}"/>'
                )
            else:
                cx_band = fr.xpix(i)
                left = cx_band - group_w / 2 + bar_w * (si if fr.spec.grouping else 0)
                cx = left + bar_w / 2
                y_top = fr.ypix(max(lo_val, hi_val))
                y_bot = fr.ypix(min(lo_val, hi_val))
                bar_h = max(abs(y_bot - y_top), 1.0)
                p.append(
                    f'<rect class="sc-bar sc-point" data-series="{si}"'
                    f' data-series-name="{esc(s.name)}" data-x="{esc(xlabel)}"'
                    f' data-y="{esc(fmt_num(hi_val))}"'
                    f' data-low="{esc(fmt_num(lo_val))}" data-high="{esc(fmt_num(hi_val))}"'
                    f' data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
                    f' cx="{cx:.1f}" cy="{y_top:.1f}"'
                    f' x="{left:.1f}" y="{y_top:.1f}"'
                    f' width="{bar_w:.1f}" height="{bar_h:.1f}"'
                    f' fill="{st.fill}"/>'
                )

        p.append("</g>")
