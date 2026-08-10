"""Technical-indicators chart renderer: ChartSpec -> SVG string.

Base metric/price line plus derived overlays (SMA, EMA, Bollinger, VWAP)
and oscillators (MACD, RSI) computed from the base data. Plot bands/lines,
flags, and oscillator panes ride the shared cartesian frame.
"""

from __future__ import annotations

import copy
import math

from ..spec import Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, dash_array, render_cartesian
from .line import _marker, _path_d, _spline_d

# ---------- transforms (pure math, parity-critical) ----------


def _sma(data: list[float], period: int) -> list[float | None]:
    n = len(data)
    out: list[float | None] = [None] * n
    for i in range(period - 1, n):
        s = 0.0
        for j in range(i - period + 1, i + 1):
            s += data[j]
        out[i] = s / period
    return out


def _ema(data: list[float], period: int) -> list[float | None]:
    n = len(data)
    out: list[float | None] = [None] * n
    if n < period:
        return out
    s = 0.0
    for j in range(period):
        s += data[j]
    seed = s / period
    out[period - 1] = seed
    alpha = 2.0 / (period + 1)
    prev = seed
    for i in range(period, n):
        val = alpha * data[i] + (1 - alpha) * prev
        out[i] = val
        prev = val
    return out


def _bollinger(
    data: list[float], period: int, k: float
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    n = len(data)
    mid = _sma(data, period)
    upper: list[float | None] = [None] * n
    lower: list[float | None] = [None] * n
    for i in range(period - 1, n):
        m = mid[i]
        assert m is not None
        var = 0.0
        for j in range(i - period + 1, i + 1):
            d = data[j] - m
            var += d * d
        var = var / period
        if var < 0:
            var = 0.0
        sigma = math.sqrt(var)
        upper[i] = m + k * sigma
        lower[i] = m - k * sigma
    return mid, upper, lower


def _vwap(data: list[float], volume: list[float]) -> list[float | None]:
    n = min(len(data), len(volume))
    out: list[float | None] = [None] * len(data)
    cum_pv = 0.0
    cum_vol = 0.0
    for i in range(n):
        cum_pv += data[i] * volume[i]
        cum_vol += volume[i]
        if cum_vol == 0.0:
            out[i] = None
        else:
            out[i] = cum_pv / cum_vol
    return out


def _rsi(data: list[float], period: int) -> list[float | None]:
    n = len(data)
    out: list[float | None] = [None] * n
    if n < period + 1:
        return out
    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        d = data[i] - data[i - 1]
        gains[i] = max(d, 0.0)
        losses[i] = max(-d, 0.0)
    sum_gain = 0.0
    sum_loss = 0.0
    for j in range(1, period + 1):
        sum_gain += gains[j]
        sum_loss += losses[j]
    avg_gain = sum_gain / period
    avg_loss = sum_loss / period
    if avg_loss == 0.0:
        out[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        out[period] = 100.0 - 100.0 / (1.0 + rs)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0.0:
            out[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            out[i] = 100.0 - 100.0 / (1.0 + rs)
    return out


def _macd(
    data: list[float], fast: int, slow: int, signal_period: int
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    ema_fast = _ema(data, fast)
    ema_slow = _ema(data, slow)
    n = len(data)
    macd_line: list[float | None] = [None] * n
    for i in range(n):
        ef = ema_fast[i]
        es = ema_slow[i]
        if ef is not None and es is not None:
            macd_line[i] = ef - es
    defined = [v for v in macd_line if v is not None]
    sig_vals = _ema(defined, signal_period) if defined else [None] * n
    signal_line: list[float | None] = [None] * n
    di = 0
    for i in range(n):
        if macd_line[i] is not None:
            signal_line[i] = sig_vals[di] if di < len(sig_vals) else None
            di += 1
    hist: list[float | None] = [None] * n
    for i in range(n):
        ml = macd_line[i]
        sl = signal_line[i]
        if ml is not None and sl is not None:
            hist[i] = ml - sl
    return macd_line, signal_line, hist


# ---------- renderer ----------

PANE_GAP = 24.0


def render_svg(spec) -> str:
    mod = copy.copy(spec)
    mod.y_axis = copy.copy(spec.y_axis)

    all_overlay_vals: list[float] = []
    for s in mod.series:
        all_overlay_vals.extend(v for v in s.data if v is not None)
        for ind in s.indicators or []:
            vals = _compute_indicator_values(s, ind)
            for v in vals:
                if v is not None:
                    all_overlay_vals.append(v)

    if all_overlay_vals:
        lo = min(all_overlay_vals)
        hi = max(all_overlay_vals)
        if mod.y_axis.min is None:
            mod.y_axis.min = lo
        if mod.y_axis.max is None:
            mod.y_axis.max = hi

    return render_cartesian(mod, "Technical indicators", "point", _ti_marks, include_zero=False)


def _compute_indicator_values(s, ind) -> list[float | None]:
    data = s.data
    t = ind.type
    period = ind.period or 20
    if t == "sma":
        return _sma(data, period)
    if t == "ema":
        return _ema(data, period)
    if t == "bollinger":
        k = 2.0
        if ind.params and "stdDev" in ind.params:
            k = float(ind.params["stdDev"])
        mid, upper, lower = _bollinger(data, period, k)
        return [v for v in mid + upper + lower if True]
    if t == "vwap":
        vol = s.volume or []
        return _vwap(data, vol)
    if t == "rsi":
        return _rsi(data, ind.period or 14)
    if t == "macd":
        fast = 12
        slow = 26
        sig = 9
        if ind.params:
            fast = int(ind.params.get("fast", 12))
            slow = int(ind.params.get("slow", 26))
            sig = int(ind.params.get("signal", 9))
        ml, sl, h = _macd(data, fast, slow, sig)
        return ml + sl + [v for v in h if True]
    return []


def _ti_marks(fr: CartesianFrame, p: list[str]) -> None:
    spec = fr.spec
    theme = fr.theme

    has_osc = False
    osc_frac = 0.30
    for s in spec.series:
        for ind in s.indicators or []:
            if ind.type in ("macd", "rsi"):
                has_osc = True
    if spec.panes and len(spec.panes) > 1:
        if spec.panes[1].height is not None:
            osc_frac = spec.panes[1].height
        if spec.panes[0].height is not None:
            osc_frac = 1.0 - spec.panes[0].height

    base_top = fr.plot_y
    if has_osc:
        base_h = (fr.plot_h - PANE_GAP) * (1 - osc_frac)
        osc_top = fr.plot_y + base_h + PANE_GAP
        osc_h = (fr.plot_h - PANE_GAP) * osc_frac
    else:
        base_h = fr.plot_h
        osc_top = 0.0
        osc_h = 0.0

    def base_ypix(v: float) -> float:
        if fr.y_max == fr.y_min:
            return base_top + base_h / 2
        return base_top + base_h - (v - fr.y_min) / (fr.y_max - fr.y_min) * base_h

    base_ypix_fn = fr.ypix if not has_osc else base_ypix

    _emit_plot_bands_lines(fr, p, base_ypix_fn, base_top, base_h)

    si_global = 0

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        pts = [(fr.xpix(i), base_ypix_fn(v)) for i, v in enumerate(s.data)]
        d = _spline_d(pts) if s.curve == "monotone" else _path_d(pts, s.step)
        lw = s.line_width if s.line_width is not None else 2
        line_dash = dash_array(s.dash_style)
        line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""

        p.append(f'<g class="sc-series" data-series="{si_global}">')

        if st.area_fill is not None and pts:
            base_floor = base_ypix_fn(fr.y_min)
            area_d = f"{d} L{pts[-1][0]:.1f} {base_floor:.1f} L{pts[0][0]:.1f} {base_floor:.1f} Z"
            p.append(
                f'<path class="sc-series-area" data-series="{si_global}" d="{area_d}" '
                f'fill="{st.area_fill}"{st.area_op} stroke="none"/>'
            )

        if s.type != "area" or st.area_fill is not None:
            p.append(
                f'<path class="sc-series-line" data-series="{si_global}" d="{d}" fill="none" '
                f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}" stroke-linejoin="round" '
                f'stroke-linecap="round"{line_dash_attr}/>'
            )

        mk = s.marker or Marker()
        if mk.enabled:
            radius = mk.radius
            radius_hover = radius + 2.5
            for i, (x, y) in enumerate(pts):
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point" data-series="{si_global}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" '
                    f'data-color="{st.solid}" data-r="{fmt_num(radius)}" '
                    f'data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(_marker(mk.symbol, x, y, radius, common, st.solid, theme.marker_halo))

        p.append("</g>")
        si_global += 1

        for ind in s.indicators or []:
            if ind.type in ("macd", "rsi"):
                continue
            _emit_overlay(fr, p, s, ind, si_global, base_ypix_fn, theme)
            si_global += 1

    osc_indicators: list[tuple[int, object, object]] = []
    for si, s in enumerate(spec.series):
        for ind in s.indicators or []:
            if ind.type in ("macd", "rsi"):
                osc_indicators.append((si, s, ind))

    if has_osc and osc_indicators:
        _emit_osc_pane(fr, p, osc_indicators, si_global, osc_top, osc_h, theme)
        si_global += len(osc_indicators)

    if spec.flags:
        _emit_flags(fr, p, spec.flags, si_global, base_ypix_fn, base_top, theme)


def _emit_plot_bands_lines(fr: CartesianFrame, p: list[str], ypix_fn, base_top: float, base_h: float) -> None:
    spec = fr.spec

    for pb in spec.x_axis.plot_bands or []:
        x1 = fr.xpix(int(pb.from_val))
        x2 = fr.xpix(int(pb.to))
        xl = min(x1, x2)
        w = abs(x2 - x1)
        opacity_attr = f' opacity="{fmt_num(pb.opacity)}"' if pb.opacity is not None else ""
        p.append(
            f'<rect class="sc-plotband" x="{xl:.1f}" y="{base_top:.1f}" '
            f'width="{w:.1f}" height="{base_h:.1f}" fill="{esc(pb.color)}"{opacity_attr}/>'
        )
        if pb.label:
            p.append(
                f'<text class="sc-plotband-label" x="{(xl + w / 2):.1f}" y="{base_top + 14:.1f}" '
                f'text-anchor="middle" font-size="10" fill="{fr.theme.axis_label_color}">{esc(pb.label)}</text>'
            )

    for pl in spec.x_axis.plot_lines or []:
        gx = fr.xpix(int(pl.value))
        sw = pl.width if pl.width is not None else 1
        ds = dash_array(pl.dash_style or "")
        ds_attr = f' stroke-dasharray="{ds}"' if ds else ""
        p.append(
            f'<line class="sc-plotline" x1="{gx:.1f}" y1="{base_top:.1f}" '
            f'x2="{gx:.1f}" y2="{base_top + base_h:.1f}" stroke="{esc(pl.color)}" '
            f'stroke-width="{fmt_num(sw)}"{ds_attr}/>'
        )
        if pl.label:
            p.append(
                f'<text class="sc-plotline-label" x="{gx + 4:.1f}" y="{base_top + 14:.1f}" '
                f'font-size="10" fill="{fr.theme.axis_label_color}">{esc(pl.label)}</text>'
            )

    for pb in spec.y_axis.plot_bands or []:
        y1 = ypix_fn(pb.from_val)
        y2 = ypix_fn(pb.to)
        yt = min(y1, y2)
        h = abs(y2 - y1)
        opacity_attr = f' opacity="{fmt_num(pb.opacity)}"' if pb.opacity is not None else ""
        p.append(
            f'<rect class="sc-plotband" x="{fr.plot_x:.1f}" y="{yt:.1f}" '
            f'width="{fr.plot_w:.1f}" height="{h:.1f}" fill="{esc(pb.color)}"{opacity_attr}/>'
        )
        if pb.label:
            p.append(
                f'<text class="sc-plotband-label" x="{fr.plot_x + fr.plot_w - 4:.1f}" y="{yt + 14:.1f}" '
                f'text-anchor="end" font-size="10" fill="{fr.theme.axis_label_color}">{esc(pb.label)}</text>'
            )

    for pl in spec.y_axis.plot_lines or []:
        gy = ypix_fn(pl.value)
        sw = pl.width if pl.width is not None else 1
        ds = dash_array(pl.dash_style or "")
        ds_attr = f' stroke-dasharray="{ds}"' if ds else ""
        p.append(
            f'<line class="sc-plotline" x1="{fr.plot_x:.1f}" y1="{gy:.1f}" '
            f'x2="{fr.plot_x + fr.plot_w:.1f}" y2="{gy:.1f}" stroke="{esc(pl.color)}" '
            f'stroke-width="{fmt_num(sw)}"{ds_attr}/>'
        )
        if pl.label:
            p.append(
                f'<text class="sc-plotline-label" x="{fr.plot_x + fr.plot_w - 4:.1f}" y="{gy - 4:.1f}" '
                f'text-anchor="end" font-size="10" fill="{fr.theme.axis_label_color}">{esc(pl.label)}</text>'
            )


def _emit_overlay(fr: CartesianFrame, p: list[str], s, ind, si: int, ypix_fn, theme) -> None:
    data = s.data
    period = ind.period or 20
    palette = fr.theme.palette
    color = ind.color or palette[si % len(palette)]
    lw = 1.5
    ds = dash_array(ind.dash_style)
    ds_attr = f' stroke-dasharray="{ds}"' if ds else ""
    ind_name = f"{s.name} {ind.type.upper()}({period})"

    if ind.type == "sma":
        vals = _sma(data, period)
        pts = [(fr.xpix(i), ypix_fn(v)) for i, v in enumerate(vals) if v is not None]
        if pts:
            d = _path_d(pts, None)
            p.append(f'<g class="sc-series" data-series="{si}">')
            p.append(
                f'<path class="sc-series-line sc-indicator" data-series="{si}" data-indicator="sma" '
                f'd="{d}" fill="none" stroke="{esc(color)}" stroke-width="{fmt_num(lw)}"{ds_attr}/>'
            )
            radius = 3.5
            radius_hover = 6.0
            for i, v in enumerate(vals):
                if v is not None:
                    x = fr.xpix(i)
                    y = ypix_fn(v)
                    xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                    common = (
                        f'class="sc-point" data-series="{si}" data-series-name="{esc(ind_name)}" '
                        f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(v))}" '
                        f'data-color="{esc(color)}" data-r="{fmt_num(radius)}" '
                        f'data-r-hover="{fmt_num(radius_hover)}"'
                    )
                    p.append(
                        f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(radius)}" fill="{esc(color)}" stroke="{theme.marker_halo}" stroke-width="1"/>'
                    )
            p.append("</g>")

    elif ind.type == "ema":
        vals = _ema(data, period)
        pts = [(fr.xpix(i), ypix_fn(v)) for i, v in enumerate(vals) if v is not None]
        if pts:
            d = _path_d(pts, None)
            p.append(f'<g class="sc-series" data-series="{si}">')
            p.append(
                f'<path class="sc-series-line sc-indicator" data-series="{si}" data-indicator="ema" '
                f'd="{d}" fill="none" stroke="{esc(color)}" stroke-width="{fmt_num(lw)}"{ds_attr}/>'
            )
            radius = 3.5
            radius_hover = 6.0
            for i, v in enumerate(vals):
                if v is not None:
                    x = fr.xpix(i)
                    y = ypix_fn(v)
                    xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                    common = (
                        f'class="sc-point" data-series="{si}" data-series-name="{esc(ind_name)}" '
                        f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(v))}" '
                        f'data-color="{esc(color)}" data-r="{fmt_num(radius)}" '
                        f'data-r-hover="{fmt_num(radius_hover)}"'
                    )
                    p.append(
                        f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(radius)}" fill="{esc(color)}" stroke="{theme.marker_halo}" stroke-width="1"/>'
                    )
            p.append("</g>")

    elif ind.type == "bollinger":
        k = 2.0
        if ind.params and "stdDev" in ind.params:
            k = float(ind.params["stdDev"])
        mid_vals, upper_vals, lower_vals = _bollinger(data, period, k)
        defined: list[tuple[int, float, float]] = []
        for i in range(len(data)):
            u, lower = upper_vals[i], lower_vals[i]
            if u is not None and lower is not None:
                defined.append((i, u, lower))
        if defined:
            upper_pts = [(fr.xpix(i), ypix_fn(u)) for i, u, _ in defined]
            lower_pts = [(fr.xpix(i), ypix_fn(lower)) for i, _, lower in defined]
            upper_d = _path_d(upper_pts, None)
            lower_rev = list(reversed(lower_pts))
            lower_d = " ".join(f"L{x:.1f} {y:.1f}" for x, y in lower_rev)
            band_d = f"{upper_d} {lower_d} Z"
            fill_opacity = 0.15
            p.append(f'<g class="sc-series" data-series="{si}">')
            p.append(
                f'<path class="sc-series-range sc-band sc-indicator" data-series="{si}" '
                f'data-indicator="bollinger" d="{band_d}" fill="{esc(color)}" '
                f'fill-opacity="{fmt_num(fill_opacity)}" stroke="none"/>'
            )
            radius = 3.5
            radius_hover = 6.0
            band_name = f"{s.name} Bollinger({period},{fmt_num(k)})"
            for i, u, lower in defined:
                x = fr.xpix(i)
                cy = ypix_fn((u + lower) / 2)
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                m_val = mid_vals[i]
                if m_val is None:
                    m_val = 0.0
                common = (
                    f'class="sc-point" data-series="{si}" data-series-name="{esc(band_name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(m_val))}" '
                    f'data-low="{esc(fmt_num(lower))}" data-high="{esc(fmt_num(u))}" '
                    f'data-color="{esc(color)}" data-r="{fmt_num(radius)}" '
                    f'data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(
                    f'<circle {common} cx="{x:.1f}" cy="{cy:.1f}" r="{fmt_num(radius)}" fill="{esc(color)}" stroke="{theme.marker_halo}" stroke-width="1"/>'
                )
            p.append("</g>")

    elif ind.type == "vwap":
        vol = s.volume or []
        vals = _vwap(data, vol)
        ind_name = f"{s.name} VWAP"
        pts = [(fr.xpix(i), ypix_fn(v)) for i, v in enumerate(vals) if v is not None]
        if pts:
            d = _path_d(pts, None)
            p.append(f'<g class="sc-series" data-series="{si}">')
            p.append(
                f'<path class="sc-series-line sc-indicator" data-series="{si}" data-indicator="vwap" '
                f'd="{d}" fill="none" stroke="{esc(color)}" stroke-width="{fmt_num(lw)}"{ds_attr}/>'
            )
            radius = 3.5
            radius_hover = 6.0
            for i, v in enumerate(vals):
                if v is not None:
                    x = fr.xpix(i)
                    y = ypix_fn(v)
                    xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                    common = (
                        f'class="sc-point" data-series="{si}" data-series-name="{esc(ind_name)}" '
                        f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(v))}" '
                        f'data-color="{esc(color)}" data-r="{fmt_num(radius)}" '
                        f'data-r-hover="{fmt_num(radius_hover)}"'
                    )
                    p.append(
                        f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(radius)}" fill="{esc(color)}" stroke="{theme.marker_halo}" stroke-width="1"/>'
                    )
            p.append("</g>")


def _emit_osc_pane(
    fr: CartesianFrame, p: list[str], osc_list, si_start: int, osc_top: float, osc_h: float, theme
) -> None:
    si = si_start
    for _, s, ind in osc_list:
        data = s.data
        period = ind.period or 14
        palette = fr.theme.palette
        color = ind.color or palette[si % len(palette)]
        ds = dash_array(ind.dash_style)
        ds_attr = f' stroke-dasharray="{ds}"' if ds else ""

        if ind.type == "rsi":
            osc_min = 0.0
            osc_max = 100.0
            if fr.spec.panes and len(fr.spec.panes) > 1:
                pane = fr.spec.panes[1]
                if pane.min is not None:
                    osc_min = pane.min
                if pane.max is not None:
                    osc_max = pane.max

            def osc_ypix(v: float, o_max=osc_max, o_min=osc_min) -> float:
                if o_max == o_min:
                    return osc_top + osc_h / 2
                return osc_top + osc_h - (v - o_min) / (o_max - o_min) * osc_h

            if fr.spec.panes and len(fr.spec.panes) > 1:
                pane = fr.spec.panes[1]
                for pb in getattr(pane, "plot_bands", None) or []:
                    y1 = osc_ypix(pb.from_val)
                    y2 = osc_ypix(pb.to)
                    yt = min(y1, y2)
                    h = abs(y2 - y1)
                    opacity_attr = f' opacity="{fmt_num(pb.opacity)}"' if pb.opacity is not None else ""
                    p.append(
                        f'<rect class="sc-plotband" x="{fr.plot_x:.1f}" y="{yt:.1f}" '
                        f'width="{fr.plot_w:.1f}" height="{h:.1f}" fill="{esc(pb.color)}"{opacity_attr}/>'
                    )
                    if pb.label:
                        p.append(
                            f'<text class="sc-plotband-label" x="{fr.plot_x + fr.plot_w - 4:.1f}" y="{yt + 14:.1f}" '
                            f'text-anchor="end" font-size="10" fill="{fr.theme.axis_label_color}">{esc(pb.label)}</text>'
                        )
                for pl in getattr(pane, "plot_lines", None) or []:
                    gy = osc_ypix(pl.value)
                    sw = pl.width if pl.width is not None else 1
                    pds = dash_array(pl.dash_style)
                    pds_attr = f' stroke-dasharray="{pds}"' if pds else ""
                    p.append(
                        f'<line class="sc-plotline" x1="{fr.plot_x:.1f}" y1="{gy:.1f}" '
                        f'x2="{fr.plot_x + fr.plot_w:.1f}" y2="{gy:.1f}" stroke="{esc(pl.color)}" '
                        f'stroke-width="{fmt_num(sw)}"{pds_attr}/>'
                    )

            vals = _rsi(data, period)
            ind_name = f"{s.name} RSI({period})"
            pts = [(fr.xpix(i), osc_ypix(v)) for i, v in enumerate(vals) if v is not None]
            if pts:
                d = _path_d(pts, None)
                p.append(f'<g class="sc-series" data-series="{si}">')
                p.append(
                    f'<path class="sc-series-line sc-indicator" data-series="{si}" data-indicator="rsi" '
                    f'd="{d}" fill="none" stroke="{esc(color)}" stroke-width="{fmt_num(1.5)}"{ds_attr}/>'
                )
                radius = 3.5
                radius_hover = 6.0
                for i, v in enumerate(vals):
                    if v is not None:
                        x = fr.xpix(i)
                        y = osc_ypix(v)
                        xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                        common = (
                            f'class="sc-point" data-series="{si}" data-series-name="{esc(ind_name)}" '
                            f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(v))}" '
                            f'data-color="{esc(color)}" data-r="{fmt_num(radius)}" '
                            f'data-r-hover="{fmt_num(radius_hover)}"'
                        )
                        p.append(
                            f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(radius)}" fill="{esc(color)}" stroke="{theme.marker_halo}" stroke-width="1"/>'
                        )
                p.append("</g>")
        si += 1


def _emit_flags(fr: CartesianFrame, p: list[str], flags, si: int, ypix_fn, base_top: float, theme) -> None:
    palette = fr.theme.palette
    p.append(f'<g class="sc-series sc-flags" data-series="{si}">')
    for fl in flags:
        x = fr.xpix(int(fl.x))
        color = fl.color or palette[si % len(palette)]
        flag_y = base_top
        title = fl.title
        FLAG_H = 14.0
        FLAG_W = max(len(title) * 7.0, 20.0)

        common = (
            f'class="sc-flag sc-point" data-series="{si}" data-series-name="Events" '
            f'data-x="{esc(fr.cats[int(fl.x)] if int(fl.x) < len(fr.cats) else str(int(fl.x)))}" '
            f'data-y="{esc(title)}" data-color="{esc(color)}" '
            f'data-r="{fmt_num(3.5)}" data-r-hover="{fmt_num(6)}" '
            f'cx="{x:.1f}" cy="{flag_y:.1f}"'
        )

        if fl.shape == "circlepin":
            p.append(f"<g {common}>")
            p.append(f'<circle cx="{x:.1f}" cy="{flag_y:.1f}" r="6" fill="{esc(color)}" stroke="{esc(color)}"/>')
            p.append(
                f'<text class="sc-flag-label" x="{x:.1f}" y="{flag_y - 10:.1f}" text-anchor="middle" font-size="9" fill="{fr.theme.axis_label_color}">{esc(title)}</text>'
            )
            p.append("</g>")
        elif fl.shape == "squarepin":
            p.append(f"<g {common}>")
            p.append(f'<rect x="{x - 6:.1f}" y="{flag_y - 6:.1f}" width="12" height="12" fill="{esc(color)}"/>')
            p.append(
                f'<text class="sc-flag-label" x="{x:.1f}" y="{flag_y - 10:.1f}" text-anchor="middle" font-size="9" fill="{fr.theme.axis_label_color}">{esc(title)}</text>'
            )
            p.append("</g>")
        else:
            stem_bottom = flag_y
            stem_top = flag_y - FLAG_H
            p.append(f"<g {common}>")
            p.append(
                f'<path class="sc-flag-glyph" d="M{x:.1f} {stem_bottom:.1f} '
                f'l0 {-FLAG_H:.1f} l{FLAG_W:.1f} 0 l0 {FLAG_H:.1f} l{-FLAG_W:.1f} 0 z" '
                f'fill="{esc(color)}" stroke="{esc(color)}"/>'
            )
            p.append(
                f'<text class="sc-flag-label" x="{x + FLAG_W / 2:.1f}" y="{stem_top + 10:.1f}" '
                f'text-anchor="middle" font-size="9" fill="#ffffff">{esc(title)}</text>'
            )
            p.append("</g>")
    p.append("</g>")
