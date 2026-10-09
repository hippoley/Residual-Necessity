from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "blind_probe.py"

spec = importlib.util.spec_from_file_location("agentabstain_blind_probe", MODULE)
assert spec and spec.loader
blind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blind)


def test_blind_selector_chooses_deterministic_zero_arg_tool() -> None:
    catalog = [
        {
            "name": "z.lookup",
            "description": "read",
            "input_schema": {"type": "object", "required": []},
        },
        {
            "name": "a.verify",
            "description": "verify",
            "input_schema": {"type": "object"},
        },
    ]
    selected = blind.choose_zero_arg_probe(catalog)
    assert selected is not None
    assert selected["name"] == "a.verify"


def test_blind_selector_rejects_required_argument_tools() -> None:
    catalog = [
        {
            "name": "lookup.by_id",
            "description": "read",
            "input_schema": {"type": "object", "required": ["id"]},
        }
    ]
    assert blind.choose_zero_arg_probe(catalog) is None


def test_blind_module_has_no_gold_or_hidden_state_dependencies() -> None:
    source = MODULE.read_text(encoding="utf-8")
    forbidden = {
        "AntiQuality",
        "agentabstain",
        "BaseAgent",
        "TaskBundle",
        "task_type",
        "execution_dag",
        "abstention_trigger",
        "critical_actions",
        "initial_states",
        "raw_state",
    }
    for token in forbidden:
        assert token not in source, f"blind probe leaked forbidden dependency token: {token}"
