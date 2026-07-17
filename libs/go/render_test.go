package peakcharts

import (
	"os"
	"testing"
)

// TestLineBasicGolden pins the Go renderer to the shared cross-language golden
// (charts/line-basic/golden/basic.svg), which the Python renderer also matches.
// If this and the Python test both pass, the two libraries are provably in sync.
func TestLineBasicGolden(t *testing.T) {
	specBytes, err := os.ReadFile("../../charts/line-basic/examples/basic.json")
	if err != nil {
		t.Fatal(err)
	}
	spec, err := FromJSON(specBytes)
	if err != nil {
		t.Fatal(err)
	}
	got := RenderSVG(spec)
	want, err := os.ReadFile("../../charts/line-basic/golden/basic.svg")
	if err != nil {
		t.Fatal(err)
	}
	if got != string(want) {
		t.Errorf("SVG != golden (got %d bytes, want %d bytes)", len(got), len(want))
	}
}
