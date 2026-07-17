# TEMPLATE — not compiled; the real module lands in libs/ during the §4 extraction.
#
# skeleton_cartesian.py — a SKELETON of the shared Cartesian chrome module that the
# §4 EXTRACTION CONTRACT (docs/roadmap/chart-families.md) mandates. It sketches the
# CartesianFrame dataclass, build_frame, and render_cartesian ONLY as signatures +
# docstrings that pin the parity rules verbatim. It lives here (charts/_cartesian/,
# OUTSIDE libs/) as a design reference and is deliberately NOT wired into the build:
# the real, compiled module is `libs/python/stonecharts/charts/_cartesian.py`, created
# with Rank 1 / Column when the shared chrome is extracted out of line.py.
#
# Do NOT import this, register it in render.py, or point a golden at it. The line
# reference renderer (libs/python/stonecharts/charts/line.py) is the source of the
# verbatim chrome bodies; this file only fixes the shapes and the pinned math so the
# eventual extraction reproduces line's bytes exactly (§4.6 byte-identity gate).
"""Shared Cartesian chrome (SKELETON).

A chart renderer supplies ONLY a marks function; the frame owns everything else —
margins, scales, ticks, gridlines, axis lines/titles, legend, crosshair, background,
<defs>, theme resolution, the a11y summary, and the <svg> open/close. Per §5's golden
rule the marks callback draws ONLY the inner content of <g class="sc-series">…</g>;
it MUST NEVER re-implement any chrome and MUST NEVER compute a scale of its own — the
frame owns the value-axis domain, including the stacking-aware y-max.

The §4.1 load-bearing design fact: the series marks are SANDWICHED between a chrome
"head" and a chrome "tail" (they are not one contiguous block). Byte-identity therefore
forbids any "emit all chrome, then all marks" reshuffle. render_cartesian injects ONE
shared accumulator (a Python list `p`) through head -> marks -> tail so the writes,
their order, and the buffer match today's single-buffer line renderer exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

# The real module imports the concrete spec model:
#   from ..spec import ChartSpec, Theme
# This TEMPLATE is not compiled, so those names are only referenced in annotations.
ChartSpec = "ChartSpec"  # placeholder — resolved by libs/ at extraction time
Theme = "Theme"          # placeholder — resolved by libs/ at extraction time


@dataclass
class SeriesStyle:
    """Resolved per-series paint refs — replaces the ad-hoc tuple in line.py's defs
    pre-pass. `fill` is the NEW field the extraction adds for bar paint: it is
    populated by the defs pre-pass but UNREAD by line marks, so line bytes do not move.

    Caution (§4.3) — the no-area sentinel is per-language: Python uses
    `area_fill: Optional[str]` where `None` means "no area", while Go uses
    `areaFill string` where `""` means "no area". Safe ONLY while a real fill value is
    never `""` and never a meaningful `None`; new fields must not overload these.
    """

    stroke: str                 # hex or url(#grad) — the line/edge stroke ref
    solid: str                  # representative solid — markers / legend / data-color
    area_fill: Optional[str]    # None = no area; else hex / url(#grad) / url(#pat)
    area_op: str                # ' fill-opacity="…"' or ''
    fill: str                   # resolved BAR paint: url(#pat) -> url(#grad) -> solid hex
                                #   (defs pre-pass; line ignores it -> line bytes unchanged)


@dataclass
class CartesianFrame:
    """Everything a cartesian chart needs but its marks — built once per render by
    build_frame(). The marks read geometry through xpix / ypix / band_width and never
    recompute a scale (§5.2).
    """

    spec: "ChartSpec"
    W: int
    H: int
    theme: "Theme"
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
    include_zero: bool               # value-axis zero-anchor (see build_frame docstring)
    stacking: Optional[str]          # None | "normal" | "percent" — frame owns stacked y-domain

    def xpix(self, i: int) -> float:
        """Map a category index i to a pixel x, per the frame's x-scale strategy.

        The ONE generalization allowed during extraction is a first-class x-scale
        strategy. Both formulas below are PINNED (identical in both languages, in this
        exact operation order) so f1 rounding lands ULP-for-ULP identically:

        POINT scale (line/area/scatter-with-categories) — line.py 192–195 verbatim:
            xpix(i) = plot_x + plot_w*i/(n-1),  and  plot_x + plot_w/2  when n<=1
        Line MUST keep this exact formula so its bytes do not move.

        BAND scale (column/bar) — §4.3 pinned formula, this operation order:
            band_width() = plot_w / n
            xpix(i)      = plot_x + band_width()*i + band_width()/2   (band center)

        The x-label loop calls frame.xpix(i), so labels land under points (point) or
        band centers (band) with no per-chart label code.
        """
        ...

    def ypix(self, v: float) -> float:
        """Map a value v to a pixel y — line.py 197–198 verbatim:
            ypix(v) = plot_y + plot_h * (1 - (v - y_min) / (y_max - y_min))
        """
        ...

    def band_width(self) -> float:
        """BAND scale only — the per-category slot width. PINNED: `plot_w / n`.

        The mark drawer builds sub-bands from band_width() with the §3.2 constants,
        evaluated in EXACTLY this order so f1 rounding matches ULP-for-ULP in Py and Go
        (PAD and K are fixed constants, not per-author choices):

            bandWidth   = plot_w / n
            xpix(i)     = plot_x + bandWidth*i + bandWidth/2      # band center
            PAD         = 0.2                                     # single group-padding constant
            groupW      = bandWidth*(1 - PAD)
            K           = len(series)
            barW        = groupW / K
            left(i, k)  = xpix(i) - groupW/2 + barW*k

        (Basic single-series => K=1 => one centered bar of width groupW.)
        """
        ...


# A chart supplies ONLY this: append its marks for one plot into the accumulator p.
MarksFn = Callable[["CartesianFrame", List[str]], None]


def build_frame(
    spec: "ChartSpec",
    chart_noun: str,
    x_scale: str = "point",
    include_zero: bool = True,
) -> CartesianFrame:
    """Do the §4.2 "frame build" phase: margins, plot rect, n/cats, the value-axis
    range + nice_ticks, xpix/ypix, and the <defs> pre-pass that resolves each
    SeriesStyle (stroke, solid, area_fill, area_op, fill) + cid + defs_parts + the
    a11y summary (parameterized by chart_noun — the BARE word "Line"/"Column", not
    "Line chart"; called with "Line" it reproduces "Line chart with N series…"
    byte-for-byte, line.py 151).

    include_zero (PINNED semantics, §3.2 caveat / §4.2):
        True  -> value axis / y baseline (column/bar/area): FORCE 0 into the domain,
                 i.e. lo = min(values + [0.0]), hi = max(values + [0.0]). Line passes
                 True and this reproduces its existing domain exactly, so line bytes do
                 not move.
        False -> free numeric x (and free numeric y) scatter/bubble axis: domain from
                 the DATA ONLY. Do NOT carry the y-baseline zero-anchor into a free
                 axis, or a scatter with x in [100,200] is wrongly anchored at 0. Both
                 languages would be wrong identically and still pass byte-parity — so
                 the flag must be explicit.

    FRAME-OWNED STACKED Y-DOMAIN (the pinned parity rule this frame exists to enforce):
        This function READS the spec's stacking mode and computes the stacking-aware
        y-domain ON THE FRAME — the marks never recompute a scale. Verbatim (§4.2):
        "For stacked/percent the frame computes the y-max from the max column TOTAL
        (cumulative in the pinned summation order), NOT the per-datum max — the frame
        owns this, the marks never recompute a scale." And (§3.2 Stacking): "The frame
        (not the marks) owns the stacking-aware y-domain: for stacked/percent the y-max
        is the max column total, not the per-datum max." The SUMMATION ORDER is pinned:
        accumulate series in index order; the frame's cumulative y-domain uses that same
        summation order in both languages so cumulative floats and %g output match.
        (Percent mode: the value axis becomes nice_ticks(0, 100).)
    """
    ...


def _chrome_head(fr: CartesianFrame, p: List[str]) -> None:
    """§4.1 HEAD — write into p, in place, in emission order: <svg> open (responsive +
    fixed) + font-family, <desc>, <defs>, background rect, title + subtitle, y
    gridlines + labels, axis line, x labels, axis titles (x + rotated y), crosshair.
    Verbatim bodies moved from line.py 230–325.
    """
    ...


def _chrome_tail(fr: CartesianFrame, p: List[str]) -> None:
    """§4.1 TAIL — write into p, in place: legend (bottom-center) then </svg>.
    Verbatim bodies moved from line.py 364–385. No trailing newline.
    """
    ...


def render_cartesian(
    spec: "ChartSpec",
    chart_noun: str,
    x_scale: str,
    marks: MarksFn,
    include_zero: bool = True,
) -> str:
    """Orchestrate head -> (chart's marks) -> tail through ONE shared accumulator p,
    making byte-identity true BY CONSTRUCTION (same writes, same order, same buffer as
    today's single-buffer line renderer). Returns a single "".join(p) with NO trailing
    newline (goldens carry no trailing newline and are UTF-8, no BOM).

    A per-chart renderer is a one-line delegation, e.g. the line reference becomes:
        render_cartesian(spec, "Line", "point", _line_marks)     # include_zero defaults True
    and Column lands as just another marks callback:
        render_cartesian(spec, "Column", "band", _column_marks)  # value axis => include_zero True
    """
    fr = build_frame(spec, chart_noun, x_scale, include_zero)
    p: List[str] = []
    _chrome_head(fr, p)
    marks(fr, p)          # chart appends its <g class="sc-series">…</g> blocks here
    _chrome_tail(fr, p)
    return "".join(p)     # single "".join, NO trailing newline


# Chrome helpers moved verbatim from line.py (bodies elided in this SKELETON):
def a11y_summary(spec: "ChartSpec", chart_noun: str) -> str:
    """Was _a11y_summary; "Line" -> chart_noun. The noun is the BARE word ("Line",
    "Column"), not "Line chart" — called with "Line" it reproduces line.py 151
    "Line chart with N series…" byte-for-byte."""
    ...


def gradient_def(gid: str, g) -> str:   # was _gradient_def
    ...


def pattern_def(pid: str, pat) -> str:  # was _pattern_def
    ...


# Dash helper is SHARED, not duplicated (§4.7 #4): gridline chrome and the series-line
# mark both call this ONE function so "5 5"/"2 3" can't drift. line imports it from here.
_DASH = {"dashed": "5 5", "dotted": "2 3"}


def dash_array(style: str) -> str:      # was _dash_array
    return _DASH.get(style, "")
