package stonecharts

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"strconv"
	"strings"
	"testing"
)

// TestGolden pins the Go renderer to the shared cross-language goldens
// (charts/line-basic/golden/*.svg), which the Python renderer also matches.
// If this and the Python test both pass, the two libraries are provably in sync.
func TestGolden(t *testing.T) {
	cases := map[string][]string{
		"line-basic":   {"basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"},
		"column":       {"basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"},
		"area":         {"basic", "stacked", "percent", "themed-dark"},
		"bar":          {"basic", "grouped", "stacked", "themed-dark", "adversarial"},
		"scatter":      {"basic", "correlation", "regression", "themed-dark", "adversarial", "xy-points"},
		"bubble":       {"basic", "multi-series", "themed-dark", "uniform-z", "adversarial"},
		"combo":        {"basic", "dark", "dual-axis", "adversarial"},
		"histogram":    {"basic", "prebinned", "pareto", "themed-dark", "adversarial"},
		"candlestick":  {"basic", "ohlc", "heikin-ashi", "themed-dark", "adversarial"},
		"error-bar":    {"basic", "overlay-grouped", "asymmetric", "themed-dark", "adversarial"},
		"arearange":    {"basic", "spline-range", "themed-dark", "adversarial"},
		"columnrange":  {"basic", "grouped", "horizontal", "themed-dark", "adversarial"},
		"waterfall":    {"basic", "intermediate-sums", "profit-bridge", "themed-dark", "adversarial"},
		"boxplot":      {"basic", "outliers", "grouped", "themed-dark", "adversarial"},
		"bullet":       {"basic", "multi-kpi", "themed-dark", "adversarial"},
		"lollipop":     {"basic", "grouped", "horizontal", "themed-dark", "adversarial"},
		"dumbbell":     {"basic", "grouped", "horizontal", "themed-dark", "adversarial"},
		"funnel":       {"basic", "adversarial", "neck", "pyramid", "themed-dark"},
		"variwide":     {"basic", "adversarial", "dark", "negative"},
		"timeline":     {"basic", "multi", "vertical", "adversarial"},
		"streamgraph":  {"basic", "silhouette", "themed-dark", "adversarial"},
		"windbarb":     {"basic", "datetime", "southern-hemisphere", "themed-dark", "adversarial"},
		"vector-plot":  {"basic", "field", "themed-dark", "uniform-length", "adversarial"},
		"flame-chart":         {"basic", "multi-series", "deep-stack", "themed-dark", "adversarial"},
		"pie":                 {"basic", "many-slices", "single-slice", "themed-dark", "adversarial", "donut", "donut-single", "donut-dark", "variable-radius"},
		"gauge":               {"basic", "no-bands", "full-scale", "themed-dark", "adversarial"},
		"solid-gauge":         {"basic", "no-bands", "full-scale", "themed-dark", "adversarial"},
		"radar":               {"basic", "line-only", "single-series", "themed-dark", "adversarial"},
		"polar":               {"basic", "line-only", "single-series", "themed-dark", "adversarial"},
		"nightingale":         {"basic", "multi-series", "single-series", "themed-dark", "adversarial"},
		"parliament":          {"basic", "multi-series", "single-series", "themed-dark", "adversarial"},
		"radial-bar":          {"basic", "multi-series", "single-series", "themed-dark", "adversarial"},
		"wind-rose":           {"basic", "many-directions", "single-series", "themed-dark", "adversarial"},
		"technical-indicators": {"basic", "bollinger", "rsi-pane", "themed-dark", "adversarial"},
		"xrange":                {"trace-waterfall", "gantt", "swimlanes", "themed-dark", "adversarial"},
		"development-triangle":  {"basic", "diagonal", "factors", "annotated", "themed-dark", "rectangular-3x5", "rectangular-6x4"},
	}
	for chartDir, names := range cases {
		for _, name := range names {
			specBytes, err := os.ReadFile("../../charts/" + chartDir + "/examples/" + name + ".json")
			if err != nil {
				t.Fatal(err)
			}
			spec, err := FromJSON(specBytes)
			if err != nil {
				t.Fatal(err)
			}
			got, err := RenderSVG(spec)
			if err != nil {
				t.Fatal(err)
			}
			want, err := os.ReadFile("../../charts/" + chartDir + "/golden/" + name + ".svg")
			if err != nil {
				t.Fatal(err)
			}
			if got != string(want) {
				t.Errorf("%s/%s: SVG != golden (got %d bytes, want %d bytes)", chartDir, name, len(got), len(want))
			}
		}
	}
}

func mustSVG(t *testing.T, spec *ChartSpec) string {
	t.Helper()
	svg, err := RenderSVG(spec)
	if err != nil {
		t.Fatal(err)
	}
	return svg
}

func mustHTML(t *testing.T, spec *ChartSpec, title string) string {
	t.Helper()
	html, err := RenderHTML(spec, title)
	if err != nil {
		t.Fatal(err)
	}
	return html
}

func TestColumnEdgeCases(t *testing.T) {
	cases := []string{
		`{"type":"column","stacking":"normal","xAxis":{"categories":["mix"]},"series":[{"name":"pos","data":[10]},{"name":"neg","data":[-9]}]}`,
		`{"type":"column","layout":{"margin":{"left":90,"right":40,"top":30,"bottom":50}},"series":[{"name":"s","data":[1,2,3]}]}`,
		`{"type":"column","stacking":"percent","xAxis":{"categories":["zero","nonzero"]},"series":[{"name":"a","data":[0,2]},{"name":"b","data":[0,3]}]}`,
		`{"type":"column","xAxis":{"categories":["neg","pos"]},"series":[{"name":"a","data":[-5,10]}]}`,
		`{"type":"column","grouping":false,"series":[{"name":"a","data":[1,2]},{"name":"b","data":[2,1]}]}`,
		`{"type":"column","series":[{"name":"0","data":[1,2,3]},{"name":"1","data":[1,2,3]},{"name":"2","data":[1,2,3]},{"name":"3","data":[1,2,3]},{"name":"4","data":[1,2,3]},{"name":"5","data":[1,2,3]},{"name":"6","data":[1,2,3]},{"name":"7","data":[1,2,3]},{"name":"8","data":[1,2,3]},{"name":"9","data":[1,2,3]}]}`,
		`{"type":"column","series":[{"name":"a","data":[42]}]}`,
	}
	for _, specJSON := range cases {
		spec, err := FromJSON([]byte(specJSON))
		if err != nil {
			t.Fatal(err)
		}
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in column render for %s", specJSON)
		}
	}
}

func TestAreaEdgeCases(t *testing.T) {
	cases := []string{
		`{"type":"area","xAxis":{"categories":["a","b"]},"series":[{"name":"s","data":[1,2]}]}`,
		`{"type":"area","stacking":"normal","xAxis":{"categories":["mix"]},"series":[{"name":"pos","data":[10]},{"name":"neg","data":[-9]}]}`,
		`{"type":"area","stacking":"percent","xAxis":{"categories":["zero","nonzero"]},"series":[{"name":"a","data":[0,2]},{"name":"b","data":[0,3]}]}`,
		`{"type":"area","series":[{"name":"a","data":[42]}]}`,
	}
	for _, specJSON := range cases {
		spec, err := FromJSON([]byte(specJSON))
		if err != nil {
			t.Fatal(err)
		}
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in area render for %s", specJSON)
		}
	}
}

func TestBarEdgeCases(t *testing.T) {
	cases := []string{
		`{"type":"bar","stacking":"normal","xAxis":{"categories":["mix"]},"series":[{"name":"pos","data":[10]},{"name":"neg","data":[-9]}]}`,
		`{"type":"bar","layout":{"margin":{"left":90,"right":40,"top":30,"bottom":50}},"series":[{"name":"s","data":[1,2,3]}]}`,
		`{"type":"bar","stacking":"percent","xAxis":{"categories":["zero","nonzero"]},"series":[{"name":"a","data":[0,2]},{"name":"b","data":[0,3]}]}`,
		`{"type":"bar","xAxis":{"categories":["neg","pos"]},"series":[{"name":"a","data":[-5,10]}]}`,
		`{"type":"bar","grouping":false,"series":[{"name":"a","data":[1,2]},{"name":"b","data":[2,1]}]}`,
		`{"type":"bar","series":[{"name":"0","data":[1,2,3]},{"name":"1","data":[1,2,3]},{"name":"2","data":[1,2,3]},{"name":"3","data":[1,2,3]},{"name":"4","data":[1,2,3]},{"name":"5","data":[1,2,3]},{"name":"6","data":[1,2,3]},{"name":"7","data":[1,2,3]},{"name":"8","data":[1,2,3]},{"name":"9","data":[1,2,3]}]}`,
		`{"type":"bar","series":[{"name":"a","data":[42]}]}`,
	}
	for _, specJSON := range cases {
		spec, err := FromJSON([]byte(specJSON))
		if err != nil {
			t.Fatal(err)
		}
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in bar render for %s", specJSON)
		}
	}
}

func TestScatterEdgeCases(t *testing.T) {
	cases := []string{
		// Degenerate x-domain: every point shares the same x (xpix must pin to
		// plot center before the divide, not divide by zero).
		`{"type":"scatter","series":[{"name":"s","data":[[5,1],[5,2],[5,3]]}]}`,
		// Degenerate y-domain: every point shares the same y.
		`{"type":"scatter","series":[{"name":"s","data":[[1,5],[2,5],[3,5]]}]}`,
		// Single point (n=1 degenerate on both axes).
		`{"type":"scatter","series":[{"name":"s","data":[[7,9]]}]}`,
		// Empty series.
		`{"type":"scatter","series":[{"name":"s","data":[]}]}`,
		// Negative x and y — free domain, no zero anchor.
		`{"type":"scatter","series":[{"name":"s","data":[[-10,-20],[-5,-8],[-1,-30]]}]}`,
		// Manual xAxis/yAxis min/max clamp.
		`{"type":"scatter","xAxis":{"min":0,"max":100},"yAxis":{"min":-50,"max":50},"series":[{"name":"s","data":[[10,5],[90,-40]]}]}`,
		// Mixed element shapes within one series (bare number, positional, object).
		`{"type":"scatter","series":[{"name":"s","data":[3,[10,20],{"x":30,"y":40}]}]}`,
		// Vertical x-gridlines enabled.
		`{"type":"scatter","xAxis":{"gridLine":{"enabled":true}},"series":[{"name":"s","data":[[1,2],[3,4],[5,6]]}]}`,
		// fillOpacity explicitly 0 must still render a fully opaque point (NN#2).
		`{"type":"scatter","series":[{"name":"s","data":[[1,2]],"fillOpacity":0}]}`,
	}
	for _, specJSON := range cases {
		spec, err := FromJSON([]byte(specJSON))
		if err != nil {
			t.Fatal(err)
		}
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in scatter render for %s", specJSON)
		}
	}
}

func TestComboEdgeCases(t *testing.T) {
	cases := []string{
		// Column-only combo (all series default to column).
		`{"type":"combo","xAxis":{"categories":["a","b","c"]},"series":[{"name":"col","data":[1,2,3]}]}`,
		// Line-only combo.
		`{"type":"combo","xAxis":{"categories":["a","b"]},"series":[{"name":"ln","type":"line","data":[10,20]}]}`,
		// Mixed column + line.
		`{"type":"combo","xAxis":{"categories":["a","b","c"]},"series":[{"name":"col","type":"column","data":[5,10,15]},{"name":"ln","type":"line","data":[3,8,12]}]}`,
		// Dual y-axis.
		`{"type":"combo","xAxis":{"categories":["a","b"]},"secondaryYAxis":{"title":"Right"},"series":[{"name":"col","type":"column","data":[100,200]},{"name":"ln","type":"line","yAxis":1,"data":[0.5,0.9]}]}`,
		// Single data point.
		`{"type":"combo","xAxis":{"categories":["x"]},"series":[{"name":"col","type":"column","data":[42]},{"name":"ln","type":"line","data":[7]}]}`,
		// Many column series (band subdivision).
		`{"type":"combo","xAxis":{"categories":["a","b"]},"series":[{"name":"c0","type":"column","data":[1,2]},{"name":"c1","type":"column","data":[3,4]},{"name":"c2","type":"column","data":[5,6]},{"name":"ln","type":"line","data":[2,4]}]}`,
		// Negative values in both column and line series.
		`{"type":"combo","xAxis":{"categories":["a","b"]},"series":[{"name":"col","type":"column","data":[-5,10]},{"name":"ln","type":"line","data":[-3,7]}]}`,
		// Stacked combo columns with line overlay.
		`{"type":"combo","stacking":"normal","xAxis":{"categories":["a","b"]},"series":[{"name":"c1","type":"column","data":[10,20]},{"name":"c2","type":"column","data":[5,15]},{"name":"ln","type":"line","data":[8,18]}]}`,
		// Percent stacking combo with zero totals.
		`{"type":"combo","stacking":"percent","xAxis":{"categories":["zero","nonzero"]},"series":[{"name":"c1","type":"column","data":[0,3]},{"name":"c2","type":"column","data":[0,7]},{"name":"ln","type":"line","data":[1,5]}]}`,
	}
	for _, specJSON := range cases {
		spec, err := FromJSON([]byte(specJSON))
		if err != nil {
			t.Fatal(err)
		}
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in combo render for %s", specJSON)
		}
	}
}

func TestBubbleEdgeCases(t *testing.T) {
	cases := []string{
		// Degenerate z-domain: every point shares the same z (size_scale must
		// pin to the fixed (RMIN+RMAX)/2 before the divide, not divide by zero).
		`{"type":"bubble","series":[{"name":"s","data":[[1,1,5],[2,2,5],[3,3,5]]}]}`,
		// Single point (degenerate z-domain by construction too).
		`{"type":"bubble","series":[{"name":"s","data":[[7,9,42]]}]}`,
		// Empty series.
		`{"type":"bubble","series":[{"name":"s","data":[]}]}`,
		// Negative x/y (free domain) with z spanning a real range.
		`{"type":"bubble","series":[{"name":"s","data":[[-10,-20,1],[-5,-8,50],[-1,-30,100]]}]}`,
		// z = 0 for some points (valid lower bound, not degenerate by itself).
		`{"type":"bubble","series":[{"name":"s","data":[[1,2,0],[3,4,100]]}]}`,
		// Manual xAxis/yAxis min/max clamp.
		`{"type":"bubble","xAxis":{"min":0,"max":100},"yAxis":{"min":-50,"max":50},"series":[{"name":"s","data":[[10,5,20],[90,-40,80]]}]}`,
		// Mixed element shapes within one series (bare number, positional, object).
		`{"type":"bubble","series":[{"name":"s","data":[3,[10,20,30],{"x":40,"y":50,"z":60}]}]}`,
		// Global z-domain spans multiple series.
		`{"type":"bubble","series":[{"name":"a","data":[[1,1,1]]},{"name":"b","data":[[2,2,1000]]}]}`,
		// fillOpacity explicitly 0 must still render a fully opaque bubble (NN#2).
		`{"type":"bubble","series":[{"name":"s","data":[[1,2,3]],"fillOpacity":0}]}`,
	}
	for _, specJSON := range cases {
		spec, err := FromJSON([]byte(specJSON))
		if err != nil {
			t.Fatal(err)
		}
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in bubble render for %s", specJSON)
		}
	}
}

func TestColumnSignedStackGeometry(t *testing.T) {
	spec, err := FromJSON([]byte(`{"type":"column","stacking":"normal","xAxis":{"categories":["mix"]},"series":[{"name":"pos","data":[10]},{"name":"neg","data":[-9]}]}`))
	if err != nil {
		t.Fatal(err)
	}
	svg := mustSVG(t, spec)
	re := regexp.MustCompile(`data-series="(\d)"[^>]* y="([^"]+)"`)
	matches := re.FindAllStringSubmatch(svg, -1)
	got := map[string]float64{}
	for _, m := range matches {
		if len(m) != 3 {
			continue
		}
		f, err := strconv.ParseFloat(m[2], 64)
		if err != nil {
			t.Fatal(err)
		}
		got[m[1]] = f
	}
	if !(got["1"] > got["0"]) {
		t.Fatalf("expected negative stack segment below positive segment, got %+v", got)
	}
}

func TestLayoutMargins(t *testing.T) {
	spec, err := FromJSON([]byte(`{"type":"column","layout":{"margin":{"left":90,"right":40,"top":30,"bottom":50}},"series":[{"name":"s","data":[1,2,3]}]}`))
	if err != nil {
		t.Fatal(err)
	}
	svg := mustSVG(t, spec)
	if !strings.Contains(svg, `x1="90.0"`) {
		t.Fatalf("expected manual left margin to shift plot area, got %s", svg)
	}
}

func TestShortCategoriesPadAndUnicodeTitle(t *testing.T) {
	spec, err := FromJSON([]byte(`{"type":"column","title":"Temperature (°C)","xAxis":{"categories":["Jan","Q4 2026 - Production Operations"]},"series":[{"name":"s","data":[1,2,3]}]}`))
	if err != nil {
		t.Fatal(err)
	}
	svg := mustSVG(t, spec)
	html := mustHTML(t, spec, "")
	for _, want := range []string{
		"Temperature (°C)",
		`Jan</text>`,
		`Q4 2026 - Production Operations`,
		`>1</text>`,
		`>2</text>`,
		`<th scope="col">Jan</th>`,
		`<th scope="col">Q4 2026 - Production Operations</th>`,
		`<th scope="col">2</th>`,
	} {
		if !strings.Contains(svg, want) && !strings.Contains(html, want) {
			t.Fatalf("expected output to contain %q\nsvg=%s\nhtml=%s", want, svg, html)
		}
	}
}

// TestXSSEscaping verifies hostile strings in user-facing fields are escaped.
func TestXSSEscaping(t *testing.T) {
	x := `"><script>alert(1)</script>`
	specJSON := `{"id":` + jsonStr(x) + `,"type":"line","title":` + jsonStr(x) +
		`,"subtitle":` + jsonStr(x) + `,"theme":{"name":"light","gridColor":"#e8e8ee"` +
		`,"palette":["#2f7ed8"]},"xAxis":{"title":` + jsonStr(x) +
		`,"categories":[` + jsonStr(x) + `,"b","c"]},"yAxis":{"title":` + jsonStr(x) +
		`},"series":[{"name":` + jsonStr(x) + `,"data":[1,2,3],"color":"#2f7ed8"` +
		`,"pattern":{"type":"hatch","color":"#333333","background":"#ffffff"}` +
		`,"fillOpacity":0.3}]}`
	spec, err := FromJSON([]byte(specJSON))
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(mustSVG(t, spec), "<script>alert(1)</script>") {
		t.Error("raw <script> leaked into SVG")
	}
	if strings.Contains(mustHTML(t, spec, ""), "<script>alert(1)</script>") {
		t.Error("raw <script> leaked into HTML")
	}
	typeData := map[string]string{
		"column":  `[1,2,3]`,
		"area":    `[1,2,3]`,
		"bar":     `[1,2,3]`,
		"scatter": `[[1,2],[3,4]]`,
		"bubble":  `[[1,2,3],[4,5,6]]`,
		"combo":   `[1,2,3]`,
	}
	for ct, data := range typeData {
		cats := ""
		if ct != "scatter" && ct != "bubble" {
			cats = `,"xAxis":{"title":` + jsonStr(x) + `,"categories":[` + jsonStr(x) + `,"b","c"]}`
		} else {
			cats = `,"xAxis":{"title":` + jsonStr(x) + `}`
		}
		j := `{"type":` + jsonStr(ct) + `,"title":` + jsonStr(x) + cats +
			`,"yAxis":{"title":` + jsonStr(x) + `},"series":[{"name":` + jsonStr(x) +
			`,"data":` + data + `,"color":"#2f7ed8"}]}`
		s, err := FromJSON([]byte(j))
		if err != nil {
			t.Fatalf("XSS %s: parse error: %v", ct, err)
		}
		if strings.Contains(mustSVG(t, s), "<script>alert(1)</script>") {
			t.Errorf("raw <script> leaked into %s SVG", ct)
		}
	}
}

func jsonStr(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

// TestMalformedNoPanic feeds coercible malformed specs and asserts the renderer
// produces valid SVG (or FromJSON returns a clean error) but never panics.
func TestMalformedNoPanic(t *testing.T) {
	specs := []string{
		`{"type":"line","series":[{"name":"s","data":null}]}`,
		`{"type":"line","series":[{"name":"s","data":[1,null,3]}]}`,
		`{"type":"line","width":"auto","series":[{"name":"s","data":[1,2]}]}`,
		`{"type":"line","series":[]}`,
		`{"type":"line","series":[{"name":"s","data":[]}]}`,
	}
	for _, s := range specs {
		spec, err := FromJSON([]byte(s))
		if err != nil {
			continue // a clean error is acceptable
		}
		if svg := mustSVG(t, spec); !strings.HasPrefix(svg, "<svg") {
			t.Errorf("bad SVG for %s", s)
		}
	}
}

// TestA11yToggle verifies a11y is on by default and a11y:false restores the
// pre-a11y bytes.
func TestA11yToggle(t *testing.T) {
	mk := func() *ChartSpec {
		return &ChartSpec{Type: "line", Title: "T", Series: []Series{{Name: "s", Data: []float64{1, 2, 3}}}}
	}
	on := mk()
	on.applyDefaults()
	svgOn := mustSVG(t, on)
	if !strings.Contains(svgOn, `role="img"`) || !strings.Contains(svgOn, "<desc>") {
		t.Error("a11y default should add role=img + <desc>")
	}
	off := mk()
	no := false
	off.A11y = &no
	off.applyDefaults()
	svgOff := mustSVG(t, off)
	if strings.Contains(svgOff, `role="img"`) || strings.Contains(svgOff, "<desc>") {
		t.Error("a11y:false should omit role=img + <desc>")
	}
}

func TestFromJSONPreservesA11yFalse(t *testing.T) {
	spec, err := FromJSON([]byte(`{"type":"line","title":"T","series":[{"name":"s","data":[1,2,3]}],"a11y":false}`))
	if err != nil {
		t.Fatalf("FromJSON failed: %v", err)
	}
	if spec.A11y == nil {
		t.Fatal("FromJSON should preserve explicit a11y:false")
	}
	if *spec.A11y {
		t.Fatal("FromJSON should preserve explicit a11y:false as false")
	}
	svg := mustSVG(t, spec)
	if strings.Contains(svg, `role="img"`) || strings.Contains(svg, "<desc>") {
		t.Fatal("a11y:false from JSON should omit role=img + <desc>")
	}
}

// TestInvalidFixturesParity checks every shared invalid fixture is rejected with
// the exact expected errors — the SAME file the Python suite checks, so both
// renderers reject identically.
func TestInvalidFixturesParity(t *testing.T) {
	paths, err := filepath.Glob("../../charts/*/invalid-fixtures.json")
	if err != nil {
		t.Fatal(err)
	}
	var cases []struct {
		Spec   interface{} `json:"spec"`
		Errors []string    `json:"errors"`
	}
	for _, path := range paths {
		b, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		var fileCases []struct {
			Spec   interface{} `json:"spec"`
			Errors []string    `json:"errors"`
		}
		if err := json.Unmarshal(b, &fileCases); err != nil {
			t.Fatal(err)
		}
		cases = append(cases, fileCases...)
	}
	if len(cases) == 0 {
		t.Fatal("no invalid fixtures")
	}
	for _, c := range cases {
		got := validate(c.Spec)
		if !reflect.DeepEqual(got, c.Errors) {
			t.Errorf("spec %v:\n got  %v\n want %v", c.Spec, got, c.Errors)
		}
	}
}

func TestAllExampleSpecsValidate(t *testing.T) {
	cases := map[string][]string{
		"line-basic": {"basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"},
		"column":     {"basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"},
		"area":       {"basic", "stacked", "percent", "themed-dark"},
		"bar":        {"basic", "grouped", "stacked", "themed-dark", "adversarial"},
		"scatter":    {"basic", "correlation", "regression", "themed-dark", "adversarial", "xy-points"},
		"bubble":     {"basic", "multi-series", "themed-dark", "uniform-z", "adversarial"},
		"combo":      {"basic", "dark", "dual-axis", "adversarial"},
	}
	if len(cases) == 0 {
		t.Fatal("no active release examples")
	}
	for chartDir, names := range cases {
		for _, name := range names {
			path := "../../charts/" + chartDir + "/examples/" + name + ".json"
			b, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			var raw interface{}
			if err := json.Unmarshal(b, &raw); err != nil {
				t.Fatal(err)
			}
			if errs := validate(raw); len(errs) > 0 {
				t.Errorf("%s: %v", path, errs)
			}
		}
	}
}

// TestThemeJSONParity keeps the baked light/dark themes in lockstep with the
// canonical spec/themes/*.json (the single source of truth). If they drift, the
// two languages could theme differently.
func TestThemeJSONParity(t *testing.T) {
	for _, name := range []string{"light", "dark"} {
		b, err := os.ReadFile("../../spec/themes/" + name + ".json")
		if err != nil {
			t.Fatal(err)
		}
		var fromJSON Theme
		if err := json.Unmarshal(b, &fromJSON); err != nil {
			t.Fatal(err)
		}
		baked, _ := builtinTheme(name)
		if !reflect.DeepEqual(baked, fromJSON) {
			t.Errorf("%s theme: baked != spec/themes/%s.json\n baked=%+v\n json =%+v", name, name, baked, fromJSON)
		}
	}
}

// TestSplineEdgeCases locks in the Phase-3 QA edge-case coverage: the monotone
// spline must stay finite (no NaN/Inf) on flat data, extrema, single/dual points,
// steep jumps, negatives, and mixed extrema.
func TestSplineEdgeCases(t *testing.T) {
	cases := [][]float64{
		{10}, {10, 20}, {10, 10, 10, 10}, {10, 30, 10},
		{30, 10, 30}, {10, 10, 100, 100}, {-10, -20, -10},
		{0, 20, -10, 30, 5, 0, -5, 15},
	}
	for _, data := range cases {
		spec := &ChartSpec{Type: "line", Series: []Series{{Name: "s", Data: data, Curve: "monotone"}}}
		spec.applyDefaults()
		low := strings.ToLower(mustSVG(t, spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in spline for %v", data)
		}
	}
}

func TestResourceLimitErrors(t *testing.T) {
	cases := []struct {
		name string
		spec string
		code string
	}{
		{
			name: "series count",
			spec: `{"type":"line","series":[` + strings.TrimRight(strings.Repeat(`{"name":"s","data":[1]},`, MaxSeries+1), ",") + `]}`,
			code: "LIMIT.SERIES_COUNT",
		},
		{
			name: "points per series",
			spec: `{"type":"line","series":[{"name":"s","data":[` + strings.TrimRight(strings.Repeat("1,", MaxPointsPerSeries+1), ",") + `]}]}`,
			code: "LIMIT.POINTS_PER_SERIES",
		},
		{
			name: "label length",
			spec: `{"type":"line","title":"` + strings.Repeat("x", MaxLabelLength+1) + `","series":[{"name":"s","data":[1]}]}`,
			code: "LIMIT.LABEL_LENGTH",
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := FromJSON([]byte(tc.spec))
			if err == nil {
				t.Fatal("expected resource limit error")
			}
			if !strings.Contains(err.Error(), tc.code) {
				t.Fatalf("expected %s in %q", tc.code, err.Error())
			}
		})
	}
}

func TestSpecByteLimitError(t *testing.T) {
	_, err := FromJSON([]byte(strings.Repeat(" ", MaxSpecBytes+1)))
	if err == nil {
		t.Fatal("expected resource limit error")
	}
	if !strings.Contains(err.Error(), "LIMIT.SPEC_BYTES") {
		t.Fatalf("expected LIMIT.SPEC_BYTES in %q", err.Error())
	}
}

func TestRandomizedSpecsRenderValidSVG(t *testing.T) {
	rng := rand.New(rand.NewSource(20260803))
	chartTypes := []string{"line", "column", "area", "bar", "scatter", "bubble"}
	for _, chartType := range chartTypes {
		for caseIndex := 0; caseIndex < 8; caseIndex++ {
			spec := map[string]interface{}{
				"type":  chartType,
				"title": fmt.Sprintf("%s property %d", chartType, caseIndex),
			}
			pointCount := rng.Intn(12) + 1
			switch chartType {
			case "scatter", "bubble":
				data := make([][]float64, pointCount)
				for i := 0; i < pointCount; i++ {
					x := float64(rng.Intn(100000)-50000) / 1000
					y := float64(rng.Intn(100000)-50000) / 1000
					if chartType == "bubble" {
						data[i] = []float64{x, y, float64(rng.Intn(100000)) / 1000}
					} else {
						data[i] = []float64{x, y}
					}
				}
				spec["series"] = []map[string]interface{}{{"name": "S0", "data": data}}
			default:
				categories := make([]string, pointCount)
				for i := 0; i < pointCount; i++ {
					categories[i] = fmt.Sprintf("C%d", i)
				}
				seriesCount := rng.Intn(4) + 1
				series := make([]map[string]interface{}, seriesCount)
				for s := 0; s < seriesCount; s++ {
					data := make([]float64, pointCount)
					for i := 0; i < pointCount; i++ {
						data[i] = float64(rng.Intn(200000)-100000) / 1000
					}
					series[s] = map[string]interface{}{"name": fmt.Sprintf("S%d", s), "data": data}
				}
				spec["xAxis"] = map[string]interface{}{"categories": categories}
				spec["series"] = series
			}
			payload, err := json.Marshal(spec)
			if err != nil {
				t.Fatal(err)
			}
			parsed, err := FromJSON(payload)
			if err != nil {
				t.Fatalf("%s case %d failed parse: %v", chartType, caseIndex, err)
			}
			svg, err := RenderSVG(parsed)
			if err != nil {
				t.Fatalf("%s case %d failed render: %v", chartType, caseIndex, err)
			}
			if !strings.HasPrefix(svg, "<svg") || !strings.Contains(svg, `role="img"`) {
				t.Fatalf("%s case %d did not render a chart SVG", chartType, caseIndex)
			}
			if strings.Contains(svg, "NaN") || strings.Contains(svg, "Infinity") {
				t.Fatalf("%s case %d rendered non-finite output", chartType, caseIndex)
			}
		}
	}
	for caseIndex := 0; caseIndex < 8; caseIndex++ {
		pointCount := rng.Intn(12) + 1
		colCount := rng.Intn(3) + 1
		lineCount := rng.Intn(2) + 1
		categories := make([]string, pointCount)
		for i := 0; i < pointCount; i++ {
			categories[i] = fmt.Sprintf("C%d", i)
		}
		series := make([]map[string]interface{}, 0, colCount+lineCount)
		for s := 0; s < colCount; s++ {
			data := make([]float64, pointCount)
			for i := 0; i < pointCount; i++ {
				data[i] = float64(rng.Intn(200000)-100000) / 1000
			}
			series = append(series, map[string]interface{}{"name": fmt.Sprintf("Col%d", s), "type": "column", "data": data})
		}
		for s := 0; s < lineCount; s++ {
			data := make([]float64, pointCount)
			for i := 0; i < pointCount; i++ {
				data[i] = float64(rng.Intn(200000)-100000) / 1000
			}
			series = append(series, map[string]interface{}{"name": fmt.Sprintf("Line%d", s), "type": "line", "data": data})
		}
		spec := map[string]interface{}{
			"type":   "combo",
			"title":  fmt.Sprintf("combo property %d", caseIndex),
			"xAxis":  map[string]interface{}{"categories": categories},
			"series": series,
		}
		payload, err := json.Marshal(spec)
		if err != nil {
			t.Fatal(err)
		}
		parsed, err := FromJSON(payload)
		if err != nil {
			t.Fatalf("combo case %d failed parse: %v", caseIndex, err)
		}
		svg, err := RenderSVG(parsed)
		if err != nil {
			t.Fatalf("combo case %d failed render: %v", caseIndex, err)
		}
		if !strings.HasPrefix(svg, "<svg") || !strings.Contains(svg, `role="img"`) {
			t.Fatalf("combo case %d did not render a chart SVG", caseIndex)
		}
		if strings.Contains(svg, "NaN") || strings.Contains(svg, "Infinity") {
			t.Fatalf("combo case %d rendered non-finite output", caseIndex)
		}
	}
}

// TestRandomizedAll36Types extends property coverage to all chart types (DEC-051).
func TestRandomizedAll36Types(t *testing.T) {
	rng := rand.New(rand.NewSource(20260810))
	validate := func(t *testing.T, label string, specJSON []byte) {
		t.Helper()
		parsed, err := FromJSON(specJSON)
		if err != nil {
			t.Fatalf("%s parse: %v", label, err)
		}
		svg, err := RenderSVG(parsed)
		if err != nil {
			t.Fatalf("%s render: %v", label, err)
		}
		if !strings.HasPrefix(svg, "<svg") || !strings.Contains(svg, `role="img"`) {
			t.Fatalf("%s: not a valid chart SVG", label)
		}
		if strings.Contains(svg, "NaN") || strings.Contains(svg, "Infinity") {
			t.Fatalf("%s: non-finite output", label)
		}
		svg2, _ := RenderSVG(parsed)
		if svg != svg2 {
			t.Fatalf("%s: non-deterministic render", label)
		}
	}

	randData := func(n int) string {
		vals := make([]string, n)
		for i := range vals {
			vals[i] = fmt.Sprintf("%.3f", float64(rng.Intn(200000)-100000)/1000)
		}
		return "[" + strings.Join(vals, ",") + "]"
	}
	posData := func(n int) string {
		vals := make([]string, n)
		for i := range vals {
			vals[i] = fmt.Sprintf("%.2f", float64(rng.Intn(9900)+100)/100)
		}
		return "[" + strings.Join(vals, ",") + "]"
	}
	cats := func(n int, prefix string) string {
		cs := make([]string, n)
		for i := range cs {
			cs[i] = fmt.Sprintf(`"%s%d"`, prefix, i)
		}
		return "[" + strings.Join(cs, ",") + "]"
	}

	// Category-value family
	for _, ct := range []string{"lollipop", "nightingale", "radial-bar"} {
		for c := 0; c < 8; c++ {
			pts := rng.Intn(10) + 2
			sc := rng.Intn(3) + 1
			series := make([]string, sc)
			for s := range series {
				series[s] = fmt.Sprintf(`{"name":"S%d","data":%s}`, s, randData(pts))
			}
			j := fmt.Sprintf(`{"type":"%s","xAxis":{"categories":%s},"series":[%s]}`,
				ct, cats(pts, "C"), strings.Join(series, ","))
			validate(t, fmt.Sprintf("%s/%d", ct, c), []byte(j))
		}
	}

	// Streamgraph (positive values — represents flow volumes)
	for c := 0; c < 8; c++ {
		pts := rng.Intn(8) + 3
		sc := rng.Intn(2) + 2
		series := make([]string, sc)
		for s := range series {
			series[s] = fmt.Sprintf(`{"name":"S%d","data":%s}`, s, posData(pts))
		}
		j := fmt.Sprintf(`{"type":"streamgraph","xAxis":{"categories":%s},"series":[%s]}`,
			cats(pts, "C"), strings.Join(series, ","))
		validate(t, fmt.Sprintf("streamgraph/%d", c), []byte(j))
	}

	// Variwide
	for c := 0; c < 8; c++ {
		pts := rng.Intn(6) + 2
		j := fmt.Sprintf(`{"type":"variwide","xAxis":{"categories":%s},"series":[{"name":"S0","data":%s,"widths":%s}]}`,
			cats(pts, "C"), randData(pts), posData(pts))
		validate(t, fmt.Sprintf("variwide/%d", c), []byte(j))
	}

	// Windbarb
	for c := 0; c < 8; c++ {
		pts := rng.Intn(10) + 2
		dir := make([]string, pts)
		spd := make([]string, pts)
		for i := range dir {
			dir[i] = fmt.Sprintf("%.1f", float64(rng.Intn(3600))/10)
			spd[i] = fmt.Sprintf("%.1f", float64(rng.Intn(400))/10)
		}
		j := fmt.Sprintf(`{"type":"windbarb","xAxis":{"categories":%s},"series":[{"name":"S0","data":[%s],"direction":[%s]}]}`,
			cats(pts, "T"), strings.Join(spd, ","), strings.Join(dir, ","))
		validate(t, fmt.Sprintf("windbarb/%d", c), []byte(j))
	}

	// Range family
	for _, ct := range []string{"arearange", "columnrange", "error-bar", "dumbbell"} {
		for c := 0; c < 8; c++ {
			pts := rng.Intn(6) + 2
			dv := make([]string, pts)
			lo := make([]string, pts)
			hi := make([]string, pts)
			for i := range dv {
				center := float64(rng.Intn(8000)+1000) / 100
				spread := float64(rng.Intn(1900)+100) / 100
				dv[i] = fmt.Sprintf("%.2f", center)
				lo[i] = fmt.Sprintf("%.2f", center-spread)
				hi[i] = fmt.Sprintf("%.2f", center+spread)
			}
			j := fmt.Sprintf(`{"type":"%s","xAxis":{"categories":%s},"series":[{"name":"S0","data":[%s],"low":[%s],"high":[%s]}]}`,
				ct, cats(pts, "C"), strings.Join(dv, ","), strings.Join(lo, ","), strings.Join(hi, ","))
			validate(t, fmt.Sprintf("%s/%d", ct, c), []byte(j))
		}
	}

	// Boxplot
	for c := 0; c < 8; c++ {
		pts := rng.Intn(4) + 2
		boxes := make([]string, pts)
		medians := make([]string, pts)
		for i := range boxes {
			vs := make([]float64, 5)
			for j := range vs {
				vs[j] = float64(rng.Intn(10000)) / 100
			}
			// sort
			for a := 0; a < 5; a++ {
				for b := a + 1; b < 5; b++ {
					if vs[a] > vs[b] {
						vs[a], vs[b] = vs[b], vs[a]
					}
				}
			}
			boxes[i] = fmt.Sprintf(`{"low":%.2f,"q1":%.2f,"median":%.2f,"q3":%.2f,"high":%.2f}`,
				vs[0], vs[1], vs[2], vs[3], vs[4])
			medians[i] = fmt.Sprintf("%.2f", vs[2])
		}
		j := fmt.Sprintf(`{"type":"boxplot","xAxis":{"categories":%s},"series":[{"name":"S0","data":[%s],"boxData":[%s]}]}`,
			cats(pts, "C"), strings.Join(medians, ","), strings.Join(boxes, ","))
		validate(t, fmt.Sprintf("boxplot/%d", c), []byte(j))
	}

	// Candlestick
	for c := 0; c < 8; c++ {
		pts := rng.Intn(10) + 2
		ohlc := make([]string, pts)
		closes := make([]string, pts)
		for i := range ohlc {
			o := float64(rng.Intn(10000)+5000) / 100
			cl := float64(rng.Intn(10000)+5000) / 100
			hi := o
			if cl > hi {
				hi = cl
			}
			hi += float64(rng.Intn(1000)+1) / 100
			lo := o
			if cl < lo {
				lo = cl
			}
			lo -= float64(rng.Intn(1000)+1) / 100
			ohlc[i] = fmt.Sprintf(`{"open":%.2f,"high":%.2f,"low":%.2f,"close":%.2f}`, o, hi, lo, cl)
			closes[i] = fmt.Sprintf("%.2f", cl)
		}
		j := fmt.Sprintf(`{"type":"candlestick","xAxis":{"categories":%s},"series":[{"name":"S0","data":[%s],"ohlc":[%s]}]}`,
			cats(pts, "D"), strings.Join(closes, ","), strings.Join(ohlc, ","))
		validate(t, fmt.Sprintf("candlestick/%d", c), []byte(j))
	}

	// Histogram
	for c := 0; c < 8; c++ {
		n := rng.Intn(40) + 10
		vals := make([]string, n)
		for i := range vals {
			vals[i] = fmt.Sprintf("%.2f", float64(rng.Intn(10000))/100)
		}
		j := fmt.Sprintf(`{"type":"histogram","outOfRange":"clip","series":[{"name":"S0","data":[%s]}]}`,
			strings.Join(vals, ","))
		validate(t, fmt.Sprintf("histogram/%d", c), []byte(j))
	}

	// Xrange
	for c := 0; c < 8; c++ {
		lanes := rng.Intn(3) + 1
		nSpans := rng.Intn(6) + 2
		spans := make([]string, nSpans)
		for i := range spans {
			x := float64(rng.Intn(800)) / 10
			x2 := x + float64(rng.Intn(200)+10)/10
			y := rng.Intn(lanes)
			spans[i] = fmt.Sprintf(`{"x":%.1f,"x2":%.1f,"y":%d}`, x, x2, y)
		}
		j := fmt.Sprintf(`{"type":"xrange","yAxis":{"categories":%s},"series":[{"name":"S0","data":[],"spans":[%s]}]}`,
			cats(lanes, "Lane"), strings.Join(spans, ","))
		validate(t, fmt.Sprintf("xrange/%d", c), []byte(j))
	}

	// Flame-chart
	for c := 0; c < 8; c++ {
		nFrames := rng.Intn(10) + 2
		frames := make([]string, nFrames)
		for i := range frames {
			x := float64(rng.Intn(800)) / 10
			x2 := x + float64(rng.Intn(200)+5)/10
			depth := rng.Intn(5)
			frames[i] = fmt.Sprintf(`{"x":%.1f,"x2":%.1f,"depth":%d,"name":"fn%d"}`, x, x2, depth, rng.Intn(100))
		}
		j := fmt.Sprintf(`{"type":"flame-chart","series":[{"name":"S0","data":[],"frames":[%s]}]}`,
			strings.Join(frames, ","))
		validate(t, fmt.Sprintf("flame-chart/%d", c), []byte(j))
	}

	// Bullet
	for c := 0; c < 8; c++ {
		val := float64(rng.Intn(800)+100) / 10
		target := float64(rng.Intn(500)+500) / 10
		r1 := float64(rng.Intn(400)+200) / 10
		r2 := r1 + float64(rng.Intn(200)+100)/10
		r3 := r2 + float64(rng.Intn(200)+100)/10
		j := fmt.Sprintf(`{"type":"bullet","bulletTarget":%.1f,"bulletRanges":[%.1f,%.1f,%.1f],"series":[{"name":"S0","data":[%.1f]}]}`,
			target, r1, r2, r3, val)
		validate(t, fmt.Sprintf("bullet/%d", c), []byte(j))
	}

	// Technical-indicators
	for c := 0; c < 8; c++ {
		pts := rng.Intn(20) + 10
		vals := make([]string, pts)
		for i := range vals {
			vals[i] = fmt.Sprintf("%.2f", float64(rng.Intn(10000)+5000)/100)
		}
		period := 5
		if pts < 5 {
			period = pts
		}
		j := fmt.Sprintf(`{"type":"technical-indicators","series":[{"name":"S0","type":"line","data":[%s],"indicators":[{"type":"sma","period":%d}]}]}`,
			strings.Join(vals, ","), period)
		validate(t, fmt.Sprintf("technical-indicators/%d", c), []byte(j))
	}

	// Pie
	for c := 0; c < 8; c++ {
		pts := rng.Intn(6) + 2
		j := fmt.Sprintf(`{"type":"pie","xAxis":{"categories":%s},"series":[{"name":"S0","data":%s}]}`,
			cats(pts, "Slice"), posData(pts))
		validate(t, fmt.Sprintf("pie/%d", c), []byte(j))
	}

	// Gauge / solid-gauge
	for _, ct := range []string{"gauge", "solid-gauge"} {
		for c := 0; c < 8; c++ {
			lo := float64(rng.Intn(300)) / 10
			hi := lo + float64(rng.Intn(1000)+200)/10
			val := lo + float64(rng.Intn(int(hi-lo)*10+1))/10
			j := fmt.Sprintf(`{"type":"%s","gaugeMin":%.1f,"gaugeMax":%.1f,"series":[{"name":"S0","data":[%.1f]}]}`,
				ct, lo, hi, val)
			validate(t, fmt.Sprintf("%s/%d", ct, c), []byte(j))
		}
	}

	// Parliament
	for c := 0; c < 8; c++ {
		pts := rng.Intn(6) + 2
		j := fmt.Sprintf(`{"type":"parliament","xAxis":{"categories":%s},"series":[{"name":"S0","data":%s}]}`,
			cats(pts, "Party"), posData(pts))
		validate(t, fmt.Sprintf("parliament/%d", c), []byte(j))
	}

	// Radar / polar
	for _, ct := range []string{"radar", "polar"} {
		for c := 0; c < 8; c++ {
			pts := rng.Intn(5) + 3
			sc := rng.Intn(2) + 1
			series := make([]string, sc)
			for s := range series {
				series[s] = fmt.Sprintf(`{"name":"S%d","data":%s}`, s, posData(pts))
			}
			j := fmt.Sprintf(`{"type":"%s","xAxis":{"categories":%s},"series":[%s]}`,
				ct, cats(pts, "Ax"), strings.Join(series, ","))
			validate(t, fmt.Sprintf("%s/%d", ct, c), []byte(j))
		}
	}

	// Wind-rose
	for c := 0; c < 8; c++ {
		pts := rng.Intn(12) + 4
		sc := rng.Intn(2) + 1
		series := make([]string, sc)
		for s := range series {
			series[s] = fmt.Sprintf(`{"name":"S%d","data":%s}`, s, posData(pts))
		}
		j := fmt.Sprintf(`{"type":"wind-rose","xAxis":{"categories":%s},"series":[%s]}`,
			cats(pts, "Dir"), strings.Join(series, ","))
		validate(t, fmt.Sprintf("wind-rose/%d", c), []byte(j))
	}

	// Waterfall
	for c := 0; c < 8; c++ {
		pts := rng.Intn(6) + 2
		j := fmt.Sprintf(`{"type":"waterfall","xAxis":{"categories":%s},"series":[{"name":"S0","data":%s}]}`,
			cats(pts, "Step"), randData(pts))
		validate(t, fmt.Sprintf("waterfall/%d", c), []byte(j))
	}

	// Funnel
	for c := 0; c < 8; c++ {
		pts := rng.Intn(4) + 2
		j := fmt.Sprintf(`{"type":"funnel","xAxis":{"categories":%s},"series":[{"name":"S0","data":%s}]}`,
			cats(pts, "Stage"), posData(pts))
		validate(t, fmt.Sprintf("funnel/%d", c), []byte(j))
	}

	// Timeline
	for c := 0; c < 8; c++ {
		n := rng.Intn(5) + 1
		vals := make([]string, n)
		labels := make([]string, n)
		for i := range vals {
			vals[i] = fmt.Sprintf("%.0f", float64(rng.Intn(8000)+1000))
			labels[i] = fmt.Sprintf(`"Evt%d"`, i)
		}
		j := fmt.Sprintf(`{"type":"timeline","series":[{"name":"S0","data":[%s],"labels":[%s]}]}`,
			strings.Join(vals, ","), strings.Join(labels, ","))
		validate(t, fmt.Sprintf("timeline/%d", c), []byte(j))
	}

	// Vector-plot
	for c := 0; c < 8; c++ {
		n := rng.Intn(10) + 2
		xs := make([]string, n)
		ys := make([]string, n)
		dirs := make([]string, n)
		lens := make([]string, n)
		for i := range xs {
			xs[i] = fmt.Sprintf("%.1f", float64(rng.Intn(1000))/10)
			ys[i] = fmt.Sprintf("%.1f", float64(rng.Intn(1000))/10)
			dirs[i] = fmt.Sprintf("%.1f", float64(rng.Intn(3600))/10)
			lens[i] = fmt.Sprintf("%.1f", float64(rng.Intn(500))/10)
		}
		j := fmt.Sprintf(`{"type":"vector-plot","series":[{"name":"S0","x":[%s],"data":[%s],"direction":[%s],"length":[%s]}]}`,
			strings.Join(xs, ","), strings.Join(ys, ","), strings.Join(dirs, ","), strings.Join(lens, ","))
		validate(t, fmt.Sprintf("vector-plot/%d", c), []byte(j))
	}

	// Development-triangle
	for c := 0; c < 8; c++ {
		nOrigins := rng.Intn(7) + 1
		nPeriods := rng.Intn(7) + 1

		// Build strictly increasing non-negative periods
		periodSet := map[int]bool{}
		for len(periodSet) < nPeriods {
			periodSet[rng.Intn(120)] = true
		}
		periodSlice := make([]int, 0, nPeriods)
		for p := range periodSet {
			periodSlice = append(periodSlice, p)
		}
		// sort
		for a := 0; a < len(periodSlice); a++ {
			for b := a + 1; b < len(periodSlice); b++ {
				if periodSlice[a] > periodSlice[b] {
					periodSlice[a], periodSlice[b] = periodSlice[b], periodSlice[a]
				}
			}
		}

		origins := make([]string, nOrigins)
		for i := range origins {
			origins[i] = fmt.Sprintf(`"Y%d"`, 2020+i)
		}
		periodsJSON := make([]string, nPeriods)
		for i, p := range periodSlice {
			periodsJSON[i] = strconv.Itoa(p)
		}

		// Build triangle rows with non-increasing lengths
		jagged := rng.Intn(2) == 0
		maxCols := nPeriods
		rows := make([]string, nOrigins)
		for r := 0; r < nOrigins; r++ {
			rowLen := maxCols
			if jagged {
				rowLen = maxCols - r
				if rowLen < 1 {
					rowLen = 1
				}
			}
			if rowLen > nPeriods {
				rowLen = nPeriods
			}
			vals := make([]string, rowLen)
			for i := range vals {
				choice := rng.Intn(3)
				switch choice {
				case 0:
					vals[i] = fmt.Sprintf("%.2f", float64(rng.Intn(50000)+100)/100)
				case 1:
					vals[i] = "0"
				default:
					vals[i] = fmt.Sprintf("%.2f", -float64(rng.Intn(20000)+100)/100)
				}
			}
			rows[r] = "[" + strings.Join(vals, ",") + "]"
			if jagged {
				maxCols = rowLen
			}
		}

		triJSON := fmt.Sprintf(`"origins":[%s],"periods":[%s],"values":[%s]`,
			strings.Join(origins, ","), strings.Join(periodsJSON, ","), strings.Join(rows, ","))

		// Optionally add view/valueType/unit
		extras := ""
		if rng.Intn(2) == 0 {
			views := []string{"cumulative", "incremental"}
			extras += fmt.Sprintf(`,"view":"%s"`, views[rng.Intn(2)])
		}
		if rng.Intn(2) == 0 {
			vtypes := []string{"paid", "incurred"}
			extras += fmt.Sprintf(`,"valueType":"%s"`, vtypes[rng.Intn(2)])
		}
		if rng.Intn(2) == 0 {
			extras += fmt.Sprintf(`,"unit":"USD-%d"`, c)
		}

		spec := fmt.Sprintf(`{"type":"development-triangle","triangle":{%s%s}`, triJSON, extras)

		// Optionally add diagonal
		if rng.Intn(2) == 0 {
			spec += `,"diagonal":{"highlight":true}`
		}
		// Optionally add colorScale
		if rng.Intn(2) == 0 {
			spec += `,"colorScale":{"type":"sequential","domain":"auto"}`
		}
		// Optionally add factors
		if rng.Intn(2) == 0 && nPeriods >= 2 {
			fvals := make([]string, nPeriods-1)
			for i := range fvals {
				fvals[i] = fmt.Sprintf("%.3f", float64(rng.Intn(3000)+500)/1000)
			}
			spec += fmt.Sprintf(`,"factors":{"show":true,"values":[%s]}`, strings.Join(fvals, ","))
		}
		spec += "}"

		validate(t, fmt.Sprintf("development-triangle/%d", c), []byte(spec))
	}
}

func TestCapabilityManifestAndError(t *testing.T) {
	caps := Capabilities()
	if caps.SpecVersion != "0.0.0.1" || caps.SVGContractVersion != "0.0.0.1" {
		t.Fatalf("unexpected manifest versions: %+v", caps)
	}
	if got, want := caps.ChartTypeNames(), []string{"area", "arearange", "bar", "boxplot", "bubble", "bullet", "candlestick", "column", "columnrange", "combo", "development-triangle", "dumbbell", "error-bar", "flame-chart", "funnel", "gauge", "histogram", "line", "lollipop", "nightingale", "parliament", "pie", "polar", "radar", "radial-bar", "scatter", "solid-gauge", "streamgraph", "technical-indicators", "timeline", "variwide", "vector-plot", "waterfall", "wind-rose", "windbarb", "xrange"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("manifest chartTypes mismatch: got %v want %v", got, want)
	}
	if tier := caps.ChartTypes["line"].Tier; tier != "certified" {
		t.Fatalf("expected line tier=certified, got %q", tier)
	}
	if tier := caps.ChartTypes["waterfall"].Tier; tier != "candidate" {
		t.Fatalf("expected waterfall tier=candidate, got %q", tier)
	}
	if tier := caps.ChartTypes["parliament"].Tier; tier != "experimental" {
		t.Fatalf("expected parliament tier=experimental, got %q", tier)
	}
	spec := &ChartSpec{Type: "column", Series: []Series{{Name: "s", Data: []float64{1}}}}
	if svg, err := RenderSVG(spec); err != nil {
		t.Fatalf("expected column to render, got %v", err)
	} else if !strings.HasPrefix(svg, "<svg") {
		t.Fatalf("expected SVG output for column, got %q", svg[:min(len(svg), 64)])
	}
	bad := &ChartSpec{Type: "heatmap", Series: []Series{{Name: "s", Data: []float64{1}}}}
	if _, err := RenderSVG(bad); err == nil {
		t.Fatal("expected capability error")
	} else {
		ce, ok := err.(*CapabilityError)
		if !ok {
			t.Fatalf("expected *CapabilityError, got %T", err)
		}
		if ce.Code != "E_CAPABILITY" || ce.Path != "$.type" {
			t.Fatalf("unexpected capability error: %+v", ce)
		}
		if ce.Message != `unsupported chart type "heatmap"` {
			t.Fatalf("unexpected capability message: %+v", ce)
		}
	}
}

func TestSaveHTML(t *testing.T) {
	spec, err := FromJSON([]byte(`{"type":"line","xAxis":{"categories":["a","b"]},"series":[{"name":"s","data":[1,2]}]}`))
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "test.html")
	if err := SaveHTML(spec, path, "Test Page"); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	html := string(data)
	if !strings.Contains(html, "<title>Test Page</title>") {
		t.Error("expected page title in HTML output")
	}
	if !strings.Contains(html, "<svg") {
		t.Error("expected SVG in HTML output")
	}
}

func TestRenderHTMLPointModelDataTable(t *testing.T) {
	cases := []struct {
		name    string
		specJSON string
		wantCol  string
	}{
		{
			"scatter",
			`{"type":"scatter","series":[{"name":"pts","data":[[1,2],[3,4]]}]}`,
			"</th><td>",
		},
		{
			"bubble",
			`{"type":"bubble","series":[{"name":"pts","data":[[1,2,5],[3,4,10]]}]}`,
			`<th scope="col">Z</th>`,
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			spec, err := FromJSON([]byte(tc.specJSON))
			if err != nil {
				t.Fatal(err)
			}
			html := mustHTML(t, spec, "test")
			if !strings.Contains(html, `class="sc-visually-hidden"`) {
				t.Error("expected accessible data table in HTML")
			}
			if !strings.Contains(html, tc.wantCol) {
				t.Errorf("expected %q in data table", tc.wantCol)
			}
		})
	}
}

func TestErrorMethods(t *testing.T) {
	ce := &CapabilityError{Code: "E_CAPABILITY", Message: "test cap", Path: "$.type"}
	if got := ce.Error(); got != "$.type: test cap" {
		t.Errorf("CapabilityError.Error() = %q, want %q", got, "$.type: test cap")
	}
	ceNoPath := &CapabilityError{Code: "E_CAPABILITY", Message: "no path"}
	if got := ceNoPath.Error(); got != "no path" {
		t.Errorf("CapabilityError.Error() without path = %q, want %q", got, "no path")
	}
	var ceNil *CapabilityError
	if got := ceNil.Error(); got != "" {
		t.Errorf("nil CapabilityError.Error() = %q, want empty", got)
	}
	se := &SpecError{Errors: []string{"bad field"}}
	if got := se.Error(); !strings.Contains(got, "bad field") {
		t.Errorf("SpecError.Error() = %q, expected to contain 'bad field'", got)
	}
	rle := &ResourceLimitError{Code: "LIMIT.TEST", Path: "$.x", Limit: 10, Received: 20}
	if got := rle.Error(); !strings.Contains(got, "LIMIT.TEST") {
		t.Errorf("ResourceLimitError.Error() = %q, expected to contain code", got)
	}
}

func FuzzFromJSON(f *testing.F) {
	seeds := []struct {
		dir  string
		name string
	}{
		{"line-basic", "basic"},
		{"line-basic", "adversarial"},
		{"column", "basic"},
		{"column", "stacked"},
		{"area", "basic"},
		{"bar", "basic"},
		{"scatter", "basic"},
		{"bubble", "basic"},
		{"combo", "basic"},
		{"combo", "dual-axis"},
		{"lollipop", "basic"},
		{"variwide", "basic"},
		{"streamgraph", "basic"},
		{"windbarb", "basic"},
		{"nightingale", "basic"},
		{"radial-bar", "basic"},
		{"arearange", "basic"},
		{"columnrange", "basic"},
		{"error-bar", "basic"},
		{"dumbbell", "basic"},
		{"boxplot", "basic"},
		{"candlestick", "basic"},
		{"histogram", "basic"},
		{"xrange", "trace-waterfall"},
		{"flame-chart", "basic"},
		{"bullet", "basic"},
		{"technical-indicators", "basic"},
		{"pie", "basic"},
		{"gauge", "basic"},
		{"solid-gauge", "basic"},
		{"parliament", "basic"},
		{"radar", "basic"},
		{"polar", "basic"},
		{"wind-rose", "basic"},
		{"waterfall", "basic"},
		{"funnel", "basic"},
		{"timeline", "basic"},
		{"vector-plot", "basic"},
		{"development-triangle", "basic"},
		{"development-triangle", "diagonal"},
		{"development-triangle", "factors"},
		{"development-triangle", "annotated"},
		{"development-triangle", "themed-dark"},
		{"development-triangle", "rectangular-3x5"},
		{"development-triangle", "rectangular-6x4"},
	}
	for _, s := range seeds {
		data, err := os.ReadFile("../../charts/" + s.dir + "/examples/" + s.name + ".json")
		if err != nil {
			f.Fatal(err)
		}
		f.Add(data)
	}
	// Inline development-triangle seeds for shapes not covered by example files
	// Rectangular 3x5 (all rows same length)
	f.Add([]byte(`{"type":"development-triangle","triangle":{"origins":["2021","2022","2023"],"periods":[12,24,36,48,60],"values":[[100,150,170,180,185],[110,160,175,190,195],[120,170,185,200,210]]}}`))
	// Adversarial minimal 1x1
	f.Add([]byte(`{"type":"development-triangle","triangle":{"origins":["2025"],"periods":[0],"values":[[0]]}}`))
	f.Fuzz(func(t *testing.T, data []byte) {
		spec, err := FromJSON(data)
		if err != nil {
			return
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			return
		}
		if strings.Contains(svg, "NaN") || strings.Contains(svg, "+Inf") || strings.Contains(svg, "-Inf") {
			t.Errorf("NaN/Inf in fuzz render output")
		}
	})
}

func loadBenchSpec(b *testing.B, chartDir, name string) *ChartSpec {
	b.Helper()
	data, err := os.ReadFile("../../charts/" + chartDir + "/examples/" + name + ".json")
	if err != nil {
		b.Fatal(err)
	}
	spec, err := FromJSON(data)
	if err != nil {
		b.Fatal(err)
	}
	return spec
}

func BenchmarkRender(b *testing.B) {
	cases := []struct {
		dir  string
		name string
	}{
		{"line-basic", "basic"},
		{"column", "basic"},
		{"area", "basic"},
		{"bar", "basic"},
		{"scatter", "basic"},
		{"bubble", "basic"},
		{"combo", "basic"},
	}
	for _, tc := range cases {
		spec := loadBenchSpec(b, tc.dir, tc.name)
		b.Run(tc.dir, func(b *testing.B) {
			for i := 0; i < b.N; i++ {
				if _, err := RenderSVG(spec); err != nil {
					b.Fatal(err)
				}
			}
		})
	}
}

func BenchmarkRenderComplex(b *testing.B) {
	cases := []struct {
		dir  string
		name string
	}{
		{"line-basic", "gradient"},
		{"column", "stacked"},
		{"area", "stacked"},
		{"bar", "stacked"},
		{"scatter", "correlation"},
		{"bubble", "multi-series"},
		{"combo", "dual-axis"},
	}
	for _, tc := range cases {
		spec := loadBenchSpec(b, tc.dir, tc.name)
		b.Run(tc.dir, func(b *testing.B) {
			for i := 0; i < b.N; i++ {
				if _, err := RenderSVG(spec); err != nil {
					b.Fatal(err)
				}
			}
		})
	}
}

func BenchmarkFromJSON(b *testing.B) {
	data, err := os.ReadFile("../../charts/combo/examples/dual-axis.json")
	if err != nil {
		b.Fatal(err)
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if _, err := FromJSON(data); err != nil {
			b.Fatal(err)
		}
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// TestRendererPurity verifies that RenderSVG does not mutate the input ChartSpec (SC-CERT-03).
func TestRendererPurity(t *testing.T) {
	cases := map[string][]string{
		"line-basic":            {"basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"},
		"column":                {"basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"},
		"area":                  {"basic", "stacked", "percent", "themed-dark"},
		"bar":                   {"basic", "grouped", "stacked", "themed-dark", "adversarial"},
		"scatter":               {"basic", "correlation", "regression", "themed-dark", "adversarial", "xy-points"},
		"bubble":                {"basic", "multi-series", "themed-dark", "uniform-z", "adversarial"},
		"combo":                 {"basic", "dark", "dual-axis", "adversarial"},
		"histogram":             {"basic", "prebinned", "pareto", "themed-dark", "adversarial"},
		"candlestick":           {"basic", "ohlc", "heikin-ashi", "themed-dark", "adversarial"},
		"error-bar":             {"basic", "overlay-grouped", "asymmetric", "themed-dark", "adversarial"},
		"arearange":             {"basic", "spline-range", "themed-dark", "adversarial"},
		"columnrange":           {"basic", "grouped", "horizontal", "themed-dark", "adversarial"},
		"waterfall":             {"basic", "intermediate-sums", "profit-bridge", "themed-dark", "adversarial"},
		"boxplot":               {"basic", "outliers", "grouped", "themed-dark", "adversarial"},
		"bullet":                {"basic", "multi-kpi", "themed-dark", "adversarial"},
		"lollipop":              {"basic", "grouped", "horizontal", "themed-dark", "adversarial"},
		"dumbbell":              {"basic", "grouped", "horizontal", "themed-dark", "adversarial"},
		"funnel":                {"basic", "adversarial", "neck", "pyramid", "themed-dark"},
		"variwide":              {"basic", "adversarial", "dark", "negative"},
		"timeline":              {"basic", "multi", "vertical", "adversarial"},
		"streamgraph":           {"basic", "silhouette", "themed-dark", "adversarial"},
		"windbarb":              {"basic", "datetime", "southern-hemisphere", "themed-dark", "adversarial"},
		"vector-plot":           {"basic", "field", "themed-dark", "uniform-length", "adversarial"},
		"flame-chart":           {"basic", "multi-series", "deep-stack", "themed-dark", "adversarial"},
		"pie":                   {"basic", "many-slices", "single-slice", "themed-dark", "adversarial", "donut", "donut-single", "donut-dark", "variable-radius"},
		"gauge":                 {"basic", "no-bands", "full-scale", "themed-dark", "adversarial"},
		"solid-gauge":           {"basic", "no-bands", "full-scale", "themed-dark", "adversarial"},
		"radar":                 {"basic", "line-only", "single-series", "themed-dark", "adversarial"},
		"polar":                 {"basic", "line-only", "single-series", "themed-dark", "adversarial"},
		"nightingale":           {"basic", "multi-series", "single-series", "themed-dark", "adversarial"},
		"parliament":            {"basic", "multi-series", "single-series", "themed-dark", "adversarial"},
		"radial-bar":            {"basic", "multi-series", "single-series", "themed-dark", "adversarial"},
		"wind-rose":             {"basic", "many-directions", "single-series", "themed-dark", "adversarial"},
		"technical-indicators":  {"basic", "bollinger", "rsi-pane", "themed-dark", "adversarial"},
		"xrange":                {"trace-waterfall", "gantt", "swimlanes", "themed-dark", "adversarial"},
		"development-triangle":  {"basic", "diagonal", "factors", "annotated", "themed-dark", "rectangular-3x5", "rectangular-6x4"},
	}
	for chartDir, names := range cases {
		for _, name := range names {
			specBytes, err := os.ReadFile("../../charts/" + chartDir + "/examples/" + name + ".json")
			if err != nil {
				t.Fatal(err)
			}
			spec, err := FromJSON(specBytes)
			if err != nil {
				t.Fatal(err)
			}
			before, err := json.Marshal(spec)
			if err != nil {
				t.Fatal(err)
			}
			_, err = RenderSVG(spec)
			if err != nil {
				t.Fatal(err)
			}
			after, err := json.Marshal(spec)
			if err != nil {
				t.Fatal(err)
			}
			if string(before) != string(after) {
				t.Errorf("renderer mutated spec for %s/%s", chartDir, name)
			}
		}
	}
}

// TestSemanticInvariants verifies output correctness properties (DEC-050 / SC-CERT-06).
func TestSemanticInvariants(t *testing.T) {
	root := "../../"
	barRe := regexp.MustCompile(`<rect\s[^>]*class="sc-bar sc-point"[^>]*/>`)
	bubbleRe := regexp.MustCompile(`<circle\s[^>]*class="sc-bubble sc-point"[^>]*/>`)
	attrRe := regexp.MustCompile(`([\w-]+)="([^"]*)"`)

	extractAttrs := func(re2 *regexp.Regexp, svg string) []map[string]string {
		matches := re2.FindAllString(svg, -1)
		var out []map[string]string
		for _, m := range matches {
			attrs := map[string]string{}
			for _, a := range attrRe.FindAllStringSubmatch(m, -1) {
				attrs[a[1]] = a[2]
			}
			out = append(out, attrs)
		}
		return out
	}

	// SC-SEM-001: histogram bin counts == observation count
	t.Run("SC-SEM-001/histogram-observation-count", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/histogram/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)
		total := 0.0
		for _, b := range bars {
			v, _ := strconv.ParseFloat(b["data-y"], 64)
			total += v
		}
		nObs := 0
		for _, s := range spec.Series {
			nObs += len(s.Data)
		}
		if total != float64(nObs) {
			t.Errorf("bin counts %.0f != observations %d", total, nObs)
		}
	})

	// SC-SEM-001: multi-series histogram
	t.Run("SC-SEM-001/histogram-multi-series", func(t *testing.T) {
		specJSON := []byte(`{
			"type": "histogram",
			"binning": {"count": 5},
			"series": [
				{"name": "A", "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
				{"name": "B", "data": [3, 5, 7, 9, 11, 13]}
			]
		}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)
		for si, s := range spec.Series {
			count := 0.0
			idx := strconv.Itoa(si)
			for _, b := range bars {
				if b["data-series"] == idx {
					v, _ := strconv.ParseFloat(b["data-y"], 64)
					count += v
				}
			}
			if count != float64(len(s.Data)) {
				t.Errorf("series %d: bin counts %.0f != observations %d", si, count, len(s.Data))
			}
		}
	})

	// SC-SEM-002: waterfall closing total == sum(deltas)
	t.Run("SC-SEM-002/waterfall-balance", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/waterfall/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)
		lastTotal, _ := strconv.ParseFloat(bars[len(bars)-1]["data-total"], 64)
		expected := 0.0
		for _, v := range spec.Series[0].Data {
			expected += v
		}
		if lastTotal != expected {
			t.Errorf("closing total %.0f != sum(deltas) %.0f", lastTotal, expected)
		}
	})

	// SC-SEM-002: waterfall with intermediate sums
	t.Run("SC-SEM-002/waterfall-intermediate-sums", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/waterfall/examples/intermediate-sums.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)

		skip := map[int]bool{}
		for _, v := range spec.SumIndices {
			skip[v] = true
		}
		for _, v := range spec.IntermediateSumIndices {
			skip[v] = true
		}
		expected := 0.0
		for i, v := range spec.Series[0].Data {
			if !skip[i] {
				expected += v
			}
		}

		lastTotal, _ := strconv.ParseFloat(bars[len(bars)-1]["data-total"], 64)
		if lastTotal != expected {
			t.Errorf("closing total %.0f != sum(non-sum deltas) %.0f", lastTotal, expected)
		}
	})

	// SC-SEM-006: bubble z > z' implies r >= r'
	t.Run("SC-SEM-006/bubble-z-radius-monotonic", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/bubble/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		circles := extractAttrs(bubbleRe, svg)
		type zr struct{ z, r float64 }
		var pairs []zr
		for _, c := range circles {
			z, _ := strconv.ParseFloat(c["data-z"], 64)
			r, _ := strconv.ParseFloat(c["data-r"], 64)
			pairs = append(pairs, zr{z, r})
		}
		for i, a := range pairs {
			for j, b := range pairs {
				if a.z > b.z && a.r < b.r {
					t.Errorf("bubble %d (z=%.0f, r=%.1f) smaller than bubble %d (z=%.0f, r=%.1f)",
						i, a.z, a.r, j, b.z, b.r)
				}
			}
		}
	})

	// SC-SEM-006: multi-series bubbles share a global z scale
	t.Run("SC-SEM-006/bubble-z-radius-multi-series", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/bubble/examples/multi-series.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		circles := extractAttrs(bubbleRe, svg)
		type zr struct{ z, r float64 }
		var pairs []zr
		for _, c := range circles {
			z, _ := strconv.ParseFloat(c["data-z"], 64)
			r, _ := strconv.ParseFloat(c["data-r"], 64)
			pairs = append(pairs, zr{z, r})
		}
		for i, a := range pairs {
			for j, b := range pairs {
				if a.z > b.z && a.r < b.r {
					t.Errorf("bubble %d (z=%.0f, r=%.1f) smaller than bubble %d (z=%.0f, r=%.1f)",
						i, a.z, a.r, j, b.z, b.r)
				}
			}
		}
	})

	// SC-SEM-007: percent stack bar heights tile to 100%
	t.Run("SC-SEM-007/percent-stack-bar-heights", func(t *testing.T) {
		specJSON := []byte(`{
			"type": "column",
			"stacking": "percent",
			"xAxis": {"categories": ["Q1", "Q2", "Q3"]},
			"series": [
				{"name": "A", "data": [30, 40, 10]},
				{"name": "B", "data": [20, 10, 50]},
				{"name": "C", "data": [50, 50, 40]}
			]
		}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)

		byCat := map[string]float64{}
		for _, b := range bars {
			h, _ := strconv.ParseFloat(b["height"], 64)
			byCat[b["data-x"]] += h
		}

		var ref float64
		var refCat string
		for cat, total := range byCat {
			if refCat == "" {
				ref = total
				refCat = cat
				continue
			}
			if diff := total - ref; diff > 0.5 || diff < -0.5 {
				t.Errorf("category %s height %.1f != %s height %.1f", cat, total, refCat, ref)
			}
		}
		if ref <= 0 {
			t.Error("no bar height rendered")
		}
	})

	// SC-SEM-007: zero category produces no visible bars
	t.Run("SC-SEM-007/percent-stack-zero-category", func(t *testing.T) {
		specJSON := []byte(`{
			"type": "column",
			"stacking": "percent",
			"xAxis": {"categories": ["Q1", "Q2", "Q3"]},
			"series": [
				{"name": "A", "data": [30, 0, 10]},
				{"name": "B", "data": [20, 0, 50]}
			]
		}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)

		byCat := map[string]float64{}
		for _, b := range bars {
			h, _ := strconv.ParseFloat(b["height"], 64)
			byCat[b["data-x"]] += h
		}

		if byCat["Q2"] > 0.5 {
			t.Errorf("zero category Q2 has height %.1f", byCat["Q2"])
		}
		q1 := byCat["Q1"]
		q3 := byCat["Q3"]
		if diff := q1 - q3; diff > 0.5 || diff < -0.5 {
			t.Errorf("Q1 height %.1f != Q3 height %.1f", q1, q3)
		}
	})

	// ── SC-SEM-011: Range family: data-low <= data-high ──

	pointRe := regexp.MustCompile(`<(?:circle|rect)\s[^>]*class="[^"]*sc-point[^"]*"[^>]*/?>`)

	extractRangePoints := func(svg string) []map[string]string {
		matches := pointRe.FindAllString(svg, -1)
		var out []map[string]string
		for _, m := range matches {
			attrs := map[string]string{}
			for _, a := range attrRe.FindAllStringSubmatch(m, -1) {
				attrs[a[1]] = a[2]
			}
			if _, hasLow := attrs["data-low"]; hasLow {
				if _, hasHigh := attrs["data-high"]; hasHigh {
					out = append(out, attrs)
				}
			}
		}
		return out
	}

	t.Run("SC-SEM-011/arearange-low-le-high", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/arearange/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		points := extractRangePoints(svg)
		if len(points) == 0 {
			t.Fatal("no arearange points found")
		}
		for i, p := range points {
			lo, _ := strconv.ParseFloat(p["data-low"], 64)
			hi, _ := strconv.ParseFloat(p["data-high"], 64)
			if lo > hi {
				t.Errorf("point %d: low %.1f > high %.1f", i, lo, hi)
			}
		}
	})

	t.Run("SC-SEM-011/columnrange-low-le-high", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/columnrange/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		points := extractRangePoints(svg)
		if len(points) == 0 {
			t.Fatal("no columnrange points found")
		}
		for i, p := range points {
			lo, _ := strconv.ParseFloat(p["data-low"], 64)
			hi, _ := strconv.ParseFloat(p["data-high"], 64)
			if lo > hi {
				t.Errorf("bar %d: low %.1f > high %.1f", i, lo, hi)
			}
		}
	})

	t.Run("SC-SEM-011/columnrange-bar-height-positive", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/columnrange/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		points := extractRangePoints(svg)
		for i, p := range points {
			lo, _ := strconv.ParseFloat(p["data-low"], 64)
			hi, _ := strconv.ParseFloat(p["data-high"], 64)
			if lo != hi {
				h, _ := strconv.ParseFloat(p["height"], 64)
				if h <= 0 {
					t.Errorf("bar %d: low %.1f != high %.1f but height is %.1f", i, lo, hi, h)
				}
			}
		}
	})

	t.Run("SC-SEM-011/dumbbell-low-le-high", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/dumbbell/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		points := extractRangePoints(svg)
		if len(points) == 0 {
			t.Fatal("no dumbbell points found")
		}
		for i, p := range points {
			lo, _ := strconv.ParseFloat(p["data-low"], 64)
			hi, _ := strconv.ParseFloat(p["data-high"], 64)
			if lo > hi {
				t.Errorf("point %d: low %.1f > high %.1f", i, lo, hi)
			}
		}
	})

	connectorRe := regexp.MustCompile(`class="sc-connector"`)

	t.Run("SC-SEM-011/dumbbell-connector-count", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/dumbbell/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		connectors := connectorRe.FindAllString(svg, -1)
		nPoints := 0
		for _, s := range spec.Series {
			nPoints += len(s.Data)
		}
		if len(connectors) != nPoints {
			t.Errorf("connectors %d != points %d", len(connectors), nPoints)
		}
	})

	// ── SC-SEM-012: Error-bar: low <= central value <= high ──

	t.Run("SC-SEM-012/error-bar-low-le-value-le-high", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/error-bar/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		points := extractRangePoints(svg)
		if len(points) == 0 {
			t.Fatal("no error-bar points found")
		}
		for i, p := range points {
			lo, _ := strconv.ParseFloat(p["data-low"], 64)
			y, _ := strconv.ParseFloat(p["data-y"], 64)
			hi, _ := strconv.ParseFloat(p["data-high"], 64)
			if lo > y || y > hi {
				t.Errorf("point %d: low %.1f <= y %.1f <= high %.1f violated", i, lo, y, hi)
			}
		}
	})

	t.Run("SC-SEM-012/error-bar-constructed", func(t *testing.T) {
		specJSON := []byte(`{
			"type": "error-bar",
			"xAxis": {"categories": ["A", "B", "C"]},
			"series": [{"name": "test", "data": [50, 100, 75], "low": [30, 80, 60], "high": [70, 120, 90]}]
		}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		points := extractRangePoints(svg)
		if len(points) != 3 {
			t.Fatalf("expected 3 points, got %d", len(points))
		}
		for i, p := range points {
			lo, _ := strconv.ParseFloat(p["data-low"], 64)
			y, _ := strconv.ParseFloat(p["data-y"], 64)
			hi, _ := strconv.ParseFloat(p["data-high"], 64)
			if lo > y || y > hi {
				t.Errorf("point %d: %.1f <= %.1f <= %.1f violated", i, lo, y, hi)
			}
		}
	})

	// ── SC-SEM-013: Boxplot structural integrity ──

	boxRe := regexp.MustCompile(`<rect\s[^>]*class="sc-box sc-point"[^>]*/>`)
	whiskerCapRe := regexp.MustCompile(`class="sc-whisker-cap"`)

	t.Run("SC-SEM-013/boxplot-median-matches-input", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/boxplot/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		var raw map[string]interface{}
		if err := json.Unmarshal(specBytes, &raw); err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		boxes := extractAttrs(boxRe, svg)
		series0 := raw["series"].([]interface{})[0].(map[string]interface{})
		boxData := series0["boxData"].([]interface{})
		if len(boxes) != len(boxData) {
			t.Fatalf("boxes %d != boxData %d", len(boxes), len(boxData))
		}
		for i, box := range boxes {
			actual, _ := strconv.ParseFloat(box["data-y"], 64)
			expected := boxData[i].(map[string]interface{})["median"].(float64)
			if actual != expected {
				t.Errorf("box %d: data-y %.1f != median %.1f", i, actual, expected)
			}
		}
	})

	t.Run("SC-SEM-013/boxplot-box-height-positive", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/boxplot/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		boxes := extractAttrs(boxRe, svg)
		for i, box := range boxes {
			h, _ := strconv.ParseFloat(box["height"], 64)
			if h <= 0 {
				t.Errorf("box %d: height is %.1f, expected > 0", i, h)
			}
		}
	})

	t.Run("SC-SEM-013/boxplot-whisker-cap-count", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/boxplot/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		boxes := extractAttrs(boxRe, svg)
		caps := whiskerCapRe.FindAllString(svg, -1)
		if len(caps) != 2*len(boxes) {
			t.Errorf("caps %d != 2 * boxes %d", len(caps), len(boxes))
		}
	})

	t.Run("SC-SEM-013/boxplot-constructed", func(t *testing.T) {
		specJSON := []byte(`{
			"type": "boxplot",
			"xAxis": {"categories": ["X", "Y"]},
			"series": [{"name": "test", "data": [50, 100], "boxData": [
				{"low": 10, "q1": 30, "median": 50, "q3": 70, "high": 90},
				{"low": 60, "q1": 80, "median": 100, "q3": 120, "high": 140}
			]}]
		}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		boxes := extractAttrs(boxRe, svg)
		if len(boxes) != 2 {
			t.Fatalf("expected 2 boxes, got %d", len(boxes))
		}
		v0, _ := strconv.ParseFloat(boxes[0]["data-y"], 64)
		v1, _ := strconv.ParseFloat(boxes[1]["data-y"], 64)
		if v0 != 50 {
			t.Errorf("box 0: data-y %.1f != 50", v0)
		}
		if v1 != 100 {
			t.Errorf("box 1: data-y %.1f != 100", v1)
		}
		caps := whiskerCapRe.FindAllString(svg, -1)
		if len(caps) != 4 {
			t.Errorf("expected 4 caps, got %d", len(caps))
		}
	})

	// ── SC-SEM-014: Bullet structural completeness ──

	rangeRe := regexp.MustCompile(`class="sc-range"`)
	targetRe := regexp.MustCompile(`class="sc-target"`)

	t.Run("SC-SEM-014/bullet-measure-matches-input", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/bullet/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)
		if len(bars) != len(spec.Series[0].Data) {
			t.Fatalf("bars %d != data %d", len(bars), len(spec.Series[0].Data))
		}
		for i, bar := range bars {
			actual, _ := strconv.ParseFloat(bar["data-y"], 64)
			if actual != spec.Series[0].Data[i] {
				t.Errorf("bar %d: data-y %.1f != data %.1f", i, actual, spec.Series[0].Data[i])
			}
		}
	})

	t.Run("SC-SEM-014/bullet-range-count", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/bullet/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		var raw map[string]interface{}
		if err := json.Unmarshal(specBytes, &raw); err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		ranges := rangeRe.FindAllString(svg, -1)
		nRanges := len(raw["bulletRanges"].([]interface{}))
		nCats := len(raw["xAxis"].(map[string]interface{})["categories"].([]interface{}))
		expected := nRanges * nCats
		if len(ranges) != expected {
			t.Errorf("ranges %d != %d (%d * %d)", len(ranges), expected, nRanges, nCats)
		}
	})

	t.Run("SC-SEM-014/bullet-target-present", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/bullet/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		targets := targetRe.FindAllString(svg, -1)
		if len(targets) != 1 {
			t.Errorf("expected 1 target, got %d", len(targets))
		}
	})

	t.Run("SC-SEM-014/bullet-constructed", func(t *testing.T) {
		specJSON := []byte(`{
			"type": "bullet",
			"xAxis": {"categories": ["KPI-A", "KPI-B"]},
			"series": [{"name": "measure", "data": [75, 120]}],
			"bulletTarget": 100,
			"bulletRanges": [50, 100, 150]
		}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		bars := extractAttrs(barRe, svg)
		if len(bars) != 2 {
			t.Fatalf("expected 2 bars, got %d", len(bars))
		}
		v0, _ := strconv.ParseFloat(bars[0]["data-y"], 64)
		v1, _ := strconv.ParseFloat(bars[1]["data-y"], 64)
		if v0 != 75 {
			t.Errorf("bar 0: data-y %.1f != 75", v0)
		}
		if v1 != 120 {
			t.Errorf("bar 1: data-y %.1f != 120", v1)
		}
		ranges := rangeRe.FindAllString(svg, -1)
		if len(ranges) != 6 {
			t.Errorf("expected 6 ranges (3 * 2 categories), got %d", len(ranges))
		}
		targets := targetRe.FindAllString(svg, -1)
		if len(targets) != 2 {
			t.Errorf("expected 2 targets (1 * 2 categories), got %d", len(targets))
		}
	})
}

// TestSemanticInvariantsDevelopmentTriangle verifies output correctness properties for development-triangle.
func TestSemanticInvariantsDevelopmentTriangle(t *testing.T) {
	root := "../../"
	dtValueRe := regexp.MustCompile(`<text\s[^>]*class="sc-dt-value"[^>]*>([^<]+)</text>`)
	dtDiagRe := regexp.MustCompile(`<rect\s[^>]*class="sc-dt-diag"[^>]*/>`)
	dtFactorRe := regexp.MustCompile(`<text\s[^>]*class="sc-dt-factor"[^>]*>([^<]+)</text>`)
	attrRe2 := regexp.MustCompile(`([\w-]+)="([^"]*)"`)

	extractDiags := func(svg string) []map[string]string {
		matches := dtDiagRe.FindAllString(svg, -1)
		var out []map[string]string
		for _, m := range matches {
			attrs := map[string]string{}
			for _, a := range attrRe2.FindAllStringSubmatch(m, -1) {
				attrs[a[1]] = a[2]
			}
			out = append(out, attrs)
		}
		return out
	}

	// DT-SEM-001: every rendered data cell maps to exactly one supplied triangle value
	t.Run("DT-SEM-001/cell-count-basic", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		rendered := dtValueRe.FindAllStringSubmatch(svg, -1)
		totalValues := 0
		for _, row := range spec.Triangle.Values {
			totalValues += len(row)
		}
		if len(rendered) != totalValues {
			t.Errorf("rendered cells %d != supplied values %d", len(rendered), totalValues)
		}
	})

	t.Run("DT-SEM-001/cell-count-diagonal", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/diagonal.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		rendered := dtValueRe.FindAllStringSubmatch(svg, -1)
		totalValues := 0
		for _, row := range spec.Triangle.Values {
			totalValues += len(row)
		}
		if len(rendered) != totalValues {
			t.Errorf("rendered cells %d != supplied values %d", len(rendered), totalValues)
		}
	})

	// DT-SEM-003: latest diagonal highlights rightmost populated cell per row
	t.Run("DT-SEM-003/diagonal-positions", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/diagonal.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		diags := extractDiags(svg)
		values := spec.Triangle.Values
		if len(diags) != len(values) {
			t.Fatalf("diagonal rects %d != rows %d", len(diags), len(values))
		}
		for i, diag := range diags {
			expectedPeriod := len(values[i]) - 1
			gotOrigin, _ := strconv.Atoi(diag["data-origin"])
			gotPeriod, _ := strconv.Atoi(diag["data-period"])
			if gotOrigin != i {
				t.Errorf("diagonal rect %d: origin %d != expected %d", i, gotOrigin, i)
			}
			if gotPeriod != expectedPeriod {
				t.Errorf("diagonal rect %d: period %d != expected %d", i, gotPeriod, expectedPeriod)
			}
		}
	})

	t.Run("DT-SEM-003/diagonal-constructed", func(t *testing.T) {
		specJSON := []byte(`{"type":"development-triangle","triangle":{"origins":["A","B","C"],"periods":[12,24,36],"values":[[10,20,30],[40,50],[60]]},"diagonal":{"highlight":true}}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		diags := extractDiags(svg)
		if len(diags) != 3 {
			t.Fatalf("expected 3 diagonal rects, got %d", len(diags))
		}
		// Row 0: last cell = period 2, Row 1: last cell = period 1, Row 2: last cell = period 0
		expected := []int{2, 1, 0}
		for i, diag := range diags {
			gotPeriod, _ := strconv.Atoi(diag["data-period"])
			if gotPeriod != expected[i] {
				t.Errorf("diagonal %d: period %d != expected %d", i, gotPeriod, expected[i])
			}
		}
	})

	// DT-SEM-005: supplied factor values are rendered exactly (not recalculated)
	t.Run("DT-SEM-005/factors-rendered-exactly", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/factors.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		rendered := dtFactorRe.FindAllStringSubmatch(svg, -1)
		supplied := spec.Factors.Values
		if len(rendered) != len(supplied) {
			t.Fatalf("rendered factors %d != supplied %d", len(rendered), len(supplied))
		}
		for i, m := range rendered {
			expected := fmt.Sprintf("%.3f", supplied[i])
			if m[1] != expected {
				t.Errorf("factor %d: rendered %q != expected %q", i, m[1], expected)
			}
		}
	})

	t.Run("DT-SEM-005/factors-constructed", func(t *testing.T) {
		specJSON := []byte(`{"type":"development-triangle","triangle":{"origins":["X","Y"],"periods":[12,24,36],"values":[[100,200,300],[150,250]]},"factors":{"show":true,"values":[2.000,1.500]}}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		rendered := dtFactorRe.FindAllStringSubmatch(svg, -1)
		expected := []string{"2.000", "1.500"}
		if len(rendered) != len(expected) {
			t.Fatalf("rendered factors %d != expected %d", len(rendered), len(expected))
		}
		for i, m := range rendered {
			if m[1] != expected[i] {
				t.Errorf("factor %d: rendered %q != expected %q", i, m[1], expected[i])
			}
		}
	})

	// DT-SEM-007: annotation resolves to exactly its intended populated cell
	t.Run("DT-SEM-007/annotation-position", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/annotated.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		annGroupRe := regexp.MustCompile(`<g class="sc-dt-annotation-group"`)
		annCircleRe := regexp.MustCompile(`<circle class="sc-dt-annotation"`)
		groups := annGroupRe.FindAllString(svg, -1)
		circles := annCircleRe.FindAllString(svg, -1)
		if len(groups) != 1 {
			t.Errorf("expected 1 annotation group, got %d", len(groups))
		}
		if len(circles) != 1 {
			t.Errorf("expected 1 annotation circle, got %d", len(circles))
		}
	})

	t.Run("DT-SEM-007/annotation-constructed", func(t *testing.T) {
		specJSON := []byte(`{"type":"development-triangle","triangle":{"origins":["R1","R2"],"periods":[6,12],"values":[[10,20],[30]]},"annotations":[{"origin":"R1","period":12,"text":"Check this"}]}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		annGroupRe := regexp.MustCompile(`<g class="sc-dt-annotation-group"`)
		groups := annGroupRe.FindAllString(svg, -1)
		if len(groups) != 1 {
			t.Errorf("expected 1 annotation group, got %d", len(groups))
		}
	})

	// DT-SEM-008: annotation text survives into accessible SVG metadata
	t.Run("DT-SEM-008/annotation-accessible-metadata", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/annotated.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		annText := spec.Annotations[0].Text
		if !strings.Contains(svg, "<title>"+annText+"</title>") {
			t.Errorf("annotation text %q not found in <title>", annText)
		}
		if !strings.Contains(svg, `aria-label="`+annText+`"`) {
			t.Errorf("annotation text %q not found in aria-label", annText)
		}
	})

	t.Run("DT-SEM-008/annotation-text-constructed", func(t *testing.T) {
		specJSON := []byte(`{"type":"development-triangle","triangle":{"origins":["A"],"periods":[12],"values":[[99]]},"annotations":[{"origin":"A","period":12,"text":"Special note here"}]}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(svg, "<title>Special note here</title>") {
			t.Error("expected <title>Special note here</title> in SVG")
		}
		if !strings.Contains(svg, `aria-label="Special note here"`) {
			t.Error(`expected aria-label="Special note here" in SVG`)
		}
	})

	// DT-SEM-009: unit/view/valueType survive into deterministic output metadata
	t.Run("DT-SEM-009/metadata-basic", func(t *testing.T) {
		specBytes, err := os.ReadFile(root + "charts/development-triangle/examples/basic.json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(svg, `data-triangle-view="cumulative"`) {
			t.Error("expected data-triangle-view=cumulative")
		}
		if !strings.Contains(svg, `data-triangle-value-type="incurred"`) {
			t.Error("expected data-triangle-value-type=incurred")
		}
	})

	t.Run("DT-SEM-009/metadata-with-unit", func(t *testing.T) {
		specJSON := []byte(`{"type":"development-triangle","title":"Unit test","triangle":{"origins":["2024"],"periods":[12],"values":[[100]],"unit":"GBP thousands","view":"incremental","valueType":"paid"}}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(svg, `data-triangle-view="incremental"`) {
			t.Error("expected data-triangle-view=incremental")
		}
		if !strings.Contains(svg, `data-triangle-value-type="paid"`) {
			t.Error("expected data-triangle-value-type=paid")
		}
		if !strings.Contains(svg, "Unit: GBP thousands") {
			t.Error("expected unit label text")
		}
	})

	t.Run("DT-SEM-009/defaults", func(t *testing.T) {
		specJSON := []byte(`{"type":"development-triangle","triangle":{"origins":["2025"],"periods":[0],"values":[[42]]}}`)
		spec, err := FromJSON(specJSON)
		if err != nil {
			t.Fatal(err)
		}
		svg, err := RenderSVG(spec)
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(svg, `data-triangle-view="cumulative"`) {
			t.Error("expected default data-triangle-view=cumulative")
		}
		if !strings.Contains(svg, `data-triangle-value-type="incurred"`) {
			t.Error("expected default data-triangle-value-type=incurred")
		}
	})

	// DT-SEM-010: malformed inputs are rejected before rendering
	t.Run("DT-SEM-010/boolean-value", func(t *testing.T) {
		_, err := FromJSON([]byte(`{"type":"development-triangle","triangle":{"origins":["A"],"periods":[12],"values":[[true]]}}`))
		if err == nil {
			t.Error("expected error for boolean value")
		}
	})

	t.Run("DT-SEM-010/fractional-period", func(t *testing.T) {
		_, err := FromJSON([]byte(`{"type":"development-triangle","triangle":{"origins":["A"],"periods":[12.5],"values":[[100]]}}`))
		if err == nil {
			t.Error("expected error for fractional period")
		}
	})

	t.Run("DT-SEM-010/increasing-row-lengths", func(t *testing.T) {
		_, err := FromJSON([]byte(`{"type":"development-triangle","triangle":{"origins":["A","B"],"periods":[12,24,36],"values":[[10],[20,30]]}}`))
		if err == nil {
			t.Error("expected error for increasing row lengths")
		}
	})

	t.Run("DT-SEM-010/boolean-period", func(t *testing.T) {
		_, err := FromJSON([]byte(`{"type":"development-triangle","triangle":{"origins":["A"],"periods":[true],"values":[[100]]}}`))
		if err == nil {
			t.Error("expected error for boolean period")
		}
	})

	t.Run("DT-SEM-010/empty-row", func(t *testing.T) {
		_, err := FromJSON([]byte(`{"type":"development-triangle","triangle":{"origins":["A","B"],"periods":[12,24],"values":[[100,200],[]]}}`)	)
		if err == nil {
			t.Error("expected error for empty row")
		}
	})
}

func TestRangeDataParity(t *testing.T) {
	cases := []struct {
		name     string
		parallel string
		atomic   string
	}{
		{
			name:     "arearange",
			parallel: `{"type":"arearange","xAxis":{"categories":["A","B","C"]},"series":[{"name":"s","data":[120,180,150],"low":[60,95,80]}]}`,
			atomic:   `{"type":"arearange","xAxis":{"categories":["A","B","C"]},"series":[{"name":"s","rangeData":[{"low":60,"high":120},{"low":95,"high":180},{"low":80,"high":150}]}]}`,
		},
		{
			name:     "columnrange",
			parallel: `{"type":"columnrange","xAxis":{"categories":["A","B"]},"series":[{"name":"s","data":[10,20],"high":[50,70]}]}`,
			atomic:   `{"type":"columnrange","xAxis":{"categories":["A","B"]},"series":[{"name":"s","rangeData":[{"low":10,"high":50},{"low":20,"high":70}]}]}`,
		},
		{
			name:     "error-bar",
			parallel: `{"type":"error-bar","xAxis":{"categories":["A","B"]},"series":[{"name":"s","data":[100,200],"low":[80,170],"high":[120,230]}]}`,
			atomic:   `{"type":"error-bar","xAxis":{"categories":["A","B"]},"series":[{"name":"s","rangeData":[{"low":80,"high":120,"value":100},{"low":170,"high":230,"value":200}]}]}`,
		},
		{
			name:     "dumbbell",
			parallel: `{"type":"dumbbell","xAxis":{"categories":["A","B"]},"series":[{"name":"s","data":[10,20],"high":[50,70]}]}`,
			atomic:   `{"type":"dumbbell","xAxis":{"categories":["A","B"]},"series":[{"name":"s","rangeData":[{"low":10,"high":50},{"low":20,"high":70}]}]}`,
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			specP, err := FromJSON([]byte(tc.parallel))
			if err != nil {
				t.Fatalf("parallel: %v", err)
			}
			specA, err := FromJSON([]byte(tc.atomic))
			if err != nil {
				t.Fatalf("atomic: %v", err)
			}
			svgP, _ := RenderSVG(specP)
			svgA, _ := RenderSVG(specA)
			if svgP != svgA {
				t.Errorf("SVG mismatch for %s: parallel (%d bytes) != atomic (%d bytes)", tc.name, len(svgP), len(svgA))
			}
		})
	}
}

func TestRangeDataValidation(t *testing.T) {
	bad := `{"type":"arearange","series":[{"name":"s","rangeData":[{"low":100,"high":50}]}]}`
	_, err := FromJSON([]byte(bad))
	if err == nil {
		t.Fatal("expected error for low > high")
	}
	if !strings.Contains(err.Error(), "low (100) must be <= high (50)") {
		t.Errorf("expected low>high error, got: %v", err)
	}

	missingVal := `{"type":"error-bar","series":[{"name":"s","rangeData":[{"low":5,"high":10}]}]}`
	_, err = FromJSON([]byte(missingVal))
	if err == nil {
		t.Fatal("expected error for missing value")
	}
	if !strings.Contains(err.Error(), "value: required for error-bar") {
		t.Errorf("expected value required error, got: %v", err)
	}

	valid := `{"type":"columnrange","xAxis":{"categories":["A"]},"series":[{"name":"s","rangeData":[{"low":10,"high":50}]}]}`
	_, err = FromJSON([]byte(valid))
	if err != nil {
		t.Fatalf("valid rangeData rejected: %v", err)
	}
}
