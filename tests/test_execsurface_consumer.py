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
        "collection_health": {"state": "complete", "warning_codes": []},
        "unsupported_capabilities": [],
        "effects": [],
    }


def test_matching_effect_supports_true():
    report = base_report()
    report["effects"] = [{
        "proposition": "file_fd_write_effect_observed",
        "actor": "/bin/test",
        "target": "/tmp/marker",
        "guarantees": {},
    }]
    result = consumer.target_write_observation(report, "/tmp/marker")
    assert result["status"] == "TRUE"


def test_incomplete_collection_is_unknown():
    report = base_report()
    report["collection_health"]["state"] = "incomplete_loss"
    result = consumer.target_write_observation(report, "/tmp/marker")
    assert result["status"] == "UNKNOWN"


def test_unsupported_capability_is_unknown():
    report = base_report()
    report["unsupported_capabilities"] = ["fd_read_write_effect"]
    result = consumer.target_write_observation(report, "/tmp/marker")
    assert result["status"] == "UNKNOWN"


def test_absence_is_not_silently_false():
    result = consumer.target_write_observation(base_report(), "/tmp/marker")
    assert result["status"] == "UNKNOWN"
