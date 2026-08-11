package stonecharts

import (
	"fmt"
	"strings"
)

const (
	dtCellW   = 72.0
	dtCellH   = 28.0
	dtHeaderW = 68.0
	dtHeaderH = 24.0

	dtLightR, dtLightG, dtLightB = 227, 242, 253
	dtDarkR, dtDarkG, dtDarkB    = 21, 101, 192
)

func dtScaleColor(t float64) string {
	r := int(float64(dtLightR) + t*float64(dtDarkR-dtLightR) + 0.5)
	g := int(float64(dtLightG) + t*float64(dtDarkG-dtLightG) + 0.5)
	b := int(float64(dtLightB) + t*float64(dtDarkB-dtLightB) + 0.5)
	return fmt.Sprintf("#%02x%02x%02x", r, g, b)
}

func renderDevelopmentTriangleSVG(spec *ChartSpec) string {
	W, H := int(spec.Width), int(spec.Height)
	theme := spec.theme
	if theme == nil {
		t := lightTheme()
		theme = &t
	}

	tri := spec.Triangle
	var origins []string
	var periods []int
	var values [][]float64
	view := "cumulative"
	valueType := "incurred"
	unit := ""
	if tri != nil {
		origins = tri.Origins
		periods = tri.Periods
		values = tri.Values
		if tri.View != "" {
			view = tri.View
		}
		if tri.ValueType != "" {
			valueType = tri.ValueType
		}
		unit = tri.Unit
	}
	nRows := len(origins)
	nCols := len(periods)

	// --- a11y summary (WP7: include view, valueType, unit) ---
	a11yAttr := ""
	a11yDescStr := ""
	if spec.a11yOn() {
		parts := []string{}
		if spec.Title != "" {
			parts = append(parts, spec.Title+".")
		}
		if unit != "" {
			parts = append(parts, "Unit: "+unit+".")
		}
		parts = append(parts, fmt.Sprintf("Development triangle, view: %s, value type: %s.", view, valueType))
		parts = append(parts, fmt.Sprintf("%d origins, %d periods.", nRows, nCols))
		sum := esc(strings.Join(parts, " "))
		a11yAttr = fmt.Sprintf(` role="img" aria-label="%s"`, sum)
		a11yDescStr = fmt.Sprintf("<desc>%s</desc>", sum)
	}

	mTop := 20.0
	if spec.Title != "" {
		mTop += 26
	}
	if spec.Subtitle != "" {
		mTop += 18
	}
	if unit != "" {
		mTop += 16
	}
	mLeft := 22.0
	mRight := 22.0
	mBottom := 20.0
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
	_ = mRight
	_ = mBottom

	showFactors := spec.Factors != nil && spec.Factors.Show
	useColor := spec.ColorScaleCfg != nil
	diagOn := spec.Diagonal != nil && spec.Diagonal.Highlight

	var allVals []float64
	for _, row := range values {
		allVals = append(allVals, row...)
	}
	minVal := 0.0
	maxVal := 0.0
	if len(allVals) > 0 {
		minVal = allVals[0]
		maxVal = allVals[0]
		for _, v := range allVals[1:] {
			if v < minVal {
				minVal = v
			}
			if v > maxVal {
				maxVal = v
			}
		}
	}
	valRange := maxVal - minVal
	if valRange <= 0 {
		valRange = 1.0
	}

	gridX := mLeft + dtHeaderW
	gridY := mTop + dtHeaderH

	cellColor := theme.GridColor
	if cellColor == "" {
		cellColor = "#d8d8e0"
	}
	textColor := theme.TitleColor
	if textColor == "" {
		textColor = "#22223a"
	}
	headerColor := theme.AxisLabelColor
	if headerColor == "" {
		headerColor = "#666"
	}
	diagColor := "#e65100"
	annColor := "#d32f2f"

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

	if a11yDescStr != "" {
		p.WriteString(a11yDescStr)
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
		ty += 16
	}

	// --- WP7: unit label ---
	if unit != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-dt-unit" x="%s" y="%d" text-anchor="middle" font-size="11" fill="%s">Unit: %s</text>`,
			f1(float64(W)/2), ty, theme.SubtitleColor, esc(unit)))
	}

	// --- WP7: wrapping group with data attributes ---
	p.WriteString(fmt.Sprintf(
		`<g class="sc-dt-triangle" data-triangle-view="%s" data-triangle-value-type="%s">`,
		esc(view), esc(valueType)))

	// Period headers
	p.WriteString(`<g class="sc-dt-headers">`)
	for c := 0; c < nCols; c++ {
		cx := gridX + float64(c)*dtCellW + dtCellW/2
		cy := gridY - 6
		p.WriteString(fmt.Sprintf(
			`<text class="sc-dt-period-header" x="%s" y="%s" text-anchor="middle" font-size="11" font-weight="600" fill="%s">%s</text>`,
			f1(cx), f1(cy), headerColor, esc(fmtNum(float64(periods[c])))))
	}
	p.WriteString("</g>")

	// Origin headers
	p.WriteString(`<g class="sc-dt-origins">`)
	for r := 0; r < nRows; r++ {
		ox := gridX - 8
		oy := gridY + float64(r)*dtCellH + dtCellH/2 + 4
		p.WriteString(fmt.Sprintf(
			`<text class="sc-dt-origin-header" x="%s" y="%s" text-anchor="end" font-size="11" font-weight="600" fill="%s">%s</text>`,
			f1(ox), f1(oy), headerColor, esc(origins[r])))
	}
	p.WriteString("</g>")

	// Grid cells
	p.WriteString(`<g class="sc-dt-grid">`)
	for r := 0; r < nRows; r++ {
		var row []float64
		if r < len(values) {
			row = values[r]
		}
		p.WriteString(fmt.Sprintf(`<g class="sc-dt-row" data-origin="%d">`, r))
		for c := 0; c < len(row); c++ {
			v := row[c]
			x := gridX + float64(c)*dtCellW
			y := gridY + float64(r)*dtCellH
			fill := "none"
			if useColor {
				t := (v - minVal) / valRange
				fill = dtScaleColor(t)
			}
			p.WriteString(fmt.Sprintf(
				`<rect class="sc-dt-cell sc-point" data-origin="%d" data-period="%d" x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s"/>`,
				r, c, f1(x), f1(y), f1(dtCellW), f1(dtCellH), fill, cellColor))
			tx := x + dtCellW/2
			tyCell := y + dtCellH/2 + 4
			vColor := textColor
			if useColor && (v-minVal)/valRange > 0.55 {
				vColor = "#ffffff"
			}
			p.WriteString(fmt.Sprintf(
				`<text class="sc-dt-value" x="%s" y="%s" text-anchor="middle" font-size="10" fill="%s">%s</text>`,
				f1(tx), f1(tyCell), vColor, esc(fmtNum(v))))
		}
		p.WriteString("</g>")
	}
	p.WriteString("</g>")

	// --- WP5: fixed latest-diagonal (rightmost populated cell) ---
	if diagOn {
		p.WriteString(`<g class="sc-dt-diagonal">`)
		for r := 0; r < nRows; r++ {
			var row []float64
			if r < len(values) {
				row = values[r]
			}
			if len(row) == 0 {
				continue
			}
			c := len(row) - 1
			x := gridX + float64(c)*dtCellW
			y := gridY + float64(r)*dtCellH
			p.WriteString(fmt.Sprintf(
				`<rect class="sc-dt-diag" data-origin="%d" data-period="%d" x="%s" y="%s" width="%s" height="%s" fill="none" stroke="%s" stroke-width="2"/>`,
				r, c, f1(x), f1(y), f1(dtCellW), f1(dtCellH), diagColor))
		}
		if spec.Diagonal != nil && spec.Diagonal.Label != "" {
			lx := gridX + float64(nCols)*dtCellW + 8
			ly := gridY + dtCellH/2 + 4
			p.WriteString(fmt.Sprintf(
				`<text class="sc-dt-diag-label" x="%s" y="%s" font-size="10" fill="%s">%s</text>`,
				f1(lx), f1(ly), diagColor, esc(spec.Diagonal.Label)))
		}
		p.WriteString("</g>")
	}

	// --- WP6: render supplied factors (no computation) ---
	if showFactors && spec.Factors != nil {
		factorValues := spec.Factors.Values
		fy := gridY + float64(nRows)*dtCellH
		flx := gridX - 8
		fly := fy + dtCellH/2 + 4
		p.WriteString(`<g class="sc-dt-factors">`)
		p.WriteString(fmt.Sprintf(
			`<text class="sc-dt-factor-header" x="%s" y="%s" text-anchor="end" font-size="10" font-weight="600" fill="%s">Factors</text>`,
			f1(flx), f1(fly), headerColor))
		for c := 0; c < len(factorValues); c++ {
			fx := gridX + float64(c)*dtCellW + dtCellW/2 + dtCellW/2
			p.WriteString(fmt.Sprintf(
				`<text class="sc-dt-factor" x="%s" y="%s" text-anchor="middle" font-size="10" fill="%s">%s</text>`,
				f1(fx), f1(fly), textColor, fmt.Sprintf("%.3f", factorValues[c])))
		}
		p.WriteString("</g>")
	}

	// --- WP7: annotations with text in accessible metadata ---
	if len(spec.Annotations) > 0 {
		originIdx := make(map[string]int, len(origins))
		for i, o := range origins {
			originIdx[o] = i
		}
		periodIdx := make(map[int]int, nCols)
		for i := 0; i < nCols; i++ {
			periodIdx[periods[i]] = i
		}
		p.WriteString(`<g class="sc-dt-annotations">`)
		for _, ann := range spec.Annotations {
			ri, riOk := originIdx[ann.Origin]
			ci, ciOk := periodIdx[ann.Period]
			if riOk && ciOk {
				var row []float64
				if ri < len(values) {
					row = values[ri]
				}
				if ci < len(row) {
					ax := gridX + float64(ci)*dtCellW + dtCellW - 6
					ay := gridY + float64(ri)*dtCellH + 6
					escapedText := esc(ann.Text)
					p.WriteString(fmt.Sprintf(
						`<g class="sc-dt-annotation-group" aria-label="%s">`,
						escapedText))
					p.WriteString(fmt.Sprintf(`<title>%s</title>`, escapedText))
					p.WriteString(fmt.Sprintf(
						`<circle class="sc-dt-annotation" cx="%s" cy="%s" r="4" fill="%s" opacity="0.8"/>`,
						f1(ax), f1(ay), annColor))
					p.WriteString(fmt.Sprintf(
						`<text class="sc-dt-annotation-text" x="%s" y="%s" text-anchor="middle" font-size="7" font-weight="700" fill="#ffffff">!</text>`,
						f1(ax), f1(ay+3)))
					p.WriteString("</g>")
				}
			}
		}
		p.WriteString("</g>")
	}

	// Close the wrapping triangle group
	p.WriteString("</g>")

	p.WriteString("</svg>")
	return p.String()
}

func devTriangleDataTable(spec *ChartSpec) string {
	tri := spec.Triangle
	caption := ""
	if spec.Title != "" {
		caption = "<caption>" + esc(spec.Title) + "</caption>"
	}
	var head strings.Builder
	for _, per := range tri.Periods {
		head.WriteString(`<th scope="col">` + esc(fmtNum(float64(per))) + "</th>")
	}
	var rows strings.Builder
	for i, origin := range tri.Origins {
		var row []float64
		if i < len(tri.Values) {
			row = tri.Values[i]
		}
		rows.WriteString(`<tr><th scope="row">` + esc(origin) + "</th>")
		for j := 0; j < len(tri.Periods); j++ {
			if j < len(row) {
				rows.WriteString("<td>" + esc(fmtNum(row[j])) + "</td>")
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

