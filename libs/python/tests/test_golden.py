"""Pin the Python renderer to the shared cross-language goldens.

The Go renderer pins to the same goldens (libs/go/render_test.go). When both
pass, the two libraries are provably byte-identical for every fixture.

Run standalone:  python libs/python/tests/test_golden.py
Or with pytest:  pytest libs/python/tests/
"""
import json
import pathlib
import sys
import re

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts import CapabilityError, ChartSpec, THEMES, capabilities  # noqa: E402
from stonecharts.render import render_svg  # noqa: E402
from stonecharts.validate import SpecError, validate  # noqa: E402

LINE_CASES = ["basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"]
COLUMN_CASES = ["basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"]
BAR_CASES = ["basic", "grouped", "stacked", "themed-dark"]
COMBO_CASES = ["basic", "dark", "dual-axis", "adversarial"]
AREA_CASES = ["basic", "stacked", "percent", "themed-dark"]
AREARANGE_CASES = ["basic", "spline-range", "themed-dark", "adversarial"]
HISTOGRAM_CASES = ["basic", "pareto", "prebinned", "themed-dark", "adversarial"]
SCATTER_CASES = ["basic", "correlation", "regression", "themed-dark"]
ACTIVE_VALIDATION_CASES = {
    "line-basic": LINE_CASES,
    "column": COLUMN_CASES,
    "bar": BAR_CASES,
    "combo": COMBO_CASES,
    "area": AREA_CASES,
    "arearange": AREARANGE_CASES,
    "histogram": HISTOGRAM_CASES,
    "scatter": SCATTER_CASES,
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


def test_bar_goldens():
    for name in BAR_CASES:
        _check("bar", name)


def test_combo_goldens():
    for name in COMBO_CASES:
        _check("combo", name)


def test_area_goldens():
    for name in AREA_CASES:
        _check("area", name)


def test_arearange_goldens():
    for name in AREARANGE_CASES:
        _check("arearange", name)


def test_histogram_goldens():
    for name in HISTOGRAM_CASES:
        _check("histogram", name)


def test_scatter_goldens():
    for name in SCATTER_CASES:
        _check("scatter", name)


def test_column_edge_cases():
    for spec in [
        {"type": "column", "stacking": "normal", "xAxis": {"categories": ["mix"]},
         "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}]},
        {"type": "column", "layout": {"margin": {"left": 90, "right": 40, "top": 30, "bottom": 50}},
         "series": [{"name": "s", "data": [1, 2, 3]}]},
        {"type": "column", "stacking": "percent", "xAxis": {"categories": ["zero", "nonzero"]},
         "series": [{"name": "a", "data": [0, 2]}, {"name": "b", "data": [0, 3]}]},
        {"type": "column", "xAxis": {"categories": ["neg", "pos"]},
         "series": [{"name": "a", "data": [-5, 10]}]},
        {"type": "column", "grouping": False,
         "series": [{"name": "a", "data": [1, 2]}, {"name": "b", "data": [2, 1]}]},
        {"type": "column", "series": [{"name": str(i), "data": [1, 2, 3]} for i in range(10)]},
        {"type": "column", "series": [{"name": "a", "data": [42]}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_bar_edge_cases():
    for spec in [
        {"type": "bar", "stacking": "normal", "xAxis": {"categories": ["mix"]},
         "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}]},
        {"type": "bar", "layout": {"margin": {"left": 90, "right": 40, "top": 30, "bottom": 50}},
         "series": [{"name": "s", "data": [1, 2, 3]}]},
        {"type": "bar", "stacking": "percent", "xAxis": {"categories": ["zero", "nonzero"]},
         "series": [{"name": "a", "data": [0, 2]}, {"name": "b", "data": [0, 3]}]},
        {"type": "bar", "xAxis": {"categories": ["neg", "pos"]},
         "series": [{"name": "a", "data": [-5, 10]}]},
        {"type": "bar", "grouping": False,
         "series": [{"name": "a", "data": [1, 2]}, {"name": "b", "data": [2, 1]}]},
        {"type": "bar", "series": [{"name": str(i), "data": [1, 2, 3]} for i in range(10)]},
        {"type": "bar", "series": [{"name": "a", "data": [42]}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_area_edge_cases():
    for spec in [
        {"type": "area", "xAxis": {"categories": ["a", "b"]},
         "series": [{"name": "s", "data": [1, 2]}]},
        {"type": "combo", "xAxis": {"categories": ["a", "b"]},
         "series": [{"name": "bars", "type": "column", "data": [1, 2]}, {"name": "line", "type": "line", "data": [2, 3]}]},
        {"type": "combo", "secondaryYAxis": {"title": "p95"},
         "xAxis": {"categories": ["a", "b"]},
         "series": [{"name": "bars", "type": "column", "data": [1, 2]}, {"name": "line", "type": "line", "yAxis": 1, "data": [2, 3]}]},
        {"type": "area", "stacking": "normal", "xAxis": {"categories": ["mix"]},
         "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}]},
        {"type": "area", "stacking": "percent", "xAxis": {"categories": ["zero", "nonzero"]},
         "series": [{"name": "a", "data": [0, 2]}, {"name": "b", "data": [0, 3]}]},
        {"type": "area", "series": [{"name": "a", "data": [42]}]},
    ]:
        low = render_svg(ChartSpec.from_dict(spec)).lower()
        assert "nan" not in low and "inf" not in low, spec


def test_column_signed_stack_geometry():
    svg = render_svg(ChartSpec.from_dict({
        "type": "column", "stacking": "normal", "xAxis": {"categories": ["mix"]},
        "series": [{"name": "pos", "data": [10]}, {"name": "neg", "data": [-9]}],
    }))
    rects = {
        int(series): float(y)
        for series, y in re.findall(r'data-series="(\d)"[^>]* y="([^"]+)"', svg)
    }
    assert rects[1] > rects[0], rects


def test_layout_margins():
    spec = ChartSpec.from_dict({
        "type": "column",
        "layout": {"margin": {"left": 90, "right": 40, "top": 30, "bottom": 50}},
        "series": [{"name": "s", "data": [1, 2, 3]}],
    })
    svg = render_svg(spec)
    assert 'x1="90.0"' in svg
    assert 'y="30"' in svg or 'y="30.0"' in svg


def test_short_categories_pad_and_unicode_title():
    spec = ChartSpec.from_dict({
        "type": "column",
        "title": "Temperature (°C)",
        "xAxis": {"categories": ["Jan", "Q4 2026 - Production Operations"]},
        "series": [{"name": "s", "data": [1, 2, 3]}],
    })
    svg = render_svg(spec)
    from stonecharts.render import render_html
    html = render_html(spec)
    assert "Temperature (°C)" in svg
    assert 'Jan</text>' in svg
    assert 'Q4 2026 - Production Operations' in svg
    assert '>1</text>' in svg
    assert '>2</text>' in svg
    assert '<th scope="col">Jan</th>' in html
    assert '<th scope="col">Q4 2026 - Production Operations</th>' in html
    assert '<th scope="col">2</th>' in html
    assert '<th scope="col">2</th>' in html


def test_xss_escaping():
    """Hostile strings in every user-facing field must be escaped, never injected."""
    x = '"><script>alert(1)</script>'
    spec = ChartSpec.from_dict({
        "id": x, "type": "line", "title": x, "subtitle": x,
        "theme": {"name": "light", "gridColor": "#e8e8ee", "palette": ["#2f7ed8"]},
        "xAxis": {"title": x, "categories": [x, "b", "c"]}, "yAxis": {"title": x},
        "series": [{"name": x, "data": [1, 2, 3], "color": "#2f7ed8",
                    "pattern": {"type": "hatch", "color": "#333333", "background": "#ffffff"},
                    "fillOpacity": 0.3}],
    })
    from stonecharts.render import render_html
    assert "<script>alert(1)</script>" not in render_svg(spec)
    assert "<script>alert(1)</script>" not in render_html(spec)


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
    assert caps["chartTypes"] == ["area", "arearange", "bar", "combo", "column", "histogram", "line", "scatter"]
    spec = ChartSpec.from_dict({"type": "combo", "series": [{"name": "s", "type": "column", "data": [1]}]})
    assert render_svg(spec).startswith("<svg")
    try:
        render_svg(ChartSpec(type="pie", series=[{"name": "s", "data": [1]}]))
        raise AssertionError("expected capability error")
    except CapabilityError as exc:
        assert exc.code == "E_CAPABILITY"
        assert exc.path == "$.type"
        assert exc.message == 'unsupported chart type "pie"'


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
        "background": "background", "titleColor": "title_color",
        "subtitleColor": "subtitle_color", "axisLabelColor": "axis_label_color",
        "axisTitleColor": "axis_title_color", "gridColor": "grid_color",
        "axisLineColor": "axis_line_color", "crosshairColor": "crosshair_color",
        "markerHalo": "marker_halo", "legendTextColor": "legend_text_color",
        "palette": "palette",
    }
    for name in ("light", "dark"):
        j = json.loads((ROOT / "spec" / "themes" / f"{name}.json").read_text(encoding="utf-8"))
        t = THEMES[name]
        assert t.name == j["name"], name
        for jk, attr in key_map.items():
            assert getattr(t, attr) == j[jk], f"{name}.{jk}"


# Edge-case vectors from the Phase-3 QA report: flat data, extrema, single/dual
# points, steep jumps, negatives, mixed extrema. The spline must stay finite.
SPLINE_EDGE_CASES = [
    [10.0], [10.0, 20.0], [10.0, 10.0, 10.0, 10.0], [10.0, 30.0, 10.0],
    [30.0, 10.0, 30.0], [10.0, 10.0, 100.0, 100.0], [-10.0, -20.0, -10.0],
    [0.0, 20.0, -10.0, 30.0, 5.0, 0.0, -5.0, 15.0],
]


def test_spline_edge_cases():
    for data in SPLINE_EDGE_CASES:
        spec = ChartSpec.from_dict(
            {"type": "line", "series": [{"name": "s", "data": data, "curve": "monotone"}]}
        )
        low = render_svg(spec).lower()
        assert "nan" not in low and "inf" not in low, f"NaN/Inf in spline for {data}"


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
    for _n in AREARANGE_CASES:
        _check("arearange", _n)
        print(f"PASS: python arearange-{_n} golden")
    for _n in HISTOGRAM_CASES:
        _check("histogram", _n)
        print(f"PASS: python histogram-{_n} golden")
    for _n in SCATTER_CASES:
        _check("scatter", _n)
        print(f"PASS: python scatter-{_n} golden")
    test_spline_edge_cases()
    print("PASS: python spline edge cases")

