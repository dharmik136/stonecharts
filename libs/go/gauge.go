package stonecharts

import (
	"fmt"
	"math"
	"strings"
	"unicode/utf8"
)

const (
	gaugeStart = 3 * math.Pi / 4
	gaugeSweep = 3 * math.Pi / 2
)

func renderGaugeSVG(spec *ChartSpec) string {
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
		sum := esc(a11ySummary(spec, "Gauge"))
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

	var s0 *Series
	if len(spec.Series) > 0 {
		s0 = &spec.Series[0]
	}
	value := 0.0
	if s0 != nil && len(s0.Data) > 0 {
		value = s0.Data[0]
	}

	gaugeMin := fdef(spec.GaugeMin, 0)
	gaugeMax := fdef(spec.GaugeMax, 100)
	if gaugeMax <= gaugeMin {
		gaugeMax = gaugeMin + 100
	}

	ptrColor := esc(palette[0])
	if s0 != nil {
		grad, solidHex := s0.colorSpec()
		if grad != nil {
			if len(grad.Stops) > 0 {
				ptrColor = esc(grad.Stops[0].Color)
			} else {
				ptrColor = esc(palette[0])
			}
		} else if solidHex != "" {
			ptrColor = esc(solidHex)
		}
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

	cx := plotX + plotW/2
	cy := plotY + plotH/2
	rMax := plotW / 2
	if plotH/2 < rMax {
		rMax = plotH / 2
	}
	trackW := rMax * 0.15
	rOuter := rMax
	rInner := rMax - trackW

	trackColor := theme.GridColor

	a1 := gaugeStart
	a2 := gaugeStart + gaugeSweep
	ox1 := cx + rOuter*math.Cos(a1)
	oy1 := cy + rOuter*math.Sin(a1)
	ox2 := cx + rOuter*math.Cos(a2)
	oy2 := cy + rOuter*math.Sin(a2)
	ix1 := cx + rInner*math.Cos(a1)
	iy1 := cy + rInner*math.Sin(a1)
	ix2 := cx + rInner*math.Cos(a2)
	iy2 := cy + rInner*math.Sin(a2)
	dTrack := fmt.Sprintf(
		"M %s %s A %s %s 0 1 1 %s %s L %s %s A %s %s 0 1 0 %s %s Z",
		f1(ox1), f1(oy1), f1(rOuter), f1(rOuter), f1(ox2), f1(oy2),
		f1(ix2), f1(iy2), f1(rInner), f1(rInner), f1(ix1), f1(iy1))
	p.WriteString(fmt.Sprintf(`<path class="sc-gauge-track" d="%s" fill="%s"/>`, dTrack, trackColor))

	if s0 != nil {
		p.WriteString(`<g class="sc-series" data-series="0">`)

		for bi, band := range spec.GaugeBands {
			bFrom := band.From
			if bFrom < gaugeMin {
				bFrom = gaugeMin
			}
			bTo := band.To
			if bTo > gaugeMax {
				bTo = gaugeMax
			}
			if bTo <= bFrom {
				continue
			}
			frac1 := (bFrom - gaugeMin) / (gaugeMax - gaugeMin)
			frac2 := (bTo - gaugeMin) / (gaugeMax - gaugeMin)
			ba1 := gaugeStart + frac1*gaugeSweep
			ba2 := gaugeStart + frac2*gaugeSweep
			bSweep := ba2 - ba1
			bLarge := 0
			if bSweep > math.Pi {
				bLarge = 1
			}

			boox1 := cx + rOuter*math.Cos(ba1)
			booy1 := cy + rOuter*math.Sin(ba1)
			boox2 := cx + rOuter*math.Cos(ba2)
			booy2 := cy + rOuter*math.Sin(ba2)
			biix1 := cx + rInner*math.Cos(ba1)
			biiy1 := cy + rInner*math.Sin(ba1)
			biix2 := cx + rInner*math.Cos(ba2)
			biiy2 := cy + rInner*math.Sin(ba2)
			dBand := fmt.Sprintf(
				"M %s %s A %s %s 0 %d 1 %s %s L %s %s A %s %s 0 %d 0 %s %s Z",
				f1(boox1), f1(booy1), f1(rOuter), f1(rOuter), bLarge, f1(boox2), f1(booy2),
				f1(biix2), f1(biiy2), f1(rInner), f1(rInner), bLarge, f1(biix1), f1(biiy1))
			p.WriteString(fmt.Sprintf(
				`<path class="sc-gauge-band" data-index="%d" data-from="%s" data-to="%s" d="%s" fill="%s"/>`,
				bi, esc(fmtNum(band.From)), esc(fmtNum(band.To)), dBand, esc(band.Color)))
		}

		frac := (value - gaugeMin) / (gaugeMax - gaugeMin)
		if frac < 0 {
			frac = 0
		}
		if frac > 1 {
			frac = 1
		}
		ptrAngle := gaugeStart + frac*gaugeSweep
		tipR := rInner - 4
		baseW := 6.0
		tailR := 12.0
		tipX := cx + tipR*math.Cos(ptrAngle)
		tipY := cy + tipR*math.Sin(ptrAngle)
		leftX := cx + baseW*math.Cos(ptrAngle+math.Pi/2)
		leftY := cy + baseW*math.Sin(ptrAngle+math.Pi/2)
		rightX := cx + baseW*math.Cos(ptrAngle-math.Pi/2)
		rightY := cy + baseW*math.Sin(ptrAngle-math.Pi/2)
		tailX := cx + tailR*math.Cos(ptrAngle+math.Pi)
		tailY := cy + tailR*math.Sin(ptrAngle+math.Pi)
		dPtr := fmt.Sprintf(
			"M %s %s L %s %s L %s %s L %s %s Z",
			f1(tipX), f1(tipY), f1(leftX), f1(leftY), f1(tailX), f1(tailY), f1(rightX), f1(rightY))
		sName := s0.Name
		p.WriteString(fmt.Sprintf(
			`<path class="sc-pointer sc-point" data-series="0" data-series-name="%s" data-y="%s" data-color="%s" d="%s" fill="%s"/>`,
			esc(sName), esc(fmtNum(value)), ptrColor, dPtr, ptrColor))

		p.WriteString(fmt.Sprintf(
			`<circle class="sc-pivot" cx="%s" cy="%s" r="8" fill="%s"/>`,
			f1(cx), f1(cy), ptrColor))

		p.WriteString("</g>")
	}

	p.WriteString(fmt.Sprintf(
		`<text class="sc-gauge-value" x="%s" y="%s" text-anchor="middle" font-size="20" font-weight="700" fill="%s">%s</text>`,
		f1(cx), f1(cy+28), theme.TitleColor, esc(fmtNum(value))))

	if spec.legendOn() && len(spec.Series) > 0 && s0 != nil {
		gap := 22.0
		var est []float64
		est = []float64{float64(utf8.RuneCountInString(s0.Name)*7 + 26)}
		totalW := 0.0
		if len(est) > 0 {
			for _, e := range est {
				totalW += e
			}
			totalW += gap * float64(len(est)-1)
		}
		lx := plotX + (plotW-totalW)/2
		ly := float64(H - 10)
		p.WriteString(`<g class="sc-legend">`)
		p.WriteString(`<g class="sc-legend-item" data-series="0">`)
		p.WriteString(fmt.Sprintf(
			`<rect x="%s" y="%s" width="14" height="4" rx="2" fill="%s"/>`,
			f1(lx), f1(ly-9), ptrColor))
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" font-size="12" fill="%s">%s</text>`,
			f1(lx+20), f1(ly-2), theme.LegendTextColor, esc(s0.Name)))
		p.WriteString("</g>")
		p.WriteString("</g>")
	}

	p.WriteString("</svg>")
	return p.String()
}

func gaugeDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Metric</th><th scope="col">Value</th>` +
		`<th scope="col">Min</th><th scope="col">Max</th></tr></thead><tbody>`)
	if len(spec.Series) > 0 {
		s0 := spec.Series[0]
		if len(s0.Data) > 0 {
			gMin := fdef(spec.GaugeMin, 0)
			gMax := fdef(spec.GaugeMax, 100)
			b.WriteString(fmt.Sprintf(
				`<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td></tr>`,
				esc(s0.Name), esc(fmtNum(s0.Data[0])), esc(fmtNum(gMin)), esc(fmtNum(gMax))))
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}
