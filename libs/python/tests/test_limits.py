from __future__ import annotations

import pytest

from stonecharts import ChartSpec, render_svg
from stonecharts.limits import (
    MAX_LABEL_LENGTH,
    MAX_POINTS_PER_SERIES,
    MAX_SERIES,
    MAX_SPEC_BYTES,
    ResourceLimitError,
    enforce_spec_limits,
)


def test_spec_size_limit_has_stable_code():
    with pytest.raises(ResourceLimitError) as exc:
        enforce_spec_limits({"series": []}, raw_size_hint=MAX_SPEC_BYTES + 1)

    assert exc.value.code == "LIMIT.SPEC_BYTES"
    assert exc.value.path == "$"


def test_series_count_limit_has_stable_code():
    spec = {"series": [{"name": str(index), "data": [1]} for index in range(MAX_SERIES + 1)]}

    with pytest.raises(ResourceLimitError) as exc:
        ChartSpec.from_dict(spec)

    assert exc.value.code == "LIMIT.SERIES_COUNT"
    assert exc.value.path == "$.series"


def test_points_per_series_limit_has_stable_code():
    spec = {"series": [{"name": "s", "data": [1] * (MAX_POINTS_PER_SERIES + 1)}]}

    with pytest.raises(ResourceLimitError) as exc:
        ChartSpec.from_dict(spec)

    assert exc.value.code == "LIMIT.POINTS_PER_SERIES"
    assert exc.value.path == "$.series[0].data"


def test_label_length_limit_has_stable_code():
    spec = {"title": "x" * (MAX_LABEL_LENGTH + 1), "series": [{"name": "s", "data": [1]}]}

    with pytest.raises(ResourceLimitError) as exc:
        ChartSpec.from_dict(spec)

    assert exc.value.code == "LIMIT.LABEL_LENGTH"
    assert exc.value.path == "$.title"


def test_valid_spec_below_limits_still_renders():
    spec = ChartSpec.from_dict({"type": "line", "series": [{"name": "s", "data": [1, 2, 3]}]})

    assert render_svg(spec).startswith("<svg")
