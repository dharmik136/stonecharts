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

// CapabilityManifest is the machine-readable active-release renderer contract.
type CapabilityManifest struct {
	SpecVersion        string              `json:"specVersion"`
	SVGContractVersion string              `json:"svgContractVersion"`
	ChartTypes         []string            `json:"chartTypes"`
	Column             map[string][]string `json:"column"`
	Bar                map[string][]string `json:"bar"`
}

var activeCapabilities = CapabilityManifest{
	SpecVersion:        "0.0.0.1",
	SVGContractVersion: "0.0.0.1",
	ChartTypes:         []string{"area", "bar", "bubble", "combo", "column", "histogram", "line", "scatter"},
	Column: map[string][]string{
		"grouping": []string{"grouped", "overlay"},
		"stacking": []string{"none", "normal", "percent-nonnegative"},
	},
	Bar: map[string][]string{
		"grouping": []string{"grouped", "overlay"},
		"stacking": []string{"none", "normal", "percent-nonnegative"},
	},
}

// Capabilities returns the machine-readable active renderer manifest.
func Capabilities() CapabilityManifest { return activeCapabilities }
