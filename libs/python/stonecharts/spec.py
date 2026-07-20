"""Shared chart-spec model (Python view of spec/chart-spec.schema.json).

The spec is the language-agnostic 'recipe' for a chart: type, data, axes,
titles, colors, and (from the customization layer) styling. Keep this in lockstep
with spec/chart-spec.schema.json and libs/go/spec.go.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import List, Optional, Union

from .util import esc
from .validate import SpecError, validate


def _opt_float(d: dict, key: str) -> Optional[float]:
    """Float if the key is present (validation guarantees it's numeric), else None.

    This is NOT coercion: a default is supplied only when the key is ABSENT;
    malformed values are already rejected by validate() before we get here.
    """
    return float(d[key]) if key in d else None


@dataclass
class Marker:
    enabled: bool = True
    symbol: str = "circle"     # circle | square | triangle | diamond
    radius: float = 3.5


@dataclass
class GradientStop:
    offset: float
    color: str
    opacity: Optional[float] = None


@dataclass
class Gradient:
    """Linear gradient. Direction x1,y1 -> x2,y2 in 0..1 bounding-box coords."""
    stops: List[GradientStop]
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 1.0


@dataclass
class Pattern:
    type: str = "hatch"
    color: str = "#333333"
    background: Optional[str] = None
    size: float = 8.0
    angle: float = 45.0
    stroke_width: float = 1.5

@dataclass
class Binning:
    count: Optional[int] = None
    width: Optional[float] = None
    start: Optional[float] = None

@dataclass
class Series:
    name: str
    data: List[float]
    type: str = "column"                # line | column (combo per-series mark kind)
    y_axis: int = 0                      # 0 -> primary y_axis; 1 -> secondary_y_axis
    color: Optional[Union[str, Gradient]] = None
    fill_opacity: float = 0.0            # >0 -> area fill under the line
    pattern: Optional[Pattern] = None    # hatch fill for the area
    line_width: Optional[float] = None   # None -> default 2
    dash_style: str = "solid"            # solid | dashed | dotted
    step: Optional[str] = None           # None | before | after | center
    curve: Optional[str] = None          # None/linear | monotone
    marker: Optional[Marker] = None
    regression: bool = False
    low: Optional[List[float]] = None


@dataclass
class GridLine:
    enabled: bool = True
    color: Optional[str] = None      # None -> theme/default (#e8e8ee)
    dash_style: str = "solid"        # solid | dashed | dotted


@dataclass
class Axis:
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    grid_line: Optional[GridLine] = None   # yAxis only

    opposite: Optional[bool] = None        # secondaryYAxis only

    bin_edges: Optional[List[float]] = None   # xAxis only (histogram bins)


@dataclass
class Margin:
    top: Optional[float] = None
    right: Optional[float] = None
    bottom: Optional[float] = None
    left: Optional[float] = None


@dataclass
class Layout:
    margin: Optional[Margin] = None


@dataclass
class Theme:
    """Concrete color set (canonical values in spec/themes/*.json). Defaults = light,
    exactly reproducing the classic look so light output is byte-identical."""
    name: str = "light"
    background: Optional[str] = None
    title_color: str = "#1a1a2e"
    subtitle_color: str = "#6b6b80"
    axis_label_color: str = "#6b6b80"
    axis_title_color: str = "#4a4a5a"
    grid_color: str = "#e8e8ee"
    axis_line_color: str = "#b6b6c2"
    crosshair_color: str = "#c0c0cc"
    marker_halo: str = "#fff"
    legend_text_color: str = "#33334d"
    palette: List[str] = field(default_factory=lambda: [
        "#2f7ed8", "#f45b5b", "#8bbc21", "#e4a812",
        "#1aadce", "#8e44ad", "#f28f43", "#77a1e5",
    ])


# Built-in themes (baked; kept in lockstep with spec/themes/*.json by a parity test).
THEMES = {
    "light": Theme(),
    "dark": Theme(
        name="dark",
        background="#1a1a2e",
        title_color="#f5f5fa",
        subtitle_color="#a0a0b8",
        axis_label_color="#9a9ab0",
        axis_title_color="#c8c8d8",
        grid_color="#2e2e44",
        axis_line_color="#45455a",
        crosshair_color="#55556a",
        marker_halo="#1a1a2e",
        legend_text_color="#d0d0e0",
        palette=[
            "#5aa2f0", "#ff7a7a", "#a3d95a", "#f5c542",
            "#3ec8e0", "#b57ae0", "#ff9d5c", "#93b8ff",
        ],
    ),
}

# camelCase JSON key -> Theme attribute (for custom-object overrides + JSON parity).
_THEME_KEYS = {
    "background": "background", "titleColor": "title_color",
    "subtitleColor": "subtitle_color", "axisLabelColor": "axis_label_color",
    "axisTitleColor": "axis_title_color", "gridColor": "grid_color",
    "axisLineColor": "axis_line_color", "crosshairColor": "crosshair_color",
    "markerHalo": "marker_halo", "legendTextColor": "legend_text_color",
    "palette": "palette",
}


def resolve_theme(value) -> Theme:
    """A theme name, a custom object (overriding a named base), or None -> light."""
    if value is None:
        return THEMES["light"]
    if isinstance(value, str):
        return THEMES.get(value, THEMES["light"])
    if isinstance(value, dict):
        base = THEMES.get(value.get("name", "light"), THEMES["light"])
        t = Theme(**{f.name: getattr(base, f.name) for f in fields(base)})
        t.name = value.get("name", base.name)
        # Custom theme values are user input -> escape so a hostile color can't
        # break out of the SVG attribute it lands in.
        for k, attr in _THEME_KEYS.items():
            if k in value:
                v = value[k]
                if attr == "palette":
                    if isinstance(v, list) and len(v) > 0:
                        setattr(t, attr, [esc(c) for c in v])
                elif v is None:
                    setattr(t, attr, None)
                else:
                    setattr(t, attr, esc(v))
        return t
    return THEMES["light"]


@dataclass
class ChartSpec:
    series: List[Series]
    type: str = "line"
    id: str = "sc"
    theme: Theme = field(default_factory=lambda: THEMES["light"])
    title: Optional[str] = None
    subtitle: Optional[str] = None
    x_axis: Axis = field(default_factory=Axis)
    y_axis: Axis = field(default_factory=Axis)
    secondary_y_axis: Optional[Axis] = None

    binning: Optional[Binning] = None

    pre_binned: bool = False

    normalization: str = "frequency"

    overlay: Optional[str] = None

    width: int = 820
    height: int = 460
    legend: bool = True
    responsive: bool = False
    a11y: bool = True
    layout: Optional[Layout] = None
    stacking: Optional[str] = None     # None | "normal" | "percent"
    grouping: bool = True              # True = grouped side-by-side; False = overlaid

    @staticmethod
    def from_dict(d: dict) -> "ChartSpec":
        """Build a ChartSpec from a plain dict (parsed JSON).

        The dict is validated first (same rules as the Go renderer); a malformed
        spec raises SpecError. Unknown keys are ignored. Values are trusted after
        validation, so parsing does no coercion — defaults apply only on absence.
        """
        errs = validate(d)
        if errs:
            raise SpecError(errs)
        series = []
        for i, s in enumerate(d.get("series", [])):
            m = s.get("marker")
            marker = None
            if m is not None:
                r = float(m.get("radius", 3.5))
                marker = Marker(
                    enabled=m.get("enabled", True),
                    symbol=m.get("symbol") or "circle",
                    radius=r if r != 0.0 else 3.5,
                )
            c = s.get("color")
            if isinstance(c, dict):
                color: Optional[Union[str, Gradient]] = Gradient(
                    # Keep every stop (missing offset -> 0.0, color -> "") so this
                    # matches Go's decoder byte-for-byte; do NOT drop partial stops.
                    stops=[
                        GradientStop(
                            offset=float(st.get("offset", 0.0)),
                            color=st.get("color", ""),
                            opacity=_opt_float(st, "opacity"),
                        )
                        for st in c.get("stops", [])
                    ],
                    x1=float(c.get("x1", 0.0)),
                    y1=float(c.get("y1", 0.0)),
                    x2=float(c.get("x2", 0.0)),
                    y2=float(c.get("y2", 1.0)),
                )
            else:
                color = c
            p = s.get("pattern")
            pattern = None
            if p is not None:
                pattern = Pattern(
                    type=p.get("type") or "hatch",
                    color=p.get("color") or "#333333",
                    background=p.get("background"),
                    size=float(p.get("size", 8.0)),
                    angle=float(p.get("angle", 45.0)),
                    stroke_width=float(p.get("strokeWidth", 1.5)),
                )
            series.append(
                Series(
                    name=s.get("name") or f"Series {i + 1}",
                    data=[float(v) for v in s["data"]],
                    type=s.get("type") or "column",
                    y_axis=int(s.get("yAxis", 0)),
                    color=color,
                    fill_opacity=float(s.get("fillOpacity", 0.0)),
                    pattern=pattern,
                    line_width=_opt_float(s, "lineWidth"),
                    dash_style=s.get("dashStyle") or "solid",
                    step=s.get("step"),
                    curve=s.get("curve"),
                    marker=marker,
                    regression=bool(s.get("regression", False)),
                    low=[float(v) for v in s["low"]] if "low" in s and s["low"] is not None else None,
                )
            )
        xa = d.get("xAxis") or {}
        ya = d.get("yAxis") or {}
        sy = d.get("secondaryYAxis")

        bn = d.get("binning")
        binning = None
        if bn is not None:
            binning = Binning(
                count=int(bn["count"]) if "count" in bn and bn["count"] is not None else None,
                width=_opt_float(bn, "width"),
                start=_opt_float(bn, "start"),
            )

        grid = None
        gl = ya.get("gridLine")
        if gl is not None:
            grid = GridLine(
                enabled=gl.get("enabled", True),
                color=gl.get("color"),
                dash_style=gl.get("dashStyle", "solid"),
            )

        layout = None
        ly = d.get("layout")
        if ly is not None:
            m = ly.get("margin")
            margin = None
            if m is not None:
                margin = Margin(
                    top=_opt_float(m, "top"),
                    right=_opt_float(m, "right"),
                    bottom=_opt_float(m, "bottom"),
                    left=_opt_float(m, "left"),
                )
            layout = Layout(margin=margin)

        secondary = None
        if sy is not None:
            sgrid = None
            sgl = sy.get("gridLine")
            if sgl is not None:
                sgrid = GridLine(
                    enabled=sgl.get("enabled", True),
                    color=sgl.get("color"),
                    dash_style=sgl.get("dashStyle", "solid"),
                )
            secondary = Axis(
                title=sy.get("title"),
                min=_opt_float(sy, "min"),
                max=_opt_float(sy, "max"),
                grid_line=sgrid,
                opposite=sy.get("opposite", True),
            )
        return ChartSpec(
            series=series,
            type=d.get("type") or "line",
            id=d.get("id") or "sc",
            theme=resolve_theme(d.get("theme")),
            title=d.get("title"),
            subtitle=d.get("subtitle"),
            x_axis=Axis(
                title=xa.get("title"),
                categories=xa.get("categories"),
                min=_opt_float(xa, "min"),
                max=_opt_float(xa, "max"),
                bin_edges=xa.get("binEdges"),
            ),
            y_axis=Axis(
                title=ya.get("title"),
                min=_opt_float(ya, "min"),
                max=_opt_float(ya, "max"),
                grid_line=grid,
            ),
            secondary_y_axis=secondary,

            binning=binning,

            pre_binned=bool(d.get("preBinned", False)),

            normalization=d.get("normalization") or "frequency",

            overlay=d.get("overlay"),

            width=int(d.get("width", 820)),
            height=int(d.get("height", 460)),
            legend=bool(d.get("legend", True)),
            responsive=bool(d.get("responsive", False)),
            a11y=bool(d.get("a11y", True)),
            layout=layout,
            stacking=d.get("stacking"),
            grouping=bool(d.get("grouping", True)),
        )

