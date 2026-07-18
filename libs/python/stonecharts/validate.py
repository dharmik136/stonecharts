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
from typing import Any, List


class SpecError(ValueError):
    """Raised when a chart spec fails validation. `.errors` lists every problem."""

    def __init__(self, errors: List[str]):
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


def _num(v: Any, path: str, errs: List[str]) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        errs.append(f"{path}: expected number, received {_jtype(v)}")
    elif isinstance(v, float) and not math.isfinite(v):
        errs.append(f"{path}: expected finite number, received "
                    + ("NaN" if math.isnan(v) else "Infinity"))


def _intnum(v: Any, path: str, errs: List[str]) -> None:
    # width/height map to Go int; require an integer-VALUED number (5 and 5.0 ok,
    # 5.7 rejected) so both languages agree. Go's interface{} can't tell 5 from 5.0.
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        errs.append(f"{path}: expected integer, received {_jtype(v)}")
    elif isinstance(v, float) and (not math.isfinite(v) or not v.is_integer()):
        errs.append(f"{path}: expected integer, received "
                    + ("non-finite number" if not math.isfinite(v) else "non-integer number"))


def _str(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, str):
        errs.append(f"{path}: expected string, received {_jtype(v)}")


def _bool(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, bool):
        errs.append(f"{path}: expected boolean, received {_jtype(v)}")


def _str_array(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, list):
        errs.append(f"{path}: expected array, received {_jtype(v)}")
        return
    for i, e in enumerate(v):
        _str(e, f"{path}[{i}]", errs)


def _gridline(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "enabled" in v:
        _bool(v["enabled"], f"{path}.enabled", errs)
    if "color" in v:
        _str(v["color"], f"{path}.color", errs)
    if "dashStyle" in v:
        _str(v["dashStyle"], f"{path}.dashStyle", errs)


def _axis(v: Any, path: str, errs: List[str]) -> None:
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


def _marker(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "enabled" in v:
        _bool(v["enabled"], f"{path}.enabled", errs)
    if "symbol" in v:
        _str(v["symbol"], f"{path}.symbol", errs)
    if "radius" in v:
        _num(v["radius"], f"{path}.radius", errs)


def _pattern(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    for k in ("type", "color", "background"):
        if k in v:
            _str(v[k], f"{path}.{k}", errs)
    for k in ("size", "angle", "strokeWidth"):
        if k in v:
            _num(v[k], f"{path}.{k}", errs)


def _gradient(v: dict, path: str, errs: List[str]) -> None:
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


def _color(v: Any, path: str, errs: List[str]) -> None:
    # oneOf: hex string OR a linear-gradient object.
    if isinstance(v, str):
        return
    if isinstance(v, dict):
        _gradient(v, path, errs)
        return
    errs.append(f"{path}: expected string or gradient object, received {_jtype(v)}")


def _theme(v: Any, path: str, errs: List[str]) -> None:
    # oneOf: theme name (string) OR a theme object.
    if isinstance(v, str):
        return
    if not isinstance(v, dict):
        errs.append(f"{path}: expected string or theme object, received {_jtype(v)}")
        return
    if "name" in v:
        _str(v["name"], f"{path}.name", errs)
    if "background" in v and v["background"] is not None:  # background is nullable
        _str(v["background"], f"{path}.background", errs)
    for k in ("titleColor", "subtitleColor", "axisLabelColor", "axisTitleColor",
              "gridColor", "axisLineColor", "crosshairColor", "markerHalo",
              "legendTextColor"):
        if k in v:
            _str(v[k], f"{path}.{k}", errs)
    if "palette" in v:
        _str_array(v["palette"], f"{path}.palette", errs)


def _series(v: Any, path: str, errs: List[str]) -> None:
    if not isinstance(v, dict):
        errs.append(f"{path}: expected object, received {_jtype(v)}")
        return
    if "name" in v:
        _str(v["name"], f"{path}.name", errs)
    if "data" not in v:
        errs.append(f"{path}.data: required")
    elif not isinstance(v["data"], list):
        errs.append(f"{path}.data: expected array, received {_jtype(v['data'])}")
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
    if "marker" in v:
        _marker(v["marker"], f"{path}.marker", errs)


# Known chart types for the active 0.0.0.1 release scope.  Keep sorted for
# readability; the set comparison is order-independent.
_KNOWN_TYPES = {
    "column",
    "line",
}


def validate(d: Any) -> List[str]:
    """Return a list of validation errors ([] = valid)."""
    errs: List[str] = []
    if not isinstance(d, dict):
        return [f"$: expected object, received {_jtype(d)}"]
    for k in ("type", "id", "title", "subtitle"):
        if k in d:
            _str(d[k], f"$.{k}", errs)
    if "type" in d:
        if isinstance(d["type"], str) and d["type"] not in _KNOWN_TYPES:
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
    if "grouping" in d:
        _bool(d["grouping"], "$.grouping", errs)
    if "theme" in d:
        _theme(d["theme"], "$.theme", errs)
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
            _series(s, f"$.series[{i}]", errs)
    return errs
