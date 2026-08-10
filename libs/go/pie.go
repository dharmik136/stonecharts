package stonecharts

import (
	"fmt"
	"math"
	"strings"
	"unicode/utf8"
)

func renderPieSVG(spec *ChartSpec) string {
	W, H := int(spec.Width), int(spec.Height)
	theme := spec.theme
	if theme == nil {
		t := lightTheme()
		theme = &t
	}
	palette := theme.Palette
	cid := esc(spec.ID)

	a11yAttr := ""
	a11yDesc := ""
	if spec.a11yOn() {
		sum := esc(a11ySummary(spec, "Pie"))
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
	var data []float64
	if s0 != nil {
		data = s0.Data
	}
	n := len(data)
	cats := spec.XAxis.Categories
	if len(cats) == 0 {
		cats = make([]string, n)
		for i := 0; i < n; i++ {
			cats[i] = fmt.Sprintf("%d", i)
		}
	}

	var defsParts []string
	colorByPoint := true
	pieFill := ""
	if s0 != nil {
		grad, solidHex := s0.colorSpec()
		if grad != nil {
			gid := cid + "-grad-0"
			defsParts = append(defsParts, gradientDef(gid, grad))
			pieFill = "url(#" + gid + ")"
			colorByPoint = false
		} else if solidHex != "" {
			pieFill = esc(solidHex)
			colorByPoint = false
		}
		if s0.Pattern != nil {
			pid := cid + "-pat-0"
			defsParts = append(defsParts, patternDef(pid, s0.Pattern))
			pieFill = "url(#" + pid + ")"
			colorByPoint = false
		}
	}

	solid0 := ""
	if s0 != nil {
		grad, solidHex := s0.colorSpec()
		if grad != nil {
			if len(grad.Stops) > 0 {
				solid0 = esc(grad.Stops[0].Color)
			} else {
				solid0 = esc(palette[0])
			}
		} else if solidHex != "" {
			solid0 = esc(solidHex)
		} else {
			solid0 = esc(palette[0])
		}
	}

	total := 0.0
	for _, v := range data {
		if v > 0 {
			total += v
		}
	}

	strokeColor := "#ffffff"
	if theme.Background != "" {
		strokeColor = "#1e1e2f"
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

	if len(defsParts) > 0 {
		p.WriteString("<defs>" + strings.Join(defsParts, "") + "</defs>")
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
	r := rMax
	ri := r * fdef(spec.InnerSize, 0)

	var zVals []float64
	if s0 != nil {
		zVals = s0.Z
	}
	zMin, zMax := 0.0, 0.0
	if len(zVals) >= n && n > 0 {
		zMin = zVals[0]
		zMax = zVals[0]
		for _, zv := range zVals[:n] {
			if zv < zMin {
				zMin = zv
			}
			if zv > zMax {
				zMax = zv
			}
		}
	}
	minSizeFrac := fdef(spec.MinSize, 0.2)
	sliceR := func(i int) float64 {
		if len(zVals) == 0 || i >= len(zVals) || zMax <= zMin {
			return rMax
		}
		t := 0.5
		if zMax > zMin {
			t = (zVals[i] - zMin) / (zMax - zMin)
		}
		return rMax * (minSizeFrac + (1-minSizeFrac)*t)
	}

	if n > 0 && s0 != nil && total > 0 {
		p.WriteString(`<g class="sc-series" data-series="0">`)

		positiveCount := 0
		for _, v := range data {
			if v > 0 {
				positiveCount++
			}
		}

		if positiveCount == 1 {
			idx := 0
			for i, v := range data {
				if v > 0 {
					idx = i
					break
				}
			}
			var fill string
			if colorByPoint {
				fill = esc(palette[idx%len(palette)])
			} else {
				fill = pieFill
			}
			cat := fmt.Sprintf("%d", idx)
			if idx < len(cats) {
				cat = cats[idx]
			}
			pct := "100.0%"
			if ri > 0 {
				dStr := fmt.Sprintf(
					"M %s %s A %s %s 0 1 1 %s %s A %s %s 0 1 1 %s %s M %s %s A %s %s 0 1 0 %s %s A %s %s 0 1 0 %s %s Z",
					f1(cx-r), f1(cy), f1(r), f1(r), f1(cx+r), f1(cy),
					f1(r), f1(r), f1(cx-r), f1(cy),
					f1(cx-ri), f1(cy), f1(ri), f1(ri), f1(cx+ri), f1(cy),
					f1(ri), f1(ri), f1(cx-ri), f1(cy))
				p.WriteString(fmt.Sprintf(
					`<path class="sc-slice sc-point" data-series="0" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-index="%d" data-percentage="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s" d="%s" fill-rule="evenodd" fill="%s" stroke="%s" stroke-width="2"/>`,
					esc(s0.Name), esc(cat), esc(fmtNum(data[idx])), fill,
					idx, pct, f1(r), f1(r+4),
					f1(cx), f1(cy), dStr,
					fill, strokeColor))
			} else {
				p.WriteString(fmt.Sprintf(
					`<circle class="sc-slice sc-point" data-series="0" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-index="%d" data-percentage="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="2"/>`,
					esc(s0.Name), esc(cat), esc(fmtNum(data[idx])), fill,
					idx, pct, f1(r), f1(r+4),
					f1(cx), f1(cy), f1(r),
					fill, strokeColor))
			}
		} else {
			angle := -math.Pi / 2
			for i := 0; i < n; i++ {
				v := data[i]
				if v <= 0 {
					continue
				}
				sweep := (v / total) * 2 * math.Pi
				sr := sliceR(i)
				ox1 := cx + sr*math.Cos(angle)
				oy1 := cy + sr*math.Sin(angle)
				endAngle := angle + sweep
				ox2 := cx + sr*math.Cos(endAngle)
				oy2 := cy + sr*math.Sin(endAngle)
				largeArc := 0
				if sweep > math.Pi {
					largeArc = 1
				}

				var fill string
				if colorByPoint {
					fill = esc(palette[i%len(palette)])
				} else {
					fill = pieFill
				}
				cat := fmt.Sprintf("%d", i)
				if i < len(cats) {
					cat = cats[i]
				}
				pct := fmt.Sprintf("%.1f%%", (v/total)*100)

				var dStr string
				if ri > 0 {
					ix1 := cx + ri*math.Cos(angle)
					iy1 := cy + ri*math.Sin(angle)
					ix2 := cx + ri*math.Cos(endAngle)
					iy2 := cy + ri*math.Sin(endAngle)
					dStr = fmt.Sprintf(
						"M %s %s A %s %s 0 %d 1 %s %s L %s %s A %s %s 0 %d 0 %s %s Z",
						f1(ox1), f1(oy1), f1(sr), f1(sr), largeArc, f1(ox2), f1(oy2),
						f1(ix2), f1(iy2), f1(ri), f1(ri), largeArc, f1(ix1), f1(iy1))
				} else {
					dStr = fmt.Sprintf(
						"M %s %s L %s %s A %s %s 0 %d 1 %s %s Z",
						f1(cx), f1(cy), f1(ox1), f1(oy1),
						f1(sr), f1(sr), largeArc, f1(ox2), f1(oy2))
				}

				p.WriteString(fmt.Sprintf(
					`<path class="sc-slice sc-point" data-series="0" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-index="%d" data-percentage="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s" d="%s" fill="%s" stroke="%s" stroke-width="2"/>`,
					esc(s0.Name), esc(cat), esc(fmtNum(v)), fill,
					i, pct, f1(sr), f1(sr+4),
					f1(cx), f1(cy), dStr,
					fill, strokeColor))

				angle = endAngle
			}
		}

		p.WriteString("</g>")
	}

	if spec.legendOn() && len(spec.Series) > 0 {
		gap := 22.0
		var est []float64
		if s0 != nil {
			est = []float64{float64(utf8.RuneCountInString(s0.Name)*7 + 26)}
		}
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
			f1(lx), f1(ly-9), solid0))
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" font-size="12" fill="%s">%s</text>`,
			f1(lx+20), f1(ly-2), theme.LegendTextColor, esc(s0.Name)))
		p.WriteString("</g>")
		p.WriteString("</g>")
	}

	p.WriteString("</svg>")
	return p.String()
}

func pieDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Category</th><th scope="col">Value</th>` +
		`<th scope="col">Percentage</th></tr></thead><tbody>`)
	cats := spec.XAxis.Categories
	if len(spec.Series) > 0 {
		s0 := spec.Series[0]
		total := 0.0
		for _, v := range s0.Data {
			if v > 0 {
				total += v
			}
		}
		for i, v := range s0.Data {
			cat := fmt.Sprintf("%d", i)
			if i < len(cats) {
				cat = cats[i]
			}
			pct := 0.0
			if total > 0 {
				pct = (v / total) * 100
			}
			b.WriteString(fmt.Sprintf(
				`<tr><th scope="row">%s</th><td>%s</td><td>%.1f%%</td></tr>`,
				esc(cat), esc(fmtNum(v)), pct))
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}
