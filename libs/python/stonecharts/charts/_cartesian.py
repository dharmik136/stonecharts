"""Shared Cartesian chrome: the substrate every Cartesian/XY chart rides.

Extracted verbatim from the line renderer per the §4 extraction contract
(docs/roadmap/chart-families.md). A chart renderer supplies ONLY a marks
function; the frame owns everything else — margins, scales, ticks, gridlines,
axis lines/titles, legend, crosshair, background, <defs>, theme resolution,
the a11y summary, and the <svg> open/close. Per §5's golden rule the marks
callback draws ONLY the inner content of <g class="sc-series">…</g>; it never
re-implements chrome and never computes a scale of its own — the frame owns
the value-axis domain, including the stacking-aware y-max.

The §4.1 load-bearing design fact: the series marks are SANDWICHED between a
chrome "head" and a chrome "tail" (chrome is not one contiguous block).
render_cartesian injects ONE shared accumulator (a Python list `p`) through
head -> marks -> tail so the writes, their order, and the buffer match the
original single-buffer line renderer exactly — byte-identity by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ..spec import Axis, ChartSpec, Gradient, GridLine, Pattern, Theme
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

    stroke: str  # hex or url(#grad) — the line/edge stroke ref
    solid: str  # representative solid — markers / legend / data-color
    area_fill: str | None  # None = no area; else hex / url(#grad) / url(#pat)
    area_op: str  # ' fill-opacity="…"' or ''
    fill: str  # resolved BAR paint: url(#pat) -> url(#grad) -> solid hex


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
    cats: list[str]
    y_min: float
    y_max: float
    y_ticks: list[float]
    cid: str
    styles: list[SeriesStyle]
    defs_parts: list[str]
    a11y_attr: str
    a11y_desc: str
    scale: str  # "point" | "band" | "linear"
    include_zero: bool  # value-axis zero-anchor (see build_frame)
    orientation: str  # "vertical" | "horizontal"
    stacking: str | None  # None | "normal" | "percent" — frame owns stacked y-domain
    secondary_axis: Axis | None = None
    y2_min: float = 0.0
    y2_max: float = 0.0
    y2_ticks: list[float] = field(default_factory=list)
    x_min: float = 0.0  # LINEAR scale only (scatter) — free numeric x-domain
    x_max: float = 0.0
    x_ticks: list[float] = field(default_factory=list)

    def xpix(self, i: float) -> float:
        """Category index (or, under LINEAR scale, a numeric x-VALUE) -> pixel x.

        LINEAR scale (scatter, §3.3 Rank 3) — a free numeric x-domain, mirrors
        ypix exactly: xpix(v) = plot_x + plot_w*(v - x_min)/(x_max - x_min).
        Degenerate domain (x_max == x_min) is pinned to plot center BEFORE the
        divide, identically to value_pix's existing y-degenerate guard.
        POINT scale (line/area) — the original line formula, verbatim:
            xpix(i) = plot_x + plot_w*i/(n-1),  and  plot_x + plot_w/2  when n<=1
        BAND scale (column/bar) — §4.3 pinned formula, this operation order:
            xpix(i) = plot_x + band_width()*i + band_width()/2   (band center)
        """
        if self.scale == "linear":
            if self.x_max == self.x_min:
                return self.plot_x + self.plot_w / 2
            return self.plot_x + self.plot_w * (i - self.x_min) / (self.x_max - self.x_min)
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

    def band_height(self) -> float:
        """BAND scale only — the per-category slot height for horizontal charts."""
        return self.plot_h / self.n

    def band_center(self, i: int) -> float:
        if self.orientation == "horizontal":
            return self.plot_y + self.band_height() * i + self.band_height() / 2
        return self.xpix(i)

    def value_pix(self, v: float) -> float:
        if self.orientation == "horizontal":
            if self.y_max == self.y_min:
                return self.plot_x + self.plot_w / 2
            return self.plot_x + self.plot_w * (v - self.y_min) / (self.y_max - self.y_min)
        return self.ypix(v)

    def value_zero(self) -> float:
        return self.value_pix(0.0)

    def ypix2(self, v: float) -> float:
        if self.y2_max == self.y2_min:
            return self.plot_y + self.plot_h / 2
        return self.plot_y + self.plot_h * (1 - (v - self.y2_min) / (self.y2_max - self.y2_min))


# A chart supplies ONLY this: append its marks for one plot into the accumulator p.
MarksFn = Callable[[CartesianFrame, list[str]], None]


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
    bg = f'<rect width="{sz}" height="{sz}" fill="{esc(pat.background)}"/>' if pat.background else ""
    hatch = (
        f'<line x1="0" y1="0" x2="0" y2="{sz}" stroke="{esc(pat.color)}" stroke-width="{fmt_num(pat.stroke_width)}"/>'
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


def build_frame(
    spec: ChartSpec, chart_noun: str, x_scale: str = "point", include_zero: bool = True, orientation: str = "vertical"
) -> CartesianFrame:
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

    # Margins adapt to which chrome is present unless a validated manual layout
    # margin overrides the deterministic default for that edge.
    m_top: float = 20
    if spec.title:
        m_top += 26
    if spec.subtitle:
        m_top += 18
    m_left: float = 62 if spec.y_axis.title else 52
    has_secondary = spec.secondary_y_axis is not None
    sec = spec.secondary_y_axis
    m_right: float = 62 if sec is not None and sec.title else (52 if has_secondary else 22)
    m_bottom: float = 46 + (18 if spec.legend else 0) + (18 if spec.x_axis.title else 0)
    if spec.layout and spec.layout.margin:
        m = spec.layout.margin
        if m.top is not None:
            m_top = m.top
        if m.left is not None:
            m_left = m.left
        if m.right is not None:
            m_right = m.right
        if m.bottom is not None:
            m_bottom = m.bottom

    plot_x, plot_y = m_left, m_top
    plot_w, plot_h = W - m_left - m_right, H - m_top - m_bottom

    # LINEAR scale (scatter, §3.3 Rank 3): series carry point-model data_points
    # instead of a plain number[] — n/values/x-domain extraction branches here,
    # additively, so the ELSE branch below (line/column/area/bar) is byte-for-
    # byte the same code that ran before scatter existed.
    is_point_model = x_scale == "linear"

    # X categories (labels). Numeric fallback to index.
    if is_point_model:
        n = max((len(s.data_points or []) for s in spec.series), default=0)
    else:
        n = max((len(s.data) for s in spec.series), default=0)
    cats = spec.x_axis.categories or [str(i) for i in range(n)]

    x_min = x_max = 0.0
    x_ticks: list[float] = []
    if is_point_model:
        xs = [d.x for s in spec.series for d in (s.data_points or [])]
        x_lo = spec.x_axis.min if spec.x_axis.min is not None else (min(xs) if xs else 0.0)
        x_hi = spec.x_axis.max if spec.x_axis.max is not None else (max(xs) if xs else 0.0)
        x_min, x_max, x_ticks = nice_ticks(x_lo, x_hi)

    # Value-axis domain — owned by the frame, never by the marks.
    stacking = spec.stacking
    if stacking in ("normal", "percent"):
        if stacking == "percent":
            lo = spec.y_axis.min if spec.y_axis.min is not None else 0.0
            hi = spec.y_axis.max if spec.y_axis.max is not None else 100.0
        else:
            pos_totals = [0.0] * n
            neg_totals = [0.0] * n
            for s in spec.series:
                for i, v in enumerate(s.data):
                    if v >= 0:
                        pos_totals[i] += v
                    else:
                        neg_totals[i] += v
            lo = spec.y_axis.min if spec.y_axis.min is not None else min([*neg_totals, 0.0])
            hi = spec.y_axis.max if spec.y_axis.max is not None else max([*pos_totals, 0.0])
    elif is_point_model:
        # Free y-domain (include_zero=False is always passed for scatter).
        values = [d.y for s in spec.series for d in (s.data_points or [])]
        lo = spec.y_axis.min if spec.y_axis.min is not None else (min(values) if values else 0.0)
        hi = spec.y_axis.max if spec.y_axis.max is not None else (max(values) if values else 0.0)
    else:
        # Y range across all series; include_zero=True anchors the 0 baseline.
        values = [v for s in spec.series for v in s.data]
        for s in spec.series:
            low = getattr(s, "low", None)
            if low is not None:
                values.extend(low)
            high = getattr(s, "high", None)
            if high is not None:
                values.extend(high)
        if include_zero:
            lo = spec.y_axis.min if spec.y_axis.min is not None else min([*values, 0.0])
            hi = spec.y_axis.max if spec.y_axis.max is not None else max([*values, 0.0])
        else:
            lo = spec.y_axis.min if spec.y_axis.min is not None else (min(values) if values else 0.0)
            hi = spec.y_axis.max if spec.y_axis.max is not None else (max(values) if values else 0.0)
    y_min, y_max, y_ticks = nice_ticks(lo, hi)

    # Secondary y-axis domain (combo dual-axis).
    y2_min = y2_max = 0.0
    y2_ticks: list[float] = []
    if has_secondary and sec is not None:
        y2_values = [v for s in spec.series if s.y_axis == 1 for v in s.data]
        y2_lo = sec.min if sec.min is not None else min([*y2_values, 0.0])
        y2_hi = sec.max if sec.max is not None else max([*y2_values, 0.0])
        y2_min, y2_max, y2_ticks = nice_ticks(y2_lo, y2_hi)

    # Resolve per-series styling and collect <defs> (gradients/patterns). Defs are
    # emitted ONLY when something needs them, so default output stays byte-identical.
    cid = esc(spec.id)  # namespaces <defs> ids; escaped so a hostile id can't inject
    defs_parts: list[str] = []
    styles: list[SeriesStyle] = []
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
            area_fill: str | None = f"url(#{pid})"
            area_op = ""
            fill = f"url(#{pid})"  # bar paint: pattern wins
        elif s.fill_opacity > 0:
            area_fill = fill_color
            area_op = f' fill-opacity="{fmt_num(s.fill_opacity)}"'
            fill = fill_color  # bar paint: url(#grad) or solid hex
        else:
            area_fill = None
            area_op = ""
            fill = fill_color  # bar paint: url(#grad) or solid hex
        styles.append(SeriesStyle(stroke, solid, area_fill, area_op, fill))

    return CartesianFrame(
        spec=spec,
        W=W,
        H=H,
        theme=theme,
        plot_x=plot_x,
        plot_y=plot_y,
        plot_w=plot_w,
        plot_h=plot_h,
        n=n,
        cats=cats,
        y_min=y_min,
        y_max=y_max,
        y_ticks=y_ticks,
        cid=cid,
        styles=styles,
        defs_parts=defs_parts,
        a11y_attr=a11y_attr,
        a11y_desc=a11y_desc,
        scale=x_scale,
        include_zero=include_zero,
        orientation=orientation,
        stacking=stacking,
        x_min=x_min,
        x_max=x_max,
        x_ticks=x_ticks,
        secondary_axis=spec.secondary_y_axis if has_secondary else None,
        y2_min=y2_min,
        y2_max=y2_max,
        y2_ticks=y2_ticks,
    )


def _chrome_head(fr: CartesianFrame, p: list[str]) -> None:
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
            f'<svg class="sc-chart"{a11y_attr} xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
            f'width="100%" {_font}>'
        )
    else:
        p.append(
            f'<svg class="sc-chart"{a11y_attr} xmlns="http://www.w3.org/2000/svg" '
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
        p.append(f'<rect class="sc-bg" x="0" y="0" width="{W}" height="{H}" fill="{theme.background}"/>')

    # Titles.
    ty = 26
    if spec.title:
        p.append(
            f'<text class="sc-title" x="{W / 2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="17" font-weight="600" fill="{theme.title_color}">{esc(spec.title)}</text>'
        )
        ty += 20
    if spec.subtitle:
        p.append(
            f'<text class="sc-subtitle" x="{W / 2:.1f}" y="{ty}" text-anchor="middle" '
            f'font-size="12" fill="{theme.subtitle_color}">{esc(spec.subtitle)}</text>'
        )

    if fr.orientation == "horizontal":
        gl = spec.y_axis.grid_line or GridLine()
        grid_color = gl.color or theme.grid_color
        grid_dash = dash_array(gl.dash_style)
        dash_attr = f' stroke-dasharray="{grid_dash}"' if grid_dash else ""
        p.append('<g class="sc-axis sc-axis-x">')
        for tv in y_ticks:
            gx = fr.value_pix(tv)
            if gl.enabled:
                p.append(
                    f'<line class="sc-gridline" x1="{gx:.1f}" y1="{plot_y:.1f}" '
                    f'x2="{gx:.1f}" y2="{plot_y + plot_h:.1f}" stroke="{grid_color}" '
                    f'stroke-width="1"{dash_attr}/>'
                )
            p.append(
                f'<text x="{gx:.1f}" y="{plot_y + plot_h + 18:.1f}" text-anchor="middle" '
                f'font-size="11" fill="{theme.axis_label_color}">{esc(fmt_num(tv))}</text>'
            )
        p.append("</g>")

        p.append(
            f'<line class="sc-axis-line" x1="{plot_x:.1f}" y1="{plot_y + plot_h:.1f}" '
            f'x2="{plot_x + plot_w:.1f}" y2="{plot_y + plot_h:.1f}" stroke="{theme.axis_line_color}" stroke-width="1"/>'
        )

        p.append('<g class="sc-axis sc-axis-y">')
        for i in range(n):
            label = cats[i] if i < len(cats) else str(i)
            gy = fr.band_center(i)
            p.append(
                f'<text x="{plot_x - 8:.1f}" y="{gy + 4:.1f}" text-anchor="end" '
                f'font-size="11" fill="{theme.axis_label_color}">{esc(label)}</text>'
            )
        p.append("</g>")

        if spec.x_axis.title:
            yc = plot_y + plot_h / 2
            p.append(
                f'<text x="14" y="{yc:.1f}" text-anchor="middle" font-size="12" '
                f'fill="{theme.axis_title_color}" transform="rotate(-90 14 {yc:.1f})">{esc(spec.x_axis.title)}</text>'
            )
        if spec.y_axis.title:
            p.append(
                f'<text x="{plot_x + plot_w / 2:.1f}" y="{H - 6}" text-anchor="middle" '
                f'font-size="12" fill="{theme.axis_title_color}">{esc(spec.y_axis.title)}</text>'
            )
    else:
        # Y gridlines + labels. Defaults reproduce the built-in look byte-for-byte.
        gl = spec.y_axis.grid_line or GridLine()
        grid_color = gl.color or theme.grid_color
        grid_dash = dash_array(gl.dash_style)
        dash_attr = f' stroke-dasharray="{grid_dash}"' if grid_dash else ""
        p.append('<g class="sc-axis sc-axis-y">')
        for tv in y_ticks:
            gy = ypix(tv)
            if gl.enabled:
                p.append(
                    f'<line class="sc-gridline" x1="{plot_x:.1f}" y1="{gy:.1f}" '
                    f'x2="{plot_x + plot_w:.1f}" y2="{gy:.1f}" stroke="{grid_color}" '
                    f'stroke-width="1"{dash_attr}/>'
                )
            p.append(
                f'<text x="{plot_x - 8:.1f}" y="{gy + 4:.1f}" text-anchor="end" '
                f'font-size="11" fill="{theme.axis_label_color}">{esc(fmt_num(tv))}</text>'
            )
        p.append("</g>")

        # Axis lines.
        p.append(
            f'<line class="sc-axis-line" x1="{plot_x:.1f}" y1="{plot_y + plot_h:.1f}" '
            f'x2="{plot_x + plot_w:.1f}" y2="{plot_y + plot_h:.1f}" stroke="{theme.axis_line_color}" stroke-width="1"/>'
        )

        # X labels. LINEAR scale (scatter, §3.3 Rank 3) draws numeric ticks +
        # optional vertical gridlines, mirroring the y-axis; every other scale
        # keeps the original categorical-label loop unchanged.
        if fr.scale == "linear":
            xgl = spec.x_axis.grid_line or GridLine(enabled=False)
            xgrid_color = xgl.color or theme.grid_color
            xgrid_dash = dash_array(xgl.dash_style)
            xdash_attr = f' stroke-dasharray="{xgrid_dash}"' if xgrid_dash else ""
            if xgl.enabled:
                p.append('<g class="sc-gridlines-x">')
                for tv in fr.x_ticks:
                    gx = xpix(tv)
                    p.append(
                        f'<line class="sc-gridline" x1="{gx:.1f}" y1="{plot_y:.1f}" '
                        f'x2="{gx:.1f}" y2="{plot_y + plot_h:.1f}" stroke="{xgrid_color}" '
                        f'stroke-width="1"{xdash_attr}/>'
                    )
                p.append("</g>")
            p.append('<g class="sc-axis sc-axis-x">')
            for tv in fr.x_ticks:
                lx = xpix(tv)
                p.append(
                    f'<text x="{lx:.1f}" y="{plot_y + plot_h + 18:.1f}" text-anchor="middle" '
                    f'font-size="11" fill="{theme.axis_label_color}">{esc(fmt_num(tv))}</text>'
                )
            p.append("</g>")
        else:
            p.append('<g class="sc-axis sc-axis-x">')
            for i in range(n):
                label = cats[i] if i < len(cats) else str(i)
                lx = xpix(i)
                p.append(
                    f'<text x="{lx:.1f}" y="{plot_y + plot_h + 18:.1f}" text-anchor="middle" '
                    f'font-size="11" fill="{theme.axis_label_color}">{esc(label)}</text>'
                )
            p.append("</g>")

        # Axis titles.
        if spec.x_axis.title:
            p.append(
                f'<text x="{plot_x + plot_w / 2:.1f}" y="{H - 6}" text-anchor="middle" '
                f'font-size="12" fill="{theme.axis_title_color}">{esc(spec.x_axis.title)}</text>'
            )
        if spec.y_axis.title:
            yc = plot_y + plot_h / 2
            p.append(
                f'<text x="14" y="{yc:.1f}" text-anchor="middle" font-size="12" '
                f'fill="{theme.axis_title_color}" transform="rotate(-90 14 {yc:.1f})">{esc(spec.y_axis.title)}</text>'
            )

    if fr.secondary_axis is not None and fr.y2_ticks:
        side_left = bool(getattr(fr.secondary_axis, "opposite", True) is False)
        ax_x = plot_x - 8 if side_left else plot_x + plot_w + 8
        anchor = "end" if side_left else "start"
        14 if side_left else max(14, W - 14)
        title_rot = (
            f"rotate(-90 14 {plot_y + plot_h / 2:.1f})"
            if side_left
            else f"rotate(90 {W - 14} {plot_y + plot_h / 2:.1f})"
        )
        p.append('<g class="sc-axis sc-axis-y2">')
        for tv in fr.y2_ticks:
            p.append(
                f'<text x="{ax_x:.1f}" y="{fr.ypix2(tv) + 4:.1f}" text-anchor="{anchor}" '
                f'font-size="11" fill="{theme.axis_label_color}">{esc(fmt_num(tv))}</text>'
            )
        p.append("</g>")
        if fr.secondary_axis.title:
            p.append(
                f'<text x="{W - 14 if not side_left else 14}" y="{plot_y + plot_h / 2:.1f}" '
                f'text-anchor="middle" font-size="12" fill="{theme.axis_title_color}" '
                f'transform="{title_rot}">{esc(fr.secondary_axis.title)}</text>'
            )

    # Crosshair (hidden until a point is hovered; driven by the JS runtime).
    p.append(
        f'<line class="sc-crosshair" x1="0" y1="{plot_y:.1f}" x2="0" y2="{plot_y + plot_h:.1f}" '
        f'stroke="{theme.crosshair_color}" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>'
    )


def _chrome_tail(fr: CartesianFrame, p: list[str]) -> None:
    """§4.1 TAIL — write into p, in place: legend (bottom-center), </svg>.
    No trailing newline."""
    spec, theme = fr.spec, fr.theme
    H = fr.H
    plot_x, plot_w = fr.plot_x, fr.plot_w

    # Legend (bottom center).
    if spec.legend and spec.series:
        if spec.type == "waterfall":
            # Three-swatch direction key: Increase / Decrease / Total
            up_color = getattr(spec, "up_color", "#3f9b6a")
            down_color = getattr(spec, "down_color", "#d65f5f")
            total_color = getattr(spec, "total_color", "#4b6cb7")
            sum_idx = set(getattr(spec, "sum_indices", None) or [])
            isum_idx = set(getattr(spec, "intermediate_sum_indices", None) or [])
            has_total = bool(sum_idx or isum_idx)
            items = [("Increase", up_color), ("Decrease", down_color)]
            if has_total:
                items.append(("Total", total_color))
            gap = 22
            est = [len(label) * 7 + 26 for label, _ in items]
            total = sum(est) + gap * (len(items) - 1)
            lx = plot_x + (plot_w - total) / 2
            ly = H - (10 + (18 if spec.x_axis.title else 0))
            p.append('<g class="sc-legend">')
            for idx, (label, color) in enumerate(items):
                p.append(f'<g class="sc-legend-item" data-series="{idx}">')
                p.append(f'<rect x="{lx:.1f}" y="{ly - 9:.1f}" width="14" height="4" rx="2" fill="{color}"/>')
                p.append(
                    f'<text x="{lx + 20:.1f}" y="{ly - 2:.1f}" font-size="12" fill="{theme.legend_text_color}">{esc(label)}</text>'
                )
                p.append("</g>")
                lx += est[idx] + gap
            p.append("</g>")
        else:
            gap = 22
            est = [len(s.name) * 7 + 26 for s in spec.series]
            total = sum(est) + gap * (len(spec.series) - 1)
            lx = plot_x + (plot_w - total) / 2
            ly = H - (10 + (18 if spec.x_axis.title else 0))
            p.append('<g class="sc-legend">')
            for si, s in enumerate(spec.series):
                color = fr.styles[si].solid
                p.append(f'<g class="sc-legend-item" data-series="{si}">')
                if spec.type == "combo" and s.type == "line":
                    p.append(f'<rect x="{lx:.1f}" y="{ly - 8:.1f}" width="14" height="2" rx="1" fill="{color}"/>')
                else:
                    p.append(f'<rect x="{lx:.1f}" y="{ly - 9:.1f}" width="14" height="4" rx="2" fill="{color}"/>')
                p.append(
                    f'<text x="{lx + 20:.1f}" y="{ly - 2:.1f}" font-size="12" fill="{theme.legend_text_color}">{esc(s.name)}</text>'
                )
                p.append("</g>")
                lx += est[si] + gap
            p.append("</g>")

    p.append("</svg>")


def render_cartesian(
    spec: ChartSpec,
    chart_noun: str,
    x_scale: str,
    marks: MarksFn,
    include_zero: bool = True,
    orientation: str = "vertical",
) -> str:
    """Orchestrate head -> (chart's marks) -> tail through ONE shared
    accumulator p. Returns a single "".join(p) with NO trailing newline."""
    fr = build_frame(spec, chart_noun, x_scale, include_zero, orientation)
    p: list[str] = []
    _chrome_head(fr, p)
    marks(fr, p)  # chart appends its <g class="sc-series">…</g> blocks here
    _chrome_tail(fr, p)
    return "".join(p)  # single "".join, NO trailing newline
