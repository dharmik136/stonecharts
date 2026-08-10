package stonecharts

import (
	"fmt"
	"math"
	"strings"
	"unicode/utf8"
)

func renderRadialBarSVG(spec *ChartSpec) string {
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
		sum := esc(a11ySummary(spec, "Radial bar"))
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
	nCats := len(cats)
	if nCats < 1 {
		nCats = 1
	}

	labelMargin := 40.0
	cx := plotX + plotW/2
	cy := plotY + plotH/2
	rMax := plotW / 2
	if plotH/2 < rMax {
		rMax = plotH / 2
	}
	rMax -= labelMargin
	rInnerMargin := rMax * 0.3

	yMax := 0.0
	hasYMax := false
	if spec.YAxis.Max != nil {
		yMax = *spec.YAxis.Max
		hasYMax = true
	}
	if !hasYMax {
		for j := 0; j < nCats; j++ {
			stack := 0.0
			for _, s := range spec.Series {
				v := 0.0
				if j < len(s.Data) {
					v = s.Data[j]
				}
				if v > 0 {
					stack += v
				}
			}
			if stack > yMax {
				yMax = stack
			}
		}
	}
	if yMax <= 0 {
		yMax = 100
	}

	bandF := (rMax - rInnerMargin) / float64(nCats)
	trackGap := 2.0

	pointAt := func(angle, r float64) (float64, float64) {
		return cx + r*math.Cos(angle), cy + r*math.Sin(angle)
	}

	arcPath := func(rOut, rIn, aStart, aEnd float64) string {
		sweep := aEnd - aStart
		large := 0
		if math.Abs(sweep) > math.Pi {
			large = 1
		}
		ox1, oy1 := pointAt(aStart, rOut)
		ox2, oy2 := pointAt(aEnd, rOut)
		ix2, iy2 := pointAt(aEnd, rIn)
		ix1, iy1 := pointAt(aStart, rIn)
		return fmt.Sprintf("M %s %s A %s %s 0 %d 1 %s %s L %s %s A %s %s 0 %d 0 %s %s Z",
			f1(ox1), f1(oy1),
			f1(rOut), f1(rOut), large, f1(ox2), f1(oy2),
			f1(ix2), f1(iy2),
			f1(rIn), f1(rIn), large, f1(ix1), f1(iy1))
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

	// Angular grid lines at 0%, 25%, 50%, 75%
	for _, pct := range []int{0, 25, 50, 75} {
		angle := -math.Pi/2 + (float64(pct)/100)*2*math.Pi
		gx, gy := pointAt(angle, rMax)
		p.WriteString(fmt.Sprintf(
			`<line class="sc-radialbar-grid" data-pct="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
			pct, f1(cx), f1(cy), f1(gx), f1(gy), theme.GridColor))
	}

	// Track backgrounds
	for j := 0; j < nCats; j++ {
		rOut := rMax - float64(j)*bandF
		rIn := rOut - bandF + trackGap
		p.WriteString(fmt.Sprintf(
			`<path class="sc-radialbar-track" data-index="%d" d="%s" fill="%s" fill-opacity="0.15" stroke="none"/>`,
			j, arcPath(rOut, rIn, -math.Pi/2, -math.Pi/2+2*math.Pi-0.001), theme.GridColor))
	}

	// Category labels
	for j := 0; j < nCats; j++ {
		rOut := rMax - float64(j)*bandF
		lx := cx - rOut - 4
		ly := cy
		label := fmt.Sprintf("%d", j)
		if j < len(cats) {
			label = cats[j]
		}
		p.WriteString(fmt.Sprintf(
			`<text class="sc-radialbar-label" data-index="%d" x="%s" y="%s" text-anchor="end" dominant-baseline="central" font-size="11" fill="%s">%s</text>`,
			j, f1(lx), f1(ly), theme.AxisLabelColor, esc(label)))
	}

	// Tick labels at 25%, 50%, 75%, 100%
	for _, pct := range []int{25, 50, 75, 100} {
		angle := -math.Pi/2 + (float64(pct)/100)*2*math.Pi
		tickVal := yMax * float64(pct) / 100
		tx, ty2 := pointAt(angle, rMax+4)
		cosA := math.Cos(angle)
		anchor := "middle"
		if cosA > 0.01 {
			anchor = "start"
		} else if cosA < -0.01 {
			anchor = "end"
		}
		p.WriteString(fmt.Sprintf(
			`<text class="sc-radialbar-tick" data-value="%s" x="%s" y="%s" text-anchor="%s" dominant-baseline="central" font-size="9" fill="%s">%s</text>`,
			esc(fmtNum(tickVal)), f1(tx), f1(ty2), anchor, theme.AxisLabelColor, esc(fmtNum(tickVal))))
	}

	// Value arc bars
	cumulative := make([]float64, nCats)
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

		for j := 0; j < nCats; j++ {
			v := 0.0
			if j < len(s.Data) {
				v = s.Data[j]
			}
			if v <= 0 {
				continue
			}
			rOut := rMax - float64(j)*bandF
			rIn := rOut - bandF + trackGap
			aStart := -math.Pi/2 + (cumulative[j]/yMax)*2*math.Pi
			aEnd := -math.Pi/2 + ((cumulative[j]+v)/yMax)*2*math.Pi

			strokeColor := theme.Background
			if strokeColor == "" {
				strokeColor = "#fff"
			}

			p.WriteString(fmt.Sprintf(
				`<path class="sc-radialbar-bar sc-point" data-series="%d" data-index="%d" data-y="%s" data-color="%s" d="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
				si, j, esc(fmtNum(v)), color, arcPath(rOut, rIn, aStart, aEnd), color, strokeColor))
		}

		for j := 0; j < nCats; j++ {
			v := 0.0
			if j < len(s.Data) {
				v = s.Data[j]
			}
			if v > 0 {
				cumulative[j] += v
			}
		}
	}

	// Legend
	if spec.legendOn() && len(spec.Series) > 0 {
		gapL := 22.0
		est := make([]float64, len(spec.Series))
		for i, s := range spec.Series {
			est[i] = float64(utf8.RuneCountInString(s.Name)*7 + 26)
		}
		totalW := 0.0
		for _, e := range est {
			totalW += e
		}
		totalW += gapL * float64(len(est)-1)
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
			lx += est[si] + gapL
		}
		p.WriteString("</g>")
	}

	p.WriteString("</svg>")
	return p.String()
}
