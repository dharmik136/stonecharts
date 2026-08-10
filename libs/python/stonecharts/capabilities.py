"""Machine-readable renderer capability manifest for the active release scope."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_CAPABILITIES: dict[str, Any] = {
    "specVersion": "0.0.0.1",
    "svgContractVersion": "0.0.0.1",
    "chartTypes": [
        "area",
        "arearange",
        "bar",
        "boxplot",
        "bubble",
        "bullet",
        "candlestick",
        "column",
        "columnrange",
        "combo",
        "dumbbell",
        "error-bar",
        "flame-chart",
        "funnel",
        "gauge",
        "histogram",
        "line",
        "lollipop",
        "nightingale",
        "radial-bar",
        "pie",
        "polar",
        "radar",
        "scatter",
        "solid-gauge",
        "streamgraph",
        "technical-indicators",
        "timeline",
        "vector-plot",
        "variwide",
        "waterfall",
        "wind-rose",
        "windbarb",
        "xrange",
    ],
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
