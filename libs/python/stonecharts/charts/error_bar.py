"""Error-bar chart renderer: ChartSpec -> SVG string.

Each datum is a vertical whisker (stem + two caps) with a center-value marker
on top.  Shared Cartesian chrome comes from _cartesian.py; this module draws
only the whisker marks.
"""

from __future__ import annotations

import copy

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker

PAD = 0.2
CAP = 6.0
WHISKER_SW = "1.5"


def render_svg(spec: ChartSpec) -> str:
    mod = copy.copy(spec)
    mod.y_axis = copy.copy(spec.y_axis)

    all_lows: list[float] = []
    all_highs: list[float] = []
    for s in mod.series:
        low = getattr(s, "low", None)
        high = getattr(s, "high", None)
        if low is not None:
            all_lows.extend(low)
        if high is not None:
            all_highs.extend(high)
        all_lows.extend(s.data)
        all_highs.extend(s.data)
    if mod.y_axis.min is None and all_lows:
        mod.y_axis.min = min(all_lows)
    if mod.y_axis.max is None and all_highs:
        mod.y_axis.max = max(all_highs)

    return render_cartesian(mod, "Error bar", "band", _error_bar_marks)


def _error_bar_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    band_width = fr.band_width()
    group_w = band_width * (1 - PAD)
    k = max(len(spec.series), 1)
    slot_w = group_w / k

    for si, s in enumerate(spec.series):
        color = fr.styles[si].solid
        halo = fr.theme.marker_halo

        marker_cfg = getattr(s, "marker", None) or {}
        if isinstance(marker_cfg, dict):
            m_enabled = marker_cfg.get("enabled", True)
            m_symbol = marker_cfg.get("symbol", "circle")
            m_radius = float(marker_cfg.get("radius", 3.5))
        else:
            m_enabled = getattr(marker_cfg, "enabled", True)
            m_symbol = getattr(marker_cfg, "symbol", "circle")
            m_radius = float(getattr(marker_cfg, "radius", 3.5))

        low_arr = getattr(s, "low", None) or []
        high_arr = getattr(s, "high", None) or []

        p.append(f'<g class="sc-series" data-series="{si}">')

        for i in range(min(len(s.data), fr.n)):
            y_val = s.data[i]
            xc = fr.xpix(i)
            cx = xc - group_w / 2 + slot_w * si + slot_w / 2

            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)

            has_lo = i < len(low_arr)
            has_hi = i < len(high_arr)

            if has_lo and has_hi:
                lo_val = low_arr[i]
                hi_val = high_arr[i]
                y_low = fr.ypix(lo_val)
                y_high = fr.ypix(hi_val)

                p.append(
                    f'<line class="sc-whisker sc-whisker-stem" data-series="{si}"'
                    f' x1="{cx:.1f}" y1="{y_low:.1f}"'
                    f' x2="{cx:.1f}" y2="{y_high:.1f}"'
                    f' stroke="{color}" stroke-width="{WHISKER_SW}"/>'
                )
                p.append(
                    f'<line class="sc-whisker sc-whisker-cap" data-series="{si}"'
                    f' x1="{cx - CAP:.1f}" y1="{y_low:.1f}"'
                    f' x2="{cx + CAP:.1f}" y2="{y_low:.1f}"'
                    f' stroke="{color}" stroke-width="{WHISKER_SW}"/>'
                )
                p.append(
                    f'<line class="sc-whisker sc-whisker-cap" data-series="{si}"'
                    f' x1="{cx - CAP:.1f}" y1="{y_high:.1f}"'
                    f' x2="{cx + CAP:.1f}" y2="{y_high:.1f}"'
                    f' stroke="{color}" stroke-width="{WHISKER_SW}"/>'
                )
            else:
                lo_val = y_val
                hi_val = y_val

            if m_enabled:
                y_ctr = fr.ypix(y_val)
                common = (
                    f'class="sc-point" data-series="{si}"'
                    f' data-series-name="{esc(s.name)}"'
                    f' data-x="{esc(xlabel)}"'
                    f' data-y="{esc(fmt_num(y_val))}"'
                    f' data-low="{esc(fmt_num(lo_val))}"'
                    f' data-high="{esc(fmt_num(hi_val))}"'
                    f' data-color="{color}"'
                    f' data-r="{fmt_num(m_radius)}"'
                    f' data-r-hover="{fmt_num(m_radius + 2.5)}"'
                )
                p.append(_marker(m_symbol, cx, y_ctr, m_radius, common, color, halo))

        p.append("</g>")
