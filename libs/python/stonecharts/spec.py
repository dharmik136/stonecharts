"""Shared chart-spec model (Python view of spec/chart-spec.schema.json).

The spec is the language-agnostic 'recipe' for a chart: type, data, axes,
titles, colors, and (from the customization layer) styling. Keep this in lockstep
with spec/chart-spec.schema.json and libs/go/spec.go.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields

from .limits import enforce_spec_limits
from .util import esc
from .validate import SpecError, validate


def _opt_float(d: dict, key: str) -> float | None:
    """Float if the key is present (validation guarantees it's numeric), else None.

    This is NOT coercion: a default is supplied only when the key is ABSENT;
    malformed values are already rejected by validate() before we get here.
    """
    return float(d[key]) if key in d else None


def _normalize_datum(v: object, index: int) -> Datum:
    """Point-model normalization (scatter §3.3 Rank 3 / bubble §3.3 Rank 4,
    §5.4b lockstep).

    Bare number -> Datum(x=index, y=v) (the pinned fast path — must match Go's
    UnmarshalJSON byte-for-byte). Positional [x, y] / [x, y, z] and object
    {x, y} / {x, y, z} are sugar over the same datum; z stays None unless
    present (scatter never supplies it). validate() already rejected any
    other shape for the active chart type.
    """
    if isinstance(v, dict):
        z = float(v["z"]) if "z" in v else None
        return Datum(x=float(v["x"]), y=float(v["y"]), z=z)
    if isinstance(v, list):
        z = float(v[2]) if len(v) > 2 else None
        return Datum(x=float(v[0]), y=float(v[1]), z=z)
    return Datum(x=float(index), y=float(v))  # type: ignore[arg-type]


@dataclass
class Marker:
    enabled: bool = True
    symbol: str = "circle"  # circle | square | triangle | diamond
    radius: float = 3.5


@dataclass
class GradientStop:
    offset: float
    color: str
    opacity: float | None = None


@dataclass
class Gradient:
    """Linear gradient. Direction x1,y1 -> x2,y2 in 0..1 bounding-box coords."""

    stops: list[GradientStop]
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 1.0


@dataclass
class Pattern:
    type: str = "hatch"
    color: str = "#333333"
    background: str | None = None
    size: float = 8.0
    angle: float = 45.0
    stroke_width: float = 1.5


@dataclass
class Connector:
    enabled: bool = True
    dash_style: str = "dashed"


@dataclass
class Binning:
    count: int | None = None
    width: float | None = None
    start: float | None = None


@dataclass
class Datum:
    """One (x, y) or (x, y, z) observation — the scatter (§3.3 Rank 3) / bubble
    (§3.3 Rank 4) point model.

    Populated ONLY on Series.data_points, and only for chart type "scatter" or
    "bubble"; every other chart type continues to use Series.data (plain
    float y-values, x = category index) completely unchanged, so this
    addition carries zero byte-parity risk for line/column/area/bar. `z` is
    None for scatter (never supplied) and always set for bubble.
    """

    x: float
    y: float
    z: float | None = None


@dataclass
class BoxDatum:
    low: float
    q1: float
    median: float
    q3: float
    high: float
    outliers: list[float] = field(default_factory=list)


@dataclass
class Series:
    name: str
    data: list[float]
    type: str = "column"  # line | column (combo per-series mark kind)
    y_axis: int = 0  # 0 -> primary y_axis; 1 -> secondary_y_axis
    color: str | Gradient | None = None
    fill_opacity: float = 0.0  # >0 -> area fill under the line
    pattern: Pattern | None = None  # hatch fill for the area
    line_width: float | None = None  # None -> default 2
    dash_style: str = "solid"  # solid | dashed | dotted
    step: str | None = None  # None | before | after | center
    curve: str | None = None  # None/linear | monotone
    marker: Marker | None = None
    regression: bool = False
    low: list[float] | None = None
    high: list[float] | None = None
    data_points: list[Datum] | None = None  # scatter only — see Datum
    ohlc: list[dict] | None = None  # candlestick only — [{open,high,low,close}, ...]
    box_data: list[BoxDatum] | None = None  # boxplot only — 5-number summary per category


@dataclass
class GridLine:
    enabled: bool = True
    color: str | None = None  # None -> theme/default (#e8e8ee)
    dash_style: str = "solid"  # solid | dashed | dotted


@dataclass
class Axis:
    title: str | None = None
    categories: list[str] | None = None
    min: float | None = None
    max: float | None = None
    grid_line: GridLine | None = None  # yAxis always; xAxis only meaningful for scatter's numeric x

    opposite: bool | None = None  # secondaryYAxis only

    bin_edges: list[float] | None = None  # xAxis only (histogram bins)


@dataclass
class Margin:
    top: float | None = None
    right: float | None = None
    bottom: float | None = None
    left: float | None = None


@dataclass
class Layout:
    margin: Margin | None = None


@dataclass
class Theme:
    """Concrete color set (canonical values in spec/themes/*.json). Defaults = light,
    exactly reproducing the classic look so light output is byte-identical."""

    name: str = "light"
    background: str | None = None
    title_color: str = "#1a1a2e"
    subtitle_color: str = "#6b6b80"
    axis_label_color: str = "#6b6b80"
    axis_title_color: str = "#4a4a5a"
    grid_color: str = "#e8e8ee"
    axis_line_color: str = "#b6b6c2"
    crosshair_color: str = "#c0c0cc"
    marker_halo: str = "#fff"
    legend_text_color: str = "#33334d"
    palette: list[str] = field(
        default_factory=lambda: [
            "#2f7ed8",
            "#f45b5b",
            "#8bbc21",
            "#e4a812",
            "#1aadce",
            "#8e44ad",
            "#f28f43",
            "#77a1e5",
        ]
    )


# Built-in themes (baked; kept in lockstep with spec/themes/*.json by a parity test).
THEMES = {
    "light": Theme(),
    "dark": Theme(
        name="dark",
        background="#1a1a2e",
        title_color="#f5f5fa",
        subtitle_color="#a0a0b8",
        axis_label_color="#9a9ab0",
        axis_title_color="#c8c8d8",
        grid_color="#2e2e44",
        axis_line_color="#45455a",
        crosshair_color="#55556a",
        marker_halo="#1a1a2e",
        legend_text_color="#d0d0e0",
        palette=[
            "#5aa2f0",
            "#ff7a7a",
            "#a3d95a",
            "#f5c542",
            "#3ec8e0",
            "#b57ae0",
            "#ff9d5c",
            "#93b8ff",
        ],
    ),
}

# camelCase JSON key -> Theme attribute (for custom-object overrides + JSON parity).
_THEME_KEYS = {
    "background": "background",
    "titleColor": "title_color",
    "subtitleColor": "subtitle_color",
    "axisLabelColor": "axis_label_color",
    "axisTitleColor": "axis_title_color",
    "gridColor": "grid_color",
    "axisLineColor": "axis_line_color",
    "crosshairColor": "crosshair_color",
    "markerHalo": "marker_halo",
    "legendTextColor": "legend_text_color",
    "palette": "palette",
}


def resolve_theme(value) -> Theme:
    """A theme name, a custom object (overriding a named base), or None -> light."""
    if value is None:
        return THEMES["light"]
    if isinstance(value, str):
        return THEMES.get(value, THEMES["light"])
    if isinstance(value, dict):
        base = THEMES.get(value.get("name", "light"), THEMES["light"])
        t = Theme(**{f.name: getattr(base, f.name) for f in fields(base)})
        t.name = value.get("name", base.name)
        # Custom theme values are user input -> escape so a hostile color can't
        # break out of the SVG attribute it lands in.
        for k, attr in _THEME_KEYS.items():
            if k in value:
                v = value[k]
                if attr == "palette":
                    if isinstance(v, list) and len(v) > 0:
                        setattr(t, attr, [esc(c) for c in v])
                elif v is None:
                    setattr(t, attr, None)
                else:
                    setattr(t, attr, esc(v))
        return t
    return THEMES["light"]


@dataclass
class ChartSpec:
    series: list[Series]
    type: str = "line"
    id: str = "sc"
    theme: Theme = field(default_factory=lambda: THEMES["light"])
    title: str | None = None
    subtitle: str | None = None
    x_axis: Axis = field(default_factory=Axis)
    y_axis: Axis = field(default_factory=Axis)
    secondary_y_axis: Axis | None = None

    binning: Binning | None = None

    pre_binned: bool = False

    def __post_init__(self) -> None:
        """Point-model normalization for the typed-construction path (scatter
        §3.3 Rank 3 / bubble §3.3 Rank 4): from_dict() normalizes
        data_points itself before the Series objects exist, but a caller
        building ChartSpec/Series directly (see charts/scatter/design.md
        "Generate it - typed") never goes through from_dict, so it lands
        here instead. Guarded by `data_points is None` so from_dict's own
        already-normalized series are never touched twice.
        """
        if self.type in ("scatter", "bubble"):
            for s in self.series:
                if s.data_points is None:
                    s.data_points = [_normalize_datum(v, i) for i, v in enumerate(s.data)]
                    s.data = []

    normalization: str = "frequency"

    overlay: str | None = None

    subtype: str | None = None  # candlestick: candlestick|ohlc|hlc|heikin-ashi|hollow
    up_color: str = "#3f9b6a"  # candlestick up (close >= open) color
    down_color: str = "#d65f5f"  # candlestick down (close < open) color

    width: int = 820
    height: int = 460
    legend: bool = True
    responsive: bool = False
    a11y: bool = True
    layout: Layout | None = None
    stacking: str | None = None  # None | "normal" | "percent"
    grouping: bool = True  # True = grouped side-by-side; False = overlaid
    orientation: str | None = None  # None -> "vertical"; "horizontal" for bar-range
    total_color: str = "#4b6cb7"
    sum_indices: list[int] | None = None
    intermediate_sum_indices: list[int] | None = None
    connector: Connector | None = None
    bullet_target: float | None = None
    bullet_ranges: list[float] | None = None

    @staticmethod
    def from_dict(d: dict, *, raw_size_hint: int | None = None) -> ChartSpec:
        """Build a ChartSpec from a plain dict (parsed JSON).

        The dict is validated first (same rules as the Go renderer); a malformed
        spec raises SpecError. Unknown keys are ignored. Values are trusted after
        validation, so parsing does no coercion — defaults apply only on absence.
        """
        enforce_spec_limits(d, raw_size_hint=raw_size_hint)
        errs = validate(d)
        if errs:
            raise SpecError(errs)
        chart_type = d.get("type") or "line"
        series = []
        for i, s in enumerate(d.get("series", [])):
            m = s.get("marker")
            marker = None
            if m is not None:
                r = float(m.get("radius", 3.5))
                marker = Marker(
                    enabled=m.get("enabled", True),
                    symbol=m.get("symbol") or "circle",
                    radius=r if r != 0.0 else 3.5,
                )
            c = s.get("color")
            if isinstance(c, dict):
                color: str | Gradient | None = Gradient(
                    # Keep every stop (missing offset -> 0.0, color -> "") so this
                    # matches Go's decoder byte-for-byte; do NOT drop partial stops.
                    stops=[
                        GradientStop(
                            offset=float(st.get("offset", 0.0)),
                            color=st.get("color", ""),
                            opacity=_opt_float(st, "opacity"),
                        )
                        for st in c.get("stops", [])
                    ],
                    x1=float(c.get("x1", 0.0)),
                    y1=float(c.get("y1", 0.0)),
                    x2=float(c.get("x2", 0.0)),
                    y2=float(c.get("y2", 1.0)),
                )
            else:
                color = c
            p = s.get("pattern")
            pattern = None
            if p is not None:
                pattern = Pattern(
                    type=p.get("type") or "hatch",
                    color=p.get("color") or "#333333",
                    background=p.get("background"),
                    size=float(p.get("size", 8.0)),
                    angle=float(p.get("angle", 45.0)),
                    stroke_width=float(p.get("strokeWidth", 1.5)),
                )
            if chart_type in ("scatter", "bubble"):
                data_points = [_normalize_datum(v, j) for j, v in enumerate(s["data"])]
                data_field: list[float] = []
            else:
                data_points = None
                data_field = [float(v) for v in s["data"]]
            box_data_raw = s.get("boxData")
            box_data = None
            if isinstance(box_data_raw, list):
                box_data = [
                    BoxDatum(
                        low=float(bd["low"]),
                        q1=float(bd["q1"]),
                        median=float(bd["median"]),
                        q3=float(bd["q3"]),
                        high=float(bd["high"]),
                        outliers=[float(v) for v in bd.get("outliers", [])],
                    )
                    for bd in box_data_raw
                ]
            series.append(
                Series(
                    name=s.get("name") or f"Series {i + 1}",
                    data=data_field,
                    data_points=data_points,
                    type=s.get("type") or "column",
                    y_axis=int(s.get("yAxis", 0)),
                    color=color,
                    fill_opacity=float(s.get("fillOpacity", 0.0)),
                    pattern=pattern,
                    line_width=_opt_float(s, "lineWidth"),
                    dash_style=s.get("dashStyle") or "solid",
                    step=s.get("step"),
                    curve=s.get("curve"),
                    marker=marker,
                    regression=bool(s.get("regression", False)),
                    low=[float(v) for v in s["low"]] if "low" in s and s["low"] is not None else None,
                    high=[float(v) for v in s["high"]] if "high" in s and s["high"] is not None else None,
                    ohlc=s.get("ohlc"),
                    box_data=box_data,
                )
            )
        xa = d.get("xAxis") or {}
        ya = d.get("yAxis") or {}
        sy = d.get("secondaryYAxis")

        bn = d.get("binning")
        binning = None
        if bn is not None:
            binning = Binning(
                count=int(bn["count"]) if "count" in bn and bn["count"] is not None else None,
                width=_opt_float(bn, "width"),
                start=_opt_float(bn, "start"),
            )

        grid = None
        gl = ya.get("gridLine")
        if gl is not None:
            grid = GridLine(
                enabled=gl.get("enabled", True),
                color=gl.get("color"),
                dash_style=gl.get("dashStyle", "solid"),
            )

        # xAxis.gridLine (scatter's numeric x only; default OFF, unlike yAxis's
        # default-ON — an explicit object always wins, matching yAxis's pattern).
        xgrid = None
        xgl = xa.get("gridLine")
        if xgl is not None:
            xgrid = GridLine(
                enabled=xgl.get("enabled", False),
                color=xgl.get("color"),
                dash_style=xgl.get("dashStyle", "solid"),
            )

        layout = None
        ly = d.get("layout")
        if ly is not None:
            m = ly.get("margin")
            margin = None
            if m is not None:
                margin = Margin(
                    top=_opt_float(m, "top"),
                    right=_opt_float(m, "right"),
                    bottom=_opt_float(m, "bottom"),
                    left=_opt_float(m, "left"),
                )
            layout = Layout(margin=margin)

        secondary = None
        if sy is not None:
            sgrid = None
            sgl = sy.get("gridLine")
            if sgl is not None:
                sgrid = GridLine(
                    enabled=sgl.get("enabled", True),
                    color=sgl.get("color"),
                    dash_style=sgl.get("dashStyle", "solid"),
                )
            secondary = Axis(
                title=sy.get("title"),
                min=_opt_float(sy, "min"),
                max=_opt_float(sy, "max"),
                grid_line=sgrid,
                opposite=sy.get("opposite", True),
            )
        conn_raw = d.get("connector")
        connector_obj = None
        if conn_raw is not None and isinstance(conn_raw, dict):
            connector_obj = Connector(
                enabled=conn_raw.get("enabled", True),
                dash_style=conn_raw.get("dashStyle", "dashed"),
            )

        return ChartSpec(
            series=series,
            type=d.get("type") or "line",
            id=d.get("id") or "sc",
            theme=resolve_theme(d.get("theme")),
            title=d.get("title"),
            subtitle=d.get("subtitle"),
            x_axis=Axis(
                title=xa.get("title"),
                categories=xa.get("categories"),
                min=_opt_float(xa, "min"),
                max=_opt_float(xa, "max"),
                bin_edges=xa.get("binEdges"),
                grid_line=xgrid,
            ),
            y_axis=Axis(
                title=ya.get("title"),
                min=_opt_float(ya, "min"),
                max=_opt_float(ya, "max"),
                grid_line=grid,
            ),
            secondary_y_axis=secondary,
            binning=binning,
            pre_binned=bool(d.get("preBinned", False)),
            normalization=d.get("normalization") or "frequency",
            overlay=d.get("overlay"),
            subtype=d.get("subtype"),
            up_color=d.get("upColor") or "#3f9b6a",
            down_color=d.get("downColor") or "#d65f5f",
            width=int(d.get("width", 820)),
            height=int(d.get("height", 460)),
            legend=bool(d.get("legend", True)),
            responsive=bool(d.get("responsive", False)),
            a11y=bool(d.get("a11y", True)),
            layout=layout,
            stacking=d.get("stacking"),
            grouping=bool(d.get("grouping", True)),
            orientation=d.get("orientation"),
            total_color=d.get("totalColor") or "#4b6cb7",
            sum_indices=[int(v) for v in d.get("sumIndices", [])] or None,
            intermediate_sum_indices=[int(v) for v in d.get("intermediateSumIndices", [])] or None,
            connector=connector_obj,
            bullet_target=_opt_float(d, "bulletTarget"),
            bullet_ranges=[float(v) for v in d["bulletRanges"]]
            if "bulletRanges" in d and isinstance(d.get("bulletRanges"), list)
            else None,
        )
