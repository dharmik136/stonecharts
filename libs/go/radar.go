package stonecharts

import (
	"fmt"
	"math"
	"strings"
	"unicode/utf8"
)

func renderRadarSVG(spec *ChartSpec) string {
	W, H := int(spec.Width), int(spec.Height)
	theme := spec.theme
	if theme == nil {
		t := lightTheme()
		theme = &t
	}
	palette := theme.Palette
	cid := esc(spec.ID)
	_ = cid

	a11yAttr := ""
	a11yDesc := ""
	if spec.a11yOn() {
		sum := esc(a11ySummary(spec, "Radar"))
		a11yAttr = fmt.Sprintf(` role="img" aria-label="%s"`, sum)
		a11yDesc = fmt.Sprintf("<desc>%s</desc>", sum)
	}

	mTop := 20.0
	if spec.Title != "" {
		mTop += 26
	}
	if spec.Subtitle != "" {
		mTop += 18
	}
	mLeft := 22.0
	mRight := 22.0
	mBottom := 28.0
	if spec.legendOn() {
		mBottom += 18
	}
	if spec.Layout != nil && spec.Layout.Margin != nil {
		m := spec.Layout.Margin
		if m.Top != nil {
			mTop = *m.Top
		}
		if m.Left != nil {
			mLeft = *m.Left
		}
		if m.Right != nil {
			mRight = *m.Right
		}
		if m.Bottom != nil {
			mBottom = *m.Bottom
		}
	}

	plotX, plotY := mLeft, mTop
	plotW, plotH := float64(W)-mLeft-mRight, float64(H)-mTop-mBottom

	cats := spec.XAxis.Categories
	nAxes := len(cats)
	if nAxes < 3 {
		nAxes = 3
	}

	yMin := 0.0
	if spec.YAxis.Min != nil {
		yMin = *spec.YAxis.Min
	}
	yMax := 0.0
	hasYMax := false
	if spec.YAxis.Max != nil {
		yMax = *spec.YAxis.Max
		hasYMax = true
	}
	if !hasYMax {
		for _, s := range spec.Series {
			for _, v := range s.Data {
				if v > yMax {
					yMax = v
				}
			}
		}
	}
	if yMax <= yMin {
		yMax = yMin + 100
	}

	labelMargin := 40.0
	cx := plotX + plotW/2
	cy := plotY + plotH/2
	rMax := plotW / 2
	if plotH/2 < rMax {
		rMax = plotH / 2
	}
	rMax -= labelMargin

	nRings := 5

	axisAngle := func(i int) float64 {
		return -math.Pi/2 + float64(i)*2*math.Pi/float64(nAxes)
	}
	pointAt := func(angle, r float64) (float64, float64) {
		return cx + r*math.Cos(angle), cy + r*math.Sin(angle)
	}

	var p strings.Builder

	font := `font-family="Segoe UI, Helvetica, Arial, sans-serif"`
	if spec.Responsive {
		p.WriteString(fmt.Sprintf(
			`<svg class="sc-chart"%s xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" width="100%%" %s>`,
			a11yAttr, W, H, font))
	} else {
		p.WriteString(fmt.Sprintf(
			`<svg class="sc-chart"%s xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" %s>`,
			a11yAttr, W, H, W, H, font))
	}

	if a11yDesc != "" {
		p.WriteString(a11yDesc)
	}

	if theme.Background != "" {
		p.WriteString(fmt.Sprintf(
			`<rect class="sc-bg" x="0" y="0" width="%d" height="%d" fill="%s"/>`,
			W, H, theme.Background))
	}

	ty := 26
	if spec.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-title" x="%s" y="%d" text-anchor="middle" font-size="17" font-weight="600" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, theme.TitleColor, esc(spec.Title)))
		ty += 20
	}
	if spec.Subtitle != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-subtitle" x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, theme.SubtitleColor, esc(spec.Subtitle)))
	}

	p.WriteString(fmt.Sprintf(
		`<line class="sc-crosshair" x1="0" y1="%s" x2="0" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>`,
		f1(plotY), f1(plotY+plotH), theme.CrosshairColor))

	// Grid rings (spiderweb)
	for level := 0; level < nRings; level++ {
		frac := float64(level+1) / float64(nRings)
		r := rMax * frac
		var pts strings.Builder
		for i := 0; i < nAxes; i++ {
			if i > 0 {
				pts.WriteString(" ")
			}
			px, py := pointAt(axisAngle(i), r)
			pts.WriteString(fmt.Sprintf("%s,%s", f1(px), f1(py)))
		}
		p.WriteString(fmt.Sprintf(
			`<polygon class="sc-radar-ring" data-level="%d" points="%s" fill="none" stroke="%s" stroke-width="1"/>`,
			level, pts.String(), theme.GridColor))
	}

	// Radial axis lines
	for i := 0; i < nAxes; i++ {
		ex, ey := pointAt(axisAngle(i), rMax)
		p.WriteString(fmt.Sprintf(
			`<line class="sc-radar-axis" data-index="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
			i, f1(cx), f1(cy), f1(ex), f1(ey), theme.GridColor))
	}

	// Category labels
	for i := 0; i < nAxes; i++ {
		angle := axisAngle(i)
		lx, ly := pointAt(angle, rMax+12)
		cosA := math.Cos(angle)
		anchor := "middle"
		if cosA > 0.01 {
			anchor = "start"
		} else if cosA < -0.01 {
			anchor = "end"
		}
		label := fmt.Sprintf("%d", i)
		if i < len(cats) {
			label = cats[i]
		}
		p.WriteString(fmt.Sprintf(
			`<text class="sc-radar-label" data-index="%d" x="%s" y="%s" text-anchor="%s" dominant-baseline="central" font-size="11" fill="%s">%s</text>`,
			i, f1(lx), f1(ly), anchor, theme.AxisLabelColor, esc(label)))
	}

	// Tick labels along first axis
	for level := 0; level < nRings; level++ {
		frac := float64(level+1) / float64(nRings)
		tickVal := yMin + frac*(yMax-yMin)
		tickR := rMax * frac
		tx, ty2 := pointAt(axisAngle(0), tickR)
		p.WriteString(fmt.Sprintf(
			`<text class="sc-radar-tick" data-value="%s" x="%s" y="%s" font-size="9" fill="%s">%s</text>`,
			esc(fmtNum(tickVal)), f1(tx+4), f1(ty2-2), theme.AxisLabelColor, esc(fmtNum(tickVal))))
	}

	// Series polygons and vertices
	for si, s := range spec.Series {
		color := palette[si%len(palette)]
		grad, solidHex := s.colorSpec()
		if grad != nil {
			if len(grad.Stops) > 0 {
				color = grad.Stops[0].Color
			}
		} else if solidHex != "" {
			color = solidHex
		}
		color = esc(color)

		fillOpacity := s.FillOpacity

		type vertex struct{ x, y float64 }
		vertices := make([]vertex, nAxes)
		for j := 0; j < nAxes; j++ {
			v := 0.0
			if j < len(s.Data) {
				v = s.Data[j]
			}
			frac := (v - yMin) / (yMax - yMin)
			if frac < 0 {
				frac = 0
			}
			if frac > 1 {
				frac = 1
			}
			r := rMax * frac
			vx, vy := pointAt(axisAngle(j), r)
			vertices[j] = vertex{vx, vy}
		}

		var pathD strings.Builder
		for k, vt := range vertices {
			if k == 0 {
				pathD.WriteString(fmt.Sprintf("M %s %s", f1(vt.x), f1(vt.y)))
			} else {
				pathD.WriteString(fmt.Sprintf(" L %s %s", f1(vt.x), f1(vt.y)))
			}
		}
		pathD.WriteString(" Z")

		fillAttr := `fill="none"`
		opacityAttr := ""
		if fillOpacity > 0 {
			fillAttr = fmt.Sprintf(`fill="%s"`, color)
			opacityAttr = fmt.Sprintf(` fill-opacity="%g"`, fillOpacity)
		}

		p.WriteString(fmt.Sprintf(
			`<path class="sc-radar-poly sc-point" data-series="%d" data-series-name="%s" data-color="%s" d="%s" %s%s stroke="%s" stroke-width="2"/>`,
			si, esc(s.Name), color, pathD.String(), fillAttr, opacityAttr, color))

		for j, vt := range vertices {
			v := 0.0
			if j < len(s.Data) {
				v = s.Data[j]
			}
			p.WriteString(fmt.Sprintf(
				`<circle class="sc-radar-dot sc-point" data-series="%d" data-index="%d" data-y="%s" cx="%s" cy="%s" r="4" fill="%s"/>`,
				si, j, esc(fmtNum(v)), f1(vt.x), f1(vt.y), color))
		}
	}

	// Legend
	if spec.legendOn() && len(spec.Series) > 0 {
		gap := 22.0
		est := make([]float64, len(spec.Series))
		for i, s := range spec.Series {
			est[i] = float64(utf8.RuneCountInString(s.Name)*7 + 26)
		}
		totalW := 0.0
		for _, e := range est {
			totalW += e
		}
		totalW += gap * float64(len(est)-1)
		lx := plotX + (plotW-totalW)/2
		ly := float64(H - 10)
		p.WriteString(`<g class="sc-legend">`)
		for si, s := range spec.Series {
			color := palette[si%len(palette)]
			grad, solidHex := s.colorSpec()
			if grad != nil {
				if len(grad.Stops) > 0 {
					color = grad.Stops[0].Color
				}
			} else if solidHex != "" {
				color = solidHex
			}
			color = esc(color)
			p.WriteString(fmt.Sprintf(`<g class="sc-legend-item" data-series="%d">`, si))
			p.WriteString(fmt.Sprintf(
				`<rect x="%s" y="%s" width="14" height="4" rx="2" fill="%s"/>`,
				f1(lx), f1(ly-9), color))
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" font-size="12" fill="%s">%s</text>`,
				f1(lx+20), f1(ly-2), theme.LegendTextColor, esc(s.Name)))
			p.WriteString("</g>")
			lx += est[si] + gap
		}
		p.WriteString("</g>")
	}

	p.WriteString("</svg>")
	return p.String()
}

func radarDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	cats := spec.XAxis.Categories
	n := 0
	for _, s := range spec.Series {
		if len(s.Data) > n {
			n = len(s.Data)
		}
	}
	b.WriteString("<thead><tr><td></td>")
	for i := 0; i < n; i++ {
		label := fmt.Sprintf("%d", i)
		if i < len(cats) {
			label = cats[i]
		}
		b.WriteString(`<th scope="col">` + esc(label) + `</th>`)
	}
	b.WriteString("</tr></thead><tbody>")
	for _, s := range spec.Series {
		b.WriteString(`<tr><th scope="row">` + esc(s.Name) + `</th>`)
		for i := 0; i < n; i++ {
			if i < len(s.Data) {
				b.WriteString("<td>" + esc(fmtNum(s.Data[i])) + "</td>")
			} else {
				b.WriteString("<td></td>")
			}
		}
		b.WriteString("</tr>")
	}
	b.WriteString("</tbody></table>")
	return b.String()
}
