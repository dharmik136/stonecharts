package stonecharts

import (
	"fmt"
	"strings"
)

func scatterOLS(values []float64) (float64, float64) {
	n := len(values)
	if n == 0 {
		return 0, 0
	}
	if n == 1 {
		return values[0], values[0]
	}
	sx, sy, sxx, sxy := 0.0, 0.0, 0.0, 0.0
	for i, y := range values {
		x := float64(i)
		sx += x
		sy += y
		sxx += x * x
		sxy += x * y
	}
	denom := float64(n)*sxx - sx*sx
	if denom == 0 {
		mean := sy / float64(n)
		return mean, mean
	}
	slope := (float64(n)*sxy - sx*sy) / denom
	intercept := (sy - slope*sx) / float64(n)
	return intercept, slope*float64(n-1) + intercept
}

func renderScatterSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Scatter", "point", scatterMarks, false)
}

func scatterMarks(f *cartesianFrame, p *strings.Builder) {
	for si, s := range f.spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		if s.Regression && len(s.Data) >= 1 {
			y0, y1 := scatterOLS(s.Data)
			pts := [][2]float64{{f.xpix(0), f.ypix(y0)}, {f.xpix(len(s.Data)-1), f.ypix(y1)}}
			d := pathD(pts, "")
			p.WriteString(fmt.Sprintf(`<path class="sc-series-line sc-trend" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>`, si, d, st.stroke, fmtNum(s.lineWidth())))
		}
		if s.markerEnabled() {
			radius := s.markerRadius()
			radiusHover := radius + 2.5
			opacity := s.FillOpacity
			if opacity <= 0 {
				opacity = 1
			}
			for i, pt := range s.Data {
				xlabel := fmtNum(float64(i))
				common := fmt.Sprintf(`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s" fill-opacity="%s"`, si, esc(s.Name), esc(xlabel), esc(fmtNum(pt)), st.solid, fmtNum(radius), fmtNum(radiusHover), fmtNum(opacity))
				p.WriteString(markerSVG(s.markerSymbol(), f.xpix(i), f.ypix(pt), radius, common, st.solid, f.theme.MarkerHalo))
			}
		}
		p.WriteString(`</g>`)
	}
}
