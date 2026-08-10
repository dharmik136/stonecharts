"""X-range / Gantt chart renderer: ChartSpec -> SVG string.

Horizontal span bars on lane categories with optional milestones and
dependency connectors. Rides the shared cartesian frame with
orientation="horizontal", x_scale="band", include_zero=False.
"""

from __future__ import annotations

from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


def render_svg(spec) -> str:
    lane_cats = spec.y_axis.categories or []
    lane_count = len(lane_cats)
    spec.x_axis.categories = lane_cats

    for s in spec.series:
        while len(s.data) < lane_count:
            s.data.append(0.0)

    all_times: list[float] = []
    for s in spec.series:
        for sp in s.spans or []:
            all_times.append(sp.x)
            all_times.append(sp.x2)
    if spec.y_axis.min is None:
        spec.y_axis.min = spec.x_axis.min if spec.x_axis.min is not None else (min(all_times) if all_times else 0.0)
    if spec.y_axis.max is None:
        spec.y_axis.max = spec.x_axis.max if spec.x_axis.max is not None else (max(all_times) if all_times else 0.0)

    return render_cartesian(spec, "X-range", "band", _xrange_marks, include_zero=False, orientation="horizontal")


PAD = 0.2


def _xrange_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    lane_height = fr.plot_h / fr.n
    bar_thickness = lane_height * (1 - PAD)

    def ypix_band(j: int) -> float:
        return fr.plot_y + lane_height * j + lane_height / 2

    def xval(v: float) -> float:
        return fr.value_pix(v)

    cats = fr.cats

    span_index: dict[str, tuple[float, float]] = {}
    for si, s in enumerate(fr.spec.series):
        for sp in s.spans or []:
            if sp.id:
                end_x = xval(sp.x2)
                cy = ypix_band(sp.y)
                span_index[sp.id] = (end_x, cy)

    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        fill = st.fill

        p.append(f'<g class="sc-series" data-series="{si}">')

        for sp in s.spans or []:
            start = sp.x
            end = sp.x2
            lane = sp.y

            x_left = xval(min(start, end))
            x_right = xval(max(start, end))
            w = x_right - x_left
            cy = ypix_band(lane)
            cx = xval((start + end) / 2)

            lane_label = cats[lane] if lane < len(cats) else str(lane)
            duration = end - start

            data_attrs = (
                f'data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(lane_label)}" data-y="{esc(fmt_num(start))}" '
                f'data-start="{esc(fmt_num(start))}" data-end="{esc(fmt_num(end))}" '
                f'data-lane="{esc(lane_label)}" data-duration="{esc(fmt_num(duration))}" '
                f'data-color="{st.solid}" data-r="{fmt_num(3.5)}" data-r-hover="{fmt_num(6)}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}"'
            )

            if sp.milestone:
                h = bar_thickness / 2
                points = f"{cx:.1f},{cy - h:.1f} {cx + h:.1f},{cy:.1f} {cx:.1f},{cy + h:.1f} {cx - h:.1f},{cy:.1f}"
                p.append(f'<polygon class="sc-milestone sc-point" {data_attrs} points="{points}" fill="{fill}"/>')
            else:
                if w < 1.0:
                    w = 1.0
                top = cy - bar_thickness / 2
                p.append(
                    f'<rect class="sc-span sc-point" {data_attrs} '
                    f'x="{x_left:.1f}" y="{top:.1f}" width="{w:.1f}" height="{bar_thickness:.1f}" fill="{fill}"/>'
                )

            if sp.dependency:
                for dep_id in sp.dependency:
                    if dep_id in span_index:
                        pred_x, pred_y = span_index[dep_id]
                        this_x = xval(start)
                        this_y = cy
                        mid_x = (pred_x + this_x) / 2
                        ah = 4.0
                        d = (
                            f"M{pred_x:.1f} {pred_y:.1f} "
                            f"L{mid_x:.1f} {pred_y:.1f} "
                            f"L{mid_x:.1f} {this_y:.1f} "
                            f"L{this_x:.1f} {this_y:.1f} "
                            f"M{this_x - ah:.1f} {this_y - ah:.1f} "
                            f"L{this_x:.1f} {this_y:.1f} "
                            f"L{this_x - ah:.1f} {this_y + ah:.1f}"
                        )
                        p.append(
                            f'<path class="sc-dependency" d="{d}" '
                            f'fill="none" stroke="{st.solid}" stroke-width="1" opacity="0.5"/>'
                        )

        p.append("</g>")
