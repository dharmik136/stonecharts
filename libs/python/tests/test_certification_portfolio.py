"""Portfolio-wide SC-CERT assertions with one named result per chart type."""

from __future__ import annotations

import copy
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

import jsonschema
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts import ChartSpec  # noqa: E402
from stonecharts.render import render_html, render_svg  # noqa: E402
from stonecharts.validate import validate  # noqa: E402

REGISTRY = json.loads((ROOT / "spec" / "capabilities.json").read_text(encoding="utf-8"))
CERTIFIED = [item["id"] for item in REGISTRY["chartTypes"] if item["tier"] == "certified"]
SCHEMA = json.loads((ROOT / "spec" / "chart-spec.schema.json").read_text(encoding="utf-8"))
SCHEMA_VALIDATOR = jsonschema.validators.validator_for(SCHEMA)(SCHEMA)


def chart_dir(chart_id: str) -> pathlib.Path:
    return ROOT / "charts" / ("line-basic" if chart_id == "line" else chart_id)


def basic_fixture(chart_id: str) -> pathlib.Path:
    examples = sorted((chart_dir(chart_id) / "examples").glob("*.json"))
    preferred = chart_dir(chart_id) / "examples" / "basic.json"
    return preferred if preferred.exists() else examples[0]


def test_packaged_runtime_asset_matches_canonical_source():
    """The wheel asset must remain the exact governed browser runtime."""
    canonical = ROOT / "runtime" / "chart-interactions.js"
    packaged = ROOT / "libs" / "python" / "stonecharts" / "_assets" / "chart-interactions.js"
    assert packaged.read_bytes() == canonical.read_bytes()


@pytest.mark.parametrize("chart_id", CERTIFIED)
def test_certified_chart_contract_and_semantic_floor(chart_id):
    """SC-CERT-01/03/06/07: every chart satisfies the shared semantic floor."""
    raw = json.loads(basic_fixture(chart_id).read_text(encoding="utf-8"))
    assert list(SCHEMA_VALIDATOR.iter_errors(raw)) == []
    assert validate(raw) == []

    spec = ChartSpec.from_dict(raw)
    before = copy.deepcopy(spec)
    svg = render_svg(spec)
    assert spec == before
    assert svg.startswith("<svg")
    assert 'class="sc-chart"' in svg
    assert 'role="img"' in svg
    assert re.search(r'aria-label="[^\"]+"', svg)
    assert 'class="sc-' in svg
    assert "NaN" not in svg and "Infinity" not in svg and '="null"' not in svg
    ET.fromstring(svg)

    html = render_html(spec)
    assert '<table class="sc-visually-hidden">' in html
    assert "<caption>" in html
    assert "window.StoneCharts" in html


@pytest.mark.parametrize("chart_id", CERTIFIED)
def test_certified_chart_invalid_corpus_is_rejected(chart_id):
    """SC-CERT-05: every declared invalid fixture is rejected before rendering."""
    fixture_path = chart_dir(chart_id) / "invalid-fixtures.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert len(cases) >= 3
    for index, case in enumerate(cases):
        raw = case["spec"]
        schema_errors = list(SCHEMA_VALIDATOR.iter_errors(raw))
        runtime_errors = validate(raw)
        rejected = bool(schema_errors or runtime_errors)
        if not rejected:
            try:
                render_svg(ChartSpec.from_dict(raw))
            except (TypeError, ValueError):
                rejected = True
        assert rejected, f"{chart_id} invalid fixture {index} was accepted"
