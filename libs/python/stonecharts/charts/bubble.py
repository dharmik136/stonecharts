"""Bubble chart renderer: ChartSpec -> SVG string.

Unconnected circles at (x, y) on the same free numeric x/y plane scatter
already rides (§3.3 Rank 4 of docs/roadmap/chart-families.md); the one net-new
piece is the size-scale (z -> area-proportional radius). No shared-frame
changes are needed at all — this module supplies only the marks callback,
exactly like bar's admission, not scatter's.
"""

from __future__ import annotations

import math

from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian

RMIN = 4.0
RMAX = 32.0


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _size_scale(z: float, zmin: float, zmax: float) -> float:
    """Pinned size-scale geometry (§3.2 "Size scale"; §3.3 Rank 4). Evaluated
    in this exact order in both languages: check the degenerate domain BEFORE
    any divide, clamp01 BEFORE sqrt."""
    if zmax <= zmin:
        return (RMIN + RMAX) / 2
    t = _clamp01((z - zmin) / (zmax - zmin))
    return RMIN + (RMAX - RMIN) * math.sqrt(t)


def render_svg(spec) -> str:
    return render_cartesian(spec, "Bubble", "linear", _bubble_marks, include_zero=False)


def _bubble_marks(fr: CartesianFrame, p: list) -> None:
    # Global z-domain: reduced over EVERY point of EVERY series, in
    # series-index order then point order, so a given z maps to the same
    # radius everywhere (bubbles stay comparable across series).
    zmin = zmax = 0.0
    first = True
    for s in fr.spec.series:
        for d in s.data_points or []:
            z = d.z if d.z is not None else 0.0
            if first:
                zmin = zmax = z
                first = False
                continue
            if z < zmin:
                zmin = z
            if z > zmax:
                zmax = z

    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        # Bubble reinterprets fillOpacity: line's default (0.0) means "no
        # fill" there, but an unfilled bubble is a broken chart (NN#2), so
        # the pinned bubble default is 0.65, not 0.
        op = s.fill_opacity if s.fill_opacity > 0 else 0.65
        p.append(f'<g class="sc-series" data-series="{si}">')
        for d in s.data_points or []:
            z = d.z if d.z is not None else 0.0
            x, y = fr.xpix(d.x), fr.ypix(d.y)
            r = _size_scale(z, zmin, zmax)
            p.append(
                f'<circle class="sc-bubble sc-point" data-series="{si}" '
                f'data-series-name="{esc(s.name)}" data-x="{esc(fmt_num(d.x))}" '
                f'data-y="{esc(fmt_num(d.y))}" data-z="{esc(fmt_num(z))}" '
                f'data-color="{st.solid}" data-r="{fmt_num(r)}" data-r-hover="{fmt_num(r)}" '
                f'cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(r)}" '
                f'fill="{st.fill}" fill-opacity="{fmt_num(op)}"/>'
            )
        p.append("</g>")
