package stonecharts

import (
	"fmt"
	"strings"
)

func renderTimelineSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Timeline", "numeric", timelineMarks, false)
}

func timelineMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	const LEAD = 28.0

	for si, s := range f.spec.Series {
		st := f.styles[si]
		symbol := s.markerSymbol()
		radius := s.markerRadius()
		if radius == 3.5 {
			radius = 5.0
		}
		rHover := fmtNum(radius + 3)

		baseY := f.plotY + f.plotH/2

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		for k, v := range s.Data {
			cx := f.xpix(v)
			cy := baseY

			side := -1.0
			if k%2 != 0 {
				side = 1.0
			}
			labelY := baseY + side*LEAD

			labelText := ""
			if k < len(s.Labels) {
				labelText = s.Labels[k]
			}

			dataX := esc(labelText)
			if labelText == "" {
				dataX = esc(fmtNum(v))
			}

			p.WriteString(fmt.Sprintf(
				`<line class="sc-leader" data-series="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
				si, f1(cx), f1(cy), f1(cx), f1(labelY), f.theme.AxisLineColor))

			common := fmt.Sprintf(
				`class="sc-event sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
				si, esc(s.Name), dataX, esc(fmtNum(v)), st.solid, fmtNum(radius), rHover)
			p.WriteString(markerSVG(symbol, cx, cy, radius, common, st.fill, f.theme.MarkerHalo, 1.0))

			if labelText != "" {
				anchorY := labelY - 6
				if side >= 0 {
					anchorY = labelY + 12
				}
				p.WriteString(fmt.Sprintf(
					`<text class="sc-label" data-series="%d" x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
					si, f1(cx), f1(anchorY), f.theme.AxisLabelColor, esc(labelText)))
			}
		}
		p.WriteString(`</g>`)
	}
}
