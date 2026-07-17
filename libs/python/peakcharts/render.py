"""Render a ChartSpec to a self-contained interactive HTML document.

The SVG is drawn per chart type (charts/*.py); this module wraps it with CSS and
the shared JS interaction runtime (runtime/chart-interactions.js at the repo
root — one source of truth, embedded inline so the output is a single portable
file).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from .charts import column as _column
from .charts import line as _line
from .spec import ChartSpec
from .util import esc, fmt_num

# The canonical shared runtime lives at <repo>/runtime/chart-interactions.js.
# render.py -> peakcharts -> python -> libs -> <repo>
_RUNTIME_PATH = Path(__file__).resolve().parents[3] / "runtime" / "chart-interactions.js"

# chart type -> SVG renderer. New chart types register here.
_RENDERERS: Dict[str, Callable[[ChartSpec], str]] = {
    "column": _column.render_svg,
    "line": _line.render_svg,
}

_CSS = """
  .pk-chart-wrap{position:relative;display:inline-block;line-height:0}
  .pk-chart{display:block;background:#fff}
  .pk-point{cursor:pointer;transition:r .08s ease}
  .pk-legend-item.pk-hidden{opacity:.35}
  .pk-tooltip{position:absolute;pointer-events:none;z-index:10;background:rgba(255,255,255,.97);
    border:1px solid #d8d8e0;border-radius:6px;box-shadow:0 4px 14px rgba(20,20,40,.14);
    padding:7px 10px;font:12px/1.4 Segoe UI,Helvetica,Arial,sans-serif;color:#22223a;white-space:nowrap}
  .pk-tt-title{font-weight:600;margin-bottom:2px}
  .pk-tt-row{display:flex;align-items:center}
  .pk-tt-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
  .pk-visually-hidden{position:absolute!important;width:1px!important;height:1px!important;
    padding:0!important;margin:-1px!important;overflow:hidden!important;
    clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
""".strip()


def _data_table(spec: ChartSpec) -> str:
    """A visually-hidden HTML data table: the accessible, keyboard-navigable
    alternative to the SVG (which is role="img"). Screen readers read this."""
    n = max((len(s.data) for s in spec.series), default=0)
    cats = spec.x_axis.categories or [str(i) for i in range(n)]
    head = "".join(f'<th scope="col">{esc(cats[i])}</th>' for i in range(n))
    rows = []
    for s in spec.series:
        cells = "".join(
            f"<td>{esc(fmt_num(s.data[i]))}</td>" if i < len(s.data) else "<td></td>"
            for i in range(n)
        )
        rows.append(f'<tr><th scope="row">{esc(s.name)}</th>{cells}</tr>')
    caption = f"<caption>{esc(spec.title)}</caption>" if spec.title else ""
    return (
        f'<table class="pk-visually-hidden">{caption}'
        f'<thead><tr><td></td>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def render_svg(spec: ChartSpec) -> str:
    renderer = _RENDERERS.get(spec.type)
    if renderer is None:
        raise ValueError(
            f"Unknown chart type {spec.type!r}. Known: {', '.join(sorted(_RENDERERS))}"
        )
    return renderer(spec)


def _runtime_js() -> str:
    try:
        return _RUNTIME_PATH.read_text(encoding="utf-8")
    except OSError:
        # Degrade gracefully: static chart still renders, just without interactivity.
        return "/* PeakCharts runtime not found at %s */" % _RUNTIME_PATH


def render_html(spec: ChartSpec, page_title: str | None = None) -> str:
    """Return a full, self-contained interactive HTML document for the chart."""
    svg = render_svg(spec)
    title = page_title or spec.title or "PeakCharts"
    wrap_style = (
        f' style="display:block;width:100%;max-width:{spec.width}px;'
        f'aspect-ratio:{spec.width} / {spec.height}"'
        if spec.responsive else ""
    )
    table = _data_table(spec) if spec.a11y else ""
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title>\n"
        f"<style>{_CSS}</style></head>\n"
        "<body>\n"
        f'<div class="pk-chart-wrap"{wrap_style}>{svg}{table}'
        f'<div class="pk-tooltip" style="display:none"></div></div>\n'
        f"<script>{_runtime_js()}</script>\n"
        "</body></html>\n"
    )


def save_html(spec: ChartSpec, path: str | Path, page_title: str | None = None) -> Path:
    out = Path(path)
    out.write_text(render_html(spec, page_title), encoding="utf-8")
    return out
