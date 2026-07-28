// Bubble chart renderer: *ChartSpec -> SVG string.
//
// Unconnected circles at (x, y) on the same free numeric x/y plane scatter
// already rides (§3.3 Rank 4 of docs/roadmap/chart-families.md); the one
// net-new piece is the size-scale (z -> area-proportional radius). No
// shared-frame changes are needed at all — this file supplies only the
// marks callback, exactly like bar's admission, not scatter's. Mirrors
// libs/python/stonecharts/charts/bubble.py exactly.
package stonecharts

import (
	"math"
	"strings"
)

const (
	bubbleRMin = 4.0
	bubbleRMax = 32.0
)

func clamp01(v float64) float64 {
	if v < 0 {
		return 0
	}
	if v > 1 {
		return 1
	}
	return v
}

// sizeScale is the pinned size-scale geometry (§3.2 "Size scale"; §3.3
// Rank 4), evaluated in this exact order so both languages land on the same
// fmtNum-rounded radius: check the degenerate domain BEFORE any divide,
// clamp01 BEFORE sqrt.
func sizeScale(z, zmin, zmax float64) float64 {
	if zmax <= zmin {
		return (bubbleRMin + bubbleRMax) / 2
	}
	t := clamp01((z - zmin) / (zmax - zmin))
	return bubbleRMin + (bubbleRMax-bubbleRMin)*math.Sqrt(t)
}

func renderBubbleSVG(spec *ChartSpec) string {
	for i := range spec.Series {
		s := &spec.Series[i]
		if len(s.DataPoints) == 0 && len(s.Data) > 0 {
			s.DataPoints = make([]Datum, len(s.Data))
			for j, v := range s.Data {
				s.DataPoints[j] = Datum{X: float64(j), Y: v}
			}
		}
	}
	return renderCartesian(spec, "Bubble", "linear", bubbleMarks, false)
}

func bubbleMarks(f *cartesianFrame, p *strings.Builder) {
	// Global z-domain: reduced over EVERY point of EVERY series, in
	// series-index order then point order, so a given z maps to the same
	// radius everywhere (bubbles stay comparable across series).
	zmin, zmax := 0.0, 0.0
	first := true
	for _, s := range f.spec.Series {
		for _, d := range s.DataPoints {
			z := 0.0
			if d.Z != nil {
				z = *d.Z
			}
			if first {
				zmin, zmax = z, z
				first = false
				continue
			}
			if z < zmin {
				zmin = z
			}
			if z > zmax {
				zmax = z
			}
		}
	}

	for si, s := range f.spec.Series {
		st := f.styles[si]
		// Bubble reinterprets FillOpacity: line's default (0.0) means "no
		// fill" there, but an unfilled bubble is a broken chart (NN#2), so
		// the pinned bubble default is 0.65, not 0.
		op := s.FillOpacity
		if op <= 0 {
			op = 0.65
		}
		p.WriteString(`<g class="sc-series" data-series="` + itoa(si) + `">`)
		for _, d := range s.DataPoints {
			z := 0.0
			if d.Z != nil {
				z = *d.Z
			}
			x, y := f.xpix(d.X), f.ypix(d.Y)
			r := sizeScale(z, zmin, zmax)
			p.WriteString(`<circle class="sc-bubble sc-point" data-series="` + itoa(si) +
				`" data-series-name="` + esc(s.Name) +
				`" data-x="` + esc(fmtNum(d.X)) +
				`" data-y="` + esc(fmtNum(d.Y)) +
				`" data-z="` + esc(fmtNum(z)) +
				`" data-color="` + st.solid +
				`" data-r="` + fmtNum(r) +
				`" data-r-hover="` + fmtNum(r) +
				`" cx="` + f1(x) + `" cy="` + f1(y) +
				`" r="` + fmtNum(r) +
				`" fill="` + st.fill +
				`" fill-opacity="` + fmtNum(op) + `"/>`)
		}
		p.WriteString(`</g>`)
	}
}
