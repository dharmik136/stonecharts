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

type ChartSpec struct {
	Type       string   `json:"type"`
	ID         string   `json:"id,omitempty"`
	Title      string   `json:"title,omitempty"`
	Subtitle   string   `json:"subtitle,omitempty"`
	Width      int      `json:"width,omitempty"`
	Height     int      `json:"height,omitempty"`
	Legend     *bool    `json:"legend,omitempty"`
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

// gridEnabled / gridColor / gridDashStyle resolve yAxis gridline defaults.
func (a *Axis) gridEnabled() bool {
	return a.GridLine == nil || a.GridLine.Enabled == nil || *a.GridLine.Enabled
}
func (a *Axis) gridColor() string {
	if a.GridLine != nil && a.GridLine.Color != "" {
		return a.GridLine.Color
	}
	return "#e8e8ee"
}
func (a *Axis) gridDashStyle() string {
	if a.GridLine != nil && a.GridLine.DashStyle != "" {
		return a.GridLine.DashStyle
	}
	return "solid"
}

// FromJSON parses a spec (matching spec/chart-spec.schema.json) and applies defaults.
// Unknown keys are ignored (forward-compatible).
func FromJSON(b []byte) (*ChartSpec, error) {
	var c ChartSpec
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, err
	}
	c.applyDefaults()
	return &c, nil
}
