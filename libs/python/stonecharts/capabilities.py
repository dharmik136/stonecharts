"""Machine-readable renderer capability manifest for the active release scope."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_CAPABILITIES: dict[str, Any] = {
    "specVersion": "0.0.0.1",
    "svgContractVersion": "0.0.0.1",
    "chartTypes": {
        "area":                  {"tier": "certified",    "since": "0.0.0.3"},
        "arearange":             {"tier": "candidate",    "since": "0.0.0.9"},
        "bar":                   {"tier": "certified",    "since": "0.0.0.2"},
        "boxplot":               {"tier": "candidate",    "since": "0.0.0.12"},
        "bubble":                {"tier": "certified",    "since": "0.0.0.4"},
        "bullet":                {"tier": "candidate",    "since": "0.0.0.11"},
        "candlestick":           {"tier": "experimental", "since": "0.0.0.7"},
        "column":                {"tier": "certified",    "since": "0.0.0.1"},
        "columnrange":           {"tier": "candidate",    "since": "0.0.0.9"},
        "combo":                 {"tier": "certified",    "since": "0.0.0.5"},
        "dumbbell":              {"tier": "candidate",    "since": "0.0.0.14"},
        "error-bar":             {"tier": "candidate",    "since": "0.0.0.8"},
        "flame-chart":           {"tier": "experimental", "since": "0.0.0.23"},
        "funnel":                {"tier": "experimental", "since": "0.0.0.15"},
        "gauge":                 {"tier": "experimental", "since": "0.0.0.25"},
        "histogram":             {"tier": "candidate",    "since": "0.0.0.6"},
        "line":                  {"tier": "certified",    "since": "0.0.0.1"},
        "lollipop":              {"tier": "experimental", "since": "0.0.0.13"},
        "nightingale":           {"tier": "experimental", "since": "0.0.0.30"},
        "parliament":            {"tier": "experimental", "since": "0.0.0.32"},
        "pie":                   {"tier": "experimental", "since": "0.0.0.24"},
        "polar":                 {"tier": "experimental", "since": "0.0.0.28"},
        "radar":                 {"tier": "experimental", "since": "0.0.0.27"},
        "radial-bar":            {"tier": "experimental", "since": "0.0.0.31"},
        "scatter":               {"tier": "certified",    "since": "0.0.0.3"},
        "solid-gauge":           {"tier": "experimental", "since": "0.0.0.26"},
        "streamgraph":           {"tier": "experimental", "since": "0.0.0.19"},
        "technical-indicators":  {"tier": "experimental", "since": "0.0.0.22"},
        "timeline":              {"tier": "experimental", "since": "0.0.0.17"},
        "variwide":              {"tier": "experimental", "since": "0.0.0.16"},
        "vector-plot":           {"tier": "experimental", "since": "0.0.0.20"},
        "waterfall":             {"tier": "candidate",    "since": "0.0.0.10"},
        "wind-rose":             {"tier": "experimental", "since": "0.0.0.29"},
        "windbarb":              {"tier": "experimental", "since": "0.0.0.18"},
        "xrange":                {"tier": "experimental", "since": "0.0.0.21"},
        "development-triangle":  {"tier": "certified",    "since": "0.0.0.33"},
    },
    "column": {
        "grouping": ["grouped", "overlay"],
        "stacking": ["none", "normal", "percent-nonnegative"],
    },
    "bar": {
        "grouping": ["grouped", "overlay"],
        "stacking": ["none", "normal", "percent-nonnegative"],
    },
}


class CapabilityError(Exception):
    """Typed non-fatal error for unsupported renderer capabilities."""

    def __init__(self, code: str, path: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message
        self.details = deepcopy(details) if details is not None else None

    def __str__(self) -> str:
        return f"{self.path}: {self.message}" if self.path else self.message


def capabilities() -> dict[str, Any]:
    """Return a machine-readable snapshot of the active renderer capabilities."""
    return deepcopy(_CAPABILITIES)
