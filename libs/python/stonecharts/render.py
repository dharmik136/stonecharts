"""Render a ChartSpec to a self-contained interactive HTML document.

The SVG is drawn per chart type (charts/*.py); this module wraps it with CSS and
the shared JS interaction runtime (runtime/chart-interactions.js at the repo
root — one source of truth, embedded inline so the output is a single portable
file).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .capabilities import CapabilityError, capabilities
from .charts import area as _area
from .charts import arearange as _arearange
from .charts import bar as _bar
from .charts import bubble as _bubble
from .charts import candlestick as _candlestick
from .charts import column as _column
from .charts import columnrange as _columnrange
from .charts import combo as _combo
from .charts import error_bar as _error_bar
from .charts import histogram as _histogram
from .charts import line as _line
from .charts import scatter as _scatter
from .charts import waterfall as _waterfall
from .limits import enforce_svg_limit
from .spec import ChartSpec
from .util import esc, fmt_num

# The canonical shared runtime lives at <repo>/runtime/chart-interactions.js.
# render.py -> stonecharts -> python -> libs -> <repo>
_RUNTIME_PATH = Path(__file__).resolve().parents[3] / "runtime" / "chart-interactions.js"

# chart type -> SVG renderer. New chart types register here.
_RENDERERS: dict[str, Callable[[ChartSpec], str]] = {
    "area": _area.render_svg,
    "arearange": _arearange.render_svg,
    "bar": _bar.render_svg,
    "combo": _combo.render_svg,
    "column": _column.render_svg,
    "columnrange": _columnrange.render_svg,
    "error-bar": _error_bar.render_svg,
    "histogram": _histogram.render_svg,
    "line": _line.render_svg,
    "scatter": _scatter.render_svg,
    "bubble": _bubble.render_svg,
    "candlestick": _candlestick.render_svg,
    "waterfall": _waterfall.render_svg,
}
_CAPABILITIES = capabilities()

_CSS = """
  .sc-chart-wrap{position:relative;display:inline-block;line-height:0}
  .sc-chart{display:block;background:#fff}
  .sc-point{cursor:pointer;transition:r .08s ease}
  .sc-legend-item.sc-hidden{opacity:.35}
  .sc-tooltip{position:absolute;pointer-events:none;z-index:10;background:rgba(255,255,255,.97);
    border:1px solid #d8d8e0;border-radius:6px;box-shadow:0 4px 14px rgba(20,20,40,.14);
    padding:7px 10px;font:12px/1.4 Segoe UI,Helvetica,Arial,sans-serif;color:#22223a;white-space:nowrap}
  .sc-tt-title{font-weight:600;margin-bottom:2px}
  .sc-tt-row{display:flex;align-items:center}
  .sc-tt-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
  .sc-visually-hidden{position:absolute!important;width:1px!important;height:1px!important;
    padding:0!important;margin:-1px!important;overflow:hidden!important;
    clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
""".strip()


def _data_table(spec: ChartSpec) -> str:
    """A visually-hidden HTML data table: the accessible, keyboard-navigable
    alternative to the SVG (which is role="img"). Screen readers read this."""
    caption = f"<caption>{esc(spec.title)}</caption>" if spec.title else ""
    if spec.type in ("arearange", "columnrange"):
        cats = spec.x_axis.categories or []
        rows = []
        for s in spec.series:
            low_arr = getattr(s, "low", None) or []
            high_arr = getattr(s, "high", None) or []
            is_cr = spec.type == "columnrange"
            for i in range(len(s.data)):
                cat = cats[i] if i < len(cats) else str(i)
                if is_cr:
                    lo_val = s.data[i]
                    hi_val = high_arr[i] if i < len(high_arr) else lo_val
                else:
                    hi_val = s.data[i]
                    lo_val = low_arr[i] if i < len(low_arr) else hi_val
                rows.append(
                    f'<tr><th scope="row">{esc(cat)}</th>'
                    f"<td>{esc(s.name)}</td>"
                    f"<td>{esc(fmt_num(lo_val))}</td>"
                    f"<td>{esc(fmt_num(hi_val))}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Category</th><th scope="col">Series</th>'
            '<th scope="col">Low</th><th scope="col">High</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "error-bar":
        cats = spec.x_axis.categories or []
        rows = []
        for s in spec.series:
            low_arr = getattr(s, "low", None) or []
            high_arr = getattr(s, "high", None) or []
            for i, y_val in enumerate(s.data):
                cat = cats[i] if i < len(cats) else str(i)
                lo_val = low_arr[i] if i < len(low_arr) else y_val
                hi_val = high_arr[i] if i < len(high_arr) else y_val
                rows.append(
                    f'<tr><th scope="row">{esc(cat)}</th>'
                    f"<td>{esc(s.name)}</td>"
                    f"<td>{esc(fmt_num(y_val))}</td>"
                    f"<td>{esc(fmt_num(lo_val))}</td>"
                    f"<td>{esc(fmt_num(hi_val))}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Category</th><th scope="col">Series</th>'
            '<th scope="col">Y</th><th scope="col">Low</th>'
            '<th scope="col">High</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "candlestick":
        cats = spec.x_axis.categories or []
        rows = []
        for s in spec.series:
            ohlc = getattr(s, "ohlc", None) or []
            for i, bar in enumerate(ohlc):
                cat = cats[i] if i < len(cats) else str(i)
                rows.append(
                    f'<tr><th scope="row">{esc(cat)}</th>'
                    f"<td>{esc(s.name)}</td>"
                    f"<td>{esc(fmt_num(bar['open']))}</td>"
                    f"<td>{esc(fmt_num(bar['high']))}</td>"
                    f"<td>{esc(fmt_num(bar['low']))}</td>"
                    f"<td>{esc(fmt_num(bar['close']))}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Category</th><th scope="col">Series</th>'
            '<th scope="col">Open</th><th scope="col">High</th>'
            '<th scope="col">Low</th><th scope="col">Close</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type in ("scatter", "bubble"):
        # Point-model data (scatter §3.3 Rank 3 / bubble §3.3 Rank 4, §5.4b-DT):
        # data is (x, y) or (x, y, z), not a coerced single number per shared
        # category — a long-format table (one row per point) is the only
        # lossless shape.
        has_z = spec.type == "bubble"
        rows = []
        for s in spec.series:
            for d in s.data_points or []:
                z_cell = f"<td>{esc(fmt_num(d.z if d.z is not None else 0.0))}</td>" if has_z else ""
                rows.append(
                    f'<tr><th scope="row">{esc(s.name)}</th>'
                    f"<td>{esc(fmt_num(d.x))}</td><td>{esc(fmt_num(d.y))}</td>{z_cell}</tr>"
                )
        z_head = '<th scope="col">Z</th>' if has_z else ""
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Series</th><th scope="col">X</th>'
            f'<th scope="col">Y</th>{z_head}</tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    n = max((len(s.data) for s in spec.series), default=0)
    cats = spec.x_axis.categories or []
    head = "".join(f'<th scope="col">{esc(cats[i] if i < len(cats) else str(i))}</th>' for i in range(n))
    rows = []
    for s in spec.series:
        cells = "".join(f"<td>{esc(fmt_num(s.data[i]))}</td>" if i < len(s.data) else "<td></td>" for i in range(n))
        rows.append(f'<tr><th scope="row">{esc(s.name)}</th>{cells}</tr>')
    return (
        f'<table class="sc-visually-hidden">{caption}'
        f"<thead><tr><td></td>{head}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_svg(spec: ChartSpec) -> str:
    resolved_type = spec.type or "line"
    if resolved_type not in _CAPABILITIES["chartTypes"]:
        raise CapabilityError(
            "E_CAPABILITY",
            "$.type",
            f'unsupported chart type "{resolved_type}"',
            {"expected": list(_CAPABILITIES["chartTypes"]), "received": resolved_type},
        )
    renderer = _RENDERERS.get(resolved_type)
    if renderer is None:
        raise CapabilityError(
            "E_CAPABILITY",
            "$.type",
            f'unsupported chart type "{resolved_type}"',
            {"expected": list(_CAPABILITIES["chartTypes"]), "received": resolved_type},
        )
    svg = renderer(spec)
    enforce_svg_limit(svg)
    return svg


def _runtime_js() -> str:
    try:
        return _RUNTIME_PATH.read_text(encoding="utf-8")
    except OSError:
        # Degrade gracefully: static chart still renders, just without interactivity.
        return f"/* StoneCharts runtime not found at {_RUNTIME_PATH} */"


def render_html(spec: ChartSpec, page_title: str | None = None) -> str:
    """Return a full, self-contained interactive HTML document for the chart."""
    svg = render_svg(spec)
    title = page_title or spec.title or "StoneCharts"
    wrap_style = (
        f' style="display:block;width:100%;max-width:{spec.width}px;aspect-ratio:{spec.width} / {spec.height}"'
        if spec.responsive
        else ""
    )
    table = _data_table(spec) if spec.a11y else ""
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title>\n"
        f"<style>{_CSS}</style></head>\n"
        "<body>\n"
        f'<div class="sc-chart-wrap"{wrap_style}>{svg}{table}'
        f'<div class="sc-tooltip" style="display:none"></div></div>\n'
        f"<script>{_runtime_js()}</script>\n"
        "</body></html>\n"
    )


def save_html(spec: ChartSpec, path: str | Path, page_title: str | None = None) -> Path:
    out = Path(path)
    out.write_text(render_html(spec, page_title), encoding="utf-8")
    return out
