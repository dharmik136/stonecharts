package stonecharts

import (
	"fmt"
	"math"
	"strings"
)

const boxplotPad = 0.2
const boxplotCap = 0.5
const boxplotOpacity = 0.5
const boxplotOutlierR = 2.5
const boxplotMinBox = 1.0

func renderBoxplotSVG(spec *ChartSpec) string {
	s2 := *spec
	s2.Series = make([]Series, len(spec.Series))
	copy(s2.Series, spec.Series)

	var allVals []float64
	for _, s := range s2.Series {
		for _, bd := range s.BoxData {
			allVals = append(allVals, bd.Low, bd.High)
			allVals = append(allVals, bd.Outliers...)
		}
	}
	if len(allVals) == 0 {
		for _, s := range s2.Series {
			allVals = append(allVals, s.Data...)
		}
	}

	if s2.YAxis.Min == nil && len(allVals) > 0 {
		mn := allVals[0]
		for _, v := range allVals[1:] {
			if v < mn {
				mn = v
			}
		}
		s2.YAxis.Min = &mn
	}
	if s2.YAxis.Max == nil && len(allVals) > 0 {
		mx := allVals[0]
		for _, v := range allVals[1:] {
			if v > mx {
				mx = v
			}
		}
		s2.YAxis.Max = &mx
	}

	orientation := s2.Orientation
	if orientation == "" {
		orientation = "vertical"
	}
	return renderCartesian(&s2, "Boxplot", "band", boxplotMarks, false, orientation)
}

func boxplotMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}
	spec := f.spec
	horiz := f.orientation == "horizontal"
	K := len(spec.Series)
	if K <= 0 {
		K = 1
	}

	for si, s := range spec.Series {
		st := f.styles[si]
		boxData := s.BoxData
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		count := len(boxData)
		if count > f.n {
			count = f.n
		}

		for i := 0; i < count; i++ {
			bd := boxData[i]
			cat := fmt.Sprintf("%d", i)
			if i < len(f.cats) {
				cat = f.cats[i]
			}

			if horiz {
				bandSz := f.bandHeight()
				groupSz := bandSz * (1 - boxplotPad)
				barSz := groupSz / float64(K)
				bandC := f.bandCenter(i)
				slotStart := bandC - groupSz/2 + barSz*float64(si)
				mid := slotStart + barSz/2
				capHalf := barSz * boxplotCap / 2

				xq1 := f.valuePix(bd.Q1)
				xq3 := f.valuePix(bd.Q3)
				xmed := f.valuePix(bd.Median)
				xlow := f.valuePix(bd.Low)
				xhigh := f.valuePix(bd.High)

				bx := math.Min(xq1, xq3)
				bw := math.Abs(xq3 - xq1)
				if bw < boxplotMinBox {
					bw = boxplotMinBox
				}

				cxVal := xmed
				cyVal := mid

				common := fmt.Sprintf(
					`class="sc-box sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
					si, esc(s.Name), esc(cat), esc(fmtNum(bd.Median)), st.solid)
				p.WriteString(fmt.Sprintf(
					`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s" fill-opacity="%s" stroke="%s"/>`,
					common, f1(cxVal), f1(cyVal), f1(bx), f1(slotStart), f1(bw), f1(barSz), st.fill, fmtNum(boxplotOpacity), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-median" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(xmed), f1(slotStart), f1(xmed), f1(slotStart+barSz), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(xq3), f1(mid), f1(xhigh), f1(mid), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker-cap" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(xhigh), f1(mid-capHalf), f1(xhigh), f1(mid+capHalf), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(xq1), f1(mid), f1(xlow), f1(mid), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker-cap" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(xlow), f1(mid-capHalf), f1(xlow), f1(mid+capHalf), st.solid))
				for _, o := range bd.Outliers {
					ox := f.valuePix(o)
					p.WriteString(fmt.Sprintf(
						`<circle class="sc-outlier" cx="%s" cy="%s" r="%s" fill="%s"/>`,
						f1(ox), f1(mid), fmtNum(boxplotOutlierR), st.solid))
				}
			} else {
				bandSz := f.bandWidth()
				groupSz := bandSz * (1 - boxplotPad)
				barSz := groupSz / float64(K)
				bandC := f.xpix(float64(i))
				slotStart := bandC - groupSz/2 + barSz*float64(si)
				mid := slotStart + barSz/2
				capHalf := barSz * boxplotCap / 2

				yq3 := f.ypix(bd.Q3)
				yq1 := f.ypix(bd.Q1)
				ymed := f.ypix(bd.Median)
				yhigh := f.ypix(bd.High)
				ylow := f.ypix(bd.Low)

				boxH := yq1 - yq3
				if boxH < boxplotMinBox {
					boxH = boxplotMinBox
				}

				cxVal := mid
				cyVal := ymed

				common := fmt.Sprintf(
					`class="sc-box sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
					si, esc(s.Name), esc(cat), esc(fmtNum(bd.Median)), st.solid)
				p.WriteString(fmt.Sprintf(
					`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s" fill-opacity="%s" stroke="%s"/>`,
					common, f1(cxVal), f1(cyVal), f1(slotStart), f1(yq3), f1(barSz), f1(boxH), st.fill, fmtNum(boxplotOpacity), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-median" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(slotStart), f1(ymed), f1(slotStart+barSz), f1(ymed), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(mid), f1(yq3), f1(mid), f1(yhigh), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker-cap" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(mid-capHalf), f1(yhigh), f1(mid+capHalf), f1(yhigh), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(mid), f1(yq1), f1(mid), f1(ylow), st.solid))
				p.WriteString(fmt.Sprintf(
					`<line class="sc-whisker-cap" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>`,
					f1(mid-capHalf), f1(ylow), f1(mid+capHalf), f1(ylow), st.solid))
				for _, o := range bd.Outliers {
					oy := f.ypix(o)
					p.WriteString(fmt.Sprintf(
						`<circle class="sc-outlier" cx="%s" cy="%s" r="%s" fill="%s"/>`,
						f1(mid), f1(oy), fmtNum(boxplotOutlierR), st.solid))
				}
			}
		}

		p.WriteString(`</g>`)
	}
}
