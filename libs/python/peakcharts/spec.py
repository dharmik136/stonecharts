"""Shared chart-spec model (Python view of spec/chart-spec.schema.json).

The spec is the language-agnostic 'recipe' for a chart: type, data, axes,
titles, colors, and (from the customization layer) styling. Keep this in lockstep
with spec/chart-spec.schema.json and libs/go/spec.go.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import List, Optional, Union

from .util import esc


def _num(v) -> float:
    """Coerce a data value to float; non-numeric/None -> 0.0 (never crash)."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _int(v, default: int) -> int:
    """Coerce to int; non-numeric/None -> default (never crash)."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


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
class Series:
    name: str
    data: List[float]
    color: Optional[Union[str, Gradient]] = None
    fill_opacity: float = 0.0            # >0 -> area fill under the line
    pattern: Optional[Pattern] = None    # hatch fill for the area
    line_width: Optional[float] = None   # None -> default 2
    dash_style: str = "solid"            # solid | dashed | dotted
    step: Optional[str] = None           # None | before | after | center
    curve: Optional[str] = None          # None/linear | monotone
    marker: Optional[Marker] = None


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
                if attr == "palette" and isinstance(v, list):
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
    id: str = "pk"
    theme: Theme = field(default_factory=lambda: THEMES["light"])
    title: Optional[str] = None
    subtitle: Optional[str] = None
    x_axis: Axis = field(default_factory=Axis)
    y_axis: Axis = field(default_factory=Axis)
    width: int = 820
    height: int = 460
    legend: bool = True
    responsive: bool = False
    a11y: bool = True

    @staticmethod
    def from_dict(d: dict) -> "ChartSpec":
        """Build a ChartSpec from a plain dict (parsed JSON). Unknown keys ignored."""
        series = []
        for i, s in enumerate(d.get("series", [])):
            m = s.get("marker")
            marker = None
            if m is not None:
                marker = Marker(
                    enabled=m.get("enabled", True),
                    symbol=m.get("symbol", "circle"),
                    radius=float(m.get("radius", 3.5)),
                )
            c = s.get("color")
            if isinstance(c, dict):
                color: Optional[Union[str, Gradient]] = Gradient(
                    stops=[
                        GradientStop(
                            offset=float(st["offset"]),
                            color=st["color"],
                            opacity=st.get("opacity"),
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
                    type=p.get("type", "hatch"),
                    color=p.get("color", "#333333"),
                    background=p.get("background"),
                    size=float(p.get("size", 8.0)),
                    angle=float(p.get("angle", 45.0)),
                    stroke_width=float(p.get("strokeWidth", 1.5)),
                )
            series.append(
                Series(
                    name=s.get("name", f"Series {i + 1}"),
                    data=[_num(v) for v in (s.get("data") or [])],
                    color=color,
                    fill_opacity=float(s.get("fillOpacity", 0.0)),
                    pattern=pattern,
                    line_width=s.get("lineWidth"),
                    dash_style=s.get("dashStyle", "solid"),
                    step=s.get("step"),
                    curve=s.get("curve"),
                    marker=marker,
                )
            )
        xa = d.get("xAxis") or {}
        ya = d.get("yAxis") or {}

        grid = None
        gl = ya.get("gridLine")
        if gl is not None:
            grid = GridLine(
                enabled=gl.get("enabled", True),
                color=gl.get("color"),
                dash_style=gl.get("dashStyle", "solid"),
            )

        return ChartSpec(
            series=series,
            type=d.get("type", "line"),
            id=d.get("id", "pk"),
            theme=resolve_theme(d.get("theme")),
            title=d.get("title"),
            subtitle=d.get("subtitle"),
            x_axis=Axis(
                title=xa.get("title"),
                categories=xa.get("categories"),
                min=xa.get("min"),
                max=xa.get("max"),
            ),
            y_axis=Axis(
                title=ya.get("title"),
                min=ya.get("min"),
                max=ya.get("max"),
                grid_line=grid,
            ),
            width=_int(d.get("width", 820), 820),
            height=_int(d.get("height", 460), 460),
            legend=bool(d.get("legend", True)),
            responsive=bool(d.get("responsive", False)),
            a11y=bool(d.get("a11y", True)),
        )
