"""Basic line chart renderer: ChartSpec -> SVG string.

Produces SVG that follows spec/svg-contract.md so the shared JS runtime can
enhance it (tooltip, highlight, legend toggle, crosshair). All shared cartesian
chrome (margins, scales, axes, gridlines, legend, theme, a11y, <defs>) comes
from the shared frame (_cartesian.py); this module draws ONLY the line-specific
marks — series paths, area fills, and point markers.
"""

from __future__ import annotations

import math

from ..spec import Marker
from ..util import esc, fmt_num
from ._cartesian import CartesianFrame, dash_array, render_cartesian


def _path_d(pts, step) -> str:
    """Build the line path 'd'. step in {None, before, after, center}."""
    if not step:
        return " ".join(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    parts: list[str] = []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            parts.append(f"M{x:.1f} {y:.1f}")
            continue
        px, py = pts[i - 1]
        if step == "before":
            parts.append(f"L{px:.1f} {y:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
        elif step == "center":
            mx = (px + x) / 2
            parts.append(f"L{mx:.1f} {py:.1f}")
            parts.append(f"L{mx:.1f} {y:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
        else:  # after
            parts.append(f"L{x:.1f} {py:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
    return " ".join(parts)


def _spline_d(pts) -> str:
    """Monotone cubic spline path (Fritsch-Carlson). Identical math to line.go."""
    n = len(pts)
    if n < 3:
        return _path_d(pts, None)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    delta = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [0.0] * n
    m[0] = delta[0]
    m[n - 1] = delta[n - 2]
    for i in range(1, n - 1):
        if delta[i - 1] * delta[i] <= 0:
            m[i] = 0.0
        else:
            m[i] = (delta[i - 1] + delta[i]) / 2
    for i in range(n - 1):
        if delta[i] == 0:
            m[i] = 0.0
            m[i + 1] = 0.0
        else:
            a = m[i] / delta[i]
            b = m[i + 1] / delta[i]
            s = a * a + b * b
            if s > 9:
                t = 3.0 / math.sqrt(s)
                m[i] = t * a * delta[i]
                m[i + 1] = t * b * delta[i]
    parts = [f"M{xs[0]:.1f} {ys[0]:.1f}"]
    for i in range(n - 1):
        h = xs[i + 1] - xs[i]
        c1x = xs[i] + h / 3
        c1y = ys[i] + m[i] * h / 3
        c2x = xs[i + 1] - h / 3
        c2y = ys[i + 1] - m[i + 1] * h / 3
        parts.append(f"C{c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {xs[i + 1]:.1f} {ys[i + 1]:.1f}")
    return " ".join(parts)


def _marker(symbol, x, y, r, common, color, halo, fill_opacity: float = 1.0) -> str:
    """One data-point marker. `common` = the shared class + data-* attributes.
    Non-circle shapes carry cx/cy attrs so the JS runtime (crosshair) still works.
    `fill_opacity` is opt-in (default 1.0 reproduces the original byte-for-byte
    output with no attribute added) — scatter's primary points are the only
    caller that passes a value < 1.0 (§3.3 Rank 3)."""
    op_attr = f' fill-opacity="{fmt_num(fill_opacity)}"' if fill_opacity != 1.0 else ""
    fs = f'fill="{color}" stroke="{halo}" stroke-width="1"{op_attr}'
    if symbol == "square":
        return (
            f'<rect {common} cx="{x:.1f}" cy="{y:.1f}" x="{x - r:.1f}" y="{y - r:.1f}" '
            f'width="{2 * r:.1f}" height="{2 * r:.1f}" {fs}/>'
        )
    if symbol == "triangle":
        poly = f"{x:.1f},{y - r:.1f} {x - r:.1f},{y + r:.1f} {x + r:.1f},{y + r:.1f}"
        return f'<polygon {common} cx="{x:.1f}" cy="{y:.1f}" points="{poly}" {fs}/>'
    if symbol == "diamond":
        poly = f"{x:.1f},{y - r:.1f} {x + r:.1f},{y:.1f} {x:.1f},{y + r:.1f} {x - r:.1f},{y:.1f}"
        return f'<polygon {common} cx="{x:.1f}" cy="{y:.1f}" points="{poly}" {fs}/>'
    # circle (default)
    return f'<circle {common} cx="{x:.1f}" cy="{y:.1f}" r="{fmt_num(r)}" {fs}/>'


def render_svg(spec) -> str:
    return render_cartesian(spec, "Line", "point", _line_marks)  # include_zero defaults True


def _line_marks(fr: CartesianFrame, p: list) -> None:
    # Series: one group per series (data-series drives legend toggle).
    theme = fr.theme
    for si, s in enumerate(fr.spec.series):
        st = fr.styles[si]
        pts = [(fr.xpix(i), fr.ypix(v)) for i, v in enumerate(s.data)]
        d = _spline_d(pts) if s.curve == "monotone" else _path_d(pts, s.step)
        lw = s.line_width if s.line_width is not None else 2
        line_dash = dash_array(s.dash_style)
        line_dash_attr = f' stroke-dasharray="{line_dash}"' if line_dash else ""
        p.append(f'<g class="sc-series" data-series="{si}">')
        # Area fill (under the line, drawn first so the line sits on top).
        if st.area_fill is not None and pts:
            base = fr.ypix(0.0)
            area_d = f"{d} L{pts[-1][0]:.1f} {base:.1f} L{pts[0][0]:.1f} {base:.1f} Z"
            p.append(
                f'<path class="sc-series-area" data-series="{si}" d="{area_d}" '
                f'fill="{st.area_fill}"{st.area_op} stroke="none"/>'
            )
        p.append(
            f'<path class="sc-series-line" data-series="{si}" d="{d}" fill="none" '
            f'stroke="{st.stroke}" stroke-width="{fmt_num(lw)}" stroke-linejoin="round" '
            f'stroke-linecap="round"{line_dash_attr}/>'
        )
        mk = s.marker or Marker()
        if mk.enabled:
            radius = mk.radius
            radius_hover = radius + 2.5
            for i, (x, y) in enumerate(pts):
                xlabel = fr.cats[i] if i < len(fr.cats) else str(i)
                common = (
                    f'class="sc-point" data-series="{si}" data-series-name="{esc(s.name)}" '
                    f'data-x="{esc(xlabel)}" data-y="{esc(fmt_num(s.data[i]))}" '
                    f'data-color="{st.solid}" data-r="{fmt_num(radius)}" '
                    f'data-r-hover="{fmt_num(radius_hover)}"'
                )
                p.append(_marker(mk.symbol, x, y, radius, common, st.solid, theme.marker_halo))
        p.append("</g>")
