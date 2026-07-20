package stonecharts

import (
	"fmt"
	"strings"
)

func bandD(hiPts, loPts [][2]float64) string {
	top := pathD(hiPts, "")
	var b strings.Builder
	b.WriteString(top)
	for i := len(loPts) - 1; i >= 0; i-- {
		b.WriteString(" L" + f1(loPts[i][0]) + " " + f1(loPts[i][1]))
	}
	b.WriteString(" Z")
	return b.String()
}

func renderAreaRangeSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Range area", "point", arearangeMarks, true)
}

func arearangeMarks(f *cartesianFrame, p *strings.Builder) {
	for si, s := range f.spec.Series {
		st := f.styles[si]
		highs := s.Data
		lows := s.Low
		if len(lows) == 0 {
			lows = s.Data
		}
		n := len(highs)
		if len(lows) < n {
			n = len(lows)
		}
		if n == 0 {
			p.WriteString(`</g>`)
			continue
		}
		highs = highs[:n]
		lows = lows[:n]
		hiPts := make([][2]float64, n)
		loPts := make([][2]float64, n)
		for i := range highs {
			hiPts[i] = [2]float64{f.xpix(i), f.ypix(highs[i])}
		}
		for i := range lows {
			loPts[i] = [2]float64{f.xpix(i), f.ypix(lows[i])}
		}
		fillOpacity := s.FillOpacity
		if fillOpacity <= 0 {
			fillOpacity = 0.5
		}
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		p.WriteString(fmt.Sprintf(`<path class="sc-series-range sc-band" data-series="%d" d="%s" fill="%s" fill-opacity="%s" stroke="none"/>`, si, bandD(hiPts, loPts), st.fill, fmtNum(fillOpacity)))
		mk := s.Marker
		if mk == nil || mk.Enabled == nil || *mk.Enabled {
			radius := 3.5
			if mk != nil && mk.Radius != 0 {
				radius = mk.Radius
			}
			radiusHover := radius + 2.5
			for i, pt := range hiPts {
				xlabel := itoa(i)
				if i < len(f.cats) {
					xlabel = f.cats[i]
				}
				common := fmt.Sprintf(`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-low="%s" data-high="%s" data-y="%s–%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(xlabel), esc(fmtNum(lows[i])), esc(fmtNum(highs[i])), esc(fmtNum(lows[i])), esc(fmtNum(highs[i])), st.solid, fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(markerSVG("circle", pt[0], pt[1], radius, common, st.solid, f.theme.MarkerHalo))
			}
		}
		p.WriteString(`</g>`)
	}
}
