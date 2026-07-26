#!/usr/bin/env python3
"""Validate StoneCharts controlled documents and traceability registries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple
from urllib.parse import unquote, urlsplit

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
    from markdown_it import MarkdownIt
except ImportError as exc:  # pragma: no cover - actionable bootstrap path
    print(
        "missing governance dependency: "
        f"{exc.name}; install with `python -m pip install -e \"libs/python[dev]\"`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONTROLLED_DIRS = (
    DOCS / "governance",
    DOCS / "product",
    DOCS / "requirements",
    DOCS / "architecture",
    DOCS / "contracts",
    DOCS / "quality",
    DOCS / "security",
    DOCS / "releases",
    DOCS / "project",
    DOCS / "customization",
    DOCS / "roadmap",
)
EXTRA_CONTROLLED = (
    DOCS / "README.md",
    ROOT / "spec" / "svg-contract.md",
    ROOT / "charts" / "_cartesian" / "README.md",
    ROOT / "charts" / "line-basic" / "design.md",
    ROOT / "charts" / "column" / "design.md",
)

SCHEMA_DIR = DOCS / "governance" / "schemas"
METADATA_SCHEMA = SCHEMA_DIR / "document-metadata.schema.json"
REQUIREMENTS_SCHEMA = SCHEMA_DIR / "requirements-registry.schema.json"
EVIDENCE_SCHEMA = SCHEMA_DIR / "evidence-registry.schema.json"
RISK_SCHEMA = SCHEMA_DIR / "risk-register.schema.json"
ROLES_SCHEMA = SCHEMA_DIR / "roles.schema.json"
PROJECT_BACKLOG_SCHEMA = SCHEMA_DIR / "project-backlog.schema.json"
RELEASE_MANIFEST_SCHEMA = (
    DOCS / "releases" / "0.0.0.1" / "evidence" / "manifest.schema.json"
)

REQUIREMENTS_FILE = DOCS / "requirements" / "registry.yaml"
EVIDENCE_FILE = DOCS / "quality" / "evidence-registry.yaml"
RISK_FILE = DOCS / "governance" / "risk-register.yaml"
ROLES_FILE = DOCS / "governance" / "roles.yaml"
PROJECT_BACKLOG_FILE = DOCS / "project" / "backlog.yaml"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected a YAML object")
    return value


def validate_value(
    value: Dict[str, Any], schema_path: Path, source_path: Path, errors: List[str]
) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for issue in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        where = ".".join(str(part) for part in issue.absolute_path) or "$"
        errors.append(f"{rel(source_path)}:{where}: {issue.message}")


def controlled_markdown() -> List[Path]:
    paths: Set[Path] = set(EXTRA_CONTROLLED)
    for directory in CONTROLLED_DIRS:
        if directory.exists():
            paths.update(directory.rglob("*.md"))
    return sorted(paths, key=lambda path: rel(path))


def parse_frontmatter(path: Path) -> Tuple[Dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("controlled Markdown must start with YAML frontmatter")
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise ValueError("frontmatter has no closing `---`")
    metadata = yaml.safe_load("".join(lines[1:end]))
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a YAML object")
    return metadata, "".join(lines[end + 1 :])


def markdown_links(markdown: str) -> Iterable[str]:
    parser = MarkdownIt("commonmark")
    for token in parser.parse(markdown):
        children = token.children or []
        for child in children:
            if child.type == "link_open":
                href = child.attrGet("href")
                if href:
                    yield href
            elif child.type == "image":
                src = child.attrGet("src")
                if src:
                    yield src


def check_local_links(path: Path, markdown: str, errors: List[str]) -> None:
    for target in markdown_links(markdown):
        split = urlsplit(target)
        if split.scheme or split.netloc or target.startswith("#"):
            continue
        clean = unquote(split.path)
        if not clean:
            continue
        resolved = (ROOT / clean.lstrip("/")) if clean.startswith("/") else (path.parent / clean)
        if not resolved.exists():
            errors.append(f"{rel(path)}: broken local link `{target}`")


def duplicate_ids(items: Iterable[Dict[str, Any]], label: str, errors: List[str]) -> Set[str]:
    seen: Set[str] = set()
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str):
            continue
        if item_id in seen:
            errors.append(f"duplicate {label} id: {item_id}")
        seen.add(item_id)
    return seen


def check_path_reference(value: Any, source: str, errors: List[str]) -> None:
    if value is None or not isinstance(value, str):
        return
    if not (ROOT / value).exists():
        errors.append(f"{source}: referenced path does not exist: {value}")


def check_dependency_cycles(items: List[Dict[str, Any]], errors: List[str]) -> None:
    dependencies = {item["id"]: item.get("dependencies", []) for item in items}
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(item_id: str, path: List[str]) -> None:
        if item_id in visited:
            return
        if item_id in visiting:
            start = path.index(item_id)
            errors.append("project backlog dependency cycle: " + " -> ".join(path[start:] + [item_id]))
            return
        visiting.add(item_id)
        for dependency in dependencies.get(item_id, []):
            visit(dependency, path + [item_id])
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in dependencies:
        visit(item_id, [])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--traceability-json",
        type=Path,
        help="write a deterministic traceability snapshot after validation",
    )
    args = parser.parse_args()
    errors: List[str] = []

    schemas = [
        METADATA_SCHEMA,
        REQUIREMENTS_SCHEMA,
        EVIDENCE_SCHEMA,
        RISK_SCHEMA,
        ROLES_SCHEMA,
        PROJECT_BACKLOG_SCHEMA,
        RELEASE_MANIFEST_SCHEMA,
    ]
    for schema_path in schemas:
        try:
            Draft202012Validator.check_schema(load_json(schema_path))
        except Exception as exc:  # jsonschema provides precise text in the exception
            errors.append(f"{rel(schema_path)}: invalid JSON Schema: {exc}")

    try:
        requirements = load_yaml(REQUIREMENTS_FILE)
        validate_value(requirements, REQUIREMENTS_SCHEMA, REQUIREMENTS_FILE, errors)
    except Exception as exc:
        errors.append(f"{rel(REQUIREMENTS_FILE)}: {exc}")
        requirements = {"requirements": []}

    try:
        evidence = load_yaml(EVIDENCE_FILE)
        validate_value(evidence, EVIDENCE_SCHEMA, EVIDENCE_FILE, errors)
    except Exception as exc:
        errors.append(f"{rel(EVIDENCE_FILE)}: {exc}")
        evidence = {"evidence": []}

    try:
        risks = load_yaml(RISK_FILE)
        validate_value(risks, RISK_SCHEMA, RISK_FILE, errors)
    except Exception as exc:
        errors.append(f"{rel(RISK_FILE)}: {exc}")
        risks = {"risks": []}

    try:
        roles_data = load_yaml(ROLES_FILE)
        validate_value(roles_data, ROLES_SCHEMA, ROLES_FILE, errors)
        roles = set((roles_data.get("roles") or {}).keys())
        if not roles:
            errors.append(f"{rel(ROLES_FILE)}: no roles defined")
    except Exception as exc:
        errors.append(f"{rel(ROLES_FILE)}: {exc}")
        roles = set()

    try:
        project_backlog = load_yaml(PROJECT_BACKLOG_FILE)
        validate_value(project_backlog, PROJECT_BACKLOG_SCHEMA, PROJECT_BACKLOG_FILE, errors)
    except Exception as exc:
        errors.append(f"{rel(PROJECT_BACKLOG_FILE)}: {exc}")
        project_backlog = {"items": [], "workflow": {}}

    requirement_rows = requirements.get("requirements", [])
    evidence_rows = evidence.get("evidence", [])
    risk_rows = risks.get("risks", [])
    requirement_ids = duplicate_ids(requirement_rows, "requirement", errors)
    evidence_ids = duplicate_ids(evidence_rows, "evidence", errors)
    risk_ids = duplicate_ids(risk_rows, "risk", errors)
    backlog_rows = project_backlog.get("items", [])
    backlog_ids = duplicate_ids(backlog_rows, "project backlog", errors)
    project_views = project_backlog.get("project", {}).get("views", [])
    view_names = [view.get("name") for view in project_views if isinstance(view.get("name"), str)]
    duplicate_view_names = sorted({name for name in view_names if view_names.count(name) > 1})
    if duplicate_view_names:
        errors.append(
            f"{rel(PROJECT_BACKLOG_FILE)}: duplicate Project view names: "
            + ", ".join(duplicate_view_names)
        )

    documents: Dict[str, Tuple[Path, Dict[str, Any]]] = {}
    for path in controlled_markdown():
        try:
            metadata, body = parse_frontmatter(path)
            validate_value(metadata, METADATA_SCHEMA, path, errors)
            doc_id = metadata.get("id")
            if isinstance(doc_id, str):
                if doc_id in documents:
                    errors.append(
                        f"duplicate document id {doc_id}: {rel(documents[doc_id][0])}, {rel(path)}"
                    )
                documents[doc_id] = (path, metadata)
            check_local_links(path, body, errors)
        except Exception as exc:
            errors.append(f"{rel(path)}: {exc}")

    artifact_ids = set(documents) | {"SC-GOV-003", "SC-GOV-004"}

    for doc_id, (path, metadata) in documents.items():
        for role_field in ("owner", "approver"):
            role = metadata.get(role_field)
            if role not in roles:
                errors.append(f"{rel(path)}:{role_field}: unknown role `{role}`")
        for requirement_id in metadata.get("requirements", []):
            if requirement_id not in requirement_ids:
                errors.append(f"{rel(path)}: unknown requirement `{requirement_id}`")
        for evidence_id in metadata.get("evidence", []):
            if evidence_id not in evidence_ids:
                errors.append(f"{rel(path)}: unknown evidence `{evidence_id}`")
        for relation in ("supersedes", "superseded_by"):
            related_id = metadata.get(relation)
            if related_id is not None and related_id not in artifact_ids:
                errors.append(f"{rel(path)}:{relation}: unknown document `{related_id}`")
        if metadata.get("status") == "superseded" and not metadata.get("superseded_by"):
            errors.append(f"{rel(path)}: superseded document has no `superseded_by`")
        if metadata.get("review_mode") == "independent" and metadata.get("owner") == metadata.get("approver"):
            errors.append(f"{rel(path)}: independent review cannot use the same owner and approver")

    for row in requirement_rows:
        requirement_id = row.get("id", "<unknown>")
        source = row.get("source")
        if source not in artifact_ids:
            errors.append(f"{rel(REQUIREMENTS_FILE)}:{requirement_id}: unknown source `{source}`")
        if row.get("priority") == "must" and not row.get("verification"):
            errors.append(f"{rel(REQUIREMENTS_FILE)}:{requirement_id}: must requirement has no verification")
        for decision in row.get("decisions", []):
            if decision not in artifact_ids:
                errors.append(f"{rel(REQUIREMENTS_FILE)}:{requirement_id}: unknown decision `{decision}`")
        for contract in row.get("contracts", []):
            if contract not in artifact_ids:
                errors.append(f"{rel(REQUIREMENTS_FILE)}:{requirement_id}: unknown contract `{contract}`")
        for evidence_id in row.get("verification", []):
            if evidence_id not in evidence_ids:
                errors.append(f"{rel(REQUIREMENTS_FILE)}:{requirement_id}: unknown evidence `{evidence_id}`")
        for implementation in row.get("implementation", []):
            check_path_reference(implementation, f"{rel(REQUIREMENTS_FILE)}:{requirement_id}", errors)
        if row.get("owner") not in roles:
            errors.append(f"{rel(REQUIREMENTS_FILE)}:{requirement_id}: unknown owner `{row.get('owner')}`")

    for row in evidence_rows:
        evidence_id = row.get("id", "<unknown>")
        for requirement_id in row.get("requirements", []):
            if requirement_id not in requirement_ids:
                errors.append(f"{rel(EVIDENCE_FILE)}:{evidence_id}: unknown requirement `{requirement_id}`")
        check_path_reference(row.get("location"), f"{rel(EVIDENCE_FILE)}:{evidence_id}", errors)

    for row in risk_rows:
        risk_id = row.get("id", "<unknown>")
        if row.get("owner") not in roles:
            errors.append(f"{rel(RISK_FILE)}:{risk_id}: unknown owner `{row.get('owner')}`")
        for requirement_id in row.get("requirements", []):
            if requirement_id not in requirement_ids:
                errors.append(f"{rel(RISK_FILE)}:{risk_id}: unknown requirement `{requirement_id}`")

    expected_workflow = {
        "statuses": ["Inbox", "Triage", "Ready", "In Progress", "In Review", "Qualification", "Blocked", "Done"],
        "priorities": ["P0", "P1", "P2", "P3"],
        "workstreams": [
            "WS-01 Governance", "WS-02 Renderer", "WS-03 Conformance",
            "WS-04 Runtime & A11y", "WS-05 Customization", "WS-06 Release",
            "WS-07 Docs & DX", "WS-08 Expansion",
        ],
        "stages": [
            "S0 Foundation", "S1 Contract Closure", "S2 Qualification",
            "S3 Release Candidate", "S4 Release", "S5 Expansion",
            "S6 Qualification 0.0.0.2", "S7 Release Candidate 0.0.0.2", "S8 Release 0.0.0.2",
        ],
        "targets": ["0.0.0.1", "0.0.0.2", "Post-0.0.0.1", "Unscheduled"],
        "item_types": ["Decision", "Requirement", "Work Package", "Defect", "Release Gate"],
    }
    for field, expected in expected_workflow.items():
        if project_backlog.get("workflow", {}).get(field) != expected:
            errors.append(f"{rel(PROJECT_BACKLOG_FILE)}: workflow.{field} must match the governed order")

    requirement_item_ids: Set[str] = set()
    for row in backlog_rows:
        item_id = row.get("id", "<unknown>")
        traceability = row.get("traceability", [])
        for reference in traceability:
            if reference not in requirement_ids and reference not in artifact_ids:
                errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: unknown traceability reference `{reference}`")
        for risk_id in row.get("risks", []):
            if risk_id not in risk_ids:
                errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: unknown risk `{risk_id}`")
        for evidence_id in row.get("evidence", []):
            if evidence_id not in evidence_ids:
                errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: unknown evidence `{evidence_id}`")
        for dependency in row.get("dependencies", []):
            if dependency not in backlog_ids:
                errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: unknown dependency `{dependency}`")
        if row.get("item_type") == "Requirement":
            requirement_item_ids.add(item_id)
            if item_id not in requirement_ids:
                errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: no matching requirement registry entry")
            if item_id not in traceability:
                errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: requirement item must trace to itself")
        elif not row.get("acceptance") or not row.get("verification"):
            errors.append(f"{rel(PROJECT_BACKLOG_FILE)}:{item_id}: non-requirement item needs acceptance and verification")

    missing_requirement_items = requirement_ids - requirement_item_ids
    extra_requirement_items = requirement_item_ids - requirement_ids
    if missing_requirement_items:
        errors.append(
            f"{rel(PROJECT_BACKLOG_FILE)}: requirements missing Project items: "
            + ", ".join(sorted(missing_requirement_items))
        )
    if extra_requirement_items:
        errors.append(
            f"{rel(PROJECT_BACKLOG_FILE)}: Project requirement items missing registry entries: "
            + ", ".join(sorted(extra_requirement_items))
        )

    backlog_by_id = {row["id"]: row for row in backlog_rows if isinstance(row.get("id"), str)}
    for row in backlog_rows:
        if row.get("status") in {"Ready", "In Progress", "In Review", "Qualification", "Done"}:
            unfinished = [
                dependency
                for dependency in row.get("dependencies", [])
                if backlog_by_id.get(dependency, {}).get("status") != "Done"
            ]
            if unfinished:
                errors.append(
                    f"{rel(PROJECT_BACKLOG_FILE)}:{row.get('id')}: active status has unfinished dependencies: "
                    + ", ".join(unfinished)
                )
    check_dependency_cycles(backlog_rows, errors)

    # The active chart schema is itself a controlled machine-readable contract.
    try:
        chart_schema = load_json(ROOT / "spec" / "chart-spec.schema.json")
        validator_class = __import__("jsonschema").validators.validator_for(chart_schema)
        validator_class.check_schema(chart_schema)
    except Exception as exc:
        errors.append(f"spec/chart-spec.schema.json: invalid JSON Schema: {exc}")

    if errors:
        print(f"documentation control FAILED ({len(errors)} issue(s))", file=sys.stderr)
        for issue in errors:
            print(f"- {issue}", file=sys.stderr)
        return 1

    if args.traceability_json:
        evidence_status = {row["id"]: row["status"] for row in evidence_rows}
        risk_by_requirement: Dict[str, List[str]] = {}
        for row in risk_rows:
            for requirement_id in row.get("requirements", []):
                risk_by_requirement.setdefault(requirement_id, []).append(row["id"])
        snapshot = {
            "registryVersion": requirements.get("version"),
            "registryUpdated": requirements.get("updated"),
            "documents": {
                doc_id: {
                    "path": rel(path),
                    "status": metadata["status"],
                    "classification": metadata["classification"],
                }
                for doc_id, (path, metadata) in sorted(documents.items())
            },
            "requirements": [
                {
                    "id": row["id"],
                    "status": row["status"],
                    "target": row["target"],
                    "source": row["source"],
                    "decisions": row["decisions"],
                    "contracts": row["contracts"],
                    "verification": [
                        {"id": item, "status": evidence_status[item]}
                        for item in row["verification"]
                    ],
                    "implementation": row["implementation"],
                    "risks": sorted(risk_by_requirement.get(row["id"], [])),
                }
                for row in requirement_rows
            ],
            "projectBacklog": [
                {
                    "id": row["id"],
                    "type": row["item_type"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "workstream": row["workstream"],
                    "stage": row["stage"],
                    "target": row["target"],
                    "traceability": row["traceability"],
                    "risks": row["risks"],
                    "evidence": row["evidence"],
                    "dependencies": row["dependencies"],
                }
                for row in backlog_rows
            ],
        }
        output_path = args.traceability_json
        if not output_path.is_absolute():
            output_path = ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        print(f"traceability snapshot: {output_path}")

    print(
        "documentation control PASS: "
        f"{len(documents)} documents, {len(requirement_ids)} requirements, "
        f"{len(evidence_ids)} evidence definitions, {len(risk_rows)} risks, "
        f"{len(backlog_ids)} project items"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
