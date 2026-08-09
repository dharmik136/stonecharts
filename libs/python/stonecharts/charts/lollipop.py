"""Lollipop chart renderer: ChartSpec -> SVG string.

Thin stems from the baseline capped with marker heads. Reuses Column's band
layout and Line's marker shapes. See charts/lollipop/design.md for the full
geometry contract.
"""

from __future__ import annotations

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker

PAD = 0.2


def render_svg(spec: ChartSpec) -> str:
    orientation = spec.orientation or "vertical"
    return render_cartesian(spec, "Lollipop", "band", _lollipop_marks, orientation=orientation)


def _lollipop_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    horiz = fr.orientation == "horizontal"
    stacked = fr.stacking in ("normal", "percent")
    K = 1 if stacked or not spec.grouping else max(len(spec.series), 1)
    halo = fr.theme.marker_halo

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        m = s.marker
        symbol = m.symbol if m else "circle"
        r = m.radius if m and m.radius else 3.5
        r_hover = r * 1.5
        lw = s.line_width if s.line_width is not None else 2
        p.append(f'<g class="sc-series" data-series="{si}">')

        if horiz:
            band_sz = fr.band_height()
            group_sz = band_sz * (1 - PAD)
            bar_sz = group_sz / K
            baseline = fr.value_pix(0.0)

            for i, v in enumerate(s.data):
                if i >= fr.n:
                    break
                slot = si if spec.grouping and not stacked else 0
                band_c = fr.band_center(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                stem_y = slot_start + bar_sz / 2
                val_x = fr.value_pix(v)
                p.append(
                    f'<line class="sc-stem" data-series="{si}" '
                    f'x1="{baseline:.1f}" y1="{stem_y:.1f}" x2="{val_x:.1f}" y2="{stem_y:.1f}" '
                    f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}"/>'
                )

            for i, v in enumerate(s.data):
                if i >= fr.n:
                    break
                slot = si if spec.grouping and not stacked else 0
                band_c = fr.band_center(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                stem_y = slot_start + bar_sz / 2
                val_x = fr.value_pix(v)
                cat = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point sc-lollipop-head" data-series="{si}" '
                    f'data-series-name="{esc(s.name)}" data-x="{esc(cat)}" '
                    f'data-y="{esc(fmt_num(v))}" data-color="{st.solid}" '
                    f'data-r="{fmt_num(r)}" data-r-hover="{fmt_num(r_hover)}"'
                )
                p.append(_marker(symbol, val_x, stem_y, r, common, st.solid, halo))
        else:
            band_sz = fr.band_width()
            group_sz = band_sz * (1 - PAD)
            bar_sz = group_sz / K
            baseline_y = fr.ypix(0.0)

            for i, v in enumerate(s.data):
                if i >= fr.n:
                    break
                slot = si if spec.grouping and not stacked else 0
                band_c = fr.xpix(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                stem_x = slot_start + bar_sz / 2
                val_y = fr.ypix(v)
                p.append(
                    f'<line class="sc-stem" data-series="{si}" '
                    f'x1="{stem_x:.1f}" y1="{baseline_y:.1f}" x2="{stem_x:.1f}" y2="{val_y:.1f}" '
                    f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}"/>'
                )

            for i, v in enumerate(s.data):
                if i >= fr.n:
                    break
                slot = si if spec.grouping and not stacked else 0
                band_c = fr.xpix(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                stem_x = slot_start + bar_sz / 2
                val_y = fr.ypix(v)
                cat = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point sc-lollipop-head" data-series="{si}" '
                    f'data-series-name="{esc(s.name)}" data-x="{esc(cat)}" '
                    f'data-y="{esc(fmt_num(v))}" data-color="{st.solid}" '
                    f'data-r="{fmt_num(r)}" data-r-hover="{fmt_num(r_hover)}"'
                )
                p.append(_marker(symbol, stem_x, val_y, r, common, st.solid, halo))

        p.append("</g>")
