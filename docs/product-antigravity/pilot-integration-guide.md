---
id: SC-PROD-004-ANTIGRAVITY
title: StoneCharts Pilot Integration Guide
status: superseded
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: []
evidence: []
last_reviewed: "2026-07-30"
review_due: "2027-07-30"
supersedes: null
superseded_by: SC-QUAL-004
---

# Pilot Integration Guide

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

This guide is designed for engineering teams integrating the **Deterministic Reporting SDK** into multi-language service architectures (Python and Go). It demonstrates how to parse a shared JSON chart contract, render deterministic SVGs, verify byte conformance, and generate final PDF report exports.

---

## 1. Defining the Shared Chart Contract (JSON)

Save the following chart definition as `report-chart.json`. This format is language-agnostic and validated against the shared StoneCharts JSON schema.

```json
{
  "type": "column",
  "id": "q3-revenue",
  "title": "Q3 Regional Revenue",
  "subtitle": "Figures in USD Millions (Audited)",
  "width": 800,
  "height": 400,
  "theme": "light",
  "xAxis": {
    "categories": ["July", "August", "September"]
  },
  "yAxis": {
    "title": "Revenue ($M)"
  },
  "series": [
    {
      "name": "North America",
      "data": [12.4, 15.1, 18.2]
    },
    {
      "name": "Europe",
      "data": [9.8, 11.2, 12.5]
    }
  ]
}
```

---

## 2. Rendering in Python

To render this contract in a Python data pipeline or analysis task, use the `stonecharts` package.

```python
import json
import sys
from pathlib import Path
from stonecharts import ChartSpec, render_svg, SpecError, CapabilityError

def render_chart_python(spec_path: str, output_path: str):
    try:
        # 1. Read JSON spec
        spec_content = Path(spec_path).read_text(encoding="utf-8")
        spec_dict = json.loads(spec_content)
        
        # 2. Instantiate and validate contract
        # (This throws SpecError if invalid, CapabilityError if unsupported)
        spec = ChartSpec.from_dict(spec_dict)
        
        # 3. Render directly to canonical SVG string
        svg_content = render_svg(spec)
        
        # 4. Save output
        Path(output_path).write_text(svg_content, encoding="utf-8")
        print(f"[Python] Success: Rendered canonical SVG to {output_path}")
        
    except (SpecError, CapabilityError) as e:
        print(f"[Python] Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Python] Unexpected rendering error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    render_chart_python("report-chart.json", "chart_python.svg")
```

---

## 3. Rendering in Go

To render the identical chart contract inside a Go microservice or report generation worker, use the `stonecharts` Go module.

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"stonecharts" // Import the local Go edition
)

func main() {
	// 1. Read JSON spec
	specBytes, err := os.ReadFile("report-chart.json")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to read spec: %v\n", err)
		os.Exit(1)
	}

	// 2. Decode the contract, validate, and apply defaults
	spec, err := stonecharts.FromJSON(specBytes)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to decode/validate spec: %v\n", err)
		os.Exit(1)
	}

	// 3. Render natively
	svgContent, err := stonecharts.RenderSVG(spec)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Render failed: %v\n", err)
		os.Exit(1)
	}

	// 4. Save output
	err = os.WriteFile("chart_go.svg", []byte(svgContent), 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to save output: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("[Go] Success: Rendered canonical SVG to chart_go.svg")
}
```

---

## 4. Verifying Conformance

Since StoneCharts promises strict deterministic cross-language parity, you can assert that the Go and Python outputs are byte-identical.

```bash
# Compare generated SVGs
diff chart_python.svg chart_go.svg

if [ $? -eq 0 ]; then
    echo "PASS: Parity verified. Go and Python generated identical SVG bytes!"
else
    echo "FAIL: Chart drift detected!"
    exit 1
fi
```

> [!NOTE]
> StoneCharts enforces consistent attribute ordering, CDATA namespaces, and layout coordinates to guarantee that visual elements line up down to the exact byte.

---

## 5. Text Geometry and Font Considerations

Go and Python measure Unicode string geometry differently due to standard library details. To avoid visual label collisions and coordinate drift:
- Ensure all rendering machines share the same default host fonts.
- Apply explicit manual margins (using `layout.margin`) if category labels are long or contain non-ASCII characters to keep the SVG outputs byte-identical.

---

## 6. Compiling Reports to PDF (Certified Export Path)

To compile the report including the rendered chart into a printable, governed document format (PDF) without a browser running in production, use a lightweight utility like `weasyprint` or `librsvg`.

> [!CAUTION]
> **SSRF and Local File Access Warning**:
> PDF compilers like `weasyprint` resolve external URLs and local files by default. If your HTML or SVG contains untrusted user input, this exposes your environment to Server-Side Request Forgery (SSRF) and Local File Inclusion (LFI). 
> Always sandbox your PDF rendering environment, disable network access for the compiler, or configure Weasyprint's URL fetcher redirection to filter out external or non-embedded assets.

```bash
# Wrap the generated SVG in a clean HTML report template
cat <<EOF > report.html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: sans-serif; margin: 50px; color: #222; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 30px; }
        .chart-container { text-align: center; margin: 40px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Quarterly Business Review</h1>
        <p>Generated: 2026-07-21 | Security: Restricted</p>
    </div>
    <p>Below is the audited regional performance chart generated natively on our Go services:</p>
    
    <div class="chart-container">
        $(cat chart_go.svg)
    </div>
</body>
</html>
EOF

# Compile to PDF using a lightweight backend compiler
weasyprint report.html q3_report.pdf
echo "Q3 PDF Report successfully generated at q3_report.pdf"
```
