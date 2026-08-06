#!/usr/bin/env python3
"""Validate that the Python validator rejects edge-case invalid inputs.

Generates invalid chart specs programmatically across multiple categories
(wrong types, invalid enums, boundary violations, missing fields, nested
errors) and asserts each is correctly rejected by the validator.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts.validate import validate


def _base(chart_type: str = "line") -> dict[str, Any]:
    return {"type": chart_type, "series": [{"name": "s", "data": [1, 2, 3]}]}


def _invalid_specs() -> list[tuple[str, dict[str, Any]]]:
    specs: list[tuple[str, dict[str, Any]]] = []

    specs.append(("type: wrong type (number)", {**_base(), "type": 42}))
    specs.append(("type: unsupported chart", {**_base(), "type": "pie"}))
    specs.append(("title: wrong type (number)", {**_base(), "title": 123}))
    specs.append(("subtitle: wrong type (list)", {**_base(), "subtitle": ["a"]}))
    specs.append(("width: wrong type (string)", {**_base(), "width": "wide"}))
    specs.append(("height: wrong type (string)", {**_base(), "height": "tall"}))
    specs.append(("width: NaN", {**_base(), "width": float("nan")}))
    specs.append(("width: Infinity", {**_base(), "width": float("inf")}))
    specs.append(("theme: wrong type (number)", {**_base(), "theme": 42}))
    specs.append(("theme: invalid name", {**_base(), "theme": "neon"}))
    specs.append(("legend: wrong type (string)", {**_base(), "legend": "yes"}))
    specs.append(("responsive: wrong type (string)", {**_base(), "responsive": "yes"}))
    specs.append(("a11y: wrong type (string)", {**_base(), "a11y": "yes"}))
    specs.append(("stacking: wrong type (number)", {**_base(), "stacking": 1}))
    specs.append(("stacking: invalid value", {**_base(), "stacking": "magic"}))
    specs.append(("grouping: wrong type (string)", {**_base("column"), "grouping": "yes"}))

    specs.append(("series: wrong type (string)", {**_base(), "series": "not-array"}))
    specs.append(("series[0].name: wrong type (number)", {"type": "line", "series": [{"name": 42, "data": [1]}]}))
    specs.append(("series[0].data: wrong type (string)", {"type": "line", "series": [{"name": "s", "data": "abc"}]}))
    specs.append(("series[0].data[0]: NaN", {"type": "line", "series": [{"name": "s", "data": [float("nan")]}]}))
    specs.append(("series[0].data[0]: Infinity", {"type": "line", "series": [{"name": "s", "data": [float("inf")]}]}))
    specs.append(("series[0].data[0]: string", {"type": "line", "series": [{"name": "s", "data": ["x"]}]}))
    specs.append(
        ("series[0].color: wrong type (number)", {"type": "line", "series": [{"name": "s", "data": [1], "color": 42}]})
    )
    specs.append(
        ("series[0].dashStyle: invalid", {"type": "line", "series": [{"name": "s", "data": [1], "dashStyle": "wavy"}]})
    )
    specs.append(
        ("series[0].curve: invalid", {"type": "line", "series": [{"name": "s", "data": [1], "curve": "spline"}]})
    )
    specs.append(
        ("series[0].step: invalid", {"type": "line", "series": [{"name": "s", "data": [1], "step": "middle"}]})
    )

    specs.append(
        (
            "marker.symbol: wrong type (number)",
            {"type": "line", "series": [{"name": "s", "data": [1], "marker": {"symbol": 123}}]},
        )
    )
    specs.append(
        (
            "marker.symbol: invalid",
            {"type": "line", "series": [{"name": "s", "data": [1], "marker": {"symbol": "star"}}]},
        )
    )
    specs.append(
        (
            "marker.radius: wrong type (string)",
            {"type": "line", "series": [{"name": "s", "data": [1], "marker": {"radius": "big"}}]},
        )
    )
    specs.append(
        ("marker: wrong type (string)", {"type": "line", "series": [{"name": "s", "data": [1], "marker": "circle"}]})
    )

    specs.append(
        ("pattern.type: invalid", {"type": "line", "series": [{"name": "s", "data": [1], "pattern": {"type": "dots"}}]})
    )
    specs.append(
        (
            "pattern.color: invalid hex",
            {"type": "line", "series": [{"name": "s", "data": [1], "pattern": {"type": "hatch", "color": "red"}}]},
        )
    )
    specs.append(("pattern: wrong type", {"type": "line", "series": [{"name": "s", "data": [1], "pattern": "hatch"}]}))

    specs.append(("xAxis: wrong type (string)", {**_base(), "xAxis": "time"}))
    specs.append(("yAxis: wrong type (string)", {**_base(), "yAxis": "linear"}))
    specs.append(("xAxis.title: wrong type (number)", {**_base(), "xAxis": {"title": 42}}))
    specs.append(("xAxis.categories: wrong type (string)", {**_base(), "xAxis": {"categories": "a,b,c"}}))
    specs.append(("xAxis.min: wrong type (string)", {**_base(), "xAxis": {"min": "zero"}}))
    specs.append(("yAxis.max: NaN", {**_base(), "yAxis": {"max": float("nan")}}))
    specs.append(("yAxis.gridLine: wrong type", {**_base(), "yAxis": {"gridLine": "dashed"}}))
    specs.append(("yAxis.gridLine.enabled: wrong type", {**_base(), "yAxis": {"gridLine": {"enabled": "yes"}}}))

    specs.append(("layout: wrong type (string)", {**_base(), "layout": "auto"}))
    specs.append(("layout.margin: wrong type", {**_base(), "layout": {"margin": "auto"}}))
    specs.append(("layout.margin.left: negative", {**_base(), "layout": {"margin": {"left": -10}}}))
    specs.append(("layout.margin.top: string", {**_base(), "layout": {"margin": {"top": "big"}}}))

    specs.append(
        (
            "percent stacking with negative data",
            {"type": "column", "stacking": "percent", "series": [{"name": "s", "data": [1, -2]}]},
        )
    )

    specs.append(
        ("bubble data: pair not triple", {"type": "bubble", "series": [{"name": "s", "data": [[1, 2], [3, 4]]}]})
    )

    specs.append(("theme palette: invalid color", {**_base(), "theme": {"name": "light", "palette": ["not-hex"]}}))
    specs.append(("theme gridColor: invalid", {**_base(), "theme": {"name": "light", "gridColor": "rgb(0,0,0)"}}))

    return specs


def main() -> int:
    specs = _invalid_specs()
    passed = 0
    failed = 0

    for label, spec in specs:
        try:
            serializable = json.loads(json.dumps(spec, allow_nan=True, default=str))
        except (ValueError, TypeError):
            serializable = spec

        errors = validate(serializable)
        if errors:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL  {label} -- wrongly accepted")

    print(f"\n{passed + failed} specs tested: {passed} correctly rejected, {failed} wrongly accepted")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
