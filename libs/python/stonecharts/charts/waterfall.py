"""Waterfall chart renderer: ChartSpec -> SVG string.

Floating bars stepping through signed deltas with a running total.
Shared Cartesian chrome comes from _cartesian.py; this module draws only the
waterfall marks: connector lines + one floating rect per stage.
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

    sum_idx = set(getattr(mod, "sum_indices", None) or [])
    isum_idx = set(getattr(mod, "intermediate_sum_indices", None) or [])

    # Running-total transform to compute y-domain.
    all_vals = [0.0]
    for s in mod.series:
        running = 0.0
        for i, delta in enumerate(s.data):
            if i in sum_idx or i in isum_idx:
                all_vals.append(0.0)
                all_vals.append(running)
            else:
                all_vals.append(running)
                running += delta
                all_vals.append(running)
    if mod.y_axis.min is None:
        mod.y_axis.min = min(all_vals)
    if mod.y_axis.max is None:
        mod.y_axis.max = max(all_vals)

    return render_cartesian(mod, "Waterfall", "band", _waterfall_marks)


def _waterfall_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    sum_idx = set(getattr(spec, "sum_indices", None) or [])
    isum_idx = set(getattr(spec, "intermediate_sum_indices", None) or [])
    up_color = getattr(spec, "up_color", "#3f9b6a")
    down_color = getattr(spec, "down_color", "#d65f5f")
    total_color = getattr(spec, "total_color", "#4b6cb7")

    connector_cfg = getattr(spec, "connector", None)
    conn_enabled = True
    conn_dash = "4 3"  # dashed default
    conn_color = fr.theme.grid_color
    if connector_cfg is not None:
        if hasattr(connector_cfg, "enabled"):
            conn_enabled = connector_cfg.enabled
        if hasattr(connector_cfg, "dash_style"):
            ds = connector_cfg.dash_style
            if ds == "dotted":
                conn_dash = "2 3"
            elif ds == "solid":
                conn_dash = ""

    band = fr.band_width()
    group_w = band * (1 - PAD)
    k = 1 if not fr.spec.grouping else max(len(fr.spec.series), 1)
    bar_w = group_w / k

    for si, s in enumerate(spec.series):
        n = min(len(s.data), fr.n)
        p.append(f'<g class="sc-series" data-series="{si}">')

        # Running-total transform
        bars = []  # list of (start, end, kind, running_after)
        running = 0.0
        for i in range(n):
            delta = s.data[i]
            if i in sum_idx or i in isum_idx:
                start = 0.0
                end = running
                kind = "total"
                bars.append((start, end, kind, running))
            else:
                start = running
                end = running + delta
                running = end
                kind = "increase" if delta >= 0 else "decrease"
                bars.append((start, end, kind, running))

        # Emit connectors first (so bars paint over line ends)
        if conn_enabled:
            for i in range(len(bars) - 1):
                _start, _end, _kind, level = bars[i]
                x1 = fr.xpix(i) - group_w / 2 + bar_w * (si if fr.spec.grouping else 0) + bar_w
                x2 = fr.xpix(i + 1) - group_w / 2 + bar_w * (si if fr.spec.grouping else 0)
                y = fr.ypix(level)
                dash_attr = f' stroke-dasharray="{conn_dash}"' if conn_dash else ""
                p.append(
                    f'<line class="sc-connector" x1="{x1:.1f}" y1="{y:.1f}"'
                    f' x2="{x2:.1f}" y2="{y:.1f}"'
                    f' stroke="{conn_color}" stroke-width="1"{dash_attr}/>'
                )

        # Emit bars
        for i in range(len(bars)):
            start, end, kind, total_after = bars[i]
            xlabel = fr.cats[i] if i < len(fr.cats) else str(i)

            left = fr.xpix(i) - group_w / 2 + bar_w * (si if fr.spec.grouping else 0)
            cx = left + bar_w / 2
            y_top = fr.ypix(max(start, end))
            y_bot = fr.ypix(min(start, end))
            bar_h = max(abs(y_bot - y_top), 1.0)

            if kind == "increase":
                fill = up_color
            elif kind == "decrease":
                fill = down_color
            else:
                fill = total_color

            display_val = total_after if kind == "total" else s.data[i]

            p.append(
                f'<rect class="sc-bar sc-point" data-series="{si}"'
                f' data-series-name="{esc(s.name)}" data-x="{esc(xlabel)}"'
                f' data-y="{esc(fmt_num(display_val))}"'
                f' data-kind="{kind}" data-total="{esc(fmt_num(total_after))}"'
                f' data-color="{fill}" data-r="3.5" data-r-hover="6"'
                f' cx="{cx:.1f}" cy="{y_top:.1f}"'
                f' x="{left:.1f}" y="{y_top:.1f}"'
                f' width="{bar_w:.1f}" height="{bar_h:.1f}"'
                f' fill="{fill}"/>'
            )

        p.append("</g>")
