from __future__ import annotations

import pytest

from stonecharts.verify.result import (
    SCHEMA_VERSION,
    build_finding,
    build_verification_result,
    capture_environment,
    digest,
    sha256_digest,
)


def test_digest_shape():
    d = digest("sha-256", "abc123")
    assert d == {"algorithm": "sha-256", "value": "abc123"}


def test_sha256_digest_is_digest_with_sha256_algorithm():
    d = sha256_digest("deadbeef")
    assert d == {"algorithm": "sha-256", "value": "deadbeef"}


def test_capture_environment_has_required_keys():
    env = capture_environment(stonecharts_version="0.0.0.4", stoneverify_version="1.0.0")
    for key in ("os", "arch", "pythonVersion", "stonechartsVersion", "stoneverifyVersion", "schemaVersion", "locale", "timezone"):
        assert key in env, f"missing {key}"
    assert env["schemaVersion"] == SCHEMA_VERSION
    assert env["goVersion"] is None


def test_capture_environment_records_supplied_go_version():
    env = capture_environment(stonecharts_version="0.0.0.4", stoneverify_version="1.0.0", go_version="go1.26")
    assert env["goVersion"] == "go1.26"


def test_capture_environment_excludes_font_and_toolchain_fields():
    env = capture_environment(stonecharts_version="0.0.0.4", stoneverify_version="1.0.0")
    for excluded in ("font", "fonts", "toolchain", "toolchainId"):
        assert excluded not in env


def test_build_finding_default_shape():
    f = build_finding(code="VERIFY.SCALE.DOMAIN_CHANGED", category="scale-domain", message="y-axis domain changed")
    assert f == {
        "code": "VERIFY.SCALE.DOMAIN_CHANGED",
        "category": "scale-domain",
        "message": "y-axis domain changed",
        "equality": "unknown",
        "confidence": "low",
        "basis": [],
    }


def test_build_finding_accepts_equality_confidence_basis():
    f = build_finding(
        code="VERIFY.SERIALIZATION.WHITESPACE",
        category="serialization-only",
        message="whitespace-only difference",
        equality="structural",
        confidence="high",
        basis=["tag inventory equal", "attribute values equal"],
    )
    assert f["equality"] == "structural"
    assert f["confidence"] == "high"
    assert f["basis"] == ["tag inventory equal", "attribute values equal"]


@pytest.mark.parametrize("bad_equality", ["byte-ish", "", "SEMANTIC", None])
def test_build_finding_rejects_unknown_equality(bad_equality):
    with pytest.raises(ValueError):
        build_finding(code="X.Y", category="theme-style", message="m", equality=bad_equality)


@pytest.mark.parametrize("bad_confidence", ["certain", "", "HIGH", None])
def test_build_finding_rejects_unknown_confidence(bad_confidence):
    with pytest.raises(ValueError):
        build_finding(code="X.Y", category="theme-style", message="m", confidence=bad_confidence)


def test_build_verification_result_has_canonical_envelope_shape():
    finding = build_finding(
        code="VERIFY.LABEL.TEXT_CHANGED",
        category="label-text",
        message="label changed",
        equality="unknown",
        confidence="high",
        basis=["text node changed"],
    )
    result = build_verification_result(
        status="fail",
        comparison_mode="cross-runtime",
        baseline=None,
        candidate={"runtimes": ["python", "go"]},
        inputs={"specSha256": "abc"},
        runtime_coverage={"shared": ["python", "go"], "onlyLeft": [], "onlyRight": []},
        findings=[finding],
        evidence={"inputSpec": {"algorithm": "sha-256", "value": "abc"}},
        environment={"schemaVersion": SCHEMA_VERSION},
    )

    assert result["schemaVersion"] == SCHEMA_VERSION
    assert result["comparisonMode"] == "cross-runtime"
    assert result["findings"] == [finding]
    assert result["evidence"]["inputSpec"]["algorithm"] == "sha-256"


@pytest.mark.parametrize("bad_status", ["", "passed", "error"])
def test_build_verification_result_rejects_unknown_status(bad_status):
    with pytest.raises(ValueError):
        build_verification_result(status=bad_status, comparison_mode="cross-runtime")


@pytest.mark.parametrize("bad_mode", ["", "runtime", "baseline-compare"])
def test_build_verification_result_rejects_unknown_mode(bad_mode):
    with pytest.raises(ValueError):
        build_verification_result(status="pass", comparison_mode=bad_mode)
