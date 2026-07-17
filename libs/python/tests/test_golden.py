"""Pin the Python renderer to the shared cross-language goldens.

The Go renderer pins to the same goldens (libs/go/render_test.go). When both
pass, the two libraries are provably byte-identical for every fixture.

Run standalone:  python libs/python/tests/test_golden.py
Or with pytest:  pytest libs/python/tests/
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from peakcharts import ChartSpec, THEMES  # noqa: E402
from peakcharts.render import render_svg  # noqa: E402
from peakcharts.validate import SpecError, validate  # noqa: E402

CASES = ["basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"]


def _check(name: str):
    spec_path = ROOT / "charts" / "line-basic" / "examples" / f"{name}.json"
    golden_path = ROOT / "charts" / "line-basic" / "golden" / f"{name}.svg"
    spec = ChartSpec.from_dict(json.loads(spec_path.read_text(encoding="utf-8")))
    got = render_svg(spec)
    want = golden_path.read_text(encoding="utf-8")
    assert got == want, f"{name}: SVG != golden ({len(got)} vs {len(want)} bytes)"


def test_line_basic_golden():
    _check("basic")


def test_line_styled_golden():
    _check("styled")


def test_line_markers_golden():
    _check("markers")


def test_line_spline_golden():
    _check("spline")


def test_line_gradient_golden():
    _check("gradient")


def test_line_dark_golden():
    _check("dark")


def test_line_adversarial_golden():
    _check("adversarial")


def test_xss_escaping():
    """Hostile strings in every user-facing field must be escaped, never injected."""
    x = '"><script>alert(1)</script>'
    spec = ChartSpec.from_dict({
        "id": x, "type": "line", "title": x, "subtitle": x,
        "theme": {"name": "light", "gridColor": x, "palette": [x]},
        "xAxis": {"title": x, "categories": [x, "b", "c"]}, "yAxis": {"title": x},
        "series": [{"name": x, "data": [1, 2, 3], "color": x,
                    "pattern": {"type": "hatch", "color": x, "background": x},
                    "fillOpacity": 0.3}],
    })
    from peakcharts.render import render_html
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
    cases = json.loads(
        (ROOT / "charts" / "line-basic" / "invalid-fixtures.json").read_text(encoding="utf-8")
    )
    assert cases, "no invalid fixtures"
    for c in cases:
        assert validate(c["spec"]) == c["errors"], c["spec"]
        try:
            ChartSpec.from_dict(c["spec"])
            raise AssertionError(f"not rejected: {c['spec']}")
        except SpecError:
            pass


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
    for _n in CASES:
        _check(_n)
        print(f"PASS: python line-{_n} golden")
    test_spline_edge_cases()
    print("PASS: python spline edge cases")
