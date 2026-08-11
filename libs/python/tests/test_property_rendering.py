from __future__ import annotations

import random

from stonecharts import ChartSpec
from stonecharts.render import render_svg


def _series_data(rng: random.Random, count: int) -> list[float]:
    return [round(rng.uniform(-100, 100), 3) for _ in range(count)]


def _pos_data(rng: random.Random, count: int) -> list[float]:
    return [round(rng.uniform(1, 100), 2) for _ in range(count)]


def _point_data(rng: random.Random, count: int, z: bool = False) -> list[list[float]]:
    points = []
    for _ in range(count):
        x = round(rng.uniform(-50, 50), 3)
        y = round(rng.uniform(-50, 50), 3)
        if z:
            points.append([x, y, round(rng.uniform(0, 100), 3)])
        else:
            points.append([x, y])
    return points


def _specs():
    rng = random.Random(20260803)

    # ── Category-value family ──
    for chart_type in ("line", "column", "area", "bar",
                       "lollipop", "nightingale", "radial-bar"):
        for case in range(8):
            points = rng.randint(1, 12)
            series_count = rng.randint(1, 4)
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "xAxis": {"categories": [f"C{i}" for i in range(points)]},
                "series": [{"name": f"S{s}", "data": _series_data(rng, points)}
                           for s in range(series_count)],
            }

    # ── Streamgraph (positive values — represents flow volumes) ──
    for case in range(8):
        points = rng.randint(3, 12)
        series_count = rng.randint(2, 4)
        yield {
            "type": "streamgraph",
            "title": f"streamgraph property {case}",
            "xAxis": {"categories": [f"C{i}" for i in range(points)]},
            "series": [{"name": f"S{s}", "data": _pos_data(rng, points)}
                       for s in range(series_count)],
        }

    # ── Combo ──
    for case in range(8):
        points = rng.randint(1, 12)
        col_count = rng.randint(1, 3)
        line_count = rng.randint(1, 2)
        series = [
            {"name": f"Col{s}", "type": "column", "data": _series_data(rng, points)}
            for s in range(col_count)
        ] + [
            {"name": f"Line{s}", "type": "line", "data": _series_data(rng, points)}
            for s in range(line_count)
        ]
        yield {
            "type": "combo",
            "title": f"combo property {case}",
            "xAxis": {"categories": [f"C{i}" for i in range(points)]},
            "series": series,
        }

    # ── Point models ──
    for chart_type, has_z in (("scatter", False), ("bubble", True)):
        for case in range(8):
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "series": [{"name": "S0", "data": _point_data(rng, rng.randint(1, 12), z=has_z)}],
            }

    # ── Variwide ──
    for case in range(8):
        points = rng.randint(1, 8)
        yield {
            "type": "variwide",
            "title": f"variwide property {case}",
            "xAxis": {"categories": [f"C{i}" for i in range(points)]},
            "series": [{"name": "S0", "data": _series_data(rng, points),
                        "widths": [round(rng.uniform(1, 20), 2) for _ in range(points)]}],
        }

    # ── Windbarb ──
    for case in range(8):
        points = rng.randint(1, 12)
        yield {
            "type": "windbarb",
            "title": f"windbarb property {case}",
            "xAxis": {"categories": [f"T{i}" for i in range(points)]},
            "series": [{"name": "S0",
                        "data": [round(rng.uniform(0, 40), 1) for _ in range(points)],
                        "direction": [round(rng.uniform(0, 360), 1) for _ in range(points)]}],
        }

    # ── Range family ──
    for chart_type in ("arearange", "columnrange", "error-bar", "dumbbell"):
        for case in range(8):
            points = rng.randint(1, 8)
            centers = [round(rng.uniform(10, 90), 2) for _ in range(points)]
            spreads = [round(rng.uniform(1, 20), 2) for _ in range(points)]
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "xAxis": {"categories": [f"C{i}" for i in range(points)]},
                "series": [{"name": "S0",
                            "data": centers,
                            "low": [round(c - s, 2) for c, s in zip(centers, spreads)],
                            "high": [round(c + s, 2) for c, s in zip(centers, spreads)]}],
            }

    # ── Boxplot ──
    for case in range(8):
        points = rng.randint(1, 6)
        box_data = []
        for _ in range(points):
            vals = sorted(round(rng.uniform(0, 100), 2) for _ in range(5))
            box_data.append({"low": vals[0], "q1": vals[1], "median": vals[2],
                             "q3": vals[3], "high": vals[4]})
        yield {
            "type": "boxplot",
            "title": f"boxplot property {case}",
            "xAxis": {"categories": [f"C{i}" for i in range(points)]},
            "series": [{"name": "S0",
                        "data": [b["median"] for b in box_data],
                        "boxData": box_data}],
        }

    # ── Candlestick ──
    for case in range(8):
        points = rng.randint(1, 12)
        ohlc = []
        for _ in range(points):
            o = round(rng.uniform(50, 150), 2)
            c = round(rng.uniform(50, 150), 2)
            h = round(max(o, c) + rng.uniform(0.01, 10), 2)
            lo = round(min(o, c) - rng.uniform(0.01, 10), 2)
            ohlc.append({"open": o, "high": h, "low": lo, "close": c})
        yield {
            "type": "candlestick",
            "title": f"candlestick property {case}",
            "xAxis": {"categories": [f"D{i}" for i in range(points)]},
            "series": [{"name": "S0",
                        "data": [d["close"] for d in ohlc],
                        "ohlc": ohlc}],
        }

    # ── Histogram ──
    for case in range(8):
        n = rng.randint(5, 50)
        yield {
            "type": "histogram",
            "title": f"histogram property {case}",
            "outOfRange": "clip",
            "series": [{"name": "S0",
                        "data": [round(rng.gauss(50, 15), 2) for _ in range(n)]}],
        }

    # ── Xrange ──
    for case in range(8):
        lanes = rng.randint(1, 4)
        spans = []
        for _ in range(rng.randint(1, 8)):
            x = round(rng.uniform(0, 80), 1)
            spans.append({"x": x, "x2": round(x + rng.uniform(1, 20), 1),
                          "y": rng.randint(0, lanes - 1)})
        yield {
            "type": "xrange",
            "title": f"xrange property {case}",
            "yAxis": {"categories": [f"Lane{i}" for i in range(lanes)]},
            "series": [{"name": "S0", "data": [], "spans": spans}],
        }

    # ── Flame-chart ──
    for case in range(8):
        frames = []
        for _ in range(rng.randint(1, 12)):
            x = round(rng.uniform(0, 80), 1)
            frames.append({"x": x, "x2": round(x + rng.uniform(0.5, 20), 1),
                           "depth": rng.randint(0, 5),
                           "name": f"fn{rng.randint(0, 99)}"})
        yield {
            "type": "flame-chart",
            "title": f"flame-chart property {case}",
            "series": [{"name": "S0", "data": [], "frames": frames}],
        }

    # ── Bullet ──
    for case in range(8):
        yield {
            "type": "bullet",
            "title": f"bullet property {case}",
            "bulletTarget": round(rng.uniform(50, 100), 1),
            "bulletRanges": sorted(round(rng.uniform(20, 100), 1) for _ in range(3)),
            "series": [{"name": "S0", "data": [round(rng.uniform(10, 90), 1)]}],
        }

    # ── Technical-indicators ──
    for case in range(8):
        points = rng.randint(10, 30)
        yield {
            "type": "technical-indicators",
            "title": f"technical-indicators property {case}",
            "series": [{"name": "S0", "type": "line",
                        "data": [round(rng.uniform(50, 150), 2) for _ in range(points)],
                        "indicators": [{"type": "sma", "period": min(5, points)}]}],
        }

    # ── Pie ──
    for case in range(8):
        points = rng.randint(2, 8)
        yield {
            "type": "pie",
            "title": f"pie property {case}",
            "xAxis": {"categories": [f"Slice{i}" for i in range(points)]},
            "series": [{"name": "S0", "data": _pos_data(rng, points)}],
        }

    # ── Gauge / solid-gauge ──
    for chart_type in ("gauge", "solid-gauge"):
        for case in range(8):
            lo = round(rng.uniform(0, 30), 1)
            hi = round(lo + rng.uniform(20, 100), 1)
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "gaugeMin": lo,
                "gaugeMax": hi,
                "series": [{"name": "S0", "data": [round(rng.uniform(lo, hi), 1)]}],
            }

    # ── Parliament ──
    for case in range(8):
        points = rng.randint(2, 8)
        yield {
            "type": "parliament",
            "title": f"parliament property {case}",
            "xAxis": {"categories": [f"Party{i}" for i in range(points)]},
            "series": [{"name": "S0", "data": _pos_data(rng, points)}],
        }

    # ── Radar / polar ──
    for chart_type in ("radar", "polar"):
        for case in range(8):
            points = rng.randint(3, 8)
            series_count = rng.randint(1, 3)
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "xAxis": {"categories": [f"Axis{i}" for i in range(points)]},
                "series": [{"name": f"S{s}",
                            "data": [round(rng.uniform(0, 100), 1) for _ in range(points)]}
                           for s in range(series_count)],
            }

    # ── Wind-rose ──
    for case in range(8):
        points = rng.randint(4, 16)
        series_count = rng.randint(1, 3)
        yield {
            "type": "wind-rose",
            "title": f"wind-rose property {case}",
            "xAxis": {"categories": [f"Dir{i}" for i in range(points)]},
            "series": [{"name": f"S{s}",
                        "data": [round(rng.uniform(0, 50), 1) for _ in range(points)]}
                       for s in range(series_count)],
        }

    # ── Waterfall ──
    for case in range(8):
        points = rng.randint(2, 8)
        yield {
            "type": "waterfall",
            "title": f"waterfall property {case}",
            "xAxis": {"categories": [f"Step{i}" for i in range(points)]},
            "series": [{"name": "S0", "data": _series_data(rng, points)}],
        }

    # ── Funnel ──
    for case in range(8):
        points = rng.randint(2, 6)
        yield {
            "type": "funnel",
            "title": f"funnel property {case}",
            "xAxis": {"categories": [f"Stage{i}" for i in range(points)]},
            "series": [{"name": "S0", "data": _pos_data(rng, points)}],
        }

    # ── Timeline ──
    for case in range(8):
        n = rng.randint(1, 6)
        data = sorted(round(rng.uniform(1000, 9000), 0) for _ in range(n))
        yield {
            "type": "timeline",
            "title": f"timeline property {case}",
            "series": [{"name": "S0", "data": list(data),
                        "labels": [f"Evt{k}" for k in range(n)]}],
        }

    # ── Vector-plot ──
    for case in range(8):
        n = rng.randint(1, 12)
        yield {
            "type": "vector-plot",
            "title": f"vector-plot property {case}",
            "series": [{"name": "S0",
                        "x": [round(rng.uniform(0, 100), 1) for _ in range(n)],
                        "data": [round(rng.uniform(0, 100), 1) for _ in range(n)],
                        "direction": [round(rng.uniform(0, 360), 1) for _ in range(n)],
                        "length": [round(rng.uniform(0, 50), 1) for _ in range(n)]}],
        }

    # ── Development-triangle ──
    for case in range(8):
        n_origins = rng.randint(1, 8)
        n_periods = rng.randint(1, 8)
        origins = [f"Y{2020 + i}" for i in range(n_origins)]
        periods = sorted(rng.sample(range(0, 120), min(n_periods, 120)))
        # Ensure periods are strictly increasing non-negative integers
        if len(periods) == 0:
            periods = [0]
        seen: set[int] = set()
        deduped: list[int] = []
        for pv in periods:
            if pv not in seen:
                seen.add(pv)
                deduped.append(pv)
        periods = deduped[:n_periods] if deduped else [0]
        n_periods = len(periods)

        # Build triangle rows with non-increasing lengths
        jagged = rng.choice([True, False])
        values: list[list[float]] = []
        max_cols = min(n_periods, n_periods)
        for r in range(n_origins):
            if jagged:
                row_len = max(1, max_cols - r)
            else:
                # Rectangular: all rows same length, capped at n_periods
                row_len = max_cols
            row_len = min(row_len, n_periods)
            row: list[float] = []
            for _ in range(row_len):
                # Mix of positive, zero, and negative values
                choice = rng.randint(0, 2)
                if choice == 0:
                    row.append(round(rng.uniform(1, 500), 2))
                elif choice == 1:
                    row.append(0.0)
                else:
                    row.append(round(rng.uniform(-200, -1), 2))
            values.append(row)
            if jagged:
                max_cols = row_len

        spec: dict = {
            "type": "development-triangle",
            "title": f"development-triangle property {case}",
            "triangle": {
                "origins": origins,
                "periods": periods,
                "values": values,
            },
        }

        # Randomly add optional fields
        if rng.random() < 0.5:
            spec["triangle"]["unit"] = f"USD-{case}"
        if rng.random() < 0.5:
            spec["triangle"]["view"] = rng.choice(["cumulative", "incremental"])
        if rng.random() < 0.5:
            spec["triangle"]["valueType"] = rng.choice(["paid", "incurred"])
        if rng.random() < 0.5:
            spec["diagonal"] = {"highlight": True, "label": f"Diag {case}"}
        if rng.random() < 0.5:
            spec["colorScale"] = {"type": "sequential", "domain": "auto"}
        if rng.random() < 0.5 and n_periods >= 2:
            factor_vals = [round(rng.uniform(0.5, 3.0), 3) for _ in range(n_periods - 1)]
            spec["factors"] = {"show": True, "values": factor_vals}

        # Optionally add annotations targeting valid cells
        if rng.random() < 0.4 and len(values) > 0:
            ann_row = rng.randint(0, len(values) - 1)
            ann_col = rng.randint(0, len(values[ann_row]) - 1)
            spec["annotations"] = [{
                "origin": origins[ann_row],
                "period": periods[ann_col],
                "text": f"Note {case}",
            }]

        yield spec


def _has_marks(spec_dict: dict) -> bool:
    # development-triangle has no series
    if spec_dict.get("type") == "development-triangle":
        tri = spec_dict.get("triangle", {})
        for row in tri.get("values", []):
            if row:
                return True
        return False
    for s in spec_dict["series"]:
        if s.get("data") or s.get("spans") or s.get("frames"):
            return True
    return False


def test_randomized_specs_render_valid_svg_without_nonfinite_output():
    for spec_dict in _specs():
        svg = render_svg(ChartSpec.from_dict(spec_dict))

        assert svg.startswith("<svg")
        assert 'role="img"' in svg
        assert "NaN" not in svg
        assert "Infinity" not in svg
        if _has_marks(spec_dict):
            assert 'class="sc-' in svg


def test_render_determinism():
    for spec_dict in _specs():
        spec = ChartSpec.from_dict(spec_dict)
        first = render_svg(spec)
        for _ in range(4):
            assert render_svg(spec) == first, f"non-deterministic render for {spec_dict['type']}"
