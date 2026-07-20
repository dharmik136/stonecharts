package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

const barPad = 0.2

// renderBarSVG is the horizontal transpose of renderColumnSVG.
func renderBarSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Bar", "band", barMarks, true, "horizontal")
}

// barMarks emits the bar-specific marks — one <g class="sc-series"> per
// series and one baseline/floating <rect> per datum. The frame owns the scale;
// this function owns only the pinned band sub-layout and stack transform.
func barMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	bandHeight := f.bandHeight()
	groupH := bandHeight * (1 - barPad)
	stacked := f.stacking == "normal" || f.stacking == "percent"
	kSlots := len(f.spec.Series)
	if stacked || !f.spec.groupingOn() {
		kSlots = 1
	}
	if kSlots <= 0 {
		kSlots = 1
	}
	barH := groupH / float64(kSlots)
	baseline := f.valueZero()

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

	positive := make([]float64, f.n)
	negative := make([]float64, f.n)
	for si, s := range f.spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		for i, raw := range s.Data {
			if i >= f.n {
				break
			}
			cyBand := f.bandCenter(i)
			var top, x, w, cx float64
			if stacked {
				top = cyBand - groupH/2
				value := raw
				if f.stacking == "percent" {
					total := totals[i]
					if total == 0 {
						value = 0
					} else {
						value = raw / total * 100.0
					}
				}
				var leftV, rightV float64
				if value >= 0 {
					leftV = positive[i]
					rightV = leftV + value
					positive[i] = rightV
				} else {
					leftV = negative[i]
					rightV = leftV + value
					negative[i] = rightV
				}
				x0 := f.valuePix(leftV)
				x1 := f.valuePix(rightV)
				x = math.Min(x0, x1)
				w = math.Abs(x0 - x1)
				cx = x1
			} else {
				slot := 0
				if f.spec.groupingOn() {
					slot = si
				}
				top = cyBand - groupH/2 + barH*float64(slot)
				xv := f.valuePix(raw)
				x = math.Min(baseline, xv)
				w = math.Abs(baseline - xv)
				cx = xv
			}
			xlabel := strconv.Itoa(i)
			if i < len(f.cats) {
				xlabel = f.cats[i]
			}
			cy := top + barH/2
			common := fmt.Sprintf(
				`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
				si, esc(s.Name), esc(xlabel), esc(fmtNum(raw)), st.solid)
			p.WriteString(fmt.Sprintf(
				`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
				common, f1(cx), f1(cy), f1(x), f1(top), f1(w), f1(barH), st.fill))
		}
		p.WriteString(`</g>`)
	}
}
