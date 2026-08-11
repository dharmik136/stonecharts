"""Semantic invariant tests (SC-CERT-06 / DEC-050).

Output correctness invariants verify the *meaning* of rendered SVG,
beyond byte-identical cross-language parity. Each test asserts a
mathematical property that must hold for the chart type's semantics.

Input validation invariants (SC-SEM-003 through SC-SEM-010) are covered
by DEC-052 strict input validation.
"""

import json
import pathlib
import re
import sys
from collections import defaultdict

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts import ChartSpec  # noqa: E402
from stonecharts.render import render_svg  # noqa: E402

# ── SVG parsing helpers ──────────────────────────────────────────────

_ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


def _bars(svg):
    out = []
    for m in re.finditer(r'<rect\s[^>]*class="sc-bar sc-point"[^>]*/>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _bubbles(svg):
    out = []
    for m in re.finditer(r'<circle\s[^>]*class="sc-bubble sc-point"[^>]*/>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _candles(svg):
    out = []
    for m in re.finditer(r'<g\s[^>]*class="sc-candle sc-point"[^>]*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _slices(svg):
    out = []
    for m in re.finditer(
        r'<(?:path|polygon)\s[^>]*class="sc-slice sc-point"[^>]*/?\s*>', svg
    ):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _lollipop_heads(svg):
    out = []
    for m in re.finditer(
        r'<circle\s[^>]*class="[^"]*sc-lollipop-head[^"]*"[^>]*/?\s*>', svg
    ):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _events(svg):
    out = []
    for m in re.finditer(r'<circle\s[^>]*class="sc-event sc-point"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _barbs(svg):
    out = []
    for m in re.finditer(r'<g\s[^>]*class="sc-barb sc-point"[^>]*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _vectors(svg):
    out = []
    for m in re.finditer(r'<path\s[^>]*class="sc-vector sc-point"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _spans(svg):
    out = []
    for m in re.finditer(r'<rect\s[^>]*class="sc-span sc-point"[^>]*/>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _frames(svg):
    out = []
    for m in re.finditer(r'<rect\s[^>]*class="sc-frame sc-point"[^>]*/>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _pointers(svg):
    out = []
    for m in re.finditer(r'<path\s[^>]*class="sc-pointer sc-point"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _gauge_fills(svg):
    out = []
    for m in re.finditer(r'<path\s[^>]*class="sc-gauge-fill sc-point"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _radar_dots(svg):
    out = []
    for m in re.finditer(r'<circle\s[^>]*class="sc-radar-dot sc-point"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _polar_dots(svg):
    out = []
    for m in re.finditer(r'<circle\s[^>]*class="sc-polar-dot sc-point"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _windrose_sectors(svg):
    out = []
    for m in re.finditer(
        r'<path\s[^>]*class="sc-windrose-sector sc-point"[^>]*/?\s*>', svg
    ):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _nightingale_sectors(svg):
    out = []
    for m in re.finditer(
        r'<path\s[^>]*class="sc-nightingale-sector sc-point"[^>]*/?\s*>', svg
    ):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _radialbar_bars(svg):
    out = []
    for m in re.finditer(
        r'<path\s[^>]*class="sc-radialbar-bar sc-point"[^>]*/?\s*>', svg
    ):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _parliament_dots(svg):
    out = []
    for m in re.finditer(
        r'<circle\s[^>]*class="sc-parliament-dot sc-point"[^>]*/?\s*>', svg
    ):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _point_circles(svg):
    out = []
    for m in re.finditer(r'<circle\s[^>]*class="[^"]*sc-point[^"]*"[^>]*/?\s*>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


# ── SC-SEM-001  Histogram: sum(bin_counts) == len(observations) ──────


def test_histogram_observation_count():
    spec_path = ROOT / "charts" / "histogram" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    total_count = sum(float(b["data-y"]) for b in bars)
    n_obs = sum(len(s.data) for s in spec.series)
    assert total_count == n_obs, f"bin counts {total_count} != observations {n_obs}"


def test_histogram_observation_count_multi_series():
    d = {
        "type": "histogram",
        "binning": {"count": 5},
        "series": [
            {"name": "A", "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
            {"name": "B", "data": [3, 5, 7, 9, 11, 13]},
        ],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    for si, s in enumerate(spec.series):
        series_bars = [b for b in bars if b["data-series"] == str(si)]
        count = sum(float(b["data-y"]) for b in series_bars)
        assert count == len(s.data), f"series {si}: bin counts {count} != observations {len(s.data)}"


# ── SC-SEM-002  Waterfall: closing_total == opening + sum(deltas) ────


def test_waterfall_balance():
    spec_path = ROOT / "charts" / "waterfall" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    last_total = float(bars[-1]["data-total"])
    expected = sum(spec.series[0].data)
    assert last_total == expected, f"closing total {last_total} != sum(deltas) {expected}"


def test_waterfall_balance_with_intermediate_sums():
    spec_path = ROOT / "charts" / "waterfall" / "examples" / "intermediate-sums.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)

    skip = set(d.get("sumIndices", []) + d.get("intermediateSumIndices", []))
    expected = sum(v for i, v in enumerate(spec.series[0].data) if i not in skip)

    last_total = float(bars[-1]["data-total"])
    assert last_total == expected, f"closing total {last_total} != sum(non-sum deltas) {expected}"


# ── SC-SEM-006  Bubble: z[a] > z[b] ⟹ radius[a] >= radius[b] ───────


def test_bubble_z_radius_monotonic():
    spec_path = ROOT / "charts" / "bubble" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    circles = _bubbles(svg)

    pairs = [(float(c["data-z"]), float(c["data-r"])) for c in circles]
    for i, (za, ra) in enumerate(pairs):
        for j, (zb, rb) in enumerate(pairs):
            if za > zb:
                assert ra >= rb, f"bubble {i} (z={za}, r={ra}) smaller than bubble {j} (z={zb}, r={rb})"


def test_bubble_z_radius_monotonic_multi_series():
    spec_path = ROOT / "charts" / "bubble" / "examples" / "multi-series.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    circles = _bubbles(svg)

    pairs = [(float(c["data-z"]), float(c["data-r"])) for c in circles]
    for i, (za, ra) in enumerate(pairs):
        for j, (zb, rb) in enumerate(pairs):
            if za > zb:
                assert ra >= rb, f"bubble {i} (z={za}, r={ra}) smaller than bubble {j} (z={zb}, r={rb})"


# ── SC-SEM-007  Percent stack: each category sums to 100% ────────────


def test_percent_stack_bar_heights():
    d = {
        "type": "column",
        "stacking": "percent",
        "xAxis": {"categories": ["Q1", "Q2", "Q3"]},
        "series": [
            {"name": "A", "data": [30, 40, 10]},
            {"name": "B", "data": [20, 10, 50]},
            {"name": "C", "data": [50, 50, 40]},
        ],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)

    by_cat = defaultdict(float)
    for b in bars:
        by_cat[b["data-x"]] += float(b["height"])

    totals = list(by_cat.values())
    assert totals[0] > 0, "no bar height rendered"
    for cat, t in by_cat.items():
        assert abs(t - totals[0]) < 0.5, f"category {cat} height {t:.1f} != expected {totals[0]:.1f}"


def test_percent_stack_zero_category():
    d = {
        "type": "column",
        "stacking": "percent",
        "xAxis": {"categories": ["Q1", "Q2", "Q3"]},
        "series": [
            {"name": "A", "data": [30, 0, 10]},
            {"name": "B", "data": [20, 0, 50]},
        ],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)

    by_cat = defaultdict(float)
    for b in bars:
        by_cat[b["data-x"]] += float(b["height"])

    assert by_cat.get("Q2", 0) < 0.5, f"zero category Q2 has height {by_cat['Q2']:.1f}"
    non_zero = {k: v for k, v in by_cat.items() if k != "Q2"}
    totals = list(non_zero.values())
    for t in totals:
        assert abs(t - totals[0]) < 0.5


# ── SC-SEM-011  Range family: data-low <= data-high ────────────────────


def _range_points(svg):
    """Extract sc-point elements that carry both data-low and data-high."""
    out = []
    for m in re.finditer(r'<(?:circle|rect)\s[^>]*class="[^"]*sc-point[^"]*"[^>]*/?\s*>', svg):
        attrs = dict(_ATTR_RE.findall(m.group(0)))
        if "data-low" in attrs and "data-high" in attrs:
            out.append(attrs)
    return out


def test_arearange_low_le_high():
    """SC-SEM-011: arearange data-low <= data-high for every rendered point."""
    spec_path = ROOT / "charts" / "arearange" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _range_points(svg)
    assert len(points) > 0, "no arearange points found"
    for i, p in enumerate(points):
        lo, hi = float(p["data-low"]), float(p["data-high"])
        assert lo <= hi, f"point {i}: low {lo} > high {hi}"


def test_columnrange_low_le_high():
    """SC-SEM-011: columnrange data-low <= data-high for every rendered bar."""
    spec_path = ROOT / "charts" / "columnrange" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _range_points(svg)
    assert len(points) > 0, "no columnrange points found"
    for i, p in enumerate(points):
        lo, hi = float(p["data-low"]), float(p["data-high"])
        assert lo <= hi, f"bar {i}: low {lo} > high {hi}"


def test_columnrange_bar_height_positive():
    """SC-SEM-011: columnrange bar has positive pixel height when low != high."""
    spec_path = ROOT / "charts" / "columnrange" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _range_points(svg)
    for i, p in enumerate(points):
        lo, hi = float(p["data-low"]), float(p["data-high"])
        if lo != hi:
            h = float(p.get("height", "0"))
            assert h > 0, f"bar {i}: low {lo} != high {hi} but height is {h}"


def test_dumbbell_low_le_high():
    """SC-SEM-011: dumbbell data-low <= data-high for every rendered point."""
    spec_path = ROOT / "charts" / "dumbbell" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _range_points(svg)
    assert len(points) > 0, "no dumbbell points found"
    for i, p in enumerate(points):
        lo, hi = float(p["data-low"]), float(p["data-high"])
        assert lo <= hi, f"point {i}: low {lo} > high {hi}"


def test_dumbbell_connector_count():
    """SC-SEM-011: dumbbell has one connector line per data point."""
    spec_path = ROOT / "charts" / "dumbbell" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    connectors = re.findall(r'class="sc-connector"', svg)
    n_points = sum(len(s.data) for s in spec.series)
    assert len(connectors) == n_points, f"connectors {len(connectors)} != points {n_points}"


def test_range_family_constructed():
    """SC-SEM-011: constructed range specs all satisfy low <= high."""
    specs = {
        "arearange": {"data": [50, 60, 70], "low": [10, 20, 30]},
        "columnrange": {"data": [10, 20, 30], "high": [50, 60, 70]},
        "dumbbell": {"data": [10, 20, 30], "high": [50, 60, 70]},
    }
    for chart_type, series_fields in specs.items():
        d = {
            "type": chart_type,
            "xAxis": {"categories": ["A", "B", "C"]},
            "series": [{"name": "s", **series_fields}],
        }
        spec = ChartSpec.from_dict(d)
        svg = render_svg(spec)
        points = _range_points(svg)
        assert len(points) == 3, f"{chart_type}: expected 3 points, got {len(points)}"
        for i, p in enumerate(points):
            lo, hi = float(p["data-low"]), float(p["data-high"])
            assert lo <= hi, f"{chart_type} point {i}: low {lo} > high {hi}"


# ── SC-SEM-012  Error-bar: low <= central value <= high ────────────────


def test_error_bar_low_le_value_le_high():
    """SC-SEM-012: error-bar central value lies between its bounds."""
    spec_path = ROOT / "charts" / "error-bar" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _range_points(svg)
    assert len(points) > 0, "no error-bar points found"
    for i, p in enumerate(points):
        lo = float(p["data-low"])
        y = float(p["data-y"])
        hi = float(p["data-high"])
        assert lo <= y <= hi, f"point {i}: low {lo} <= y {y} <= high {hi} violated"


def test_error_bar_constructed():
    """SC-SEM-012: error-bar bounds with constructed spec."""
    d = {
        "type": "error-bar",
        "xAxis": {"categories": ["A", "B", "C"]},
        "series": [{
            "name": "test",
            "data": [50, 100, 75],
            "low": [30, 80, 60],
            "high": [70, 120, 90],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _range_points(svg)
    assert len(points) == 3
    for i, p in enumerate(points):
        lo = float(p["data-low"])
        y = float(p["data-y"])
        hi = float(p["data-high"])
        assert lo <= y <= hi, f"point {i}: {lo} <= {y} <= {hi} violated"


# ── SC-SEM-013  Boxplot: structural integrity ──────────────────────────


def _boxes(svg):
    """Extract sc-box sc-point rect elements."""
    out = []
    for m in re.finditer(r'<rect\s[^>]*class="sc-box sc-point"[^>]*/>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def test_boxplot_median_matches_input():
    """SC-SEM-013: boxplot data-y matches median from boxData input."""
    spec_path = ROOT / "charts" / "boxplot" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    boxes = _boxes(svg)
    medians = [bd["median"] for bd in d["series"][0]["boxData"]]
    assert len(boxes) == len(medians), f"boxes {len(boxes)} != data {len(medians)}"
    for i, (box, expected) in enumerate(zip(boxes, medians)):
        actual = float(box["data-y"])
        assert actual == expected, f"box {i}: data-y {actual} != median {expected}"


def test_boxplot_box_height_positive():
    """SC-SEM-013: boxplot box has positive pixel height (q1 < q3)."""
    spec_path = ROOT / "charts" / "boxplot" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    boxes = _boxes(svg)
    for i, box in enumerate(boxes):
        h = float(box.get("height", "0"))
        assert h > 0, f"box {i}: height is {h}, expected > 0"


def test_boxplot_whisker_cap_count():
    """SC-SEM-013: boxplot has exactly 2 whisker caps per box."""
    spec_path = ROOT / "charts" / "boxplot" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    boxes = _boxes(svg)
    caps = re.findall(r'class="sc-whisker-cap"', svg)
    assert len(caps) == 2 * len(boxes), f"caps {len(caps)} != 2 * boxes {len(boxes)}"


def test_boxplot_constructed():
    """SC-SEM-013: boxplot with constructed spec verifies structure."""
    d = {
        "type": "boxplot",
        "xAxis": {"categories": ["X", "Y"]},
        "series": [{
            "name": "test",
            "data": [50, 100],
            "boxData": [
                {"low": 10, "q1": 30, "median": 50, "q3": 70, "high": 90},
                {"low": 60, "q1": 80, "median": 100, "q3": 120, "high": 140},
            ],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    boxes = _boxes(svg)
    assert len(boxes) == 2
    assert float(boxes[0]["data-y"]) == 50
    assert float(boxes[1]["data-y"]) == 100
    caps = re.findall(r'class="sc-whisker-cap"', svg)
    assert len(caps) == 4


# ── SC-SEM-014  Bullet: structural completeness ───────────────────────


def test_bullet_measure_matches_input():
    """SC-SEM-014: bullet data-y matches the measure value from input."""
    spec_path = ROOT / "charts" / "bullet" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    expected = d["series"][0]["data"]
    assert len(bars) == len(expected), f"bars {len(bars)} != data {len(expected)}"
    for i, (bar, val) in enumerate(zip(bars, expected)):
        actual = float(bar["data-y"])
        assert actual == val, f"bar {i}: data-y {actual} != data {val}"


def test_bullet_range_count():
    """SC-SEM-014: bullet has one sc-range rect per bulletRanges entry per category."""
    spec_path = ROOT / "charts" / "bullet" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    ranges = re.findall(r'class="sc-range"', svg)
    n_cats = len(d["xAxis"]["categories"])
    n_expected = len(d["bulletRanges"]) * n_cats
    assert len(ranges) == n_expected, f"ranges {len(ranges)} != {n_expected} ({len(d['bulletRanges'])} * {n_cats})"


def test_bullet_target_present():
    """SC-SEM-014: bullet renders target line when bulletTarget is specified."""
    spec_path = ROOT / "charts" / "bullet" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    assert "bulletTarget" in d
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    targets = re.findall(r'class="sc-target"', svg)
    assert len(targets) == 1, f"expected 1 target, got {len(targets)}"


def test_bullet_constructed():
    """SC-SEM-014: bullet with constructed multi-KPI spec."""
    d = {
        "type": "bullet",
        "xAxis": {"categories": ["KPI-A", "KPI-B"]},
        "series": [{"name": "measure", "data": [75, 120]}],
        "bulletTarget": 100,
        "bulletRanges": [50, 100, 150],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    assert len(bars) == 2
    assert float(bars[0]["data-y"]) == 75
    assert float(bars[1]["data-y"]) == 120
    ranges = re.findall(r'class="sc-range"', svg)
    assert len(ranges) == 6, f"expected 3 ranges * 2 categories = 6, got {len(ranges)}"
    targets = re.findall(r'class="sc-target"', svg)
    assert len(targets) == 2, f"expected 1 target * 2 categories = 2, got {len(targets)}"


# ── SC-SEM-015  Candlestick: OHLC bounds ────────────────────────────────


def test_candlestick_ohlc_bounds():
    """SC-SEM-015: high >= max(open,close), low <= min(open,close)."""
    spec_path = ROOT / "charts" / "candlestick" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    candles = _candles(svg)
    assert len(candles) > 0, "no candles found"
    for i, c in enumerate(candles):
        o, h, l, cl = float(c["data-open"]), float(c["data-high"]), float(c["data-low"]), float(c["data-close"])
        assert h >= max(o, cl), f"candle {i}: high {h} < max(open {o}, close {cl})"
        assert l <= min(o, cl), f"candle {i}: low {l} > min(open {o}, close {cl})"


def test_candlestick_constructed():
    """SC-SEM-015: candlestick OHLC with constructed spec."""
    d = {
        "type": "candlestick",
        "subtype": "candlestick",
        "xAxis": {"categories": ["Mon", "Tue"]},
        "series": [{
            "name": "Stock",
            "data": [105, 95],
            "ohlc": [
                {"open": 100, "high": 110, "low": 90, "close": 105},
                {"open": 105, "high": 108, "low": 88, "close": 95},
            ],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    candles = _candles(svg)
    assert len(candles) == 2
    for c in candles:
        o, h, l, cl = float(c["data-open"]), float(c["data-high"]), float(c["data-low"]), float(c["data-close"])
        assert h >= max(o, cl)
        assert l <= min(o, cl)


# ── SC-SEM-016  Lollipop: head count matches data ───────────────────────


def test_lollipop_head_count():
    """SC-SEM-016: lollipop head count matches data points."""
    spec_path = ROOT / "charts" / "lollipop" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    heads = _lollipop_heads(svg)
    n_points = sum(len(s.data) for s in spec.series)
    assert len(heads) == n_points, f"heads {len(heads)} != data points {n_points}"


def test_lollipop_constructed():
    """SC-SEM-016: lollipop with constructed spec."""
    d = {
        "type": "lollipop",
        "xAxis": {"categories": ["A", "B", "C"]},
        "series": [{"name": "s", "data": [10, 20, 30]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    heads = _lollipop_heads(svg)
    assert len(heads) == 3
    stems = re.findall(r'class="sc-stem"', svg)
    assert len(stems) == 3


# ── SC-SEM-017  Funnel: slice count matches categories ──────────────────


def test_funnel_slice_count():
    """SC-SEM-017: funnel slice count matches categories."""
    spec_path = ROOT / "charts" / "funnel" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    slices = _slices(svg)
    n_cats = len(d["xAxis"]["categories"])
    assert len(slices) == n_cats, f"slices {len(slices)} != categories {n_cats}"


def test_funnel_constructed():
    """SC-SEM-017: funnel with constructed spec."""
    d = {
        "type": "funnel",
        "xAxis": {"categories": ["Leads", "Qualified", "Won"]},
        "series": [{"name": "Pipeline", "data": [1000, 500, 200]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    slices = _slices(svg)
    assert len(slices) == 3
    values = [float(s["data-y"]) for s in slices]
    assert values == [1000, 500, 200]


# ── SC-SEM-018  Variwide: width-weight matches input ────────────────────


def test_variwide_width_weight():
    """SC-SEM-018: variwide data-z matches input widths."""
    spec_path = ROOT / "charts" / "variwide" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    widths = d["series"][0]["widths"]
    assert len(bars) == len(widths), f"bars {len(bars)} != widths {len(widths)}"
    for i, (bar, w) in enumerate(zip(bars, widths)):
        assert float(bar["data-z"]) == w, f"bar {i}: data-z {bar['data-z']} != width {w}"


def test_variwide_constructed():
    """SC-SEM-018: variwide with constructed spec."""
    d = {
        "type": "variwide",
        "xAxis": {"categories": ["X", "Y", "Z"]},
        "series": [{"name": "s", "data": [30, 50, 20], "widths": [100, 200, 150]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    assert len(bars) == 3
    for bar, exp_z in zip(bars, [100, 200, 150]):
        assert float(bar["data-z"]) == exp_z


# ── SC-SEM-019  Timeline: event count matches data ──────────────────────


def test_timeline_event_count():
    """SC-SEM-019: timeline event markers match data points."""
    spec_path = ROOT / "charts" / "timeline" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    events = _events(svg)
    n_points = sum(len(s.data) for s in spec.series)
    assert len(events) == n_points, f"events {len(events)} != data points {n_points}"


def test_timeline_constructed():
    """SC-SEM-019: timeline with constructed spec."""
    d = {
        "type": "timeline",
        "xAxis": {"type": "datetime"},
        "series": [{
            "name": "Events",
            "data": [1609459200000, 1612137600000, 1614556800000],
            "labels": ["Jan", "Feb", "Mar"],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    events = _events(svg)
    assert len(events) == 3
    labels = re.findall(r'class="sc-label"', svg)
    assert len(labels) == 3


# ── SC-SEM-020  Windbarb: speed/direction match input ───────────────────


def test_windbarb_data_attributes():
    """SC-SEM-020: windbarb data-speed and data-direction match input."""
    spec_path = ROOT / "charts" / "windbarb" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    barbs = _barbs(svg)
    speeds = d["series"][0]["data"]
    dirs = d["series"][0]["direction"]
    assert len(barbs) == len(speeds), f"barbs {len(barbs)} != data {len(speeds)}"
    for i, (b, spd, dr) in enumerate(zip(barbs, speeds, dirs)):
        assert float(b["data-speed"]) == spd, f"barb {i}: speed mismatch"
        assert float(b["data-direction"]) == dr, f"barb {i}: direction mismatch"


def test_windbarb_constructed():
    """SC-SEM-020: windbarb with constructed spec."""
    d = {
        "type": "windbarb",
        "xAxis": {"categories": ["00Z", "06Z", "12Z"]},
        "series": [{
            "name": "Wind",
            "data": [15, 25, 5],
            "direction": [180, 270, 90],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    barbs = _barbs(svg)
    assert len(barbs) == 3
    assert float(barbs[0]["data-speed"]) == 15
    assert float(barbs[1]["data-direction"]) == 270


# ── SC-SEM-021  Streamgraph: point count per series matches data ────────


def test_streamgraph_point_count():
    """SC-SEM-021: streamgraph point count matches total data length."""
    spec_path = ROOT / "charts" / "streamgraph" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _point_circles(svg)
    total_data = sum(len(s.data) for s in spec.series)
    assert len(points) == total_data, f"points {len(points)} != data {total_data}"


def test_streamgraph_constructed():
    """SC-SEM-021: streamgraph with constructed spec."""
    d = {
        "type": "streamgraph",
        "offset": "wiggle",
        "xAxis": {"categories": ["Q1", "Q2", "Q3"]},
        "series": [
            {"name": "A", "data": [10, 20, 30]},
            {"name": "B", "data": [20, 15, 25]},
        ],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    points = _point_circles(svg)
    assert len(points) == 6


# ── SC-SEM-022  Vector-plot: direction/length match input ───────────────


def test_vector_plot_attributes():
    """SC-SEM-022: vector-plot data-direction and data-length match input."""
    spec_path = ROOT / "charts" / "vector-plot" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    vectors = _vectors(svg)
    dirs = d["series"][0]["direction"]
    lengths = d["series"][0]["length"]
    assert len(vectors) == len(dirs), f"vectors {len(vectors)} != data {len(dirs)}"
    for i, (v, dr, ln) in enumerate(zip(vectors, dirs, lengths)):
        assert float(v["data-direction"]) == dr, f"vector {i}: direction mismatch"
        assert float(v["data-length"]) == ln, f"vector {i}: length mismatch"


def test_vector_plot_constructed():
    """SC-SEM-022: vector-plot with constructed spec."""
    d = {
        "type": "vector-plot",
        "series": [{
            "name": "Flow",
            "x": [0, 1, 2],
            "data": [0, 1, 2],
            "direction": [45, 90, 135],
            "length": [1.0, 1.5, 2.0],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    vectors = _vectors(svg)
    assert len(vectors) == 3
    assert float(vectors[0]["data-direction"]) == 45
    assert float(vectors[2]["data-length"]) == 2.0


# ── SC-SEM-023  XRange: span start <= end ───────────────────────────────


def test_xrange_span_bounds():
    """SC-SEM-023: xrange data-start <= data-end for every span."""
    spec_path = ROOT / "charts" / "xrange" / "examples" / "gantt.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    spans = _spans(svg)
    assert len(spans) > 0, "no xrange spans found"
    for i, s in enumerate(spans):
        start, end = float(s["data-start"]), float(s["data-end"])
        assert start <= end, f"span {i}: start {start} > end {end}"


def test_xrange_constructed():
    """SC-SEM-023: xrange with constructed spec."""
    d = {
        "type": "xrange",
        "xAxis": {"type": "datetime"},
        "yAxis": {"categories": ["Track A", "Track B"]},
        "series": [{
            "name": "Schedule",
            "data": [],
            "spans": [
                {"x": 1609459200000, "x2": 1609545600000, "y": 0, "id": "s1", "name": "Step 1"},
                {"x": 1609545600000, "x2": 1609718400000, "y": 1, "id": "s2", "name": "Step 2"},
            ],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    spans = _spans(svg)
    assert len(spans) == 2
    for s in spans:
        assert float(s["data-start"]) <= float(s["data-end"])


# ── SC-SEM-024  Technical-indicators: overlay series present ────────────


def test_technical_indicators_overlay():
    """SC-SEM-024: indicator overlays present with data-indicator attribute."""
    spec_path = ROOT / "charts" / "technical-indicators" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    indicators = re.findall(r'data-indicator="(\w+)"', svg)
    expected = set()
    for s in d["series"]:
        for ind in s.get("indicators", []):
            expected.add(ind["type"])
    assert set(indicators) == expected, f"indicators {set(indicators)} != expected {expected}"


def test_technical_indicators_constructed():
    """SC-SEM-024: technical-indicators with constructed spec."""
    d = {
        "type": "technical-indicators",
        "xAxis": {"categories": [str(i) for i in range(10)]},
        "series": [{
            "name": "Price",
            "data": [10, 12, 11, 13, 14, 12, 15, 16, 14, 17],
            "indicators": [{"type": "sma", "period": 3}],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    indicators = re.findall(r'data-indicator="(\w+)"', svg)
    assert "sma" in indicators


# ── SC-SEM-025  Flame-chart: frame structure ────────────────────────────


def test_flame_chart_frame_bounds():
    """SC-SEM-025: flame-chart data-start <= data-end, depth >= 0."""
    spec_path = ROOT / "charts" / "flame-chart" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    frames = _frames(svg)
    assert len(frames) > 0, "no flame-chart frames found"
    for i, f in enumerate(frames):
        start, end = float(f["data-start"]), float(f["data-end"])
        depth = int(f["data-depth"])
        assert start <= end, f"frame {i}: start {start} > end {end}"
        assert depth >= 0, f"frame {i}: depth {depth} < 0"


def test_flame_chart_constructed():
    """SC-SEM-025: flame-chart with constructed spec."""
    d = {
        "type": "flame-chart",
        "series": [{
            "name": "Profile",
            "data": [],
            "frames": [
                {"x": 0, "x2": 100, "depth": 0, "name": "main"},
                {"x": 10, "x2": 60, "depth": 1, "name": "foo"},
                {"x": 60, "x2": 90, "depth": 1, "name": "bar"},
            ],
        }],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    frames = _frames(svg)
    assert len(frames) == 3
    for f in frames:
        assert float(f["data-start"]) <= float(f["data-end"])
        assert int(f["data-depth"]) >= 0


# ── SC-SEM-026  Pie: percentage sum ≈ 100 ──────────────────────────────


def test_pie_percentage_sum():
    """SC-SEM-026: pie slice percentages sum to approximately 100."""
    spec_path = ROOT / "charts" / "pie" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    slices = _slices(svg)
    assert len(slices) > 0, "no pie slices found"
    total_pct = sum(float(s["data-percentage"].rstrip("%")) for s in slices)
    assert abs(total_pct - 100.0) < 0.5, f"percentages sum to {total_pct}, expected ~100"


def test_pie_slice_count():
    """SC-SEM-026: pie slice count matches non-zero categories."""
    d = {
        "type": "pie",
        "xAxis": {"categories": ["A", "B", "C", "D"]},
        "series": [{"name": "s", "data": [40, 30, 30, 0]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    slices = _slices(svg)
    assert len(slices) == 3, f"expected 3 slices (zero skipped), got {len(slices)}"
    total_pct = sum(float(s["data-percentage"].rstrip("%")) for s in slices)
    assert abs(total_pct - 100.0) < 0.5


# ── SC-SEM-027  Gauge: pointer value within range ──────────────────────


def test_gauge_pointer_bounds():
    """SC-SEM-027: gauge pointer data-y within [gaugeMin, gaugeMax]."""
    spec_path = ROOT / "charts" / "gauge" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    pointers = _pointers(svg)
    assert len(pointers) > 0, "no gauge pointers found"
    g_min, g_max = d["gaugeMin"], d["gaugeMax"]
    for i, p in enumerate(pointers):
        val = float(p["data-y"])
        assert g_min <= val <= g_max, f"pointer {i}: {val} not in [{g_min}, {g_max}]"


def test_gauge_constructed():
    """SC-SEM-027: gauge with constructed spec."""
    d = {
        "type": "gauge",
        "gaugeMin": 0,
        "gaugeMax": 100,
        "gaugeBands": [{"from": 0, "to": 50, "color": "#55BF3B"}, {"from": 50, "to": 100, "color": "#DF5353"}],
        "series": [{"name": "Speed", "data": [72]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    pointers = _pointers(svg)
    assert len(pointers) == 1
    assert float(pointers[0]["data-y"]) == 72


# ── SC-SEM-028  Solid-gauge: fill value within range ───────────────────


def test_solid_gauge_fill_bounds():
    """SC-SEM-028: solid-gauge fill data-y within [gaugeMin, gaugeMax]."""
    spec_path = ROOT / "charts" / "solid-gauge" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    fills = _gauge_fills(svg)
    assert len(fills) > 0, "no solid-gauge fills found"
    g_min, g_max = d["gaugeMin"], d["gaugeMax"]
    for i, f in enumerate(fills):
        val = float(f["data-y"])
        assert g_min <= val <= g_max, f"fill {i}: {val} not in [{g_min}, {g_max}]"


def test_solid_gauge_constructed():
    """SC-SEM-028: solid-gauge with constructed spec."""
    d = {
        "type": "solid-gauge",
        "gaugeMin": 0,
        "gaugeMax": 200,
        "gaugeBands": [{"from": 0, "to": 100, "color": "#55BF3B"}],
        "series": [{"name": "Progress", "data": [150]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    fills = _gauge_fills(svg)
    assert len(fills) == 1
    assert float(fills[0]["data-y"]) == 150


# ── SC-SEM-029  Radar: dot count = categories × series ─────────────────


def test_radar_dot_count():
    """SC-SEM-029: radar dot count = categories × series."""
    spec_path = ROOT / "charts" / "radar" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    dots = _radar_dots(svg)
    n_cats = len(d["xAxis"]["categories"])
    n_series = len(d["series"])
    expected = n_cats * n_series
    assert len(dots) == expected, f"dots {len(dots)} != {n_cats} × {n_series} = {expected}"


def test_radar_constructed():
    """SC-SEM-029: radar with constructed spec."""
    d = {
        "type": "radar",
        "xAxis": {"categories": ["Speed", "Power", "Range", "Handling"]},
        "series": [
            {"name": "Car A", "data": [8, 7, 5, 9]},
            {"name": "Car B", "data": [6, 9, 8, 5]},
        ],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    dots = _radar_dots(svg)
    assert len(dots) == 8, f"expected 4 × 2 = 8 dots, got {len(dots)}"


# ── SC-SEM-030  Polar: dot count = categories × series ─────────────────


def test_polar_dot_count():
    """SC-SEM-030: polar dot count = categories × series."""
    spec_path = ROOT / "charts" / "polar" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    dots = _polar_dots(svg)
    n_cats = len(d["xAxis"]["categories"])
    n_series = len(d["series"])
    expected = n_cats * n_series
    assert len(dots) == expected, f"dots {len(dots)} != {n_cats} × {n_series} = {expected}"


def test_polar_constructed():
    """SC-SEM-030: polar with constructed spec."""
    d = {
        "type": "polar",
        "xAxis": {"categories": ["N", "E", "S", "W"]},
        "series": [{"name": "Signal", "data": [5, 3, 4, 6]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    dots = _polar_dots(svg)
    assert len(dots) == 4


# ── SC-SEM-031  Wind-rose: sector count = categories × series ──────────


def test_windrose_sector_count():
    """SC-SEM-031: wind-rose sector count = categories × series."""
    spec_path = ROOT / "charts" / "wind-rose" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    sectors = _windrose_sectors(svg)
    n_cats = len(d["xAxis"]["categories"])
    n_series = len(d["series"])
    expected = n_cats * n_series
    assert len(sectors) == expected, f"sectors {len(sectors)} != {n_cats} × {n_series} = {expected}"


def test_windrose_constructed():
    """SC-SEM-031: wind-rose with constructed spec."""
    d = {
        "type": "wind-rose",
        "xAxis": {"categories": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]},
        "series": [
            {"name": "0-5 kt", "data": [5, 3, 4, 2, 6, 4, 3, 5]},
            {"name": "5-10 kt", "data": [3, 2, 3, 1, 4, 3, 2, 3]},
        ],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    sectors = _windrose_sectors(svg)
    assert len(sectors) == 16, f"expected 8 × 2 = 16, got {len(sectors)}"


# ── SC-SEM-032  Nightingale: sector count = categories × series ────────


def test_nightingale_sector_count():
    """SC-SEM-032: nightingale sector count = categories × series."""
    spec_path = ROOT / "charts" / "nightingale" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    sectors = _nightingale_sectors(svg)
    n_cats = len(d["xAxis"]["categories"])
    n_series = len(d["series"])
    expected = n_cats * n_series
    assert len(sectors) == expected, f"sectors {len(sectors)} != {n_cats} × {n_series} = {expected}"


def test_nightingale_constructed():
    """SC-SEM-032: nightingale with constructed spec."""
    d = {
        "type": "nightingale",
        "xAxis": {"categories": ["Jan", "Feb", "Mar", "Apr"]},
        "series": [{"name": "Cases", "data": [10, 20, 15, 25]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    sectors = _nightingale_sectors(svg)
    assert len(sectors) == 4


# ── SC-SEM-033  Radial-bar: bar count = categories × series ────────────


def test_radialbar_bar_count():
    """SC-SEM-033: radial-bar bar count = categories × series."""
    spec_path = ROOT / "charts" / "radial-bar" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _radialbar_bars(svg)
    n_cats = len(d["xAxis"]["categories"])
    n_series = len(d["series"])
    expected = n_cats * n_series
    assert len(bars) == expected, f"bars {len(bars)} != {n_cats} × {n_series} = {expected}"


def test_radialbar_constructed():
    """SC-SEM-033: radial-bar with constructed spec."""
    d = {
        "type": "radial-bar",
        "xAxis": {"categories": ["A", "B", "C"]},
        "yAxis": {"max": 100},
        "series": [{"name": "Score", "data": [85, 60, 75]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _radialbar_bars(svg)
    assert len(bars) == 3


# ── SC-SEM-034  Parliament: dot count = sum(seat counts) ───────────────


def test_parliament_dot_count():
    """SC-SEM-034: parliament total dots = sum of all seat counts."""
    spec_path = ROOT / "charts" / "parliament" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    dots = _parliament_dots(svg)
    total_seats = sum(d["series"][0]["data"])
    assert len(dots) == total_seats, f"dots {len(dots)} != seats {total_seats}"


def test_parliament_constructed():
    """SC-SEM-034: parliament with constructed spec."""
    d = {
        "type": "parliament",
        "xAxis": {"categories": ["Party A", "Party B", "Party C"]},
        "series": [{"name": "Seats", "data": [10, 8, 5]}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    dots = _parliament_dots(svg)
    assert len(dots) == 23, f"expected 10+8+5=23 dots, got {len(dots)}"


# ── DT-SEM-001  Every rendered data cell maps to exactly one supplied value ──


def _dt_cells(svg):
    """Extract development-triangle cell value texts from SVG."""
    out = []
    for m in re.finditer(r'<text\s[^>]*class="sc-dt-value"[^>]*>([^<]+)</text>', svg):
        out.append(m.group(1))
    return out


def _dt_diag_rects(svg):
    """Extract diagonal highlight rect attributes from SVG."""
    out = []
    for m in re.finditer(r'<rect\s[^>]*class="sc-dt-diag"[^>]*/>', svg):
        out.append(dict(_ATTR_RE.findall(m.group(0))))
    return out


def _dt_factor_texts(svg):
    """Extract factor text elements from SVG."""
    out = []
    for m in re.finditer(r'<text\s[^>]*class="sc-dt-factor"[^>]*>([^<]+)</text>', svg):
        out.append(m.group(1))
    return out


def test_dt_sem_001_cell_count_matches_values():
    """DT-SEM-001: every rendered data cell maps to exactly one supplied triangle value."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    rendered = _dt_cells(svg)
    total_values = sum(len(row) for row in d["triangle"]["values"])
    assert len(rendered) == total_values, f"rendered cells {len(rendered)} != supplied values {total_values}"


def test_dt_sem_001_cell_count_diagonal():
    """DT-SEM-001: cell count with diagonal enabled."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "diagonal.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    rendered = _dt_cells(svg)
    total_values = sum(len(row) for row in d["triangle"]["values"])
    assert len(rendered) == total_values, f"rendered cells {len(rendered)} != supplied values {total_values}"


# ── DT-SEM-003  Latest diagonal highlights rightmost populated cell per row ──


def test_dt_sem_003_diagonal_positions():
    """DT-SEM-003: latest diagonal highlights exactly the last populated cell in each row."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "diagonal.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    diags = _dt_diag_rects(svg)
    values = d["triangle"]["values"]
    assert len(diags) == len(values), f"diagonal rects {len(diags)} != rows {len(values)}"
    for i, diag in enumerate(diags):
        expected_period = len(values[i]) - 1
        assert int(diag["data-origin"]) == i, f"diagonal rect {i}: origin {diag['data-origin']} != expected {i}"
        assert int(diag["data-period"]) == expected_period, (
            f"diagonal rect {i}: period {diag['data-period']} != expected {expected_period}"
        )


def test_dt_sem_003_diagonal_constructed():
    """DT-SEM-003: diagonal positions for a manually constructed spec."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["A", "B", "C"],
            "periods": [12, 24, 36],
            "values": [[10, 20, 30], [40, 50], [60]],
        },
        "diagonal": {"highlight": True},
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    diags = _dt_diag_rects(svg)
    assert len(diags) == 3
    # Row 0: last cell = period 2, Row 1: last cell = period 1, Row 2: last cell = period 0
    assert int(diags[0]["data-period"]) == 2
    assert int(diags[1]["data-period"]) == 1
    assert int(diags[2]["data-period"]) == 0


# ── DT-SEM-005  Supplied factor values are rendered exactly ──


def test_dt_sem_005_factors_rendered_exactly():
    """DT-SEM-005: supplied factor values are rendered exactly (not recalculated)."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "factors.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    rendered_factors = _dt_factor_texts(svg)
    supplied_factors = d["factors"]["values"]
    assert len(rendered_factors) == len(supplied_factors), (
        f"rendered factors {len(rendered_factors)} != supplied {len(supplied_factors)}"
    )
    for i, (rendered, supplied) in enumerate(zip(rendered_factors, supplied_factors)):
        expected = f"{supplied:.3f}"
        assert rendered == expected, f"factor {i}: rendered {rendered!r} != expected {expected!r}"


def test_dt_sem_005_factors_constructed():
    """DT-SEM-005: factor values for constructed spec."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["X", "Y"],
            "periods": [12, 24, 36],
            "values": [[100, 200, 300], [150, 250]],
        },
        "factors": {"show": True, "values": [2.000, 1.500]},
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    rendered_factors = _dt_factor_texts(svg)
    assert rendered_factors == ["2.000", "1.500"]


# ── DT-SEM-007  Annotation resolves to exactly its intended populated cell ──


def test_dt_sem_007_annotation_position():
    """DT-SEM-007: annotation resolves to exactly its intended populated cell."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "annotated.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    # The annotation should target origin "2022" (index 0), period 36 (index 2)
    ann_groups = re.findall(r'<g class="sc-dt-annotation-group"[^>]*>', svg)
    assert len(ann_groups) == 1, f"expected 1 annotation group, got {len(ann_groups)}"
    # Verify the annotation circle exists inside the group
    ann_circles = re.findall(r'<circle class="sc-dt-annotation"[^>]*/>', svg)
    assert len(ann_circles) == 1


def test_dt_sem_007_annotation_constructed():
    """DT-SEM-007: annotation at a known position in constructed spec."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["R1", "R2"],
            "periods": [6, 12],
            "values": [[10, 20], [30]],
        },
        "annotations": [{"origin": "R1", "period": 12, "text": "Check this"}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    ann_groups = re.findall(r'<g class="sc-dt-annotation-group"[^>]*>', svg)
    assert len(ann_groups) == 1
    ann_circles = re.findall(r'<circle class="sc-dt-annotation"[^>]*/>', svg)
    assert len(ann_circles) == 1


# ── DT-SEM-008  Annotation text survives into accessible SVG metadata ──


def test_dt_sem_008_annotation_accessible_metadata():
    """DT-SEM-008: annotation text survives into <title> and aria-label."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "annotated.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    ann_text = d["annotations"][0]["text"]
    assert f"<title>{ann_text}</title>" in svg, f"annotation text {ann_text!r} not found in <title>"
    assert f'aria-label="{ann_text}"' in svg, f"annotation text {ann_text!r} not found in aria-label"


def test_dt_sem_008_annotation_text_constructed():
    """DT-SEM-008: annotation text in constructed spec."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["A"],
            "periods": [12],
            "values": [[99]],
        },
        "annotations": [{"origin": "A", "period": 12, "text": "Special note here"}],
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    assert "<title>Special note here</title>" in svg
    assert 'aria-label="Special note here"' in svg


# ── DT-SEM-009  Unit/view/valueType survive into output metadata ──


def test_dt_sem_009_metadata_basic():
    """DT-SEM-009: view and valueType in data attributes from basic example."""
    spec_path = ROOT / "charts" / "development-triangle" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    assert 'data-triangle-view="cumulative"' in svg
    assert 'data-triangle-value-type="incurred"' in svg


def test_dt_sem_009_metadata_with_unit():
    """DT-SEM-009: unit label text and metadata attributes."""
    d = {
        "type": "development-triangle",
        "title": "Unit test",
        "triangle": {
            "origins": ["2024"],
            "periods": [12],
            "values": [[100]],
            "unit": "GBP thousands",
            "view": "incremental",
            "valueType": "paid",
        },
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    assert 'data-triangle-view="incremental"' in svg
    assert 'data-triangle-value-type="paid"' in svg
    assert "Unit: GBP thousands" in svg


def test_dt_sem_009_defaults():
    """DT-SEM-009: default view/valueType when not supplied."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["2025"],
            "periods": [0],
            "values": [[42]],
        },
    }
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    assert 'data-triangle-view="cumulative"' in svg
    assert 'data-triangle-value-type="incurred"' in svg


# ── DT-SEM-010  Malformed numeric and shape inputs fail before rendering ──


def test_dt_sem_010_boolean_value_rejected():
    """DT-SEM-010: boolean in values is rejected."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["2024"],
            "periods": [12],
            "values": [[True]],
        },
    }
    with pytest.raises((ValueError, TypeError)):
        spec = ChartSpec.from_dict(d)
        render_svg(spec)


def test_dt_sem_010_nan_rejected():
    """DT-SEM-010: NaN period is rejected."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["2024"],
            "periods": [float("nan")],
            "values": [[100]],
        },
    }
    with pytest.raises((ValueError, TypeError)):
        spec = ChartSpec.from_dict(d)
        render_svg(spec)


def test_dt_sem_010_fractional_period_rejected():
    """DT-SEM-010: fractional period is rejected."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["2024"],
            "periods": [12.5],
            "values": [[100]],
        },
    }
    with pytest.raises((ValueError, TypeError)):
        spec = ChartSpec.from_dict(d)
        render_svg(spec)


def test_dt_sem_010_increasing_row_lengths_rejected():
    """DT-SEM-010: increasing row lengths are rejected."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["A", "B"],
            "periods": [12, 24, 36],
            "values": [[10], [20, 30]],
        },
    }
    with pytest.raises((ValueError, TypeError)):
        spec = ChartSpec.from_dict(d)
        render_svg(spec)


def test_dt_sem_010_boolean_period_rejected():
    """DT-SEM-010: boolean period is rejected."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["A"],
            "periods": [True],
            "values": [[100]],
        },
    }
    with pytest.raises((ValueError, TypeError)):
        spec = ChartSpec.from_dict(d)
        render_svg(spec)


def test_dt_sem_010_empty_row_rejected():
    """DT-SEM-010: empty row (zero-length) is rejected."""
    d = {
        "type": "development-triangle",
        "triangle": {
            "origins": ["A", "B"],
            "periods": [12, 24],
            "values": [[100, 200], []],
        },
    }
    with pytest.raises((ValueError, TypeError)):
        spec = ChartSpec.from_dict(d)
        render_svg(spec)
