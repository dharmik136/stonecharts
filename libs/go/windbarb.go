package stonecharts

import (
	"fmt"
	"math"
	"strings"
)

func renderWindbarbSVG(spec *ChartSpec) string {
	return renderCartesian(spec, "Windbarb", "band", windbarbMarks, true)
}

const (
	staffW    = 1.5
	featherDX = 7.0
	featherDY = 3.0
	halfDX    = 3.5
	halfDY    = 1.5
	barbStep  = 3.0
	rCalm     = 3.5
)

func windbarbMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	barbLen := fdef(f.spec.BarbLength, 20)
	calmThr := fdef(f.spec.CalmThreshold, 2)
	yOff := fdef(f.spec.YOffset, 0)
	hemi := f.spec.Hemisphere
	if hemi == "" {
		hemi = "N"
	}

	dx := featherDX
	hdx := halfDX
	if hemi == "S" {
		dx = -featherDX
		hdx = -halfDX
	}

	laneY := f.plotY + f.plotH/2 + yOff

	for si, s := range f.spec.Series {
		st := f.styles[si]
		color := st.stroke
		solid := st.solid

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		for k, speed := range s.Data {
			direction := 0.0
			if k < len(s.Direction) {
				direction = s.Direction[k]
			}
			xc := f.xpix(float64(k))

			cat := fmt.Sprintf("%d", k)
			if k < len(f.spec.XAxis.Categories) {
				cat = f.spec.XAxis.Categories[k]
			}

			p.WriteString(fmt.Sprintf(
				`<g class="sc-barb sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-speed="%s" data-direction="%s" data-color="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s" transform="rotate(%s %s %s)">`,
				si, esc(s.Name), esc(cat), esc(fmtNum(speed)), esc(fmtNum(speed)), esc(fmtNum(direction)),
				solid, fmtNum(rCalm), fmtNum(rCalm+3),
				f1(xc), f1(laneY), fmtNum(direction), f1(xc), f1(laneY)))

			if speed < calmThr {
				p.WriteString(fmt.Sprintf(
					`<circle class="sc-calm" cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="%s"/>`,
					f1(xc), f1(laneY), fmtNum(rCalm), color, fmtNum(staffW)))
			} else {
				tipY := laneY - barbLen
				p.WriteString(fmt.Sprintf(
					`<line class="sc-staff" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>`,
					f1(xc), f1(laneY), f1(xc), f1(tipY), color, fmtNum(staffW)))

				s5 := int(math.Floor(speed/5+0.5)) * 5
				nFlags := s5 / 50
				nFull := (s5 % 50) / 10
				nHalf := (s5 % 10) / 5

				fi := 0
				for range nFlags {
					y0 := tipY + float64(fi)*barbStep
					yBase := tipY + float64(fi+2)*barbStep
					p.WriteString(fmt.Sprintf(
						`<polygon class="sc-flag" points="%s,%s %s,%s %s,%s" fill="%s" stroke="%s" stroke-width="%s"/>`,
						f1(xc), f1(y0), f1(xc+dx), f1(y0-featherDY), f1(xc), f1(yBase),
						color, color, fmtNum(staffW)))
					fi += 2
				}
				for range nFull {
					y := tipY + float64(fi)*barbStep
					p.WriteString(fmt.Sprintf(
						`<line class="sc-feather" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>`,
						f1(xc), f1(y), f1(xc+dx), f1(y-featherDY), color, fmtNum(staffW)))
					fi++
				}
				if nHalf > 0 {
					y := tipY + float64(fi)*barbStep
					p.WriteString(fmt.Sprintf(
						`<line class="sc-feather-half" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>`,
						f1(xc), f1(y), f1(xc+hdx), f1(y-halfDY), color, fmtNum(staffW)))
				}
			}

			p.WriteString(`</g>`)
		}
		p.WriteString(`</g>`)
	}
}
