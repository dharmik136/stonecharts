#!/usr/bin/env python3
"""Parse a GitHub issue form body and map it to governed project fields."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

SECTION_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")


WORKSTREAMS = [
    "WS-01 Governance",
    "WS-02 Renderer",
    "WS-03 Conformance",
    "WS-04 Runtime & A11y",
    "WS-05 Customization",
    "WS-06 Release",
    "WS-07 Docs & DX",
    "WS-08 Expansion",
]

STAGES = [
    "S0 Foundation",
    "S1 Contract Closure",
    "S2 Qualification",
    "S3 Release Candidate",
    "S4 Release",
    "S5 Expansion",
]

PRIORITIES = ["P0", "P1", "P2", "P3"]
TARGETS = ["0.0.0.1", "Post-0.0.0.1", "Unscheduled"]


@dataclass
class FormData:
    sections: dict[str, str]


def parse_sections(text: str) -> FormData:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in text.splitlines():
        match = SECTION_RE.match(raw_line.strip())
        if match:
            current = match.group("title").strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(raw_line.rstrip())

    joined = {key: "\n".join(lines).strip() for key, lines in sections.items()}
    return FormData(sections=joined)


def first_nonempty(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def normalize_choice(value: str, allowed: list[str]) -> str:
    value = value.strip()
    return value if value in allowed else ""


def map_project_fields(role: str, form: FormData) -> dict[str, str]:
    sections = form.sections
    workstream = normalize_choice(first_nonempty(sections.get("Workstream")), WORKSTREAMS)
    stage = normalize_choice(first_nonempty(sections.get("Stage")), STAGES)
    priority = normalize_choice(first_nonempty(sections.get("Priority"), "P1"), PRIORITIES)
    target = normalize_choice(
        first_nonempty(sections.get("Target release or stage"), sections.get("Target"), "0.0.0.1"),
        TARGETS,
    )

    item_type = {
        "planner": "Decision",
        "developer": "Work Package",
        "qa": "Work Package",
        "security": "Work Package",
        "compliance": "Work Package",
        "release": "Release Gate",
    }[role]

    mapped = {
        "Status": "Triage",
        "Item Type": item_type,
    }
    if workstream:
        mapped["Workstream"] = workstream
    if stage:
        mapped["Stage"] = stage
    if priority:
        mapped["Priority"] = priority
    if target:
        mapped["Target"] = target
    return mapped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--role", required=True, choices=["planner", "developer", "qa", "security", "compliance", "release"]
    )
    parser.add_argument("--input", "-i", help="Path to issue body text; defaults to stdin")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    text = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()

    form = parse_sections(text)
    mapped = map_project_fields(args.role, form)
    result = {
        "role": args.role,
        "sections": form.sections,
        "project_fields": mapped,
    }

    if args.format == "json":
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for key, value in mapped.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
