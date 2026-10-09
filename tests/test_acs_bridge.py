from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "acs_bridge.py"

spec = importlib.util.spec_from_file_location("acs_bridge", MODULE)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def authority(predicate_id: str, target: str = "service:payments", revision: str = "r1"):
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": target,
            "target_revision": revision,
        },
        "basis": "unit_test",
        "evidence_ref": f"test:{predicate_id}",
    }


def receipt(status: str = "TRUE"):
    observation = {"status": status}
    if status == "TRUE":
        observation["positive_authority"] = authority("violation_exists")
    elif status == "FALSE":
        observation["negative_authority"] = authority("violation_exists")

    return {
        "schema_version": "0.2",
        "intervention": {
            "id": "repair",
            "kind": "modify_state",
            "description": "repair payments",
            "justified_by": ["violation_exists"],
        },
        "target": {"identity": "service:payments", "revision": "r1"},
        "predicates": [
            {"id": "violation_exists", "required": True, "kind": "reality"},
        ],
        "observations": {"violation_exists": observation},
    }


def annotation_for(status: str):
    annotator = bridge.NecessityAnnotator(lambda _: receipt(status))
    return annotator.dispatch("residual_necessity", {}, {})


def invocation(annotation: dict):
    return {"input": {"annotations": {"residual_necessity": annotation}}}


def test_act_allows():
    annotation = annotation_for("TRUE")
    assert annotation["verdict"] == "ACT"
    verdict = bridge.NecessityPolicy().evaluate(invocation(annotation))
    assert verdict["decision"] == "allow"
    assert verdict["evidence"]["artefact"].startswith("sha256:")


def test_abstain_denies():
    annotation = annotation_for("FALSE")
    assert annotation["verdict"] == "ABSTAIN"
    verdict = bridge.NecessityPolicy().evaluate(invocation(annotation))
    assert verdict["decision"] == "deny"


def test_unknown_escalates():
    annotation = annotation_for("UNKNOWN")
    assert annotation["verdict"] == "INVESTIGATE"
    verdict = bridge.NecessityPolicy().evaluate(invocation(annotation))
    assert verdict["decision"] == "escalate"


def test_wrong_target_true_cannot_bypass_gate():
    bad = receipt("TRUE")
    bad["observations"]["violation_exists"]["positive_authority"]["scope"]["target_identity"] = "service:other"
    annotator = bridge.NecessityAnnotator(lambda _: bad)
    annotation = annotator.dispatch("residual_necessity", {}, {})
    assert annotation["verdict"] == "INVESTIGATE"
    verdict = bridge.NecessityPolicy().evaluate(invocation(annotation))
    assert verdict["decision"] == "escalate"


def test_provider_must_return_receipt_object():
    annotator = bridge.NecessityAnnotator(lambda _: "not-a-receipt")
    try:
        annotator.dispatch("residual_necessity", {}, {})
    except ValueError as exc:
        assert "receipt object" in str(exc)
    else:
        raise AssertionError("invalid provider output must fail")
