"""Machine-readable renderer capability manifest for the active release scope."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

_CAPABILITIES: Dict[str, Any] = {
    "specVersion": "0.0.0.1",
    "svgContractVersion": "0.0.0.1",
    "chartTypes": ["area", "bar", "column", "line"],
    "column": {
        "grouping": ["grouped", "overlay"],
        "stacking": ["none", "normal", "percent-nonnegative"],
    },
}


class CapabilityError(Exception):
    """Typed non-fatal error for unsupported renderer capabilities."""

    def __init__(self, code: str, path: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message
        self.details = deepcopy(details) if details is not None else None

    def __str__(self) -> str:
        return f"{self.path}: {self.message}" if self.path else self.message


def capabilities() -> Dict[str, Any]:
    """Return a machine-readable snapshot of the active renderer capabilities."""
    return deepcopy(_CAPABILITIES)
