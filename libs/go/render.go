package stonecharts

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const cssBlock = `.sc-chart-wrap{position:relative;display:inline-block;line-height:0}
  .sc-chart{display:block;background:#fff}
  .sc-point{cursor:pointer;transition:r .08s ease}
  .sc-legend-item.sc-hidden{opacity:.35}
  .sc-tooltip{position:absolute;pointer-events:none;z-index:10;background:rgba(255,255,255,.97);
    border:1px solid #d8d8e0;border-radius:6px;box-shadow:0 4px 14px rgba(20,20,40,.14);
    padding:7px 10px;font:12px/1.4 Segoe UI,Helvetica,Arial,sans-serif;color:#22223a;white-space:nowrap}
  .sc-tt-title{font-weight:600;margin-bottom:2px}
  .sc-tt-row{display:flex;align-items:center}
  .sc-tt-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
  .sc-visually-hidden{position:absolute!important;width:1px!important;height:1px!important;
    padding:0!important;margin:-1px!important;overflow:hidden!important;
    clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}`

// dataTable mirrors render.py _data_table: a visually-hidden HTML data table, the
// accessible alternative to the SVG (which is role="img").
func dataTable(spec *ChartSpec) string {
	if spec.Type == "arearange" || spec.Type == "columnrange" {
		return rangeDataTable(spec)
	}
	if spec.Type == "error-bar" {
		return errorBarDataTable(spec)
	}
	if spec.Type == "boxplot" {
		return boxplotDataTable(spec)
	}
	if spec.Type == "candlestick" {
		return candlestickDataTable(spec)
	}
	if spec.Type == "flame-chart" {
		return flameChartDataTable(spec)
	}
	if spec.Type == "gauge" {
		return gaugeDataTable(spec)
	}
	if spec.Type == "pie" {
		return pieDataTable(spec)
	}
	if spec.Type == "technical-indicators" {
		return tiDataTable(spec)
	}
	if spec.Type == "xrange" {
		return xrangeDataTable(spec)
	}
	if spec.Type == "vector-plot" {
		return vectorPlotDataTable(spec)
	}
	if spec.Type == "scatter" || spec.Type == "bubble" {
		return pointModelDataTable(spec, spec.Type == "bubble")
	}
	n := 0
	for _, s := range spec.Series {
		if len(s.Data) > n {
			n = len(s.Data)
		}
	}
	cats := spec.XAxis.Categories
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString("<thead><tr><td></td>")
	for i := 0; i < n; i++ {
		label := strconv.Itoa(i)
		if i < len(cats) {
			label = cats[i]
		}
		b.WriteString(`<th scope="col">` + esc(label) + `</th>`)
	}
	b.WriteString("</tr></thead><tbody>")
	for _, s := range spec.Series {
		b.WriteString(`<tr><th scope="row">` + esc(s.Name) + `</th>`)
		for i := 0; i < n; i++ {
			if i < len(s.Data) {
				b.WriteString("<td>" + esc(fmtNum(s.Data[i])) + "</td>")
			} else {
				b.WriteString("<td></td>")
			}
		}
		b.WriteString("</tr>")
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

// scatterDataTable mirrors render.py's _data_table scatter branch (§3.3
// Rank 3 / §5.4b-DT): a long-format table (one row per point) is the only
// lossless shape for (x, y) point-model data.
// pointModelDataTable mirrors render.py's _data_table point-model branch
// (scatter §3.3 Rank 3 / bubble §3.3 Rank 4, §5.4b-DT): a long-format table
// (one row per point) is the only lossless shape for (x,y) or (x,y,z) data.
func pointModelDataTable(spec *ChartSpec, hasZ bool) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Series</th><th scope="col">X</th><th scope="col">Y</th>`)
	if hasZ {
		b.WriteString(`<th scope="col">Z</th>`)
	}
	b.WriteString(`</tr></thead><tbody>`)
	for _, s := range spec.Series {
		for _, d := range s.DataPoints {
			b.WriteString(`<tr><th scope="row">` + esc(s.Name) + `</th><td>` +
				esc(fmtNum(d.X)) + `</td><td>` + esc(fmtNum(d.Y)) + `</td>`)
			if hasZ {
				z := 0.0
				if d.Z != nil {
					z = *d.Z
				}
				b.WriteString(`<td>` + esc(fmtNum(z)) + `</td>`)
			}
			b.WriteString(`</tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func boxplotDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Category</th><th scope="col">Series</th>` +
		`<th scope="col">Low</th><th scope="col">Q1</th>` +
		`<th scope="col">Median</th><th scope="col">Q3</th>` +
		`<th scope="col">High</th><th scope="col">Outliers</th></tr></thead><tbody>`)
	cats := spec.XAxis.Categories
	for _, s := range spec.Series {
		for i, bd := range s.BoxData {
			cat := strconv.Itoa(i)
			if i < len(cats) {
				cat = cats[i]
			}
			outliers := ""
			for j, o := range bd.Outliers {
				if j > 0 {
					outliers += ", "
				}
				outliers += fmtNum(o)
			}
			b.WriteString(`<tr><th scope="row">` + esc(cat) + `</th><td>` +
				esc(s.Name) + `</td><td>` + esc(fmtNum(bd.Low)) + `</td><td>` +
				esc(fmtNum(bd.Q1)) + `</td><td>` + esc(fmtNum(bd.Median)) + `</td><td>` +
				esc(fmtNum(bd.Q3)) + `</td><td>` + esc(fmtNum(bd.High)) + `</td><td>` +
				esc(outliers) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func candlestickDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Category</th><th scope="col">Series</th>` +
		`<th scope="col">Open</th><th scope="col">High</th>` +
		`<th scope="col">Low</th><th scope="col">Close</th></tr></thead><tbody>`)
	cats := spec.XAxis.Categories
	for _, s := range spec.Series {
		for i, d := range s.OHLC {
			cat := strconv.Itoa(i)
			if i < len(cats) {
				cat = cats[i]
			}
			b.WriteString(`<tr><th scope="row">` + esc(cat) + `</th><td>` +
				esc(s.Name) + `</td><td>` + esc(fmtNum(d.Open)) + `</td><td>` +
				esc(fmtNum(d.High)) + `</td><td>` + esc(fmtNum(d.Low)) + `</td><td>` +
				esc(fmtNum(d.Close)) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func rangeDataTable(spec *ChartSpec) string {
	isCR := spec.Type == "columnrange"
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Category</th><th scope="col">Series</th>` +
		`<th scope="col">Low</th><th scope="col">High</th></tr></thead><tbody>`)
	cats := spec.XAxis.Categories
	for _, s := range spec.Series {
		for i := range s.Data {
			cat := strconv.Itoa(i)
			if i < len(cats) {
				cat = cats[i]
			}
			var loVal, hiVal float64
			if isCR {
				loVal = s.Data[i]
				hiVal = loVal
				if i < len(s.High) {
					hiVal = s.High[i]
				}
			} else {
				hiVal = s.Data[i]
				loVal = hiVal
				if i < len(s.Low) {
					loVal = s.Low[i]
				}
			}
			b.WriteString(`<tr><th scope="row">` + esc(cat) + `</th><td>` +
				esc(s.Name) + `</td><td>` + esc(fmtNum(loVal)) + `</td><td>` +
				esc(fmtNum(hiVal)) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func errorBarDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Category</th><th scope="col">Series</th>` +
		`<th scope="col">Y</th><th scope="col">Low</th>` +
		`<th scope="col">High</th></tr></thead><tbody>`)
	cats := spec.XAxis.Categories
	for _, s := range spec.Series {
		for i, yVal := range s.Data {
			cat := strconv.Itoa(i)
			if i < len(cats) {
				cat = cats[i]
			}
			loVal := yVal
			hiVal := yVal
			if i < len(s.Low) {
				loVal = s.Low[i]
			}
			if i < len(s.High) {
				hiVal = s.High[i]
			}
			b.WriteString(`<tr><th scope="row">` + esc(cat) + `</th><td>` +
				esc(s.Name) + `</td><td>` + esc(fmtNum(yVal)) + `</td><td>` +
				esc(fmtNum(loVal)) + `</td><td>` + esc(fmtNum(hiVal)) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func xrangeDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Series</th><th scope="col">Lane</th>` +
		`<th scope="col">Start</th><th scope="col">End</th>` +
		`<th scope="col">Duration</th></tr></thead><tbody>`)
	laneCats := spec.YAxis.Categories
	for _, s := range spec.Series {
		for _, sp := range s.Spans {
			laneLabel := strconv.Itoa(sp.Y)
			if sp.Y < len(laneCats) {
				laneLabel = laneCats[sp.Y]
			}
			b.WriteString(`<tr><th scope="row">` + esc(s.Name) + `</th><td>` +
				esc(laneLabel) + `</td><td>` + esc(fmtNum(sp.X)) + `</td><td>` +
				esc(fmtNum(sp.X2)) + `</td><td>` + esc(fmtNum(sp.X2-sp.X)) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func vectorPlotDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Series</th><th scope="col">X</th>` +
		`<th scope="col">Y</th><th scope="col">Direction</th>` +
		`<th scope="col">Length</th></tr></thead><tbody>`)
	for _, s := range spec.Series {
		xArr := s.X
		if len(xArr) == 0 {
			xArr = make([]float64, len(s.Data))
			for i := range s.Data {
				xArr[i] = float64(i)
			}
		}
		dirArr := s.Direction
		if len(dirArr) == 0 {
			dirArr = make([]float64, len(s.Data))
		}
		lenArr := s.Length
		if len(lenArr) == 0 {
			lenArr = make([]float64, len(s.Data))
		}
		nPts := len(xArr)
		if len(s.Data) < nPts {
			nPts = len(s.Data)
		}
		if len(dirArr) < nPts {
			nPts = len(dirArr)
		}
		if len(lenArr) < nPts {
			nPts = len(lenArr)
		}
		for i := 0; i < nPts; i++ {
			b.WriteString(`<tr><th scope="row">` + esc(s.Name) + `</th><td>` +
				esc(fmtNum(xArr[i])) + `</td><td>` + esc(fmtNum(s.Data[i])) + `</td><td>` +
				esc(fmtNum(dirArr[i])) + `</td><td>` + esc(fmtNum(lenArr[i])) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}

func capabilityError(received string) error {
	return &CapabilityError{
		Code:    "E_CAPABILITY",
		Path:    "$.type",
		Message: fmt.Sprintf("unsupported chart type %q", received),
		Details: map[string]interface{}{
			"expected": Capabilities().ChartTypes,
			"received": received,
		},
	}
}

// RenderSVG renders a spec to an SVG string, dispatched by chart type.
func RenderSVG(spec *ChartSpec) (string, error) {
	typ := spec.Type
	if typ == "" {
		typ = "line"
	}
	var svg string
	switch typ {
	case "area":
		svg = renderAreaSVG(spec)
	case "arearange":
		svg = renderAreaRangeSVG(spec)
	case "bar":
		svg = renderBarSVG(spec)
	case "boxplot":
		svg = renderBoxplotSVG(spec)
	case "bullet":
		svg = renderBulletSVG(spec)
	case "combo":
		svg = renderComboSVG(spec)
	case "dumbbell":
		svg = renderDumbbellSVG(spec)
	case "funnel":
		svg = renderFunnelSVG(spec)
	case "gauge":
		svg = renderGaugeSVG(spec)
	case "candlestick":
		svg = renderCandlestickSVG(spec)
	case "column":
		svg = renderColumnSVG(spec)
	case "columnrange":
		svg = renderColumnRangeSVG(spec)
	case "error-bar":
		svg = renderErrorBarSVG(spec)
	case "flame-chart":
		svg = renderFlameChartSVG(spec)
	case "histogram":
		svg = renderHistogramSVG(spec)
	case "line":
		svg = renderLineSVG(spec)
	case "lollipop":
		svg = renderLollipopSVG(spec)
	case "pie":
		svg = renderPieSVG(spec)
	case "scatter":
		svg = renderScatterSVG(spec)
	case "streamgraph":
		svg = renderStreamgraphSVG(spec)
	case "technical-indicators":
		svg = renderTechnicalIndicatorsSVG(spec)
	case "bubble":
		svg = renderBubbleSVG(spec)
	case "timeline":
		svg = renderTimelineSVG(spec)
	case "variwide":
		svg = renderVariwideSVG(spec)
	case "vector-plot":
		svg = renderVectorPlotSVG(spec)
	case "waterfall":
		svg = renderWaterfallSVG(spec)
	case "windbarb":
		svg = renderWindbarbSVG(spec)
	case "xrange":
		svg = renderXRangeSVG(spec)
	default:
		return "", capabilityError(typ)
	}
	if err := enforceSVGLimit(svg); err != nil {
		return "", err
	}
	return svg, nil
}

// runtimeJS loads the shared interaction runtime. Canonical source is
// <repo>/runtime/chart-interactions.js; override with STONECHARTS_RUNTIME.
func runtimeJS() string {
	candidates := []string{}
	if p := os.Getenv("STONECHARTS_RUNTIME"); p != "" {
		candidates = append(candidates, p)
	}
	candidates = append(candidates,
		filepath.Join("runtime", "chart-interactions.js"),
		filepath.Join("..", "..", "runtime", "chart-interactions.js"),
	)
	for _, c := range candidates {
		if b, err := os.ReadFile(c); err == nil {
			return string(b)
		}
	}
	return "/* StoneCharts runtime not found */"
}

// RenderHTML returns a self-contained interactive HTML document for the chart.
func RenderHTML(spec *ChartSpec, pageTitle string) (string, error) {
	svg, err := RenderSVG(spec)
	if err != nil {
		return "", err
	}
	title := pageTitle
	if title == "" {
		title = spec.Title
	}
	if title == "" {
		title = "StoneCharts"
	}
	wrapStyle := ""
	if spec.Responsive {
		wrapStyle = fmt.Sprintf(` style="display:block;width:100%%;max-width:%dpx;aspect-ratio:%d / %d"`, spec.Width, spec.Width, spec.Height)
	}
	table := ""
	if spec.a11yOn() {
		table = dataTable(spec)
	}
	return "<!doctype html>\n" +
		`<html lang="en"><head><meta charset="utf-8">` +
		`<meta name="viewport" content="width=device-width,initial-scale=1">` +
		"<title>" + esc(title) + "</title>\n" +
		"<style>" + cssBlock + "</style></head>\n" +
		"<body>\n" +
		`<div class="sc-chart-wrap"` + wrapStyle + `>` + svg + table + `<div class="sc-tooltip" style="display:none"></div></div>` + "\n" +
		"<script>" + runtimeJS() + "</script>\n" +
		"</body></html>\n", nil
}

// SaveHTML writes the interactive HTML document to path.
func SaveHTML(spec *ChartSpec, path, pageTitle string) error {
	html, err := RenderHTML(spec, pageTitle)
	if err != nil {
		return err
	}
	return os.WriteFile(path, []byte(html), 0o644)
}
