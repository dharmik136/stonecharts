package stonecharts

// CapabilityError is returned when a spec is structurally valid but requests an
// unsupported renderer capability.
type CapabilityError struct {
	Code    string                 `json:"code"`
	Path    string                 `json:"path"`
	Message string                 `json:"message"`
	Details map[string]interface{} `json:"details,omitempty"`
}

func (e *CapabilityError) Error() string {
	if e == nil {
		return ""
	}
	if e.Path != "" {
		return e.Path + ": " + e.Message
	}
	return e.Message
}

// ChartTypeMeta describes the certification tier and version origin of a chart type.
type ChartTypeMeta struct {
	Tier  string `json:"tier"`
	Since string `json:"since"`
}

// CapabilityManifest is the machine-readable active-release renderer contract.
type CapabilityManifest struct {
	SpecVersion        string                     `json:"specVersion"`
	SVGContractVersion string                     `json:"svgContractVersion"`
	ChartTypes         map[string]ChartTypeMeta   `json:"chartTypes"`
	Column             map[string][]string        `json:"column"`
	Bar                map[string][]string        `json:"bar"`
}

// --- BEGIN GENERATED FROM spec/capabilities.json ---
var activeCapabilities = CapabilityManifest{
	SpecVersion:        "0.0.0.1",
	SVGContractVersion: "0.0.0.1",
	ChartTypes: map[string]ChartTypeMeta{
		"area":                 {Tier: "certified", Since: "0.0.0.3"},
		"arearange":            {Tier: "certified", Since: "0.0.0.9"},
		"bar":                  {Tier: "certified", Since: "0.0.0.2"},
		"boxplot":              {Tier: "certified", Since: "0.0.0.12"},
		"bubble":               {Tier: "certified", Since: "0.0.0.4"},
		"bullet":               {Tier: "certified", Since: "0.0.0.11"},
		"candlestick":          {Tier: "certified", Since: "0.0.0.7"},
		"column":               {Tier: "certified", Since: "0.0.0.1"},
		"columnrange":          {Tier: "certified", Since: "0.0.0.9"},
		"combo":                {Tier: "certified", Since: "0.0.0.5"},
		"development-triangle": {Tier: "certified", Since: "0.0.0.33"},
		"dumbbell":             {Tier: "certified", Since: "0.0.0.14"},
		"error-bar":            {Tier: "certified", Since: "0.0.0.8"},
		"flame-chart":          {Tier: "certified", Since: "0.0.0.23"},
		"funnel":               {Tier: "certified", Since: "0.0.0.15"},
		"gauge":                {Tier: "certified", Since: "0.0.0.25"},
		"histogram":            {Tier: "certified", Since: "0.0.0.6"},
		"line":                 {Tier: "certified", Since: "0.0.0.1"},
		"lollipop":             {Tier: "certified", Since: "0.0.0.13"},
		"nightingale":          {Tier: "certified", Since: "0.0.0.30"},
		"parliament":           {Tier: "certified", Since: "0.0.0.32"},
		"pie":                  {Tier: "certified", Since: "0.0.0.24"},
		"polar":                {Tier: "certified", Since: "0.0.0.28"},
		"radar":                {Tier: "certified", Since: "0.0.0.27"},
		"radial-bar":           {Tier: "certified", Since: "0.0.0.31"},
		"scatter":              {Tier: "certified", Since: "0.0.0.3"},
		"solid-gauge":          {Tier: "certified", Since: "0.0.0.26"},
		"streamgraph":          {Tier: "certified", Since: "0.0.0.19"},
		"technical-indicators": {Tier: "certified", Since: "0.0.0.22"},
		"timeline":             {Tier: "certified", Since: "0.0.0.17"},
		"variwide":             {Tier: "certified", Since: "0.0.0.16"},
		"vector-plot":          {Tier: "certified", Since: "0.0.0.20"},
		"waterfall":            {Tier: "certified", Since: "0.0.0.10"},
		"wind-rose":            {Tier: "certified", Since: "0.0.0.29"},
		"windbarb":             {Tier: "certified", Since: "0.0.0.18"},
		"xrange":               {Tier: "certified", Since: "0.0.0.21"},
	},
	Column: map[string][]string{
		"grouping": {"grouped", "overlay"},
		"stacking": {"none", "normal", "percent-nonnegative"},
	},
	Bar: map[string][]string{
		"grouping": {"grouped", "overlay"},
		"stacking": {"none", "normal", "percent-nonnegative"},
	},
}
// --- END GENERATED FROM spec/capabilities.json ---

// ChartTypeNames returns a sorted list of all chart type names.
func (m CapabilityManifest) ChartTypeNames() []string {
	names := make([]string, 0, len(m.ChartTypes))
	for k := range m.ChartTypes {
		names = append(names, k)
	}
	// sort for determinism
	for i := 0; i < len(names); i++ {
		for j := i + 1; j < len(names); j++ {
			if names[i] > names[j] {
				names[i], names[j] = names[j], names[i]
			}
		}
	}
	return names
}

// Capabilities returns the machine-readable active renderer manifest.
func Capabilities() CapabilityManifest { return activeCapabilities }
