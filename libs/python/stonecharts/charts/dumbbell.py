"""Dumbbell chart renderer: ChartSpec -> SVG string.

Connected-dot plot: two marker heads (low + high) joined by a thin
connector per category. Reuses Column's band layout and Line's marker
shapes. See charts/dumbbell/design.md for the full geometry contract.
"""

from __future__ import annotations

from ..spec import ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, dash_array, render_cartesian
from .line import _marker

PAD = 0.2


def render_svg(spec: ChartSpec) -> str:
    orientation = spec.orientation or "vertical"
    return render_cartesian(spec, "Dumbbell", "band", _dumbbell_marks, include_zero=False, orientation=orientation)


def _dumbbell_marks(fr: CartesianFrame, p: list) -> None:
    if fr.n <= 0:
        return

    spec = fr.spec
    horiz = fr.orientation == "horizontal"
    K = max(len(spec.series), 1) if spec.grouping else 1
    halo = fr.theme.marker_halo

    for si, s in enumerate(spec.series):
        st = fr.styles[si]
        m = s.marker
        symbol = m.symbol if m else "circle"
        r = m.radius if m and m.radius else 4.0
        r_hover = r * 1.5
        lw = s.line_width if s.line_width is not None else 2
        line_dash = dash_array(s.dash_style)
        dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
        high_arr = s.high or []
        p.append(f'<g class="sc-series" data-series="{si}">')

        if horiz:
            band_sz = fr.band_height()
            group_sz = band_sz * (1 - PAD)
            bar_sz = group_sz / K

            for i in range(min(len(s.data), fr.n)):
                lo_val = s.data[i]
                hi_val = high_arr[i] if i < len(high_arr) else lo_val
                slot = si if spec.grouping and K > 1 else 0
                band_c = fr.band_center(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                db_y = slot_start + bar_sz / 2
                lo_x = fr.value_pix(lo_val)
                hi_x = fr.value_pix(hi_val)
                p.append(
                    f'<line class="sc-connector" data-series="{si}" '
                    f'x1="{lo_x:.1f}" y1="{db_y:.1f}" x2="{hi_x:.1f}" y2="{db_y:.1f}" '
                    f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}"{dash_attr}/>'
                )

            for i in range(min(len(s.data), fr.n)):
                lo_val = s.data[i]
                slot = si if spec.grouping and K > 1 else 0
                band_c = fr.band_center(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                db_y = slot_start + bar_sz / 2
                lo_x = fr.value_pix(lo_val)
                low_common = f'class="sc-dumbbell-low" data-series="{si}"'
                p.append(_marker(symbol, lo_x, db_y, r, low_common, st.solid, halo))

            for i in range(min(len(s.data), fr.n)):
                lo_val = s.data[i]
                hi_val = high_arr[i] if i < len(high_arr) else lo_val
                slot = si if spec.grouping and K > 1 else 0
                band_c = fr.band_center(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                db_y = slot_start + bar_sz / 2
                hi_x = fr.value_pix(hi_val)
                cat = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point sc-dumbbell-high" data-series="{si}" '
                    f'data-series-name="{esc(s.name)}" data-x="{esc(cat)}" '
                    f'data-y="{esc(fmt_num(hi_val))}" data-low="{esc(fmt_num(lo_val))}" '
                    f'data-high="{esc(fmt_num(hi_val))}" data-color="{st.solid}" '
                    f'data-r="{fmt_num(r)}" data-r-hover="{fmt_num(r_hover)}"'
                )
                p.append(_marker(symbol, hi_x, db_y, r, common, st.solid, halo))
        else:
            band_sz = fr.band_width()
            group_sz = band_sz * (1 - PAD)
            bar_sz = group_sz / K

            for i in range(min(len(s.data), fr.n)):
                lo_val = s.data[i]
                hi_val = high_arr[i] if i < len(high_arr) else lo_val
                slot = si if spec.grouping and K > 1 else 0
                band_c = fr.xpix(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                db_x = slot_start + bar_sz / 2
                lo_y = fr.ypix(lo_val)
                hi_y = fr.ypix(hi_val)
                p.append(
                    f'<line class="sc-connector" data-series="{si}" '
                    f'x1="{db_x:.1f}" y1="{lo_y:.1f}" x2="{db_x:.1f}" y2="{hi_y:.1f}" '
                    f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}"{dash_attr}/>'
                )

            for i in range(min(len(s.data), fr.n)):
                lo_val = s.data[i]
                slot = si if spec.grouping and K > 1 else 0
                band_c = fr.xpix(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                db_x = slot_start + bar_sz / 2
                lo_y = fr.ypix(lo_val)
                low_common = f'class="sc-dumbbell-low" data-series="{si}"'
                p.append(_marker(symbol, db_x, lo_y, r, low_common, st.solid, halo))

            for i in range(min(len(s.data), fr.n)):
                lo_val = s.data[i]
                hi_val = high_arr[i] if i < len(high_arr) else lo_val
                slot = si if spec.grouping and K > 1 else 0
                band_c = fr.xpix(i)
                slot_start = band_c - group_sz / 2 + bar_sz * slot
                db_x = slot_start + bar_sz / 2
                hi_y = fr.ypix(hi_val)
                cat = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point sc-dumbbell-high" data-series="{si}" '
                    f'data-series-name="{esc(s.name)}" data-x="{esc(cat)}" '
                    f'data-y="{esc(fmt_num(hi_val))}" data-low="{esc(fmt_num(lo_val))}" '
                    f'data-high="{esc(fmt_num(hi_val))}" data-color="{st.solid}" '
                    f'data-r="{fmt_num(r)}" data-r-hover="{fmt_num(r_hover)}"'
                )
                p.append(_marker(symbol, db_x, hi_y, r, common, st.solid, halo))

        p.append("</g>")
