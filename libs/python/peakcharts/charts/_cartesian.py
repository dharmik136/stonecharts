"""Shared Cartesian chrome: the substrate every Cartesian/XY chart rides.

Extracted verbatim from the line renderer per the §4 extraction contract
(docs/roadmap/chart-families.md). A chart renderer supplies ONLY a marks
function; the frame owns everything else — margins, scales, ticks, gridlines,
axis lines/titles, legend, crosshair, background, <defs>, theme resolution,
the a11y summary, and the <svg> open/close. Per §5's golden rule the marks
callback draws ONLY the inner content of <g class="pk-series">…</g>; it never
re-implements chrome and never computes a scale of its own — the frame owns
the value-axis domain, including the stacking-aware y-max.

The §4.1 load-bearing design fact: the series marks are SANDWICHED between a
chrome "head" and a chrome "tail" (chrome is not one contiguous block).
render_cartesian injects ONE shared accumulator (a Python list `p`) through
head -> marks -> tail so the writes, their order, and the buffer match the
original single-buffer line renderer exactly — byte-identity by construction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from ..spec import ChartSpec, Gradient, GridLine, Pattern, Theme
from ..util import esc, fmt_num, nice_ticks


@dataclass
class SeriesStyle:
    """Resolved per-series paint refs (replaces the ad-hoc tuple in line.py).

    `fill` is the bar paint the extraction adds: populated by the defs
    pre-pass but UNREAD by line marks, so line bytes do not move.

    Caution (§4.3) — the no-area sentinel is per-language: Python uses
    `area_fill: Optional[str]` (None = no area) while Go uses `areaFill string`
    ("" = no area). Safe ONLY while a real fill value is never "" and never a
    meaningful None; new fields must not overload these sentinels.
    """

    stroke: str                 # hex or url(#grad) — the line/edge stroke ref
    solid: str                  # representative solid — markers / legend / data-color
    area_fill: Optional[str]    # None = no area; else hex / url(#grad) / url(#pat)
    area_op: str                # ' fill-opacity="…"' or ''
    fill: str                   # resolved BAR paint: url(#pat) -> url(#grad) -> solid hex


@dataclass
class CartesianFrame:
    """Everything a cartesian chart needs but its marks — built once per render
    by build_frame(). The marks read geometry through xpix / ypix / band_width
    and never recompute a scale (§5.2)."""

    spec: ChartSpec
    W: int
    H: int
    theme: Theme
    plot_x: float
    plot_y: float
    plot_w: float
    plot_h: float
    n: int
    cats: List[str]
    y_min: float
    y_max: float
    y_ticks: List[float]
    cid: str
    styles: List[SeriesStyle]
    defs_parts: List[str]
    a11y_attr: str
    a11y_desc: str
    scale: str                       # "point" | "band"
    include_zero: bool               # value-axis zero-anchor (see build_frame)
    stacking: Optional[str]          # None | "normal" | "percent" — frame owns stacked y-domain

    def xpix(self, i: int) -> float:
        """Category index -> pixel x, per the frame's x-scale strategy.

        POINT scale (line/area) — the original line formula, verbatim:
            xpix(i) = plot_x + plot_w*i/(n-1),  and  plot_x + plot_w/2  when n<=1
        BAND scale (column/bar) — §4.3 pinned formula, this operation order:
            xpix(i) = plot_x + band_width()*i + band_width()/2   (band center)
        """
        if self.scale == "band":
            return self.plot_x + self.band_width() * i + self.band_width() / 2
        if self.n <= 1:
            return self.plot_x + self.plot_w / 2
        return self.plot_x + self.plot_w * i / (self.n - 1)

    def ypix(self, v: float) -> float:
        return self.plot_y + self.plot_h * (1 - (v - self.y_min) / (self.y_max - self.y_min))

    def band_width(self) -> float:
        """BAND scale only — the per-category slot width. PINNED: plot_w / n."""
        return self.plot_w / self.n


# A chart supplies ONLY this: append its marks for one plot into the accumulator p.
MarksFn = Callable[[CartesianFrame, List[str]], None]


def a11y_summary(spec: ChartSpec, chart_noun: str) -> str:
    """Screen-reader summary: title (if any), series names, category range.
    `chart_noun` is the BARE word ("Line", "Column") — called with "Line" it
    reproduces "Line chart with N series…" byte-for-byte."""
    names = ", ".join(s.name for s in spec.series)
    parts = []
    if spec.title:
        parts.append(f"{spec.title}.")
    parts.append(f"{chart_noun} chart with {len(spec.series)} series: {names}.")
    if spec.x_axis.categories:
        c = spec.x_axis.categories
        parts.append(f"Categories from {c[0]} to {c[-1]}.")
    return " ".join(parts)


def gradient_def(gid: str, g: Gradient) -> str:
    """<linearGradient> def. Direction is x1,y1->x2,y2 (objectBoundingBox)."""
    stops = []
    for st in g.stops:
        op = f' stop-opacity="{fmt_num(st.opacity)}"' if st.opacity is not None else ""
        stops.append(f'<stop offset="{fmt_num(st.offset)}" stop-color="{esc(st.color)}"{op}/>')
    return (
        f'<linearGradient id="{gid}" x1="{fmt_num(g.x1)}" y1="{fmt_num(g.y1)}" '
        f'x2="{fmt_num(g.x2)}" y2="{fmt_num(g.y2)}">' + "".join(stops) + "</linearGradient>"
    )


def pattern_def(pid: str, pat: Pattern) -> str:
    """<pattern> def: a diagonal hatch tile (userSpaceOnUse, rotated)."""
    sz = fmt_num(pat.size)
    bg = (
        f'<rect width="{sz}" height="{sz}" fill="{esc(pat.background)}"/>'
        if pat.background else ""
    )
    hatch = (
        f'<line x1="0" y1="0" x2="0" y2="{sz}" stroke="{esc(pat.color)}" '
        f'stroke-width="{fmt_num(pat.stroke_width)}"/>'
    )
    return (
        f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{sz}" height="{sz}" '
        f'patternTransform="rotate({fmt_num(pat.angle)})">' + bg + hatch + "</pattern>"
    )


# dashStyle name -> SVG stroke-dasharray value ("" = solid, no attribute).
# Lives ONCE here (§4.7 #4): gridline chrome and the series-line mark call the
# SAME function so "5 5"/"2 3" can't drift. line imports it from here.
_DASH = {"dashed": "5 5", "dotted": "2 3"}


def dash_array(style: str) -> str:
    return _DASH.get(style, "")


def build_frame(spec: ChartSpec, chart_noun: str, x_scale: str = "point",
                include_zero: bool = True) -> CartesianFrame:
    """The §4.2 "frame build" phase: margins, plot rect, n/cats, the value-axis
    range + nice_ticks, and the <defs> pre-pass resolving each SeriesStyle
    (stroke, solid, area_fill, area_op, fill) + cid + defs_parts + the a11y
    summary (parameterized by chart_noun).

    include_zero (PINNED, §3.2 caveat / §4.2):
        True  -> value axis / y baseline (line/column/bar/area): force 0 into
                 the domain — min(values + [0.0]) / max(values + [0.0]). Line
                 passes True and this reproduces its existing domain exactly.
        False -> free numeric x/y (scatter/bubble): domain from the data only.

    Stacked y-domain (frame-owned, §4.2): for stacking "normal"/"percent" the
    y-max comes from the max category TOTAL (cumulative in the pinned summation
    order — series index order), NOT the per-datum max; percent mode's axis
    becomes nice_ticks(0, 100). The marks never recompute a scale.
    """
    W, H = spec.width, spec.height
    theme = spec.theme
    palette = theme.palette
    a11y_attr = ""
    a11y_desc = ""
    if spec.a11y:
        _sum = esc(a11y_summary(spec, chart_noun))
        a11y_attr = f' role="img" aria-label="{_sum}"'
        a11y_desc = f"<desc>{_sum}</desc>"

    # Margins adapt to which chrome is present.
    m_top = 20
    if spec.title:
        m_top += 26
    if spec.subtitle:
        m_top += 18
    m_left = 62 if spec.y_axis.title else 52
    m_right = 22
    m_bottom = 46 + (18 if spec.legend else 0) + (18 if spec.x_axis.title else 0)

    plot_x, plot_y = m_left, m_top
    plot_w, plot_h = W - m_left - m_right, H - m_top - m_bottom

    # X categories (labels). Numeric fallback to index.
    n = max((len(s.data) for s in spec.series), default=0)
    cats = spec.x_axis.categories or [str(i) for i in range(n)]

    # Value-axis domain — owned by the frame, never by the marks.
    stacking = spec.stacking
    if stacking in ("normal", "percent"):
        # Per-category totals, accumulated in series index order (pinned).
        totals = [0.0] * n
        for s in spec.series:
            for i, v in enumerate(s.data):
                totals[i] += v
        if stacking == "percent":
            lo = spec.y_axis.min if spec.y_axis.min is not None else 0.0
            hi = spec.y_axis.max if spec.y_axis.max is not None else 100.0
        else:
            lo = spec.y_axis.min if spec.y_axis.min is not None else min(totals + [0.0])
            hi = spec.y_axis.max if spec.y_axis.max is not None else max(totals + [0.0])
    else:
        # Y range across all series; include_zero=True anchors the 0 baseline.
        values = [v for s in spec.series for v in s.data]
        if include_zero:
            lo = spec.y_axis.min if spec.y_axis.min is not None else min(values + [0.0])
            hi = spec.y_axis.max if spec.y_axis.max is not None else max(values + [0.0])
        else:
            lo = spec.y_axis.min if spec.y_axis.min is not None else (min(values) if values else 0.0)
            hi = spec.y_axis.max if spec.y_axis.max is not None else (max(values) if values else 0.0)
    y_min, y_max, y_ticks = nice_ticks(lo, hi)

    # Resolve per-series styling and collect <defs> (gradients/patterns). Defs are
    # emitted ONLY when something needs them, so default output stays byte-identical.
    cid = esc(spec.id)  # namespaces <defs> ids; escaped so a hostile id can't inject
    defs_parts: List[str] = []
    styles: List[SeriesStyle] = []
    for si, s in enumerate(spec.series):
        if isinstance(s.color, Gradient):
            gid = f"{cid}-grad-{si}"
            defs_parts.append(gradient_def(gid, s.color))
            ref = f"url(#{gid})"
            stroke = ref
            fill_color = ref
            solid = esc(s.color.stops[0].color) if s.color.stops else esc(palette[si % len(palette)])
        elif s.color:
            stroke = fill_color = solid = esc(s.color)
        else:
            stroke = fill_color = solid = esc(palette[si % len(palette)])
        if s.pattern is not None:
            pid = f"{cid}-pat-{si}"
            defs_parts.append(pattern_def(pid, s.pattern))
            area_fill: Optional[str] = f"url(#{pid})"
            area_op = ""
            fill = f"url(#{pid})"     # bar paint: pattern wins
        elif s.fill_opacity > 0:
            area_fill = fill_color
            area_op = f' fill-opacity="{fmt_num(s.fill_opacity)}"'
            fill = fill_color         # bar paint: url(#grad) or solid hex
        else:
            area_fill = None
            area_op = ""
            fill = fill_color         # bar paint: url(#grad) or solid hex
        styles.append(SeriesStyle(stroke, solid, area_fill, area_op, fill))

    return CartesianFrame(
        spec=spec, W=W, H=H, theme=theme,
        plot_x=plot_x, plot_y=plot_y, plot_w=plot_w, plot_h=plot_h,
        n=n, cats=cats,
        y_min=y_min, y_max=y_max, y_ticks=y_ticks,
        cid=cid, styles=styles, defs_parts=defs_parts,
        a11y_attr=a11y_attr, a11y_desc=a11y_desc,
        scale=x_scale, include_zero=include_zero, stacking=stacking,
    )


def _chrome_head(fr: CartesianFrame, p: List[str]) -> None:
    """§4.1 HEAD — write into p, in place, in emission order: <svg> open,
    <desc>, <defs>, background rect, title + subtitle, y gridlines + labels,
    axis line, x labels, axis titles (x + rotated y), crosshair."""
    spec, theme = fr.spec, fr.theme
    W, H = fr.W, fr.H
    plot_x, plot_y, plot_w, plot_h = fr.plot_x, fr.plot_y, fr.plot_w, fr.plot_h
    n, cats, y_ticks = fr.n, fr.cats, fr.y_ticks
    a11y_attr, a11y_desc, defs_parts = fr.a11y_attr, fr.a11y_desc, fr.defs_parts
    xpix, ypix = fr.xpix, fr.ypix

    _font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    if spec.responsive:
        p.append(
            f'<svg class="pk-chart"{a11y_attr} xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
            f'width="100%" {_font}>'
        )
    else:
        p.append(
            f'<svg class="pk-chart"{a11y_attr} xmlns="http://www.w3.org/2000/svg" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" {_font}>'
        )

    # Accessible description (screen readers; role="img" makes the chart one image).
    if a11y_desc:
        p.append(a11y_desc)

    # Gradient / pattern defs (only present when a series needs them).
    if defs_parts:
        p.append("<defs>" + "".join(defs_parts) + "</defs>")

    # Background (only when the theme sets one; light theme -> none).
    if theme.background:
        p.append(
            f'<rect class="pk-bg" x="0" y="0" width="{W}" height="{H}" fill="{theme.background}"/>'
        )

    # Titles.
    ty = 26
    if spec.title:
        p.append(
            f'<text class="pk-title" x="{W/2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="17" font-weight="600" fill="{theme.title_color}">{esc(spec.title)}</text>'
        )
        ty += 20
    if spec.subtitle:
        p.append(
            f'<text class="pk-subtitle" x="{W/2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="12" fill="{theme.subtitle_color}">{esc(spec.subtitle)}</text>'
        )

    # Y gridlines + labels. Defaults reproduce the built-in look byte-for-byte.
    gl = spec.y_axis.grid_line or GridLine()
    grid_color = gl.color or theme.grid_color
    grid_dash = dash_array(gl.dash_style)
    dash_attr = f' stroke-dasharray="{grid_dash}"' if grid_dash else ''
    p.append('<g class="pk-axis pk-axis-y">')
    for tv in y_ticks:
        gy = ypix(tv)
        if gl.enabled:
            p.append(
                f'<line class="pk-gridline" x1="{plot_x:.1f}" y1="{gy:.1f}" '
                f'x2="{plot_x+plot_w:.1f}" y2="{gy:.1f}" stroke="{grid_color}" '
                f'stroke-width="1"{dash_attr}/>'
            )
        p.append(
            f'<text x="{plot_x-8:.1f}" y="{gy+4:.1f}" text-anchor="end" '
            f'font-size="11" fill="{theme.axis_label_color}">{esc(fmt_num(tv))}</text>'
        )
    p.append("</g>")

    # Axis lines.
    p.append(
        f'<line class="pk-axis-line" x1="{plot_x:.1f}" y1="{plot_y+plot_h:.1f}" '
        f'x2="{plot_x+plot_w:.1f}" y2="{plot_y+plot_h:.1f}" stroke="{theme.axis_line_color}" stroke-width="1"/>'
    )

    # X labels.
    p.append('<g class="pk-axis pk-axis-x">')
    for i, label in enumerate(cats[:n]):
        lx = xpix(i)
        p.append(
            f'<text x="{lx:.1f}" y="{plot_y+plot_h+18:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{theme.axis_label_color}">{esc(label)}</text>'
        )
    p.append("</g>")

    # Axis titles.
    if spec.x_axis.title:
        p.append(
            f'<text x="{plot_x+plot_w/2:.1f}" y="{H-6}" text-anchor="middle" '
            f'font-size="12" fill="{theme.axis_title_color}">{esc(spec.x_axis.title)}</text>'
        )
    if spec.y_axis.title:
        yc = plot_y + plot_h / 2
        p.append(
            f'<text x="14" y="{yc:.1f}" text-anchor="middle" font-size="12" '
            f'fill="{theme.axis_title_color}" transform="rotate(-90 14 {yc:.1f})">{esc(spec.y_axis.title)}</text>'
        )

    # Crosshair (hidden until a point is hovered; driven by the JS runtime).
    p.append(
        f'<line class="pk-crosshair" x1="0" y1="{plot_y:.1f}" x2="0" y2="{plot_y+plot_h:.1f}" '
        f'stroke="{theme.crosshair_color}" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>'
    )


def _chrome_tail(fr: CartesianFrame, p: List[str]) -> None:
    """§4.1 TAIL — write into p, in place: legend (bottom-center), </svg>.
    No trailing newline."""
    spec, theme = fr.spec, fr.theme
    H = fr.H
    plot_x, plot_w = fr.plot_x, fr.plot_w

    # Legend (bottom center).
    if spec.legend and spec.series:
        gap = 22
        est = [len(s.name) * 7 + 26 for s in spec.series]
        total = sum(est) + gap * (len(spec.series) - 1)
        lx = plot_x + (plot_w - total) / 2
        ly = H - (10 + (18 if spec.x_axis.title else 0))
        p.append('<g class="pk-legend">')
        for si, s in enumerate(spec.series):
            color = fr.styles[si].solid
            p.append(f'<g class="pk-legend-item" data-series="{si}">')
            p.append(
                f'<rect x="{lx:.1f}" y="{ly-9:.1f}" width="14" height="4" rx="2" fill="{color}"/>'
            )
            p.append(
                f'<text x="{lx+20:.1f}" y="{ly-2:.1f}" font-size="12" fill="{theme.legend_text_color}">{esc(s.name)}</text>'
            )
            p.append("</g>")
            lx += est[si] + gap
        p.append("</g>")

    p.append("</svg>")


def render_cartesian(spec: ChartSpec, chart_noun: str, x_scale: str, marks: MarksFn,
                     include_zero: bool = True) -> str:
    """Orchestrate head -> (chart's marks) -> tail through ONE shared
    accumulator p. Returns a single "".join(p) with NO trailing newline."""
    fr = build_frame(spec, chart_noun, x_scale, include_zero)
    p: List[str] = []
    _chrome_head(fr, p)
    marks(fr, p)          # chart appends its <g class="pk-series">…</g> blocks here
    _chrome_tail(fr, p)
    return "".join(p)     # single "".join, NO trailing newline
