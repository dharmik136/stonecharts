"""StoneCharts — an original, proprietary charting library (Python edition).

Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.


Build a chart spec, render it to a self-contained interactive HTML document.

    from stonecharts import ChartSpec, Series, render_html, save_html

    spec = ChartSpec(
        title="Monthly Temperature",
        x_axis=Axis(categories=["Jan", "Feb", "Mar"]),
        series=[Series(name="Tokyo", data=[7.0, 6.9, 9.5])],
    )
    save_html(spec, "chart.html")
"""
from .spec import (
    Axis, ChartSpec, Gradient, GradientStop, Layout, Margin, Marker, Pattern, Series, Theme, THEMES,
)
from .capabilities import CapabilityError, capabilities
from .validate import SpecError, validate
from .render import render_html, render_svg, save_html

__version__ = "0.0.0.4"
__all__ = [
    "ChartSpec",
    "Series",
    "Axis",
    "Marker",
    "Gradient",
    "GradientStop",
    "Margin",
    "Layout",
    "Pattern",
    "Theme",
    "THEMES",
    "CapabilityError",
    "capabilities",
    "SpecError",
    "validate",
    "render_html",
    "render_svg",
    "save_html",
    "__version__",
]
