#!/usr/bin/env python3
"""Generate edge-case invalid specs and verify the Python validator rejects them all.

A complement to the fixture-based approach in charts/*/invalid-fixtures.json:
this tool programmatically builds a broad set of malformed inputs covering wrong
types, invalid enums, boundary violations, missing required fields, and nested
shape errors, then asserts that each one produces at least one validation error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts.validate import validate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base(**overrides: Any) -> dict[str, Any]:
    """Minimal valid spec with caller overrides merged in."""
    spec: dict[str, Any] = {
        "type": "line",
        "series": [{"name": "s", "data": [1, 2, 3]}],
    }
    spec.update(overrides)
    return spec


def _with_series(**series_overrides: Any) -> dict[str, Any]:
    """Spec whose single series has the given field overrides."""
    s: dict[str, Any] = {"name": "s", "data": [1, 2, 3]}
    s.update(series_overrides)
    return {"type": "line", "series": [s]}


# ---------------------------------------------------------------------------
# Invalid spec generators by category
# ---------------------------------------------------------------------------

_WRONG_TYPES: list[tuple[str, Any]] = [
    ("number", 123),
    ("boolean", True),
    ("null", None),
    ("array", []),
    ("object", {}),
]


def _wrong_type_cases() -> list[tuple[str, dict[str, Any]]]:
    """Wrong types for every top-level field."""
    cases: list[tuple[str, dict[str, Any]]] = []

    for field in ("type", "id", "title", "subtitle"):
        for label, val in _WRONG_TYPES:
            cases.append((f"{field}={label}", _base(**{field: val})))

    for field in ("width", "height"):
        for label, val in [
            ("string", "auto"),
            ("boolean", True),
            ("null", None),
            ("array", []),
            ("object", {}),
            ("non-integer", 5.7),
        ]:
            cases.append((f"{field}={label}", _base(**{field: val})))

    for field in ("responsive", "legend", "a11y", "grouping"):
        for label, val in [
            ("string", "yes"),
            ("number", 1),
            ("null", None),
            ("array", []),
            ("object", {}),
        ]:
            cases.append((f"{field}={label}", _base(**{field: val})))

    for label, val in _WRONG_TYPES:
        cases.append((f"stacking={label}", _base(stacking=val)))

    for label, val in [("number", 123), ("boolean", True), ("array", [1, 2])]:
        cases.append((f"theme={label}", _base(theme=val)))

    return cases


def _invalid_enum_cases() -> list[tuple[str, dict[str, Any]]]:
    """Invalid enum values for constrained fields."""
    return [
        ("type='pie'", _base(type="pie")),
        ("type='histogram'", _base(type="histogram")),
        ("type='donut'", _base(type="donut")),
        ("stacking='magic'", _base(stacking="magic")),
        ("stacking='absolute'", _base(stacking="absolute")),
        ("theme='solarized'", _base(theme="solarized")),
        ("theme='monokai'", _base(theme="monokai")),
        ("dashStyle='wavy'", _with_series(dashStyle="wavy")),
        ("dashStyle='longdash'", _with_series(dashStyle="longdash")),
        ("step='through'", _with_series(step="through")),
        ("step='middle'", _with_series(step="middle")),
        ("curve='spline'", _with_series(curve="spline")),
        ("curve='bezier'", _with_series(curve="bezier")),
        ("marker.symbol='star'", _with_series(marker={"symbol": "star"})),
        ("marker.symbol='hexagon'", _with_series(marker={"symbol": "hexagon"})),
        ("pattern.type='weave'", _with_series(pattern={"type": "weave"})),
        ("pattern.type='dots'", _with_series(pattern={"type": "dots"})),
    ]


def _boundary_cases() -> list[tuple[str, dict[str, Any]]]:
    """Boundary violations: NaN, Infinity, negatives in guarded fields."""
    return [
        ("NaN in data", _base(series=[{"name": "s", "data": [float("nan")]}])),
        ("Inf in data", _base(series=[{"name": "s", "data": [float("inf")]}])),
        ("-Inf in data", _base(series=[{"name": "s", "data": [float("-inf")]}])),
        (
            "NaN in data[1]",
            _base(series=[{"name": "s", "data": [1, float("nan"), 3]}]),
        ),
        ("negative margin.left", _base(layout={"margin": {"left": -10}})),
        ("negative margin.top", _base(layout={"margin": {"top": -5}})),
        ("negative margin.right", _base(layout={"margin": {"right": -1}})),
        ("negative margin.bottom", _base(layout={"margin": {"bottom": -0.5}})),
        (
            "percent stacking negative data",
            _base(
                type="area",
                stacking="percent",
                series=[{"name": "s", "data": [1, -3]}],
            ),
        ),
        (
            "percent stacking negative in second series",
            _base(
                type="column",
                stacking="percent",
                series=[
                    {"name": "a", "data": [1, 2]},
                    {"name": "b", "data": [-1, 2]},
                ],
            ),
        ),
    ]


def _missing_required_cases() -> list[tuple[str, dict[str, Any]]]:
    """Missing required fields."""
    return [
        ("missing series", {"type": "area"}),
        ("missing series (bare object)", {}),
        ("missing data in series[0]", _base(series=[{"name": "s"}])),
        (
            "missing data in series[1]",
            _base(series=[{"name": "a", "data": [1]}, {"name": "b"}]),
        ),
    ]


def _nested_shape_cases() -> list[tuple[str, dict[str, Any]]]:
    """Nested shape / type errors inside series, axes, and sub-objects."""
    return [
        # series-level type errors
        ("series='nope'", _base(series="nope")),
        ("series=123", _base(series=123)),
        ("series=null", _base(series=None)),
        ("series[0]=number", _base(series=[5])),
        ("series[0]=string", _base(series=["bad"])),
        ("series[0].data=string", _with_series(data="not-array")),
        ("series[0].data=null", _with_series(data=None)),
        ("series[0].data=number", _with_series(data=42)),
        ("series[0].name=number", _with_series(name=123)),
        ("series[0].color=number", _with_series(color=5)),
        ("series[0].fillOpacity=string", _with_series(fillOpacity="high")),
        ("series[0].fillOpacity=boolean", _with_series(fillOpacity=True)),
        ("series[0].fillOpacity=null", _with_series(fillOpacity=None)),
        ("series[0].lineWidth=string", _with_series(lineWidth="thick")),
        ("series[0].lineWidth=boolean", _with_series(lineWidth=False)),
        # marker sub-object
        ("marker.symbol=number", _with_series(marker={"symbol": 123})),
        ("marker.radius=string", _with_series(marker={"radius": "big"})),
        ("marker.radius=boolean", _with_series(marker={"radius": True})),
        ("marker.enabled=string", _with_series(marker={"enabled": "yes"})),
        # pattern sub-object
        ("pattern.type=number", _with_series(pattern={"type": 99})),
        ("pattern.size=string", _with_series(pattern={"size": "large"})),
        ("pattern.color=bad hex", _with_series(pattern={"color": "red"})),
        (
            "pattern.background=bad hex",
            _with_series(pattern={"background": "inherit"}),
        ),
        # gradient stop errors
        (
            "gradient stop offset=string",
            _with_series(color={"stops": [{"offset": "x", "color": "#f00"}]}),
        ),
        (
            "gradient stop color=bad hex",
            _with_series(color={"stops": [{"offset": 0, "color": "red"}]}),
        ),
        # axis sub-objects
        ("xAxis=string", _base(xAxis="bad")),
        ("yAxis=number", _base(yAxis=123)),
        ("xAxis.categories=number", _base(xAxis={"categories": 123})),
        (
            "xAxis.categories[1]=number",
            _base(xAxis={"categories": ["a", 2, "c"]}),
        ),
        ("xAxis.min=string", _base(xAxis={"min": "low"})),
        ("yAxis.max=boolean", _base(yAxis={"max": True})),
        ("yAxis.gridLine=string", _base(yAxis={"gridLine": "solid"})),
        (
            "yAxis.gridLine.enabled=string",
            _base(yAxis={"gridLine": {"enabled": "yes"}}),
        ),
        (
            "yAxis.gridLine.color=number",
            _base(yAxis={"gridLine": {"color": 42}}),
        ),
        # layout sub-object
        ("layout=string", _base(layout="flat")),
        ("layout.margin=string", _base(layout={"margin": "auto"})),
        (
            "layout.margin.left=string",
            _base(layout={"margin": {"left": "big"}}),
        ),
        # theme sub-object
        ("theme palette non-string", _base(theme={"palette": [1, 2]})),
        ("theme bad hex in palette", _base(theme={"palette": ["not-hex"]})),
        ("theme titleColor=number", _base(theme={"titleColor": 42})),
        # color as bad hex string
        ("color='red'", _with_series(color="red")),
        ("color='url(#bad)'", _with_series(color="url(#bad)")),
        # data element wrong types
        ("data[0]=string", _with_series(data=["a", 2])),
        ("data[0]=boolean", _with_series(data=[True, 2])),
        ("data[0]=null", _with_series(data=[None, 2])),
        ("data[0]=object", _with_series(data=[{}, 2])),
        # yAxis out of range in series
        ("series[0].yAxis=2", _with_series(yAxis=2)),
        ("series[0].yAxis=string", _with_series(yAxis="primary")),
    ]


def _scatter_bubble_cases() -> list[tuple[str, dict[str, Any]]]:
    """Scatter- and bubble-specific shape errors."""
    return [
        (
            "scatter {x:1} missing y",
            {
                "type": "scatter",
                "series": [{"name": "s", "data": [{"x": 1}]}],
            },
        ),
        (
            "scatter {x,y,z} extra z",
            {
                "type": "scatter",
                "series": [
                    {"name": "s", "data": [{"x": 1, "y": 2, "z": 3}]},
                ],
            },
        ),
        (
            "scatter [1,2,3] 3-element",
            {
                "type": "scatter",
                "series": [{"name": "s", "data": [[1, 2, 3]]}],
            },
        ),
        (
            "scatter ['a',2]",
            {
                "type": "scatter",
                "series": [{"name": "s", "data": [["a", 2]]}],
            },
        ),
        (
            "bubble {x,y} missing z",
            {
                "type": "bubble",
                "series": [{"name": "s", "data": [{"x": 1, "y": 2}]}],
            },
        ),
        (
            "bubble [1,2] 2-element",
            {
                "type": "bubble",
                "series": [{"name": "s", "data": [[1, 2]]}],
            },
        ),
        (
            "bubble ['a',2,3]",
            {
                "type": "bubble",
                "series": [{"name": "s", "data": [["a", 2, 3]]}],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate_all() -> list[tuple[str, dict[str, Any]]]:
    """Assemble every category of invalid spec."""
    cases: list[tuple[str, dict[str, Any]]] = []
    cases.extend(_wrong_type_cases())
    cases.extend(_invalid_enum_cases())
    cases.extend(_boundary_cases())
    cases.extend(_missing_required_cases())
    cases.extend(_nested_shape_cases())
    cases.extend(_scatter_bubble_cases())
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description=("Generate invalid specs and verify the Python validator rejects every one."),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print error details for each spec",
    )
    args = parser.parse_args()

    cases = generate_all()
    passed = 0
    failures: list[str] = []

    for desc, spec in cases:
        errors = validate(spec)
        if errors:
            passed += 1
            if args.verbose:
                print(f"  OK  {desc} -> {len(errors)} error(s): {errors}")
            else:
                print(f"  OK  {desc} -> {len(errors)} error(s)")
        else:
            failures.append(desc)
            print(
                f"  FAIL  {desc} -> accepted (should have been rejected)",
            )

    print()
    if failures:
        print(
            f"{len(cases)} specs tested, {len(failures)} wrongly accepted:",
        )
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"{len(cases)} specs tested, all correctly rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
