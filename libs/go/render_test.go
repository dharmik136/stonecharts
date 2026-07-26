package stonecharts

import (
	"encoding/json"
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
		"line-basic": {"basic", "styled", "markers", "spline", "gradient", "dark", "adversarial", "gradient-partial"},
		"column":     {"basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"},
		"area":       {"basic", "stacked", "percent", "themed-dark"},
		"bar":        {"basic", "grouped", "stacked", "themed-dark", "adversarial"},
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

func TestCapabilityManifestAndError(t *testing.T) {
	caps := Capabilities()
	if caps.SpecVersion != "0.0.0.1" || caps.SVGContractVersion != "0.0.0.1" {
		t.Fatalf("unexpected manifest versions: %+v", caps)
	}
	if got, want := caps.ChartTypes, []string{"area", "bar", "column", "line"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("manifest chartTypes mismatch: got %v want %v", got, want)
	}
	spec := &ChartSpec{Type: "column", Series: []Series{{Name: "s", Data: []float64{1}}}}
	if svg, err := RenderSVG(spec); err != nil {
		t.Fatalf("expected column to render, got %v", err)
	} else if !strings.HasPrefix(svg, "<svg") {
		t.Fatalf("expected SVG output for column, got %q", svg[:min(len(svg), 64)])
	}
	bad := &ChartSpec{Type: "pie", Series: []Series{{Name: "s", Data: []float64{1}}}}
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
		if ce.Message != `unsupported chart type "pie"` {
			t.Fatalf("unexpected capability message: %+v", ce)
		}
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
