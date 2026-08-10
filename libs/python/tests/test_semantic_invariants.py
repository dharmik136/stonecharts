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
        assert count == len(s.data), (
            f"series {si}: bin counts {count} != observations {len(s.data)}"
        )


# ── SC-SEM-002  Waterfall: closing_total == opening + sum(deltas) ────

def test_waterfall_balance():
    spec_path = ROOT / "charts" / "waterfall" / "examples" / "basic.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)
    last_total = float(bars[-1]["data-total"])
    expected = sum(spec.series[0].data)
    assert last_total == expected, (
        f"closing total {last_total} != sum(deltas) {expected}"
    )


def test_waterfall_balance_with_intermediate_sums():
    spec_path = ROOT / "charts" / "waterfall" / "examples" / "intermediate-sums.json"
    d = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = ChartSpec.from_dict(d)
    svg = render_svg(spec)
    bars = _bars(svg)

    skip = set(d.get("sumIndices", []) + d.get("intermediateSumIndices", []))
    expected = sum(v for i, v in enumerate(spec.series[0].data) if i not in skip)

    last_total = float(bars[-1]["data-total"])
    assert last_total == expected, (
        f"closing total {last_total} != sum(non-sum deltas) {expected}"
    )


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
                assert ra >= rb, (
                    f"bubble {i} (z={za}, r={ra}) smaller than "
                    f"bubble {j} (z={zb}, r={rb})"
                )


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
                assert ra >= rb, (
                    f"bubble {i} (z={za}, r={ra}) smaller than "
                    f"bubble {j} (z={zb}, r={rb})"
                )


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
        assert abs(t - totals[0]) < 0.5, (
            f"category {cat} height {t:.1f} != expected {totals[0]:.1f}"
        )


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

    assert by_cat.get("Q2", 0) < 0.5, (
        f"zero category Q2 has height {by_cat['Q2']:.1f}"
    )
    non_zero = {k: v for k, v in by_cat.items() if k != "Q2"}
    totals = list(non_zero.values())
    for t in totals:
        assert abs(t - totals[0]) < 0.5
