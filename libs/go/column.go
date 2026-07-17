package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

const columnPad = 0.2

// renderColumnSVG is a one-line delegation to the shared cartesian frame:
// band x-scale, include-zero value axis, a11y noun "Column".
func renderColumnSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Column", "band", columnMarks, true)
}

// columnMarks emits the column-specific marks — one <g class="sc-series"> per
// series and one baseline/floating <rect> per datum. All scales come from the
// frame; this function owns only the pinned band sub-layout and stack transform.
func columnMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	bandWidth := f.bandWidth()
	groupW := bandWidth * (1 - columnPad)
	stacked := f.stacking == "normal" || f.stacking == "percent"
	kSlots := len(f.spec.Series)
	if stacked || !f.spec.groupingOn() {
		kSlots = 1
	}
	if kSlots <= 0 {
		kSlots = 1
	}
	barW := groupW / float64(kSlots)
	baseline := f.ypix(0.0)

	totals := make([]float64, f.n)
	if stacked {
		for _, s := range f.spec.Series {
			for i, v := range s.Data {
				if i < f.n {
					totals[i] += v
				}
			}
		}
	}

	cumulative := make([]float64, f.n)
	for si, s := range f.spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		for i, raw := range s.Data {
			if i >= f.n {
				break
			}
			cxBand := f.xpix(i)
			var left, y, h float64
			if stacked {
				left = cxBand - groupW/2
				value := raw
				if f.stacking == "percent" {
					total := totals[i]
					if total == 0 {
						value = 0
					} else {
						value = raw / total * 100.0
					}
				}
				bottomV := cumulative[i]
				topV := bottomV + value
				cumulative[i] = topV
				y0 := f.ypix(bottomV)
				y1 := f.ypix(topV)
				y = math.Min(y0, y1)
				h = math.Abs(y0 - y1)
			} else {
				slot := 0
				if f.spec.groupingOn() {
					slot = si
				}
				left = cxBand - groupW/2 + barW*float64(slot)
				yv := f.ypix(raw)
				y = math.Min(baseline, yv)
				h = math.Abs(baseline - yv)
			}
			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}
			cx := left + barW/2
			common := fmt.Sprintf(
				`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
				si, esc(s.Name), esc(xlabel), esc(fmtNum(raw)), st.solid)
			p.WriteString(fmt.Sprintf(
				`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
				common, f1(cx), f1(y), f1(left), f1(y), f1(barW), f1(h), st.fill))
		}
		p.WriteString(`</g>`)
	}
}
