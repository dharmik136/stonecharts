package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// pathD builds the line path 'd'. step in {"", before, after, center}.
// Mirrors line.py _path_d (parts joined by a single space).
func pathD(pts [][2]float64, step string) string {
	parts := make([]string, 0, len(pts)*2)
	if step == "" {
		for i, pt := range pts {
			pre := "L"
			if i == 0 {
				pre = "M"
			}
			parts = append(parts, pre+f1(pt[0])+" "+f1(pt[1]))
		}
		return strings.Join(parts, " ")
	}
	for i, pt := range pts {
		x, y := pt[0], pt[1]
		if i == 0 {
			parts = append(parts, "M"+f1(x)+" "+f1(y))
			continue
		}
		px, py := pts[i-1][0], pts[i-1][1]
		switch step {
		case "before":
			parts = append(parts, "L"+f1(px)+" "+f1(y), "L"+f1(x)+" "+f1(y))
		case "center":
			mx := (px + x) / 2
			parts = append(parts, "L"+f1(mx)+" "+f1(py), "L"+f1(mx)+" "+f1(y), "L"+f1(x)+" "+f1(y))
		default: // after
			parts = append(parts, "L"+f1(x)+" "+f1(py), "L"+f1(x)+" "+f1(y))
		}
	}
	return strings.Join(parts, " ")
}

// splineD builds a monotone cubic spline path (Fritsch-Carlson). Identical math
// to _spline_d in line.py so both languages emit byte-identical curves.
func splineD(pts [][2]float64) string {
	n := len(pts)
	if n < 3 {
		return pathD(pts, "")
	}
	xs := make([]float64, n)
	ys := make([]float64, n)
	for i, p := range pts {
		xs[i], ys[i] = p[0], p[1]
	}
	delta := make([]float64, n-1)
	for i := 0; i < n-1; i++ {
		delta[i] = (ys[i+1] - ys[i]) / (xs[i+1] - xs[i])
	}
	m := make([]float64, n)
	m[0] = delta[0]
	m[n-1] = delta[n-2]
	for i := 1; i < n-1; i++ {
		if delta[i-1]*delta[i] <= 0 {
			m[i] = 0
		} else {
			m[i] = (delta[i-1] + delta[i]) / 2
		}
	}
	for i := 0; i < n-1; i++ {
		if delta[i] == 0 {
			m[i] = 0
			m[i+1] = 0
		} else {
			a := m[i] / delta[i]
			b := m[i+1] / delta[i]
			s := a*a + b*b
			if s > 9 {
				t := 3.0 / math.Sqrt(s)
				m[i] = t * a * delta[i]
				m[i+1] = t * b * delta[i]
			}
		}
	}
	parts := make([]string, 0, n)
	parts = append(parts, "M"+f1(xs[0])+" "+f1(ys[0]))
	for i := 0; i < n-1; i++ {
		h := xs[i+1] - xs[i]
		c1x := xs[i] + h/3
		c1y := ys[i] + m[i]*h/3
		c2x := xs[i+1] - h/3
		c2y := ys[i+1] - m[i+1]*h/3
		parts = append(parts,
			"C"+f1(c1x)+" "+f1(c1y)+" "+f1(c2x)+" "+f1(c2y)+" "+f1(xs[i+1])+" "+f1(ys[i+1]))
	}
	return strings.Join(parts, " ")
}

// markerSVG renders one data-point marker. `common` = shared class + data-* attrs.
// Non-circle shapes carry cx/cy attrs so the JS runtime (crosshair) still works.
func markerSVG(symbol string, x, y, r float64, common, color, halo string) string {
	fs := fmt.Sprintf(`fill="%s" stroke="%s" stroke-width="1"`, color, halo)
	switch symbol {
	case "square":
		return fmt.Sprintf(`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" %s/>`,
			common, f1(x), f1(y), f1(x-r), f1(y-r), f1(2*r), f1(2*r), fs)
	case "triangle":
		poly := f1(x) + "," + f1(y-r) + " " + f1(x-r) + "," + f1(y+r) + " " + f1(x+r) + "," + f1(y+r)
		return fmt.Sprintf(`<polygon %s cx="%s" cy="%s" points="%s" %s/>`, common, f1(x), f1(y), poly, fs)
	case "diamond":
		poly := f1(x) + "," + f1(y-r) + " " + f1(x+r) + "," + f1(y) + " " + f1(x) + "," + f1(y+r) + " " + f1(x-r) + "," + f1(y)
		return fmt.Sprintf(`<polygon %s cx="%s" cy="%s" points="%s" %s/>`, common, f1(x), f1(y), poly, fs)
	default: // circle
		return fmt.Sprintf(`<circle %s cx="%s" cy="%s" r="%s" %s/>`, common, f1(x), f1(y), fmtNum(r), fs)
	}
}

// renderLineSVG mirrors libs/python/stonecharts/charts/line.py exactly so the two
// libraries emit byte-identical SVG for the same spec (see charts/line-basic/golden).
// It is a one-line delegation to the shared cartesian frame (cartesian.go, §4):
// point x-scale, include-zero value axis, a11y noun "Line".
func renderLineSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Line", "point", lineMarks, true)
}

// lineMarks emits the line-specific series marks — one <g class="sc-series">
// per series: area fill, series line, point markers. Moved verbatim from the
// pre-extraction renderLineSVG series loop; all geometry comes from the frame
// (f.xpix / f.ypix), never recomputed here.
func lineMarks(f *cartesianFrame, p *strings.Builder) {
	theme := f.theme
	cats := f.cats
	for si, s := range f.spec.Series {
		st := f.styles[si]
		color := st.solid
		pts := make([][2]float64, len(s.Data))
		for i, v := range s.Data {
			pts[i] = [2]float64{f.xpix(i), f.ypix(v)}
		}
		var d string
		if s.Curve == "monotone" {
			d = splineD(pts)
		} else {
			d = pathD(pts, s.Step)
		}
		lineDashAttr := ""
		if da := dashArray(s.DashStyle); da != "" {
			lineDashAttr = ` stroke-dasharray="` + da + `"`
		}
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		// Area fill (under the line, drawn first so the line sits on top).
		if st.areaFill != "" && len(pts) > 0 {
			base := f.ypix(0.0)
			areaD := d + " L" + f1(pts[len(pts)-1][0]) + " " + f1(base) +
				" L" + f1(pts[0][0]) + " " + f1(base) + " Z"
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
				si, areaD, st.areaFill, st.areaOp))
		}
		p.WriteString(fmt.Sprintf(
			`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
			si, d, st.stroke, fmtNum(s.lineWidth()), lineDashAttr))
		if s.markerEnabled() {
			radius := s.markerRadius()
			radiusHover := radius + 2.5
			symbol := s.markerSymbol()
			for i, pt := range pts {
				xlabel := strconv.Itoa(i)
				if i < len(cats) {
					xlabel = cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(xlabel), esc(fmtNum(s.Data[i])), color, fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, color, theme.MarkerHalo))
			}
		}
		p.WriteString(`</g>`)
	}
}
