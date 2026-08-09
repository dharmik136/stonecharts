package stonecharts

import (
	"math"
	"sort"
	"strings"
)

var (
	knownThemeNames    = map[string]bool{"light": true, "dark": true}
	knownDashStyles    = map[string]bool{"solid": true, "dashed": true, "dotted": true}
	knownMarkerSymbols = map[string]bool{"circle": true, "square": true, "triangle": true, "diamond": true}
	knownStepTypes     = map[string]bool{"before": true, "after": true, "center": true}
	knownCurveTypes    = map[string]bool{"linear": true, "monotone": true}
	knownPatternTypes  = map[string]bool{"hatch": true}
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

func isHexColor(s string) bool {
	if len(s) != 4 && len(s) != 5 && len(s) != 7 && len(s) != 9 {
		return false
	}
	if len(s) == 0 || s[0] != '#' {
		return false
	}
	for _, r := range s[1:] {
		switch {
		case r >= '0' && r <= '9':
		case r >= 'a' && r <= 'f':
		case r >= 'A' && r <= 'F':
		default:
			return false
		}
	}
	return true
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
		if s, ok := x.(string); ok && !isHexColor(s) {
			*errs = append(*errs, path+".color: expected hex color, received \""+s+"\"")
		}
	}
	if x, ok := has(m, "dashStyle"); ok {
		vstr(x, path+".dashStyle", errs)
		if s, ok := x.(string); ok && !knownDashStyles[s] {
			*errs = append(*errs, path+`.dashStyle: expected one of "solid", "dashed", "dotted", received "`+s+`"`)
		}
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
	if x, ok := has(m, "binEdges"); ok {
		if arr, ok := x.([]interface{}); !ok {
			*errs = append(*errs, path+".binEdges: expected array, received "+jtype(x))
		} else {
			for i, e := range arr {
				vnum(e, path+".binEdges["+itoa(i)+"]", errs)
			}
		}
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
	if x, ok := has(m, "opposite"); ok {
		vbool(x, path+".opposite", errs)
	}
}

func vmargin(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	for _, k := range []string{"top", "right", "bottom", "left"} {
		if x, ok := has(m, k); ok {
			vnum(x, path+"."+k, errs)
			if f, ok := x.(float64); ok && f < 0 {
				*errs = append(*errs, path+"."+k+": expected non-negative number, received "+fmtNum(f))
			}
		}
	}
}

func vlayout(v interface{}, path string, errs *[]string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "margin"); ok {
		vmargin(x, path+".margin", errs)
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
		if s, ok := x.(string); ok && !knownMarkerSymbols[s] {
			*errs = append(*errs, path+`.symbol: expected one of "circle", "square", "triangle", "diamond", received "`+s+`"`)
		}
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
	if x, ok := has(m, "type"); ok {
		if s, ok := x.(string); ok && !knownPatternTypes[s] {
			*errs = append(*errs, path+`.type: expected one of "hatch", received "`+s+`"`)
		}
	}
	if x, ok := has(m, "color"); ok {
		if s, ok := x.(string); ok && !isHexColor(s) {
			*errs = append(*errs, path+".color: expected hex color, received \""+s+"\"")
		}
	}
	if x, ok := has(m, "background"); ok {
		if s, ok := x.(string); ok && !isHexColor(s) {
			*errs = append(*errs, path+".background: expected hex color, received \""+s+"\"")
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
		if s, ok := x.(string); ok && s != "linearGradient" {
			*errs = append(*errs, path+`.type: expected one of "linearGradient", received "`+s+`"`)
		}
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
				if s, ok := y.(string); ok && !isHexColor(s) {
					*errs = append(*errs, sp+".color: expected hex color, received \""+s+"\"")
				}
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
		if !isHexColor(c) {
			*errs = append(*errs, path+": expected hex color, received \""+c+"\"")
		}
		return
	case map[string]interface{}:
		vgradient(c, path, errs)
	default:
		*errs = append(*errs, path+": expected string or gradient object, received "+jtype(v))
	}
}

func vtheme(v interface{}, path string, errs *[]string) {
	if s, ok := v.(string); ok {
		if !knownThemeNames[s] {
			*errs = append(*errs, path+`: expected one of "light", "dark", received "`+s+`"`)
		}
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
			if s, ok := x.(string); ok && !isHexColor(s) {
				*errs = append(*errs, path+"."+k+": expected hex color, received \""+s+"\"")
			}
		}
	}
	if x, ok := has(m, "palette"); ok {
		vstrArray(x, path+".palette", errs)
		if arr, ok := x.([]interface{}); ok {
			for i, e := range arr {
				if s, ok := e.(string); ok && !isHexColor(s) {
					*errs = append(*errs, path+".palette["+itoa(i)+"]: expected hex color, received \""+s+"\"")
				}
			}
		}
	}
}

// vdatum validates a point-model element (scatter only, §3.3 Rank 3):
// number | [x,y] | {x,y}. Mirrors _datum in validate.py.
func vdatum(v interface{}, path string, errs *[]string) {
	switch e := v.(type) {
	case bool:
		*errs = append(*errs, path+": expected number, [x,y], or {x,y}, received boolean")
	case float64:
		vnum(v, path, errs)
	case []interface{}:
		if len(e) != 2 {
			*errs = append(*errs, path+": expected a 2-element [x,y] array, received "+itoa(len(e))+" elements")
		} else {
			vnum(e[0], path+"[0]", errs)
			vnum(e[1], path+"[1]", errs)
		}
	case map[string]interface{}:
		if x, ok := has(e, "x"); !ok {
			*errs = append(*errs, path+".x: required")
		} else {
			vnum(x, path+".x", errs)
		}
		if y, ok := has(e, "y"); !ok {
			*errs = append(*errs, path+".y: required")
		} else {
			vnum(y, path+".y", errs)
		}
		extra := []string{}
		for k := range e {
			if k != "x" && k != "y" {
				extra = append(extra, k)
			}
		}
		sort.Strings(extra)
		for _, k := range extra {
			*errs = append(*errs, path+"."+k+": unknown field")
		}
	default:
		*errs = append(*errs, path+": expected number, [x,y], or {x,y}, received "+jtype(v))
	}
}

// vdatumXYZ validates a point-model element (bubble only, §3.3 Rank 4):
// number | [x,y,z] | {x,y,z}. Mirrors _datum_xyz in validate.py.
func vdatumXYZ(v interface{}, path string, errs *[]string) {
	switch e := v.(type) {
	case bool:
		*errs = append(*errs, path+": expected number, [x,y,z], or {x,y,z}, received boolean")
	case float64:
		vnum(v, path, errs)
	case []interface{}:
		if len(e) != 3 {
			*errs = append(*errs, path+": expected a 3-element [x,y,z] array, received "+itoa(len(e))+" elements")
		} else {
			vnum(e[0], path+"[0]", errs)
			vnum(e[1], path+"[1]", errs)
			vnum(e[2], path+"[2]", errs)
		}
	case map[string]interface{}:
		for _, key := range []string{"x", "y", "z"} {
			if val, ok := has(e, key); !ok {
				*errs = append(*errs, path+"."+key+": required")
			} else {
				vnum(val, path+"."+key, errs)
			}
		}
		extra := []string{}
		for k := range e {
			if k != "x" && k != "y" && k != "z" {
				extra = append(extra, k)
			}
		}
		sort.Strings(extra)
		for _, k := range extra {
			*errs = append(*errs, path+"."+k+": unknown field")
		}
	default:
		*errs = append(*errs, path+": expected number, [x,y,z], or {x,y,z}, received "+jtype(v))
	}
}

func vseries(v interface{}, path string, errs *[]string, chartType string) {
	m, ok := v.(map[string]interface{})
	if !ok {
		*errs = append(*errs, path+": expected object, received "+jtype(v))
		return
	}
	if x, ok := has(m, "name"); ok {
		vstr(x, path+".name", errs)
	}
	if x, ok := has(m, "yAxis"); ok {
		vintnum(x, path+".yAxis", errs)
		if f, ok := x.(float64); ok && !math.IsNaN(f) && !math.IsInf(f, 0) {
			i := int(f)
			if i != 0 && i != 1 {
				*errs = append(*errs, path+`.yAxis: expected one of 0, 1, received "`+itoa(i)+`"`)
			}
		}
	}
	if x, ok := has(m, "data"); !ok && chartType != "boxplot" {
		*errs = append(*errs, path+".data: required")
	} else if !ok {
		// boxplot uses boxData instead of data
	} else if arr, ok := x.([]interface{}); !ok {
		*errs = append(*errs, path+".data: expected array, received "+jtype(x))
	} else if chartType == "scatter" {
		for i, e := range arr {
			vdatum(e, path+".data["+itoa(i)+"]", errs)
		}
	} else if chartType == "bubble" {
		for i, e := range arr {
			vdatumXYZ(e, path+".data["+itoa(i)+"]", errs)
		}
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
	if x, ok := has(m, "dashStyle"); ok {
		if s, ok := x.(string); ok && !knownDashStyles[s] {
			*errs = append(*errs, path+`.dashStyle: expected one of "solid", "dashed", "dotted", received "`+s+`"`)
		}
	}
	if x, ok := has(m, "step"); ok {
		if s, ok := x.(string); ok && !knownStepTypes[s] {
			*errs = append(*errs, path+`.step: expected one of "before", "after", "center", received "`+s+`"`)
		}
	}
	if x, ok := has(m, "curve"); ok {
		if s, ok := x.(string); ok && !knownCurveTypes[s] {
			*errs = append(*errs, path+`.curve: expected one of "linear", "monotone", received "`+s+`"`)
		}
	}
	if x, ok := has(m, "marker"); ok {
		vmarker(x, path+".marker", errs)
	}
	if x, ok := has(m, "type"); ok {
		vstr(x, path+".type", errs)
	}
}

func vnonneg(v interface{}, path string, errs *[]string) {
	f, ok := v.(float64)
	if !ok {
		return
	}
	if f < 0 {
		*errs = append(*errs, path+": expected non-negative number, received "+fmtNum(f))
	}
}

// knownTypes — active release scope (0.0.0.1: area/column/line; 0.0.0.2 admits
// bar per DEC-014; 0.0.0.3 admits scatter per DEC-015; 0.0.0.4 admits bubble
// per DEC-016; 0.0.0.5 admits combo per DEC-020; 0.0.0.6 admits histogram
// per DEC-021; 0.0.0.7 admits candlestick per DEC-022;
// 0.0.0.8 admits error-bar per DEC-023;
// 0.0.0.9 admits arearange per DEC-024 and columnrange per DEC-025;
// 0.0.0.10 admits waterfall per DEC-026;
// 0.0.0.11 admits bullet per DEC-027;
// 0.0.0.12 admits boxplot per DEC-028;
// 0.0.0.13 admits lollipop per DEC-029;
// 0.0.0.14 admits dumbbell per DEC-030).
// Mirrors _KNOWN_TYPES in validate.py.
var knownTypes = map[string]bool{
	"area":        true,
	"arearange":   true,
	"bar":         true,
	"boxplot":     true,
	"bubble":      true,
	"bullet":      true,
	"candlestick": true,
	"column":      true,
	"columnrange": true,
	"combo":       true,
	"dumbbell":    true,
	"error-bar":   true,
	"histogram":   true,
	"line":        true,
	"lollipop":    true,
	"scatter":     true,
	"waterfall":   true,
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
	if x, ok := has(d, "layout"); ok {
		vlayout(x, "$.layout", &errs)
	}
	if x, ok := has(d, "xAxis"); ok {
		vaxis(x, "$.xAxis", &errs)
	}
	if x, ok := has(d, "yAxis"); ok {
		vaxis(x, "$.yAxis", &errs)
	}
	chartType, _ := has(d, "type")
	chartTypeStr, _ := chartType.(string)
	if x, ok := has(d, "series"); !ok {
		errs = append(errs, "$.series: required")
	} else if arr, ok := x.([]interface{}); !ok {
		errs = append(errs, "$.series: expected array, received "+jtype(x))
	} else {
		for i, s := range arr {
			vseries(s, "$.series["+itoa(i)+"]", &errs, chartTypeStr)
		}
	}
	if x, ok := has(d, "stacking"); ok {
		if s, ok := x.(string); ok && s == "percent" {
			if arr, ok := has(d, "series"); ok {
				if series, ok := arr.([]interface{}); ok {
					for i, s := range series {
						m, ok := s.(map[string]interface{})
						if !ok {
							continue
						}
						if typ, ok := has(m, "type"); ok {
							if ts, ok := typ.(string); ok && ts == "line" {
								continue
							}
						}
						if data, ok := has(m, "data"); ok {
							if arr, ok := data.([]interface{}); ok {
								for j, v := range arr {
									vnonneg(v, "$.series["+itoa(i)+"].data["+itoa(j)+"]", &errs)
								}
							}
						}
					}
				}
			}
		}
	}
	if x, ok := has(d, "layout"); ok {
		if ly, ok := x.(map[string]interface{}); ok {
			left := 52.0
			if yAxis, ok := has(d, "yAxis"); ok {
				if ya, ok := yAxis.(map[string]interface{}); ok {
					if title, ok := has(ya, "title"); ok && title != "" {
						left = 62.0
					}
				}
			}
			right := 22.0
			top := 20.0
			if title, ok := has(d, "title"); ok && title != "" {
				top += 26.0
			}
			if subtitle, ok := has(d, "subtitle"); ok && subtitle != "" {
				top += 18.0
			}
			bottom := 46.0
			if legend, ok := has(d, "legend"); !ok || legend == nil || legend == true {
				bottom += 18.0
			}
			if xAxis, ok := has(d, "xAxis"); ok {
				if xa, ok := xAxis.(map[string]interface{}); ok {
					if title, ok := has(xa, "title"); ok && title != "" {
						bottom += 18.0
					}
				}
			}
			if margin, ok := has(ly, "margin"); ok {
				if m, ok := margin.(map[string]interface{}); ok {
					if v, ok := has(m, "left"); ok {
						if f, ok := v.(float64); ok {
							left = f
						}
					}
					if v, ok := has(m, "right"); ok {
						if f, ok := v.(float64); ok {
							right = f
						}
					}
					if v, ok := has(m, "top"); ok {
						if f, ok := v.(float64); ok {
							top = f
						}
					}
					if v, ok := has(m, "bottom"); ok {
						if f, ok := v.(float64); ok {
							bottom = f
						}
					}
				}
			}
			if w, ok := has(d, "width"); ok {
				if h, ok := has(d, "height"); ok {
					if wf, ok := w.(float64); ok {
						if hf, ok := h.(float64); ok {
							if wf-left-right <= 0 {
								errs = append(errs, "$.layout.margin: plot width must remain positive, received "+fmtNum(wf-left-right))
							}
							if hf-top-bottom <= 0 {
								errs = append(errs, "$.layout.margin: plot height must remain positive, received "+fmtNum(hf-top-bottom))
							}
						}
					}
				}
			}
		}
	}
	return errs
}
