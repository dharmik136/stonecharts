"""Machine-readable renderer capability manifest for the active release scope."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# --- BEGIN GENERATED FROM spec/capabilities.json ---
_CAPABILITIES: dict[str, Any] = {
    "specVersion": "0.0.0.1",
    "svgContractVersion": "0.0.0.1",
    "chartTypes": {
        "area":                 {"tier": "certified",     "since": "0.0.0.3"},
        "arearange":            {"tier": "certified",     "since": "0.0.0.9"},
        "bar":                  {"tier": "certified",     "since": "0.0.0.2"},
        "boxplot":              {"tier": "certified",     "since": "0.0.0.12"},
        "bubble":               {"tier": "certified",     "since": "0.0.0.4"},
        "bullet":               {"tier": "certified",     "since": "0.0.0.11"},
        "candlestick":          {"tier": "certified",     "since": "0.0.0.7"},
        "column":               {"tier": "certified",     "since": "0.0.0.1"},
        "columnrange":          {"tier": "certified",     "since": "0.0.0.9"},
        "combo":                {"tier": "certified",     "since": "0.0.0.5"},
        "development-triangle": {"tier": "certified",     "since": "0.0.0.33"},
        "dumbbell":             {"tier": "certified",     "since": "0.0.0.14"},
        "error-bar":            {"tier": "certified",     "since": "0.0.0.8"},
        "flame-chart":          {"tier": "certified",     "since": "0.0.0.23"},
        "funnel":               {"tier": "certified",     "since": "0.0.0.15"},
        "gauge":                {"tier": "certified",     "since": "0.0.0.25"},
        "histogram":            {"tier": "certified",     "since": "0.0.0.6"},
        "line":                 {"tier": "certified",     "since": "0.0.0.1"},
        "lollipop":             {"tier": "certified",     "since": "0.0.0.13"},
        "nightingale":          {"tier": "certified",     "since": "0.0.0.30"},
        "parliament":           {"tier": "certified",     "since": "0.0.0.32"},
        "pie":                  {"tier": "certified",     "since": "0.0.0.24"},
        "polar":                {"tier": "certified",     "since": "0.0.0.28"},
        "radar":                {"tier": "certified",     "since": "0.0.0.27"},
        "radial-bar":           {"tier": "certified",     "since": "0.0.0.31"},
        "scatter":              {"tier": "certified",     "since": "0.0.0.3"},
        "solid-gauge":          {"tier": "certified",     "since": "0.0.0.26"},
        "streamgraph":          {"tier": "certified",     "since": "0.0.0.19"},
        "technical-indicators": {"tier": "certified",     "since": "0.0.0.22"},
        "timeline":             {"tier": "certified",     "since": "0.0.0.17"},
        "variwide":             {"tier": "certified",     "since": "0.0.0.16"},
        "vector-plot":          {"tier": "certified",     "since": "0.0.0.20"},
        "waterfall":            {"tier": "certified",     "since": "0.0.0.10"},
        "wind-rose":            {"tier": "certified",     "since": "0.0.0.29"},
        "windbarb":             {"tier": "certified",     "since": "0.0.0.18"},
        "xrange":               {"tier": "certified",     "since": "0.0.0.21"},
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
# --- END GENERATED FROM spec/capabilities.json ---


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
