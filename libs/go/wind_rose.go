package stonecharts

import (
	"fmt"
	"math"
	"strings"
	"unicode/utf8"
)

func renderWindRoseSVG(spec *ChartSpec) string {
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
		sum := esc(a11ySummary(spec, "Wind rose"))
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
	nDirs := len(cats)
	if nDirs < 3 {
		nDirs = 3
	}

	labelMargin := 40.0
	cx := plotX + plotW/2
	cy := plotY + plotH/2
	rMax := plotW / 2
	if plotH/2 < rMax {
		rMax = plotH / 2
	}
	rMax -= labelMargin

	stacks := make([]float64, nDirs)
	for _, s := range spec.Series {
		for j := 0; j < nDirs; j++ {
			v := 0.0
			if j < len(s.Data) {
				v = s.Data[j]
			}
			if v > 0 {
				stacks[j] += v
			}
		}
	}
	yMax := 0.0
	for _, st := range stacks {
		if st > yMax {
			yMax = st
		}
	}
	if yMax <= 0 {
		yMax = 100
	}

	nRings := 5
	gapRad := 0.02

	axisAngle := func(i int) float64 {
		return -math.Pi/2 + float64(i)*2*math.Pi/float64(nDirs)
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

	// Grid rings (circular)
	for level := 0; level < nRings; level++ {
		frac := float64(level+1) / float64(nRings)
		r := rMax * frac
		p.WriteString(fmt.Sprintf(
			`<circle class="sc-windrose-ring" data-level="%d" cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1"/>`,
			level, f1(cx), f1(cy), f1(r), theme.GridColor))
	}

	// Radial axis lines
	for i := 0; i < nDirs; i++ {
		ex, ey := pointAt(axisAngle(i), rMax)
		p.WriteString(fmt.Sprintf(
			`<line class="sc-windrose-axis" data-index="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
			i, f1(cx), f1(cy), f1(ex), f1(ey), theme.GridColor))
	}

	// Direction labels
	for i := 0; i < nDirs; i++ {
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
			`<text class="sc-windrose-label" data-index="%d" x="%s" y="%s" text-anchor="%s" dominant-baseline="central" font-size="11" fill="%s">%s</text>`,
			i, f1(lx), f1(ly), anchor, theme.AxisLabelColor, esc(label)))
	}

	// Tick labels along first axis
	for level := 0; level < nRings; level++ {
		frac := float64(level+1) / float64(nRings)
		tickVal := frac * yMax
		tickR := rMax * frac
		tx, ty2 := pointAt(axisAngle(0), tickR)
		p.WriteString(fmt.Sprintf(
			`<text class="sc-windrose-tick" data-value="%s" x="%s" y="%s" font-size="9" fill="%s">%s</text>`,
			esc(fmtNum(tickVal)), f1(tx+4), f1(ty2-2), theme.AxisLabelColor, esc(fmtNum(tickVal))))
	}

	// Stacked sector wedges
	halfSpan := math.Pi/float64(nDirs) - gapRad

	cumulative := make([]float64, nDirs)
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

		for j := 0; j < nDirs; j++ {
			v := 0.0
			if j < len(s.Data) {
				v = s.Data[j]
			}
			if v <= 0 {
				continue
			}
			rInner := cumulative[j] / yMax * rMax
			rOuter := (cumulative[j] + v) / yMax * rMax
			angle := axisAngle(j)
			aStart := angle - halfSpan
			aEnd := angle + halfSpan

			ox1, oy1 := pointAt(aStart, rOuter)
			ox2, oy2 := pointAt(aEnd, rOuter)

			strokeColor := theme.Background
			if strokeColor == "" {
				strokeColor = "#fff"
			}

			var pathD string
			if rInner > 0 {
				ix2, iy2 := pointAt(aEnd, rInner)
				ix1, iy1 := pointAt(aStart, rInner)
				pathD = fmt.Sprintf("M %s %s A %s %s 0 0 1 %s %s L %s %s A %s %s 0 0 0 %s %s Z",
					f1(ox1), f1(oy1),
					f1(rOuter), f1(rOuter), f1(ox2), f1(oy2),
					f1(ix2), f1(iy2),
					f1(rInner), f1(rInner), f1(ix1), f1(iy1))
			} else {
				pathD = fmt.Sprintf("M %s %s A %s %s 0 0 1 %s %s L %s %s Z",
					f1(ox1), f1(oy1),
					f1(rOuter), f1(rOuter), f1(ox2), f1(oy2),
					f1(cx), f1(cy))
			}

			p.WriteString(fmt.Sprintf(
				`<path class="sc-windrose-sector sc-point" data-series="%d" data-index="%d" data-y="%s" data-color="%s" d="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
				si, j, esc(fmtNum(v)), color, pathD, color, strokeColor))
		}

		for j := 0; j < nDirs; j++ {
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
