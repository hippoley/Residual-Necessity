from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"audit"/"impact.py"
VALIDATOR=ROOT/"audit"/"validate_horizontal_matrix.py"
spec=importlib.util.spec_from_file_location("horizontal_impact",MODULE)
assert spec and spec.loader
impact=importlib.util.module_from_spec(spec)
spec.loader.exec_module(impact)

validator_spec=importlib.util.spec_from_file_location("horizontal_validator",VALIDATOR)
assert validator_spec and validator_spec.loader
validator=importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)

def test_core_semantic_change_expands_to_dependent_integrations() -> None:
    result=impact.impacted(["US-01"])
    assert "US-01" in result
    assert "US-18" in result
    assert "US-19" in result

def test_gold_firewall_change_retests_reality_gate() -> None:
    result=impact.impacted(["US-25"])
    assert "US-26" in result
    assert "US-27" in result
    assert "US-28" in result
    assert "US-37" in result


def test_current_horizontal_matrix_and_story_ledger_are_consistent() -> None:
    data=impact.load()
    assert validator.validate(data) == []


def test_dependency_cycle_is_detected() -> None:
    stories=[
        {"id":"US-1","dependencies":["US-2"]},
        {"id":"US-2","dependencies":["US-1"]},
    ]
    cycle=validator._dependency_cycle(stories)
    assert cycle is not None
    assert cycle[0] == cycle[-1]


def test_verified_closed_requires_dependencies_verified_closed() -> None:
    dims = {
        "functional": {"status": "verified", "evidence": "x", "reason": None},
        "state": {"status": "verified", "evidence": "x", "reason": None},
        "integration": {"status": "verified", "evidence": "x", "reason": None},
        "security_correctness": {"status": "verified", "evidence": "x", "reason": None},
        "performance_scalability": {
            "status": "not_applicable",
            "evidence": None,
            "reason": "not needed",
        },
        "maintainability": {"status": "verified", "evidence": "x", "reason": None},
        "observability_traceability": {"status": "verified", "evidence": "x", "reason": None},
        "testability": {"status": "verified", "evidence": "x", "reason": None},
        "user_value": {"status": "verified", "evidence": "x", "reason": None},
        "external_compatibility": {
            "status": "not_applicable",
            "evidence": None,
            "reason": "not needed",
        },
    }
    stories = [
        {
            "id": "US-A",
            "vertical_status": "closed",
            "dependencies": ["US-B"],
            "dimensions": dims,
        },
        {
            "id": "US-B",
            "vertical_status": "partial",
            "dependencies": [],
            "dimensions": dims,
        },
    ]
    closures = validator._dependency_aware_closures(stories)
    assert closures["US-B"] == "partial"
    assert closures["US-A"] == "partial"
