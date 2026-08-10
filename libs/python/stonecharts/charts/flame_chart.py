"""Flame chart (time-ordered) renderer: ChartSpec -> SVG string.

Per-thread stack frames over wall-clock time, drawn as horizontal floating
bars at [start, end] per depth level. Depth 0 = root at bottom, increasing
upward. Rides the shared cartesian frame with orientation="horizontal",
x_scale="band", include_zero=False.
"""

from __future__ import annotations

from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


def render_svg(spec) -> str:
    max_depth = 0
    all_times: list[float] = []
    for s in spec.series:
        for fr in s.frames or []:
            if fr.depth > max_depth:
                max_depth = fr.depth
            all_times.append(fr.x)
            all_times.append(fr.x2)

    depth_cats = [str(d) for d in range(max_depth + 1)]
    spec.x_axis.categories = depth_cats

    for s in spec.series:
        while len(s.data) < len(depth_cats):
            s.data.append(0.0)

    if spec.y_axis.min is None:
        spec.y_axis.min = spec.x_axis.min if spec.x_axis.min is not None else (min(all_times) if all_times else 0.0)
    if spec.y_axis.max is None:
        spec.y_axis.max = spec.x_axis.max if spec.x_axis.max is not None else (max(all_times) if all_times else 0.0)

    return render_cartesian(spec, "Flame chart", "band", _flame_marks, include_zero=False, orientation="horizontal")


PAD = 0.2
LABEL_MIN_PX = 40
CHAR_WIDTH = 6.5


def _flame_marks(fr: CartesianFrame, p: list[str]) -> None:
    if fr.n <= 0:
        return

    lane_height = fr.plot_h / fr.n
    bar_thickness = lane_height * (1 - PAD)

    def ypix_band(depth: int) -> float:
        inverted = fr.n - 1 - depth
        return fr.plot_y + lane_height * inverted + lane_height / 2

    def xval(v: float) -> float:
        return fr.value_pix(v)

    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        fill = st.fill

        p.append(f'<g class="sc-series" data-series="{si}">')

        for frame in s.frames or []:
            start = frame.x
            end = frame.x2
            depth = frame.depth
            name = frame.name or ""

            frame_fill = fill
            if frame.color:
                frame_fill = frame.color

            x_left = xval(min(start, end))
            x_right = xval(max(start, end))
            w = x_right - x_left
            if w < 1.0:
                w = 1.0
            cy = ypix_band(depth)
            cx = xval((start + end) / 2)
            top = cy - bar_thickness / 2

            duration = end - start
            depth_label = str(depth)

            data_attrs = (
                f'class="sc-frame sc-point" '
                f'data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(depth_label)}" data-y="{esc(fmt_num(start))}" '
                f'data-start="{esc(fmt_num(start))}" data-end="{esc(fmt_num(end))}" '
                f'data-depth="{depth}" data-name="{esc(name)}" '
                f'data-duration="{esc(fmt_num(duration))}" '
                f'data-color="{esc(frame_fill)}" data-r="{fmt_num(3.5)}" data-r-hover="{fmt_num(6)}" '
                f'cx="{cx:.1f}" cy="{cy:.1f}"'
            )

            p.append(
                f"<rect {data_attrs} "
                f'x="{x_left:.1f}" y="{top:.1f}" width="{w:.1f}" height="{bar_thickness:.1f}" fill="{esc(frame_fill)}"/>'
            )

            if name and w >= LABEL_MIN_PX:
                max_chars = int(w / CHAR_WIDTH)
                label = name
                if len(label) > max_chars:
                    label = label[: max(max_chars - 1, 0)] + "…"
                label_y = cy + 3.5
                p.append(
                    f'<text class="sc-frame-label" x="{cx:.1f}" y="{label_y:.1f}" '
                    f'text-anchor="middle" font-size="10" fill="#ffffff">{esc(label)}</text>'
                )

        p.append("</g>")
