// Error-bar chart renderer — whisker marks with center-value markers.
// Byte-identical SVG output with the Python renderer.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package stonecharts

import (
	"strconv"
	"strings"
)

const (
	errorBarPAD      = 0.2
	errorBarCAP      = 6.0
	errorBarWhiskerSW = "1.5"
)

func renderErrorBarSVG(spec *ChartSpec) string {
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
		for _, v := range s.High {
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

	return renderCartesian(&s2, "Error bar", "band", errorBarMarks, true)
}

func errorBarMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	bandWidth := f.bandWidth()
	groupW := bandWidth * (1 - errorBarPAD)
	k := len(f.spec.Series)
	if k < 1 {
		k = 1
	}
	slotW := groupW / float64(k)

	for si, s := range f.spec.Series {
		color := f.styles[si].solid
		halo := f.theme.MarkerHalo

		mEnabled := true
		mSymbol := "circle"
		mRadius := 3.5
		if s.Marker != nil {
			if s.Marker.Enabled != nil {
				mEnabled = *s.Marker.Enabled
			}
			if s.Marker.Symbol != "" {
				mSymbol = s.Marker.Symbol
			}
			if s.Marker.Radius != 0 {
				mRadius = s.Marker.Radius
			}
		}

		lowArr := s.Low
		highArr := s.High

		p.WriteString(`<g class="sc-series" data-series="` + strconv.Itoa(si) + `">`)

		limit := len(s.Data)
		if f.n < limit {
			limit = f.n
		}
		for i := 0; i < limit; i++ {
			yVal := s.Data[i]
			xc := f.xpix(float64(i))
			cx := xc - groupW/2 + slotW*float64(si) + slotW/2

			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}

			hasLo := i < len(lowArr)
			hasHi := i < len(highArr)

			loVal := yVal
			hiVal := yVal

			if hasLo && hasHi {
				loVal = lowArr[i]
				hiVal = highArr[i]
				yLow := f.ypix(loVal)
				yHigh := f.ypix(hiVal)

				p.WriteString(`<line class="sc-whisker sc-whisker-stem" data-series="` + strconv.Itoa(si) +
					`" x1="` + f1(cx) + `" y1="` + f1(yLow) +
					`" x2="` + f1(cx) + `" y2="` + f1(yHigh) +
					`" stroke="` + color + `" stroke-width="` + errorBarWhiskerSW + `"/>`)
				p.WriteString(`<line class="sc-whisker sc-whisker-cap" data-series="` + strconv.Itoa(si) +
					`" x1="` + f1(cx-errorBarCAP) + `" y1="` + f1(yLow) +
					`" x2="` + f1(cx+errorBarCAP) + `" y2="` + f1(yLow) +
					`" stroke="` + color + `" stroke-width="` + errorBarWhiskerSW + `"/>`)
				p.WriteString(`<line class="sc-whisker sc-whisker-cap" data-series="` + strconv.Itoa(si) +
					`" x1="` + f1(cx-errorBarCAP) + `" y1="` + f1(yHigh) +
					`" x2="` + f1(cx+errorBarCAP) + `" y2="` + f1(yHigh) +
					`" stroke="` + color + `" stroke-width="` + errorBarWhiskerSW + `"/>`)
			}

			if mEnabled {
				yCtr := f.ypix(yVal)
				common := `class="sc-point" data-series="` + strconv.Itoa(si) +
					`" data-series-name="` + esc(s.Name) +
					`" data-x="` + esc(xlabel) +
					`" data-y="` + esc(fmtNum(yVal)) +
					`" data-low="` + esc(fmtNum(loVal)) +
					`" data-high="` + esc(fmtNum(hiVal)) +
					`" data-color="` + color +
					`" data-r="` + fmtNum(mRadius) +
					`" data-r-hover="` + fmtNum(mRadius+2.5) + `"`
				p.WriteString(markerSVG(mSymbol, cx, yCtr, mRadius, common, color, halo, 1.0))
			}
		}

		p.WriteString(`</g>`)
	}
}
