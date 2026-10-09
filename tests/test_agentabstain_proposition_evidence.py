from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "proposition_evidence.py"

spec = importlib.util.spec_from_file_location("agentabstain_proposition_evidence", MODULE)
assert spec and spec.loader
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


def test_unbound_verify_can_never_become_authoritative() -> None:
    result = provider.classify({
        "probed": True,
        "binding_complete": False,
        "tool_kind": "verify",
        "success": True,
        "result": {"verified": True},
    })
    assert result == {
        "status": "UNKNOWN",
        "reason": "incomplete_argument_binding",
    }
    assert provider.permits_decision(result["status"]) is False


def test_lookup_success_is_not_proposition_authority() -> None:
    result = provider.classify({
        "probed": True,
        "binding_complete": True,
        "tool_kind": "lookup",
        "success": True,
        "result": {"status": "active"},
    })
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "lookup_is_not_proposition_authority"


def test_verify_failure_is_not_false_evidence() -> None:
    result = provider.classify({
        "probed": True,
        "binding_complete": True,
        "tool_kind": "verify",
        "success": False,
        "result": None,
    })
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "verification_tool_unavailable"


def test_bound_successful_verify_still_needs_explicit_profile() -> None:
    result = provider.classify({
        "probed": True,
        "binding_complete": True,
        "tool_kind": "verify",
        "success": True,
        "result": {"verified": True},
    })
    assert result == {
        "status": "UNKNOWN",
        "reason": "no_explicit_provider_profile",
    }


def test_partial_positive_evidence_does_not_authorize_whole_task() -> None:
    evidence = {
        "status": "TRUE",
        "decision_scope": {
            "intervention": "one_sub_action",
            "task_coverage": "partial",
        },
    }
    assert provider.decision_for(evidence) == "INVESTIGATE"


def test_partial_negative_evidence_can_block_required_sub_action() -> None:
    evidence = {
        "status": "FALSE",
        "decision_scope": {
            "intervention": "one_sub_action",
            "task_coverage": "partial",
        },
    }
    assert provider.decision_for(evidence) == "ABSTAIN"


def test_complete_positive_evidence_can_authorize_task() -> None:
    evidence = {
        "status": "TRUE",
        "decision_scope": {
            "intervention": "whole_task",
            "task_coverage": "complete",
        },
    }
    assert provider.decision_for(evidence) == "ACT"
