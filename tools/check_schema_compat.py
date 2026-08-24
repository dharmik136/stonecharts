"""Check supported JSON Schema backward-compatibility rules.

Compares an old and new schema file and reports breaking changes:
- Removed properties
- Narrowed enum values
- Newly required fields
- Type changes
- Narrowed numeric, string, and array bounds
- Added or changed patterns and constants
- Restricted additional properties
- Changed combinator topology

Exit code 0 = compatible, 1 = breaking changes found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_MISSING = object()


def _canonical(value: Any) -> str:
    """Represent JSON values without conflating values such as 1 and "1"."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _compare_lower_bound(
    old: dict[str, Any],
    new: dict[str, Any],
    path: str,
    keyword: str,
    breaking: list[str],
) -> None:
    old_value = old.get(keyword, _MISSING)
    new_value = new.get(keyword, _MISSING)
    if new_value is _MISSING:
        return
    if old_value is _MISSING:
        breaking.append(f"NARROWED BOUND: {path} added {keyword} {_canonical(new_value)}")
    elif _is_number(old_value) and _is_number(new_value) and new_value > old_value:
        breaking.append(
            f"NARROWED BOUND: {path} raised {keyword} from {_canonical(old_value)} to {_canonical(new_value)}"
        )


def _compare_upper_bound(
    old: dict[str, Any],
    new: dict[str, Any],
    path: str,
    keyword: str,
    breaking: list[str],
) -> None:
    old_value = old.get(keyword, _MISSING)
    new_value = new.get(keyword, _MISSING)
    if new_value is _MISSING:
        return
    if old_value is _MISSING:
        breaking.append(f"NARROWED BOUND: {path} added {keyword} {_canonical(new_value)}")
    elif _is_number(old_value) and _is_number(new_value) and new_value < old_value:
        breaking.append(
            f"NARROWED BOUND: {path} lowered {keyword} from {_canonical(old_value)} to {_canonical(new_value)}"
        )


def _compare_schemas(
    old: dict[str, Any] | bool,
    new: dict[str, Any] | bool,
    path: str,
    breaking: list[str],
) -> None:
    """Recursively compare two schema nodes and collect breaking changes."""

    if isinstance(old, bool) or isinstance(new, bool):
        if old is True and new is False:
            breaking.append(f"BOOLEAN SCHEMA RESTRICTED: {path} changed from true to false")
        elif isinstance(old, dict) and new is False:
            breaking.append(f"BOOLEAN SCHEMA RESTRICTED: {path} changed to false")
        elif old is True and isinstance(new, dict):
            breaking.append(f"BOOLEAN SCHEMA RESTRICTED: {path} changed from true to a constrained schema")
        return

    # --- Removed properties ---------------------------------------------------
    old_props = old.get("properties", {})
    new_props = new.get("properties", {})
    for key in old_props:
        if key not in new_props:
            breaking.append(f"REMOVED PROPERTY: {path}/properties/{key}")
        else:
            _compare_schemas(old_props[key], new_props[key], f"{path}/properties/{key}", breaking)

    # --- Narrowed enum values -------------------------------------------------
    old_enum = old.get("enum", _MISSING)
    new_enum = new.get("enum", _MISSING)
    if new_enum is not _MISSING:
        if old_enum is _MISSING:
            breaking.append(f"NARROWED ENUM: {path} added enum constraint")
        else:
            new_values = {_canonical(value) for value in new_enum}
            removed_values = sorted(
                (value for value in old_enum if _canonical(value) not in new_values),
                key=_canonical,
            )
            for value in removed_values:
                breaking.append(f"NARROWED ENUM: {path} removed value {_canonical(value)}")

    # --- Newly required fields ------------------------------------------------
    old_required = set(old.get("required", []))
    new_required = set(new.get("required", []))
    for field in sorted(new_required - old_required):
        breaking.append(f"NEWLY REQUIRED: {path} added required field '{field}'")

    # --- Type changes ---------------------------------------------------------
    old_type = old.get("type")
    new_type = new.get("type")
    if old_type is not None and new_type is not None and old_type != new_type:
        breaking.append(f"TYPE CHANGED: {path} changed from {old_type!r} to {new_type!r}")

    # --- Numeric, string, and array bound narrowing ---------------------------
    for keyword in ("minimum", "exclusiveMinimum", "minItems", "minLength"):
        _compare_lower_bound(old, new, path, keyword, breaking)
    for keyword in ("maximum", "exclusiveMaximum", "maxItems", "maxLength"):
        _compare_upper_bound(old, new, path, keyword, breaking)

    # --- Pattern and const restrictions --------------------------------------
    old_pattern = old.get("pattern", _MISSING)
    new_pattern = new.get("pattern", _MISSING)
    if new_pattern is not _MISSING and old_pattern is _MISSING:
        breaking.append(f"PATTERN ADDED: {path} added pattern {_canonical(new_pattern)}")
    elif new_pattern is not _MISSING and old_pattern != new_pattern:
        breaking.append(
            f"PATTERN CHANGED: {path} changed pattern from {_canonical(old_pattern)} to {_canonical(new_pattern)}"
        )

    old_const = old.get("const", _MISSING)
    new_const = new.get("const", _MISSING)
    if new_const is not _MISSING and old_const is _MISSING:
        breaking.append(f"CONST ADDED: {path} added const {_canonical(new_const)}")
    elif new_const is not _MISSING and _canonical(old_const) != _canonical(new_const):
        breaking.append(f"CONST CHANGED: {path} changed const from {_canonical(old_const)} to {_canonical(new_const)}")

    # --- additionalProperties restrictions ----------------------------------
    old_additional = old.get("additionalProperties", True)
    new_additional = new.get("additionalProperties", True)
    if old_additional is not False:
        if new_additional is False:
            breaking.append(f"ADDITIONAL PROPERTIES RESTRICTED: {path} changed to false")
        elif old_additional is True and isinstance(new_additional, dict):
            breaking.append(f"ADDITIONAL PROPERTIES RESTRICTED: {path} changed from true to a constrained schema")
        elif isinstance(old_additional, dict) and isinstance(new_additional, dict):
            _compare_schemas(
                old_additional,
                new_additional,
                f"{path}/additionalProperties",
                breaking,
            )

    # --- Recurse into items ---------------------------------------------------
    old_items = old.get("items")
    new_items = new.get("items")
    if isinstance(old_items, dict) and isinstance(new_items, dict):
        _compare_schemas(old_items, new_items, f"{path}/items", breaking)

    # --- Recurse into $defs / definitions -------------------------------------
    for defs_key in ("$defs", "definitions"):
        old_defs = old.get(defs_key, {})
        new_defs = new.get(defs_key, {})
        for key in old_defs:
            if key not in new_defs:
                breaking.append(f"REMOVED DEFINITION: {path}/{defs_key}/{key}")
            else:
                _compare_schemas(
                    old_defs[key],
                    new_defs[key],
                    f"{path}/{defs_key}/{key}",
                    breaking,
                )

    # --- Recurse into combinators (allOf, anyOf, oneOf) -----------------------
    for combinator in ("allOf", "anyOf", "oneOf"):
        old_list = old.get(combinator, [])
        new_list = new.get(combinator, [])
        if len(old_list) != len(new_list):
            breaking.append(
                f"COMBINATOR TOPOLOGY CHANGED: {path}/{combinator} branch count changed "
                f"from {len(old_list)} to {len(new_list)}"
            )
        for i, (old_item, new_item) in enumerate(zip(old_list, new_list)):
            _compare_schemas(old_item, new_item, f"{path}/{combinator}[{i}]", breaking)

    # --- Recurse into conditional keywords (if/then/else) ---------------------
    for kw in ("if", "then", "else"):
        old_kw = old.get(kw)
        new_kw = new.get(kw)
        if isinstance(old_kw, dict) and isinstance(new_kw, dict):
            _compare_schemas(old_kw, new_kw, f"{path}/{kw}", breaking)


def find_breaking_changes(
    old: dict[str, Any] | bool,
    new: dict[str, Any] | bool,
) -> list[str]:
    """Return the supported set of candidate-schema compatibility failures."""
    breaking: list[str] = []
    _compare_schemas(old, new, "#", breaking)
    return breaking


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check JSON Schema backward compatibility between two versions.",
    )
    parser.add_argument(
        "old_schema",
        type=Path,
        help="Path to the old (baseline) schema file.",
    )
    parser.add_argument(
        "new_schema",
        type=Path,
        help="Path to the new (candidate) schema file.",
    )
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=None,
        help="JSON file listing acknowledged breaking changes that should not fail the check.",
    )
    args = parser.parse_args()

    if not args.old_schema.exists():
        print(f"Error: old schema not found: {args.old_schema}", file=sys.stderr)
        return 2

    if not args.new_schema.exists():
        print(f"Error: new schema not found: {args.new_schema}", file=sys.stderr)
        return 2

    with open(args.old_schema, encoding="utf-8") as f:
        old = json.load(f)

    with open(args.new_schema, encoding="utf-8") as f:
        new = json.load(f)

    acknowledged: set[str] = set()
    if args.exceptions and args.exceptions.exists():
        with open(args.exceptions, encoding="utf-8") as f:
            exceptions = json.load(f)
        acknowledged = set(exceptions.get("acknowledged", []))

    breaking = find_breaking_changes(old, new)

    unacknowledged = [msg for msg in breaking if msg not in acknowledged]
    ack_matched = [msg for msg in breaking if msg in acknowledged]

    for msg in ack_matched:
        print(f"ACKNOWLEDGED: {msg}")
    for msg in unacknowledged:
        print(msg)

    if unacknowledged:
        print(f"\n{len(unacknowledged)} unacknowledged breaking changes found")
        if ack_matched:
            print(f"({len(ack_matched)} acknowledged changes skipped)")
        return 1

    if ack_matched:
        print(f"\n{len(ack_matched)} acknowledged changes, 0 unacknowledged")
    else:
        print("No breaking changes found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
