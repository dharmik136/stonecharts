#!/usr/bin/env python3
"""Apply or verify the governed StoneCharts GitHub Project backlog."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - actionable bootstrap path
    print(
        "missing project-control dependency: PyYAML; install with "
        "`python -m pip install -e \"libs/python[dev]\"`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


ROOT = Path(__file__).resolve().parents[1]
BACKLOG_FILE = ROOT / "docs" / "project" / "backlog.yaml"
REQUIREMENTS_FILE = ROOT / "docs" / "requirements" / "registry.yaml"

FIELD_SPECS = {
    "Tracking ID": ("TEXT", None),
    "Item Type": ("SINGLE_SELECT", "item_types"),
    "Priority": ("SINGLE_SELECT", "priorities"),
    "Workstream": ("SINGLE_SELECT", "workstreams"),
    "Stage": ("SINGLE_SELECT", "stages"),
    "Target": ("SINGLE_SELECT", "targets"),
    "Traceability": ("TEXT", None),
    "Risks": ("TEXT", None),
    "Evidence": ("TEXT", None),
    "Dependencies": ("TEXT", None),
}

SELECT_STYLE = {
    "Status": {
        "Inbox": ("GRAY", "Admitted but not yet assessed"),
        "Triage": ("YELLOW", "Being scoped, sequenced, or dependency-checked"),
        "Ready": ("BLUE", "Acceptance is complete and every dependency is done"),
        "In Progress": ("ORANGE", "Active implementation or decision work"),
        "In Review": ("PURPLE", "Awaiting technical or product review"),
        "Qualification": ("PINK", "Implementation complete; required evidence is running"),
        "Blocked": ("RED", "Cannot progress until a named dependency changes"),
        "Done": ("GREEN", "Integrated, verified, evidenced, and documented"),
    },
    "Item Type": {
        "Decision": ("PURPLE", "Bounded product, architecture, or operating decision"),
        "Requirement": ("BLUE", "Delivery and qualification of a registered requirement"),
        "Work Package": ("GRAY", "Bounded implementation, documentation, or operations outcome"),
        "Defect": ("RED", "Incorrect, unsafe, divergent, or regressed behavior"),
        "Release Gate": ("YELLOW", "Evidence-based authorization to enter the next stage"),
    },
    "Priority": {
        "P0": ("RED", "Security, integrity, or release blocker"),
        "P1": ("ORANGE", "Required for the target release or stage"),
        "P2": ("YELLOW", "Valuable and deferrable"),
        "P3": ("GRAY", "Exploratory or long-range backlog"),
    },
    "Workstream": {
        "WS-01 Governance": ("PURPLE", "Product contract and governance"),
        "WS-02 Renderer": ("BLUE", "Renderer correctness and active scope"),
        "WS-03 Conformance": ("GREEN", "Parity, tests, security, and performance evidence"),
        "WS-04 Runtime & A11y": ("YELLOW", "Browser runtime and accessibility"),
        "WS-05 Customization": ("PINK", "Customization, layout, and visual profiles"),
        "WS-06 Release": ("ORANGE", "Packaging, release, and supply chain"),
        "WS-07 Docs & DX": ("GRAY", "Documentation and developer experience"),
        "WS-08 Expansion": ("RED", "Chart and language expansion admission"),
    },
    "Stage": {
        "S0 Foundation": ("PURPLE", "Governed product and execution baseline"),
        "S1 Contract Closure": ("BLUE", "Correct and freeze active release behavior"),
        "S2 Qualification": ("GREEN", "Collect conformance and quality evidence"),
        "S3 Release Candidate": ("ORANGE", "Build artifacts and immutable evidence"),
        "S4 Release": ("PINK", "Authorize and publish 0.0.0.1"),
        "S5 Expansion": ("GRAY", "Admit post-release charts and languages"),
        "S6 Qualification 0.0.0.2": ("GREEN", "Collect conformance and quality evidence for 0.0.0.2"),
        "S7 Release Candidate 0.0.0.2": ("ORANGE", "Build artifacts and immutable evidence for 0.0.0.2"),
        "S8 Release 0.0.0.2": ("PINK", "Authorize and publish 0.0.0.2"),
    },
    "Target": {
        "0.0.0.1": ("GREEN", "Required for the first governed release"),
        "0.0.0.2": ("BLUE", "Required for the second governed release"),
        "Post-0.0.0.1": ("PURPLE", "Begins only after the first release"),
        "Unscheduled": ("GRAY", "No approved release target"),
    },
}

LABEL_SPECS = {
    "type:defect": ("B60205", "Incorrect, unsafe, divergent, or regressed behavior"),
    "type:work": ("1D76DB", "Planned implementation, qualification, documentation, or operations work"),
    "type:decision": ("5319E7", "A bounded decision requiring explicit resolution"),
    "type:gate": ("FBCA04", "An evidence-based stage or release authorization"),
    "role:planner": ("5319E7", "Planning, scope, and decision routing"),
    "role:developer": ("0052CC", "Implementation and controlled code changes"),
    "role:qa": ("0E8A16", "Verification, parity, and regression evidence"),
    "role:security": ("B60205", "Security and supply-chain review"),
    "role:compliance": ("D4C5F9", "Traceability and document control"),
    "role:release": ("FBCA04", "Release assembly and final ship evidence"),
    "priority:P0": ("B60205", "Security, data integrity, or release blocker"),
    "priority:P1": ("D93F0B", "Required for the active milestone"),
    "priority:P2": ("FBCA04", "Valuable and deferrable"),
    "priority:P3": ("0E8A16", "Exploratory or long-range backlog"),
    "target:0.0.0.1": ("0E8A16", "Targets StoneCharts release 0.0.0.1"),
    "target:post-0.0.0.1": ("0052CC", "Begins after the first governed release"),
    "target:unscheduled": ("8A8A8A", "No approved target release"),
    "area:spec": ("0052CC", "Specification, schema, validation, or capability contract"),
    "area:python": ("3572A5", "Python package or renderer"),
    "area:go": ("00ADD8", "Go module or renderer"),
    "area:runtime": ("F1E05A", "Browser runtime, DOM, interaction, or accessibility"),
    "area:docs": ("0075CA", "Controlled documentation or developer guidance"),
    "area:release": ("C5DEF5", "Packaging, evidence, release, or supply chain"),
    "area:security": ("B60205", "Security boundary, vulnerability, or threat control"),
    "release:0.0.0.1": ("0E8A16", "Targets StoneCharts release 0.0.0.1"),
}


class ProjectError(RuntimeError):
    """Raised when GitHub Project application or verification fails."""


def load_yaml(path: Path) -> Dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProjectError(f"{path}: expected a YAML object")
    return value


def run_gh(args: Sequence[str], payload: Any = None) -> str:
    command = ["gh", *args]
    input_text = None if payload is None else json.dumps(payload)
    process = subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.returncode:
        detail = process.stderr.strip() or process.stdout.strip()
        raise ProjectError(f"`{' '.join(command)}` failed: {detail}")
    return process.stdout


def gh_json(args: Sequence[str], payload: Any = None) -> Any:
    output = run_gh(args, payload)
    return json.loads(output) if output.strip() else None


def graphql(query: str, variables: Mapping[str, Any]) -> Dict[str, Any]:
    response = gh_json(["api", "graphql", "--input", "-"], {"query": query, "variables": variables})
    if response.get("errors"):
        raise ProjectError("GitHub GraphQL error: " + json.dumps(response["errors"]))
    return response["data"]


def csv(values: Iterable[str]) -> str:
    materialized = list(values)
    return ", ".join(materialized) if materialized else "None"


def expected_labels(item: Mapping[str, Any]) -> List[str]:
    type_label = {
        "Decision": "type:decision",
        "Requirement": "type:work",
        "Work Package": "type:work",
        "Defect": "type:defect",
        "Release Gate": "type:gate",
    }[item["item_type"]]
    labels = [type_label, f"priority:{item['priority']}"]
    labels.extend(f"area:{area}" for area in item["areas"])
    if item["target"] == "0.0.0.1":
        labels.append("release:0.0.0.1")
    return sorted(labels)


def issue_body(
    item: Mapping[str, Any],
    requirements: Mapping[str, Mapping[str, Any]],
    backlog: Mapping[str, Mapping[str, Any]],
) -> str:
    done = item["status"] == "Done"
    mark = "x" if done else " "
    lines = [
        f"<!-- stonecharts-project:v1 tracking={item['id']} -->",
        "",
        "## Required outcome",
        "",
        item["outcome"],
        "",
        "## Control classification",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Tracking ID | `{item['id']}` |",
        f"| Item type | {item['item_type']} |",
        f"| Priority | {item['priority']} |",
        f"| Workstream | {item['workstream']} |",
        f"| Stage | {item['stage']} |",
        f"| Target | {item['target']} |",
        "",
        "## Traceability",
        "",
        f"- Requirements, ADRs, contracts, or documents: {csv(f'`{value}`' for value in item['traceability'])}",
        f"- Risks: {csv(f'`{value}`' for value in item['risks'])}",
        f"- Required evidence: {csv(f'`{value}`' for value in item['evidence'])}",
        "",
    ]

    requirement = requirements.get(item["id"])
    if requirement:
        lines.extend(
            [
                "## Registered contract",
                "",
                requirement["statement"],
                "",
                f"**Rationale:** {requirement['rationale']}",
                "",
                "## Acceptance criteria",
                "",
            ]
        )
        lines.extend(f"- [{mark}] {value}" for value in requirement["acceptance"])
        lines.extend(
            [
                "",
                "## Affected implementation",
                "",
                *[f"- `{value}`" for value in requirement["implementation"]],
                "",
                "## Verification",
                "",
                *[f"- `{value}`" for value in requirement["verification"]],
            ]
        )
    else:
        lines.extend(["## Acceptance criteria", ""])
        lines.extend(f"- [{mark}] {value}" for value in item["acceptance"])
        lines.extend(["", "## Verification", ""])
        lines.extend(f"- {value}" for value in item["verification"])

    dependencies = item["dependencies"]
    lines.extend(["", "## Dependencies", ""])
    if dependencies:
        for dependency in dependencies:
            dependency_done = backlog[dependency]["status"] == "Done"
            lines.append(f"- [{'x' if dependency_done else ' '}] `{dependency}`")
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Compatibility impact",
            "",
            item["compatibility"],
            "",
            "## Completion contract",
            "",
            f"- [{mark}] Acceptance criteria pass.",
            f"- [{mark}] Required evidence is recorded and reviewable.",
            f"- [{mark}] Affected controlled documentation is current.",
            f"- [{mark}] Project fields and dependencies match the governed backlog.",
            "",
            "---",
            "Governed source: `docs/project/backlog.yaml`. Update the source and apply the",
            "Project control tool rather than editing classification fields independently.",
            "",
        ]
    )
    return "\n".join(lines)


def project_field_list(number: int, owner: str) -> Dict[str, Dict[str, Any]]:
    data = gh_json(["project", "field-list", str(number), "--owner", owner, "--format", "json"])
    return {field["name"]: field for field in data["fields"]}


def update_select_options(field: Mapping[str, Any], names: Sequence[str]) -> None:
    existing = {option["name"]: option["id"] for option in field.get("options", [])}
    style = SELECT_STYLE[field["name"]]
    options = []
    for name in names:
        color, description = style[name]
        option = {"name": name, "color": color, "description": description}
        if name in existing:
            option["id"] = existing[name]
        options.append(option)
    query = """
      mutation($input: UpdateProjectV2FieldInput!) {
        updateProjectV2Field(input: $input) {
          projectV2Field { ... on ProjectV2SingleSelectField { id name } }
        }
      }
    """
    graphql(query, {"input": {"fieldId": field["id"], "singleSelectOptions": options}})


def ensure_fields(backlog: Mapping[str, Any]) -> tuple[str, Dict[str, Dict[str, Any]]]:
    owner = backlog["project"]["owner"]
    number = backlog["project"]["number"]
    project = gh_json(["project", "view", str(number), "--owner", owner, "--format", "json"])
    fields = project_field_list(number, owner)
    if "Status" not in fields:
        raise ProjectError("GitHub Project has no Status field")
    update_select_options(fields["Status"], backlog["workflow"]["statuses"])

    for name, (data_type, source) in FIELD_SPECS.items():
        if name not in fields:
            args = [
                "project", "field-create", str(number), "--owner", owner,
                "--name", name, "--data-type", data_type, "--format", "json",
            ]
            if source:
                args.extend(["--single-select-options", ",".join(backlog["workflow"][source])])
            gh_json(args)
            fields = project_field_list(number, owner)
        if data_type == "SINGLE_SELECT":
            update_select_options(fields[name], backlog["workflow"][source])

    fields = project_field_list(number, owner)
    return project["id"], fields


def ensure_labels(repository: str) -> None:
    for name, (color, description) in LABEL_SPECS.items():
        run_gh(
            [
                "label", "create", name, "--repo", repository, "--color", color,
                "--description", description, "--force",
            ]
        )


def ensure_milestone(repository: str, title: str) -> int:
    milestones = gh_json(["api", f"repos/{repository}/milestones?state=all&per_page=100"])
    exact = next((item for item in milestones if item["title"] == title), None)
    if exact:
        return exact["number"]
    legacy = next((item for item in milestones if item["title"] == "0.0.1-alpha.1"), None)
    payload = {
        "title": title,
        "description": "StoneCharts first governed release: Stage 0 through release qualification and publication.",
        "state": "open",
    }
    if legacy:
        result = gh_json(
            ["api", "--method", "PATCH", f"repos/{repository}/milestones/{legacy['number']}", "--input", "-"],
            payload,
        )
    else:
        result = gh_json(["api", "--method", "POST", f"repos/{repository}/milestones", "--input", "-"], payload)
    return result["number"]


def list_issues(repository: str) -> Dict[str, Dict[str, Any]]:
    issues = gh_json(
        [
            "issue", "list", "--repo", repository, "--state", "all", "--limit", "1000",
            "--json", "number,title,url,state,body,labels,milestone,assignees",
        ]
    )
    found: Dict[str, Dict[str, Any]] = {}
    for issue in issues:
        title = issue["title"]
        if title.startswith("[") and "]" in title:
            found[title[1:title.index("]")]] = issue
    return found


def upsert_issue(
    repository: str,
    owner: str,
    milestone_number: int,
    item: Mapping[str, Any],
    body: str,
    existing: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    payload = {
        "title": f"[{item['id']}] {item['title']}",
        "body": body,
        "labels": expected_labels(item),
        "milestone": milestone_number if item["target"] == "0.0.0.1" else None,
        "assignees": [owner],
    }
    if existing:
        payload["state"] = "closed" if item["status"] == "Done" else "open"
        if item["status"] == "Done":
            payload["state_reason"] = "completed"
        return gh_json(
            ["api", "--method", "PATCH", f"repos/{repository}/issues/{existing['number']}", "--input", "-"],
            payload,
        )

    issue = gh_json(["api", "--method", "POST", f"repos/{repository}/issues", "--input", "-"], payload)
    if item["status"] == "Done":
        issue = gh_json(
            ["api", "--method", "PATCH", f"repos/{repository}/issues/{issue['number']}", "--input", "-"],
            {"state": "closed", "state_reason": "completed"},
        )
    return issue


def fetch_project_items(owner: str, number: int) -> List[Dict[str, Any]]:
    query = """
      query($owner: String!, $number: Int!) {
        user(login: $owner) {
          projectV2(number: $number) {
            items(first: 100) {
              nodes {
                id
                content {
                  __typename
                  ... on Issue {
                    id number title url state body
                    repository { nameWithOwner }
                    milestone { title }
                    assignees(first: 20) { nodes { login } }
                    labels(first: 50) { nodes { name } }
                  }
                }
                fieldValues(first: 100) {
                  nodes {
                    ... on ProjectV2ItemFieldTextValue {
                      text
                      field { ... on ProjectV2Field { name } }
                    }
                    ... on ProjectV2ItemFieldSingleSelectValue {
                      name
                      field { ... on ProjectV2SingleSelectField { name } }
                    }
                  }
                }
              }
            }
          }
        }
      }
    """
    data = graphql(query, {"owner": owner, "number": number})
    project = data.get("user", {}).get("projectV2")
    if not project:
        raise ProjectError(f"GitHub Project {owner}/{number} not found")
    return project["items"]["nodes"]


def fetch_project_views(owner: str, number: int) -> List[Dict[str, Any]]:
    query = """
      query($owner: String!, $number: Int!) {
        user(login: $owner) {
          projectV2(number: $number) {
            views(first: 100) {
              nodes {
                name layout filter
                fields(first: 100) {
                  nodes {
                    ... on ProjectV2Field { name }
                    ... on ProjectV2SingleSelectField { name }
                    ... on ProjectV2IterationField { name }
                  }
                }
                groupByFields(first: 100) {
                  nodes {
                    ... on ProjectV2Field { name }
                    ... on ProjectV2SingleSelectField { name }
                    ... on ProjectV2IterationField { name }
                  }
                }
              }
            }
          }
        }
      }
    """
    data = graphql(query, {"owner": owner, "number": number})
    project = data.get("user", {}).get("projectV2")
    if not project:
        raise ProjectError(f"GitHub Project {owner}/{number} not found")
    return project["views"]["nodes"]


def add_project_item(project_id: str, issue_node_id: str) -> str:
    query = """
      mutation($input: AddProjectV2ItemByIdInput!) {
        addProjectV2ItemById(input: $input) { item { id } }
      }
    """
    data = graphql(query, {"input": {"projectId": project_id, "contentId": issue_node_id}})
    return data["addProjectV2ItemById"]["item"]["id"]


def expected_field_values(item: Mapping[str, Any]) -> Dict[str, str]:
    return {
        "Tracking ID": item["id"],
        "Item Type": item["item_type"],
        "Status": item["status"],
        "Priority": item["priority"],
        "Workstream": item["workstream"],
        "Stage": item["stage"],
        "Target": item["target"],
        "Traceability": csv(item["traceability"]),
        "Risks": csv(item["risks"]),
        "Evidence": csv(item["evidence"]),
        "Dependencies": csv(item["dependencies"]),
    }


def set_item_fields(
    project_id: str,
    project_item_id: str,
    fields: Mapping[str, Mapping[str, Any]],
    values: Mapping[str, str],
) -> None:
    variable_definitions = []
    selections = []
    variables: Dict[str, Any] = {}
    for index, (name, value) in enumerate(values.items()):
        variable = f"input{index}"
        variable_definitions.append(f"${variable}: UpdateProjectV2ItemFieldValueInput!")
        selections.append(
            f"value{index}: updateProjectV2ItemFieldValue(input: ${variable}) "
            "{ projectV2Item { id } }"
        )
        field = fields[name]
        if field["type"] == "ProjectV2SingleSelectField":
            option_ids = {option["name"]: option["id"] for option in field["options"]}
            encoded_value = {"singleSelectOptionId": option_ids[value]}
        else:
            encoded_value = {"text": value}
        variables[variable] = {
            "projectId": project_id,
            "itemId": project_item_id,
            "fieldId": field["id"],
            "value": encoded_value,
        }
    query = "mutation(" + ", ".join(variable_definitions) + ") { " + " ".join(selections) + " }"
    graphql(query, variables)


def apply(backlog: Mapping[str, Any], requirements: Mapping[str, Mapping[str, Any]]) -> None:
    owner = backlog["project"]["owner"]
    number = backlog["project"]["number"]
    repository = backlog["project"]["repository"]
    milestone = backlog["project"]["milestone"]
    items = backlog["items"]
    by_id = {item["id"]: item for item in items}

    print("Configuring labels, milestone, workflow, and Project fields...", flush=True)
    ensure_labels(repository)
    milestone_number = ensure_milestone(repository, milestone)
    project_id, fields = ensure_fields(backlog)

    remote_items = fetch_project_items(owner, number)
    item_id_by_url = {
        node["content"].get("url"): node["id"]
        for node in remote_items
        if node.get("content") and node["content"].get("url")
    }
    existing_issues = list_issues(repository)

    for index, item in enumerate(items, start=1):
        print(f"[{index:02d}/{len(items):02d}] Applying {item['id']}: {item['title']}", flush=True)
        body = issue_body(item, requirements, by_id)
        issue = upsert_issue(
            repository,
            owner,
            milestone_number,
            item,
            body,
            existing_issues.get(item["id"]),
        )
        project_item_id = item_id_by_url.get(issue["html_url"])
        if not project_item_id:
            project_item_id = add_project_item(project_id, issue["node_id"])
            item_id_by_url[issue["html_url"]] = project_item_id
        set_item_fields(project_id, project_item_id, fields, expected_field_values(item))


def field_values(node: Mapping[str, Any]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for value in node["fieldValues"]["nodes"]:
        field = value.get("field")
        if not field or not field.get("name"):
            continue
        if "text" in value:
            values[field["name"]] = value["text"]
        elif "name" in value:
            values[field["name"]] = value["name"]
    return values


def check_fields(backlog: Mapping[str, Any], errors: List[str]) -> Dict[str, Dict[str, Any]]:
    owner = backlog["project"]["owner"]
    number = backlog["project"]["number"]
    fields = project_field_list(number, owner)
    expected_selects = {"Status": backlog["workflow"]["statuses"]}
    for name, (data_type, source) in FIELD_SPECS.items():
        field = fields.get(name)
        if not field:
            errors.append(f"missing Project field: {name}")
            continue
        expected_type = "ProjectV2Field" if data_type == "TEXT" else "ProjectV2SingleSelectField"
        if field["type"] != expected_type:
            errors.append(f"Project field {name}: expected {expected_type}, got {field['type']}")
        if source:
            expected_selects[name] = backlog["workflow"][source]
    status = fields.get("Status")
    if not status:
        errors.append("missing Project field: Status")
    for name, expected in expected_selects.items():
        field = fields.get(name)
        if field and [option["name"] for option in field.get("options", [])] != expected:
            errors.append(f"Project field {name}: option order or values drifted")
    return fields


def check_views(backlog: Mapping[str, Any], errors: List[str]) -> None:
    owner = backlog["project"]["owner"]
    number = backlog["project"]["number"]
    expected_views = backlog["project"]["views"]
    remote_views = fetch_project_views(owner, number)
    expected_names = [view["name"] for view in expected_views]
    remote_names = [view["name"] for view in remote_views]
    if remote_names != expected_names:
        errors.append(f"Project view order or names drifted: {remote_names}; expected {expected_names}")

    remote_by_name = {view["name"]: view for view in remote_views}
    for expected in expected_views:
        name = expected["name"]
        actual = remote_by_name.get(name)
        if not actual:
            continue
        if actual["layout"] != expected["layout"]:
            errors.append(
                f"Project view {name}: layout is {actual['layout']}, expected {expected['layout']}"
            )
        if (actual.get("filter") or "") != expected["filter"]:
            errors.append(
                f"Project view {name}: filter is {actual.get('filter')!r}, "
                f"expected {expected['filter']!r}"
            )
        actual_fields = [field["name"] for field in actual["fields"]["nodes"]]
        if actual_fields != expected["fields"]:
            errors.append(f"Project view {name}: visible fields drifted: {actual_fields}")
        actual_groups = [field["name"] for field in actual["groupByFields"]["nodes"]]
        if actual_groups != expected["group_by"]:
            errors.append(
                f"Project view {name}: grouping is {actual_groups}, expected {expected['group_by']}"
            )


def check(backlog: Mapping[str, Any], requirements: Mapping[str, Mapping[str, Any]]) -> int:
    errors: List[str] = []
    check_fields(backlog, errors)
    check_views(backlog, errors)
    owner = backlog["project"]["owner"]
    number = backlog["project"]["number"]
    repository = backlog["project"]["repository"]
    milestone = backlog["project"]["milestone"]
    expected_items = {item["id"]: item for item in backlog["items"]}
    remote_items = fetch_project_items(owner, number)
    seen: set[str] = set()

    for node in remote_items:
        values = field_values(node)
        tracking_id = values.get("Tracking ID")
        content = node.get("content")
        if not tracking_id:
            errors.append(f"Project item {node['id']} has no Tracking ID")
            continue
        if tracking_id not in expected_items:
            errors.append(f"unregistered Project item: {tracking_id}")
            continue
        if tracking_id in seen:
            errors.append(f"duplicate Project item: {tracking_id}")
            continue
        seen.add(tracking_id)
        item = expected_items[tracking_id]
        if not content or content.get("__typename") != "Issue":
            errors.append(f"{tracking_id}: Project item is not a GitHub issue")
            continue
        if content["repository"]["nameWithOwner"] != repository:
            errors.append(f"{tracking_id}: issue belongs to {content['repository']['nameWithOwner']}")
        expected_title = f"[{tracking_id}] {item['title']}"
        if content["title"] != expected_title:
            errors.append(f"{tracking_id}: issue title drifted")
        expected_body = issue_body(item, requirements, expected_items)
        if content["body"].replace("\r\n", "\n") != expected_body:
            errors.append(f"{tracking_id}: governed issue body drifted")
        expected_state = "CLOSED" if item["status"] == "Done" else "OPEN"
        if content["state"] != expected_state:
            errors.append(f"{tracking_id}: issue state is {content['state']}, expected {expected_state}")
        expected_milestone = milestone if item["target"] == "0.0.0.1" else None
        actual_milestone = content.get("milestone", {}).get("title") if content.get("milestone") else None
        if actual_milestone != expected_milestone:
            errors.append(f"{tracking_id}: milestone is {actual_milestone!r}, expected {expected_milestone!r}")
        actual_labels = sorted(label["name"] for label in content["labels"]["nodes"])
        if actual_labels != expected_labels(item):
            errors.append(f"{tracking_id}: labels drifted: {actual_labels}")
        assignees = sorted(person["login"] for person in content["assignees"]["nodes"])
        if assignees != [owner]:
            errors.append(f"{tracking_id}: assignees are {assignees}, expected [{owner}]")
        for field, expected in expected_field_values(item).items():
            if values.get(field) != expected:
                errors.append(f"{tracking_id}: {field} is {values.get(field)!r}, expected {expected!r}")

    missing = set(expected_items) - seen
    if missing:
        errors.append("missing Project items: " + ", ".join(sorted(missing)))

    if errors:
        print(f"GitHub Project conformance FAILED ({len(errors)} issue(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"GitHub Project conformance PASS: {len(seen)} governed items, "
        f"{len(backlog['workflow']['statuses'])} statuses, {len(FIELD_SPECS) + 1} governed fields, "
        f"{len(backlog['project']['views'])} saved views"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "create or update labels, milestone, fields, issues, and Project values before checking; "
            "saved views are verified but remain UI-managed"
        ),
    )
    args = parser.parse_args()
    backlog = load_yaml(BACKLOG_FILE)
    requirement_data = load_yaml(REQUIREMENTS_FILE)
    requirements = {row["id"]: row for row in requirement_data["requirements"]}
    try:
        if args.apply:
            apply(backlog, requirements)
        return check(backlog, requirements)
    except (ProjectError, OSError, json.JSONDecodeError) as exc:
        print(f"GitHub Project control FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
