// Package stonecharts is the Go edition of StoneCharts. It builds the same
// language-agnostic chart spec (spec/chart-spec.schema.json) and renders it to
// contract-compliant SVG (spec/svg-contract.md), byte-compatible with the other
// language libraries.
//
// Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
package stonecharts

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

type Binning struct {
	Count *int     `json:"count,omitempty"`
	Width *float64 `json:"width,omitempty"`
	Start *float64 `json:"start,omitempty"`
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

// Datum is one (x, y) or (x, y, z) observation — the scatter (§3.3 Rank 3) /
// bubble (§3.3 Rank 4) point model. Populated on every Series (see
// Series.UnmarshalJSON) but read ONLY by the scatter/bubble renderers; every
// other chart type continues to read Series.Data (plain float y-values, x =
// category index) completely unchanged, so this addition carries zero
// byte-parity risk for line/column/area/bar.
type Datum struct {
	X float64
	Y float64
	Z *float64 // bubble only (§3.3 Rank 4); nil for scatter, always set for bubble
}

// RangePoint bundles low/high (and optional center value) into one object,
// replacing parallel data[]+low[]+high[] arrays for range chart types.
type RangePoint struct {
	Low      float64 `json:"low"`
	High     float64 `json:"high"`
	Value    *float64 `json:"value,omitempty"`
	Category string   `json:"category,omitempty"`
	Name     string   `json:"name,omitempty"`
}

// BoxDatum is a 5-number summary for one category in a boxplot chart.
type BoxDatum struct {
	Low      float64   `json:"low"`
	Q1       float64   `json:"q1"`
	Median   float64   `json:"median"`
	Q3       float64   `json:"q3"`
	High     float64   `json:"high"`
	Outliers []float64 `json:"outliers,omitempty"`
}

// OHLCDatum is one Open-High-Low-Close observation for candlestick charts.
type OHLCDatum struct {
	Open  float64 `json:"open"`
	High  float64 `json:"high"`
	Low   float64 `json:"low"`
	Close float64 `json:"close"`
}

// Indicator describes a technical indicator overlay (SMA, EMA, etc.).
type Indicator struct {
	Type      string                 `json:"type"`
	Period    *int                   `json:"period,omitempty"`
	Color     string                 `json:"color,omitempty"`
	DashStyle string                 `json:"dashStyle,omitempty"`
	Params    map[string]interface{} `json:"params,omitempty"`
	Pane      *int                   `json:"pane,omitempty"`
}

// Flag marks a point event on the chart.
type Flag struct {
	X     float64 `json:"x"`
	Title string  `json:"title"`
	Text  string  `json:"text,omitempty"`
	Color string  `json:"color,omitempty"`
	Shape string  `json:"shape,omitempty"`
}

// PlotBand is a horizontal band across the plot area.
type PlotBand struct {
	From    float64  `json:"from"`
	To      float64  `json:"to"`
	Color   string   `json:"color"`
	Label   string   `json:"label,omitempty"`
	Opacity *float64 `json:"opacity,omitempty"`
}

// PlotLine is a horizontal reference line on an axis.
type PlotLine struct {
	Value     float64  `json:"value"`
	Color     string   `json:"color"`
	Width     *float64 `json:"width,omitempty"`
	DashStyle string   `json:"dashStyle,omitempty"`
	Label     string   `json:"label,omitempty"`
}

// GaugeBand is a colored range band on a gauge chart.
type GaugeBand struct {
	From  float64 `json:"from"`
	To    float64 `json:"to"`
	Color string  `json:"color"`
}

// Pane defines a sub-pane (e.g. for indicators rendered below the main chart).
type Pane struct {
	Height    *float64   `json:"height,omitempty"`
	Min       *float64   `json:"min,omitempty"`
	Max       *float64   `json:"max,omitempty"`
	Title     string     `json:"title,omitempty"`
	PlotBands []PlotBand `json:"plotBands,omitempty"`
	PlotLines []PlotLine `json:"plotLines,omitempty"`
}

type Series struct {
	Name        string          `json:"name"`
	Data        []float64       `json:"data"`
	DataPoints  []Datum         `json:"-"`                     // scatter only — see Datum; built by UnmarshalJSON
	Type        string          `json:"type,omitempty"`        // line | column (combo per-series mark kind)
	YAxis       int             `json:"yAxis,omitempty"`       // 0 -> primary yAxis; 1 -> secondaryYAxis
	Color       json.RawMessage `json:"color,omitempty"`       // hex string OR gradient object
	FillOpacity float64         `json:"fillOpacity,omitempty"` // >0 -> area fill
	Pattern     *Pattern        `json:"pattern,omitempty"`     // hatch fill for the area
	LineWidth   float64         `json:"lineWidth,omitempty"`   // 0 -> default 2
	DashStyle   string          `json:"dashStyle,omitempty"`   // "" -> solid
	Step        string          `json:"step,omitempty"`        // "" | before | after | center
	Curve       string          `json:"curve,omitempty"`       // "" / linear | monotone
	Marker      *Marker         `json:"marker,omitempty"`
	Regression  bool            `json:"regression,omitempty"`
	Low         []float64       `json:"low,omitempty"`
	High        []float64       `json:"high,omitempty"`
	RangeData   []RangePoint    `json:"rangeData,omitempty"`
	OHLC        []OHLCDatum     `json:"ohlc,omitempty"`
	BoxData     []BoxDatum      `json:"boxData,omitempty"`
	Widths      []float64       `json:"widths,omitempty"`
	Labels      []string        `json:"labels,omitempty"`
	X           []float64       `json:"x,omitempty"`
	Z           []float64       `json:"z,omitempty"`
	Direction   []float64       `json:"direction,omitempty"`
	Length      []float64       `json:"length,omitempty"`
	Spans       []SpanDatum     `json:"spans,omitempty"`
	Frames      []FrameDatum    `json:"frames,omitempty"`
	Volume     []float64   `json:"volume,omitempty"`
	Indicators []Indicator `json:"indicators,omitempty"`
}

type FrameDatum struct {
	X     float64 `json:"x"`
	X2    float64 `json:"x2"`
	Depth int     `json:"depth"`
	Name  string  `json:"name,omitempty"`
	Color string  `json:"color,omitempty"`
}

type SpanDatum struct {
	X          float64  `json:"x"`
	X2         float64  `json:"x2"`
	Y          int      `json:"y"`
	ID         string   `json:"id,omitempty"`
	Name       string   `json:"name,omitempty"`
	Dependency []string `json:"dependency,omitempty"`
	Milestone  bool     `json:"milestone,omitempty"`
}

// UnmarshalJSON normalizes the point model (§3.3 Rank 3 / §5.4b lockstep):
// each data[i] element is a bare number, a positional [x,y] pair, or an
// {x,y} object. validate() already rejected any other shape by the time this
// runs. Data []float64 is populated only when every element in the series is
// a bare number (reproducing the exact original decode for line/column/
// area/bar); DataPoints []Datum is always populated in lockstep so scatter
// can read it regardless of which literal form the input used.
func (s *Series) UnmarshalJSON(b []byte) error {
	type seriesAlias Series
	aux := struct {
		Data []json.RawMessage `json:"data"`
		*seriesAlias
	}{seriesAlias: (*seriesAlias)(s)}
	if err := json.Unmarshal(b, &aux); err != nil {
		return err
	}
	nums := make([]float64, 0, len(aux.Data))
	points := make([]Datum, 0, len(aux.Data))
	allNumeric := true
	for i, raw := range aux.Data {
		trimmed := bytes.TrimSpace(raw)
		switch {
		case len(trimmed) > 0 && trimmed[0] == '{':
			var obj struct {
				X float64  `json:"x"`
				Y float64  `json:"y"`
				Z *float64 `json:"z"`
			}
			if err := json.Unmarshal(raw, &obj); err != nil {
				return err
			}
			points = append(points, Datum{X: obj.X, Y: obj.Y, Z: obj.Z})
			allNumeric = false
		case len(trimmed) > 0 && trimmed[0] == '[':
			var tuple []float64
			if err := json.Unmarshal(raw, &tuple); err != nil {
				return err
			}
			d := Datum{X: tuple[0], Y: tuple[1]}
			if len(tuple) > 2 {
				z := tuple[2]
				d.Z = &z
			}
			points = append(points, d)
			allNumeric = false
		default:
			var v float64
			if err := json.Unmarshal(raw, &v); err != nil {
				return err
			}
			nums = append(nums, v)
			points = append(points, Datum{X: float64(i), Y: v})
		}
	}
	if allNumeric {
		s.Data = nums
	} else {
		s.Data = nil
	}
	s.DataPoints = points
	return nil
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
	BinEdges   []float64 `json:"binEdges,omitempty"`
	Min        *float64  `json:"min,omitempty"`
	Max        *float64  `json:"max,omitempty"`
	GridLine   *GridLine `json:"gridLine,omitempty"` // yAxis only
	Opposite   *bool     `json:"opposite,omitempty"` // secondaryYAxis only
	PlotBands []PlotBand `json:"plotBands,omitempty"`
	PlotLines []PlotLine `json:"plotLines,omitempty"`
}

type Margin struct {
	Top    *float64 `json:"top,omitempty"`
	Right  *float64 `json:"right,omitempty"`
	Bottom *float64 `json:"bottom,omitempty"`
	Left   *float64 `json:"left,omitempty"`
}

type Layout struct {
	Margin *Margin `json:"margin,omitempty"`
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

type Connector struct {
	Enabled   *bool  `json:"enabled,omitempty"`
	DashStyle string `json:"dashStyle,omitempty"`
}

type ChartSpec struct {
	Type                   string          `json:"type"`
	ID                     string          `json:"id,omitempty"`
	Theme                  json.RawMessage `json:"theme,omitempty"` // name string OR theme object
	theme                  *Theme          // resolved (set in applyDefaults)
	Title                  string          `json:"title,omitempty"`
	Subtitle               string          `json:"subtitle,omitempty"`
	Width                  pxInt           `json:"width,omitempty"`
	Height                 pxInt           `json:"height,omitempty"`
	Legend                 *bool           `json:"legend,omitempty"`
	A11y                   *bool           `json:"a11y,omitempty"` // nil -> true
	Responsive             bool            `json:"responsive,omitempty"`
	Layout                 *Layout         `json:"layout,omitempty"`
	Stacking               string          `json:"stacking,omitempty"`    // "" | "normal" | "percent"
	Grouping               *bool           `json:"grouping,omitempty"`    // nil -> true
	Orientation            string          `json:"orientation,omitempty"` // "" -> "vertical"; "horizontal" for bar-range
	Binning                *Binning        `json:"binning,omitempty"`
	PreBinned              bool            `json:"preBinned,omitempty"`
	Normalization          string          `json:"normalization,omitempty"`
	Overlay                string          `json:"overlay,omitempty"`
	Subtype                string          `json:"subtype,omitempty"`
	UpColor                string          `json:"upColor,omitempty"`
	DownColor              string          `json:"downColor,omitempty"`
	TotalColor             string          `json:"totalColor,omitempty"`
	SumIndices             []int           `json:"sumIndices,omitempty"`
	IntermediateSumIndices []int           `json:"intermediateSumIndices,omitempty"`
	Connector              *Connector      `json:"connector,omitempty"`
	BulletTarget           *float64        `json:"bulletTarget,omitempty"`
	BulletRanges           []float64       `json:"bulletRanges,omitempty"`
	NeckWidth              *float64        `json:"neckWidth,omitempty"`
	NeckHeight             *float64        `json:"neckHeight,omitempty"`
	MinWidth               *float64        `json:"minWidth,omitempty"`
	SpeedUnit              string          `json:"speedUnit,omitempty"`
	CalmThreshold          *float64        `json:"calmThreshold,omitempty"`
	Hemisphere             string          `json:"hemisphere,omitempty"`
	BarbLength             *float64        `json:"barbLength,omitempty"`
	YOffset                *float64        `json:"yOffset,omitempty"`
	Offset                 string          `json:"offset,omitempty"` // streamgraph: "wiggle" | "silhouette"
	VectorLength           *float64        `json:"vectorLength,omitempty"`
	RotationOrigin         string          `json:"rotationOrigin,omitempty"`
	InnerSize              *float64        `json:"innerSize,omitempty"`
	MinSize                *float64        `json:"minSize,omitempty"`
	GaugeMin               *float64        `json:"gaugeMin,omitempty"`
	GaugeMax               *float64        `json:"gaugeMax,omitempty"`
	GaugeBands             []GaugeBand     `json:"gaugeBands,omitempty"`
	OutOfRange             string          `json:"outOfRange,omitempty"`
	XAxis                  Axis            `json:"xAxis"`
	YAxis                  Axis            `json:"yAxis"`
	SecondaryYAxis         *Axis           `json:"secondaryYAxis,omitempty"`
	Series                 []Series        `json:"series"`
	Flags []Flag `json:"flags,omitempty"`
	Panes []Pane `json:"panes,omitempty"`
}

// applyDefaults mirrors the Python ChartSpec defaults so the two libraries
// produce identical output from the same input.
func (c *ChartSpec) applyDefaults() {
	if c.Type == "" {
		c.Type = "line"
	}
	if c.ID == "" {
		c.ID = "sc"
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
	if c.OutOfRange == "" {
		c.OutOfRange = "error"
	}
	for i := range c.Series {
		if c.Series[i].Name == "" {
			c.Series[i].Name = "Series " + strconv.Itoa(i+1)
		}
		if c.Series[i].Type == "" {
			c.Series[i].Type = "column"
		}
		if len(c.Series[i].RangeData) > 0 {
			rd := c.Series[i].RangeData
			n := len(rd)
			switch c.Type {
			case "arearange":
				c.Series[i].Data = make([]float64, n)
				c.Series[i].Low = make([]float64, n)
				for j, rp := range rd {
					c.Series[i].Data[j] = rp.High
					c.Series[i].Low[j] = rp.Low
				}
			case "error-bar":
				c.Series[i].Data = make([]float64, n)
				c.Series[i].Low = make([]float64, n)
				c.Series[i].High = make([]float64, n)
				for j, rp := range rd {
					if rp.Value != nil {
						c.Series[i].Data[j] = *rp.Value
					}
					c.Series[i].Low[j] = rp.Low
					c.Series[i].High[j] = rp.High
				}
			case "columnrange", "dumbbell":
				c.Series[i].Data = make([]float64, n)
				c.Series[i].High = make([]float64, n)
				for j, rp := range rd {
					c.Series[i].Data[j] = rp.Low
					c.Series[i].High[j] = rp.High
				}
			}
		}
	}
}

func (c *ChartSpec) legendOn() bool   { return c.Legend == nil || *c.Legend }
func (c *ChartSpec) a11yOn() bool     { return c.A11y == nil || *c.A11y }
func (c *ChartSpec) groupingOn() bool { return c.Grouping == nil || *c.Grouping }

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
	if len(b) > MaxSpecBytes {
		return nil, &ResourceLimitError{Code: "LIMIT.SPEC_BYTES", Path: "$", Limit: MaxSpecBytes, Received: len(b)}
	}
	var raw interface{}
	if err := json.Unmarshal(b, &raw); err != nil {
		return nil, err
	}
	if err := enforceSpecLimits(raw, len(b)); err != nil {
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
