"""Candlestick chart renderer: ChartSpec -> SVG string.

Financial chart rendering for OHLC data. Supports subtypes: candlestick (default),
ohlc, hlc, heikin-ashi, and hollow. Shared Cartesian chrome comes from
_cartesian.py; this module draws only the candle/bar marks.
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

    # Pre-set y_axis min/max from OHLC highs/lows (only if not already explicit).
    all_lows: list[float] = []
    all_highs: list[float] = []
    for s in mod.series:
        for bar in getattr(s, "ohlc", None) or []:
            all_lows.append(bar["low"])
            all_highs.append(bar["high"])
    if mod.y_axis.min is None and all_lows:
        mod.y_axis.min = min(all_lows)
    if mod.y_axis.max is None and all_highs:
        mod.y_axis.max = max(all_highs)

    for s in mod.series:
        ohlc = getattr(s, "ohlc", None) or []
        if not s.data and ohlc:
            s.data = [0.0] * len(ohlc)

    return render_cartesian(mod, "Candlestick", "band", _candlestick_marks, include_zero=False)


def _candlestick_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    up_color = getattr(spec, "up_color", "#3f9b6a")
    down_color = getattr(spec, "down_color", "#d65f5f")
    subtype = getattr(spec, "subtype", "candlestick")

    band_width = fr.band_width()
    group_w = band_width * (1 - PAD)
    k = max(len(spec.series), 1)
    bar_w = group_w / k

    # Pre-compute Heikin-Ashi transformed values if needed.
    ha_data: dict[int, list[dict[str, float]]] = {}
    if subtype == "heikin-ashi":
        for si, s in enumerate(spec.series):
            ohlc = getattr(s, "ohlc", None) or []
            ha_bars: list[dict[str, float]] = []
            prev_ha_open = 0.0
            prev_ha_close = 0.0
            for j, raw in enumerate(ohlc):
                ha_close = (raw["open"] + raw["high"] + raw["low"] + raw["close"]) / 4
                ha_open = (raw["open"] + raw["close"]) / 2 if j == 0 else (prev_ha_open + prev_ha_close) / 2
                ha_high = max(raw["high"], ha_open, ha_close)
                ha_low = min(raw["low"], ha_open, ha_close)
                ha_bars.append(
                    {
                        "open": ha_open,
                        "high": ha_high,
                        "low": ha_low,
                        "close": ha_close,
                    }
                )
                prev_ha_open = ha_open
                prev_ha_close = ha_close
            ha_data[si] = ha_bars

    for si, s in enumerate(spec.series):
        ohlc = getattr(s, "ohlc", None) or []
        p.append(f'<g class="sc-series" data-series="{si}">')

        for i in range(min(len(ohlc), fr.n)):
            bar = ha_data[si][i] if subtype == "heikin-ashi" else ohlc[i]
            o, h, lo, c = bar["open"], bar["high"], bar["low"], bar["close"]

            xc = fr.xpix(i)
            left = xc - group_w / 2 + bar_w * si
            cx = left + bar_w / 2
            is_up = c >= o
            col = up_color if is_up else down_color
            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)

            p.append(
                f'<g class="sc-candle sc-point" data-series="{si}"'
                f' data-series-name="{esc(s.name)}"'
                f' data-x="{esc(xlabel)}" data-y="{esc(fmt_num(c))}"'
                f' data-open="{esc(fmt_num(o))}"'
                f' data-high="{esc(fmt_num(h))}"'
                f' data-low="{esc(fmt_num(lo))}"'
                f' data-close="{esc(fmt_num(c))}"'
                f' data-color="{col}" data-r="3.5" data-r-hover="6"'
                f' cx="{cx:.1f}" cy="{fr.ypix(c):.1f}">'
            )

            if subtype in ("candlestick", "heikin-ashi", "hollow"):
                # Wick line (high to low).
                p.append(
                    f'<line class="sc-wick"'
                    f' x1="{cx:.1f}" y1="{fr.ypix(h):.1f}"'
                    f' x2="{cx:.1f}" y2="{fr.ypix(lo):.1f}"'
                    f' stroke="{col}" stroke-width="1"/>'
                )
                # Body rect.
                y_top = fr.ypix(max(o, c))
                y_bot = fr.ypix(min(o, c))
                body_h = max(abs(y_bot - y_top), 1.0)
                fill = ("none" if is_up else col) if subtype == "hollow" else col
                p.append(
                    f'<rect class="sc-body"'
                    f' x="{left:.1f}" y="{y_top:.1f}"'
                    f' width="{bar_w:.1f}" height="{body_h:.1f}"'
                    f' fill="{fill}" stroke="{col}"/>'
                )
            elif subtype == "ohlc":
                # Vertical line.
                p.append(
                    f'<line class="sc-wick"'
                    f' x1="{cx:.1f}" y1="{fr.ypix(h):.1f}"'
                    f' x2="{cx:.1f}" y2="{fr.ypix(lo):.1f}"'
                    f' stroke="{col}" stroke-width="1"/>'
                )
                # Open tick.
                p.append(
                    f'<line class="sc-open-tick"'
                    f' x1="{left:.1f}" y1="{fr.ypix(o):.1f}"'
                    f' x2="{cx:.1f}" y2="{fr.ypix(o):.1f}"'
                    f' stroke="{col}" stroke-width="1"/>'
                )
                # Close tick.
                p.append(
                    f'<line class="sc-close-tick"'
                    f' x1="{cx:.1f}" y1="{fr.ypix(c):.1f}"'
                    f' x2="{(left + bar_w):.1f}" y2="{fr.ypix(c):.1f}"'
                    f' stroke="{col}" stroke-width="1"/>'
                )
            elif subtype == "hlc":
                # Vertical line.
                p.append(
                    f'<line class="sc-wick"'
                    f' x1="{cx:.1f}" y1="{fr.ypix(h):.1f}"'
                    f' x2="{cx:.1f}" y2="{fr.ypix(lo):.1f}"'
                    f' stroke="{col}" stroke-width="1"/>'
                )
                # Close tick only (no open tick).
                p.append(
                    f'<line class="sc-close-tick"'
                    f' x1="{cx:.1f}" y1="{fr.ypix(c):.1f}"'
                    f' x2="{(left + bar_w):.1f}" y2="{fr.ypix(c):.1f}"'
                    f' stroke="{col}" stroke-width="1"/>'
                )

            p.append("</g>")

        p.append("</g>")
