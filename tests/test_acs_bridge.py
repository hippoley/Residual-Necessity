from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "acs_bridge.py"

spec = importlib.util.spec_from_file_location("acs_bridge", MODULE)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def invocation(status: str):
    return {
        "input": {
            "annotations": {
                "residual_necessity": {"status": status}
            }
        }
    }


def test_true_allows():
    verdict = bridge.NecessityPolicy().evaluate(invocation("TRUE"))
    assert verdict["decision"] == "allow"


def test_false_denies_without_approval():
    verdict = bridge.NecessityPolicy().evaluate(invocation("FALSE"))
    assert verdict["decision"] == "deny"
    assert "approval" not in verdict


def test_unknown_denies_with_approval():
    verdict = bridge.NecessityPolicy().evaluate(invocation("UNKNOWN"))
    assert verdict["decision"] == "deny"
    assert verdict["approval"]["kind"] == "residual_necessity_review"


def test_conflicted_and_stale_require_review():
    policy = bridge.NecessityPolicy()
    for status in ("CONFLICTED", "STALE"):
        verdict = policy.evaluate(invocation(status))
        assert verdict["decision"] == "deny"
        assert "approval" in verdict


def test_annotator_rejects_invalid_provider_status():
    annotator = bridge.NecessityAnnotator(lambda _: {"status": "MAYBE"})
    try:
        annotator.dispatch("residual_necessity", {}, {})
    except ValueError as exc:
        assert "invalid status" in str(exc)
    else:
        raise AssertionError("invalid provider status must fail")
