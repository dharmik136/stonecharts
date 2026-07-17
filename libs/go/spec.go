// Package peakcharts is the Go edition of PeakCharts. It builds the same
// language-agnostic chart spec (spec/chart-spec.schema.json) and renders it to
// contract-compliant SVG (spec/svg-contract.md), byte-compatible with the other
// language libraries.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package peakcharts

import (
	"encoding/json"
	"strconv"
)

type Marker struct {
	Enabled *bool   `json:"enabled,omitempty"` // nil -> true
	Symbol  string  `json:"symbol,omitempty"`  // circle | square | triangle | diamond
	Radius  float64 `json:"radius,omitempty"`  // 0 -> default 3.5
}

type Series struct {
	Name      string    `json:"name"`
	Data      []float64 `json:"data"`
	Color     string    `json:"color,omitempty"`
	LineWidth float64   `json:"lineWidth,omitempty"` // 0 -> default 2
	DashStyle string    `json:"dashStyle,omitempty"` // "" -> solid
	Step      string    `json:"step,omitempty"`      // "" | before | after | center
	Curve     string    `json:"curve,omitempty"`     // "" / linear | monotone
	Marker    *Marker   `json:"marker,omitempty"`
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
