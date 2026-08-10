package stonecharts

import (
	"fmt"
	"math"
	"strings"
)

func renderXRangeSVG(spec *ChartSpec) string {
	laneCats := spec.YAxis.Categories
	laneCount := len(laneCats)
	spec.XAxis.Categories = laneCats

	for i := range spec.Series {
		s := &spec.Series[i]
		for len(s.Data) < laneCount {
			s.Data = append(s.Data, 0.0)
		}
	}

	allTimes := []float64{}
	for _, s := range spec.Series {
		for _, sp := range s.Spans {
			allTimes = append(allTimes, sp.X, sp.X2)
		}
	}
	if spec.YAxis.Min == nil && len(allTimes) > 0 {
		if spec.XAxis.Min != nil {
			v := *spec.XAxis.Min
			spec.YAxis.Min = &v
		} else {
			v := allTimes[0]
			for _, t := range allTimes[1:] {
				if t < v {
					v = t
				}
			}
			spec.YAxis.Min = &v
		}
	}
	if spec.YAxis.Max == nil && len(allTimes) > 0 {
		if spec.XAxis.Max != nil {
			v := *spec.XAxis.Max
			spec.YAxis.Max = &v
		} else {
			v := allTimes[0]
			for _, t := range allTimes[1:] {
				if t > v {
					v = t
				}
			}
			spec.YAxis.Max = &v
		}
	}

	return renderCartesian(spec, "X-range", "band", xrangeMarks, false, "horizontal")
}

const xrPAD = 0.2

func xrangeMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	laneHeight := f.plotH / float64(f.n)
	barThickness := laneHeight * (1 - xrPAD)

	ypixBand := func(j int) float64 {
		return f.plotY + laneHeight*float64(j) + laneHeight/2
	}

	xval := func(v float64) float64 {
		return f.valuePix(v)
	}

	cats := f.cats

	type spanRef struct {
		endX float64
		cy   float64
	}
	spanIndex := map[string]spanRef{}
	for _, s := range f.spec.Series {
		for _, sp := range s.Spans {
			if sp.ID != "" {
				spanIndex[sp.ID] = spanRef{xval(sp.X2), ypixBand(sp.Y)}
			}
		}
	}

	for si, s := range f.spec.Series {
		st := f.styles[si]
		fill := st.fill

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		for _, sp := range s.Spans {
			start := sp.X
			end := sp.X2
			lane := sp.Y

			xLeft := xval(math.Min(start, end))
			xRight := xval(math.Max(start, end))
			w := xRight - xLeft
			cy := ypixBand(lane)
			cx := xval((start + end) / 2)

			laneLabel := fmt.Sprintf("%d", lane)
			if lane < len(cats) {
				laneLabel = cats[lane]
			}
			duration := end - start

			dataAttrs := fmt.Sprintf(
				`data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-start="%s" data-end="%s" data-lane="%s" data-duration="%s" data-color="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s"`,
				si, esc(s.Name), esc(laneLabel), esc(fmtNum(start)),
				esc(fmtNum(start)), esc(fmtNum(end)),
				esc(laneLabel), esc(fmtNum(duration)),
				st.solid, fmtNum(3.5), fmtNum(6),
				f1(cx), f1(cy))

			if sp.Milestone {
				h := barThickness / 2
				points := fmt.Sprintf("%s,%s %s,%s %s,%s %s,%s",
					f1(cx), f1(cy-h), f1(cx+h), f1(cy), f1(cx), f1(cy+h), f1(cx-h), f1(cy))
				p.WriteString(fmt.Sprintf(`<polygon class="sc-milestone sc-point" %s points="%s" fill="%s"/>`, dataAttrs, points, fill))
			} else {
				if w < 1.0 {
					w = 1.0
				}
				top := cy - barThickness/2
				p.WriteString(fmt.Sprintf(`<rect class="sc-span sc-point" %s x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
					dataAttrs, f1(xLeft), f1(top), f1(w), f1(barThickness), fill))
			}

			for _, depID := range sp.Dependency {
				if pred, ok := spanIndex[depID]; ok {
					predX := pred.endX
					predY := pred.cy
					thisX := xval(start)
					thisY := cy
					midX := (predX + thisX) / 2
					ah := 4.0
					d := fmt.Sprintf("M%s %s L%s %s L%s %s L%s %s M%s %s L%s %s L%s %s",
						f1(predX), f1(predY), f1(midX), f1(predY),
						f1(midX), f1(thisY), f1(thisX), f1(thisY),
						f1(thisX-ah), f1(thisY-ah), f1(thisX), f1(thisY),
						f1(thisX-ah), f1(thisY+ah))
					p.WriteString(fmt.Sprintf(`<path class="sc-dependency" d="%s" fill="none" stroke="%s" stroke-width="1" opacity="0.5"/>`,
						d, st.solid))
				}
			}
		}

		p.WriteString(`</g>`)
	}
}
