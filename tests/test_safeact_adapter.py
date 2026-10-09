from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "safeact_adapter",
    ROOT / "experiments" / "safeact_adapter.py",
)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

gate_spec = importlib.util.spec_from_file_location(
    "residual_gate_safeact_test",
    ROOT / "src" / "gate.py",
)
assert gate_spec and gate_spec.loader
gate = importlib.util.module_from_spec(gate_spec)
gate_spec.loader.exec_module(gate)


def base_receipt() -> dict:
    return {
        "schema_version": "0.3",
        "intervention": {
            "id": "repair",
            "kind": "modify_state",
            "description": "repair only while a residual violation exists",
            "justified_by": ["residual_violation_exists"],
        },
        "target": {"identity": "resource:test", "revision": "r1"},
        "predicates": [
            {
                "id": "residual_violation_exists",
                "required": True,
                "kind": "reality",
                "role": "necessity",
            }
        ],
        "observations": {
            "residual_violation_exists": {
                "status": "TRUE",
                "positive_authority": {
                    "scope": {
                        "predicate_id": "residual_violation_exists",
                        "target_identity": "resource:test",
                        "target_revision": "r1",
                    },
                    "basis": "test",
                    "evidence_ref": "sha256:residual",
                },
            }
        },
    }


def safeact_materialized(status: str, result: str) -> dict:
    return {
        "case_id": "SAB-TEST-001",
        "rule_execution_trace": [
            {
                "rule_id": "RULE-1",
                "status": status,
                "predicate_result": result,
                "reason": "test",
                "management_effect": "permit_action",
            }
        ],
    }


def test_supported_safeact_rule_becomes_true_constraint_only() -> None:
    fragment = adapter.constraint_fragment(
        safeact_materialized("SUPPORTED", "TRUE"),
        target_identity="resource:test",
        target_revision="r1",
    )
    assert fragment["predicates"][0]["role"] == "constraint"
    obs = next(iter(fragment["observations"].values()))
    assert obs["status"] == "TRUE"
    assert "positive_authority" in obs


def test_missing_safeact_rule_becomes_false_constraint_only() -> None:
    fragment = adapter.constraint_fragment(
        safeact_materialized("MISSING", "FALSE"),
        target_identity="resource:test",
        target_revision="r1",
    )
    assert fragment["predicates"][0]["role"] == "constraint"
    obs = next(iter(fragment["observations"].values()))
    assert obs["status"] == "FALSE"
    assert "negative_authority" in obs


def test_true_safeact_constraint_does_not_replace_necessity() -> None:
    fragment = adapter.constraint_fragment(
        safeact_materialized("SUPPORTED", "TRUE"),
        target_identity="resource:test",
        target_revision="r1",
    )
    receipt = adapter.merge_constraints(base_receipt(), fragment)
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "ACT"

    support_pid = fragment["predicates"][0]["id"]
    receipt["intervention"]["justified_by"] = [support_pid]
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_false_safeact_constraint_does_not_disprove_necessity() -> None:
    fragment = adapter.constraint_fragment(
        safeact_materialized("MISSING", "FALSE"),
        target_identity="resource:test",
        target_revision="r1",
    )
    receipt = adapter.merge_constraints(base_receipt(), fragment)
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_adapter_refuses_necessity_role_in_external_fragment() -> None:
    fragment = adapter.constraint_fragment(
        safeact_materialized("SUPPORTED", "TRUE"),
        target_identity="resource:test",
        target_revision="r1",
    )
    fragment["predicates"][0]["role"] = "necessity"
    try:
        adapter.merge_constraints(base_receipt(), fragment)
    except ValueError as exc:
        assert "constraint predicates only" in str(exc)
    else:
        raise AssertionError("SafeAct adapter must never inject necessity predicates")
