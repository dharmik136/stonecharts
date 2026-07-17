"""Shared chart-spec model (Python view of spec/chart-spec.schema.json).

The spec is the language-agnostic 'recipe' for a chart: type, data, axes,
titles, colors, and (from the customization layer) styling. Keep this in lockstep
with spec/chart-spec.schema.json and libs/go/spec.go.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Marker:
    enabled: bool = True
    symbol: str = "circle"     # circle | square | triangle | diamond
    radius: float = 3.5


@dataclass
class Series:
    name: str
    data: List[float]
    color: Optional[str] = None
    line_width: Optional[float] = None   # None -> default 2
    dash_style: str = "solid"            # solid | dashed | dotted
    step: Optional[str] = None           # None | before | after | center
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
class ChartSpec:
    series: List[Series]
    type: str = "line"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    x_axis: Axis = field(default_factory=Axis)
    y_axis: Axis = field(default_factory=Axis)
    width: int = 820
    height: int = 460
    legend: bool = True
    responsive: bool = False

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
            series.append(
                Series(
                    name=s.get("name", f"Series {i + 1}"),
                    data=[float(v) for v in s["data"]],
                    color=s.get("color"),
                    line_width=s.get("lineWidth"),
                    dash_style=s.get("dashStyle", "solid"),
                    step=s.get("step"),
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
            width=int(d.get("width", 820)),
            height=int(d.get("height", 460)),
            legend=bool(d.get("legend", True)),
            responsive=bool(d.get("responsive", False)),
        )
