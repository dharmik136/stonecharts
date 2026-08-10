"""Pin the Python renderer to the shared cross-language goldens.

The Go renderer pins to the same goldens (libs/go/render_test.go). When both
pass, the two libraries are provably byte-identical for every fixture.

Run standalone:  python libs/python/tests/test_golden.py
Or with pytest:  pytest libs/python/tests/
"""

import json
import pathlib
import re
import sys

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts import THEMES, CapabilityError, ChartSpec, capabilities  # noqa: E402
from stonecharts.render import render_svg  # noqa: E402
from stonecharts.validate import SpecError, validate  # noqa: E402

LINE_CASES = ["basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"]
COLUMN_CASES = ["basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"]
AREA_CASES = ["basic", "stacked", "percent", "themed-dark"]
BAR_CASES = ["basic", "grouped", "stacked", "themed-dark", "adversarial"]
SCATTER_CASES = ["basic", "correlation", "regression", "themed-dark", "adversarial", "xy-points"]
BUBBLE_CASES = ["basic", "multi-series", "themed-dark", "uniform-z", "adversarial"]
COMBO_CASES = ["basic", "dark", "dual-axis", "adversarial"]
HISTOGRAM_CASES = ["basic", "prebinned", "pareto", "themed-dark", "adversarial"]
CANDLESTICK_CASES = ["basic", "ohlc", "heikin-ashi", "themed-dark", "adversarial"]
ERROR_BAR_CASES = ["basic", "overlay-grouped", "asymmetric", "themed-dark", "adversarial"]
AREARANGE_CASES = ["basic", "spline-range", "themed-dark", "adversarial"]
COLUMNRANGE_CASES = ["basic", "grouped", "horizontal", "themed-dark", "adversarial"]
WATERFALL_CASES = ["basic", "intermediate-sums", "profit-bridge", "themed-dark", "adversarial"]
BOXPLOT_CASES = ["basic", "outliers", "grouped", "themed-dark", "adversarial"]
BULLET_CASES = ["basic", "multi-kpi", "themed-dark", "adversarial"]
LOLLIPOP_CASES = ["basic", "grouped", "horizontal", "themed-dark", "adversarial"]
DUMBBELL_CASES = ["basic", "grouped", "horizontal", "themed-dark", "adversarial"]
FUNNEL_CASES = ["basic", "adversarial", "neck", "pyramid", "themed-dark"]
VARIWIDE_CASES = ["basic", "adversarial", "dark", "negative"]
TIMELINE_CASES = ["basic", "multi", "vertical", "adversarial"]
STREAMGRAPH_CASES = ["basic", "silhouette", "themed-dark", "adversarial"]
WINDBARB_CASES = ["basic", "datetime", "southern-hemisphere", "themed-dark", "adversarial"]
VECTOR_PLOT_CASES = ["basic", "field", "themed-dark", "uniform-length", "adversarial"]
PIE_CASES = [
    "basic",
    "many-slices",
    "single-slice",
    "themed-dark",
    "adversarial",
    "donut",
    "donut-single",
    "donut-dark",
    "variable-radius",
]
FLAME_CHART_CASES = ["basic", "multi-series", "deep-stack", "themed-dark", "adversarial"]
TECHNICAL_INDICATORS_CASES = ["basic", "bollinger", "rsi-pane", "themed-dark", "adversarial"]
GAUGE_CASES = ["basic", "no-bands", "full-scale", "themed-dark", "adversarial"]
SOLID_GAUGE_CASES = ["basic", "no-bands", "full-scale", "themed-dark", "adversarial"]
RADAR_CASES = ["basic", "line-only", "single-series", "themed-dark", "adversarial"]
XRANGE_CASES = ["trace-waterfall", "gantt", "swimlanes", "themed-dark", "adversarial"]
ACTIVE_VALIDATION_CASES = {
    "line-basic": LINE_CASES,
    "column": COLUMN_CASES,
    "area": AREA_CASES,
    "bar": BAR_CASES,
    "scatter": SCATTER_CASES,
    "bubble": BUBBLE_CASES,
    "combo": COMBO_CASES,
    "histogram": HISTOGRAM_CASES,
    "candlestick": CANDLESTICK_CASES,
    "error-bar": ERROR_BAR_CASES,
    "arearange": AREARANGE_CASES,
    "columnrange": COLUMNRANGE_CASES,
    "waterfall": WATERFALL_CASES,
    "boxplot": BOXPLOT_CASES,
    "bullet": BULLET_CASES,
    "lollipop": LOLLIPOP_CASES,
    "dumbbell": DUMBBELL_CASES,
    "flame-chart": FLAME_CHART_CASES,
    "pie": PIE_CASES,
    "funnel": FUNNEL_CASES,
    "gauge": GAUGE_CASES,
    "solid-gauge": SOLID_GAUGE_CASES,
    "radar": RADAR_CASES,
    "streamgraph": STREAMGRAPH_CASES,
    "technical-indicators": TECHNICAL_INDICATORS_CASES,
    "variwide": VARIWIDE_CASES,
    "timeline": TIMELINE_CASES,
    "windbarb": WINDBARB_CASES,
    "vector-plot": VECTOR_PLOT_CASES,
    "xrange": XRANGE_CASES,
}
SCHEMA = json.loads((ROOT / "spec" / "chart-spec.schema.json").read_text(encoding="utf-8"))
SCHEMA_VALIDATOR_CLASS = jsonschema.validators.validator_for(SCHEMA)
SCHEMA_VALIDATOR_CLASS.check_schema(SCHEMA)
SCHEMA_VALIDATOR = SCHEMA_VALIDATOR_CLASS(SCHEMA)


def _check(chart_dir: str, name: str):
    spec_path = ROOT / "charts" / chart_dir / "examples" / f"{name}.json"
    golden_path = ROOT / "charts" / chart_dir / "golden" / f"{name}.svg"
    spec = ChartSpec.from_dict(json.loads(spec_path.read_text(encoding="utf-8")))
    got = render_svg(spec)
    want = golden_path.read_text(encoding="utf-8")
    assert got == want, f"{chart_dir}/{name}: SVG != golden ({len(got)} vs {len(want)} bytes)"


def test_line_basic_golden():
    _check("line-basic", "basic")


def test_line_styled_golden():
    _check("line-basic", "styled")


def test_line_markers_golden():
    _check("line-basic", "markers")


def test_line_spline_golden():
    _check("line-basic", "spline")


def test_line_gradient_golden():
    _check("line-basic", "gradient")


def test_line_dark_golden():
    _check("line-basic", "dark")


def test_line_adversarial_golden():
    _check("line-basic", "adversarial")


def test_line_gradient_partial_golden():
    _check("line-basic", "gradient-partial")


def test_column_goldens():
    for name in COLUMN_CASES:
        _check("column", name)


def test_area_goldens():
    for name in AREA_CASES:
        _check("area", name)


def test_bar_goldens():
    for name in BAR_CASES:
        _check("bar", name)


def test_scatter_goldens():
    for name in SCATTER_CASES:
        _check("scatter", name)


def test_bubble_goldens():
    for name in BUBBLE_CASES:
        _check("bubble", name)


def test_combo_goldens():
    for name in COMBO_CASES:
        _check("combo", name)


def test_combo_edge_cases():
    for spec in [
        {
            "type": "combo",
            "xAxis": {"categories": ["a", "b", "c"]},
            "series": [
                {"name": "bars", "type": "column", "data": [1, 2, 3]},
                {"name": "trend", "type": "line", "data": [1.5, 2.0, 2.5]},
            ],
        },
        {
            "type": "combo",
            "xAxis": {"categories": ["a"]},
            "series": [{"name": "s", "type": "column", "data": [42]}],
        },
        {
            "type": "combo",
            "stacking": "normal",
            "xAxis": {"categories": ["a", "b"]},
            "series": [
                {"name": "c1", "type": "column", "data": [5, 3]},
                {"name": "c2", "type": "column", "data": [3, 7]},
                {"name": "line", "type": "line", "data": [6, 8]},
            ],
        },
        {
            "type": "combo",
            "xAxis": {"categories": ["x"]},
            "series": [
                {"name": "col", "type": "column", "data": [10]},
                {"name": "line", "type": "line", "data": [5]},
            ],
            "secondaryYAxis": {"title": "Right"},
        },
        {
            "type": "combo",
            "stacking": "percent",
            "xAxis": {"categories": ["zero", "nonzero"]},
            "series": [
                {"name": "c1", "type": "column", "data": [0, 3]},
                {"name": "c2", "type": "column", "data": [0, 7]},
                {"name": "line", "type": "line", "data": [1, 5]},
            ],
        },
        {
            "type": "combo",
            "stacking": "normal",
            "xAxis": {"categories": ["a", "b"]},
            "series": [
                {"name": "c1", "type": "column", "data": [-5, 10]},
                {"name": "c2", "type": "column", "data": [-3, 7]},
                {"name": "line", "type": "line", "data": [-2, 8]},
            ],
        },
        {
            "type": "combo",
            "xAxis": {"categories": []},
            "series": [{"name": "empty", "type": "column", "data": []}],
        },
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_histogram_goldens():
    for name in HISTOGRAM_CASES:
        _check("histogram", name)


def test_candlestick_goldens():
    for name in CANDLESTICK_CASES:
        _check("candlestick", name)


def test_error_bar_goldens():
    for name in ERROR_BAR_CASES:
        _check("error-bar", name)


def test_arearange_goldens():
    for name in AREARANGE_CASES:
        _check("arearange", name)


def test_columnrange_goldens():
    for name in COLUMNRANGE_CASES:
        _check("columnrange", name)


def test_waterfall_goldens():
    for name in WATERFALL_CASES:
        _check("waterfall", name)


def test_boxplot_goldens():
    for name in BOXPLOT_CASES:
        _check("boxplot", name)


def test_bullet_goldens():
    for name in BULLET_CASES:
        _check("bullet", name)


def test_lollipop_goldens():
    for name in LOLLIPOP_CASES:
        _check("lollipop", name)


def test_dumbbell_goldens():
    for name in DUMBBELL_CASES:
        _check("dumbbell", name)


def test_funnel_goldens():
    for name in FUNNEL_CASES:
        _check("funnel", name)


def test_variwide_goldens():
    for name in VARIWIDE_CASES:
        _check("variwide", name)


def test_timeline_goldens():
    for name in TIMELINE_CASES:
        _check("timeline", name)


def test_streamgraph_goldens():
    for name in STREAMGRAPH_CASES:
        _check("streamgraph", name)


def test_windbarb_goldens():
    for name in WINDBARB_CASES:
        _check("windbarb", name)


def test_vector_plot_goldens():
    for name in VECTOR_PLOT_CASES:
        _check("vector-plot", name)


def test_xrange_goldens():
    for name in XRANGE_CASES:
        _check("xrange", name)


def test_pie_goldens():
    for name in PIE_CASES:
        _check("pie", name)


def test_gauge_goldens():
    for name in GAUGE_CASES:
        _check("gauge", name)


def test_solid_gauge_goldens():
    for name in SOLID_GAUGE_CASES:
        _check("solid-gauge", name)


def test_radar_goldens():
    for name in RADAR_CASES:
        _check("radar", name)


def test_flame_chart_goldens():
    for name in FLAME_CHART_CASES:
        _check("flame-chart", name)


def test_technical_indicators_goldens():
    for name in TECHNICAL_INDICATORS_CASES:
        _check("technical-indicators", name)


def test_column_edge_cases():
    for spec in [
        {
            "type": "column",
            "stacking": "normal",
            "xAxis": {"categories": ["mix"]},
            "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}],
        },
        {
            "type": "column",
            "layout": {"margin": {"left": 90, "right": 40, "top": 30, "bottom": 50}},
            "series": [{"name": "s", "data": [1, 2, 3]}],
        },
        {
            "type": "column",
            "stacking": "percent",
            "xAxis": {"categories": ["zero", "nonzero"]},
            "series": [{"name": "a", "data": [0, 2]}, {"name": "b", "data": [0, 3]}],
        },
        {"type": "column", "xAxis": {"categories": ["neg", "pos"]}, "series": [{"name": "a", "data": [-5, 10]}]},
        {"type": "column", "grouping": False, "series": [{"name": "a", "data": [1, 2]}, {"name": "b", "data": [2, 1]}]},
        {"type": "column", "series": [{"name": str(i), "data": [1, 2, 3]} for i in range(10)]},
        {"type": "column", "series": [{"name": "a", "data": [42]}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_area_edge_cases():
    for spec in [
        {"type": "area", "xAxis": {"categories": ["a", "b"]}, "series": [{"name": "s", "data": [1, 2]}]},
        {
            "type": "area",
            "stacking": "normal",
            "xAxis": {"categories": ["mix"]},
            "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}],
        },
        {
            "type": "area",
            "stacking": "percent",
            "xAxis": {"categories": ["zero", "nonzero"]},
            "series": [{"name": "a", "data": [0, 2]}, {"name": "b", "data": [0, 3]}],
        },
        {"type": "area", "series": [{"name": "a", "data": [42]}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_bar_edge_cases():
    for spec in [
        {
            "type": "bar",
            "stacking": "normal",
            "xAxis": {"categories": ["mix"]},
            "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}],
        },
        {
            "type": "bar",
            "layout": {"margin": {"left": 90, "right": 40, "top": 30, "bottom": 50}},
            "series": [{"name": "s", "data": [1, 2, 3]}],
        },
        {
            "type": "bar",
            "stacking": "percent",
            "xAxis": {"categories": ["zero", "nonzero"]},
            "series": [{"name": "a", "data": [0, 2]}, {"name": "b", "data": [0, 3]}],
        },
        {"type": "bar", "xAxis": {"categories": ["neg", "pos"]}, "series": [{"name": "a", "data": [-5, 10]}]},
        {"type": "bar", "grouping": False, "series": [{"name": "a", "data": [1, 2]}, {"name": "b", "data": [2, 1]}]},
        {"type": "bar", "series": [{"name": str(i), "data": [1, 2, 3]} for i in range(10)]},
        {"type": "bar", "series": [{"name": "a", "data": [42]}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_scatter_edge_cases():
    for spec in [
        # Degenerate x-domain: every point shares the same x (xpix must pin to
        # plot center before the divide, not divide by zero).
        {"type": "scatter", "series": [{"name": "s", "data": [[5, 1], [5, 2], [5, 3]]}]},
        # Degenerate y-domain: every point shares the same y.
        {"type": "scatter", "series": [{"name": "s", "data": [[1, 5], [2, 5], [3, 5]]}]},
        # Single point (n=1 degenerate on both axes).
        {"type": "scatter", "series": [{"name": "s", "data": [[7, 9]]}]},
        # Empty series.
        {"type": "scatter", "series": [{"name": "s", "data": []}]},
        # Negative x and y — free domain, no zero anchor.
        {"type": "scatter", "series": [{"name": "s", "data": [[-10, -20], [-5, -8], [-1, -30]]}]},
        # Manual xAxis/yAxis min/max clamp.
        {
            "type": "scatter",
            "xAxis": {"min": 0, "max": 100},
            "yAxis": {"min": -50, "max": 50},
            "series": [{"name": "s", "data": [[10, 5], [90, -40]]}],
        },
        # Mixed element shapes within one series (bare number, positional, object) —
        # schema-legal since the point-model union applies per element, not per series.
        {"type": "scatter", "series": [{"name": "s", "data": [3, [10, 20], {"x": 30, "y": 40}]}]},
        # Vertical x-gridlines enabled.
        {
            "type": "scatter",
            "xAxis": {"gridLine": {"enabled": True}},
            "series": [{"name": "s", "data": [[1, 2], [3, 4], [5, 6]]}],
        },
        # fillOpacity explicitly 0 must still render a fully opaque point (NN#2).
        {"type": "scatter", "series": [{"name": "s", "data": [[1, 2]], "fillOpacity": 0}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_bubble_edge_cases():
    for spec in [
        # Degenerate z-domain: every point shares the same z (size_scale must
        # pin to the fixed (RMIN+RMAX)/2 before the divide, not divide by zero).
        {"type": "bubble", "series": [{"name": "s", "data": [[1, 1, 5], [2, 2, 5], [3, 3, 5]]}]},
        # Single point (degenerate z-domain by construction too).
        {"type": "bubble", "series": [{"name": "s", "data": [[7, 9, 42]]}]},
        # Empty series.
        {"type": "bubble", "series": [{"name": "s", "data": []}]},
        # Negative x/y (free domain) with z spanning a real range.
        {"type": "bubble", "series": [{"name": "s", "data": [[-10, -20, 1], [-5, -8, 50], [-1, -30, 100]]}]},
        # z = 0 for some points (valid lower bound, not degenerate by itself).
        {"type": "bubble", "series": [{"name": "s", "data": [[1, 2, 0], [3, 4, 100]]}]},
        # Manual xAxis/yAxis min/max clamp.
        {
            "type": "bubble",
            "xAxis": {"min": 0, "max": 100},
            "yAxis": {"min": -50, "max": 50},
            "series": [{"name": "s", "data": [[10, 5, 20], [90, -40, 80]]}],
        },
        # Mixed element shapes within one series (bare number, positional, object).
        {"type": "bubble", "series": [{"name": "s", "data": [3, [10, 20, 30], {"x": 40, "y": 50, "z": 60}]}]},
        # Global z-domain spans multiple series — a series with only the min
        # or only the max z must still size correctly against the shared domain.
        {
            "type": "bubble",
            "series": [
                {"name": "a", "data": [[1, 1, 1]]},
                {"name": "b", "data": [[2, 2, 1000]]},
            ],
        },
        # fillOpacity explicitly 0 must still render a fully opaque bubble (NN#2);
        # bubble's pinned default (0.65) differs from line's (0).
        {"type": "bubble", "series": [{"name": "s", "data": [[1, 2, 3]], "fillOpacity": 0}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_column_signed_stack_geometry():
    svg = render_svg(
        ChartSpec.from_dict(
            {
                "type": "column",
                "stacking": "normal",
                "xAxis": {"categories": ["mix"]},
                "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}],
            }
        )
    )
    rects = {int(series): float(y) for series, y in re.findall(r'data-series="(\d)"[^>]* y="([^"]+)"', svg)}
    assert rects[1] > rects[0], rects


def test_layout_margins():
    spec = ChartSpec.from_dict(
        {
            "type": "column",
            "layout": {"margin": {"left": 90, "right": 40, "top": 30, "bottom": 50}},
            "series": [{"name": "s", "data": [1, 2, 3]}],
        }
    )
    svg = render_svg(spec)
    assert 'x1="90.0"' in svg
    assert 'y="30"' in svg or 'y="30.0"' in svg


def test_short_categories_pad_and_unicode_title():
    spec = ChartSpec.from_dict(
        {
            "type": "column",
            "title": "Temperature (°C)",
            "xAxis": {"categories": ["Jan", "Q4 2026 - Production Operations"]},
            "series": [{"name": "s", "data": [1, 2, 3]}],
        }
    )
    svg = render_svg(spec)
    from stonecharts.render import render_html

    html = render_html(spec)
    assert "Temperature (°C)" in svg
    assert "Jan</text>" in svg
    assert "Q4 2026 - Production Operations" in svg
    assert ">1</text>" in svg
    assert ">2</text>" in svg
    assert '<th scope="col">Jan</th>' in html
    assert '<th scope="col">Q4 2026 - Production Operations</th>' in html
    assert '<th scope="col">2</th>' in html
    assert '<th scope="col">2</th>' in html


def test_xss_escaping():
    """Hostile strings in every user-facing field must be escaped, never injected."""
    x = '"><script>alert(1)</script>'
    payload = "<script>alert(1)</script>"

    type_data = {
        "line": [1, 2, 3],
        "column": [1, 2, 3],
        "area": [1, 2, 3],
        "bar": [1, 2, 3],
        "scatter": [[1, 2], [3, 4]],
        "bubble": [[1, 2, 3], [4, 5, 6]],
        "combo": [1, 2, 3],
    }

    from stonecharts.render import render_html

    for chart_type, data in type_data.items():
        spec = ChartSpec.from_dict(
            {
                "id": x,
                "type": chart_type,
                "title": x,
                "subtitle": x,
                "theme": {"name": "light", "gridColor": "#e8e8ee", "palette": ["#2f7ed8"]},
                "xAxis": {"title": x, "categories": [x, "b", "c"]}
                if chart_type not in ("scatter", "bubble")
                else {"title": x},
                "yAxis": {"title": x},
                "series": [
                    {
                        "name": x,
                        "data": data,
                        "color": "#2f7ed8",
                        "pattern": {"type": "hatch", "color": "#333333", "background": "#ffffff"},
                        "fillOpacity": 0.3,
                    }
                ],
            }
        )
        svg = render_svg(spec)
        html = render_html(spec)
        assert payload not in svg, f"XSS in SVG for {chart_type}"
        assert payload not in html, f"XSS in HTML for {chart_type}"


def test_valid_edges_render():
    """Absent/degenerate-but-valid specs still render (absent != malformed)."""
    for spec in [
        {"type": "line", "series": []},
        {"type": "line", "series": [{"name": "s", "data": []}]},
        {"type": "line", "width": 5.0, "series": [{"name": "s", "data": [1, 2]}]},
        {"type": "line", "frob": 1, "series": [{"name": "s", "data": [1, 2], "wib": 9}]},
    ]:
        svg = render_svg(ChartSpec.from_dict(spec))
        assert svg.startswith("<svg") and svg.endswith("</svg>")


def test_invalid_fixtures_parity():
    """Every shared invalid fixture is rejected with the exact expected errors — the
    SAME file the Go suite checks, so both renderers reject identically."""
    cases = []
    for path in sorted((ROOT / "charts").glob("*/invalid-fixtures.json")):
        cases.extend(json.loads(path.read_text(encoding="utf-8")))
    assert cases, "no invalid fixtures"
    for c in cases:
        assert validate(c["spec"]) == c["errors"], c["spec"]
        try:
            ChartSpec.from_dict(c["spec"])
            raise AssertionError(f"not rejected: {c['spec']}")
        except SpecError:
            pass


def test_all_example_specs_validate():
    assert ACTIVE_VALIDATION_CASES, "no active release examples"
    for chart_dir, names in ACTIVE_VALIDATION_CASES.items():
        for name in names:
            path = ROOT / "charts" / chart_dir / "examples" / f"{name}.json"
            spec = json.loads(path.read_text(encoding="utf-8"))
            assert validate(spec) == [], str(path)


def test_schema_parity():
    assert ACTIVE_VALIDATION_CASES, "no active release examples"
    for chart_dir, names in ACTIVE_VALIDATION_CASES.items():
        for name in names:
            path = ROOT / "charts" / chart_dir / "examples" / f"{name}.json"
            spec = json.loads(path.read_text(encoding="utf-8"))
            schema_errors = list(SCHEMA_VALIDATOR.iter_errors(spec))
            assert not schema_errors, f"{path}: {schema_errors}"
            assert validate(spec) == [], str(path)

    for path in sorted((ROOT / "charts").glob("*/invalid-fixtures.json")):
        cases = json.loads(path.read_text(encoding="utf-8"))
        for c in cases:
            schema_errors = list(SCHEMA_VALIDATOR.iter_errors(c["spec"]))
            assert schema_errors, c["spec"]
            assert validate(c["spec"]) == c["errors"], c["spec"]


def test_capability_manifest_and_error():
    caps = capabilities()
    assert caps["specVersion"] == "0.0.0.1"
    assert caps["svgContractVersion"] == "0.0.0.1"
    assert caps["chartTypes"] == [
        "area",
        "arearange",
        "bar",
        "boxplot",
        "bubble",
        "bullet",
        "candlestick",
        "column",
        "columnrange",
        "combo",
        "dumbbell",
        "error-bar",
        "flame-chart",
        "funnel",
        "gauge",
        "histogram",
        "line",
        "lollipop",
        "pie",
        "radar",
        "scatter",
        "solid-gauge",
        "streamgraph",
        "technical-indicators",
        "timeline",
        "vector-plot",
        "variwide",
        "waterfall",
        "windbarb",
        "xrange",
    ]
    spec = ChartSpec.from_dict({"type": "column", "series": [{"name": "s", "data": [1]}]})
    assert render_svg(spec).startswith("<svg")
    try:
        render_svg(ChartSpec(type="heatmap", series=[{"name": "s", "data": [1]}]))
        raise AssertionError("expected capability error")
    except CapabilityError as exc:
        assert exc.code == "E_CAPABILITY"
        assert exc.path == "$.type"
        assert exc.message == 'unsupported chart type "heatmap"'


def test_a11y_toggle():
    """a11y is on by default (role/desc); a11y:false restores the pre-a11y bytes."""
    base = {"type": "line", "title": "T", "series": [{"name": "s", "data": [1, 2, 3]}]}
    on = render_svg(ChartSpec.from_dict(base))
    assert 'role="img"' in on and "<desc>" in on
    off = render_svg(ChartSpec.from_dict({**base, "a11y": False}))
    assert 'role="img"' not in off and "<desc>" not in off


def test_theme_json_parity():
    """The baked THEMES must stay in lockstep with the canonical spec/themes/*.json."""
    key_map = {
        "background": "background",
        "titleColor": "title_color",
        "subtitleColor": "subtitle_color",
        "axisLabelColor": "axis_label_color",
        "axisTitleColor": "axis_title_color",
        "gridColor": "grid_color",
        "axisLineColor": "axis_line_color",
        "crosshairColor": "crosshair_color",
        "markerHalo": "marker_halo",
        "legendTextColor": "legend_text_color",
        "palette": "palette",
    }
    for name in ("light", "dark"):
        j = json.loads((ROOT / "spec" / "themes" / f"{name}.json").read_text(encoding="utf-8"))
        t = THEMES[name]
        assert t.name == j["name"], name
        for jk, attr in key_map.items():
            assert getattr(t, attr) == j[jk], f"{name}.{jk}"


def test_golden_coverage_completeness():
    """Every golden SVG must have a matching example JSON, and vice versa."""
    for chart_dir in ACTIVE_VALIDATION_CASES:
        golden_dir = ROOT / "charts" / chart_dir / "golden"
        example_dir = ROOT / "charts" / chart_dir / "examples"
        golden_names = {p.stem for p in golden_dir.glob("*.svg")}
        example_names = {p.stem for p in example_dir.glob("*.json")}
        assert golden_names == example_names, (
            f"{chart_dir}: golden/example mismatch — "
            f"golden-only: {golden_names - example_names}, "
            f"example-only: {example_names - golden_names}"
        )


def test_schema_type_enum_matches_capabilities():
    """The JSON schema type enum must list exactly the capabilities chartTypes."""
    schema_types = set(SCHEMA["properties"]["type"]["enum"])
    cap_types = set(capabilities()["chartTypes"])
    assert schema_types == cap_types, f"schema={schema_types}, capabilities={cap_types}"


def test_active_validation_cases_cover_all_chart_types():
    """ACTIVE_VALIDATION_CASES must cover every capability-listed chart type."""
    dir_to_type = {"line-basic": "line"}
    tested_types = {dir_to_type.get(d, d) for d in ACTIVE_VALIDATION_CASES}
    cap_types = set(capabilities()["chartTypes"])
    assert tested_types == cap_types, f"tested={tested_types}, capabilities={cap_types}"


def test_invalid_fixtures_minimum_coverage():
    """Every certified chart type must have at least 3 invalid fixture cases."""
    for chart_dir in ACTIVE_VALIDATION_CASES:
        path = ROOT / "charts" / chart_dir / "invalid-fixtures.json"
        assert path.is_file(), f"{chart_dir} missing invalid-fixtures.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        assert len(cases) >= 3, f"{chart_dir} has only {len(cases)} invalid fixtures (minimum 3)"


# Edge-case vectors from the Phase-3 QA report: flat data, extrema, single/dual
# points, steep jumps, negatives, mixed extrema. The spline must stay finite.
SPLINE_EDGE_CASES = [
    [10.0],
    [10.0, 20.0],
    [10.0, 10.0, 10.0, 10.0],
    [10.0, 30.0, 10.0],
    [30.0, 10.0, 30.0],
    [10.0, 10.0, 100.0, 100.0],
    [-10.0, -20.0, -10.0],
    [0.0, 20.0, -10.0, 30.0, 5.0, 0.0, -5.0, 15.0],
]


def test_spline_edge_cases():
    for data in SPLINE_EDGE_CASES:
        spec = ChartSpec.from_dict({"type": "line", "series": [{"name": "s", "data": data, "curve": "monotone"}]})
        low = render_svg(spec).lower()
        assert "nan" not in low and "inf" not in low, f"NaN/Inf in spline for {data}"


def test_save_html(tmp_path):
    spec = ChartSpec.from_dict(
        {"type": "line", "xAxis": {"categories": ["a", "b"]}, "series": [{"name": "s", "data": [1, 2]}]}
    )
    from stonecharts.render import save_html

    out = save_html(spec, str(tmp_path / "test.html"), "Test Page")
    html = out.read_text(encoding="utf-8")
    assert "<title>Test Page</title>" in html
    assert "<svg" in html


def test_step_interpolation_modes():
    """Cover before/center step branches in _path_d."""
    for step in ("before", "center", "after"):
        spec = ChartSpec.from_dict(
            {
                "type": "line",
                "xAxis": {"categories": ["a", "b", "c"]},
                "series": [{"name": "s", "data": [1, 3, 2], "step": step}],
            }
        )
        svg = render_svg(spec).lower()
        assert "nan" not in svg and "inf" not in svg, f"NaN/Inf for step={step}"


def test_validation_type_error_branches():
    """Hit validation branches for wrong-typed fields that invalid fixtures don't cover."""
    cases = [
        (
            {"type": "line", "series": [{"name": "s", "data": [1]}], "xAxis": {"categories": 42}},
            "$.xAxis.categories: expected array, received number",
        ),
        (
            {"type": "line", "series": [{"name": "s", "data": [1]}], "xAxis": {"gridLine": "bad"}},
            "$.xAxis.gridLine: expected object, received string",
        ),
        (
            {
                "type": "line",
                "series": [{"name": "s", "data": [1]}],
                "xAxis": {"opposite": "yes", "binEdges": "bad"},
            },
            "$.xAxis.opposite: expected boolean, received string",
        ),
        (
            {
                "type": "line",
                "series": [{"name": "s", "data": [1]}],
                "xAxis": {"binEdges": [1, "two", 3]},
            },
            "$.xAxis.binEdges[1]: expected number, received string",
        ),
        (
            {
                "type": "line",
                "series": [{"name": "s", "data": [1]}],
                "layout": {"margin": "flat"},
            },
            "$.layout.margin: expected object, received string",
        ),
    ]
    for spec, expected_fragment in cases:
        errs = validate(spec)
        assert any(expected_fragment in e for e in errs), (
            f"Expected '{expected_fragment}' in validation errors, got: {errs}"
        )


def test_validation_deep_coverage():
    """Cover remaining validate.py branches: type helpers, gradient/pattern/theme/datum edges,
    margin plot-area check, unknown chart type, and percent-stacking guards."""
    cases = [
        # _jtype returns "array" / "object" for wrong-typed top-level fields
        ({"type": ["line"], "series": [{"data": [1]}]}, "$.type: expected string, received array"),
        ({"type": {}, "series": [{"data": [1]}]}, "$.type: expected string, received object"),
        # _num with NaN / Infinity
        ({"type": "line", "series": [{"data": [float("nan")]}]}, "received NaN"),
        ({"type": "line", "series": [{"data": [float("inf")]}]}, "received Infinity"),
        # _nonneg_num: bool and non-finite values skip the negative check (no crash)
        (
            {"type": "line", "stacking": "percent", "series": [{"type": "column", "data": [True]}]},
            "expected number, received boolean",
        ),
        (
            {"type": "line", "stacking": "percent", "series": [{"type": "column", "data": [float("inf")]}]},
            "received Infinity",
        ),
        # _axis called with non-dict
        ({"type": "line", "series": [{"data": [1]}], "xAxis": 42}, "$.xAxis: expected object, received number"),
        # _layout non-dict
        ({"type": "line", "series": [{"data": [1]}], "layout": "flat"}, "$.layout: expected object, received string"),
        # _marker non-dict
        (
            {"type": "line", "series": [{"marker": "bad", "data": [1]}]},
            "$.series[0].marker: expected object, received string",
        ),
        # _pattern non-dict
        (
            {"type": "line", "series": [{"pattern": 42, "data": [1]}]},
            "$.series[0].pattern: expected object, received number",
        ),
        # _gradient: stops as non-array, stop as non-dict, stop with bad hex color
        (
            {"type": "line", "series": [{"color": {"stops": "bad"}, "data": [1]}]},
            "$.series[0].color.stops: expected array, received string",
        ),
        (
            {"type": "line", "series": [{"color": {"stops": [42]}, "data": [1]}]},
            "$.series[0].color.stops[0]: expected object, received number",
        ),
        (
            {"type": "line", "series": [{"color": {"stops": [{"offset": 0, "color": "bad"}]}, "data": [1]}]},
            '$.series[0].color.stops[0].color: expected hex color, received "bad"',
        ),
        (
            {"type": "line", "series": [{"color": {"stops": [{"opacity": "x"}]}, "data": [1]}]},
            "$.series[0].color.stops[0].opacity: expected number, received string",
        ),
        # _color: non-string, non-dict
        (
            {"type": "line", "series": [{"color": 42, "data": [1]}]},
            "$.series[0].color: expected string or gradient object, received number",
        ),
        # _theme: non-string, non-dict
        ({"type": "line", "series": [{"data": [1]}], "theme": 42}, "expected string or theme object, received number"),
        # _theme: dict with typed name field
        (
            {"type": "line", "series": [{"data": [1]}], "theme": {"name": 42}},
            "$.theme.name: expected string, received number",
        ),
        # _datum: boolean (scatter)
        ({"type": "scatter", "series": [{"data": [True]}]}, "received boolean"),
        # _datum: dict missing x and y
        ({"type": "scatter", "series": [{"data": [{"y": 1}]}]}, "$.series[0].data[0].x: required"),
        ({"type": "scatter", "series": [{"data": [{"x": 1}]}]}, "$.series[0].data[0].y: required"),
        # _datum: extra keys in dict
        ({"type": "scatter", "series": [{"data": [{"x": 1, "y": 2, "z": 3}]}]}, ".z: unknown field"),
        # _datum: non-number/list/dict/bool (null)
        ({"type": "scatter", "series": [{"data": [None]}]}, "received null"),
        # _datum_xyz: boolean (bubble)
        ({"type": "bubble", "series": [{"data": [True]}]}, "received boolean"),
        # _datum_xyz: else branch (null)
        ({"type": "bubble", "series": [{"data": [None]}]}, "received null"),
        # yAxis out of range (not 0 or 1)
        (
            {"type": "combo", "series": [{"data": [1], "yAxis": 2}]},
            '$.series[0].yAxis: expected one of 0, 1, received "2"',
        ),
        # unknown chart type
        ({"type": "heatmap", "series": [{"data": [1]}]}, '$.type: unknown chart type "heatmap"'),
        # percent stacking: non-dict series item skipped
        ({"type": "line", "stacking": "percent", "series": [42]}, "$.series[0]: expected object, received number"),
        # percent stacking: non-list data skipped
        (
            {"type": "line", "stacking": "percent", "series": [{"data": "bad"}]},
            "$.series[0].data: expected array, received string",
        ),
        # margin plot-area check: width squeezed to zero or negative
        (
            {
                "type": "line",
                "width": 100,
                "height": 400,
                "layout": {"margin": {"left": 60, "right": 60}},
                "series": [{"data": [1]}],
            },
            "plot width must remain positive",
        ),
        # margin plot-area check: height squeezed to zero or negative
        (
            {
                "type": "line",
                "width": 400,
                "height": 50,
                "layout": {"margin": {"top": 30, "bottom": 30}},
                "series": [{"data": [1]}],
            },
            "plot height must remain positive",
        ),
        # _marker dict with enabled (non-bool) — covers _marker.enabled branch
        (
            {"type": "line", "series": [{"marker": {"enabled": "yes"}, "data": [1]}]},
            "$.series[0].marker.enabled: expected boolean, received string",
        ),
        # _theme dict with non-string background — covers _theme.background branch
        (
            {"type": "line", "series": [{"data": [1]}], "theme": {"background": 42}},
            "$.theme.background: expected string, received number",
        ),
        # validate() called with non-dict — covers root-level type check
        (42, "$: expected object, received number"),
    ]
    for spec, expected_fragment in cases:
        errs = validate(spec)
        assert any(expected_fragment in e for e in errs), (
            f"Expected '{expected_fragment}' in validation errors, got: {errs}"
        )


def test_util_fmt_num_edge_cases():
    """Cover fmt_num with non-finite values (NaN, Inf) and nice_ticks degenerate ranges."""
    from stonecharts.util import fmt_num, nice_ticks

    assert fmt_num(float("nan")) == "0"
    assert fmt_num(float("inf")) == "0"
    assert fmt_num(float("-inf")) == "0"
    _, _, ticks = nice_ticks(5.0, 5.0)
    assert len(ticks) > 0


def test_capability_error_str_empty_path():
    """Cover CapabilityError.__str__ when path is empty."""
    err = CapabilityError("E_TEST", "", "something went wrong")
    assert str(err) == "something went wrong"
    err2 = CapabilityError("E_TEST", "$.type", "bad type")
    assert str(err2) == "$.type: bad type"


def test_limits_edge_cases():
    """Cover enforce_spec_limits with non-dict (early return) and total-points limit."""
    from stonecharts.limits import MAX_TOTAL_POINTS, ResourceLimitError, enforce_spec_limits

    enforce_spec_limits(42)
    enforce_spec_limits("not a dict")

    from stonecharts.limits import MAX_POINTS_PER_SERIES

    big_data = list(range(MAX_POINTS_PER_SERIES + 1))
    try:
        enforce_spec_limits({"series": [{"data": big_data}]})
        raise AssertionError("should have raised per-series limit")
    except ResourceLimitError as e:
        assert e.code == "LIMIT.POINTS_PER_SERIES"

    chunk = list(range(MAX_POINTS_PER_SERIES))
    num_series = (MAX_TOTAL_POINTS // MAX_POINTS_PER_SERIES) + 1
    try:
        enforce_spec_limits({"series": [{"data": chunk} for _ in range(num_series)]})
        raise AssertionError("should have raised total-points limit")
    except ResourceLimitError as e:
        assert e.code == "LIMIT.TOTAL_POINTS"


def test_theme_resolve_edge_cases():
    """Cover resolve_theme fallback paths: non-dict/non-string, and null background."""
    from stonecharts.spec import THEMES, resolve_theme

    fallback = resolve_theme(42)
    assert fallback.name == THEMES["light"].name

    custom = resolve_theme({"background": None, "titleColor": "#FF0000"})
    assert custom.background is None
    assert custom.title_color == "#FF0000"


def test_scatter_direct_construction_normalizes():
    """Cover ChartSpec.__post_init__ scatter data_points normalization."""
    from stonecharts.spec import ChartSpec, Datum, Series

    spec = ChartSpec(
        type="scatter",
        series=[Series(name="pts", data=[10.0, 20.0])],
    )
    assert spec.series[0].data_points is not None
    assert len(spec.series[0].data_points) == 2
    assert spec.series[0].data == []
    assert isinstance(spec.series[0].data_points[0], Datum)


def test_empty_series_data_renders():
    """Cover n<=0 early returns in column, bar, and area marks functions."""
    from stonecharts import Axis, ChartSpec, Series
    from stonecharts.render import render_svg

    for chart_type in ("column", "bar", "area"):
        spec = ChartSpec(
            type=chart_type,
            x_axis=Axis(categories=[]),
            series=[Series(name="empty", data=[])],
        )
        svg = render_svg(spec)
        assert "<svg" in svg


def test_verify_result_edge_cases():
    """Cover check_schema_version below-minimum and build_finding validation."""
    from stonecharts.verify.result import build_finding, check_schema_version

    assert check_schema_version(0) is not None
    assert "below minimum" in check_schema_version(0)
    assert check_schema_version(999) is not None
    assert "above maximum" in check_schema_version(999)
    assert check_schema_version("bad") is not None

    finding = build_finding(code="TEST", category="test", message="ok")
    assert finding["equality"] == "unknown"

    try:
        build_finding(code="X", category="x", message="x", equality="bad")
        raise AssertionError("should have raised")
    except ValueError:
        pass

    try:
        build_finding(code="X", category="x", message="x", confidence="bad")
        raise AssertionError("should have raised")
    except ValueError:
        pass


def test_cartesian_degenerate_geometry():
    """Cover ypix2 degenerate case (all secondary data same value) and scatter same-x."""
    from stonecharts import Axis, ChartSpec, Series
    from stonecharts.render import render_svg

    combo_spec = ChartSpec(
        type="combo",
        x_axis=Axis(categories=["A", "B"]),
        series=[
            Series(name="primary", data=[10.0, 20.0], type="column"),
            Series(name="secondary", data=[5.0, 5.0], type="line", y_axis=1),
        ],
        secondary_y_axis=Axis(title="Sec"),
    )
    svg = render_svg(combo_spec)
    assert "sc-series" in svg

    scatter_spec = ChartSpec(
        type="scatter",
        series=[Series(name="pts", data=[3.0, 3.0, 3.0])],
    )
    svg2 = render_svg(scatter_spec)
    assert "<svg" in svg2


def test_combo_line_area_fill_and_data_overflow():
    """Cover combo.py: line series with area fill, and data exceeding categories."""
    from stonecharts import Axis, ChartSpec, Series
    from stonecharts.render import render_svg

    spec = ChartSpec(
        type="combo",
        x_axis=Axis(categories=["A", "B"]),
        series=[
            Series(name="trend", data=[1.0, 2.0], type="line", fill_opacity=0.3),
        ],
    )
    svg = render_svg(spec)
    assert "sc-series-area" in svg

    spec2 = ChartSpec(
        type="combo",
        x_axis=Axis(categories=["A"]),
        series=[
            Series(name="over", data=[1.0, 2.0, 3.0], type="column"),
        ],
    )
    svg2 = render_svg(spec2)
    assert "<svg" in svg2


if __name__ == "__main__":
    for _n in LINE_CASES:
        _check("line-basic", _n)
        print(f"PASS: python line-{_n} golden")
    for _n in COLUMN_CASES:
        _check("column", _n)
        print(f"PASS: python column-{_n} golden")
    for _n in AREA_CASES:
        _check("area", _n)
        print(f"PASS: python area-{_n} golden")
    for _n in BAR_CASES:
        _check("bar", _n)
        print(f"PASS: python bar-{_n} golden")
    for _n in SCATTER_CASES:
        _check("scatter", _n)
        print(f"PASS: python scatter-{_n} golden")
    for _n in BUBBLE_CASES:
        _check("bubble", _n)
        print(f"PASS: python bubble-{_n} golden")
    for _n in COMBO_CASES:
        _check("combo", _n)
        print(f"PASS: python combo-{_n} golden")
    test_spline_edge_cases()
    print("PASS: python spline edge cases")
