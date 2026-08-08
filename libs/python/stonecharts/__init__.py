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

from .capabilities import CapabilityError, capabilities
from .render import render_html, render_svg, save_html
from .spec import (
    THEMES,
    Axis,
    ChartSpec,
    Gradient,
    GradientStop,
    Layout,
    Margin,
    Marker,
    Pattern,
    Series,
    Theme,
)
from .validate import SpecError, validate

__version__ = "0.0.0.7"
__all__ = [
    "THEMES",
    "Axis",
    "CapabilityError",
    "ChartSpec",
    "Gradient",
    "GradientStop",
    "Layout",
    "Margin",
    "Marker",
    "Pattern",
    "Series",
    "SpecError",
    "Theme",
    "__version__",
    "capabilities",
    "render_html",
    "render_svg",
    "save_html",
    "validate",
]
