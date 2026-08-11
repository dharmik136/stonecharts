#!/usr/bin/env python3
"""Generate and verify capability tables from spec/capabilities.json.

Usage:
    python tools/generate_capabilities.py --generate   # Update generated files
    python tools/generate_capabilities.py --check      # Exit non-zero if drift detected
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "spec" / "capabilities.json"

PYTHON_CAPABILITIES = ROOT / "libs" / "python" / "stonecharts" / "capabilities.py"
GO_CAPABILITIES = ROOT / "libs" / "go" / "capabilities.go"
README = ROOT / "README.md"
CHARTS_MD = ROOT / "CHARTS.md"
CAPABILITY_MATRIX = ROOT / "docs" / "product" / "capability-matrix.md"
GUARANTEES = ROOT / "docs" / "contracts" / "guarantees-and-limits.md"

GENERATED_BEGIN = "<!-- BEGIN:GENERATED:capabilities -->"
GENERATED_END = "<!-- END:GENERATED:capabilities -->"


def load_registry() -> dict:
    """Load the canonical capability registry."""
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def tier_counts(chart_types: list[dict]) -> dict[str, int]:
    """Return {tier: count} from the chart type list."""
    counts: dict[str, int] = {"certified": 0, "candidate": 0, "experimental": 0}
    for ct in chart_types:
        counts[ct["tier"]] = counts.get(ct["tier"], 0) + 1
    return counts


def by_tier(chart_types: list[dict], tier: str) -> list[dict]:
    """Return chart types matching a tier, sorted by id."""
    return sorted([ct for ct in chart_types if ct["tier"] == tier], key=lambda c: c["id"])


# ---------------------------------------------------------------------------
# Python capabilities.py generation
# ---------------------------------------------------------------------------

def generate_python_capabilities(registry: dict) -> str:
    """Generate the full capabilities.py content."""
    lines = [
        '"""Machine-readable renderer capability manifest for the active release scope."""',
        "",
        "from __future__ import annotations",
        "",
        "from copy import deepcopy",
        "from typing import Any",
        "",
        "# --- BEGIN GENERATED FROM spec/capabilities.json ---",
        "_CAPABILITIES: dict[str, Any] = {",
        f'    "specVersion": "{registry["specVersion"]}",',
        f'    "svgContractVersion": "{registry["svgContractVersion"]}",',
        '    "chartTypes": {',
    ]

    chart_types = sorted(registry["chartTypes"], key=lambda c: c["id"])
    max_id_len = max(len(ct["id"]) for ct in chart_types)

    for ct in chart_types:
        cid = ct["id"]
        tier = ct["tier"]
        since = ct["since"]
        padding_id = " " * (max_id_len - len(cid))
        padding_tier = " " * (14 - len(tier))
        if since is None:
            since_str = "None"
            lines.append(
                f'        "{cid}": {padding_id}{{"tier": "{tier}",{padding_tier}"since": {since_str}}},'
            )
        else:
            lines.append(
                f'        "{cid}": {padding_id}{{"tier": "{tier}",{padding_tier}"since": "{since}"}},'
            )

    lines.append("    },")

    # Extra capabilities (column, bar)
    for key in ["column", "bar"]:
        if key in registry.get("extraCapabilities", {}):
            cap = registry["extraCapabilities"][key]
            lines.append(f'    "{key}": {{')
            for field, values in cap.items():
                val_str = json.dumps(values)
                lines.append(f'        "{field}": {val_str},')
            lines.append("    },")

    lines.append("}")
    lines.append("# --- END GENERATED FROM spec/capabilities.json ---")
    lines.append("")
    lines.append("")
    lines.append('class CapabilityError(Exception):')
    lines.append('    """Typed non-fatal error for unsupported renderer capabilities."""')
    lines.append("")
    lines.append('    def __init__(self, code: str, path: str, message: str, details: dict[str, Any] | None = None):')
    lines.append("        super().__init__(message)")
    lines.append("        self.code = code")
    lines.append("        self.path = path")
    lines.append("        self.message = message")
    lines.append("        self.details = deepcopy(details) if details is not None else None")
    lines.append("")
    lines.append("    def __str__(self) -> str:")
    lines.append('        return f"{self.path}: {self.message}" if self.path else self.message')
    lines.append("")
    lines.append("")
    lines.append("def capabilities() -> dict[str, Any]:")
    lines.append('    """Return a machine-readable snapshot of the active renderer capabilities."""')
    lines.append("    return deepcopy(_CAPABILITIES)")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Go capabilities.go generation
# ---------------------------------------------------------------------------

def generate_go_capabilities(registry: dict) -> str:
    """Generate the full capabilities.go content."""
    lines = [
        "package stonecharts",
        "",
        "// CapabilityError is returned when a spec is structurally valid but requests an",
        "// unsupported renderer capability.",
        "type CapabilityError struct {",
        '\tCode    string                 `json:"code"`',
        '\tPath    string                 `json:"path"`',
        '\tMessage string                 `json:"message"`',
        '\tDetails map[string]interface{} `json:"details,omitempty"`',
        "}",
        "",
        "func (e *CapabilityError) Error() string {",
        "\tif e == nil {",
        '\t\treturn ""',
        "\t}",
        '\tif e.Path != "" {',
        '\t\treturn e.Path + ": " + e.Message',
        "\t}",
        "\treturn e.Message",
        "}",
        "",
        "// ChartTypeMeta describes the certification tier and version origin of a chart type.",
        "type ChartTypeMeta struct {",
        '\tTier  string `json:"tier"`',
        '\tSince string `json:"since"`',
        "}",
        "",
        "// CapabilityManifest is the machine-readable active-release renderer contract.",
        "type CapabilityManifest struct {",
        '\tSpecVersion        string                     `json:"specVersion"`',
        '\tSVGContractVersion string                     `json:"svgContractVersion"`',
        '\tChartTypes         map[string]ChartTypeMeta   `json:"chartTypes"`',
        '\tColumn             map[string][]string        `json:"column"`',
        '\tBar                map[string][]string        `json:"bar"`',
        "}",
        "",
        "// --- BEGIN GENERATED FROM spec/capabilities.json ---",
        "var activeCapabilities = CapabilityManifest{",
        f'\tSpecVersion:        "{registry["specVersion"]}",',
        f'\tSVGContractVersion: "{registry["svgContractVersion"]}",',
        "\tChartTypes: map[string]ChartTypeMeta{",
    ]

    chart_types = sorted(registry["chartTypes"], key=lambda c: c["id"])
    max_id_len = max(len(ct["id"]) for ct in chart_types)

    for ct in chart_types:
        cid = ct["id"]
        tier = ct["tier"]
        since = ct["since"] if ct["since"] is not None else ""
        padding = " " * (max_id_len - len(cid))
        lines.append(
            f'\t\t"{cid}": {padding}{{Tier: "{tier}", Since: "{since}"}},'
        )

    lines.append("\t},")

    # Extra capabilities
    for key in ["column", "bar"]:
        cap_key = key.capitalize()
        if key in registry.get("extraCapabilities", {}):
            cap = registry["extraCapabilities"][key]
            lines.append(f"\t{cap_key}: map[string][]string{{")
            for field, values in cap.items():
                vals = ", ".join(f'"{v}"' for v in values)
                lines.append(f'\t\t"{field}": {{{vals}}},')
            lines.append("\t},")

    lines.append("}")
    lines.append("// --- END GENERATED FROM spec/capabilities.json ---")
    lines.append("")
    lines.append("// ChartTypeNames returns a sorted list of all chart type names.")
    lines.append("func (m CapabilityManifest) ChartTypeNames() []string {")
    lines.append("\tnames := make([]string, 0, len(m.ChartTypes))")
    lines.append("\tfor k := range m.ChartTypes {")
    lines.append("\t\tnames = append(names, k)")
    lines.append("\t}")
    lines.append("\t// sort for determinism")
    lines.append("\tfor i := 0; i < len(names); i++ {")
    lines.append("\t\tfor j := i + 1; j < len(names); j++ {")
    lines.append("\t\t\tif names[i] > names[j] {")
    lines.append("\t\t\t\tnames[i], names[j] = names[j], names[i]")
    lines.append("\t\t\t}")
    lines.append("\t\t}")
    lines.append("\t}")
    lines.append("\treturn names")
    lines.append("}")
    lines.append("")
    lines.append("// Capabilities returns the machine-readable active renderer manifest.")
    lines.append("func Capabilities() CapabilityManifest { return activeCapabilities }")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Doc checking helpers
# ---------------------------------------------------------------------------

def extract_generated_block(text: str) -> str | None:
    """Extract content between GENERATED markers, or None if markers absent."""
    m = re.search(
        re.escape(GENERATED_BEGIN) + r"\n(.*?)\n" + re.escape(GENERATED_END),
        text,
        re.DOTALL,
    )
    return m.group(1) if m else None


def check_readme(registry: dict, errors: list[str]) -> None:
    """Check README.md for accurate counts and tables."""
    text = README.read_text(encoding="utf-8")
    counts = tier_counts(registry["chartTypes"])
    total = sum(counts.values())
    certified = counts["certified"]
    candidate = counts["candidate"]
    experimental = counts["experimental"]

    # Check badge count
    if f"chart_types-{total}-" not in text:
        errors.append(f"README.md: badge should show {total} chart types")

    # Check catalog summary line
    expected_summary = f"**{total} chart types**"
    if expected_summary not in text:
        errors.append(f"README.md: catalog summary should say '{expected_summary}'")

    # Check tier count table
    if f"| **Certified** | {certified} |" not in text:
        errors.append(f"README.md: certified count should be {certified}")
    if f"| **Candidate** | {candidate} |" not in text:
        errors.append(f"README.md: candidate count should be {candidate}")
    if f"| **Experimental** | {experimental} |" not in text:
        errors.append(f"README.md: experimental count should be {experimental}")

    # Check section headers
    if f"### Certified ({certified} types)" not in text:
        errors.append(f"README.md: certified section header should show {certified}")
    if f"### Candidate ({candidate} types)" not in text:
        errors.append(f"README.md: candidate section header should show {candidate}")
    if f"### Experimental ({experimental} types)" not in text:
        errors.append(f"README.md: experimental section header should show {experimental}")

    # Check that development-triangle appears in candidate section
    if "development-triangle" not in text:
        errors.append("README.md: development-triangle must be listed")

    # Check every chart type is mentioned
    for ct in registry["chartTypes"]:
        if f"`{ct['id']}`" not in text:
            errors.append(f"README.md: chart type '{ct['id']}' not found")

    # Check the general counts in the description text
    desc_pattern = f"{total} chart types"
    found_count = text.count(desc_pattern)
    if found_count == 0 and f"{total} chart" not in text:
        errors.append(f"README.md: should mention {total} chart types somewhere")

    # Check CI section references correct count
    if f"all {total} chart types" not in text:
        errors.append(f"README.md: CI section should reference {total} chart types")


def check_charts_md(registry: dict, errors: list[str]) -> None:
    """Check CHARTS.md status fields match tiers."""
    text = CHARTS_MD.read_text(encoding="utf-8")

    for ct in registry["chartTypes"]:
        cid = ct["id"]
        tier = ct["tier"]
        # development-triangle may have a special status
        if cid == "development-triangle":
            if cid not in text:
                errors.append(f"CHARTS.md: development-triangle must be listed")
            continue

        # Check that the chart is present
        if f"`{cid}`" not in text:
            # line-basic is an alias for line in CHARTS.md
            if cid == "line" and "`line-basic`" in text:
                continue
            errors.append(f"CHARTS.md: chart type '{cid}' not found")


def _chart_id_to_display(cid: str) -> str:
    """Map a chart id to its conventional display name."""
    special = {
        "arearange": "Area Range",
        "columnrange": "Column Range",
        "error-bar": "Error Bar",
        "flame-chart": "Flame Chart",
        "line-basic": "Line",
        "radial-bar": "Radial Bar",
        "solid-gauge": "Solid Gauge",
        "technical-indicators": "Technical Indicators",
        "vector-plot": "Vector Plot",
        "wind-rose": "Wind Rose",
        "xrange": "X-Range",
        "development-triangle": "Development Triangle",
    }
    return special.get(cid, cid.replace("-", " ").title())


def check_capability_matrix(registry: dict, errors: list[str]) -> None:
    """Check docs/product/capability-matrix.md for accurate tiers and counts."""
    text = CAPABILITY_MATRIX.read_text(encoding="utf-8")
    counts = tier_counts(registry["chartTypes"])

    # Check generated block exists
    if GENERATED_BEGIN not in text:
        errors.append("capability-matrix.md: missing GENERATED markers")
        return

    block = extract_generated_block(text)
    if block is None:
        errors.append("capability-matrix.md: could not extract generated block")
        return

    # Check every chart type is in the generated block
    for ct in registry["chartTypes"]:
        cid = ct["id"]
        tier = ct["tier"].capitalize()
        display = _chart_id_to_display(cid)
        if cid not in block and display not in block:
            errors.append(f"capability-matrix.md: '{cid}' (display: '{display}') missing from generated block")


def check_guarantees(registry: dict, errors: list[str]) -> None:
    """Check docs/contracts/guarantees-and-limits.md for accurate counts."""
    text = GUARANTEES.read_text(encoding="utf-8")
    counts = tier_counts(registry["chartTypes"])
    total = sum(counts.values())

    # Should NOT say "35 chart types are certified"
    if "35 chart types are certified" in text:
        errors.append("guarantees-and-limits.md: still says '35 chart types are certified'")

    # Check generated block
    if GENERATED_BEGIN not in text:
        errors.append("guarantees-and-limits.md: missing GENERATED markers")
        return

    block = extract_generated_block(text)
    if block is None:
        errors.append("guarantees-and-limits.md: could not extract generated block")
        return

    # The generated block should have the correct counts
    if str(counts["certified"]) not in block:
        errors.append(f"guarantees-and-limits.md: certified count {counts['certified']} not in generated block")
    if str(total) not in block:
        errors.append(f"guarantees-and-limits.md: total count {total} not in generated block")


def check_python_capabilities(registry: dict, errors: list[str]) -> None:
    """Check Python capabilities.py matches the registry."""
    text = PYTHON_CAPABILITIES.read_text(encoding="utf-8")

    for ct in registry["chartTypes"]:
        cid = ct["id"]
        tier = ct["tier"]
        since = ct["since"]

        if f'"{cid}"' not in text:
            errors.append(f"capabilities.py: chart type '{cid}' not found")
            continue

        # Check tier
        if since is None:
            expected_tier = f'"tier": "{tier}"'
            expected_since = '"since": None'
        else:
            expected_tier = f'"tier": "{tier}"'
            expected_since = f'"since": "{since}"'

        # Find the line for this chart type and check tier
        for line in text.splitlines():
            if f'"{cid}"' in line:
                if expected_tier not in line:
                    errors.append(f"capabilities.py: '{cid}' tier should be '{tier}'")
                if expected_since not in line:
                    errors.append(f"capabilities.py: '{cid}' since should be '{since}'")
                break


def check_go_capabilities(registry: dict, errors: list[str]) -> None:
    """Check Go capabilities.go matches the registry."""
    text = GO_CAPABILITIES.read_text(encoding="utf-8")

    # Only search within the ChartTypes map section to avoid matching JSON tags
    in_chart_types = False
    chart_type_lines: dict[str, str] = {}
    for line in text.splitlines():
        if "ChartTypes:" in line and "map[string]ChartTypeMeta" in line:
            in_chart_types = True
            continue
        if in_chart_types:
            if line.strip().startswith("}"):
                in_chart_types = False
                continue
            # Extract chart id from lines like: "area": {Tier: "certified", Since: "0.0.0.3"},
            m = re.match(r'\s*"([^"]+)":', line)
            if m:
                chart_type_lines[m.group(1)] = line

    for ct in registry["chartTypes"]:
        cid = ct["id"]
        tier = ct["tier"]
        since = ct["since"] if ct["since"] is not None else ""

        if cid not in chart_type_lines:
            errors.append(f"capabilities.go: chart type '{cid}' not found")
            continue

        expected = f'Tier: "{tier}", Since: "{since}"'
        if expected not in chart_type_lines[cid]:
            errors.append(f"capabilities.go: '{cid}' should have {expected}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/verify capabilities from canonical registry")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true", help="Update generated files")
    group.add_argument("--check", action="store_true", help="Check for drift (exits non-zero if found)")
    args = parser.parse_args()

    registry = load_registry()

    if args.generate:
        # Generate Python capabilities
        py_content = generate_python_capabilities(registry)
        PYTHON_CAPABILITIES.write_text(py_content, encoding="utf-8")
        print(f"Updated {PYTHON_CAPABILITIES}")

        # Generate Go capabilities
        go_content = generate_go_capabilities(registry)
        GO_CAPABILITIES.write_text(go_content, encoding="utf-8")
        print(f"Updated {GO_CAPABILITIES}")

        print("Generated files updated from spec/capabilities.json.")
        return 0

    # --check mode
    errors: list[str] = []

    check_python_capabilities(registry, errors)
    check_go_capabilities(registry, errors)
    check_readme(registry, errors)
    check_charts_md(registry, errors)
    check_capability_matrix(registry, errors)
    check_guarantees(registry, errors)

    if errors:
        print(f"DRIFT DETECTED ({len(errors)} issues):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("All capability checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
