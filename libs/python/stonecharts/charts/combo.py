"""Combo chart renderer: ChartSpec -> SVG string.

Shared Cartesian chrome comes from _cartesian.py. This module composes the
existing line and column mark grammars on the same plot area, with an optional
secondary y-axis.
"""
from __future__ import annotations

from typing import List

from ..spec import Marker, Series
from ..util import esc, fmt_num, nice_ticks
from ._cartesian import CartesianFrame, _chrome_head, _chrome_tail, build_frame, dash_array
from .line import _marker as _line_marker, _path_d, _spline_d


PAD = 0.2


def render_svg(spec) -> str:
    fr = build_frame(spec, "Combo", "band", True)
    fr.secondary_axis = spec.secondary_y_axis
    if fr.secondary_axis is not None and fr.secondary_axis.title:
        fr.plot_w -= 40
    _apply_combo_domains(fr)
    p: List[str] = []
    _chrome_head(fr, p)
    _combo_marks(fr, p)
    _chrome_tail(fr, p)
    return "".join(p)


def _series_kind(s: Series) -> str:
    return getattr(s, "type", "column") or "column"


def _series_axis(fr: CartesianFrame, s: Series) -> int:
    return 1 if getattr(s, "y_axis", 0) == 1 and fr.secondary_axis is not None else 0


def _series_pix(fr: CartesianFrame, s: Series, v: float) -> float:
    return fr.ypix2(v) if _series_axis(fr, s) == 1 else fr.ypix(v)


def _apply_combo_domains(fr: CartesianFrame) -> None:
    primary = _axis_domain(fr, 0)
    fr.y_min, fr.y_max, fr.y_ticks = nice_ticks(primary[0], primary[1], 6)
    if fr.secondary_axis is not None:
        secondary = _axis_domain(fr, 1)
        fr.y2_min, fr.y2_max, fr.y2_ticks = nice_ticks(secondary[0], secondary[1], 6)
    else:
        fr.y2_min = fr.y2_max = 0.0
        fr.y2_ticks = []


def _axis_domain(fr: CartesianFrame, axis: int) -> tuple[float, float]:
    series = [s for s in fr.spec.series if _series_axis(fr, s) == axis]
    if not series:
        return 0.0, 0.0
    values = [v for s in series for v in s.data]
    if fr.stacking == "percent":
        lo, hi = 0.0, 100.0
    elif fr.stacking == "normal":
        pos = [0.0] * fr.n
        neg = [0.0] * fr.n
        for s in series:
            if _series_kind(s) != "column":
                continue
            for i, v in enumerate(s.data):
                if i >= fr.n:
                    break
                if v >= 0:
                    pos[i] += v
                else:
                    neg[i] += v
        lo = min(neg + [0.0])
        hi = max(pos + [0.0])
    else:
        lo = min(values + [0.0]) if values else 0.0
        hi = max(values + [0.0]) if values else 0.0
    for s in series:
        if _series_kind(s) != "line":
            continue
        for v in s.data:
            if v < lo:
                lo = v
            if v > hi:
                hi = v
    return lo, hi


def _combo_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    column_series = [i for i, s in enumerate(fr.spec.series) if _series_kind(s) != "line"]
    col_rank = {si: rank for rank, si in enumerate(column_series)}
    band_width = fr.band_width()
    group_w = band_width * (1 - PAD)
    stacked = fr.stacking in ("normal", "percent")
    k_slots = 1 if stacked or not fr.spec.grouping else max(len(column_series), 1)
    bar_w = group_w / k_slots

    totals = [0.0] * fr.n
    if stacked:
        for si in column_series:
            s = fr.spec.series[si]
            for i, v in enumerate(s.data):
                if i < fr.n:
                    totals[i] += v

    positive = [0.0] * fr.n
    negative = [0.0] * fr.n
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        kind = _series_kind(s)
        axis = _series_axis(fr, s)
        p.append(f'<g class="sc-series" data-series="{si}">')
        if kind == "line":
            pts = [(fr.xpix(i), _series_pix(fr, s, v)) for i, v in enumerate(s.data)]
            d = _spline_d(pts) if s.curve == "monotone" else _path_d(pts, s.step)
            line_dash = dash_array(s.dash_style)
            line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
            if st.area_fill is not None and pts:
                base = fr.ypix2(0.0) if axis == 1 else fr.ypix(0.0)
                area_d = f"{d} L{pts[-1][0]:.1f} {base:.1f} L{pts[0][0]:.1f} {base:.1f} Z"
                p.append(
                    f'<path class="sc-series-area" data-series="{si}" d="{area_d}" '
                    f'fill="{st.area_fill}"{st.area_op} stroke="none"/>'
                )
            p.append(
                f'<path class="sc-series-line" data-series="{si}" d="{d}" fill="none" '
                f'stroke="{st.stroke}" stroke-width="{fmt_num(s.line_width or 2)}" stroke-linejoin="round" '
                f'stroke-linecap="round"{line_dash_attr}/>'
            )
            mk = s.marker or Marker()
            if mk.enabled:
                radius = mk.radius
                radius_hover = radius + 2.5
                for i, (x, y) in enumerate(pts):
                    xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                    common = (
                        f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                        f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" '
                        f'data-color="{st.solid}" data-r="{fmt_num(radius)}" '
                        f'data-r-hover="{fmt_num(radius_hover)}"'
                    )
                    p.append(_line_marker(mk.symbol, x, y, radius, common, st.solid, fr.theme.marker_halo))
        else:
            for i, raw in enumerate(s.data):
                if i >= fr.n:
                    break
                cy_band = fr.band_center(i)
                if stacked:
                    top = cy_band - group_w / 2
                    value = raw
                    if fr.stacking == "percent":
                        total = totals[i]
                        value = 0.0 if total == 0.0 else raw / total * 100.0
                    if value >= 0:
                        left_v = positive[i]
                        right_v = left_v + value
                        positive[i] = right_v
                    else:
                        left_v = negative[i]
                        right_v = left_v + value
                        negative[i] = right_v
                    x0 = fr.ypix2(left_v) if axis == 1 else fr.ypix(left_v)
                    x1 = fr.ypix2(right_v) if axis == 1 else fr.ypix(right_v)
                    x = min(x0, x1)
                    w = abs(x0 - x1)
                    cx = x1
                    height = group_w
                else:
                    slot = col_rank[si] if fr.spec.grouping else 0
                    top = cy_band - group_w / 2 + bar_w * float(slot)
                    xv = fr.ypix2(raw) if axis == 1 else fr.ypix(raw)
                    baseline = fr.ypix2(0.0) if axis == 1 else fr.ypix(0.0)
                    x = min(baseline, xv)
                    w = abs(baseline - xv)
                    cx = xv
                    height = bar_w
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                cy = top + height / 2
                common = (
                    f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(raw))}" '
                    f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
                )
                p.append(
                    f'<rect {common} cx="{cx:.1f}" cy="{cy:.1f}" x="{x:.1f}" y="{top:.1f}" '
                    f'width="{w:.1f}" height="{height:.1f}" fill="{st.fill}"/>'
                )
        p.append("</g>")
