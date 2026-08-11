"""Renderer purity invariant (SC-CERT-03): render_svg must not mutate spec.

For every golden example across all 35 chart types, render the spec and
verify that the ChartSpec object is unchanged afterward. A failure here
means a renderer is writing back to the caller's input, which breaks
evidence provenance and determinism under repeated render.
"""

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts import ChartSpec  # noqa: E402
from stonecharts.render import render_svg  # noqa: E402

CHART_CASES = {
    "line-basic": ["basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"],
    "column": ["basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"],
    "area": ["basic", "stacked", "percent", "themed-dark"],
    "bar": ["basic", "grouped", "stacked", "themed-dark", "adversarial"],
    "scatter": ["basic", "correlation", "regression", "themed-dark", "adversarial", "xy-points"],
    "bubble": ["basic", "multi-series", "themed-dark", "uniform-z", "adversarial"],
    "combo": ["basic", "dark", "dual-axis", "adversarial"],
    "histogram": ["basic", "prebinned", "pareto", "themed-dark", "adversarial"],
    "candlestick": ["basic", "ohlc", "heikin-ashi", "themed-dark", "adversarial"],
    "error-bar": ["basic", "overlay-grouped", "asymmetric", "themed-dark", "adversarial"],
    "arearange": ["basic", "spline-range", "themed-dark", "adversarial"],
    "columnrange": ["basic", "grouped", "horizontal", "themed-dark", "adversarial"],
    "waterfall": ["basic", "intermediate-sums", "profit-bridge", "themed-dark", "adversarial"],
    "boxplot": ["basic", "outliers", "grouped", "themed-dark", "adversarial"],
    "bullet": ["basic", "multi-kpi", "themed-dark", "adversarial"],
    "lollipop": ["basic", "grouped", "horizontal", "themed-dark", "adversarial"],
    "dumbbell": ["basic", "grouped", "horizontal", "themed-dark", "adversarial"],
    "funnel": ["basic", "adversarial", "neck", "pyramid", "themed-dark"],
    "variwide": ["basic", "adversarial", "dark", "negative"],
    "timeline": ["basic", "multi", "vertical", "adversarial"],
    "streamgraph": ["basic", "silhouette", "themed-dark", "adversarial"],
    "windbarb": ["basic", "datetime", "southern-hemisphere", "themed-dark", "adversarial"],
    "vector-plot": ["basic", "field", "themed-dark", "uniform-length", "adversarial"],
    "flame-chart": ["basic", "multi-series", "deep-stack", "themed-dark", "adversarial"],
    "pie": [
        "basic",
        "many-slices",
        "single-slice",
        "themed-dark",
        "adversarial",
        "donut",
        "donut-single",
        "donut-dark",
        "variable-radius",
    ],
    "gauge": ["basic", "no-bands", "full-scale", "themed-dark", "adversarial"],
    "solid-gauge": ["basic", "no-bands", "full-scale", "themed-dark", "adversarial"],
    "radar": ["basic", "line-only", "single-series", "themed-dark", "adversarial"],
    "polar": ["basic", "line-only", "single-series", "themed-dark", "adversarial"],
    "nightingale": ["basic", "multi-series", "single-series", "themed-dark", "adversarial"],
    "parliament": ["basic", "multi-series", "single-series", "themed-dark", "adversarial"],
    "radial-bar": ["basic", "multi-series", "single-series", "themed-dark", "adversarial"],
    "wind-rose": ["basic", "many-directions", "single-series", "themed-dark", "adversarial"],
    "technical-indicators": ["basic", "bollinger", "rsi-pane", "themed-dark", "adversarial"],
    "xrange": ["trace-waterfall", "gantt", "swimlanes", "themed-dark", "adversarial"],
}


def _ids():
    for chart_dir, names in CHART_CASES.items():
        for name in names:
            yield chart_dir, name


import pytest  # noqa: E402


@pytest.mark.parametrize("chart_dir,name", list(_ids()), ids=[f"{d}/{n}" for d, n in _ids()])
def test_render_does_not_mutate_spec(chart_dir, name):
    spec_path = ROOT / "charts" / chart_dir / "examples" / f"{name}.json"
    spec = ChartSpec.from_dict(json.loads(spec_path.read_text(encoding="utf-8")))
    before = copy.deepcopy(spec)
    render_svg(spec)
    assert spec == before, f"Renderer mutated spec for {chart_dir}/{name}"
