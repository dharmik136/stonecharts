package peakcharts

import (
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

// TestGolden pins the Go renderer to the shared cross-language goldens
// (charts/line-basic/golden/*.svg), which the Python renderer also matches.
// If this and the Python test both pass, the two libraries are provably in sync.
func TestGolden(t *testing.T) {
	for _, name := range []string{"basic", "styled", "markers", "spline", "gradient", "dark", "adversarial"} {
		specBytes, err := os.ReadFile("../../charts/line-basic/examples/" + name + ".json")
		if err != nil {
			t.Fatal(err)
		}
		spec, err := FromJSON(specBytes)
		if err != nil {
			t.Fatal(err)
		}
		got := RenderSVG(spec)
		want, err := os.ReadFile("../../charts/line-basic/golden/" + name + ".svg")
		if err != nil {
			t.Fatal(err)
		}
		if got != string(want) {
			t.Errorf("%s: SVG != golden (got %d bytes, want %d bytes)", name, len(got), len(want))
		}
	}
}

// TestXSSEscaping verifies hostile strings in user-facing fields are escaped.
func TestXSSEscaping(t *testing.T) {
	x := `"><script>alert(1)</script>`
	specJSON := `{"id":` + jsonStr(x) + `,"type":"line","title":` + jsonStr(x) +
		`,"subtitle":` + jsonStr(x) + `,"theme":{"name":"light","gridColor":` + jsonStr(x) +
		`,"palette":[` + jsonStr(x) + `]},"xAxis":{"title":` + jsonStr(x) +
		`,"categories":[` + jsonStr(x) + `,"b","c"]},"yAxis":{"title":` + jsonStr(x) +
		`},"series":[{"name":` + jsonStr(x) + `,"data":[1,2,3],"color":` + jsonStr(x) +
		`,"pattern":{"type":"hatch","color":` + jsonStr(x) + `,"background":` + jsonStr(x) +
		`},"fillOpacity":0.3}]}`
	spec, err := FromJSON([]byte(specJSON))
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(RenderSVG(spec), "<script>alert(1)</script>") {
		t.Error("raw <script> leaked into SVG")
	}
	if strings.Contains(RenderHTML(spec, ""), "<script>alert(1)</script>") {
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
		if svg := RenderSVG(spec); !strings.HasPrefix(svg, "<svg") {
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
	svgOn := RenderSVG(on)
	if !strings.Contains(svgOn, `role="img"`) || !strings.Contains(svgOn, "<desc>") {
		t.Error("a11y default should add role=img + <desc>")
	}
	off := mk()
	no := false
	off.A11y = &no
	off.applyDefaults()
	svgOff := RenderSVG(off)
	if strings.Contains(svgOff, `role="img"`) || strings.Contains(svgOff, "<desc>") {
		t.Error("a11y:false should omit role=img + <desc>")
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
		low := strings.ToLower(RenderSVG(spec))
		if strings.Contains(low, "nan") || strings.Contains(low, "inf") {
			t.Errorf("NaN/Inf in spline for %v", data)
		}
	}
}
