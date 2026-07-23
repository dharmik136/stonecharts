package stonecharts

import (
	"fmt"
	"strconv"
	"strings"
)

// renderAreaSVG is a one-line delegation to the shared cartesian frame:
// point x-scale, include-zero value axis, a11y noun "Area".
func renderAreaSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Area", "point", areaMarks, true)
}

func areaTopPath(pts [][2]float64, step string) string {
	return pathD(pts, step)
}

func areaPath(topPts, bottomPts [][2]float64, step string) string {
	topD := areaTopPath(topPts, step)
	bottomRev := make([][2]float64, len(bottomPts))
	for i := range bottomPts {
		bottomRev[i] = bottomPts[len(bottomPts)-1-i]
	}
	bottomD := areaTopPath(bottomRev, step)
	if strings.HasPrefix(bottomD, "M") {
		bottomD = "L" + bottomD[1:]
	}
	return topD + " " + bottomD + " Z"
}

func areaSeriesFill(st seriesStyle) string {
	if st.areaFill != "" {
		return st.areaFill
	}
	if strings.HasPrefix(st.stroke, "url(") {
		return st.stroke
	}
	return st.solid
}

func areaMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	stacked := f.stacking == "normal" || f.stacking == "percent"
	totals := make([]float64, f.n)
	if f.stacking == "percent" {
		for _, s := range f.spec.Series {
			for i, v := range s.Data {
				if i < f.n {
					totals[i] += v
				}
			}
		}
	}

	running := make([]float64, f.n)
	for si, s := range f.spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		rawVals := make([]float64, 0, len(s.Data))
		for i, v := range s.Data {
			if i >= f.n {
				break
			}
			rawVals = append(rawVals, v)
		}
		topPts := make([][2]float64, len(rawVals))

		if stacked {
			vals := make([]float64, len(rawVals))
			for i, raw := range rawVals {
				if f.stacking == "percent" {
					total := totals[i]
					if total != 0 {
						vals[i] = raw / total * 100.0
					}
				} else {
					vals[i] = raw
				}
			}
			bottomPts := make([][2]float64, len(rawVals))
			for i := range vals {
				bottomPts[i] = [2]float64{f.xpix(i), f.ypix(running[i])}
				running[i] += vals[i]
				topPts[i] = [2]float64{f.xpix(i), f.ypix(running[i])}
			}
			if len(topPts) > 0 {
				fillOp := st.areaOp
				if fillOp == "" {
					fillOp = ` fill-opacity="0.75"`
				}
				p.WriteString(fmt.Sprintf(
					`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
					si, areaPath(topPts, bottomPts, s.Step), areaSeriesFill(st), fillOp))
				lineDash := dashArray(s.DashStyle)
				lineDashAttr := ""
				if lineDash != "" {
					lineDashAttr = ` stroke-dasharray="` + lineDash + `"`
				}
				p.WriteString(fmt.Sprintf(
					`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
					si, areaTopPath(topPts, s.Step), st.stroke, fmtNum(s.lineWidth()), lineDashAttr))
			}
		} else {
			bottomPts := make([][2]float64, len(rawVals))
			for i, raw := range rawVals {
				topPts[i] = [2]float64{f.xpix(i), f.ypix(raw)}
				bottomPts[i] = [2]float64{f.xpix(i), f.ypix(0.0)}
			}
			if len(topPts) > 0 {
				base := f.ypix(0.0)
				areaD := areaTopPath(topPts, s.Step) + " L" + f1(topPts[len(topPts)-1][0]) + " " + f1(base) +
					" L" + f1(topPts[0][0]) + " " + f1(base) + " Z"
				fillOp := st.areaOp
				if fillOp == "" {
					fillOp = ` fill-opacity="0.75"`
				}
				p.WriteString(fmt.Sprintf(
					`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
					si, areaD, areaSeriesFill(st), fillOp))
				lineDash := dashArray(s.DashStyle)
				lineDashAttr := ""
				if lineDash != "" {
					lineDashAttr = ` stroke-dasharray="` + lineDash + `"`
				}
				p.WriteString(fmt.Sprintf(
					`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
					si, areaTopPath(topPts, s.Step), st.stroke, fmtNum(s.lineWidth()), lineDashAttr))
			}
		}

		mk := s.Marker
		if mk == nil || mk.Enabled == nil || *mk.Enabled {
			radius := s.markerRadius()
			radiusHover := radius + 2.5
			symbol := s.markerSymbol()
			for i, pt := range topPts {
				xlabel := strconv.Itoa(i)
				if i < len(f.cats) {
					xlabel = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(xlabel), esc(fmtNum(rawVals[i])), st.solid, fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, st.solid, f.theme.MarkerHalo))
			}
		}
		p.WriteString(`</g>`)
	}
}
