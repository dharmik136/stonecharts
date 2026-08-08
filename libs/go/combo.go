package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

const comboPad = 0.2

func renderComboSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Combo", "band", comboMarks, true)
}

func comboSeriesKind(s *Series) string {
	if s.Type == "line" {
		return "line"
	}
	return "column"
}

func comboYpix(f *cartesianFrame, s *Series) func(float64) float64 {
	if s.YAxis == 1 && f.secondaryAxis != nil {
		return f.ypix2
	}
	return f.ypix
}

func comboMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	bandWidth := f.bandWidth()
	groupW := bandWidth * (1 - comboPad)
	stacked := f.stacking == "normal" || f.stacking == "percent"

	kCol := 0
	for si := range f.spec.Series {
		if comboSeriesKind(&f.spec.Series[si]) == "column" {
			kCol++
		}
	}
	kSlots := kCol
	if stacked || !f.spec.groupingOn() {
		kSlots = 1
	}
	if kSlots <= 0 {
		kSlots = 1
	}
	barW := groupW / float64(kSlots)

	kcMap := make(map[int]int)
	kc := 0
	for si := range f.spec.Series {
		if comboSeriesKind(&f.spec.Series[si]) == "column" {
			kcMap[si] = kc
			kc++
		}
	}

	totals := make([]float64, f.n)
	if stacked {
		for si := range f.spec.Series {
			if comboSeriesKind(&f.spec.Series[si]) != "column" {
				continue
			}
			for i, v := range f.spec.Series[si].Data {
				if i < f.n {
					totals[i] += v
				}
			}
		}
	}

	positive := make([]float64, f.n)
	negative := make([]float64, f.n)

	for si := range f.spec.Series {
		s := &f.spec.Series[si]
		if comboSeriesKind(s) == "line" {
			emitComboLineSeries(f, p, si, s)
		} else {
			emitComboColumnSeries(f, p, si, s, groupW, barW, kcMap, stacked, totals, positive, negative)
		}
	}
}

func emitComboColumnSeries(f *cartesianFrame, p *strings.Builder, si int, s *Series, groupW, barW float64, kcMap map[int]int, stacked bool, totals, positive, negative []float64) {
	st := f.styles[si]
	ypix := comboYpix(f, s)
	baseline := ypix(0.0)
	kc := kcMap[si]

	p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
	for i, raw := range s.Data {
		if i >= f.n {
			break
		}
		cxBand := f.xpix(float64(i))
		var left, y, h float64
		if stacked {
			left = cxBand - groupW/2
			value := raw
			if f.stacking == "percent" {
				total := totals[i]
				if total == 0 {
					value = 0
				} else {
					value = raw / total * 100.0
				}
			}
			var bottomV, topV float64
			if value >= 0 {
				bottomV = positive[i]
				topV = bottomV + value
				positive[i] = topV
			} else {
				bottomV = negative[i]
				topV = bottomV + value
				negative[i] = topV
			}
			y0 := ypix(bottomV)
			y1 := ypix(topV)
			y = math.Min(y0, y1)
			h = math.Abs(y0 - y1)
		} else {
			slot := 0
			if f.spec.groupingOn() {
				slot = kc
			}
			left = cxBand - groupW/2 + barW*float64(slot)
			yv := ypix(raw)
			y = math.Min(baseline, yv)
			h = math.Abs(baseline - yv)
		}
		xlabel := strconv.Itoa(i)
		if i < len(f.cats) {
			xlabel = f.cats[i]
		}
		cx := left + barW/2
		common := fmt.Sprintf(
			`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
			si, esc(s.Name), esc(xlabel), esc(fmtNum(raw)), st.solid)
		p.WriteString(fmt.Sprintf(
			`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
			common, f1(cx), f1(y), f1(left), f1(y), f1(barW), f1(h), st.fill))
	}
	p.WriteString(`</g>`)
}

func emitComboLineSeries(f *cartesianFrame, p *strings.Builder, si int, s *Series) {
	st := f.styles[si]
	ypix := comboYpix(f, s)
	theme := f.theme
	color := st.solid
	pts := make([][2]float64, len(s.Data))
	for i, v := range s.Data {
		pts[i] = [2]float64{f.xpix(float64(i)), ypix(v)}
	}
	var d string
	if s.Curve == "monotone" {
		d = splineD(pts)
	} else {
		d = pathD(pts, s.Step)
	}
	lineDashAttr := ""
	if da := dashArray(s.DashStyle); da != "" {
		lineDashAttr = ` stroke-dasharray="` + da + `"`
	}
	p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
	if st.areaFill != "" && len(pts) > 0 {
		base := ypix(0.0)
		areaD := d + " L" + f1(pts[len(pts)-1][0]) + " " + f1(base) +
			" L" + f1(pts[0][0]) + " " + f1(base) + " Z"
		p.WriteString(fmt.Sprintf(
			`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
			si, areaD, st.areaFill, st.areaOp))
	}
	p.WriteString(fmt.Sprintf(
		`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
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
			common := fmt.Sprintf(
				`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
				si, esc(s.Name), esc(xlabel), esc(fmtNum(s.Data[i])), color, fmtNum(radius), fmtNum(radiusHover))
			p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, color, theme.MarkerHalo, 1.0))
		}
	}
	p.WriteString(`</g>`)
}
