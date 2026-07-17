package peakcharts

import (
	"fmt"
	"os"
	"path/filepath"
)

const cssBlock = `.pk-chart-wrap{position:relative;display:inline-block;line-height:0}
  .pk-chart{display:block;background:#fff}
  .pk-point{cursor:pointer;transition:r .08s ease}
  .pk-legend-item.pk-hidden{opacity:.35}
  .pk-tooltip{position:absolute;pointer-events:none;z-index:10;background:rgba(255,255,255,.97);
    border:1px solid #d8d8e0;border-radius:6px;box-shadow:0 4px 14px rgba(20,20,40,.14);
    padding:7px 10px;font:12px/1.4 Segoe UI,Helvetica,Arial,sans-serif;color:#22223a;white-space:nowrap}
  .pk-tt-title{font-weight:600;margin-bottom:2px}
  .pk-tt-row{display:flex;align-items:center}
  .pk-tt-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}`

// RenderSVG renders a spec to an SVG string, dispatched by chart type.
func RenderSVG(spec *ChartSpec) string {
	switch spec.Type {
	case "line", "":
		return renderLineSVG(spec)
	default:
		panic(fmt.Sprintf("unknown chart type %q", spec.Type))
	}
}

// runtimeJS loads the shared interaction runtime. Canonical source is
// <repo>/runtime/chart-interactions.js; override with PEAKCHARTS_RUNTIME.
func runtimeJS() string {
	candidates := []string{}
	if p := os.Getenv("PEAKCHARTS_RUNTIME"); p != "" {
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
	return "/* PeakCharts runtime not found */"
}

// RenderHTML returns a self-contained interactive HTML document for the chart.
func RenderHTML(spec *ChartSpec, pageTitle string) string {
	svg := RenderSVG(spec)
	title := pageTitle
	if title == "" {
		title = spec.Title
	}
	if title == "" {
		title = "PeakCharts"
	}
	wrapStyle := ""
	if spec.Responsive {
		wrapStyle = fmt.Sprintf(` style="display:block;width:100%%;max-width:%dpx;aspect-ratio:%d / %d"`, spec.Width, spec.Width, spec.Height)
	}
	return "<!doctype html>\n" +
		`<html lang="en"><head><meta charset="utf-8">` +
		`<meta name="viewport" content="width=device-width,initial-scale=1">` +
		"<title>" + esc(title) + "</title>\n" +
		"<style>" + cssBlock + "</style></head>\n" +
		"<body>\n" +
		`<div class="pk-chart-wrap"` + wrapStyle + `>` + svg + `<div class="pk-tooltip" style="display:none"></div></div>` + "\n" +
		"<script>" + runtimeJS() + "</script>\n" +
		"</body></html>\n"
}

// SaveHTML writes the interactive HTML document to path.
func SaveHTML(spec *ChartSpec, path, pageTitle string) error {
	return os.WriteFile(path, []byte(RenderHTML(spec, pageTitle)), 0o644)
}
