// Waterfall chart renderer — running-total floating bars with connectors.
// Byte-identical SVG output with the Python renderer.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package stonecharts

import (
	"fmt"
	"strings"
)

const waterfallPad = 0.2

func renderWaterfallSVG(spec *ChartSpec) string {
	s2 := *spec
	s2.Series = make([]Series, len(spec.Series))
	copy(s2.Series, spec.Series)

	sumIdx := make(map[int]bool)
	for _, v := range s2.SumIndices {
		sumIdx[v] = true
	}
	isumIdx := make(map[int]bool)
	for _, v := range s2.IntermediateSumIndices {
		isumIdx[v] = true
	}

	// Compute y-domain from running totals.
	allVals := []float64{0.0}
	for _, s := range s2.Series {
		running := 0.0
		for i, delta := range s.Data {
			if sumIdx[i] || isumIdx[i] {
				allVals = append(allVals, 0.0, running)
			} else {
				allVals = append(allVals, running)
				running += delta
				allVals = append(allVals, running)
			}
		}
	}
	if s2.YAxis.Min == nil {
		mn := allVals[0]
		for _, v := range allVals[1:] {
			if v < mn {
				mn = v
			}
		}
		s2.YAxis.Min = &mn
	}
	if s2.YAxis.Max == nil {
		mx := allVals[0]
		for _, v := range allVals[1:] {
			if v > mx {
				mx = v
			}
		}
		s2.YAxis.Max = &mx
	}

	return renderCartesian(&s2, "Waterfall", "band", waterfallMarks, true, "vertical")
}

type waterfallBar struct {
	start, end float64
	kind       string // "increase", "decrease", "total"
	totalAfter float64
}

func waterfallMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}
	spec := f.spec

	sumIdx := make(map[int]bool)
	for _, v := range spec.SumIndices {
		sumIdx[v] = true
	}
	isumIdx := make(map[int]bool)
	for _, v := range spec.IntermediateSumIndices {
		isumIdx[v] = true
	}

	upColor := spec.UpColor
	if upColor == "" {
		upColor = "#3f9b6a"
	}
	downColor := spec.DownColor
	if downColor == "" {
		downColor = "#d65f5f"
	}
	totalColor := spec.TotalColor
	if totalColor == "" {
		totalColor = "#4b6cb7"
	}

	connEnabled := true
	connDash := "4 3"
	connColor := f.theme.GridColor
	if spec.Connector != nil {
		if spec.Connector.Enabled != nil && !*spec.Connector.Enabled {
			connEnabled = false
		}
		if spec.Connector.DashStyle == "dotted" {
			connDash = "2 3"
		} else if spec.Connector.DashStyle == "solid" {
			connDash = ""
		}
	}

	band := f.bandWidth()
	groupW := band * (1 - waterfallPad)
	k := 1
	if f.spec.groupingOn() {
		k = len(f.spec.Series)
		if k < 1 {
			k = 1
		}
	}
	barW := groupW / float64(k)

	for si, s := range spec.Series {
		n := len(s.Data)
		if n > f.n {
			n = f.n
		}

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		// Running-total transform.
		bars := make([]waterfallBar, n)
		running := 0.0
		for i := 0; i < n; i++ {
			delta := s.Data[i]
			if sumIdx[i] || isumIdx[i] {
				bars[i] = waterfallBar{0.0, running, "total", running}
			} else {
				start := running
				end := running + delta
				running = end
				kind := "increase"
				if delta < 0 {
					kind = "decrease"
				}
				bars[i] = waterfallBar{start, end, kind, running}
			}
		}

		siOff := 0
		if f.spec.groupingOn() {
			siOff = si
		}

		// Connectors first.
		if connEnabled {
			for i := 0; i < len(bars)-1; i++ {
				level := bars[i].totalAfter
				x1 := f.xpix(float64(i)) - groupW/2 + barW*float64(siOff) + barW
				x2 := f.xpix(float64(i+1)) - groupW/2 + barW*float64(siOff)
				y := f.ypix(level)
				dashAttr := ""
				if connDash != "" {
					dashAttr = ` stroke-dasharray="` + connDash + `"`
				}
				p.WriteString(fmt.Sprintf(
					`<line class="sc-connector" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"%s/>`,
					f1(x1), f1(y), f1(x2), f1(y), connColor, dashAttr))
			}
		}

		// Bars.
		for i := 0; i < len(bars); i++ {
			b := bars[i]
			xlabel := fmt.Sprintf("%d", i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}

			left := f.xpix(float64(i)) - groupW/2 + barW*float64(siOff)
			cx := left + barW/2

			yStart := f.ypix(b.start)
			yEnd := f.ypix(b.end)
			yTop := yEnd
			if yStart < yEnd {
				yTop = yStart
			}
			barH := yStart - yEnd
			if barH < 0 {
				barH = -barH
			}
			if barH < 1.0 {
				barH = 1.0
			}

			fill := upColor
			if b.kind == "decrease" {
				fill = downColor
			} else if b.kind == "total" {
				fill = totalColor
			}

			displayVal := b.totalAfter
			if b.kind != "total" {
				displayVal = s.Data[i]
			}

			p.WriteString(fmt.Sprintf(
				`<rect class="sc-bar sc-point" data-series="%d"`+
					` data-series-name="%s" data-x="%s"`+
					` data-y="%s"`+
					` data-kind="%s" data-total="%s"`+
					` data-color="%s" data-r="3.5" data-r-hover="6"`+
					` cx="%s" cy="%s"`+
					` x="%s" y="%s"`+
					` width="%s" height="%s"`+
					` fill="%s"/>`,
				si, esc(s.Name), esc(xlabel),
				esc(fmtNum(displayVal)),
				b.kind, esc(fmtNum(b.totalAfter)),
				fill,
				f1(cx), f1(yTop),
				f1(left), f1(yTop),
				f1(barW), f1(barH),
				fill))
		}

		p.WriteString(`</g>`)
	}
}
