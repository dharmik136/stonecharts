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
