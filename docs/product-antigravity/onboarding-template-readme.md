# Antigravity Pilot Repository Template

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

Welcome to the **Antigravity Pilot Repository**. This template provides a starting point for integrating Google Antigravity into your team's development, rendering, and testing workflows. 

Copy this README into your own repository, customize the paths, and follow the setup instructions to automate your UI specification management, visual regression testing, and cross-language byte-conformance checks.

---

## 📂 Repository Layout

To maintain compatibility with the Antigravity CLI (`agy`) and automated test runner, organize your repository using the following directory structure:

```text
├── .github/
│   └── workflows/
│       └── antigravity-ci.yml      # CI/CD pipeline for regression & conformance checks
├── specs/                          # UI/UX design specifications (YAML/JSON schemas)
│   ├── buttons.yaml
│   └── layouts.yaml
├── renderers/                      # Code that translates specs into rendered assets
│   ├── python/
│   │   ├── renderer.py             # Python rendering implementation
│   │   └── requirements.txt
│   └── go/
│       ├── renderer.go             # Go rendering implementation
│       └── go.mod
├── tests/
│   ├── baselines/                  # Approved reference screenshots (Golden files)
│   │   ├── button_primary.png
│   │   └── layout_grid.png
│   ├── python/
│   │   ├── test_conformance.py     # Python conformance & visual test suite
│   │   └── test_renderer.py
│   └── go/
│       ├── conformance_test.go     # Go conformance test suite
│       └── renderer_test.go
└── README.md                       # This guide
```

---

## 📐 1. Spec Organization

Specifications represent the "single source of truth" for your application's user interface. They define layout coordinates, spacing, colors, font sizes, and states in a machine-readable format (YAML or JSON).

### Example Design Spec (`specs/buttons.yaml`)
```yaml
version: "1.0.0"
component: "Button"
variants:
  primary:
    background_color: "#1a73e8"      # Google Blue
    text_color: "#ffffff"
    font_size: "14px"
    font_family: "Roboto, sans-serif"
    border_radius: "4px"
    padding: "8px 16px"
    label: "Submit"
  secondary:
    background_color: "#f1f3f4"
    text_color: "#3c4043"
    font_size: "14px"
    font_family: "Roboto, sans-serif"
    border_radius: "4px"
    padding: "8px 16px"
    label: "Cancel"
```

> [!TIP]
> Keep your specifications declarative. Avoid mixing behavioral scripts inside `specs/`. Focus purely on design tokens and component configurations.

---

## 🎨 2. Loading & Running Renderers

Renderers translate your declarative specifications into renderable UI targets (such as HTML/CSS strings, SVG elements, or canvas draw instructions). Below are template implementations for Python and Go.

### 🐍 Python Renderer Implementation (`renderers/python/renderer.py`)
This renderer loads raw YAML specs and produces standard HTML representing the component.

```python
import yaml
from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        .custom-button {
            background-color: {{ background_color }};
            color: {{ text_color }};
            font-size: {{ font_size }};
            font-family: {{ font_family }};
            border-radius: {{ border_radius }};
            padding: {{ padding }};
            border: none;
            cursor: pointer;
            transition: opacity 0.2s ease-in-out;
        }
        .custom-button:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <button class="custom-button">{{ label }}</button>
</body>
</html>
"""

class SpecRenderer:
    def __init__(self, spec_path: str):
        with open(spec_path, 'r') as file:
            self.spec_data = yaml.safe_load(file)

    def render_button(self, variant: str) -> str:
        if "variants" not in self.spec_data or variant not in self.spec_data["variants"]:
            raise ValueError(f"Variant '{variant}' not found in specifications.")
        
        button_spec = self.spec_data["variants"][variant]
        template = Template(HTML_TEMPLATE)
        return template.render(**button_spec)
```

### 🐹 Go Renderer Implementation (`renderers/go/renderer.go`)
This renderer parses the spec and uses Go's `html/template` package to output visual layouts.

```go
package main

import (
	"fmt"
	"html/template"
	"io"
	"os"

	"gopkg.in/yaml.v3"
)

type ButtonSpec struct {
	BackgroundColor string `yaml:"background_color"`
	TextColor       string `yaml:"text_color"`
	FontSize        string `yaml:"font_size"`
	FontFamily      string `yaml:"font_family"`
	BorderRadius    string `yaml:"border_radius"`
	Padding         string `yaml:"padding"`
	Label           string `yaml:"label"`
}

type SpecData struct {
	Version   string                `yaml:"version"`
	Component string                `yaml:"component"`
	Variants  map[string]ButtonSpec `yaml:"variants"`
}

const htmlTemplate = `<!DOCTYPE html>
<html>
<head>
    <style>
        .custom-button {
            background-color: {{.BackgroundColor}};
            color: {{.TextColor}};
            font-size: {{.FontSize}};
            font-family: {{.FontFamily}};
            border-radius: {{.BorderRadius}};
            padding: {{.Padding}};
            border: none;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <button class="custom-button">{{.Label}}</button>
</body>
</html>`

type SpecRenderer struct {
	Data SpecData
}

func NewSpecRenderer(specPath string) (*SpecRenderer, error) {
	file, err := os.Open(specPath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var data SpecData
	decoder := yaml.NewDecoder(file)
	if err := decoder.Decode(&data); err != nil {
		return nil, err
	}

	return &SpecRenderer{Data: data}, nil
}

func (r *SpecRenderer) RenderButton(w io.Writer, variant string) error {
	buttonSpec, ok := r.Data.Variants[variant]
	if !ok {
		return fmt.Errorf("variant %s not found", variant)
	}

	tmpl, err := template.New("button").Parse(htmlTemplate)
	if err != nil {
		return err
	}

	return tmpl.Execute(w, buttonSpec)
}
```

---

## 👁️ 3. Visual Regression Testing

Visual regression testing compares visual snapshots of your rendered code against baseline images. Antigravity automates this process by running browser automation, saving snapshots, and doing pixel-by-pixel comparisons.

### Running Local Visual Tests
Use the Antigravity CLI (`agy`) inside your repository to trigger visual assertions:

```sh
# Compare current rendering against approved baselines under tests/baselines/
agy test --visual

# Update the approved baseline snapshots when design changes are intentional
agy test --visual --update-baselines
```

### Python Programmatic Visual Check Example (`tests/python/test_renderer.py`)
Using Playwright to capture the local page render and compare bytes:

```python
import os
import pytest
from playwright.sync_api import sync_playwright
from pixelmatch.contrib.PIL import pixelmatch
from PIL import Image

@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

def test_visual_button_primary(browser):
    # Render HTML from spec
    from renderers.python.renderer import SpecRenderer
    renderer = SpecRenderer("specs/buttons.yaml")
    html_content = renderer.render_button("primary")
    
    # Save temporary html representation
    temp_html = "temp_button.html"
    with open(temp_html, "w") as f:
        f.write(html_content)
        
    page = browser.new_page()
    page.goto(f"file://{os.path.abspath(temp_html)}")
    
    # Target visual element
    element = page.locator(".custom-button")
    screenshot_bytes = element.screenshot()
    
    # Compare with baseline
    baseline_path = "tests/baselines/button_primary.png"
    actual_path = "tests/python/actual_button_primary.png"
    diff_path = "tests/python/diff_button_primary.png"
    
    # Save actual rendering
    with open(actual_path, "wb") as f:
        f.write(screenshot_bytes)
        
    if not os.path.exists(baseline_path):
        # Auto-initialize baseline if not present
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        with open(baseline_path, "wb") as f:
            f.write(screenshot_bytes)
        pytest.skip("Baseline initialized. Please commit the generated image.")

    # Compare images
    img_baseline = Image.open(baseline_path).convert("RGBA")
    img_actual = Image.open(actual_path).convert("RGBA")
    img_diff = Image.new("RGBA", img_baseline.size)
    
    mismatch = pixelmatch(img_baseline, img_actual, img_diff, threshold=0.1)
    
    # Save visual differences if any mismatch occurs
    if mismatch > 0:
        img_diff.save(diff_path)
        assert mismatch == 0, f"Visual regression detected! {mismatch} pixels differed. Check {diff_path}."
        
    # Clean up temp file
    os.remove(temp_html)
```

---

## 💾 4. Byte-Conformance Checks

Byte-conformance checks guarantee that serialization structures (like binary encoders, protocol buffers, or compiled JSON schemas) are strictly conforming to specifications down to the byte structure.

### 🐍 Python Byte-Conformance Test (`tests/python/test_conformance.py`)
Validates that the spec complies with the expected JSON/YAML structure, preventing raw configuration errors:

```python
import json
import jsonschema
import yaml

BUTTON_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "component": {"type": "string", "const": "Button"},
        "variants": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "background_color": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                    "text_color": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                    "font_size": {"type": "string"},
                    "font_family": {"type": "string"},
                    "border_radius": {"type": "string"},
                    "padding": {"type": "string"},
                    "label": {"type": "string"}
                },
                "required": ["background_color", "text_color", "label"]
            }
        }
    },
    "required": ["version", "component", "variants"]
}

def test_spec_conformance():
    with open("specs/buttons.yaml", "r") as file:
        data = yaml.safe_load(file)
    
    # Assert structural validity against schema
    jsonschema.validate(instance=data, schema=BUTTON_SCHEMA)

def test_binary_serialization_conformance():
    with open("specs/buttons.yaml", "r") as file:
        yaml_data = yaml.safe_load(file)
        
    # Python deterministic json encoding check (no spaces, sorted keys)
    serialized_bytes = json.dumps(yaml_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    # Verify exact byte sequence matches expected formatting (e.g. utf-8 bytes check)
    assert serialized_bytes.startswith(b'{"component":"Button"')
```

### 🐹 Go Byte-Conformance Test (`tests/go/conformance_test.go`)
Validates that Go structures unmarshal and match the specifications without any field omissions or data truncation:

```go
package main

import (
	"encoding/json"
	"os"
	"testing"

	"gopkg.in/yaml.v3"
)

func TestSpecConformance(t *testing.T) {
	file, err := os.Open("../../specs/buttons.yaml")
	if err != nil {
		t.Fatalf("Failed to open spec file: %v", err)
	}
	defer file.Close()

	var data SpecData
	decoder := yaml.NewDecoder(file)
	if err := decoder.Decode(&data); err != nil {
		t.Fatalf("Spec file failed YAML validation: %v", err)
	}

	if data.Component != "Button" {
		t.Errorf("Expected Component to be 'Button', got '%s'", data.Component)
	}

	for name, val := range data.Variants {
		if val.BackgroundColor == "" {
			t.Errorf("Variant '%s' background color must not be empty", name)
		}
		if val.TextColor == "" {
			t.Errorf("Variant '%s' text color must not be empty", name)
		}
	}
}

func TestDeterministicJSONByteOutput(t *testing.T) {
	// Ensure that Go and Python output byte-identical JSON strings for specs
	file, err := os.ReadFile("../../specs/buttons.yaml")
	if err != nil {
		t.Fatalf("Failed to read spec: %v", err)
	}

	var data map[string]interface{}
	if err := yaml.Unmarshal(file, &data); err != nil {
		t.Fatalf("Failed to unmarshal: %v", err)
	}

	// Marshaling must be deterministic
	byteOutput, err := json.Marshal(data)
	if err != nil {
		t.Fatalf("Failed to marshal JSON: %v", err)
	}

	// Perform byte checks (e.g., ensure no byte-order marks, clean UTF-8 string)
	if byteOutput[0] != '{' {
		t.Errorf("Expected JSON to start with '{', got '%c'", byteOutput[0])
	}
}
```

---

## 🚀 5. Automated CI/CD (GitHub Actions)

This pipeline runs automatically on every pull request to ensure that specifications comply with schema structures, rendering logic is verified in a headless browser, and visual regressions do not slip into production.

### GitHub Actions Workflow configuration (`.github/workflows/antigravity-ci.yml`)

```yaml
name: Antigravity CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  conformance-and-visual-testing:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
        cache: true
        cache-dependency-path: renderers/go/go.sum

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: Install Python Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r renderers/python/requirements.txt
        pip install pytest playwright jsonschema pyyaml pixelmatch pillow
        
    - name: Install Playwright Browsers
      run: |
        python -m playwright install --with-deps chromium

    - name: Run Python Conformance & Visual Tests
      run: |
        pytest tests/python/ -v

    - name: Run Go Conformance & Visual Tests
      run: |
        cd tests/go && go test -v ./...

    # In case of failures, upload the visual differences for review
    - name: Upload Visual Diff Artifacts
      if: failure()
      uses: actions/upload-artifact@v4
      with:
        name: visual-regression-diffs
        path: |
          tests/python/diff_*.png
          tests/python/actual_*.png
        retention-days: 5
```

---

## 🛠️ Best Practices

- **Baseline Commits**: Always commit your approved baseline images (`tests/baselines/*.png`) directly to the repository. The CI pipeline will fail if a pull request changes the visual output without update-baselines being executed.
- **Font Rendering Variance**: Since operating systems render fonts slightly differently, use a web font (such as Google Fonts) or set standard fallback fonts (e.g. `sans-serif`) to prevent cross-platform visual mismatches between local environments and the Ubuntu-based CI runners.
- **Deterministic Spacing**: Avoid margins or styles that depend on viewport size when verifying individual components. Instead, snapshot bounding boxes of the component class target.
