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

var activeCapabilities = CapabilityManifest{
	SpecVersion:        "0.0.0.1",
	SVGContractVersion: "0.0.0.1",
	ChartTypes: map[string]ChartTypeMeta{
		"area":                 {Tier: "certified", Since: "0.0.0.3"},
		"arearange":            {Tier: "candidate", Since: "0.0.0.9"},
		"bar":                  {Tier: "certified", Since: "0.0.0.2"},
		"boxplot":              {Tier: "candidate", Since: "0.0.0.12"},
		"bubble":               {Tier: "certified", Since: "0.0.0.4"},
		"bullet":               {Tier: "candidate", Since: "0.0.0.11"},
		"candlestick":          {Tier: "experimental", Since: "0.0.0.7"},
		"column":               {Tier: "certified", Since: "0.0.0.1"},
		"columnrange":          {Tier: "candidate", Since: "0.0.0.9"},
		"combo":                {Tier: "certified", Since: "0.0.0.5"},
		"dumbbell":             {Tier: "candidate", Since: "0.0.0.14"},
		"error-bar":            {Tier: "candidate", Since: "0.0.0.8"},
		"flame-chart":          {Tier: "experimental", Since: "0.0.0.23"},
		"funnel":               {Tier: "experimental", Since: "0.0.0.15"},
		"gauge":                {Tier: "experimental", Since: "0.0.0.25"},
		"histogram":            {Tier: "candidate", Since: "0.0.0.6"},
		"line":                 {Tier: "certified", Since: "0.0.0.1"},
		"lollipop":             {Tier: "experimental", Since: "0.0.0.13"},
		"nightingale":          {Tier: "experimental", Since: "0.0.0.30"},
		"parliament":           {Tier: "experimental", Since: "0.0.0.32"},
		"pie":                  {Tier: "experimental", Since: "0.0.0.24"},
		"polar":                {Tier: "experimental", Since: "0.0.0.28"},
		"radar":                {Tier: "experimental", Since: "0.0.0.27"},
		"radial-bar":           {Tier: "experimental", Since: "0.0.0.31"},
		"scatter":              {Tier: "certified", Since: "0.0.0.3"},
		"solid-gauge":          {Tier: "experimental", Since: "0.0.0.26"},
		"streamgraph":          {Tier: "experimental", Since: "0.0.0.19"},
		"technical-indicators": {Tier: "experimental", Since: "0.0.0.22"},
		"timeline":             {Tier: "experimental", Since: "0.0.0.17"},
		"variwide":             {Tier: "experimental", Since: "0.0.0.16"},
		"vector-plot":          {Tier: "experimental", Since: "0.0.0.20"},
		"waterfall":            {Tier: "candidate", Since: "0.0.0.10"},
		"wind-rose":            {Tier: "experimental", Since: "0.0.0.29"},
		"windbarb":             {Tier: "experimental", Since: "0.0.0.18"},
		"xrange":               {Tier: "experimental", Since: "0.0.0.21"},
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
