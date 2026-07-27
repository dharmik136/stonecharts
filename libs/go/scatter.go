// Scatter chart renderer: *ChartSpec -> SVG string.
//
// Unconnected point marks at (x, y) on a free numeric x-axis and a free
// numeric y-axis (§3.3 Rank 3 of docs/roadmap/chart-families.md). Mirrors
// libs/python/stonecharts/charts/scatter.py exactly. Rides the shared
// cartesian frame with x-scale "linear" and includeZero=false; this file
// supplies only the marks callback, reusing line's markerSVG builder exactly
// as area.go already does.
package stonecharts

import (
	"strings"
)

// renderScatterSVG mirrors scatter.py's render_svg exactly.
//
// backfillDataPoints (§3.3 Rank 3): FromJSON's Series.UnmarshalJSON normalizes
// DataPoints for every series; a caller building *ChartSpec/Series directly
// with a struct literal (bypassing FromJSON — Go has no dataclass-style
// __post_init__ hook to catch this automatically, unlike spec.py's ChartSpec)
// never runs that normalization. Backfill the bare-number fast path
// (x = index) from Data here so scatter still renders instead of silently
// emitting zero points. Positional/object forms aren't expressible through
// Series.Data ([]float64) at all in Go, so no fallback is needed for those —
// a direct-construction caller wanting them sets DataPoints directly.
func renderScatterSVG(spec *ChartSpec) string {
	for i := range spec.Series {
		s := &spec.Series[i]
		if len(s.DataPoints) == 0 && len(s.Data) > 0 {
			s.DataPoints = make([]Datum, len(s.Data))
			for j, v := range s.Data {
				s.DataPoints[j] = Datum{X: float64(j), Y: v}
			}
		}
	}
	return renderCartesian(spec, "Scatter", "linear", scatterMarks, false)
}

func scatterMarks(f *cartesianFrame, p *strings.Builder) {
	theme := f.theme
	for si, s := range f.spec.Series {
		st := f.styles[si]
		// Point fill-opacity (NN#2 — never emit an unfilled point): the shared
		// Series.FillOpacity zero value is indistinguishable from an explicit
		// 0, so scatter treats 0.0 as "unset -> fully opaque" and only a
		// truthy (>0) value dims the fill.
		op := s.FillOpacity
		if op <= 0 {
			op = 1.0
		}
		p.WriteString(`<g class="sc-series" data-series="` + itoa(si) + `">`)
		if s.markerEnabled() {
			radius := s.markerRadius()
			radiusHover := radius + 2.5
			symbol := s.markerSymbol()
			for _, d := range s.DataPoints {
				x, y := f.xpix(d.X), f.ypix(d.Y)
				common := `class="sc-point" data-series="` + itoa(si) +
					`" data-series-name="` + esc(s.Name) +
					`" data-x="` + esc(fmtNum(d.X)) +
					`" data-y="` + esc(fmtNum(d.Y)) +
					`" data-color="` + st.solid +
					`" data-r="` + fmtNum(radius) +
					`" data-r-hover="` + fmtNum(radiusHover) + `"`
				p.WriteString(markerSVG(symbol, x, y, radius, common, st.fill, theme.MarkerHalo, op))
			}
		}
		p.WriteString(`</g>`)
	}
}
