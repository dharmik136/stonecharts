"""Histogram chart renderer: ChartSpec -> SVG string.

This chart derives bin counts from raw samples or pre-binned data, then reuses
shared cartesian chrome for the actual SVG. The output stays byte-stable across
Python and Go by keeping the binning math and overlay math in lockstep.
"""
from __future__ import annotations

import math
from dataclasses import replace
from typing import List, Optional, Tuple

from ..spec import Axis, ChartSpec, Series
from ..util import esc, fmt_num, nice_ticks
from ._cartesian import CartesianFrame, render_cartesian
from .line import _marker as _line_marker, _path_d, _spline_d


def _series_kind(s: Series) -> str:
    return getattr(s, 'type', 'column') or 'column'


def _binning_params(spec: ChartSpec, values: List[float]) -> Tuple[List[float], List[float]]:
    if not values:
        return [0.0, 1.0], [0.0]
    lo = min(values)
    hi = max(values)
    if spec.pre_binned and spec.x_axis.bin_edges:
        edges = [float(v) for v in spec.x_axis.bin_edges]
        return edges, [0.0] * (len(edges) - 1)
    if spec.binning and spec.binning.width is not None:
        width = float(spec.binning.width)
        if width <= 0:
            width = 1.0
        start = float(spec.binning.start) if spec.binning.start is not None else lo
        count = max(1, int(math.ceil((hi - start) / width)))
        edges = [start + width * i for i in range(count + 1)]
        return edges, [0.0] * count
    if spec.binning and spec.binning.count is not None:
        count = max(1, int(spec.binning.count))
    else:
        count = max(1, int(math.ceil(math.sqrt(len(values)))))
    width = (hi - lo) / count if count > 0 else 1.0
    if width == 0:
        width = 1.0
    edges = [lo + width * i for i in range(count + 1)]
    return edges, [0.0] * count


def _assign_counts(values: List[float], edges: List[float]) -> List[float]:
    if len(edges) < 2:
        return [0.0]
    count = len(edges) - 1
    lo = edges[0]
    hi = edges[-1]
    width = edges[1] - edges[0]
    if width == 0:
        width = 1.0
    bins = [0.0] * count
    for v in values:
        if v == hi:
            bins[count - 1] += 1.0
            continue
        idx = int(math.floor((v - lo) / width))
        if idx < 0:
            idx = 0
        if idx >= count:
            idx = count - 1
        bins[idx] += 1.0
    return bins


def _density(counts: List[float], total: float, edges: List[float]) -> List[float]:
    vals = []
    for i, c in enumerate(counts):
        w = edges[i + 1] - edges[i]
        if total == 0.0 or w == 0.0:
            vals.append(0.0)
        else:
            vals.append(c / (total * w))
    return vals


def _labels(edges: List[float]) -> List[str]:
    return [f"{fmt_num(edges[i])}–{fmt_num(edges[i + 1])}" for i in range(len(edges) - 1)]


def _bellcurve(values: List[float], edges: List[float], base_counts: List[float], density: bool) -> List[float]:
    if not values:
        return [0.0] * (len(edges) - 1)
    n = float(len(values))
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    if var <= 0:
        return [0.0] * (len(edges) - 1)
    sigma = math.sqrt(var)
    if sigma == 0:
        return [0.0] * (len(edges) - 1)
    scale = 1.0 if density else (n * ((edges[-1] - edges[0]) / max(1, len(edges) - 1)))
    out = []
    for i in range(len(edges) - 1):
        x = (edges[i] + edges[i + 1]) / 2.0
        z = (x - mean) / sigma
        pdf = math.exp(-0.5 * z * z) / (sigma * math.sqrt(2.0 * math.pi))
        out.append(pdf * scale)
    return out


def _histogram_spec(spec: ChartSpec) -> ChartSpec:
    raw_values = [v for s in spec.series for v in s.data]
    edges, _ = _binning_params(spec, raw_values)
    labels = _labels(edges)
    derived_series: List[Series] = []
    all_counts: List[float] = [0.0] * (len(edges) - 1)
    for i, s in enumerate(spec.series):
        if spec.pre_binned and spec.x_axis.bin_edges:
            counts = [float(v) for v in s.data[: len(edges) - 1]]
        else:
            counts = _assign_counts(s.data, edges)
        if spec.normalization == 'density':
            counts = _density(counts, float(len(s.data)), edges)
        derived_series.append(replace(s, data=counts, type='column'))
        all_counts = [a + b for a, b in zip(all_counts, counts)]
    overlay = (spec.overlay or '').strip()
    secondary = spec.secondary_y_axis
    if overlay == 'pareto':
        cumulative = 0.0
        pct = []
        total = sum(all_counts) or 1.0
        for c in all_counts:
            cumulative += c
            pct.append(cumulative / total * 100.0)
        derived_series.append(Series(name='Pareto', data=pct, type='line', y_axis=1))
        if secondary is None:
            secondary = Axis(title='Percent', min=0.0, max=100.0, opposite=True)
    elif overlay == 'bellcurve':
        bell = _bellcurve(raw_values, edges, all_counts, spec.normalization == 'density')
        derived_series.append(Series(name='Bell curve', data=bell, type='line'))
    derived = replace(spec, series=derived_series, secondary_y_axis=secondary, x_axis=replace(spec.x_axis, categories=labels))
    return derived


def render_svg(spec) -> str:
    return render_cartesian(_histogram_spec(spec), 'Histogram', 'band', _histogram_marks)


def _histogram_marks(fr: CartesianFrame, p: List[str]) -> None:
    # Bars are contiguous bands; any line overlay is rendered as a normal line series.
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        kind = _series_kind(s)
        p.append(f'<g class="sc-series" data-series="{si}">')
        if kind == 'line':
            pts = [(fr.xpix(i), fr.ypix2(v) if s.y_axis == 1 and fr.secondary_axis is not None else fr.ypix(v)) for i, v in enumerate(s.data)]
            d = _spline_d(pts) if s.curve == 'monotone' else _path_d(pts, s.step)
            p.append(f'<path class="sc-series-line" data-series="{si}" d="{d}" fill="none" stroke="{st.stroke}" stroke-width="{fmt_num(s.line_width or 2)}" stroke-linejoin="round" stroke-linecap="round"/>')
            mk = s.marker or None
            if mk is not None and mk.enabled:
                radius = mk.radius
                radius_hover = radius + 2.5
                for i, (x, y) in enumerate(pts):
                    xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                    common = (
                        f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                        f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" '
                        f'data-color="{st.solid}" data-r="{fmt_num(radius)}" data-r-hover="{fmt_num(radius_hover)}"'
                    )
                    p.append(_line_marker(mk.symbol, x, y, radius, common, st.solid, fr.theme.marker_halo))
        else:
            bar_w = fr.band_width()
            for i, v in enumerate(s.data):
                cx = fr.xpix(i)
                x = cx - bar_w / 2
                top = fr.ypix(v)
                base = fr.ypix(0.0)
                y = min(base, top)
                h = abs(base - top)
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-bar sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(v))}" '
                    f'data-color="{st.solid}" data-r="3.5" data-r-hover="6"'
                )
                p.append(
                    f'<rect {common} cx="{cx:.1f}" cy="{top:.1f}" x="{x:.1f}" y="{y:.1f}" '
                    f'width="{bar_w:.1f}" height="{h:.1f}" fill="{st.fill}"/>'
                )
        p.append('</g>')
