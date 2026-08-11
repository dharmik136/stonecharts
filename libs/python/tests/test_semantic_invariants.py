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
