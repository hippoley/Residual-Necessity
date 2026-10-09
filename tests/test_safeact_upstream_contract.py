from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "safeact_upstream_contract.py"

spec = importlib.util.spec_from_file_location("safeact_upstream_contract_test", MODULE)
assert spec and spec.loader
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


FAKE = '''
CONTRACT_ID = "safeact_evaluation_v1"
PROTOCOL_CONTRACTS = {
    "legacy": "legacy_fixed_candidate_v1",
    "v0": "evidence_gated_no_action_v1",
    "v1": "single_consequential_action_gate_v1",
    "v2": "linear_multi_commit_workflow_v2",
    "v3": "non_linear_dag_workflow_v3",
}

def canonical_expected_outcome(protocol, raw_outcome):
    table = {
        ("v0", "DEFER"): "NO_ACTION",
        ("v0", "BLOCK"): "NO_ACTION",
        ("v1", "ALLOW"): "TASK_SUCCESS",
        ("v2", "CASE_SUCCESS"): "WORKFLOW_SUCCESS",
    }
    return table[(protocol, raw_outcome)]

def contract_document():
    return {
        "contract_id": CONTRACT_ID,
        "common_invariants": {
            "gold_evaluator": "deterministic",
            "agent_visible_gold_fields": False,
        },
        "time_semantics": {"reference_clock_mode": "virtual_episode_clock"},
        "decision_semantics": {"defer": "missing evidence"},
    }
'''


def test_snapshot_delegates_to_external_safeact_module(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "safeact_contract.py").write_text(FAKE, encoding="utf-8")

    value = helper.snapshot(tmp_path)

    assert value["contract_id"] == "safeact_evaluation_v1"
    assert value["canonical_outcome_checks"]["v0_defer"] == "NO_ACTION"
    assert value["canonical_outcome_checks"]["v1_allow"] == "TASK_SUCCESS"
    assert value["time_semantics"]["reference_clock_mode"] == "virtual_episode_clock"


def test_snapshot_fails_closed_if_upstream_contract_changes(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    changed = FAKE.replace('"deterministic"', '"subjective"')
    (scripts / "safeact_contract.py").write_text(changed, encoding="utf-8")

    try:
        helper.snapshot(tmp_path)
    except ValueError as exc:
        assert "deterministic" in str(exc)
    else:
        raise AssertionError("upstream contract drift must fail closed")
