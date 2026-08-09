package stonecharts

import (
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

func renderFunnelSVG(spec *ChartSpec) string {
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
		sum := esc(a11ySummary(spec, "Funnel"))
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
			cats[i] = strconv.Itoa(i)
		}
	}

	var defsParts []string
	colorByPoint := true
	funnelFill := ""
	if s0 != nil {
		grad, solidHex := s0.colorSpec()
		if grad != nil {
			gid := cid + "-grad-0"
			defsParts = append(defsParts, gradientDef(gid, grad))
			funnelFill = "url(#" + gid + ")"
			colorByPoint = false
		} else if solidHex != "" {
			funnelFill = esc(solidHex)
			colorByPoint = false
		}
		if s0.Pattern != nil {
			pid := cid + "-pat-0"
			defsParts = append(defsParts, patternDef(pid, s0.Pattern))
			funnelFill = "url(#" + pid + ")"
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

	subtype := spec.Subtype
	if subtype == "" {
		subtype = "funnel"
	}
	minWFrac := fdef(spec.MinWidth, 0.0)
	neckWFrac := fdef(spec.NeckWidth, 0.3)
	neckHFrac := fdef(spec.NeckHeight, 0.25)

	maxVal := 0.0
	if len(data) > 0 {
		maxVal = data[0]
		for _, v := range data[1:] {
			if v > maxVal {
				maxVal = v
			}
		}
	}

	wscale := func(v float64) float64 {
		if maxVal <= 0 {
			return 0.0
		}
		return plotW * v / maxVal
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

	if n > 0 && s0 != nil {
		bandH := plotH / float64(n)
		cx := plotX + plotW/2

		order := make([]int, n)
		for i := 0; i < n; i++ {
			order[i] = i
		}
		if subtype == "pyramid" {
			for i, j := 0, n-1; i < j; i, j = i+1, j-1 {
				order[i], order[j] = order[j], order[i]
			}
		}

		p.WriteString(`<g class="sc-series" data-series="0">`)

		for drawIdx, stageIdx := range order {
			v := data[stageIdx]
			wTop := wscale(v)
			if minWFrac*plotW > wTop {
				wTop = minWFrac * plotW
			}

			var wBot float64
			var yTop, yBot float64

			if subtype == "neck" {
				neckY := plotY + plotH*(1-neckHFrac)
				neckW := neckWFrac * plotW
				yTop = plotY + bandH*float64(drawIdx)
				yBot = plotY + bandH*float64(drawIdx+1)

				if yTop >= neckY {
					wTop = neckW
					wBot = neckW
				} else if yBot <= neckY {
					taperH := neckY - plotY
					var tTop, tBot float64
					if taperH <= 0 {
						tTop = 0.0
						tBot = 0.0
					} else {
						tTop = (yTop - plotY) / taperH
						tBot = (yBot - plotY) / taperH
					}
					w0 := wscale(data[order[0]])
					if minWFrac*plotW > w0 {
						w0 = minWFrac * plotW
					}
					wTop = w0 + (neckW-w0)*tTop
					wBot = w0 + (neckW-w0)*tBot
				} else {
					taperH := neckY - plotY
					var tTop float64
					if taperH <= 0 {
						tTop = 0.0
					} else {
						tTop = (yTop - plotY) / taperH
					}
					w0 := wscale(data[order[0]])
					if minWFrac*plotW > w0 {
						w0 = minWFrac * plotW
					}
					wTop = w0 + (neckW-w0)*tTop
					wBot = neckW
				}
			} else {
				yTop = plotY + bandH*float64(drawIdx)
				yBot = plotY + bandH*float64(drawIdx+1)

				if drawIdx < n-1 {
					nextStage := order[drawIdx+1]
					wBot = wscale(data[nextStage])
					if minWFrac*plotW > wBot {
						wBot = minWFrac * plotW
					}
				} else {
					if subtype == "pyramid" {
						wBot = 0.0
					} else {
						wBot = wTop
					}
				}
			}

			xTL := cx - wTop/2
			xTR := cx + wTop/2
			xBL := cx - wBot/2
			xBR := cx + wBot/2
			bandCY := yTop + bandH/2

			var fill string
			if colorByPoint {
				fill = esc(palette[stageIdx%len(palette)])
			} else {
				fill = funnelFill
			}

			cat := strconv.Itoa(stageIdx)
			if stageIdx < len(cats) {
				cat = cats[stageIdx]
			}
			sName := s0.Name

			p.WriteString(fmt.Sprintf(
				`<polygon class="sc-slice sc-point" data-series="0" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6" cx="%s" cy="%s" points="%s,%s %s,%s %s,%s %s,%s" fill="%s"/>`,
				esc(sName), esc(cat), esc(fmtNum(v)), fill,
				f1(cx), f1(bandCY),
				f1(xTL), f1(yTop), f1(xTR), f1(yTop), f1(xBR), f1(yBot), f1(xBL), f1(yBot),
				fill))
		}

		p.WriteString("</g>")
	}

	if spec.legendOn() && len(spec.Series) > 0 {
		gap := 22.0
		var est []float64
		if s0 != nil {
			est = []float64{float64(utf8.RuneCountInString(s0.Name)*7 + 26)}
		}
		total := 0.0
		if len(est) > 0 {
			for _, e := range est {
				total += e
			}
			total += gap * float64(len(est)-1)
		}
		lx := plotX + (plotW-total)/2
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
