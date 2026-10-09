from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"experiments"/"safeact_constraint_adapter.py"
spec=importlib.util.spec_from_file_location("safeact_constraint_adapter",MODULE)
assert spec and spec.loader
adapter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def test_supported_rule_becomes_true_constraint() -> None:
    value=adapter.project(
        {
            "case_id":"SAB-V1-X",
            "rule_execution_trace":[
                {
                    "rule_id":"R1",
                    "status":"SUPPORTED",
                    "predicate_result":"TRUE",
                    "reason":"SUPPORTED",
                    "management_effect":"permit_action",
                }
            ],
        },
        target_identity="resource:test",
        target_revision="r1",
    )
    predicate=value["predicates"][0]
    observation=value["observations"][predicate["id"]]
    assert predicate["role"]=="constraint"
    assert observation["status"]=="TRUE"
    assert "positive_authority" in observation
    assert value["semantic_boundary"]["provides_residual_necessity"] is False


def test_missing_rule_stays_unknown_without_negative_authority() -> None:
    value=adapter.project(
        {
            "case_id":"SAB-V0-X",
            "rule_execution_trace":[
                {
                    "rule_id":"R1",
                    "status":"MISSING",
                    "predicate_result":"FALSE",
                    "reason":"REQUIRED_RECORD_MISSING",
                    "management_effect":"permit_action",
                }
            ],
        },
        target_identity="resource:test",
        target_revision="r1",
    )
    predicate=value["predicates"][0]
    observation=value["observations"][predicate["id"]]
    assert observation["status"]=="UNKNOWN"
    assert "negative_authority" not in observation
