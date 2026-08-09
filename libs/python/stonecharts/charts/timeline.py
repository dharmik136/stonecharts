"""Timeline chart renderer: ChartSpec -> SVG string.

Events placed along a single time axis with markers, leader lines, and labels.
Uses render_cartesian with x_scale="numeric" and include_zero=False.
"""

from __future__ import annotations

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker


def render_svg(spec: ChartSpec) -> str:
    return render_cartesian(spec, "Timeline", "numeric", _timeline_marks, include_zero=False)


def _timeline_marks(fr: CartesianFrame, p: list[str]) -> None:
    spec = fr.spec
    theme = fr.theme

    LEAD = 28.0

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        mk = s.marker
        symbol = mk.symbol if mk else "circle"
        radius = mk.radius if mk and mk.radius != 0.0 else 5.0
        r_hover = fmt_num(radius + 3)

        base_y = fr.plot_y + fr.plot_h / 2

        p.append(f'<g class="sc-series" data-series="{si}">')
        for k in range(len(s.data)):
            v = s.data[k]
            cx = fr.xpix(v)
            cy = base_y

            side = -1.0 if (k % 2 == 0) else 1.0
            label_y = base_y + side * LEAD

            label_text = ""
            if s.labels and k < len(s.labels):
                label_text = s.labels[k]

            data_x = esc(label_text) if label_text else esc(fmt_num(v))

            p.append(
                f'<line class="sc-leader" data-series="{si}" '
                f'x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{label_y:.1f}" '
                f'stroke="{theme.axis_line_color}" stroke-width="1"/>'
            )

            common = (
                f'class="sc-event sc-point" data-series="{si}" '
                f'data-series-name="{esc(s.name)}" data-x="{data_x}" '
                f'data-y="{esc(fmt_num(v))}" '
                f'data-color="{st.solid}" data-r="{fmt_num(radius)}" data-r-hover="{r_hover}"'
            )
            p.append(_marker(symbol, cx, cy, radius, common, st.fill, theme.marker_halo))

            if label_text:
                anchor_y = label_y - 6 if side < 0 else label_y + 12
                p.append(
                    f'<text class="sc-label" data-series="{si}" x="{cx:.1f}" y="{anchor_y:.1f}" '
                    f'text-anchor="middle" font-size="11" fill="{theme.axis_label_color}">'
                    f"{esc(label_text)}</text>"
                )
        p.append("</g>")
