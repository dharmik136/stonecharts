package stonecharts

import (
	"fmt"
	"strings"
)

func renderStreamgraphSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Streamgraph", "point", streamgraphMarks, false)
}

func streamgraphMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	K := len(f.spec.Series)
	N := f.n

	baseline := f.sgBaseline
	cumBottom := f.sgCumBottom
	cumTop := f.sgCumTop

	allVals := make([][]float64, K)
	for k := 0; k < K; k++ {
		vals := make([]float64, 0, N)
		for i, v := range f.spec.Series[k].Data {
			if i >= N {
				break
			}
			vals = append(vals, v)
		}
		allVals[k] = vals
	}

	for si := 0; si < K; si++ {
		s := f.spec.Series[si]
		st := f.styles[si]
		rawVals := allVals[si]

		topPts := make([][2]float64, len(rawVals))
		bottomPts := make([][2]float64, len(rawVals))
		for i := range rawVals {
			x := f.xpix(float64(i))
			topY := f.ypix(baseline[i] + cumTop[si][i])
			botY := f.ypix(baseline[i] + cumBottom[si][i])
			topPts[i] = [2]float64{x, topY}
			bottomPts[i] = [2]float64{x, botY}
		}

		fmt.Fprintf(p, `<g class="sc-series" data-series="%d">`, si)

		if len(topPts) > 0 {
			topD := areaTopPath(topPts, "", s.Curve)
			bottomRev := make([][2]float64, len(bottomPts))
			for i := range bottomPts {
				bottomRev[i] = bottomPts[len(bottomPts)-1-i]
			}
			bottomD := areaTopPath(bottomRev, "", s.Curve)
			if strings.HasPrefix(bottomD, "M") {
				bottomD = "L" + bottomD[1:]
			}
			ribbonD := topD + " " + bottomD + " Z"

			fill := st.fill
			fillOp := st.areaOp
			fmt.Fprintf(p,
				`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
				si, ribbonD, fill, fillOp)
		}

		if s.markerEnabled() {
			radius := s.markerRadius()
			radiusHover := radius + 2.5
			symbol := s.markerSymbol()
			for i, pt := range topPts {
				xlabel := fmt.Sprintf("%d", i)
				if i < len(f.cats) {
					xlabel = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(xlabel), esc(fmtNum(rawVals[i])), st.solid, fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, st.solid, f.theme.MarkerHalo, 1.0))
			}
		}
		p.WriteString(`</g>`)
	}
}
