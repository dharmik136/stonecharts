"""Histogram chart renderer: ChartSpec -> SVG string.

Binning transform + contiguous bars on a numeric x-axis. Shared chrome
from _cartesian.py; reuses the LINEAR x-scale from scatter.
"""

from __future__ import annotations

import copy
import math

from ..spec import Axis, ChartSpec
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, render_cartesian


def render_svg(spec: ChartSpec) -> str:
    edges, heights, counts, totals = _compute_bins(spec)
    mod = _prepare_spec(spec, edges, heights)
    return render_cartesian(
        mod, "Histogram", "linear",
        lambda fr, p: _histogram_marks(fr, p, edges, heights, counts, totals, spec),
    )


def _compute_bins(spec):
    if spec.pre_binned:
        edges = [float(e) for e in (spec.x_axis.bin_edges or [])]
        k = len(edges) - 1
        if k <= 0:
            return [0.0, 1.0], [[0.0]], [[0.0]], [0]
        counts = []
        heights = []
        totals = []
        for s in spec.series:
            sc = [0.0] * k
            for b in range(min(k, len(s.data))):
                sc[b] = float(s.data[b])
            counts.append(sc)
            n = sum(sc)
            totals.append(int(n))
            if spec.normalization == "density":
                h = []
                for b in range(k):
                    w = edges[b + 1] - edges[b]
                    nw = n * w
                    h.append(0.0 if nw == 0 else sc[b] / nw)
                heights.append(h)
            else:
                heights.append(list(sc))
        return edges, heights, counts, totals

    all_samples = [float(v) for s in spec.series for v in s.data]
    if not all_samples:
        empty = [[0.0] for _ in spec.series]
        return [0.0, 1.0], empty, empty, [0 for _ in spec.series]

    lo = min(all_samples)
    hi = max(all_samples)
    data_hi = hi
    n_total = len(all_samples)

    bn = spec.binning
    if bn is not None and bn.count is not None:
        k = bn.count
    elif bn is not None and bn.width is not None:
        k = max(1, math.ceil((hi - lo) / bn.width)) if hi > lo else 1
    else:
        k = max(1, math.ceil(math.sqrt(n_total)))

    if bn is not None and bn.width is not None:
        w = bn.width
    else:
        w = (hi - lo) / k if k > 0 and hi > lo else 1.0

    if bn is not None and bn.start is not None and bn.width is not None:
        lo = bn.start

    edges = [lo + w * i for i in range(k + 1)]

    counts = []
    heights = []
    totals = []
    for s in spec.series:
        sc = [0.0] * k
        for v in s.data:
            if v == data_hi:
                b = k - 1
            else:
                b = int(math.floor((float(v) - lo) / w))
                b = max(0, min(k - 1, b))
            sc[b] += 1.0
        counts.append(sc)
        ns = len(s.data)
        totals.append(ns)
        if spec.normalization == "density":
            h = []
            for b in range(k):
                nw = ns * w
                h.append(0.0 if nw == 0 else sc[b] / nw)
            heights.append(h)
        else:
            heights.append(list(sc))

    return edges, heights, counts, totals


def _prepare_spec(spec, edges, heights):
    mod = copy.copy(spec)
    xa = copy.copy(spec.x_axis)
    xa.min = edges[0]
    xa.max = edges[-1]
    mod.x_axis = xa

    all_h = [h for hs in heights for h in hs]
    h_max = max(all_h) if all_h else 1.0

    ya = copy.copy(spec.y_axis)
    if ya.min is None:
        ya.min = 0.0
    if ya.max is None:
        ya.max = h_max
    mod.y_axis = ya

    if spec.overlay == "pareto":
        mod.secondary_y_axis = Axis(title="Cumulative %", min=0.0, max=100.0)

    return mod


def _histogram_marks(fr, p, edges, heights, counts, totals, orig_spec):
    k = len(edges) - 1
    if k <= 0:
        return

    for si, s in enumerate(orig_spec.series):
        st = fr.styles[si]
        baseline = fr.ypix(0.0)
        p.append(f'<g class="sc-series" data-series="{si}">')
        for b in range(k):
            x_left = fr.xpix(edges[b])
            x_right = fr.xpix(edges[b + 1])
            bar_w = x_right - x_left
            h_val = heights[si][b]
            y_top = fr.ypix(h_val)
            bar_h = baseline - y_top
            cx = (x_left + x_right) / 2
            label = f"{fmt_num(edges[b])}–{fmt_num(edges[b + 1])}"
            common = (
                f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                f'data-x="{esc(label)}" data-y="{esc(fmt_num(h_val))}" '
                f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
            )
            p.append(
                f'<rect {common} cx="{cx:.1f}" cy="{y_top:.1f}" x="{x_left:.1f}" y="{y_top:.1f}" '
                f'width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{st.fill}"/>'
            )
        p.append("</g>")

    if orig_spec.overlay == "pareto":
        _emit_pareto(fr, p, edges, counts, totals, orig_spec)
    elif orig_spec.overlay == "bellcurve":
        _emit_bellcurve(fr, p, edges, counts, totals, orig_spec)


def _emit_pareto(fr, p, edges, counts, totals, spec):
    si = len(spec.series)
    k = len(edges) - 1
    color = fr.theme.palette[si % len(fr.theme.palette)]
    total = totals[0]
    if total <= 0:
        return
    cum = 0.0
    pts = []
    for b in range(k):
        cum += counts[0][b]
        pct = 100.0 * cum / total
        cx = fr.xpix((edges[b] + edges[b + 1]) / 2)
        cy = fr.ypix2(pct)
        pts.append((cx, cy))
    if not pts:
        return
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    p.append(f'<g class="sc-series" data-series="{si}">')
    p.append(
        f'<path class="sc-series-line" data-series="{si}" d="{d}" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    for b, (x, y) in enumerate(pts):
        cum_pct = 0.0
        for j in range(b + 1):
            cum_pct += counts[0][j]
        cum_pct = 100.0 * cum_pct / total
        label = f"{fmt_num(edges[b])}–{fmt_num(edges[b + 1])}"
        common = (
            f'class="sc-point" data-series="{si}" data-series-name="{esc("Cumulative %")}" '
            f'data-x="{esc(label)}" data-y="{esc(fmt_num(cum_pct))}" '
            f'data-color="{color}" data-r="3.5" data-r-hover="6"'
        )
        p.append(
            f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" '
            f'stroke="{fr.theme.marker_halo}" stroke-width="1"/>'
        )
    p.append("</g>")


def _emit_bellcurve(fr, p, edges, counts, totals, spec):
    si = len(spec.series)
    k = len(edges) - 1
    color = fr.theme.palette[si % len(fr.theme.palette)]
    all_samples = [float(v) for s in spec.series for v in s.data]
    if not all_samples:
        return
    n = len(all_samples)
    mean = sum(all_samples) / n
    var = sum((v - mean) ** 2 for v in all_samples) / n
    std = math.sqrt(var)
    if std == 0:
        return
    w = (edges[-1] - edges[0]) / k if k > 0 else 1.0
    x_lo = edges[0]
    x_hi = edges[-1]
    n_pts = 200
    pts = []
    for i in range(n_pts):
        x = x_lo + (x_hi - x_lo) * i / (n_pts - 1)
        z = (x - mean) / std
        pdf = math.exp(-z * z / 2) / (std * math.sqrt(2 * math.pi))
        if spec.normalization == "density":
            y = pdf
        else:
            y = n * w * pdf
        px = fr.xpix(x)
        py = fr.ypix(y)
        pts.append((px, py))
    if not pts:
        return
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    p.append(f'<g class="sc-series" data-series="{si}">')
    p.append(
        f'<path class="sc-series-line" data-series="{si}" d="{d}" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    p.append("</g>")
