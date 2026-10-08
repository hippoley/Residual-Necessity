from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "execsurface_consumer.py"
spec = importlib.util.spec_from_file_location("execsurface_consumer", MODULE)
assert spec and spec.loader
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


def base_report():
    return {
        "schema_version": 1,
        "report_kind": "typed_observation_evidence",
        "stability": "experimental",
        "backend": {
            "profile": "linux-ptrace-metadata-v2",
            "implementation_version": "test",
            "platform": "linux",
            "architecture": "x86_64",
            "privacy_profile": "metadata-only-v1",
        },
        "collection_health": {"state": "complete", "warning_codes": []},
        "unsupported_capabilities": [],
        "effects": [],
        "limitations": [],
        "does_not_assert": [
            "policy_verdict",
            "vulnerability_free",
            "exact_transferred_byte_count",
            "file_contents",
            "before_after_state_roots",
            "custody",
            "trusted_time",
            "signature_as_behavioral_authority",
            "causal_source_code_provenance",
        ],
        "raw_observation": {
            "schema_version": 2,
            "backend": {
                "name": "linux-ptrace-metadata-v2",
                "platform": "linux",
                "architecture": "x86_64",
                "capabilities": [],
                "limitations": [],
            },
            "complete": True,
            "outcome": {"exit_code": 0, "signal": None},
            "events": [],
            "warnings": [],
        },
    }


def test_matching_effect_supports_true():
    report = base_report()
    report["effects"] = [{
        "proposition": "file_fd_write_effect_observed",
        "actor": "/bin/test",
        "target": "/tmp/marker",
        "guarantees": {},
    }]
    result = consumer.target_write_observation(
        report,
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    assert result["status"] == "TRUE"
    authority = result["positive_authority"]
    assert authority["scope"]["predicate_id"] == "write_effect_exists"
    assert authority["scope"]["target_identity"] == "resource:/tmp/marker"
    assert authority["scope"]["target_revision"] == "r1"


def test_incomplete_collection_is_unknown():
    report = base_report()
    report["collection_health"]["state"] = "incomplete_loss"
    report["collection_health"]["warning_codes"] = ["loss"]
    report["raw_observation"]["complete"] = False
    report["raw_observation"]["warnings"] = [{"code": "loss", "tid": None, "message": ""}]
    result = consumer.target_write_observation(
        report,
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    assert result["status"] == "UNKNOWN"


def test_unsupported_capability_is_unknown():
    report = base_report()
    report["unsupported_capabilities"] = ["fd_read_write_effect"]
    result = consumer.target_write_observation(
        report,
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    assert result["status"] == "UNKNOWN"


def test_absence_is_not_silently_false():
    result = consumer.target_write_observation(
        base_report(),
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    assert result["status"] == "UNKNOWN"


def test_contradictory_completeness_fails_closed():
    report = base_report()
    report["raw_observation"]["complete"] = False
    try:
        consumer.target_write_observation(
        report,
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    except ValueError as exc:
        assert "contradicts" in str(exc)
    else:
        raise AssertionError("contradictory evidence must fail")


def test_warning_code_mismatch_fails_closed():
    report = base_report()
    report["collection_health"]["state"] = "incomplete_loss"
    report["collection_health"]["warning_codes"] = ["loss"]
    report["raw_observation"]["complete"] = False
    report["raw_observation"]["warnings"] = [{"code": "different", "tid": None, "message": ""}]
    try:
        consumer.target_write_observation(
        report,
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    except ValueError as exc:
        assert "warning codes disagree" in str(exc)
    else:
        raise AssertionError("warning mismatch must fail")


def test_backend_mismatch_fails_closed():
    report = base_report()
    report["raw_observation"]["backend"]["name"] = "other"
    try:
        consumer.target_write_observation(
        report,
        "/tmp/marker",
        predicate_id="write_effect_exists",
        target_identity="resource:/tmp/marker",
        target_revision="r1",
    )
    except ValueError as exc:
        assert "backend mismatch" in str(exc)
    else:
        raise AssertionError("backend mismatch must fail")
