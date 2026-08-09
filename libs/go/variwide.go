package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// renderVariwideSVG is a one-line delegation to the shared cartesian frame:
// variwide x-scale (cumulative widths), include-zero value axis, a11y noun "Variwide".
func renderVariwideSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Variwide", "variwide", variwideMarks, true)
}

// variwideMarks emits the variwide-specific marks -- one <g class="sc-series"> per
// series and one baseline-anchored <rect> per category with proportional widths.
// The cumulative-width x-layout is owned by the frame; marks read slotLefts/slotWidths.
func variwideMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	const PAD = 1.0

	for si, s := range f.spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		widths := s.Widths

		for i, v := range s.Data {
			if i >= f.n {
				break
			}

			sw := f.slotWidth(i)
			sl := 0.0
			if i < len(f.slotLefts) {
				sl = f.slotLefts[i]
			}

			barX := sl + PAD
			barW := sw - 2*PAD
			if barW < 0 {
				barW = 0
			}

			basePx := f.valuePix(0)
			valPx := f.valuePix(v)
			barY := math.Min(basePx, valPx)
			barH := math.Abs(basePx - valPx)

			cx := f.xpix(float64(i))
			cy := valPx

			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}

			zVal := 0.0
			if i < len(widths) {
				zVal = widths[i]
			}

			common := fmt.Sprintf(
				`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-z="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
				si, esc(s.Name), esc(xlabel), esc(fmtNum(v)), esc(fmtNum(zVal)), st.solid)
			p.WriteString(fmt.Sprintf(
				`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
				common, f1(cx), f1(cy), f1(barX), f1(barY), f1(barW), f1(barH), st.fill))
		}
		p.WriteString(`</g>`)
	}
}
