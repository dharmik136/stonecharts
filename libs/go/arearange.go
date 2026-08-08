// Range area chart renderer — filled band between high and low boundaries.
// Byte-identical SVG output with the Python renderer.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package stonecharts

import (
	"strconv"
	"strings"
)

func renderAreaRangeSVG(spec *ChartSpec) string {
	s2 := *spec
	series := make([]Series, len(s2.Series))
	copy(series, s2.Series)
	s2.Series = series

	first := true
	var lo, hi float64
	for _, s := range s2.Series {
		for _, v := range s.Data {
			if first {
				lo, hi = v, v
				first = false
			}
			if v < lo {
				lo = v
			}
			if v > hi {
				hi = v
			}
		}
		for _, v := range s.Low {
			if first {
				lo, hi = v, v
				first = false
			}
			if v < lo {
				lo = v
			}
			if v > hi {
				hi = v
			}
		}
	}
	if s2.YAxis.Min == nil {
		s2.YAxis.Min = &lo
	}
	if s2.YAxis.Max == nil {
		s2.YAxis.Max = &hi
	}

	return renderCartesian(&s2, "Range area", "point", areaRangeMarks, true)
}

func areaRangeMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	useSpline := f.spec.Subtype == "areasplinerange"

	for si, s := range f.spec.Series {
		st := f.styles[si]
		lowArr := s.Low
		spline := useSpline || s.Curve == "monotone"

		n := len(s.Data)
		if f.n < n {
			n = f.n
		}

		hiPts := make([][2]float64, n)
		loPts := make([][2]float64, n)
		for i := 0; i < n; i++ {
			hiPts[i] = [2]float64{f.xpix(float64(i)), f.ypix(s.Data[i])}
			loVal := s.Data[i]
			if i < len(lowArr) {
				loVal = lowArr[i]
			}
			loPts[i] = [2]float64{f.xpix(float64(i)), f.ypix(loVal)}
		}

		if n == 0 {
			continue
		}

		p.WriteString(`<g class="sc-series" data-series="` + strconv.Itoa(si) + `">`)

		// Band path: high L→R, low R→L, close
		var topD string
		if spline {
			topD = splineD(hiPts)
		} else {
			topD = pathD(hiPts, "")
		}

		var bottomParts strings.Builder
		for j := n - 1; j >= 0; j-- {
			bottomParts.WriteString(" L" + f1(loPts[j][0]) + " " + f1(loPts[j][1]))
		}
		bandD := topD + bottomParts.String() + " Z"

		// Fill opacity
		fillOpVal := 0.5
		if s.FillOpacity != 0 {
			fillOpVal = s.FillOpacity
		}
		fillOp := ` fill-opacity="` + fmtNum(fillOpVal) + `"`

		p.WriteString(`<path class="sc-series-range sc-band" data-series="` + strconv.Itoa(si) +
			`" d="` + bandD + `" fill="` + st.fill + `"` + fillOp + ` stroke="none"/>`)

		// Optional bounding strokes
		if s.LineWidth > 0 {
			lw := s.LineWidth
			strokeDash := dashArray(s.DashStyle)
			dashAttr := ""
			if strokeDash != "" {
				dashAttr = ` stroke-dasharray="` + strokeDash + `"`
			}
			// High boundary stroke
			var hiStrokeD string
			if spline {
				hiStrokeD = splineD(hiPts)
			} else {
				hiStrokeD = pathD(hiPts, "")
			}
			p.WriteString(`<path class="sc-series-line sc-range-hi" data-series="` + strconv.Itoa(si) +
				`" d="` + hiStrokeD + `" fill="none" stroke="` + st.stroke +
				`" stroke-width="` + fmtNum(lw) + `" stroke-linejoin="round" stroke-linecap="round"` + dashAttr + `/>`)
			// Low boundary stroke
			var loStrokeD string
			if spline {
				loStrokeD = splineD(loPts)
			} else {
				loStrokeD = pathD(loPts, "")
			}
			p.WriteString(`<path class="sc-series-line sc-range-lo" data-series="` + strconv.Itoa(si) +
				`" d="` + loStrokeD + `" fill="none" stroke="` + st.stroke +
				`" stroke-width="` + fmtNum(lw) + `" stroke-linejoin="round" stroke-linecap="round"` + dashAttr + `/>`)
		}

		// Points at high edge
		radius := 3.5
		radiusHover := radius + 2.5
		for i := 0; i < n; i++ {
			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}
			hiVal := s.Data[i]
			loVal := hiVal
			if i < len(lowArr) {
				loVal = lowArr[i]
			}
			cx := f.xpix(float64(i))
			cy := f.ypix(hiVal)
			p.WriteString(`<circle class="sc-point" data-series="` + strconv.Itoa(si) +
				`" data-series-name="` + esc(s.Name) +
				`" data-x="` + esc(xlabel) +
				`" data-low="` + esc(fmtNum(loVal)) +
				`" data-high="` + esc(fmtNum(hiVal)) +
				`" data-y="` + esc(fmtNum(loVal)+"–"+fmtNum(hiVal)) +
				`" data-color="` + st.solid +
				`" data-r="` + fmtNum(radius) + `" data-r-hover="` + fmtNum(radiusHover) +
				`" cx="` + f1(cx) + `" cy="` + f1(cy) + `" r="` + fmtNum(radius) + `"/>`)
		}

		p.WriteString(`</g>`)
	}
}
