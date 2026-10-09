from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "agentabstain" / "prepare_runtime_blind_slice.py"

spec = importlib.util.spec_from_file_location("agentabstain_blind", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def runtime_row(task_type: str = "abstain") -> dict:
    return {
        "pair_id": "critical_tool_failure/x",
        "category": "critical_tool_failure",
        "task_id": "x",
        "task_type": task_type,
        "phase": "runtime",
        "transformation_dimension": "environment",
        "instruction": "Do the operation.",
        "system_prompt": "assistant",
        "critical_actions": ["env.commit"],
        "execution_dag": None,
        "abstention_trigger": {"description": "tool failed"},
        "environments": ["env"],
    }


def test_gold_fields_are_removed_from_runtime_view() -> None:
    blind, labels = module.build_blind_slice([runtime_row()])
    assert len(blind) == 1

    pair_id = module._opaque_pair_id("critical_tool_failure/x")
    case_id = module._opaque_case_id("critical_tool_failure/x", "abstain")

    assert blind[0]["pair_id"] == pair_id
    assert blind[0]["case_id"] == case_id
    assert "/" not in blind[0]["pair_id"]
    assert "/" not in blind[0]["case_id"]
    assert labels == [{
        "case_id": case_id,
        "pair_id": pair_id,
        "task_type": "abstain",
    }]
    for field in module.HIDDEN_FIELDS:
        assert field not in blind[0]


def test_runtime_locator_is_separate_from_inference_and_labels() -> None:
    rows = [runtime_row()]
    blind, labels = module.build_blind_slice(rows)
    runtime_map = module.build_runtime_map(rows)

    assert runtime_map == [{
        "case_id": blind[0]["case_id"],
        "category": "critical_tool_failure",
        "task_id": "x",
        "task_type": "abstain",
    }]
    assert "category" not in blind[0]
    assert "task_type" not in blind[0]
    assert "category" not in labels[0]
    assert "task_id" not in labels[0]


def test_pre_execution_cases_are_excluded() -> None:
    rows = [{
        "pair_id": "ambiguous_action_specification/x",
        "category": "ambiguous_action_specification",
        "task_id": "x",
        "task_type": "abstain",
        "phase": "pre_execution",
    }]
    blind, labels = module.build_blind_slice(rows)
    assert blind == []
    assert labels == []
    assert module.build_runtime_map(rows) == []


def test_same_pair_keeps_pair_id_but_cases_are_distinct() -> None:
    rows = []
    for task_type in ("act", "abstain"):
        row = runtime_row(task_type)
        row.update({
            "pair_id": "conflicting_evidence/preview_123",
            "category": "conflicting_evidence",
            "task_id": "preview_123",
            "instruction": "Inspect current evidence.",
        })
        rows.append(row)

    blind, labels = module.build_blind_slice(rows)

    assert blind[0]["pair_id"] == blind[1]["pair_id"]
    assert blind[0]["case_id"] != blind[1]["case_id"]
    assert "conflicting_evidence" not in blind[0]["pair_id"]
    assert "conflicting_evidence" not in blind[0]["case_id"]
    assert labels[0]["pair_id"] == labels[1]["pair_id"]
    assert labels[0]["case_id"] != labels[1]["case_id"]
