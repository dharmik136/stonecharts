"""Strict chart-spec validation.

Runs BEFORE renderer-specific parsing and rejects malformed input with structured,
cross-language errors. The same rules live in libs/go/validate.go, so both
renderers accept and reject exactly the same specs with the same error text.

Policy (see docs/customization/plan.md):
- A property present with the wrong type is an ERROR — never silently coerced.
- Numeric fields reject strings, booleans, null, NaN and Infinity.
- Defaults apply only when a property is ABSENT (handled during parsing), never
  as a cover for malformed input.

`validate(spec_dict)` returns a list of error strings (empty = valid). Errors are
emitted in a deterministic order so both languages produce identical output.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .util import fmt_num

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_THEME_NAMES = {"light", "dark"}
_DASH_STYLES = {"solid", "dashed", "dotted"}
_MARKER_SYMBOLS = {"circle", "square", "triangle", "diamond"}
_STEP_TYPES = {"before", "after", "center"}
_CURVE_TYPES = {"linear", "monotone"}
_PATTERN_TYPES = {"hatch"}


class SpecError(ValueError):
    """Raised when a chart spec fails validation. `.errors` lists every problem."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("invalid chart spec:\n  " + "\n  ".join(self.errors))


def _jtype(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return "unknown"


def _num(v: Any, path: str, errs: list[str]) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        errs.append(f"{path}: expected number, received {_jtype(v)}")
    elif isinstance(v, float) and not math.isfinite(v):
        errs.append(f"{path}: expected finite number, received " + ("NaN" if math.isnan(v) else "Infinity"))


def _nonneg_num(v: Any, path: str, errs: list[str]) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return
    if isinstance(v, float) and not math.isfinite(v):
        return
    if float(v) < 0:
        errs.append(f"{path}: expected non-negative number, received {fmt_num(float(v))}")


def _intnum(v: Any, path: str, errs: list[str]) -> None:
    # width/height map to Go int; require an integer-VALUED number (5 and 5.0 ok,
    # 5.7 rejected) so both languages agree. Go's interface{} can't tell 5 from 5.0.
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        errs.append(f"{path}: expected integer, received {_jtype(v)}")
    elif isinstance(v, float) and (not math.isfinite(v) or not v.is_integer()):
        errs.append(
            f"{path}: expected integer, received "
            + ("non-finite number" if not math.isfinite(v) else "non-integer number")
        )


def _str(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, str):
        errs.append(f"{path}: expected string, received {_jtype(v)}")


def _bool(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, bool):
        errs.append(f"{path}: expected boolean, received {_jtype(v)}")


def _str_array(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, list):
        errs.append(f"{path}: expected array, received {_jtype(v)}")
        return
    for i, e in enumerate(v):
        _str(e, f"{path}[{i}]", errs)


def _gridline(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "enabled" in v:
        _bool(v["enabled"], f"{path}.enabled", errs)
    if "color" in v:
        _str(v["color"], f"{path}.color", errs)
    if "dashStyle" in v:
        _str(v["dashStyle"], f"{path}.dashStyle", errs)


def _axis(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "title" in v:
        _str(v["title"], f"{path}.title", errs)
    if "categories" in v:
        _str_array(v["categories"], f"{path}.categories", errs)
    if "min" in v:
        _num(v["min"], f"{path}.min", errs)
    if "max" in v:
        _num(v["max"], f"{path}.max", errs)
    if "gridLine" in v:
        _gridline(v["gridLine"], f"{path}.gridLine", errs)
    if "opposite" in v:
        _bool(v["opposite"], f"{path}.opposite", errs)
    if "binEdges" in v:
        if not isinstance(v["binEdges"], list):
            errs.append(f"{path}.binEdges: expected array, received {_jtype(v['binEdges'])}")
        else:
            for i, e in enumerate(v["binEdges"]):
                _num(e, f"{path}.binEdges[{i}]", errs)


def _margin(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    for k in ("top", "right", "bottom", "left"):
        if k in v:
            _num(v[k], f"{path}.{k}", errs)
            if isinstance(v[k], (int, float)) and not isinstance(v[k], bool) and v[k] < 0:
                errs.append(f"{path}.{k}: expected non-negative number, received {fmt_num(float(v[k]))}")


def _layout(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "margin" in v:
        _margin(v["margin"], f"{path}.margin", errs)


def _num_or_default(v: Any, default: float) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else default


def _marker(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "enabled" in v:
        _bool(v["enabled"], f"{path}.enabled", errs)
    if "symbol" in v:
        _str(v["symbol"], f"{path}.symbol", errs)
    if "radius" in v:
        _num(v["radius"], f"{path}.radius", errs)


def _pattern(v: Any, path: str, errs: list[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    for k in ("type", "color", "background"):
        if k in v:
            _str(v[k], f"{path}.{k}", errs)
    for k in ("size", "angle", "strokeWidth"):
        if k in v:
            _num(v[k], f"{path}.{k}", errs)
    if isinstance(v.get("type"), str) and v["type"] not in _PATTERN_TYPES:
        errs.append(f'{path}.type: expected one of "hatch", received "{v["type"]}"')
    if "color" in v and isinstance(v["color"], str) and not _HEX_COLOR_RE.fullmatch(v["color"]):
        errs.append(f'{path}.color: expected hex color, received "{v["color"]}"')
    if "background" in v and isinstance(v["background"], str) and not _HEX_COLOR_RE.fullmatch(v["background"]):
        errs.append(f'{path}.background: expected hex color, received "{v["background"]}"')


def _gradient(v: dict, path: str, errs: list[str]) -> None:
    for k in ("x1", "y1", "x2", "y2"):
        if k in v:
            _num(v[k], f"{path}.{k}", errs)
    if "type" in v:
        _str(v["type"], f"{path}.type", errs)
    if "stops" in v:
        stops = v["stops"]
        if not isinstance(stops, list):
            errs.append(f"{path}.stops: expected array, received {_jtype(stops)}")
        else:
            for i, st in enumerate(stops):
                sp = f"{path}.stops[{i}]"
                if not isinstance(st, dict):
                    errs.append(f"{sp}: expected object, received {_jtype(st)}")
                    continue
                if "offset" in st:
                    _num(st["offset"], f"{sp}.offset", errs)
                if "color" in st:
                    _str(st["color"], f"{sp}.color", errs)
                if "opacity" in st:
                    _num(st["opacity"], f"{sp}.opacity", errs)
                if isinstance(st.get("color"), str) and not _HEX_COLOR_RE.fullmatch(st["color"]):
                    errs.append(f'{sp}.color: expected hex color, received "{st["color"]}"')


def _color(v: Any, path: str, errs: list[str]) -> None:
    # oneOf: hex string OR a linear-gradient object.
    if isinstance(v, str):
        if not _HEX_COLOR_RE.fullmatch(v):
            errs.append(f'{path}: expected hex color, received "{v}"')
        return
    if isinstance(v, dict):
        _gradient(v, path, errs)
        return
    errs.append(f"{path}: expected string or gradient object, received {_jtype(v)}")


def _theme(v: Any, path: str, errs: list[str]) -> None:
    # oneOf: theme name (string) OR a theme object.
    if isinstance(v, str):
        if v not in _THEME_NAMES:
            errs.append(f'{path}: expected one of "light", "dark", received "{v}"')
        return
    if not isinstance(v, dict):
        errs.append(f"{path}: expected string or theme object, received {_jtype(v)}")
        return
    if "name" in v:
        _str(v["name"], f"{path}.name", errs)
    if "background" in v and v["background"] is not None:  # background is nullable
        _str(v["background"], f"{path}.background", errs)
    for k in (
        "titleColor",
        "subtitleColor",
        "axisLabelColor",
        "axisTitleColor",
        "gridColor",
        "axisLineColor",
        "crosshairColor",
        "markerHalo",
        "legendTextColor",
    ):
        if k in v:
            _str(v[k], f"{path}.{k}", errs)
            if isinstance(v[k], str) and not _HEX_COLOR_RE.fullmatch(v[k]):
                errs.append(f'{path}.{k}: expected hex color, received "{v[k]}"')
    if "palette" in v:
        _str_array(v["palette"], f"{path}.palette", errs)
        if isinstance(v["palette"], list):
            for i, c in enumerate(v["palette"]):
                if isinstance(c, str) and not _HEX_COLOR_RE.fullmatch(c):
                    errs.append(f'{path}.palette[{i}]: expected hex color, received "{c}"')


def _datum(v: Any, path: str, errs: list[str]) -> None:
    """Point-model element (scatter only, §3.3 Rank 3): number | [x,y] | {x,y}."""
    if isinstance(v, bool):
        errs.append(f"{path}: expected number, [x,y], or {{x,y}}, received boolean")
    elif isinstance(v, (int, float)):
        _num(v, path, errs)
    elif isinstance(v, list):
        if len(v) != 2:
            errs.append(f"{path}: expected a 2-element [x,y] array, received {len(v)} elements")
        else:
            _num(v[0], f"{path}[0]", errs)
            _num(v[1], f"{path}[1]", errs)
    elif isinstance(v, dict):
        if "x" not in v:
            errs.append(f"{path}.x: required")
        else:
            _num(v["x"], f"{path}.x", errs)
        if "y" not in v:
            errs.append(f"{path}.y: required")
        else:
            _num(v["y"], f"{path}.y", errs)
        extra = sorted(set(v.keys()) - {"x", "y"})
        for k in extra:
            errs.append(f"{path}.{k}: unknown field")
    else:
        errs.append(f"{path}: expected number, [x,y], or {{x,y}}, received {_jtype(v)}")


def _datum_xyz(v: Any, path: str, errs: list[str]) -> None:
    """Point-model element (bubble only, §3.3 Rank 4): number | [x,y,z] | {x,y,z}."""
    if isinstance(v, bool):
        errs.append(f"{path}: expected number, [x,y,z], or {{x,y,z}}, received boolean")
    elif isinstance(v, (int, float)):
        _num(v, path, errs)
    elif isinstance(v, list):
        if len(v) != 3:
            errs.append(f"{path}: expected a 3-element [x,y,z] array, received {len(v)} elements")
        else:
            _num(v[0], f"{path}[0]", errs)
            _num(v[1], f"{path}[1]", errs)
            _num(v[2], f"{path}[2]", errs)
    elif isinstance(v, dict):
        for key in ("x", "y", "z"):
            if key not in v:
                errs.append(f"{path}.{key}: required")
            else:
                _num(v[key], f"{path}.{key}", errs)
        extra = sorted(set(v.keys()) - {"x", "y", "z"})
        for k in extra:
            errs.append(f"{path}.{k}: unknown field")
    else:
        errs.append(f"{path}: expected number, [x,y,z], or {{x,y,z}}, received {_jtype(v)}")


def _series(v: Any, path: str, errs: list[str], chart_type: Any = None) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "name" in v:
        _str(v["name"], f"{path}.name", errs)
    if "yAxis" in v:
        _intnum(v["yAxis"], f"{path}.yAxis", errs)
        if isinstance(v["yAxis"], (int, float)) and not isinstance(v["yAxis"], bool) and int(v["yAxis"]) not in (0, 1):
            errs.append(f'{path}.yAxis: expected one of 0, 1, received "{int(v["yAxis"])}"')
    if "data" not in v and chart_type not in ("boxplot", "flame-chart"):
        errs.append(f"{path}.data: required")
    elif "data" not in v:
        pass
    elif not isinstance(v["data"], list):
        errs.append(f"{path}.data: expected array, received {_jtype(v['data'])}")
    elif chart_type == "scatter":
        for i, e in enumerate(v["data"]):
            _datum(e, f"{path}.data[{i}]", errs)
    elif chart_type == "bubble":
        for i, e in enumerate(v["data"]):
            _datum_xyz(e, f"{path}.data[{i}]", errs)
    else:
        for i, e in enumerate(v["data"]):
            _num(e, f"{path}.data[{i}]", errs)
    if "color" in v:
        _color(v["color"], f"{path}.color", errs)
    if "fillOpacity" in v:
        _num(v["fillOpacity"], f"{path}.fillOpacity", errs)
    if "pattern" in v:
        _pattern(v["pattern"], f"{path}.pattern", errs)
    if "lineWidth" in v:
        _num(v["lineWidth"], f"{path}.lineWidth", errs)
    for k in ("dashStyle", "step", "curve"):
        if k in v:
            _str(v[k], f"{path}.{k}", errs)
    if isinstance(v.get("dashStyle"), str) and v["dashStyle"] not in _DASH_STYLES:
        errs.append(f'{path}.dashStyle: expected one of "solid", "dashed", "dotted", received "{v["dashStyle"]}"')
    if isinstance(v.get("step"), str) and v["step"] not in _STEP_TYPES:
        errs.append(f'{path}.step: expected one of "before", "after", "center", received "{v["step"]}"')
    if isinstance(v.get("curve"), str) and v["curve"] not in _CURVE_TYPES:
        errs.append(f'{path}.curve: expected one of "linear", "monotone", received "{v["curve"]}"')
    if (
        "marker" in v
        and isinstance(v["marker"], dict)
        and isinstance(v["marker"].get("symbol"), str)
        and v["marker"]["symbol"] not in _MARKER_SYMBOLS
    ):
        errs.append(
            f'{path}.marker.symbol: expected one of "circle", "square", "triangle", "diamond", received "{v["marker"]["symbol"]}"'
        )
    if "marker" in v:
        _marker(v["marker"], f"{path}.marker", errs)
    if "type" in v:
        _str(v["type"], f"{path}.type", errs)
    if "labels" in v:
        _str_array(v["labels"], f"{path}.labels", errs)
    if "x" in v:
        if not isinstance(v["x"], list):
            errs.append(f"{path}.x: expected array, received {_jtype(v['x'])}")
        else:
            for i, e in enumerate(v["x"]):
                _num(e, f"{path}.x[{i}]", errs)
    if "direction" in v:
        if not isinstance(v["direction"], list):
            errs.append(f"{path}.direction: expected array, received {_jtype(v['direction'])}")
        else:
            for i, e in enumerate(v["direction"]):
                _num(e, f"{path}.direction[{i}]", errs)
    if "length" in v:
        if not isinstance(v["length"], list):
            errs.append(f"{path}.length: expected array, received {_jtype(v['length'])}")
        else:
            for i, e in enumerate(v["length"]):
                _num(e, f"{path}.length[{i}]", errs)
    if "spans" in v:
        if not isinstance(v["spans"], list):
            errs.append(f"{path}.spans: expected array, received {_jtype(v['spans'])}")
        else:
            for i, sp in enumerate(v["spans"]):
                sp_path = f"{path}.spans[{i}]"
                if not isinstance(sp, dict):
                    errs.append(f"{sp_path}: expected object, received {_jtype(sp)}")
                    continue
                for req in ("x", "x2", "y"):
                    if req not in sp:
                        errs.append(f"{sp_path}.{req}: required")
                    elif req == "y":
                        if not isinstance(sp[req], (int, float)):
                            errs.append(f"{sp_path}.{req}: expected number, received {_jtype(sp[req])}")
                    else:
                        _num(sp[req], f"{sp_path}.{req}", errs)
                if "id" in sp:
                    _str(sp["id"], f"{sp_path}.id", errs)
                if "name" in sp:
                    _str(sp["name"], f"{sp_path}.name", errs)
                if "dependency" in sp:
                    _str_array(sp["dependency"], f"{sp_path}.dependency", errs)
                if "milestone" in sp and not isinstance(sp["milestone"], bool):
                    errs.append(f"{sp_path}.milestone: expected boolean, received {_jtype(sp['milestone'])}")
    if "frames" in v:
        if not isinstance(v["frames"], list):
            errs.append(f"{path}.frames: expected array, received {_jtype(v['frames'])}")
        else:
            for i, fr in enumerate(v["frames"]):
                fr_path = f"{path}.frames[{i}]"
                if not isinstance(fr, dict):
                    errs.append(f"{fr_path}: expected object, received {_jtype(fr)}")
                    continue
                for req in ("x", "x2", "depth"):
                    if req not in fr:
                        errs.append(f"{fr_path}.{req}: required")
                    else:
                        _num(fr[req], f"{fr_path}.{req}", errs)
                if "name" in fr:
                    _str(fr["name"], f"{fr_path}.name", errs)
                if "color" in fr:
                    _str(fr["color"], f"{fr_path}.color", errs)
    if "volume" in v:
        vol = v["volume"]
        if not isinstance(vol, list):
            errs.append(f"{path}.volume: expected array, received {_jtype(vol)}")
        else:
            for j, val in enumerate(vol):
                if not isinstance(val, (int, float)):
                    errs.append(f"{path}.volume[{j}]: expected number, received {_jtype(val)}")
    if "indicators" in v:
        inds = v["indicators"]
        if not isinstance(inds, list):
            errs.append(f"{path}.indicators: expected array, received {_jtype(inds)}")
        else:
            for j, ind in enumerate(inds):
                if not isinstance(ind, dict):
                    errs.append(f"{path}.indicators[{j}]: expected object, received {_jtype(ind)}")
                else:
                    if "type" not in ind:
                        errs.append(f"{path}.indicators[{j}].type: required")
                    elif not isinstance(ind["type"], str):
                        errs.append(f"{path}.indicators[{j}].type: expected string, received {_jtype(ind['type'])}")
                    if "period" in ind and not isinstance(ind["period"], (int, float)):
                        errs.append(f"{path}.indicators[{j}].period: expected number, received {_jtype(ind['period'])}")


# Known chart types for the active release scope (0.0.0.1: area/column/line;
# 0.0.0.2 admits bar per DEC-014; 0.0.0.3 admits scatter per DEC-015; 0.0.0.4
# admits bubble per DEC-016; 0.0.0.5 admits combo per DEC-020;
# 0.0.0.6 admits histogram per DEC-021;
# 0.0.0.7 admits candlestick per DEC-022;
# 0.0.0.8 admits error-bar per DEC-023;
# 0.0.0.9 admits arearange per DEC-024 and columnrange per DEC-025;
# 0.0.0.10 admits waterfall per DEC-026;
# 0.0.0.11 admits bullet per DEC-027;
# 0.0.0.12 admits boxplot per DEC-028;
# 0.0.0.13 admits lollipop per DEC-029;
# 0.0.0.14 admits dumbbell per DEC-030;
# 0.0.0.15 admits funnel per DEC-031;
# 0.0.0.16 admits variwide per DEC-032;
# 0.0.0.17 admits timeline per DEC-033;
# 0.0.0.18 admits windbarb per DEC-034).
_KNOWN_TYPES = {
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
    "pie",
    "scatter",
    "solid-gauge",
    "technical-indicators",
    "timeline",
    "variwide",
    "waterfall",
    "vector-plot",
    "windbarb",
    "streamgraph",
    "xrange",
}


def validate(d: Any) -> list[str]:
    """Return a list of validation errors ([] = valid)."""
    errs: list[str] = []
    if not isinstance(d, dict):
        return [f"$: expected object, received {_jtype(d)}"]
    for k in ("type", "id", "title", "subtitle"):
        if k in d:
            _str(d[k], f"$.{k}", errs)
    if "type" in d and isinstance(d["type"], str) and d["type"] not in _KNOWN_TYPES:
        errs.append(f'$.type: unknown chart type "{d["type"]}"')
    for k in ("width", "height"):
        if k in d:
            _intnum(d[k], f"$.{k}", errs)
    for k in ("responsive", "legend", "a11y"):
        if k in d:
            _bool(d[k], f"$.{k}", errs)
    if "stacking" in d:
        _str(d["stacking"], "$.stacking", errs)
        if isinstance(d["stacking"], str) and d["stacking"] not in ("normal", "percent"):
            errs.append(f'$.stacking: expected one of "normal", "percent", received "{d["stacking"]}"')
    if "offset" in d:
        _str(d["offset"], "$.offset", errs)
        if isinstance(d["offset"], str) and d["offset"] not in ("wiggle", "silhouette"):
            errs.append(f'$.offset: expected one of "wiggle", "silhouette", received "{d["offset"]}"')
    if "vectorLength" in d:
        _num(d["vectorLength"], "$.vectorLength", errs)
    if "rotationOrigin" in d:
        _str(d["rotationOrigin"], "$.rotationOrigin", errs)
        if isinstance(d["rotationOrigin"], str) and d["rotationOrigin"] not in ("center", "start", "end"):
            errs.append(f'$.rotationOrigin: expected one of "center", "start", "end", received "{d["rotationOrigin"]}"')
    if "grouping" in d:
        _bool(d["grouping"], "$.grouping", errs)
    if "theme" in d:
        _theme(d["theme"], "$.theme", errs)
    if "layout" in d:
        _layout(d["layout"], "$.layout", errs)
    if "xAxis" in d:
        _axis(d["xAxis"], "$.xAxis", errs)
    if "yAxis" in d:
        _axis(d["yAxis"], "$.yAxis", errs)
    if "series" not in d:
        errs.append("$.series: required")
    elif not isinstance(d["series"], list):
        errs.append(f"$.series: expected array, received {_jtype(d['series'])}")
    else:
        for i, s in enumerate(d["series"]):
            _series(s, f"$.series[{i}]", errs, d.get("type"))
    if "flags" in d:
        fl = d["flags"]
        if not isinstance(fl, list):
            errs.append(f"$.flags: expected array, received {_jtype(fl)}")
        else:
            for j, f in enumerate(fl):
                if not isinstance(f, dict):
                    errs.append(f"$.flags[{j}]: expected object, received {_jtype(f)}")
                else:
                    if "x" not in f:
                        errs.append(f"$.flags[{j}].x: required")
                    elif not isinstance(f["x"], (int, float)):
                        errs.append(f"$.flags[{j}].x: expected number, received {_jtype(f['x'])}")
                    if "title" not in f:
                        errs.append(f"$.flags[{j}].title: required")
                    elif not isinstance(f["title"], str):
                        errs.append(f"$.flags[{j}].title: expected string, received {_jtype(f['title'])}")
    if "panes" in d:
        pn = d["panes"]
        if not isinstance(pn, list):
            errs.append(f"$.panes: expected array, received {_jtype(pn)}")
        else:
            for j, p in enumerate(pn):
                if not isinstance(p, dict):
                    errs.append(f"$.panes[{j}]: expected object, received {_jtype(p)}")
    for gk in ("gaugeMin", "gaugeMax"):
        if gk in d:
            _num(d[gk], f"$.{gk}", errs)
    if "gaugeBands" in d:
        gb = d["gaugeBands"]
        if not isinstance(gb, list):
            errs.append(f"$.gaugeBands: expected array, received {_jtype(gb)}")
        else:
            for j, b in enumerate(gb):
                prefix = f"$.gaugeBands[{j}]"
                if not isinstance(b, dict):
                    errs.append(f"{prefix}: expected object, received {_jtype(b)}")
                else:
                    if "from" not in b:
                        errs.append(f"{prefix}.from: required")
                    else:
                        _num(b["from"], f"{prefix}.from", errs)
                    if "to" not in b:
                        errs.append(f"{prefix}.to: required")
                    else:
                        _num(b["to"], f"{prefix}.to", errs)
                    if "color" not in b:
                        errs.append(f"{prefix}.color: required")
                    else:
                        _str(b["color"], f"{prefix}.color", errs)
    if d.get("stacking") == "percent" and isinstance(d.get("series"), list):
        for i, s in enumerate(d["series"]):
            if not isinstance(s, dict):
                continue
            if isinstance(s.get("type"), str) and s["type"] == "line":
                continue
            data = s.get("data")
            if not isinstance(data, list):
                continue
            for j, v in enumerate(data):
                _nonneg_num(v, f"$.series[{i}].data[{j}]", errs)
    if isinstance(d.get("layout"), dict) and isinstance(d["layout"].get("margin"), dict):
        m = d["layout"]["margin"]
        if isinstance(d.get("width"), (int, float)) and isinstance(d.get("height"), (int, float)):
            ya_raw = d.get("yAxis")
            xa_raw = d.get("xAxis")
            ya = ya_raw if isinstance(ya_raw, dict) else {}
            xa = xa_raw if isinstance(xa_raw, dict) else {}
            left = _num_or_default(m.get("left"), 62 if ya.get("title") else 52)
            right = _num_or_default(m.get("right"), 22)
            top = _num_or_default(m.get("top"), 20 + (26 if d.get("title") else 0) + (18 if d.get("subtitle") else 0))
            bottom = _num_or_default(
                m.get("bottom"), 46 + (18 if d.get("legend", True) else 0) + (18 if xa.get("title") else 0)
            )
            plot_w = float(d["width"]) - left - right
            plot_h = float(d["height"]) - top - bottom
            if plot_w <= 0:
                errs.append(f"$.layout.margin: plot width must remain positive, received {fmt_num(plot_w)}")
            if plot_h <= 0:
                errs.append(f"$.layout.margin: plot height must remain positive, received {fmt_num(plot_h)}")
    return errs
