"""Bullet chart renderer: ChartSpec -> SVG string.

Horizontal KPI bars with a comparative target tick and qualitative range bands.
Shared Cartesian chrome comes from _cartesian.py; this module draws only the
bullet marks. See charts/bullet/design.md for the full geometry contract.
"""

from __future__ import annotations

import copy

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian

PAD = 0.2
MEASURE_RATIO = 0.4
TARGET_RATIO = 0.6
TARGET_WIDTH = 2

_RANGE_SHADES_LIGHT = ["#cccccc", "#dddddd", "#eeeeee"]
_RANGE_SHADES_DARK = ["#3d3d55", "#2d2d42", "#1e1e30"]


def _range_fills(n: int, is_dark: bool) -> list[str]:
    shades = _RANGE_SHADES_DARK if is_dark else _RANGE_SHADES_LIGHT
    if n <= len(shades):
        return shades[:n]
    return [shades[min(k, len(shades) - 1)] for k in range(n)]


def render_svg(spec: ChartSpec) -> str:
    mod = copy.copy(spec)
    mod.y_axis = copy.copy(spec.y_axis)

    ranges = getattr(mod, "bullet_ranges", None) or []
    target = getattr(mod, "bullet_target", None)

    all_vals = [0.0]
    for s in mod.series:
        all_vals.extend(s.data)
    if target is not None:
        all_vals.append(target)
    all_vals.extend(ranges)

    if mod.y_axis.min is None:
        mod.y_axis.min = min(all_vals)
    if mod.y_axis.max is None:
        mod.y_axis.max = max(all_vals)

    return render_cartesian(mod, "Bullet", "band", _bullet_marks, orientation="horizontal")


def _bullet_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    ranges = getattr(spec, "bullet_ranges", None) or []
    target = getattr(spec, "bullet_target", None)
    is_dark = fr.theme.name == "dark"
    target_color = "#cccccc" if is_dark else "#333333"

    band_height = fr.band_height()
    group_h = band_height * (1 - PAD)
    stacked = fr.stacking in ("normal", "percent")
    k_slots = 1 if stacked or not fr.spec.grouping else max(len(fr.spec.series), 1)
    bar_h = group_h / k_slots
    measure_h = bar_h * MEASURE_RATIO
    target_h = bar_h * TARGET_RATIO
    baseline = fr.value_zero()

    if ranges:
        sorted_ranges = sorted(ranges)
        fills = _range_fills(len(sorted_ranges), is_dark)
        for i in range(fr.n):
            cy_band = fr.band_center(i)
            band_top = cy_band - group_h / 2
            prev_x = baseline
            for k, r_val in enumerate(sorted_ranges):
                rx = fr.value_pix(r_val)
                x = min(prev_x, rx)
                w = abs(rx - prev_x)
                p.append(
                    f'<rect class="sc-range" x="{x:.1f}" y="{band_top:.1f}" '
                    f'width="{w:.1f}" height="{group_h:.1f}" fill="{fills[k]}"/>'
                )
                prev_x = rx

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        p.append(f'<g class="sc-series" data-series="{si}">')
        for i, raw in enumerate(s.data):
            if i >= fr.n:
                break
            cy_band = fr.band_center(i)
            slot = si if fr.spec.grouping and not stacked else 0
            slot_top = cy_band - group_h / 2 + bar_h * slot
            measure_top = slot_top + (bar_h - measure_h) / 2

            xv = fr.value_pix(raw)
            x = min(baseline, xv)
            w = abs(baseline - xv)
            tip = xv
            cy = measure_top + measure_h / 2

            ylabel = fr.cats[i] if i < len(fr.cats) else str(i)
            common = (
                f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(ylabel)}" data-y="{esc(fmt_num(raw))}" '
                f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
            )
            p.append(
                f'<rect {common} cx="{tip:.1f}" cy="{cy:.1f}" x="{x:.1f}" y="{measure_top:.1f}" '
                f'width="{w:.1f}" height="{measure_h:.1f}" fill="{st.fill}"/>'
            )
        p.append("</g>")

    if target is not None:
        for i in range(fr.n):
            cy_band = fr.band_center(i)
            target_top = cy_band - target_h / 2
            tx = fr.value_pix(target)
            p.append(
                f'<line class="sc-target" x1="{tx:.1f}" y1="{target_top:.1f}" '
                f'x2="{tx:.1f}" y2="{target_top + target_h:.1f}" '
                f'stroke="{target_color}" stroke-width="{TARGET_WIDTH}"/>'
            )
