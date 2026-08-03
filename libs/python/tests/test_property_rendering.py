from __future__ import annotations

import random

from stonecharts import ChartSpec
from stonecharts.render import render_svg


def _series_data(rng: random.Random, count: int) -> list[float]:
    return [round(rng.uniform(-100, 100), 3) for _ in range(count)]


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
    for chart_type in ("line", "column", "area", "bar"):
        for case in range(8):
            points = rng.randint(1, 12)
            series_count = rng.randint(1, 4)
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "xAxis": {"categories": [f"C{i}" for i in range(points)]},
                "series": [
                    {"name": f"S{s}", "data": _series_data(rng, points)}
                    for s in range(series_count)
                ],
            }
    for chart_type, has_z in (("scatter", False), ("bubble", True)):
        for case in range(8):
            yield {
                "type": chart_type,
                "title": f"{chart_type} property {case}",
                "series": [
                    {"name": "S0", "data": _point_data(rng, rng.randint(1, 12), z=has_z)}
                ],
            }


def test_randomized_specs_render_valid_svg_without_nonfinite_output():
    for spec_dict in _specs():
        svg = render_svg(ChartSpec.from_dict(spec_dict))

        assert svg.startswith("<svg")
        assert 'role="img"' in svg
        assert "NaN" not in svg
        assert "Infinity" not in svg
        if spec_dict["series"][0]["data"]:
            assert 'class="sc-' in svg
