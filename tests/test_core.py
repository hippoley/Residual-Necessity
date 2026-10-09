from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_module("residual_gate", ROOT / "src" / "gate.py")
metrics = load_module("residual_eval", ROOT / "src" / "eval.py")


def base_receipt() -> dict:
    return {
        "schema_version": "0.2",
        "intervention": {
            "id": "fix-payment",
            "kind": "modify_state",
            "description": "repair residual payment violation",
            "justified_by": ["violation_exists"],
        },
        "target": {"identity": "service:payments", "revision": "r1"},
        "predicates": [
            {"id": "violation_exists", "required": True, "kind": "reality"},
            {"id": "target_is_current", "required": True, "kind": "freshness"},
        ],
        "observations": {
            "violation_exists": {
                "status": "TRUE",
                "positive_authority": {
                    "scope": {
                        "predicate_id": "violation_exists",
                        "target_identity": "service:payments",
                        "target_revision": "r1",
                    },
                    "basis": "authoritative_probe",
                    "evidence_ref": "sha256:violation",
                },
            },
            "target_is_current": {
                "status": "TRUE",
                "positive_authority": {
                    "scope": {
                        "predicate_id": "target_is_current",
                        "target_identity": "service:payments",
                        "target_revision": "r1",
                    },
                    "basis": "revision_identity",
                    "evidence_ref": "sha256:r1",
                },
            },
        },
    }


def negative_authority(predicate_id: str, target: str = "service:payments", revision: str = "r1") -> dict:
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": target,
            "target_revision": revision,
        },
        "basis": "authoritative_query",
        "evidence_ref": "sha256:negative",
    }


def test_partial_fix_still_acts_on_residual_violation() -> None:
    receipt = gate.load(ROOT / "examples" / "residual-act.json")
    assert receipt["observations"]["historical_failure_still_reproduces"]["status"] == "FALSE"
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "ACT"


def test_missing_required_evidence_never_defaults_to_act() -> None:
    receipt = gate.load(ROOT / "examples" / "residual-act.json")
    del receipt["observations"]["residual_failure_exists"]
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_true_without_positive_authority_does_not_act() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"].pop("positive_authority")
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_positive_authority_for_wrong_target_does_not_act() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"]["positive_authority"]["scope"]["target_identity"] = "service:other"
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_positive_authority_for_wrong_revision_does_not_act() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"]["positive_authority"]["scope"]["target_revision"] = "r0"
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_intervention_must_name_current_reality_justification() -> None:
    receipt = base_receipt()
    receipt["intervention"]["justified_by"] = ["target_is_current"]
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_unknown_justification_predicate_does_not_act() -> None:
    receipt = base_receipt()
    receipt["intervention"]["justified_by"] = ["missing_predicate"]
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_false_without_negative_authority_investigates() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"] = {"status": "FALSE", "source": "observer"}
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_false_reality_with_scoped_negative_authority_abstains() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"] = {
        "status": "FALSE",
        "source": "authoritative_check",
        "negative_authority": negative_authority("violation_exists"),
    }
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "ABSTAIN"


def test_negative_authority_for_wrong_target_does_not_abstain() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"] = {
        "status": "FALSE",
        "negative_authority": negative_authority("violation_exists", target="service:other"),
    }
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_negative_authority_for_wrong_revision_does_not_abstain() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"] = {
        "status": "FALSE",
        "negative_authority": negative_authority("violation_exists", revision="r0"),
    }
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_false_freshness_investigates_instead_of_abstaining() -> None:
    receipt = base_receipt()
    receipt["observations"]["target_is_current"] = {
        "status": "FALSE",
        "negative_authority": negative_authority("target_is_current"),
    }
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_human_only_predicate_escalates() -> None:
    receipt = base_receipt()
    receipt["predicates"].append(
        {"id": "human_confirmation", "required": True, "kind": "reality", "human_only": True}
    )
    receipt["observations"]["human_confirmation"] = {"status": "UNKNOWN"}
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "ESCALATE"


def test_duplicate_predicate_ids_fail_closed() -> None:
    receipt = base_receipt()
    receipt["predicates"].append(copy.deepcopy(receipt["predicates"][0]))
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_metrics_penalize_both_failure_directions() -> None:
    result = metrics.evaluate([
        {"expected": "ABSTAIN", "actual": "ACT"},
        {"expected": "ACT", "actual": "ABSTAIN"},
    ])
    assert result["unnecessary_intervention_rate"] == 1.0
    assert result["false_abstention_rate"] == 1.0


def test_investigate_does_not_count_as_success() -> None:
    result = metrics.evaluate([
        {"expected": "ABSTAIN", "actual": "INVESTIGATE"},
        {"expected": "ACT", "actual": "ACT"},
    ])
    assert result["accuracy"] == 0.5


def test_paired_accuracy_uses_only_complete_pairs() -> None:
    result = metrics.evaluate([
        {"pair_id": "p1", "expected": "ACT", "actual": "ACT"},
        {"pair_id": "p1", "expected": "ABSTAIN", "actual": "ABSTAIN"},
        {"pair_id": "incomplete", "expected": "ACT", "actual": "ACT"},
    ])
    assert result["pair_count"] == 2
    assert result["complete_pair_count"] == 1
    assert result["paired_accuracy"] == 1.0


def test_duplicate_pair_member_is_rejected() -> None:
    try:
        metrics.evaluate([
            {"pair_id": "p1", "expected": "ACT", "actual": "ACT"},
            {"pair_id": "p1", "expected": "ACT", "actual": "ACT"},
        ])
    except ValueError as exc:
        assert "duplicate ACT member" in str(exc)
    else:
        raise AssertionError("duplicate pair members must fail")


def test_missing_target_revision_investigates() -> None:
    receipt = base_receipt()
    receipt["target"].pop("revision")
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_false_scope_investigates_instead_of_abstaining() -> None:
    receipt = base_receipt()
    receipt["predicates"].append(
        {"id": "scope_is_valid", "required": True, "kind": "scope"}
    )
    receipt["observations"]["scope_is_valid"] = {
        "status": "FALSE",
        "negative_authority": negative_authority("scope_is_valid"),
    }
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_unknown_predicate_field_fails_closed_at_runtime() -> None:
    receipt = base_receipt()
    receipt["predicates"][0]["human_ony"] = True
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_unknown_observation_field_fails_closed_at_runtime() -> None:
    receipt = base_receipt()
    receipt["observations"]["violation_exists"]["positive_authorit"] = (
        receipt["observations"]["violation_exists"]["positive_authority"]
    )
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_unknown_top_level_field_fails_closed_at_runtime() -> None:
    receipt = base_receipt()
    receipt["metadata"] = {"unexpected": True}
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_investigate_on_required_action_counts_as_false_abstention() -> None:
    result = metrics.evaluate([
        {"expected": "ACT", "actual": "INVESTIGATE"},
    ])
    assert result["false_abstention_rate"] == 1.0
    assert result["act_recall"] == 0.0


def test_escalate_on_required_action_counts_as_false_abstention() -> None:
    result = metrics.evaluate([
        {"expected": "ACT", "actual": "ESCALATE"},
    ])
    assert result["false_abstention_rate"] == 1.0
    assert result["act_recall"] == 0.0


def test_act_recall_is_one_when_required_actions_execute() -> None:
    result = metrics.evaluate([
        {"expected": "ACT", "actual": "ACT"},
        {"expected": "ABSTAIN", "actual": "ABSTAIN"},
    ])
    assert result["act_recall"] == 1.0
