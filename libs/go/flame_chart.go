package stonecharts

import (
	"fmt"
	"strings"
)

func renderFlameChartSVG(spec *ChartSpec) string {
	mod := *spec
	mod.Series = make([]Series, len(spec.Series))
	copy(mod.Series, spec.Series)
	for i := range mod.Series {
		d := make([]float64, len(spec.Series[i].Data))
		copy(d, spec.Series[i].Data)
		mod.Series[i].Data = d
	}

	maxDepth := 0
	var allTimes []float64
	for _, s := range mod.Series {
		for _, fr := range s.Frames {
			if fr.Depth > maxDepth {
				maxDepth = fr.Depth
			}
			allTimes = append(allTimes, fr.X, fr.X2)
		}
	}

	depthCats := make([]string, maxDepth+1)
	for d := 0; d <= maxDepth; d++ {
		depthCats[d] = fmt.Sprintf("%d", d)
	}
	mod.XAxis.Categories = depthCats

	for i := range mod.Series {
		for len(mod.Series[i].Data) < len(depthCats) {
			mod.Series[i].Data = append(mod.Series[i].Data, 0.0)
		}
	}

	if mod.YAxis.Min == nil {
		v := 0.0
		if mod.XAxis.Min != nil {
			v = *mod.XAxis.Min
		} else if len(allTimes) > 0 {
			v = allTimes[0]
			for _, t := range allTimes[1:] {
				if t < v {
					v = t
				}
			}
		}
		mod.YAxis.Min = &v
	}
	if mod.YAxis.Max == nil {
		v := 0.0
		if mod.XAxis.Max != nil {
			v = *mod.XAxis.Max
		} else if len(allTimes) > 0 {
			v = allTimes[0]
			for _, t := range allTimes[1:] {
				if t > v {
					v = t
				}
			}
		}
		mod.YAxis.Max = &v
	}

	return renderCartesian(&mod, "Flame chart", "band", flameMarks, false, "horizontal")
}

const (
	flamePad       = 0.2
	labelMinPx     = 40.0
	flameCharWidth = 6.5
)

func flameMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	laneHeight := f.plotH / float64(f.n)
	barThickness := laneHeight * (1 - flamePad)

	ypixBand := func(depth int) float64 {
		inverted := f.n - 1 - depth
		return f.plotY + laneHeight*float64(inverted) + laneHeight/2
	}

	xval := func(v float64) float64 {
		return f.valuePix(v)
	}

	for si, s := range f.spec.Series {
		st := f.styles[si]
		fill := st.fill

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		for _, frame := range s.Frames {
			start := frame.X
			end := frame.X2
			depth := frame.Depth
			name := frame.Name

			frameFill := fill
			if frame.Color != "" {
				frameFill = frame.Color
			}

			xLeft := xval(start)
			xRight := xval(end)
			if start > end {
				xLeft, xRight = xRight, xLeft
			}
			w := xRight - xLeft
			if w < 1.0 {
				w = 1.0
			}
			cy := ypixBand(depth)
			cx := xval((start + end) / 2)
			top := cy - barThickness/2

			duration := end - start
			depthLabel := fmt.Sprintf("%d", depth)

			dataAttrs := fmt.Sprintf(
				`class="sc-frame sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-start="%s" data-end="%s" data-depth="%d" data-name="%s" data-duration="%s" data-color="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s"`,
				si, esc(s.Name), esc(depthLabel), esc(fmtNum(start)), esc(fmtNum(start)), esc(fmtNum(end)),
				depth, esc(name), esc(fmtNum(duration)), esc(frameFill), fmtNum(3.5), fmtNum(6),
				f1(cx), f1(cy))

			p.WriteString(fmt.Sprintf(
				`<rect %s x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
				dataAttrs, f1(xLeft), f1(top), f1(w), f1(barThickness), esc(frameFill)))

			if name != "" && w >= labelMinPx {
				maxChars := int(w / flameCharWidth)
				label := name
				if len(label) > maxChars {
					if maxChars-1 > 0 {
						label = label[:maxChars-1] + "…"
					} else {
						label = "…"
					}
				}
				labelY := cy + 3.5
				p.WriteString(fmt.Sprintf(
					`<text class="sc-frame-label" x="%s" y="%s" text-anchor="middle" font-size="10" fill="#ffffff">%s</text>`,
					f1(cx), f1(labelY), esc(label)))
			}
		}

		p.WriteString(`</g>`)
	}
}

func flameChartDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Series</th><th scope="col">Depth</th>` +
		`<th scope="col">Start</th><th scope="col">End</th>` +
		`<th scope="col">Duration</th><th scope="col">Name</th></tr></thead><tbody>`)
	for _, s := range spec.Series {
		for _, fr := range s.Frames {
			duration := fr.X2 - fr.X
			name := fr.Name
			b.WriteString(`<tr><th scope="row">` + esc(s.Name) + `</th><td>` +
				fmt.Sprintf("%d", fr.Depth) + `</td><td>` +
				esc(fmtNum(fr.X)) + `</td><td>` + esc(fmtNum(fr.X2)) + `</td><td>` +
				esc(fmtNum(duration)) + `</td><td>` + esc(name) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}
