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

from peakcharts import ChartSpec  # noqa: E402
from peakcharts.render import render_svg  # noqa: E402

CASES = ["basic", "styled", "markers", "spline", "gradient"]


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
