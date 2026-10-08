from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "agentabstain" / "prepare_runtime_blind_slice.py"

spec = importlib.util.spec_from_file_location("agentabstain_blind", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_gold_fields_are_removed_from_runtime_view() -> None:
    rows = [
        {
            "pair_id": "critical_tool_failure/x",
            "category": "critical_tool_failure",
            "task_id": "x",
            "task_type": "abstain",
            "phase": "runtime",
            "transformation_dimension": "environment",
            "instruction": "Do the operation.",
            "system_prompt": "assistant",
            "critical_actions": ["env.commit"],
            "execution_dag": None,
            "abstention_trigger": {"description": "tool failed"},
            "environments": ["env"],
        }
    ]
    blind, labels = module.build_blind_slice(rows)
    assert len(blind) == 1
    assert labels == [{"pair_id": "critical_tool_failure/x", "task_type": "abstain"}]
    for field in module.HIDDEN_FIELDS:
        assert field not in blind[0]


def test_pre_execution_cases_are_excluded() -> None:
    rows = [
        {
            "pair_id": "ambiguous_action_specification/x",
            "category": "ambiguous_action_specification",
            "task_id": "x",
            "task_type": "abstain",
            "phase": "pre_execution",
        }
    ]
    blind, labels = module.build_blind_slice(rows)
    assert blind == []
    assert labels == []
