package stonecharts

import (
	"math"
	"strings"
)

// Strict chart-spec validation — mirrors libs/python/stonecharts/validate.py
// byte-for-byte (same rules, same error text, same order) so both renderers accept
// and reject exactly the same specs. Runs on the generic decoded JSON (interface{})
// BEFORE unmarshaling into the typed struct; malformed values are errors here,
// never silently coerced. Defaults apply only when a property is absent.

// SpecError is returned by FromJSON when a spec fails validation.
type SpecError struct{ Errors []string }

func (e *SpecError) Error() string {
	return "invalid chart spec:\n  " + strings.Join(e.Errors, "\n  ")
}

func jtype(v interface{}) string {
	switch v.(type) {
	case nil:
		return "null"
	case bool:
		return "boolean"
	case float64:
		return "number"
	case string:
		return "string"
	case []interface{}:
		return "array"
	case map[string]interface{}:
		return "object"
	default:
		return "unknown"
	}
}

func vnum(v interface{}, path string, errs *[]string) {
	f, ok := v.(float64)
	if !ok {
		*errs = append(*errs, path+": expected number, received "+jtype(v))
		return
	}
	if math.IsNaN(f) || math.IsInf(f, 0) {
		word := "Infinity"
		if math.IsNaN(f) {
			word = "NaN"
		}
		*errs = append(*errs, path+": expected finite number, received "+word)
	}
}

func vintnum(v interface{}, path string, errs *[]string) {
	f, ok := v.(float64)
	if !ok {
		*errs = append(*errs, path+": expected integer, received "+jtype(v))
		return
	}
	if math.IsNaN(f) || math.IsInf(f, 0) {
		*errs = append(*errs, path+": expected integer, received non-finite number")
	} else if f != math.Trunc(f) {
		*errs = append(*errs, path+": expected integer, received non-integer number")
	}
}

func vstr(v interface{}, path string, errs *[]string) {
	if _, ok := v.(string); !ok {
		*errs = append(*errs, path+": expected string, received "+jtype(v))
	}
}

func vbool(v interface{}, path string, errs *[]string) {
	if _, ok := v.(bool); !ok {
		*errs = append(*errs, path+": expected boolean, received "+jtype(v))
	}
}

func vstrArray(v interface{}, path string, errs *[]string) {
	arr, ok := v.([]interface{})
	if !ok {
		*errs = append(*errs, path+": expected array, received "+jtype(v))
		return
	}
	for i, e := range arr {
		vstr(e, path+"["+itoa(i)+"]", errs)
	}
}

func itoa(i int) string {
	// small non-negative int -> string (mirrors Python's f"{i}")
	if i == 0 {
		return "0"
	}
	var b [20]byte
	p := len(b)
	for i > 0 {
		p--
		b[p] = byte('0' + i%10)
		i /= 10
	}
	return string(b[p:])
}

func has(m map[string]interface{}, k string) (interface{}, bool) {
	v, ok := m[k]
	return v, ok
}

func vgridline(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "enabled"); ok {
		vbool(x, path+".enabled", errs)
	}
	if x, ok := has(m, "color"); ok {
		vstr(x, path+".color", errs)
	}
	if x, ok := has(m, "dashStyle"); ok {
		vstr(x, path+".dashStyle", errs)
	}
}

func vaxis(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "title"); ok {
		vstr(x, path+".title", errs)
	}
	if x, ok := has(m, "categories"); ok {
		vstrArray(x, path+".categories", errs)
	}
	if x, ok := has(m, "min"); ok {
		vnum(x, path+".min", errs)
	}
	if x, ok := has(m, "max"); ok {
		vnum(x, path+".max", errs)
	}
	if x, ok := has(m, "gridLine"); ok {
		vgridline(x, path+".gridLine", errs)
	}
}

func vmarker(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "enabled"); ok {
		vbool(x, path+".enabled", errs)
	}
	if x, ok := has(m, "symbol"); ok {
		vstr(x, path+".symbol", errs)
	}
	if x, ok := has(m, "radius"); ok {
		vnum(x, path+".radius", errs)
	}
}

func vpattern(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	for _, k := range []string{"type", "color", "background"} {
		if x, ok := has(m, k); ok {
			vstr(x, path+"."+k, errs)
		}
	}
	for _, k := range []string{"size", "angle", "strokeWidth"} {
		if x, ok := has(m, k); ok {
			vnum(x, path+"."+k, errs)
		}
	}
}

func vgradient(m map[string]interface{}, path string, errs *[]string) {
	for _, k := range []string{"x1", "y1", "x2", "y2"} {
		if x, ok := has(m, k); ok {
			vnum(x, path+"."+k, errs)
		}
	}
	if x, ok := has(m, "type"); ok {
		vstr(x, path+".type", errs)
	}
	if x, ok := has(m, "stops"); ok {
		arr, ok := x.([]interface{})
		if !ok {
			*errs = append(*errs, path+".stops: expected array, received "+jtype(x))
			return
		}
		for i, st := range arr {
			sp := path + ".stops[" + itoa(i) + "]"
			sm, ok := st.(map[string]interface{})
			if !ok {
				*errs = append(*errs, sp+": expected object, received "+jtype(st))
				continue
			}
			if y, ok := has(sm, "offset"); ok {
				vnum(y, sp+".offset", errs)
			}
			if y, ok := has(sm, "color"); ok {
				vstr(y, sp+".color", errs)
			}
			if y, ok := has(sm, "opacity"); ok {
				vnum(y, sp+".opacity", errs)
			}
		}
	}
}

func vcolor(v interface{}, path string, errs *[]string) {
	switch c := v.(type) {
	case string:
		return
	case map[string]interface{}:
		vgradient(c, path, errs)
	default:
		*errs = append(*errs, path+": expected string or gradient object, received "+jtype(v))
	}
}

func vtheme(v interface{}, path string, errs *[]string) {
	if _, ok := v.(string); ok {
		return
	}
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected string or theme object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "name"); ok {
		vstr(x, path+".name", errs)
	}
	if x, ok := has(m, "background"); ok && x != nil { // background is nullable
		vstr(x, path+".background", errs)
	}
	for _, k := range []string{"titleColor", "subtitleColor", "axisLabelColor",
		"axisTitleColor", "gridColor", "axisLineColor", "crosshairColor",
		"markerHalo", "legendTextColor"} {
		if x, ok := has(m, k); ok {
			vstr(x, path+"."+k, errs)
		}
	}
	if x, ok := has(m, "palette"); ok {
		vstrArray(x, path+".palette", errs)
	}
}

func vseries(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "name"); ok {
		vstr(x, path+".name", errs)
	}
	if x, ok := has(m, "data"); !ok {
		*errs = append(*errs, path+".data: required")
	} else if arr, ok := x.([]interface{}); !ok {
		*errs = append(*errs, path+".data: expected array, received "+jtype(x))
	} else {
		for i, e := range arr {
			vnum(e, path+".data["+itoa(i)+"]", errs)
		}
	}
	if x, ok := has(m, "color"); ok {
		vcolor(x, path+".color", errs)
	}
	if x, ok := has(m, "fillOpacity"); ok {
		vnum(x, path+".fillOpacity", errs)
	}
	if x, ok := has(m, "pattern"); ok {
		vpattern(x, path+".pattern", errs)
	}
	if x, ok := has(m, "lineWidth"); ok {
		vnum(x, path+".lineWidth", errs)
	}
	for _, k := range []string{"dashStyle", "step", "curve"} {
		if x, ok := has(m, k); ok {
			vstr(x, path+"."+k, errs)
		}
	}
	if x, ok := has(m, "marker"); ok {
		vmarker(x, path+".marker", errs)
	}
}

// knownTypes — discovered from all on-disk example specs at
// charts/*/examples/*.json. Mirrors _KNOWN_TYPES in validate.py.
var knownTypes = map[string]bool{
	"area": true, "arearange": true, "bar": true, "boxplot": true,
	"bubble": true, "candlestick": true, "column": true, "columnrange": true,
	"combo": true, "dumbbell": true, "errorbar": true, "error-bar": true,
	"funnel": true, "histogram": true, "line": true, "lollipop": true,
	"scatter": true, "streamgraph": true, "technical-indicators": true,
	"timeline": true, "variwide": true, "vector-plot": true,
	"waterfall": true, "windbarb": true, "xrange": true,
}

// validate returns validation errors ([] = valid). Same order/text as validate.py.
func validate(v interface{}) []string {
	errs := []string{}
	d, ok := v.(map[string]interface{})
	if !ok {
		return []string{"$: expected object, received " + jtype(v)}
	}
	for _, k := range []string{"type", "id", "title", "subtitle"} {
		if x, ok := has(d, k); ok {
			vstr(x, "$."+k, &errs)
		}
	}
	if x, ok := has(d, "type"); ok {
		if s, ok := x.(string); ok && !knownTypes[s] {
			errs = append(errs, `$.type: unknown chart type "`+s+`"`)
		}
	}
	for _, k := range []string{"width", "height"} {
		if x, ok := has(d, k); ok {
			vintnum(x, "$."+k, &errs)
		}
	}
	for _, k := range []string{"responsive", "legend", "a11y"} {
		if x, ok := has(d, k); ok {
			vbool(x, "$."+k, &errs)
		}
	}
	if x, ok := has(d, "stacking"); ok {
		vstr(x, "$.stacking", &errs)
		if s, ok := x.(string); ok && s != "normal" && s != "percent" {
			errs = append(errs, `$.stacking: expected one of "normal", "percent", received "`+s+`"`)
		}
	}
	if x, ok := has(d, "grouping"); ok {
		vbool(x, "$.grouping", &errs)
	}
	if x, ok := has(d, "theme"); ok {
		vtheme(x, "$.theme", &errs)
	}
	if x, ok := has(d, "xAxis"); ok {
		vaxis(x, "$.xAxis", &errs)
	}
	if x, ok := has(d, "yAxis"); ok {
		vaxis(x, "$.yAxis", &errs)
	}
	if x, ok := has(d, "series"); !ok {
		errs = append(errs, "$.series: required")
	} else if arr, ok := x.([]interface{}); !ok {
		errs = append(errs, "$.series: expected array, received "+jtype(x))
	} else {
		for i, s := range arr {
			vseries(s, "$.series["+itoa(i)+"]", &errs)
		}
	}
	return errs
}
