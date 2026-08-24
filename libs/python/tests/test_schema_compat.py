from __future__ import annotations

import pytest

from tools.check_schema_compat import find_breaking_changes


@pytest.mark.parametrize(
    ("old", "new", "marker"),
    [
        ({"type": "number"}, {"type": "number", "minimum": 0}, "NARROWED BOUND"),
        ({"minimum": 0}, {"minimum": 1}, "raised minimum"),
        ({"maximum": 10}, {"maximum": 9}, "lowered maximum"),
        ({"minItems": 1}, {"minItems": 2}, "raised minItems"),
        ({"maxItems": 5}, {"maxItems": 4}, "lowered maxItems"),
        ({"type": "object"}, {"type": "object", "additionalProperties": False}, "ADDITIONAL PROPERTIES"),
        ({"type": "string"}, {"type": "string", "pattern": "^[A-Z]+$"}, "PATTERN ADDED"),
        ({"pattern": "a+"}, {"pattern": "b+"}, "PATTERN CHANGED"),
        ({"type": "string"}, {"type": "string", "const": "fixed"}, "CONST ADDED"),
        ({"const": "old"}, {"const": "new"}, "CONST CHANGED"),
        ({"oneOf": [{"type": "string"}]}, {"oneOf": []}, "COMBINATOR TOPOLOGY"),
        ({"allOf": []}, {"allOf": [{"type": "string"}]}, "COMBINATOR TOPOLOGY"),
    ],
)
def test_detects_new_compatibility_failure_classes(old: dict, new: dict, marker: str) -> None:
    assert any(marker in finding for finding in find_breaking_changes(old, new))


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ({"minimum": 1}, {"minimum": 0}),
        ({"maximum": 9}, {"maximum": 10}),
        ({"minItems": 2}, {"minItems": 1}),
        ({"maxItems": 4}, {"maxItems": 5}),
        ({"additionalProperties": False}, {"additionalProperties": True}),
        ({"pattern": "^[A-Z]+$"}, {"type": "string"}),
        ({"const": "fixed"}, {"type": "string"}),
    ],
)
def test_allows_supported_constraint_widening(old: dict, new: dict) -> None:
    assert find_breaking_changes(old, new) == []
