// Column range chart renderer — floating low-to-high bars.
// Byte-identical SVG output with the Python renderer.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package stonecharts

import (
	"math"
	"strconv"
	"strings"
)

// renderColumnRangeSVG delegates to the shared cartesian frame with band
// x-scale, includeZero=false (floating bars need no zero anchor), and a11y
// noun "Column range". YAxis.Min/Max are pre-set from data (lows) and High
// (highs) so the frame builds the correct value-axis domain.
func renderColumnRangeSVG(spec *ChartSpec) string {
	// Shallow copy to avoid mutating the original.
	s2 := *spec
	series := make([]Series, len(s2.Series))
	copy(series, s2.Series)
	s2.Series = series

	// Pre-set YAxis.Min from min(all lows) and YAxis.Max from max(all highs).
	firstLo := true
	firstHi := true
	var lo, hi float64
	for _, s := range s2.Series {
		for _, v := range s.Data {
			if firstLo {
				lo = v
				firstLo = false
			}
			if v < lo {
				lo = v
			}
		}
		for _, v := range s.High {
			if firstHi {
				hi = v
				firstHi = false
			}
			if v > hi {
				hi = v
			}
		}
	}
	if s2.YAxis.Min == nil && !firstLo {
		s2.YAxis.Min = &lo
	}
	if s2.YAxis.Max == nil && !firstHi {
		s2.YAxis.Max = &hi
	}

	orient := s2.Orientation
	if orient == "" {
		orient = "vertical"
	}
	return renderCartesian(&s2, "Column range", "band", columnRangeMarks, false, orient)
}

// columnRangeMarks emits the column-range-specific marks — one
// <g class="sc-series"> per series and one floating <rect> per datum
// spanning ypix(high) (top) to ypix(low) (bottom).
func columnRangeMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	horiz := f.orientation == "horizontal"

	var band float64
	if horiz {
		band = f.bandHeight()
	} else {
		band = f.bandWidth()
	}
	groupW := band * (1 - 0.2)
	k := len(f.spec.Series)
	if !f.spec.groupingOn() {
		k = 1
	}
	if k < 1 {
		k = 1
	}
	barW := groupW / float64(k)

	for si, s := range f.spec.Series {
		st := f.styles[si]
		highArr := s.High

		p.WriteString(`<g class="sc-series" data-series="` + strconv.Itoa(si) + `">`)

		limit := len(s.Data)
		if f.n < limit {
			limit = f.n
		}
		for i := 0; i < limit; i++ {
			if i >= len(highArr) {
				continue // missing high[i] -> gap
			}

			loVal := s.Data[i]
			hiVal := highArr[i]

			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}

			if horiz {
				cyBand := f.bandCenter(i)
				slot := 0
				if f.spec.groupingOn() {
					slot = si
				}
				top := cyBand - groupW/2 + barW*float64(slot)
				cy := top + barW/2
				xLo := f.valuePix(math.Min(loVal, hiVal))
				xHi := f.valuePix(math.Max(loVal, hiVal))
				x := math.Min(xLo, xHi)
				w := math.Max(math.Abs(xHi-xLo), 1.0)
				cx := f.valuePix(math.Max(loVal, hiVal))

				p.WriteString(`<rect class="sc-bar sc-point" data-series="` + strconv.Itoa(si) +
					`" data-series-name="` + esc(s.Name) +
					`" data-x="` + esc(xlabel) +
					`" data-y="` + esc(fmtNum(hiVal)) +
					`" data-low="` + esc(fmtNum(loVal)) +
					`" data-high="` + esc(fmtNum(hiVal)) +
					`" data-color="` + st.solid +
					`" data-r="3.5" data-r-hover="6"` +
					` cx="` + f1(cx) +
					`" cy="` + f1(cy) +
					`" x="` + f1(x) +
					`" y="` + f1(top) +
					`" width="` + f1(w) +
					`" height="` + f1(barW) +
					`" fill="` + st.fill + `"/>`)
			} else {
				cxBand := f.xpix(float64(i))
				slot := 0
				if f.spec.groupingOn() {
					slot = si
				}
				left := cxBand - groupW/2 + barW*float64(slot)
				cx := left + barW/2
				yTop := f.ypix(math.Max(loVal, hiVal))
				yBot := f.ypix(math.Min(loVal, hiVal))
				barH := math.Max(math.Abs(yBot-yTop), 1.0)

				p.WriteString(`<rect class="sc-bar sc-point" data-series="` + strconv.Itoa(si) +
					`" data-series-name="` + esc(s.Name) +
					`" data-x="` + esc(xlabel) +
					`" data-y="` + esc(fmtNum(hiVal)) +
					`" data-low="` + esc(fmtNum(loVal)) +
					`" data-high="` + esc(fmtNum(hiVal)) +
					`" data-color="` + st.solid +
					`" data-r="3.5" data-r-hover="6"` +
					` cx="` + f1(cx) +
					`" cy="` + f1(yTop) +
					`" x="` + f1(left) +
					`" y="` + f1(yTop) +
					`" width="` + f1(barW) +
					`" height="` + f1(barH) +
					`" fill="` + st.fill + `"/>`)
			}
		}

		p.WriteString(`</g>`)
	}
}
