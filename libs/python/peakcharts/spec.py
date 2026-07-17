"""Shared chart-spec model (Python view of spec/chart-spec.schema.json).

The spec is the language-agnostic 'recipe' for a chart: type, data, axes,
titles, colors. Every PeakCharts language library builds this same shape and
renders it. Keep this in lockstep with spec/chart-spec.schema.json.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Series:
    name: str
    data: List[float]
    color: Optional[str] = None


@dataclass
class Axis:
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None


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

    @staticmethod
    def from_dict(d: dict) -> "ChartSpec":
        """Build a ChartSpec from a plain dict (parsed JSON), Highcharts-ish keys."""
        series = [
            Series(
                name=s.get("name", f"Series {i + 1}"),
                data=[float(v) for v in s["data"]],
                color=s.get("color"),
            )
            for i, s in enumerate(d.get("series", []))
        ]
        xa = d.get("xAxis") or {}
        ya = d.get("yAxis") or {}
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
            y_axis=Axis(title=ya.get("title"), min=ya.get("min"), max=ya.get("max")),
            width=int(d.get("width", 820)),
            height=int(d.get("height", 460)),
            legend=bool(d.get("legend", True)),
        )
