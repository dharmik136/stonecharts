"""PeakCharts — an original, proprietary charting library (Python edition).

Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.


Build a chart spec, render it to a self-contained interactive HTML document.

    from peakcharts import ChartSpec, Series, render_html, save_html

    spec = ChartSpec(
        title="Monthly Temperature",
        x_axis=Axis(categories=["Jan", "Feb", "Mar"]),
        series=[Series(name="Tokyo", data=[7.0, 6.9, 9.5])],
    )
    save_html(spec, "chart.html")
"""
from .spec import Axis, ChartSpec, Series
from .render import render_html, render_svg, save_html

__version__ = "0.1.0"
__all__ = [
    "ChartSpec",
    "Series",
    "Axis",
    "render_html",
    "render_svg",
    "save_html",
    "__version__",
]
