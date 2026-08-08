// Candlestick chart renderer — financial OHLC visualization.
// Byte-identical SVG output with the Python renderer.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package stonecharts

import (
	"math"
	"strconv"
	"strings"
)

// renderCandlestickSVG delegates to the shared cartesian frame with band
// x-scale, includeZero=false (price axis must not anchor to zero), and
// a11y noun "Candlestick". YAxis.Min/Max are pre-set from OHLC data so the
// frame builds the correct value-axis domain.
func renderCandlestickSVG(spec *ChartSpec) string {
	// Shallow copy to avoid mutating the original.
	s2 := *spec
	series := make([]Series, len(s2.Series))
	copy(series, s2.Series)
	s2.Series = series

	// Pre-set YAxis.Min and YAxis.Max from OHLC data.
	first := true
	var lo, hi float64
	for si := range s2.Series {
		ohlc := s2.Series[si].OHLC
		// Ensure Data has the right length so buildFrame computes n from OHLC length.
		if len(s2.Series[si].Data) == 0 && len(ohlc) > 0 {
			s2.Series[si].Data = make([]float64, len(ohlc))
		}
		for _, d := range ohlc {
			if first {
				lo, hi = d.Low, d.High
				first = false
			}
			if d.Low < lo {
				lo = d.Low
			}
			if d.High > hi {
				hi = d.High
			}
		}
	}
	if s2.YAxis.Min == nil {
		s2.YAxis.Min = &lo
	}
	if s2.YAxis.Max == nil {
		s2.YAxis.Max = &hi
	}

	return renderCartesian(&s2, "Candlestick", "band", candlestickMarks, false)
}

// candlestickMarks emits the candlestick-specific marks — one
// <g class="sc-series"> per series and one candle <g> per datum.
// Subtypes: "" / "candlestick", "ohlc", "hlc", "heikin-ashi", "hollow".
func candlestickMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	bandWidth := f.bandWidth()
	groupW := bandWidth * (1 - 0.2)
	k := len(f.spec.Series)
	if k < 1 {
		k = 1
	}
	barW := groupW / float64(k)

	upColor := f.spec.UpColor
	if upColor == "" {
		upColor = "#3f9b6a"
	}
	downColor := f.spec.DownColor
	if downColor == "" {
		downColor = "#d65f5f"
	}

	subtype := f.spec.Subtype

	for si, s := range f.spec.Series {
		p.WriteString(`<g class="sc-series" data-series="` + strconv.Itoa(si) + `">`)

		ohlcData := s.OHLC

		// Heikin-Ashi: transform OHLC before drawing as candlestick.
		if subtype == "heikin-ashi" {
			ha := make([]OHLCDatum, len(ohlcData))
			var prevHaOpen, prevHaClose float64
			for i, d := range ohlcData {
				haClose := (d.Open + d.High + d.Low + d.Close) / 4
				var haOpen float64
				if i == 0 {
					haOpen = (d.Open + d.Close) / 2
				} else {
					haOpen = (prevHaOpen + prevHaClose) / 2
				}
				haHigh := math.Max(d.High, math.Max(haOpen, haClose))
				haLow := math.Min(d.Low, math.Min(haOpen, haClose))
				ha[i] = OHLCDatum{Open: haOpen, High: haHigh, Low: haLow, Close: haClose}
				prevHaOpen = haOpen
				prevHaClose = haClose
			}
			ohlcData = ha
		}

		limit := len(ohlcData)
		if f.n < limit {
			limit = f.n
		}
		for i := 0; i < limit; i++ {
			d := ohlcData[i]
			open, high, low, cl := d.Open, d.High, d.Low, d.Close

			xc := f.xpix(float64(i))
			left := xc - groupW/2 + barW*float64(si)
			cx := left + barW/2
			isUp := cl >= open
			col := downColor
			if isUp {
				col = upColor
			}
			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}

			// Candle wrapper <g> with data attributes for interactivity.
			p.WriteString(`<g class="sc-candle sc-point" data-series="` + strconv.Itoa(si) +
				`" data-series-name="` + esc(s.Name) +
				`" data-x="` + esc(xlabel) +
				`" data-y="` + esc(fmtNum(cl)) +
				`" data-open="` + esc(fmtNum(open)) +
				`" data-high="` + esc(fmtNum(high)) +
				`" data-low="` + esc(fmtNum(low)) +
				`" data-close="` + esc(fmtNum(cl)) +
				`" data-color="` + col +
				`" data-r="3.5" data-r-hover="6" cx="` + f1(cx) +
				`" cy="` + f1(f.ypix(cl)) + `">`)

			switch subtype {
			case "ohlc":
				// Vertical line (high-low range).
				p.WriteString(`<line class="sc-wick" x1="` + f1(cx) + `" y1="` + f1(f.ypix(high)) +
					`" x2="` + f1(cx) + `" y2="` + f1(f.ypix(low)) +
					`" stroke="` + col + `" stroke-width="1"/>`)
				// Open tick.
				p.WriteString(`<line class="sc-open-tick" x1="` + f1(left) + `" y1="` + f1(f.ypix(open)) +
					`" x2="` + f1(cx) + `" y2="` + f1(f.ypix(open)) +
					`" stroke="` + col + `" stroke-width="1"/>`)
				// Close tick.
				p.WriteString(`<line class="sc-close-tick" x1="` + f1(cx) + `" y1="` + f1(f.ypix(cl)) +
					`" x2="` + f1(left+barW) + `" y2="` + f1(f.ypix(cl)) +
					`" stroke="` + col + `" stroke-width="1"/>`)

			case "hlc":
				// Vertical line (high-low range).
				p.WriteString(`<line class="sc-wick" x1="` + f1(cx) + `" y1="` + f1(f.ypix(high)) +
					`" x2="` + f1(cx) + `" y2="` + f1(f.ypix(low)) +
					`" stroke="` + col + `" stroke-width="1"/>`)
				// Close tick only (no open tick).
				p.WriteString(`<line class="sc-close-tick" x1="` + f1(cx) + `" y1="` + f1(f.ypix(cl)) +
					`" x2="` + f1(left+barW) + `" y2="` + f1(f.ypix(cl)) +
					`" stroke="` + col + `" stroke-width="1"/>`)

			case "hollow":
				// Wick.
				p.WriteString(`<line class="sc-wick" x1="` + f1(cx) + `" y1="` + f1(f.ypix(high)) +
					`" x2="` + f1(cx) + `" y2="` + f1(f.ypix(low)) +
					`" stroke="` + col + `" stroke-width="1"/>`)
				// Body: up candles get fill="none", down candles get fill=col.
				yTop := f.ypix(math.Max(open, cl))
				yBot := f.ypix(math.Min(open, cl))
				bodyH := math.Max(math.Abs(yBot-yTop), 1.0)
				bodyX := left
				bodyW := barW
				fill := col
				if isUp {
					fill = "none"
				}
				p.WriteString(`<rect class="sc-body" x="` + f1(bodyX) + `" y="` + f1(yTop) +
					`" width="` + f1(bodyW) + `" height="` + f1(bodyH) +
					`" fill="` + fill + `" stroke="` + col + `"/>`)

			default: // "candlestick", "", or "heikin-ashi" (drawn as candlestick)
				// Wick.
				p.WriteString(`<line class="sc-wick" x1="` + f1(cx) + `" y1="` + f1(f.ypix(high)) +
					`" x2="` + f1(cx) + `" y2="` + f1(f.ypix(low)) +
					`" stroke="` + col + `" stroke-width="1"/>`)
				// Body.
				yTop := f.ypix(math.Max(open, cl))
				yBot := f.ypix(math.Min(open, cl))
				bodyH := math.Max(math.Abs(yBot-yTop), 1.0)
				bodyX := left
				bodyW := barW
				p.WriteString(`<rect class="sc-body" x="` + f1(bodyX) + `" y="` + f1(yTop) +
					`" width="` + f1(bodyW) + `" height="` + f1(bodyH) +
					`" fill="` + col + `" stroke="` + col + `"/>`)
			}

			p.WriteString(`</g>`)
		}

		p.WriteString(`</g>`)
	}
}
