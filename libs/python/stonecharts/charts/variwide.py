"""Variwide chart renderer: ChartSpec -> SVG string.

Column with proportional-width bars — each bar's width encodes a second metric.
Uses render_cartesian with x_scale="variwide".
"""

from __future__ import annotations

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


def render_svg(spec: ChartSpec) -> str:
    return render_cartesian(spec, "Variwide", "variwide", _variwide_marks)


def _variwide_marks(fr: CartesianFrame, p: list[str]) -> None:
    spec = fr.spec
    n = fr.n

    PAD = 1.0

    for si, s in enumerate(spec.series):
        style = fr.styles[si]
        p.append(f'<g class="sc-series" data-series="{si}">')
        for i in range(min(n, len(s.data))):
            v = s.data[i]
            cat = fr.cats[i] if i < len(fr.cats) else str(i)

            sw = fr.slot_width(i)
            sl = fr.slot_lefts[i] if i < len(fr.slot_lefts) else fr.plot_x
            bar_x = sl + PAD
            bar_w = max(0.0, sw - 2 * PAD)

            base_px = fr.value_pix(0.0)
            val_px = fr.value_pix(v)
            bar_y = min(base_px, val_px)
            bar_h = abs(base_px - val_px)

            cx_px = sl + sw / 2
            cy_px = val_px

            z_val = ""
            if s.widths and i < len(s.widths):
                z_val = fmt_num(s.widths[i])

            p.append(
                f'<rect class="sc-bar sc-point" data-series="{si}" '
                f'data-series-name="{esc(s.name)}" data-x="{esc(cat)}" '
                f'data-y="{esc(fmt_num(v))}" data-z="{esc(z_val)}" '
                f'data-color="{style.solid}" data-r="3.5" data-r-hover="6" '
                f'cx="{cx_px:.1f}" cy="{cy_px:.1f}" '
                f'x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
                f'fill="{style.fill}"/>'
            )
        p.append("</g>")
