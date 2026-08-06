"""Resource limits for certified StoneCharts renderers."""

from __future__ import annotations

from typing import Any

MAX_SPEC_BYTES = 1_000_000
MAX_SERIES = 50
MAX_POINTS_PER_SERIES = 10_000
MAX_TOTAL_POINTS = 50_000
MAX_LABEL_LENGTH = 512
MAX_SVG_BYTES = 5_000_000


class ResourceLimitError(ValueError):
    """Raised when a spec or output exceeds a documented resource limit."""

    def __init__(self, code: str, path: str, limit: int, received: int):
        self.code = code
        self.path = path
        self.limit = limit
        self.received = received
        super().__init__(f"{code}: {path}: limit {limit} exceeded, received {received}")


def _check_label(value: Any, path: str) -> None:
    if isinstance(value, str) and len(value) > MAX_LABEL_LENGTH:
        raise ResourceLimitError("LIMIT.LABEL_LENGTH", path, MAX_LABEL_LENGTH, len(value))


def enforce_spec_limits(spec: Any, *, raw_size_hint: int | None = None) -> None:
    if raw_size_hint is not None and raw_size_hint > MAX_SPEC_BYTES:
        raise ResourceLimitError("LIMIT.SPEC_BYTES", "$", MAX_SPEC_BYTES, raw_size_hint)
    if not isinstance(spec, dict):
        return
    for key in ("id", "title", "subtitle"):
        _check_label(spec.get(key), f"$.{key}")
    for axis_name in ("xAxis", "yAxis", "secondaryYAxis"):
        axis = spec.get(axis_name)
        if isinstance(axis, dict):
            _check_label(axis.get("title"), f"$.{axis_name}.title")
            categories = axis.get("categories")
            if isinstance(categories, list):
                for index, category in enumerate(categories):
                    _check_label(category, f"$.{axis_name}.categories[{index}]")
    series = spec.get("series")
    if not isinstance(series, list):
        return
    if len(series) > MAX_SERIES:
        raise ResourceLimitError("LIMIT.SERIES_COUNT", "$.series", MAX_SERIES, len(series))
    total_points = 0
    for series_index, item in enumerate(series):
        if not isinstance(item, dict):
            continue
        _check_label(item.get("name"), f"$.series[{series_index}].name")
        data = item.get("data")
        if not isinstance(data, list):
            continue
        point_count = len(data)
        if point_count > MAX_POINTS_PER_SERIES:
            raise ResourceLimitError(
                "LIMIT.POINTS_PER_SERIES",
                f"$.series[{series_index}].data",
                MAX_POINTS_PER_SERIES,
                point_count,
            )
        total_points += point_count
        if total_points > MAX_TOTAL_POINTS:
            raise ResourceLimitError("LIMIT.TOTAL_POINTS", "$.series[*].data", MAX_TOTAL_POINTS, total_points)


def enforce_svg_limit(svg: str) -> None:
    size = len(svg.encode("utf-8"))
    if size > MAX_SVG_BYTES:
        raise ResourceLimitError("LIMIT.SVG_BYTES", "$.svg", MAX_SVG_BYTES, size)
