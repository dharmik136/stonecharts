"""Small rendering utilities: nice axis ticks, escaping, number formatting.

`nice_ticks` is the standard 'nice numbers' algorithm (Heckbert) so the y-axis
lands on human-friendly round values instead of the raw data min/max.
"""
from __future__ import annotations

import math
from typing import List, Tuple


def _nice_num(x: float, round_: bool) -> float:
    if x == 0:
        return 0.0
    exp = math.floor(math.log10(abs(x)))
    frac = abs(x) / (10 ** exp)
    if round_:
        nf = 1 if frac < 1.5 else 2 if frac < 3 else 5 if frac < 7 else 10
    else:
        nf = 1 if frac <= 1 else 2 if frac <= 2 else 5 if frac <= 5 else 10
    return nf * (10 ** exp)


def nice_ticks(lo: float, hi: float, target: int = 6) -> Tuple[float, float, List[float]]:
    """Return (axis_min, axis_max, tick_values) covering [lo, hi] on round steps."""
    if lo == hi:
        if lo == 0:
            lo, hi = -1.0, 1.0
        else:
            pad = abs(lo) * 0.1
            lo, hi = lo - pad, hi + pad
    rng = _nice_num(hi - lo, False)
    step = _nice_num(rng / max(1, (target - 1)), True) or 1.0
    axis_min = math.floor(lo / step) * step
    axis_max = math.ceil(hi / step) * step
    count = int(round((axis_max - axis_min) / step))
    ticks = [axis_min + i * step for i in range(count + 1)]
    return axis_min, axis_max, ticks


def esc(s) -> str:
    """Escape text for XML/SVG/HTML attribute and body context."""
    return (
        str("" if s is None else s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_num(v: float) -> str:
    """Compact number formatting: drop trailing .0, else 6 significant figures.

    Must stay byte-identical to Go fmtNum (libs/go/util.go). NaN/Inf -> "0"; the
    integer fast-path is bounded to |v| < 1e18 so int(v) can't overflow Go's int64.
    """
    if not math.isfinite(v):
        return "0"
    if v == int(v) and abs(v) < 1e18:
        return str(int(v))
    return f"{v:g}"
