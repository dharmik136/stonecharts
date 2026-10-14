package stonecharts

import (
	"fmt"
	"math"
	"sort"
	"strconv"
	"strings"
)

func resolveHeatmapStops(ca *ColorAxis) []ColorAxisStop {
	if ca != nil && len(ca.Stops) > 0 {
		res := make([]ColorAxisStop, len(ca.Stops))
		copy(res, ca.Stops)
		sort.Slice(res, func(i, j int) bool {
			return res[i].Offset < res[j].Offset
		})
		return res
	}
	if ca != nil && (ca.MinColor != "" || ca.MaxColor != "") {
		cMin := ca.MinColor
		if cMin == "" {
			cMin = "#e0f3f8"
		}
		cMax := ca.MaxColor
		if cMax == "" {
			cMax = "#084081"
		}
		return []ColorAxisStop{
			{Offset: 0.0, Color: cMin},
			{Offset: 1.0, Color: cMax},
		}
	}
	return []ColorAxisStop{
		{Offset: 0.0, Color: "#e0f3f8"},
		{Offset: 0.5, Color: "#4eb3d3"},
		{Offset: 1.0, Color: "#084081"},
	}
}

func parseHex(c string) (int, int, int) {
	c = strings.TrimPrefix(c, "#")
	if len(c) == 3 || len(c) == 4 {
		r, _ := strconv.ParseInt(string([]byte{c[0], c[0]}), 16, 64)
		g, _ := strconv.ParseInt(string([]byte{c[1], c[1]}), 16, 64)
		b, _ := strconv.ParseInt(string([]byte{c[2], c[2]}), 16, 64)
		return int(r), int(g), int(b)
	}
	if len(c) >= 6 {
		r, _ := strconv.ParseInt(c[0:2], 16, 64)
		g, _ := strconv.ParseInt(c[2:4], 16, 64)
		b, _ := strconv.ParseInt(c[4:6], 16, 64)
		return int(r), int(g), int(b)
	}
	return 0, 0, 0
}

func interpolateColor(t float64, stops []ColorAxisStop) string {
	if len(stops) == 0 {
		return "#e0f3f8"
	}
	if t <= stops[0].Offset {
		return stops[0].Color
	}
	if t >= stops[len(stops)-1].Offset {
		return stops[len(stops)-1].Color
	}
	for i := 0; i < len(stops)-1; i++ {
		s0, s1 := stops[i], stops[i+1]
		if s0.Offset <= t && t <= s1.Offset {
			span := s1.Offset - s0.Offset
			u := 0.0
			if span > 0 {
				u = (t - s0.Offset) / span
			}
			r0, g0, b0 := parseHex(s0.Color)
			r1, g1, b1 := parseHex(s1.Color)
			r := int(float64(r0) + u*float64(r1-r0) + 0.5)
			g := int(float64(g0) + u*float64(g1-g0) + 0.5)
			b := int(float64(b0) + u*float64(b1-b0) + 0.5)
			if r < 0 {
				r = 0
			} else if r > 255 {
				r = 255
			}
			if g < 0 {
				g = 0
			} else if g > 255 {
				g = 255
			}
			if b < 0 {
				b = 0
			} else if b > 255 {
				b = 255
			}
			return fmt.Sprintf("#%02x%02x%02x", r, g, b)
		}
	}
	return stops[len(stops)-1].Color
}

func renderHeatmapSVG(spec *ChartSpec) string {
	W, H := int(spec.Width), int(spec.Height)
	if W == 0 {
		W = 820
	}
	if H == 0 {
		H = 460
	}
	theme := spec.theme
	if theme == nil {
		t := lightTheme()
		theme = &t
	}
	xCats := spec.XAxis.Categories
	yCats := spec.YAxis.Categories
	nx := len(xCats)
	ny := len(yCats)

	a11yAttr := ""
	a11yDesc := ""
	if spec.a11yOn() {
		sum := esc(a11ySummary(spec, "Heatmap"))
		a11yAttr = fmt.Sprintf(` role="img" aria-label="%s"`, sum)
		a11yDesc = fmt.Sprintf(`<desc>%s</desc>`, sum)
	}

	showLegend := (spec.Legend == nil || *spec.Legend) &&
		(spec.ColorAxis == nil || spec.ColorAxis.Visible == nil || *spec.ColorAxis.Visible)

	mTop := 20.0
	if spec.Title != "" {
		mTop += 26.0
	}
	if spec.Subtitle != "" {
		mTop += 18.0
	}

	maxYLen := 0
	for _, c := range yCats {
		if len(c) > maxYLen {
			maxYLen = len(c)
		}
	}
	mLeft := float64(maxYLen)*7.5 + 24.0
	if mLeft < 52.0 {
		mLeft = 52.0
	}
	if spec.YAxis.Title != "" {
		mLeft += 18.0
	}

	mRight := 24.0

	mBottom := 46.0
	if spec.XAxis.Title != "" {
		mBottom += 18.0
	}
	if showLegend {
		mBottom += 36.0
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

	plotW := float64(W) - mLeft - mRight
	plotH := float64(H) - mTop - mBottom
	cellW := 0.0
	if nx > 0 {
		cellW = plotW / float64(nx)
	}
	cellH := 0.0
	if ny > 0 {
		cellH = plotH / float64(ny)
	}

	var allVals []float64
	for _, s := range spec.Series {
		for _, pt := range s.HeatmapData {
			if !math.IsNaN(pt.Value) && !math.IsInf(pt.Value, 0) {
				allVals = append(allVals, pt.Value)
			}
		}
	}

	ca := spec.ColorAxis
	minVal := 0.0
	if ca != nil && ca.Min != nil {
		minVal = *ca.Min
	} else if len(allVals) > 0 {
		minVal = allVals[0]
		for _, v := range allVals[1:] {
			if v < minVal {
				minVal = v
			}
		}
	}

	maxVal := 100.0
	if ca != nil && ca.Max != nil {
		maxVal = *ca.Max
	} else if len(allVals) > 0 {
		maxVal = allVals[0]
		for _, v := range allVals[1:] {
			if v > maxVal {
				maxVal = v
			}
		}
	}

	valRange := maxVal - minVal
	if valRange < 0 {
		valRange = 0.0
	}

	stops := resolveHeatmapStops(ca)
	strokeColor := "#ffffff"
	if theme.Name == "dark" {
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

	cid := spec.ID
	if cid == "" {
		cid = "sc"
	}
	gid := cid + "-color-axis-grad"

	if showLegend {
		legendStops := stops
		if ca != nil && ca.Reversed {
			legendStops = make([]ColorAxisStop, len(stops))
			for i, st := range stops {
				legendStops[i] = ColorAxisStop{Offset: 1.0 - st.Offset, Color: st.Color}
			}
			sort.Slice(legendStops, func(i, j int) bool {
				return legendStops[i].Offset < legendStops[j].Offset
			})
		}
		var gradStops strings.Builder
		for _, st := range legendStops {
			gradStops.WriteString(fmt.Sprintf(`<stop offset="%s" stop-color="%s"/>`, fmtNum(st.Offset), st.Color))
		}
		p.WriteString(fmt.Sprintf(`<defs><linearGradient id="%s" x1="0" y1="0" x2="1" y2="0">%s</linearGradient></defs>`, gid, gradStops.String()))
	}

	if theme.Background != "" {
		p.WriteString(fmt.Sprintf(`<rect class="sc-bg" x="0" y="0" width="%d" height="%d" fill="%s"/>`, W, H, theme.Background))
	}

	ty := 26
	if spec.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-title" x="%s" y="%d" text-anchor="middle" font-size="17" font-weight="600" fill="%s">%s</text>`,
			f1(float64(W)/2.0), ty, theme.TitleColor, esc(spec.Title)))
		ty += 20
	}
	if spec.Subtitle != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-subtitle" x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(float64(W)/2.0), ty, theme.SubtitleColor, esc(spec.Subtitle)))
		ty += 16
	}

	// Y-axis categories and title
	p.WriteString(`<g class="sc-axis sc-axis-y">`)
	for r := 0; r < ny; r++ {
		oy := mTop + float64(r)*cellH + cellH/2.0 + 4.0
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="end" font-size="11" fill="%s">%s</text>`,
			f1(mLeft-8.0), f1(oy), theme.AxisLabelColor, esc(yCats[r])))
	}
	p.WriteString(`</g>`)

	if spec.YAxis.Title != "" {
		yc := mTop + plotH/2.0
		p.WriteString(fmt.Sprintf(
			`<text x="14" y="%s" text-anchor="middle" font-size="12" fill="%s" transform="rotate(-90 14 %s)">%s</text>`,
			f1(yc), theme.AxisTitleColor, f1(yc), esc(spec.YAxis.Title)))
	}

	// X-axis categories and title
	p.WriteString(`<g class="sc-axis sc-axis-x">`)
	for c := 0; c < nx; c++ {
		cx := mLeft + float64(c)*cellW + cellW/2.0
		cy := mTop + plotH + 16.0
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
			f1(cx), f1(cy), theme.AxisLabelColor, esc(xCats[c])))
	}
	p.WriteString(`</g>`)

	if spec.XAxis.Title != "" {
		xtY := mTop + plotH + 34.0
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(mLeft+plotW/2.0), f1(xtY), theme.AxisTitleColor, esc(spec.XAxis.Title)))
	}

	// Series and cell marks
	for si, s := range spec.Series {
		p.WriteString(fmt.Sprintf(
			`<g class="sc-series sc-series-heatmap" data-series="%d" data-name="%s">`,
			si, esc(s.Name)))
		for _, pt := range s.HeatmapData {
			xCat := strconv.Itoa(pt.X)
			if pt.X < len(xCats) {
				xCat = xCats[pt.X]
			}
			yCat := strconv.Itoa(pt.Y)
			if pt.Y < len(yCats) {
				yCat = yCats[pt.Y]
			}

			fillColor := "#f0f0f0"
			if ca != nil && ca.NullColor != "" {
				fillColor = ca.NullColor
			}
			if !math.IsNaN(pt.Value) && !math.IsInf(pt.Value, 0) {
				t := 0.5
				if valRange > 0 {
					t = (pt.Value - minVal) / valRange
				}
				if t < 0.0 {
					t = 0.0
				} else if t > 1.0 {
					t = 1.0
				}
				if ca != nil && ca.Reversed {
					t = 1.0 - t
				}
				fillColor = interpolateColor(t, stops)
			}

			rectX := mLeft + float64(pt.X)*cellW + 0.5
			rectY := mTop + float64(pt.Y)*cellH + 0.5
			rectW := cellW - 1.0
			rectH := cellH - 1.0

			ariaLabel := fmt.Sprintf("%s, %s: %s", yCat, xCat, fmtNum(pt.Value))

			p.WriteString(fmt.Sprintf(
				`<rect class="sc-cell sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-cell-x="%d" data-cell-y="%d" data-value="%s" data-color="%s" x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="1" tabindex="0" aria-label="%s"/>`,
				si, esc(s.Name), esc(xCat), esc(fmtNum(pt.Value)), pt.X, pt.Y, esc(fmtNum(pt.Value)), fillColor,
				f1(rectX), f1(rectY), f1(rectW), f1(rectH), fillColor, strokeColor, esc(ariaLabel)))
		}
		p.WriteString(`</g>`)
	}

	// Legend (color-axis)
	if showLegend {
		barW := 200.0
		barH := 10.0
		barX := mLeft + (plotW-barW)/2.0
		barY := mTop + plotH + 30.0
		if spec.XAxis.Title != "" {
			barY = mTop + plotH + 48.0
		}
		labelY := barY + barH + 12.0
		midVal := (minVal + maxVal) / 2.0
		p.WriteString(`<g class="sc-color-axis">`)
		p.WriteString(fmt.Sprintf(
			`<rect x="%s" y="%s" width="%s" height="%s" fill="url(#%s)" rx="2"/>`,
			f1(barX), f1(barY), f1(barW), f1(barH), gid))
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="start" font-size="10" fill="%s">%s</text>`,
			f1(barX), f1(labelY), theme.AxisLabelColor, esc(fmtNum(minVal))))
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="middle" font-size="10" fill="%s">%s</text>`,
			f1(barX+barW/2.0), f1(labelY), theme.AxisLabelColor, esc(fmtNum(midVal))))
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="end" font-size="10" fill="%s">%s</text>`,
			f1(barX+barW), f1(labelY), theme.AxisLabelColor, esc(fmtNum(maxVal))))
		p.WriteString(`</g>`)
	}

	p.WriteString(`</svg>`)
	return p.String()
}

func heatmapDataTable(spec *ChartSpec) string {
	xCats := spec.XAxis.Categories
	yCats := spec.YAxis.Categories
	type cellKey struct{ x, y int }
	grid := make(map[cellKey]float64)
	present := make(map[cellKey]bool)
	for _, s := range spec.Series {
		for _, pt := range s.HeatmapData {
			grid[cellKey{pt.X, pt.Y}] = pt.Value
			present[cellKey{pt.X, pt.Y}] = true
		}
	}
	caption := ""
	if spec.Title != "" {
		caption = "<caption>" + esc(spec.Title) + "</caption>"
	}
	var head strings.Builder
	for _, c := range xCats {
		head.WriteString(`<th scope="col">` + esc(c) + "</th>")
	}
	var rows strings.Builder
	for y, yCat := range yCats {
		rows.WriteString(`<tr><th scope="row">` + esc(yCat) + "</th>")
		for x := 0; x < len(xCats); x++ {
			k := cellKey{x, y}
			if present[k] {
				rows.WriteString("<td>" + esc(fmtNum(grid[k])) + "</td>")
			} else {
				rows.WriteString("<td></td>")
			}
		}
		rows.WriteString("</tr>")
	}
	return `<table class="sc-visually-hidden">` + caption +
		"<thead><tr><td></td>" + head.String() + "</tr></thead>" +
		"<tbody>" + rows.String() + "</tbody></table>"
}
