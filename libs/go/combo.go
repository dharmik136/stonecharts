package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

const comboPad = 0.2

// renderComboSVG composes column and line series on one shared cartesian plot.
func renderComboSVG(spec *ChartSpec) string {
	f := buildFrame(spec, "Combo", "band", true, "vertical")
	f.secondaryAxis = spec.SecondaryYAxis
	if f.secondaryAxis != nil && f.secondaryAxis.Title != "" {
		f.plotW -= 40
	}
	applyComboDomains(f)
	var p strings.Builder
	chromeHead(f, &p)
	comboMarks(f, &p)
	chromeTail(f, &p)
	return p.String()
}

func seriesKind(s *Series) string {
	if s.Type == "" {
		return "column"
	}
	return s.Type
}

func seriesAxis(f *cartesianFrame, s *Series) int {
	if s.YAxis == 1 && f.secondaryAxis != nil {
		return 1
	}
	return 0
}

func seriesPix(f *cartesianFrame, s *Series, v float64) float64 {
	if seriesAxis(f, s) == 1 {
		return f.ypix2(v)
	}
	return f.ypix(v)
}

func applyComboDomains(f *cartesianFrame) {
	lo, hi := axisDomain(f, 0)
	lo, hi, f.yTicks = niceTicks(lo, hi, 6)
	f.yMin, f.yMax = lo, hi
	if f.secondaryAxis != nil {
		lo2, hi2 := axisDomain(f, 1)
		lo2, hi2, f.y2Ticks = niceTicks(lo2, hi2, 6)
		f.y2Min, f.y2Max = lo2, hi2
	} else {
		f.y2Min, f.y2Max = 0, 0
		f.y2Ticks = nil
	}
}

func axisDomain(f *cartesianFrame, axis int) (float64, float64) {
	series := []Series{}
	for i := range f.spec.Series {
		if seriesAxis(f, &f.spec.Series[i]) == axis {
			series = append(series, f.spec.Series[i])
		}
	}
	if len(series) == 0 {
		return 0, 0
	}
	values := []float64{}
	for _, s := range series {
		values = append(values, s.Data...)
	}
	lo, hi := 0.0, 0.0
	if f.spec.Stacking == "percent" {
		lo, hi = 0, 100
	} else if f.spec.Stacking == "normal" {
		pos := make([]float64, f.n)
		neg := make([]float64, f.n)
		for _, s := range series {
			if seriesKind(&s) != "column" {
				continue
			}
			for i, v := range s.Data {
				if i >= f.n {
					break
				}
				if v >= 0 {
					pos[i] += v
				} else {
					neg[i] += v
				}
			}
		}
		lo = 0
		hi = 0
		for _, v := range neg {
			if v < lo {
				lo = v
			}
		}
		for _, v := range pos {
			if v > hi {
				hi = v
			}
		}
	} else {
		if len(values) > 0 {
			lo = values[0]
			hi = values[0]
			for _, v := range values[1:] {
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
			if 0 < lo {
				lo = 0
			}
			if 0 > hi {
				hi = 0
			}
		}
	}
	for _, s := range series {
		if seriesKind(&s) != "line" {
			continue
		}
		for _, v := range s.Data {
			if v < lo {
				lo = v
			}
			if v > hi {
				hi = v
			}
		}
	}
	return lo, hi
}

func comboMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}
	columnSeries := []int{}
	for i := range f.spec.Series {
		if seriesKind(&f.spec.Series[i]) != "line" {
			columnSeries = append(columnSeries, i)
		}
	}
	colRank := map[int]int{}
	for rank, si := range columnSeries {
		colRank[si] = rank
	}
	bandWidth := f.bandWidth()
	groupW := bandWidth * (1 - comboPad)
	stacked := f.stacking == "normal" || f.stacking == "percent"
	kSlots := len(columnSeries)
	if stacked || !f.spec.groupingOn() {
		kSlots = 1
	}
	if kSlots <= 0 {
		kSlots = 1
	}
	barW := groupW / float64(kSlots)
	positive := make([]float64, f.n)
	negative := make([]float64, f.n)
	totals := make([]float64, f.n)
	if stacked {
		for _, si := range columnSeries {
			s := f.spec.Series[si]
			for i, v := range s.Data {
				if i < f.n {
					totals[i] += v
				}
			}
		}
	}
	for si := range f.spec.Series {
		s := &f.spec.Series[si]
		st := f.styles[si]
		kind := seriesKind(s)
		axis := seriesAxis(f, s)
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		if kind == "line" {
			pts := make([][2]float64, len(s.Data))
			for i, v := range s.Data {
				pts[i] = [2]float64{f.xpix(i), seriesPix(f, s, v)}
			}
			d := pathD(pts, s.Step)
			if s.Curve == "monotone" {
				d = splineD(pts)
			}
			lineDashAttr := ""
			if da := dashArray(s.DashStyle); da != "" {
				lineDashAttr = ` stroke-dasharray="` + da + `"`
			}
			if st.areaFill != "" && len(pts) > 0 {
				base := f.ypix(0.0)
				if axis == 1 {
					base = f.ypix2(0.0)
				}
				areaD := d + " L" + f1(pts[len(pts)-1][0]) + " " + f1(base) +
					" L" + f1(pts[0][0]) + " " + f1(base) + " Z"
				p.WriteString(fmt.Sprintf(`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
					si, areaD, st.areaFill, st.areaOp))
			}
			p.WriteString(fmt.Sprintf(`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
				si, d, st.stroke, fmtNum(s.lineWidth()), lineDashAttr))
			if s.markerEnabled() {
				radius := s.markerRadius()
				radiusHover := radius + 2.5
				symbol := s.markerSymbol()
				for i, pt := range pts {
					xlabel := strconv.Itoa(i)
					if i < len(f.cats) {
						xlabel = f.cats[i]
					}
					common := fmt.Sprintf(`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
						si, esc(s.Name), esc(xlabel), esc(fmtNum(s.Data[i])), st.solid, fmtNum(radius), fmtNum(radiusHover))
					p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, st.solid, f.theme.MarkerHalo))
				}
			}
		} else {
			for i, raw := range s.Data {
				if i >= f.n {
					break
				}
				cyBand := f.bandCenter(i)
				var top, x, w, cx, height float64
				if stacked {
					top = cyBand - groupW/2
					value := raw
					if f.stacking == "percent" {
						total := totals[i]
						if total == 0 {
							value = 0
						} else {
							value = raw / total * 100.0
						}
					}
					var leftV, rightV float64
					if value >= 0 {
						leftV = positive[i]
						rightV = leftV + value
						positive[i] = rightV
					} else {
						leftV = negative[i]
						rightV = leftV + value
						negative[i] = rightV
					}
					x0 := f.ypix(leftV)
					x1 := f.ypix(rightV)
					if axis == 1 {
						x0 = f.ypix2(leftV)
						x1 = f.ypix2(rightV)
					}
					x = math.Min(x0, x1)
					w = math.Abs(x0 - x1)
					cx = x1
					height = groupW
				} else {
					slot := colRank[si]
					if !f.spec.groupingOn() {
						slot = 0
					}
					top = cyBand - groupW/2 + barW*float64(slot)
					xv := f.ypix(raw)
					baseline := f.ypix(0.0)
					if axis == 1 {
						xv = f.ypix2(raw)
						baseline = f.ypix2(0.0)
					}
					x = math.Min(baseline, xv)
					w = math.Abs(baseline - xv)
					cx = xv
					height = barW
				}
				xlabel := strconv.Itoa(i)
				if i < len(f.cats) {
					xlabel = f.cats[i]
				}
				cy := top + height/2
				common := fmt.Sprintf(`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
					si, esc(s.Name), esc(xlabel), esc(fmtNum(raw)), st.solid)
				p.WriteString(fmt.Sprintf(`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
					common, f1(cx), f1(cy), f1(x), f1(top), f1(w), f1(height), st.fill))
			}
		}
		p.WriteString(`</g>`)
	}
}
