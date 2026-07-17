"""Pin the Python renderer to the shared cross-language golden.

The Go renderer pins to the same golden (libs/go/render_test.go). When both
pass, the two libraries are provably byte-identical for this chart.

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


def test_line_basic_golden():
    spec_path = ROOT / "charts" / "line-basic" / "examples" / "basic.json"
    golden_path = ROOT / "charts" / "line-basic" / "golden" / "basic.svg"
    spec = ChartSpec.from_dict(json.loads(spec_path.read_text(encoding="utf-8")))
    got = render_svg(spec)
    want = golden_path.read_text(encoding="utf-8")
    assert got == want, f"SVG != golden ({len(got)} vs {len(want)} bytes)"


if __name__ == "__main__":
    test_line_basic_golden()
    print("PASS: python line-basic golden")
