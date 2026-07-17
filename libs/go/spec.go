// Package peakcharts is the Go edition of PeakCharts. It builds the same
// language-agnostic chart spec (spec/chart-spec.schema.json) and renders it to
// contract-compliant SVG (spec/svg-contract.md), byte-compatible with the other
// language libraries.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package peakcharts

import (
	"bytes"
	"encoding/json"
	"strconv"
)

type Marker struct {
	Enabled *bool   `json:"enabled,omitempty"` // nil -> true
	Symbol  string  `json:"symbol,omitempty"`  // circle | square | triangle | diamond
	Radius  float64 `json:"radius,omitempty"`  // 0 -> default 3.5
}

type GradientStop struct {
	Offset  float64  `json:"offset"`
	Color   string   `json:"color"`
	Opacity *float64 `json:"opacity,omitempty"` // nil -> no stop-opacity attr
}

// Gradient direction is x1,y1 -> x2,y2 in 0..1 objectBoundingBox coords.
// Pointers distinguish "absent" from 0 so defaults (0,0,0,1) match Python exactly.
type Gradient struct {
	Type  string         `json:"type,omitempty"`
	X1    *float64       `json:"x1,omitempty"`
	Y1    *float64       `json:"y1,omitempty"`
	X2    *float64       `json:"x2,omitempty"`
	Y2    *float64       `json:"y2,omitempty"`
	Stops []GradientStop `json:"stops"`
}

func fdef(p *float64, def float64) float64 {
	if p != nil {
		return *p
	}
	return def
}
func (g *Gradient) x1() float64 { return fdef(g.X1, 0) }
func (g *Gradient) y1() float64 { return fdef(g.Y1, 0) }
func (g *Gradient) x2() float64 { return fdef(g.X2, 0) }
func (g *Gradient) y2() float64 { return fdef(g.Y2, 1) }

// Pattern is a diagonal hatch fill for the area under the line.
type Pattern struct {
	Type        string   `json:"type,omitempty"`
	Color       string   `json:"color,omitempty"`
	Background  string   `json:"background,omitempty"`
	Size        *float64 `json:"size,omitempty"`
	Angle       *float64 `json:"angle,omitempty"`
	StrokeWidth *float64 `json:"strokeWidth,omitempty"`
}

func (p *Pattern) size() float64        { return fdef(p.Size, 8) }
func (p *Pattern) angle() float64       { return fdef(p.Angle, 45) }
func (p *Pattern) strokeWidth() float64 { return fdef(p.StrokeWidth, 1.5) }
func (p *Pattern) hatchColor() string {
	if p.Color != "" {
		return p.Color
	}
	return "#333333"
}

type Series struct {
	Name        string          `json:"name"`
	Data        []float64       `json:"data"`
	Color       json.RawMessage `json:"color,omitempty"`       // hex string OR gradient object
	FillOpacity float64         `json:"fillOpacity,omitempty"` // >0 -> area fill
	Pattern     *Pattern        `json:"pattern,omitempty"`     // hatch fill for the area
	LineWidth   float64         `json:"lineWidth,omitempty"`   // 0 -> default 2
	DashStyle   string          `json:"dashStyle,omitempty"`   // "" -> solid
	Step        string          `json:"step,omitempty"`        // "" | before | after | center
	Curve       string          `json:"curve,omitempty"`       // "" / linear | monotone
	Marker      *Marker         `json:"marker,omitempty"`
}

// colorSpec resolves Color (a hex string or a gradient object).
// Returns (gradient, solidHex); solid "" means unset -> caller uses the palette.
func (s *Series) colorSpec() (*Gradient, string) {
	raw := bytes.TrimSpace([]byte(s.Color))
	if len(raw) == 0 || string(raw) == "null" {
		return nil, ""
	}
	if raw[0] == '"' {
		var str string
		if json.Unmarshal(raw, &str) == nil {
			return nil, str
		}
		return nil, ""
	}
	var g Gradient
	if json.Unmarshal(raw, &g) == nil {
		return &g, ""
	}
	return nil, ""
}

func (s *Series) lineWidth() float64 {
	if s.LineWidth != 0 {
		return s.LineWidth
	}
	return 2
}
func (s *Series) markerEnabled() bool {
	return s.Marker == nil || s.Marker.Enabled == nil || *s.Marker.Enabled
}
func (s *Series) markerSymbol() string {
	if s.Marker != nil && s.Marker.Symbol != "" {
		return s.Marker.Symbol
	}
	return "circle"
}
func (s *Series) markerRadius() float64 {
	if s.Marker != nil && s.Marker.Radius != 0 {
		return s.Marker.Radius
	}
	return 3.5
}

type GridLine struct {
	Enabled   *bool  `json:"enabled,omitempty"` // nil -> true
	Color     string `json:"color,omitempty"`   // "" -> default #e8e8ee
	DashStyle string `json:"dashStyle,omitempty"`
}

type Axis struct {
	Title      string    `json:"title,omitempty"`
	Categories []string  `json:"categories,omitempty"`
	Min        *float64  `json:"min,omitempty"`
	Max        *float64  `json:"max,omitempty"`
	GridLine   *GridLine `json:"gridLine,omitempty"` // yAxis only
}

// Theme is a concrete color set (canonical values in spec/themes/*.json).
type Theme struct {
	Name            string   `json:"name,omitempty"`
	Background      string   `json:"background,omitempty"` // "" -> transparent (no <rect>)
	TitleColor      string   `json:"titleColor,omitempty"`
	SubtitleColor   string   `json:"subtitleColor,omitempty"`
	AxisLabelColor  string   `json:"axisLabelColor,omitempty"`
	AxisTitleColor  string   `json:"axisTitleColor,omitempty"`
	GridColor       string   `json:"gridColor,omitempty"`
	AxisLineColor   string   `json:"axisLineColor,omitempty"`
	CrosshairColor  string   `json:"crosshairColor,omitempty"`
	MarkerHalo      string   `json:"markerHalo,omitempty"`
	LegendTextColor string   `json:"legendTextColor,omitempty"`
	Palette         []string `json:"palette,omitempty"`
}

func lightTheme() Theme {
	return Theme{
		Name: "light", Background: "",
		TitleColor: "#1a1a2e", SubtitleColor: "#6b6b80",
		AxisLabelColor: "#6b6b80", AxisTitleColor: "#4a4a5a",
		GridColor: "#e8e8ee", AxisLineColor: "#b6b6c2",
		CrosshairColor: "#c0c0cc", MarkerHalo: "#fff", LegendTextColor: "#33334d",
		Palette: []string{"#2f7ed8", "#f45b5b", "#8bbc21", "#e4a812", "#1aadce", "#8e44ad", "#f28f43", "#77a1e5"},
	}
}

func darkTheme() Theme {
	return Theme{
		Name: "dark", Background: "#1a1a2e",
		TitleColor: "#f5f5fa", SubtitleColor: "#a0a0b8",
		AxisLabelColor: "#9a9ab0", AxisTitleColor: "#c8c8d8",
		GridColor: "#2e2e44", AxisLineColor: "#45455a",
		CrosshairColor: "#55556a", MarkerHalo: "#1a1a2e", LegendTextColor: "#d0d0e0",
		Palette: []string{"#5aa2f0", "#ff7a7a", "#a3d95a", "#f5c542", "#3ec8e0", "#b57ae0", "#ff9d5c", "#93b8ff"},
	}
}

func builtinTheme(name string) (Theme, bool) {
	switch name {
	case "light":
		return lightTheme(), true
	case "dark":
		return darkTheme(), true
	}
	return Theme{}, false
}

// resolveTheme mirrors spec.py resolve_theme: a name, a custom object (overriding
// a named base), or absent -> light.
func resolveTheme(raw json.RawMessage) *Theme {
	b := bytes.TrimSpace([]byte(raw))
	if len(b) == 0 || string(b) == "null" {
		t := lightTheme()
		return &t
	}
	if b[0] == '"' {
		var name string
		_ = json.Unmarshal(b, &name)
		if t, ok := builtinTheme(name); ok {
			return &t
		}
		t := lightTheme()
		return &t
	}
	var over Theme
	if json.Unmarshal(b, &over) != nil {
		t := lightTheme()
		return &t
	}
	base, ok := builtinTheme(over.Name)
	if !ok {
		base = lightTheme()
	}
	// Custom theme values are user input -> escape so a hostile color can't break
	// out of the SVG attribute it lands in.
	if over.Name != "" {
		base.Name = over.Name
	}
	if over.Background != "" {
		base.Background = esc(over.Background)
	}
	if over.TitleColor != "" {
		base.TitleColor = esc(over.TitleColor)
	}
	if over.SubtitleColor != "" {
		base.SubtitleColor = esc(over.SubtitleColor)
	}
	if over.AxisLabelColor != "" {
		base.AxisLabelColor = esc(over.AxisLabelColor)
	}
	if over.AxisTitleColor != "" {
		base.AxisTitleColor = esc(over.AxisTitleColor)
	}
	if over.GridColor != "" {
		base.GridColor = esc(over.GridColor)
	}
	if over.AxisLineColor != "" {
		base.AxisLineColor = esc(over.AxisLineColor)
	}
	if over.CrosshairColor != "" {
		base.CrosshairColor = esc(over.CrosshairColor)
	}
	if over.MarkerHalo != "" {
		base.MarkerHalo = esc(over.MarkerHalo)
	}
	if over.LegendTextColor != "" {
		base.LegendTextColor = esc(over.LegendTextColor)
	}
	if len(over.Palette) > 0 {
		pal := make([]string, len(over.Palette))
		for i, c := range over.Palette {
			pal[i] = esc(c)
		}
		base.Palette = pal
	}
	return &base
}

// pxInt is an int that also accepts an integer-valued JSON float (e.g. 5.0).
// The validator already guarantees width/height are integer-valued numbers; this
// lets the struct decode 5.0 the same way Python's int(5.0) does, keeping parity.
type pxInt int

func (n *pxInt) UnmarshalJSON(b []byte) error {
	var f float64
	if err := json.Unmarshal(b, &f); err != nil {
		return err
	}
	*n = pxInt(f)
	return nil
}

type ChartSpec struct {
	Type       string          `json:"type"`
	ID         string          `json:"id,omitempty"`
	Theme      json.RawMessage `json:"theme,omitempty"` // name string OR theme object
	theme      *Theme          // resolved (set in applyDefaults)
	Title      string          `json:"title,omitempty"`
	Subtitle   string   `json:"subtitle,omitempty"`
	Width      pxInt    `json:"width,omitempty"`
	Height     pxInt    `json:"height,omitempty"`
	Legend     *bool    `json:"legend,omitempty"`
	A11y       *bool    `json:"a11y,omitempty"` // nil -> true
	Responsive bool     `json:"responsive,omitempty"`
	XAxis      Axis     `json:"xAxis"`
	YAxis      Axis     `json:"yAxis"`
	Series     []Series `json:"series"`
}

// applyDefaults mirrors the Python ChartSpec defaults so the two libraries
// produce identical output from the same input.
func (c *ChartSpec) applyDefaults() {
	if c.Type == "" {
		c.Type = "line"
	}
	if c.ID == "" {
		c.ID = "pk"
	}
	c.theme = resolveTheme(c.Theme)
	if c.Width == 0 {
		c.Width = 820
	}
	if c.Height == 0 {
		c.Height = 460
	}
	if c.Legend == nil {
		t := true
		c.Legend = &t
	}
	for i := range c.Series {
		if c.Series[i].Name == "" {
			c.Series[i].Name = "Series " + strconv.Itoa(i+1)
		}
	}
}

func (c *ChartSpec) legendOn() bool { return c.Legend == nil || *c.Legend }
func (c *ChartSpec) a11yOn() bool   { return c.A11y == nil || *c.A11y }

// gridEnabled / gridColor / gridDashStyle resolve yAxis gridline defaults.
func (a *Axis) gridEnabled() bool {
	return a.GridLine == nil || a.GridLine.Enabled == nil || *a.GridLine.Enabled
}
func (a *Axis) gridColorOr(def string) string {
	if a.GridLine != nil && a.GridLine.Color != "" {
		return a.GridLine.Color
	}
	return def
}
func (a *Axis) gridDashStyle() string {
	if a.GridLine != nil && a.GridLine.DashStyle != "" {
		return a.GridLine.DashStyle
	}
	return "solid"
}

// FromJSON parses a spec (matching spec/chart-spec.schema.json) and applies defaults.
// The spec is strictly validated first (same rules + error text as the Python
// renderer); a malformed spec returns a *SpecError. Unknown keys are ignored.
func FromJSON(b []byte) (*ChartSpec, error) {
	var raw interface{}
	if err := json.Unmarshal(b, &raw); err != nil {
		return nil, err
	}
	if errs := validate(raw); len(errs) > 0 {
		return nil, &SpecError{Errors: errs}
	}
	var c ChartSpec
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, err
	}
	c.applyDefaults()
	return &c, nil
}
