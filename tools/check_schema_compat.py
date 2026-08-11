"""Check JSON Schema backward compatibility between two versions.

Compares an old and new schema file and reports breaking changes:
- Removed properties
- Narrowed enum values
- Newly required fields
- Type changes

Exit code 0 = compatible, 1 = breaking changes found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _compare_schemas(
    old: dict,
    new: dict,
    path: str,
    breaking: list[str],
) -> None:
    """Recursively compare two schema nodes and collect breaking changes."""

    # --- Removed properties ---------------------------------------------------
    old_props = old.get("properties", {})
    new_props = new.get("properties", {})
    for key in old_props:
        if key not in new_props:
            breaking.append(f"REMOVED PROPERTY: {path}/properties/{key}")
        else:
            _compare_schemas(old_props[key], new_props[key], f"{path}/properties/{key}", breaking)

    # --- Narrowed enum values -------------------------------------------------
    old_enum = old.get("enum")
    new_enum = new.get("enum")
    if old_enum is not None and new_enum is not None:
        removed_values = set(str(v) for v in old_enum) - set(str(v) for v in new_enum)
        for val in sorted(removed_values):
            breaking.append(f"NARROWED ENUM: {path} removed value '{val}'")

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
        for i, (old_item, new_item) in enumerate(zip(old_list, new_list)):
            _compare_schemas(old_item, new_item, f"{path}/{combinator}[{i}]", breaking)

    # --- Recurse into conditional keywords (if/then/else) ---------------------
    for kw in ("if", "then", "else"):
        old_kw = old.get(kw)
        new_kw = new.get(kw)
        if isinstance(old_kw, dict) and isinstance(new_kw, dict):
            _compare_schemas(old_kw, new_kw, f"{path}/{kw}", breaking)


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

    breaking: list[str] = []
    _compare_schemas(old, new, "#", breaking)

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
