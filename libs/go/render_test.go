package peakcharts

import (
	"os"
	"testing"
)

// TestGolden pins the Go renderer to the shared cross-language goldens
// (charts/line-basic/golden/*.svg), which the Python renderer also matches.
// If this and the Python test both pass, the two libraries are provably in sync.
func TestGolden(t *testing.T) {
	for _, name := range []string{"basic", "styled"} {
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
