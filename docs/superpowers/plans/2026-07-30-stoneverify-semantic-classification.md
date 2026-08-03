# StoneVerify Semantic Difference Classification (WORK-VERIFY-009) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `classify_difference()`'s single `likelyCause` string (derived only from byte identity, tag-count equality, and a line diff) with a real semantic classifier: a named category grounded in `spec/svg-contract.md`'s element/attribute structure, an explicit equality level (byte/structural/semantic), and a confidence + basis for every classification — while keeping `likelyCause` present and unchanged for existing consumers.

**Architecture:** A new pure function, `classify_semantic(left: bytes, right: bytes) -> dict`, parses both SVG payloads with the stdlib `xml.etree.ElementTree`, walks them element-by-element in document order, and buckets every attribute/text difference it finds into one of 9 categories using an attribute-name lookup table grounded in `spec/svg-contract.md` (`d/cx/cy/r/x/y/points/transform` → geometry; `fill/stroke/stroke-width/font-*/class` → theme-style; `role/aria-*` → accessibility-metadata; element text content → label-text; everything else falls to `unknown-structural`). `classify_difference()` (existing, unchanged in its own logic) keeps producing `likelyCause`; a new call site in it also calls `classify_semantic()` and merges its output in as new keys (`category`, `equality`, `confidence`, `basis`), so nothing existing breaks.

**Tech Stack:** Python 3.9+ stdlib only (`xml.etree.ElementTree`, already-imported `difflib`/`re`) — no new runtime dependency.

## Global Constraints

- Python 3.9+ compatibility, `from __future__ import annotations` convention (already present in `tools/stonecharts_verify.py`), no `X | Y` in a runtime expression.
- No new runtime dependency. `xml.etree.ElementTree` is Python stdlib (no install needed).
- No comments unless they explain a non-obvious *why*.
- `likelyCause` (the existing field) must not change wording, must not be removed, and must not change for any currently-passing test. This work is purely additive to `classify_difference()`'s return dict.
- SVG documents compared here are always well-formed (produced by StoneCharts' own two certified renderers) — `ElementTree.fromstring()` is not expected to raise on real inputs. If a malformed/incomplete SVG is ever passed (e.g. `--demo-drift text` appends `<text>...</text>` *before* `</svg>`, which is well-formed), the classifier must catch `ET.ParseError` and fall back to `category="unknown-structural"`, `equality="unknown"`, `confidence="low"` rather than crashing StoneVerify.
- `spec/svg-contract.md`'s selector list (`.sc-chart-wrap`, `.sc-series`, `.sc-point`, `.sc-legend-item`, `.sc-crosshair`, `.sc-tooltip`) and `render.py`'s `_data_table()` (`role="img"` on the SVG root, a sibling `<table class="sc-visually-hidden">`) are the two sources of truth for which attributes mean what — do not invent an attribute-category mapping not grounded in one of these two files.
- Perceptual equality is explicitly out of scope (already documented as deferred in `REQ-VERIFY-005`) — do not add a *fifth* equality level for it.
- **Flagged spec tension, resolved here — re-open if you disagree:** `REQ-VERIFY-005` (already merged) says equality is "one of three levels" (byte/structural/semantic); `WORK-VERIFY-009`'s own acceptance text says "byte equal, structurally equal, semantically equal, **or none of those**" — a 4th outcome. These two already-shipped texts disagree about whether a genuine content change (geometry, label text) gets a real 4th value or must be forced into one of the 3. This plan resolves it by defining **`semantic` equality narrowly**: it holds only when geometry and text content are byte-for-byte identical between the two documents and *only* theme-style/accessibility-metadata attributes differ (i.e., the chart's data-bearing content is unchanged, only its presentation/metadata is). A genuine geometry or text difference therefore does NOT qualify as `semantic`, `structural`, or `byte` — it reports `"unknown"`, reusing the 4th enum value already shipped in `libs/python/stonecharts/verify/result.py`'s `_VALID_EQUALITY` and `spec/stoneverify-result.schema.json`'s `$defs.finding.equality` (both already merged, both already accept `unknown`). This overloads `"unknown"` to mean both "couldn't parse/classify" and "definitely not equal at any named tier" — a naming compromise made to avoid re-touching already-shipped, already-reviewed code for a 5th enum value. **If you'd rather have a clean 4th name (e.g. `"none"`) instead of overloading `"unknown"`, that requires editing `result.py`, `spec/stoneverify-result.schema.json`, and `REQ-VERIFY-005`'s acceptance criteria — say so before Task 1 starts, not after.**

## File Structure

```
tools/stonecharts_verify.py   # modified — new classify_semantic() function;
                                #   classify_difference() calls it and merges
                                #   the result into its existing return dict

libs/python/tests/test_stonecharts_verify.py   # modified — new tests for
                                                #   classify_semantic() and for
                                                #   classify_difference()'s merged output
```

No new files. `classify_semantic()` lives in `tools/stonecharts_verify.py` next to `classify_difference()` (same file, same concern — this is not a new subsystem the way Task 1 of the prior plan was).

---

### Task 1: Attribute-category lookup and geometry/theme/text classification

**Files:**
- Modify: `tools/stonecharts_verify.py` (add `classify_semantic()` near `classify_difference()`, i.e. before line 274)
- Test: `libs/python/tests/test_stonecharts_verify.py`

**Interfaces:**
- Produces: `classify_semantic(left: bytes, right: bytes) -> dict[str, Any]` returning `{"category": str, "equality": str, "confidence": str, "basis": list[str]}`. `category` is one of: `input-data`, `geometry`, `scale-domain`, `label-text`, `theme-style`, `accessibility-metadata`, `serialization-only`, `chart-type-capability`, `unknown-structural`. `equality` is one of `byte`, `structural`, `semantic`. `confidence` is one of `high`, `medium`, `low`.

- [ ] **Step 1: Write the failing tests**

Add to `libs/python/tests/test_stonecharts_verify.py`:

```python
from stonecharts_verify import classify_semantic


SVG_BASIC = (
    b'<svg class="sc-chart" role="img">'
    b'<g class="sc-series" data-series="0">'
    b'<path class="sc-series-line" data-series="0" d="M0,0 L10,10" stroke="#ff0000"/>'
    b'<circle class="sc-point" data-series="0" cx="10" cy="10" r="3.5"/>'
    b'</g></svg>'
)


def test_classify_semantic_byte_equal():
    result = classify_semantic(SVG_BASIC, SVG_BASIC)
    assert result["equality"] == "byte"
    assert result["category"] == "unknown-structural"  # no difference at all: no category applies
    assert result["confidence"] == "high"


def test_classify_semantic_geometry_change():
    # A geometry change is a real content change: it does NOT qualify as byte,
    # structural, or semantic equality, so it reports "unknown" (the already-shipped
    # 4th enum value from result.py/spec/stoneverify-result.schema.json), not "semantic" -
    # see this plan's Global Constraints note on the REQ-VERIFY-005/WORK-VERIFY-009 tension.
    changed = SVG_BASIC.replace(b'd="M0,0 L10,10"', b'd="M0,0 L20,20"')
    result = classify_semantic(SVG_BASIC, changed)
    assert result["category"] == "geometry"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "high"
    assert any("d" in b for b in result["basis"])


def test_classify_semantic_theme_change():
    # Theme-only differences don't change the chart's data-bearing content, so this
    # DOES qualify as "semantic" equality (same data, different presentation).
    changed = SVG_BASIC.replace(b'stroke="#ff0000"', b'stroke="#00ff00"')
    result = classify_semantic(SVG_BASIC, changed)
    assert result["category"] == "theme-style"
    assert result["equality"] == "semantic"
    assert result["confidence"] == "high"
    assert any("stroke" in b for b in result["basis"])


def test_classify_semantic_accessibility_change():
    # Same reasoning as theme: accessibility metadata isn't data-bearing content.
    changed = SVG_BASIC.replace(b'role="img"', b'role="figure"')
    result = classify_semantic(SVG_BASIC, changed)
    assert result["category"] == "accessibility-metadata"
    assert result["equality"] == "semantic"
    assert result["confidence"] == "high"


def test_classify_semantic_label_text_change():
    # Text content IS data-bearing (it's what a series/axis label says), so this is a
    # real content change like geometry, not "semantic" equality.
    left = b'<svg role="img"><text class="sc-tt-title">Jan</text></svg>'
    right = b'<svg role="img"><text class="sc-tt-title">Feb</text></svg>'
    result = classify_semantic(left, right)
    assert result["category"] == "label-text"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "high"


def test_classify_semantic_malformed_input_falls_back_safely():
    # Different malformed inputs, so the byte-equality fast path (checked before
    # parsing) does not short-circuit and the ET.ParseError fallback actually runs.
    result = classify_semantic(b"<svg><unterminated", b"<svg><also-unterminated")
    assert result["category"] == "unknown-structural"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "low"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -k classify_semantic -v`
Expected: `ImportError: cannot import name 'classify_semantic'`

- [ ] **Step 3: Write the minimal implementation**

Add near the top of `tools/stonecharts_verify.py` (after the existing imports, no new import beyond stdlib `xml.etree.ElementTree as ET` added to the import block):

```python
import xml.etree.ElementTree as ET
```

Add before `classify_difference()` (i.e. before line 274):

```python
_GEOMETRY_ATTRS = {"d", "cx", "cy", "r", "x", "y", "x1", "y1", "x2", "y2", "points", "transform", "width", "height"}
_THEME_ATTRS = {"fill", "stroke", "stroke-width", "stroke-dasharray", "opacity", "class", "style"}
_ACCESSIBILITY_ATTRS = {"role", "aria-hidden", "aria-label", "aria-labelledby", "aria-describedby", "scope"}


def _element_signature(elem: ET.Element) -> tuple[str, str | None]:
    return (elem.tag, elem.get("data-series"))


def _walk(elem: ET.Element) -> list[ET.Element]:
    result = [elem]
    for child in elem:
        result.extend(_walk(child))
    return result


def classify_semantic(left: bytes, right: bytes) -> dict[str, Any]:
    if left == right:
        return {"category": "unknown-structural", "equality": "byte", "confidence": "high", "basis": ["byte-identical"]}

    try:
        left_root = ET.fromstring(left)
        right_root = ET.fromstring(right)
    except ET.ParseError:
        return {"category": "unknown-structural", "equality": "unknown", "confidence": "low", "basis": ["one or both payloads did not parse as XML"]}

    left_elems = _walk(left_root)
    right_elems = _walk(right_root)

    if len(left_elems) != len(right_elems):
        return {
            "category": "chart-type-capability",
            "equality": "unknown",
            "confidence": "low",
            "basis": [f"element count differs: {len(left_elems)} vs {len(right_elems)}"],
        }

    geometry_hits: list[str] = []
    theme_hits: list[str] = []
    accessibility_hits: list[str] = []
    text_hits: list[str] = []
    other_attr_hits: list[str] = []

    for left_elem, right_elem in zip(left_elems, right_elems):
        left_attrs = left_elem.attrib
        right_attrs = right_elem.attrib
        all_keys = set(left_attrs) | set(right_attrs)
        for key in sorted(all_keys):
            if left_attrs.get(key) == right_attrs.get(key):
                continue
            basis_entry = f"{left_elem.tag}[{key}]: {left_attrs.get(key)!r} -> {right_attrs.get(key)!r}"
            if key in _GEOMETRY_ATTRS:
                geometry_hits.append(basis_entry)
            elif key in _THEME_ATTRS:
                theme_hits.append(basis_entry)
            elif key in _ACCESSIBILITY_ATTRS:
                accessibility_hits.append(basis_entry)
            else:
                other_attr_hits.append(basis_entry)
        left_text = (left_elem.text or "").strip()
        right_text = (right_elem.text or "").strip()
        if left_text != right_text:
            text_hits.append(f"{left_elem.tag} text: {left_text!r} -> {right_text!r}")

    # Priority order below is deliberate: geometry and text are data-bearing content,
    # so they take precedence over theme/accessibility even if multiple categories'
    # attributes changed at once. Equality mapping (see this plan's Global Constraints
    # note): geometry/text differences are real content changes -> "unknown" (not
    # byte/structural/semantic); theme/accessibility differences leave data-bearing
    # content unchanged -> "semantic".
    if geometry_hits:
        return {"category": "geometry", "equality": "unknown", "confidence": "high", "basis": geometry_hits}
    if text_hits:
        return {"category": "label-text", "equality": "unknown", "confidence": "high", "basis": text_hits}
    if accessibility_hits:
        return {"category": "accessibility-metadata", "equality": "semantic", "confidence": "high", "basis": accessibility_hits}
    if theme_hits:
        return {"category": "theme-style", "equality": "semantic", "confidence": "high", "basis": theme_hits}
    if other_attr_hits:
        return {"category": "unknown-structural", "equality": "unknown", "confidence": "medium", "basis": other_attr_hits}

    # Elements and every checked attribute/text match, but left != right at the byte level:
    # this is whitespace/attribute-ordering/serialization noise.
    return {"category": "serialization-only", "equality": "structural", "confidence": "high", "basis": ["no element, attribute, or text difference found; byte difference is serialization-only"]}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -k classify_semantic -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/stonecharts_verify.py libs/python/tests/test_stonecharts_verify.py
git commit -m "Add classify_semantic(): attribute-grounded difference categories (WORK-VERIFY-009)"
```

---

### Task 2: Serialization-only detection and the whitespace/ordering edge case

**Files:**
- Modify: `tools/stonecharts_verify.py` (`classify_semantic`, already added in Task 1)
- Test: `libs/python/tests/test_stonecharts_verify.py`

**Interfaces:**
- Consumes: `classify_semantic` from Task 1
- Produces: no new public interface — this task adds test coverage and, if the tests reveal a gap, a small fix to the serialization-only fallback path Task 1 already wrote.

- [ ] **Step 1: Write the failing test**

Add to `libs/python/tests/test_stonecharts_verify.py`:

```python
def test_classify_semantic_whitespace_only_is_serialization_only():
    left = b'<svg role="img"><g class="sc-series"><path d="M0,0 L1,1"/></g></svg>'
    right = b'<svg role="img"><g class="sc-series"><path d="M0,0 L1,1"/></g></svg>\n'
    result = classify_semantic(left, right)
    assert result["category"] == "serialization-only"
    assert result["equality"] == "structural"


def test_classify_semantic_attribute_ordering_is_serialization_only():
    left = b'<svg role="img" class="sc-chart"></svg>'
    right = b'<svg class="sc-chart" role="img"></svg>'
    result = classify_semantic(left, right)
    assert result["category"] == "serialization-only"
```

- [ ] **Step 2: Run the tests to verify they pass or fail**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -k "whitespace_only or attribute_ordering" -v`

`ElementTree` parses both documents into an identical attribute dict and identical tree regardless of source-text whitespace or attribute order, so both tests are expected to PASS immediately against Task 1's implementation with no code change — this task exists to prove that expectation with a real test, not to write new logic. If either test fails, that reveals a real gap in Task 1's implementation (e.g. `ET.tostring` round-tripping introduces some difference `_walk` doesn't see) — stop and report rather than patching around it blindly.

- [ ] **Step 3: Commit**

```bash
git add libs/python/tests/test_stonecharts_verify.py
git commit -m "Prove classify_semantic() correctly identifies serialization-only differences (WORK-VERIFY-009)"
```

---

### Task 3: Wire classify_semantic() into classify_difference() without breaking likelyCause

**Files:**
- Modify: `tools/stonecharts_verify.py:274-322` (`classify_difference`'s existing body and return statement)
- Test: `libs/python/tests/test_stonecharts_verify.py`

**Interfaces:**
- Consumes: `classify_semantic` (Tasks 1-2)
- Produces: `classify_difference()`'s return dict gains 4 new keys (`category`, `equality`, `confidence`, `basis`) alongside every key it already has (`equal`, `leftBytes`, `rightBytes`, `structural`, `firstDifference`, `lineDiff`, `likelyCause`).

- [ ] **Step 1: Write the failing tests**

Add to `libs/python/tests/test_stonecharts_verify.py`:

```python
from stonecharts_verify import classify_difference


def test_classify_difference_includes_semantic_fields():
    left = b'<svg role="img"><g class="sc-series"><path d="M0,0 L1,1" stroke="#111"/></g></svg>'
    right = b'<svg role="img"><g class="sc-series"><path d="M0,0 L2,2" stroke="#111"/></g></svg>'
    result = classify_difference(left, right, "left.svg", "right.svg")
    # existing fields untouched
    assert result["equal"] is False
    assert "likelyCause" in result
    assert "structural" in result
    # new fields present
    assert result["category"] == "geometry"
    assert result["equality"] in ("structural", "semantic")
    assert result["confidence"] == "high"
    assert isinstance(result["basis"], list) and result["basis"]


def test_classify_difference_equal_case_includes_semantic_fields():
    svg = b'<svg role="img"></svg>'
    result = classify_difference(svg, svg, "left.svg", "right.svg")
    assert result["equal"] is True
    assert result["likelyCause"] == "none"
    assert result["equality"] == "byte"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -k classify_difference_includes -v`
Expected: `KeyError: 'category'`

- [ ] **Step 3: Write the minimal implementation**

In `classify_difference()`, locate the existing `return {` statement (currently the function's last statement, lines ~310-322):

```python
    return {
        "equal": equal,
        "leftBytes": len(left),
        "rightBytes": len(right),
        "structural": {
            "equalTagInventory": structural_equal,
            "leftTagCounts": left_tags,
            "rightTagCounts": right_tags,
        },
        "firstDifference": None if equal else first_difference(left, right),
        "lineDiff": line_diff,
        "likelyCause": likely_cause,
    }
```

becomes:

```python
    semantic = classify_semantic(left, right)
    return {
        "equal": equal,
        "leftBytes": len(left),
        "rightBytes": len(right),
        "structural": {
            "equalTagInventory": structural_equal,
            "leftTagCounts": left_tags,
            "rightTagCounts": right_tags,
        },
        "firstDifference": None if equal else first_difference(left, right),
        "lineDiff": line_diff,
        "likelyCause": likely_cause,
        "category": semantic["category"],
        "equality": semantic["equality"],
        "confidence": semantic["confidence"],
        "basis": semantic["basis"],
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -v`
Expected: every test PASSES, including every pre-existing test in the file (confirms `likelyCause` and every other existing key is unaffected)

- [ ] **Step 5: Commit**

```bash
git add tools/stonecharts_verify.py libs/python/tests/test_stonecharts_verify.py
git commit -m "Wire classify_semantic() into classify_difference()'s return value (WORK-VERIFY-009)"
```

---

### Task 4: End-to-end proof via demo-drift, and the unknown-structural low-confidence path

**Files:**
- Test: `libs/python/tests/test_stonecharts_verify.py`
- Verify only: a live `--demo-drift text` and `--demo-drift attribute` CLI run

**Interfaces:**
- Consumes: everything from Tasks 1-3
- Produces: no new interface — this task is the acceptance-criteria proof named in `WORK-VERIFY-009`'s own `verification` field.

- [ ] **Step 1: Write the end-to-end tests**

Add to `libs/python/tests/test_stonecharts_verify.py` (following whatever existing convention the file already uses for invoking the CLI as a subprocess — check the pattern the prior plan's Task 4 established, at the top of this same file, before writing new subprocess calls):

```python
def test_demo_drift_text_reports_semantic_fields(tmp_path):
    spec_path = Path("charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [sys.executable, "tools/stonecharts_verify.py", str(spec_path), "--runtime", "python", "--runtime", "go", "--demo-drift", "text", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
    )
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    pair = comparison["pairs"][0]
    assert pair["category"] in ("label-text", "unknown-structural")
    assert pair["equality"] in ("structural", "semantic", "unknown")
    assert pair["confidence"] in ("high", "medium", "low")
    assert pair["basis"]


def test_demo_drift_attribute_reports_accessibility_category(tmp_path):
    spec_path = Path("charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [sys.executable, "tools/stonecharts_verify.py", str(spec_path), "--runtime", "python", "--runtime", "go", "--demo-drift", "attribute", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
    )
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    pair = comparison["pairs"][0]
    # --demo-drift attribute changes role="img" to role="figure" (apply_demo_drift, existing code)
    assert pair["category"] == "accessibility-metadata"
    assert pair["confidence"] == "high"
```

Adjust the `cwd=`/path-resolution expressions to match whatever convention the file's existing tests already use (established in the prior plan's Task 4) — do not introduce a second convention.

- [ ] **Step 2: Run the tests**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -k demo_drift -v`
Expected: both PASS. If `test_demo_drift_attribute_reports_accessibility_category` fails because the actual category differs, read `apply_demo_drift()`'s `"attribute"` mode (it replaces `role="img"` with `role="figure"`) and confirm `classify_semantic()` actually sees that change — do not weaken the assertion to make it pass; if it's genuinely wrong, that's a real bug in Task 1-3's implementation to fix, not a test to soften.

- [ ] **Step 3: Run the full existing test suite**

Run: `python -m pytest libs/python/tests -q`
Expected: all tests pass (was 72 before this plan)

Run: `cd libs/go && go test ./...`
Expected: unaffected (this plan touches no Go source)

- [ ] **Step 4: Commit**

```bash
git add libs/python/tests/test_stonecharts_verify.py
git commit -m "Prove classify_semantic() end-to-end via demo-drift text and attribute modes (WORK-VERIFY-009)"
```

## What this plan deliberately does not do

- **Does not touch `scale-domain`, `input-data`, or `chart-type-capability` categories with real detection logic beyond the coarse element-count-mismatch fallback in Task 1.** Distinguishing "the y-axis domain changed because a data value changed" (`scale-domain`) from "a data value changed but the domain didn't" (`input-data`) requires understanding the chart's *rendered scale*, not just its SVG attributes — that needs access to the chart spec, which `classify_difference()` doesn't currently receive. This is a real gap; flagging it rather than faking a heuristic. A follow-on task should decide whether to thread the spec through or accept these two categories staying coarse.
- **Does not change `WORK-VERIFY-014A`'s result envelope** — the 4 new fields land inside `classify_difference()`'s existing dict shape (used inside `compare_outputs()`'s `pairs` array and `compare_evidence_bundles()`'s `runtimes` array), not as new top-level `manifest.json`/`comparison.json` keys. `WORK-VERIFY-014A`'s pin tests (`test_manifest_only_adds_schema_version_environment_and_evidence`, `test_comparison_json_only_adds_schema_version`) should be re-run as part of this plan's Task 4 regression pass to confirm they still pass unchanged — the new fields are nested inside `pairs`, not new top-level keys, so they shouldn't trip those pins, but that assumption should be verified, not assumed.
