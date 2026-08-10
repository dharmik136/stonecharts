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
from .charts import boxplot as _boxplot
from .charts import bubble as _bubble
from .charts import bullet as _bullet
from .charts import candlestick as _candlestick
from .charts import column as _column
from .charts import columnrange as _columnrange
from .charts import combo as _combo
from .charts import dumbbell as _dumbbell
from .charts import error_bar as _error_bar
from .charts import flame_chart as _flame_chart
from .charts import funnel as _funnel
from .charts import gauge as _gauge
from .charts import histogram as _histogram
from .charts import line as _line
from .charts import lollipop as _lollipop
from .charts import pie as _pie
from .charts import scatter as _scatter
from .charts import streamgraph as _streamgraph
from .charts import technical_indicators as _technical_indicators
from .charts import timeline as _timeline
from .charts import variwide as _variwide
from .charts import vector_plot as _vector_plot
from .charts import waterfall as _waterfall
from .charts import windbarb as _windbarb
from .charts import xrange as _xrange
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
    "boxplot": _boxplot.render_svg,
    "bullet": _bullet.render_svg,
    "combo": _combo.render_svg,
    "column": _column.render_svg,
    "dumbbell": _dumbbell.render_svg,
    "columnrange": _columnrange.render_svg,
    "error-bar": _error_bar.render_svg,
    "flame-chart": _flame_chart.render_svg,
    "funnel": _funnel.render_svg,
    "gauge": _gauge.render_svg,
    "histogram": _histogram.render_svg,
    "line": _line.render_svg,
    "lollipop": _lollipop.render_svg,
    "pie": _pie.render_svg,
    "scatter": _scatter.render_svg,
    "streamgraph": _streamgraph.render_svg,
    "technical-indicators": _technical_indicators.render_svg,
    "bubble": _bubble.render_svg,
    "candlestick": _candlestick.render_svg,
    "timeline": _timeline.render_svg,
    "variwide": _variwide.render_svg,
    "vector-plot": _vector_plot.render_svg,
    "waterfall": _waterfall.render_svg,
    "windbarb": _windbarb.render_svg,
    "xrange": _xrange.render_svg,
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
    if spec.type == "boxplot":
        cats = spec.x_axis.categories or []
        rows = []
        for s in spec.series:
            for i, bd in enumerate(s.box_data or []):
                cat = cats[i] if i < len(cats) else str(i)
                outliers_str = ", ".join(fmt_num(o) for o in bd.outliers) if bd.outliers else ""
                rows.append(
                    f'<tr><th scope="row">{esc(cat)}</th>'
                    f"<td>{esc(s.name)}</td>"
                    f"<td>{esc(fmt_num(bd.low))}</td>"
                    f"<td>{esc(fmt_num(bd.q1))}</td>"
                    f"<td>{esc(fmt_num(bd.median))}</td>"
                    f"<td>{esc(fmt_num(bd.q3))}</td>"
                    f"<td>{esc(fmt_num(bd.high))}</td>"
                    f"<td>{esc(outliers_str)}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Category</th><th scope="col">Series</th>'
            '<th scope="col">Low</th><th scope="col">Q1</th>'
            '<th scope="col">Median</th><th scope="col">Q3</th>'
            '<th scope="col">High</th><th scope="col">Outliers</th></tr></thead>'
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
    if spec.type == "gauge":
        rows = []
        s0 = spec.series[0] if spec.series else None
        if s0 and s0.data:
            g_min = spec.gauge_min
            g_max = spec.gauge_max
            rows.append(
                f'<tr><th scope="row">{esc(s0.name)}</th>'
                f"<td>{esc(fmt_num(s0.data[0]))}</td>"
                f"<td>{esc(fmt_num(g_min))}</td>"
                f"<td>{esc(fmt_num(g_max))}</td></tr>"
            )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Metric</th><th scope="col">Value</th>'
            '<th scope="col">Min</th><th scope="col">Max</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "pie":
        cats = spec.x_axis.categories or []
        rows = []
        s0 = spec.series[0] if spec.series else None
        if s0:
            total = sum(v for v in s0.data if v > 0)
            for i, v in enumerate(s0.data):
                cat = cats[i] if i < len(cats) else str(i)
                pct = (v / total) * 100 if total > 0 else 0.0
                rows.append(
                    f'<tr><th scope="row">{esc(cat)}</th>'
                    f"<td>{esc(fmt_num(v))}</td>"
                    f"<td>{pct:.1f}%</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Category</th><th scope="col">Value</th>'
            '<th scope="col">Percentage</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "xrange":
        rows = []
        lane_cats = spec.y_axis.categories or []
        for s in spec.series:
            for sp in s.spans or []:
                lane_label = lane_cats[sp.y] if sp.y < len(lane_cats) else str(sp.y)
                rows.append(
                    f'<tr><th scope="row">{esc(s.name)}</th>'
                    f"<td>{esc(lane_label)}</td>"
                    f"<td>{esc(fmt_num(sp.x))}</td>"
                    f"<td>{esc(fmt_num(sp.x2))}</td>"
                    f"<td>{esc(fmt_num(sp.x2 - sp.x))}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Series</th><th scope="col">Lane</th>'
            '<th scope="col">Start</th><th scope="col">End</th>'
            '<th scope="col">Duration</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "flame-chart":
        rows = []
        for s in spec.series:
            for fr in s.frames or []:
                duration = fr.x2 - fr.x
                name = fr.name or ""
                rows.append(
                    f'<tr><th scope="row">{esc(s.name)}</th><td>{fr.depth}</td>'
                    f"<td>{esc(fmt_num(fr.x))}</td><td>{esc(fmt_num(fr.x2))}</td>"
                    f"<td>{esc(fmt_num(duration))}</td><td>{esc(name)}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Series</th><th scope="col">Depth</th>'
            '<th scope="col">Start</th><th scope="col">End</th>'
            '<th scope="col">Duration</th><th scope="col">Name</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "technical-indicators":
        cats = spec.x_axis.categories or []
        rows = []
        for s in spec.series:
            for i, v in enumerate(s.data):
                cat = cats[i] if i < len(cats) else str(i)
                rows.append(f'<tr><th scope="row">{esc(cat)}</th><td>{esc(s.name)}</td><td>{esc(fmt_num(v))}</td></tr>')
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Category</th><th scope="col">Series</th>'
            '<th scope="col">Value</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    if spec.type == "vector-plot":
        rows = []
        for s in spec.series:
            x_arr = s.x or [float(i) for i in range(len(s.data))]
            dir_arr = s.direction or [0.0] * len(s.data)
            len_arr = s.length or [0.0] * len(s.data)
            n_pts = min(len(x_arr), len(s.data), len(dir_arr), len(len_arr))
            for i in range(n_pts):
                rows.append(
                    f'<tr><th scope="row">{esc(s.name)}</th>'
                    f"<td>{esc(fmt_num(x_arr[i]))}</td>"
                    f"<td>{esc(fmt_num(s.data[i]))}</td>"
                    f"<td>{esc(fmt_num(dir_arr[i]))}</td>"
                    f"<td>{esc(fmt_num(len_arr[i]))}</td></tr>"
                )
        return (
            f'<table class="sc-visually-hidden">{caption}'
            '<thead><tr><th scope="col">Series</th><th scope="col">X</th>'
            '<th scope="col">Y</th><th scope="col">Direction</th>'
            '<th scope="col">Length</th></tr></thead>'
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
